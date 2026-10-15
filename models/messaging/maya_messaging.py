# -*- coding: utf-8 -*-
"""
Mensajería Maya desde Odoo: logs, auditoría y notificaciones hacia RabbitMQ (vhost /maya).

Contrato: estándar de mensajería de maya_platform (messaging/ESTANDAR.md, topology.yaml) y
DOCUMENTATION → servicios/rabbitmq-contracts.md. Exchanges y claves:

  maya.logs           <app>.<severity>                         solo errores de negocio
  maya.audit          <app>.<entity_type>.<action>
  maya.notifications  <app>.<type>.<channel>[.critical]        un mensaje por canal, mismo message_id

Todo se publica DESPUÉS de la transacción (cr.postcommit): si la transacción se deshace, no sale nada
(los logs de error, en cambio, salen también si se deshace: el error suele ser la causa). Publicar
nunca lanza excepciones ni hace fallar la transacción: el transporte (support/amqp.py) se encarga.

Uso desde otros modelos (métodos privados: no se pueden llamar por RPC):

  messaging = self.env['maya_core.messaging']
  messaging._publish_log('high', 'No se pudo descargar de Aules', error_code='AULES_TIMEOUT')
  messaging._publish_audit('maya_core.employee', employee.id, 'updated', {'lang': 'es_ES'}, {'lang': 'ca_ES'})
  messaging._notify(users, 'signature.batch.done', title='Lote firmado', body='…',
                    channels=['app', 'email'], url=messaging._record_url(batch),
                    attachments=messaging._field_attachment_refs(doc, 'signed_pdf', doc.signed_pdf_filename))
"""
import datetime
import functools
import hashlib
import logging
import re
import uuid

from odoo import api, models
from odoo.tools import config

from ...support import amqp

_logger = logging.getLogger(__name__)

EXCHANGE_LOGS = 'maya.logs'
EXCHANGE_AUDIT = 'maya.audit'
EXCHANGE_NOTIFICATIONS = 'maya.notifications'

LOG_SEVERITIES = ('critical', 'high', 'medium', 'low', 'other')
NOTIFICATION_SEVERITIES = ('critical', 'high', 'medium', 'low', 'info')
NOTIFICATION_CHANNELS = ('app', 'email', 'webhook', 'slack')
NOTIFICATION_SCOPES = ('user', 'dashboard', 'both')
CRITICAL_SEVERITIES = ('critical', 'high')

# metadata.attachments[] (contrato v1, adjuntos por referencia: el fichero no viaja en el mensaje)
ATTACHMENT_KEYS = ('source', 'model', 'id', 'name', 'mimetype', 'size', 'sha256')

# Trozos de una clave de enrutado: minúsculas, dígitos, `_` y `-`, separados por puntos
_ROUTING_PART = re.compile(r'^[a-z0-9_-]+(\.[a-z0-9_-]+)*$')
_SHA256 = re.compile(r'^[0-9a-f]{64}$')

_DATA_KEY = 'maya_core.messaging'                 # se publica solo si hay commit
_DATA_KEY_ALWAYS = 'maya_core.messaging.always'   # se publica con commit o con rollback


def _utc_now():
  return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def _check_routing_part(value, what):
  if not isinstance(value, str) or not _ROUTING_PART.match(value):
    raise ValueError('%s no válido para la clave de enrutado: %r (minúsculas, dígitos, _, - y puntos)'
                     % (what, value))
  return value


def _jsonable(value):
  """Valor apto para JSON (fechas a ISO 8601, recordsets a ids, bytes fuera)."""
  if isinstance(value, models.BaseModel):
    return value.ids if len(value) != 1 else value.id
  if isinstance(value, (datetime.datetime, datetime.date)):
    return value.isoformat()
  if isinstance(value, bytes):
    return None
  if isinstance(value, dict):
    return {str(k): _jsonable(v) for k, v in value.items()}
  if isinstance(value, (list, tuple, set)):
    return [_jsonable(v) for v in value]
  return value


def check_attachment_refs(refs):
  """Valida metadata.attachments[] (lista de dicts). Devuelve una copia limpia o lanza ValueError."""
  if not isinstance(refs, (list, tuple)):
    raise ValueError('attachments debe ser una lista')
  clean = []
  for ref in refs:
    if not isinstance(ref, dict):
      raise ValueError('cada adjunto debe ser un objeto')
    missing = [k for k in ATTACHMENT_KEYS if k not in ref]
    if missing:
      raise ValueError('adjunto sin %s' % ', '.join(missing))
    if not isinstance(ref['id'], int) or isinstance(ref['id'], bool) or ref['id'] <= 0:
      raise ValueError('adjunto: id debe ser un entero positivo')
    if not isinstance(ref['size'], int) or isinstance(ref['size'], bool) or ref['size'] < 0:
      raise ValueError('adjunto %s: size debe ser un entero >= 0' % ref['id'])
    for key in ('source', 'model', 'name', 'mimetype'):
      if not isinstance(ref[key], str) or not ref[key].strip():
        raise ValueError('adjunto %s: %s vacío' % (ref['id'], key))
    if not isinstance(ref['sha256'], str) or not _SHA256.match(ref['sha256']):
      raise ValueError('adjunto %s: sha256 debe ser hexadecimal en minúsculas (64)' % ref['id'])
    clean.append({k: ref[k] for k in ATTACHMENT_KEYS})
  return clean


def _publish_after_transaction(publisher, messages):
  """Callback de cr.postcommit (y cr.postrollback para los logs). Nunca lanza."""
  if not messages:
    return
  batch = list(messages)
  messages.clear()
  try:
    publisher.publish(batch)
  except Exception:  # pylint: disable=broad-except
    _logger.exception('maya messaging: fallo al publicar %s mensaje(s) tras la transacción', len(batch))


class MayaMessaging(models.AbstractModel):
  _name = 'maya_core.messaging'
  _description = 'Mensajería Maya (RabbitMQ)'

  # ------------------------------------------------------------------ infraestructura
  @api.model
  def _publisher(self):
    """Publicador del proceso (support/amqp.py). Los tests lo sustituyen por uno simulado."""
    return amqp.get_publisher(config.get)

  @api.model
  def _app(self):
    return self._publisher().settings.app_id

  @api.model
  def _enqueue(self, message, always=False):
    """Deja `message` para después de la transacción. `always`: también si hay rollback."""
    cr = self.env.cr
    key = _DATA_KEY_ALWAYS if always else _DATA_KEY
    pending = cr.postcommit.data.get(key)
    if pending is None:
      pending = cr.postcommit.data[key] = []
      callback = functools.partial(_publish_after_transaction, self._publisher(), pending)
      cr.postcommit.add(callback)
      if always:
        # Con commit, Odoo vacía postrollback; con rollback, vacía postcommit: corre una sola vez
        cr.postrollback.add(callback)
    pending.append(message)
    return message

  @api.model
  def _base_url(self):
    return (self.env['ir.config_parameter'].sudo().get_param('web.base.url') or '').rstrip('/')

  @api.model
  def _absolute_url(self, url):
    if url and url.startswith('/'):
      return self._base_url() + url
    return url or None

  @api.model
  def _record_url(self, record):
    """Enlace al formulario de `record`, desde web.base.url."""
    record.ensure_one()
    return '%s/web#id=%s&model=%s&view_type=form' % (self._base_url(), record.id, record._name)

  @api.model
  def _actor_id(self, user=None):
    """Quién hace la acción: el `sub` de Keycloak (res.users.oauth_uid) o, si no tiene, odoo:<login>."""
    if user is None:
      user_id = self.env.context.get('maya_audit_user_id')
      user = self.env['res.users'].browse(user_id) if user_id else self.env.user
    user = user.sudo().exists() if user else user
    if not user:
      return 'odoo:sistema'
    return user.oauth_uid or 'odoo:%s' % user.login

  @api.model
  def _request_info(self):
    """IP y agente de la petición HTTP en curso, si la hay."""
    try:
      from odoo.http import request  # pylint: disable=import-outside-toplevel
      if request and getattr(request, 'httprequest', None) is not None:
        agent = request.httprequest.user_agent
        return request.httprequest.remote_addr, (agent.string[:512] if agent else None)
    except Exception:  # pylint: disable=broad-except
      pass
    return None, None

  # ------------------------------------------------------------------ maya.logs
  @api.model
  def _publish_log(self, severity, message, error_code=None, file=None, line=None, metadata=None,
                   occurred_at=None):
    """Error de negocio → maya.logs. Nunca lanza: se llama desde manejadores de errores."""
    try:
      app = self._app()
      severity = severity if severity in LOG_SEVERITIES else 'other'
      body = {
        'app': app,
        'severity': severity,
        'message': str(message),
        'error_code': error_code,
        'file': file,
        'line': line,
        'metadata': _jsonable(dict(metadata or {})),
        'occurred_at': occurred_at or _utc_now(),
      }
      return self._enqueue(amqp.Message(EXCHANGE_LOGS, '%s.%s' % (app, severity), body), always=True)
    except Exception:  # pylint: disable=broad-except
      _logger.exception('maya messaging: no se pudo preparar el log de negocio')
      return None

  # ------------------------------------------------------------------ maya.audit
  @api.model
  def _publish_audit(self, entity_type, entity_id, action, previous_value=None, new_value=None,
                     user=None, block_id=None):
    """Evento de auditoría → maya.audit (`<app>.<entity_type>.<action>`), si hay commit."""
    app = self._app()
    _check_routing_part(entity_type, 'entity_type')
    _check_routing_part(action, 'action')
    ip_address, user_agent = self._request_info()
    body = {
      'application_slug': app,
      'entity_type': entity_type,
      'entity_id': str(entity_id),
      'block_id': block_id,
      'action': action,
      'user_id': self._actor_id(user),
      'ip_address': ip_address,
      'user_agent': user_agent,
      'previous_value': _jsonable(previous_value) if previous_value is not None else None,
      'new_value': _jsonable(new_value) if new_value is not None else None,
      'occurred_at': _utc_now(),
    }
    body = {k: v for k, v in body.items() if v is not None}
    return self._enqueue(amqp.Message(EXCHANGE_AUDIT, '%s.%s.%s' % (app, entity_type, action), body))

  # ------------------------------------------------------------------ maya.notifications
  @api.model
  def _notify(self, recipients, notification_type, title='', body='', channels=('app',), severity='info',
              url=None, metadata=None, attachments=None, title_key=None, body_key=None, params=None,
              scope='user'):
    """Notificación a usuarios → maya.notifications, si hay commit.

    `recipients`: res.users (se usa su oauth_uid, el `sub` de Keycloak; sin él, el dashboard la
    descartaría y no se envía). Un mensaje por destinatario y canal; las copias de un mismo
    destinatario comparten message_id. `attachments`: ir.attachment o lista ya hecha con
    _attachment_refs (van en metadata.attachments, por referencia). `url` relativa → web.base.url.
    """
    app = self._app()
    _check_routing_part(notification_type, 'type')
    channels = list(dict.fromkeys(channels or ()))
    if not channels:
      raise ValueError('hace falta al menos un canal')
    invalid = [c for c in channels if c not in NOTIFICATION_CHANNELS]
    if invalid:
      raise ValueError('canal no válido: %s' % ', '.join(invalid))
    if severity not in NOTIFICATION_SEVERITIES:
      raise ValueError('severidad no válida: %r' % severity)
    if scope not in NOTIFICATION_SCOPES:
      raise ValueError('scope no válido: %r' % scope)
    recipients = recipients if recipients is not None else self.env['res.users']
    if scope in ('user', 'both') and not recipients:
      raise ValueError("hace falta al menos un destinatario con scope '%s'" % scope)

    metadata = dict(metadata or {})
    if attachments:
      if isinstance(attachments, models.BaseModel):
        attachments = self._attachment_refs(attachments)
      metadata['attachments'] = check_attachment_refs(attachments)

    is_critical = severity in CRITICAL_SEVERITIES
    base = {
      'app': app,
      'type': notification_type,
      'recipient_keycloak_id': '',
      'title': title or '',
      'body': body or '',
      'title_key': title_key,
      'body_key': body_key,
      'params': _jsonable(dict(params or {})),
      'severity': severity,
      'url': self._absolute_url(url),
      'channels': channels,
      'metadata': _jsonable(metadata),
      'created_at': _utc_now(),
      'is_critical': is_critical,
      'scope': scope,
    }
    targets = [None] if scope == 'dashboard' else list(recipients.sudo())
    messages = []
    for user in targets:
      payload = dict(base)
      if user is not None:
        if not user.oauth_uid:
          _logger.warning('maya messaging: el usuario %s no tiene oauth_uid (sub de Keycloak); '
                          'notificación %s sin enviar', user.id, notification_type)
          continue
        payload['recipient_keycloak_id'] = user.oauth_uid
      message_id = str(uuid.uuid4())
      for channel in channels:
        routing_key = '%s.%s.%s%s' % (app, notification_type, channel, '.critical' if is_critical else '')
        messages.append(self._enqueue(amqp.Message(EXCHANGE_NOTIFICATIONS, routing_key, payload,
                                                   message_id=message_id)))
    return messages

  # ------------------------------------------------------------------ adjuntos por referencia
  @api.model
  def _attachment_refs(self, attachments):
    """metadata.attachments[] para estos ir.attachment: el fichero se queda en Odoo.

    n8n (notifications.email) los descarga con su usuario de servicio y comprueba el sha256.
    """
    refs = []
    for attachment in attachments.sudo():
      raw = attachment.raw
      if not raw:
        raise ValueError('el adjunto %s no tiene contenido (¿es de tipo url?)' % attachment.id)
      refs.append({
        'source': 'odoo',
        'model': 'ir.attachment',
        'id': attachment.id,
        'name': attachment.name or 'adjunto-%s' % attachment.id,
        'mimetype': attachment.mimetype or 'application/octet-stream',
        'size': len(raw),
        'sha256': hashlib.sha256(raw).hexdigest(),
      })
    return refs

  @api.model
  def _field_attachment_refs(self, record, field_name, filename=None):
    """Referencia al fichero de un campo Binary con attachment=True (p. ej. signed_pdf)."""
    record.ensure_one()
    attachment = self.env['ir.attachment'].sudo().search([
      ('res_model', '=', record._name),
      ('res_id', '=', record.id),
      ('res_field', '=', field_name),
    ], limit=1)
    refs = self._attachment_refs(attachment)
    if refs and filename:
      refs[0]['name'] = filename
    return refs
