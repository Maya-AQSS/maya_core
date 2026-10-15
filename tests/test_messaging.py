# -*- coding: utf-8 -*-
"""
Mensajería Maya desde Odoo (models/messaging) con el publicador simulado: qué se publica, con qué
contrato y solo después del commit.

  odoo -d <bd de pruebas> -i maya_core --test-tags /maya_core --stop-after-init
"""
import base64
import hashlib
from unittest.mock import patch

from odoo.fields import Command
from odoo.tests import TransactionCase

from odoo.addons.maya_core.models.messaging import maya_messaging
from odoo.addons.maya_core.support import amqp


class FakePublisher:
  """Hace de support/amqp.AmqpPublisher: guarda lo publicado o falla si se le pide."""

  def __init__(self):
    self.settings = amqp.Settings(host='rabbitmq.test', password='x', app_id='odoo')
    self.published = []
    self.fail = False

  def publish(self, messages):
    if self.fail:
      raise RuntimeError('RabbitMQ caído')
    self.published.extend(messages)
    return len(messages)


class MessagingCase(TransactionCase):

  def setUp(self):
    super().setUp()
    self.publisher = FakePublisher()
    self.Messaging = self.env['maya_core.messaging']
    self.startPatcher(patch.object(type(self.Messaging), '_publisher', return_value=self.publisher))
    # Nada pendiente de antes del test (lo restaura TransactionCase al acabar)
    for key in (maya_messaging._DATA_KEY, maya_messaging._DATA_KEY_ALWAYS):
      self.env.cr.postcommit.data.pop(key, None)

  def commit(self):
    """Lo que hace Odoo al confirmar: corre postcommit (y descarta postrollback)."""
    self.env.flush_all()
    self.env.cr.postrollback.clear()
    self.env.cr.postcommit.run()

  def rollback(self):
    """Lo que hace Odoo al deshacer: descarta postcommit y corre postrollback."""
    self.env.cr.postcommit.clear()
    self.env.cr.postrollback.run()

  def published(self, exchange=None):
    return [m for m in self.publisher.published if exchange is None or m.exchange == exchange]


class TestAudit(MessagingCase):

  def test_audit_only_after_commit(self):
    batch = self.env['maya_core.signature.batch'].create({'name': 'Lote de prueba'})
    self.assertEqual(self.published(), [], 'nada antes del commit')
    self.commit()
    [message] = self.published('maya.audit')
    self.assertEqual(message.routing_key, 'odoo.maya_core.signature.batch.created')
    body = message.body
    self.assertEqual(body['application_slug'], 'odoo')
    self.assertEqual(body['entity_type'], 'maya_core.signature.batch')
    self.assertEqual(body['entity_id'], str(batch.id))
    self.assertEqual(body['action'], 'created')
    self.assertEqual(body['new_value'], {'state': 'draft', 'sign_date': None})
    self.assertNotIn('previous_value', body, 'los nulos se omiten, como AuditPublisher')
    self.assertTrue(body['user_id'].startswith('odoo:'), 'usuario sin oauth_uid → odoo:<login>')
    self.assertTrue(body['occurred_at'].endswith('Z'))

  def test_audit_update_has_only_changed_fields(self):
    batch = self.env['maya_core.signature.batch'].create({'name': 'Lote'})
    self.commit()
    self.publisher.published.clear()
    batch.write({'name': 'Otro nombre'})
    self.commit()
    self.assertEqual(self.published(), [], 'campo no auditado → sin evento')
    batch.write({'state': 'ready'})
    self.commit()
    [message] = self.published('maya.audit')
    self.assertEqual(message.routing_key, 'odoo.maya_core.signature.batch.updated')
    self.assertEqual(message.body['previous_value'], {'state': 'draft'})
    self.assertEqual(message.body['new_value'], {'state': 'ready'})

  def test_audit_dropped_on_rollback(self):
    self.env['maya_core.signature.batch'].create({'name': 'Lote'})
    self.rollback()
    self.assertEqual(self.published(), [])

  def test_audit_delete(self):
    batch = self.env['maya_core.signature.batch'].create({'name': 'Lote'})
    batch_id = batch.id
    self.commit()
    self.publisher.published.clear()
    batch.unlink()
    self.commit()
    [message] = self.published('maya.audit')
    self.assertEqual(message.body['action'], 'deleted')
    self.assertEqual(message.body['entity_id'], str(batch_id))
    self.assertEqual(message.body['previous_value']['state'], 'draft')

  def test_employee_audit_redacts_and_uses_api_user(self):
    team = self.env['maya_core.team'].create({'name': 'Equipo C7', 'abbr': 'EC7'})
    owner = self.env['res.users'].create({
      'name': 'Empleada', 'surname': 'De Prueba', 'login': 'empleada.c7@example.com',
      'oauth_uid': 'kc-empleada-c7',
    })
    employee = self.env['maya_core.employee'].create({
      'user_ids': [Command.link(owner.id)],
      'team_ids': [Command.set(team.ids)],
    })
    self.commit()
    [created] = self.published('maya.audit')
    self.assertEqual(created.routing_key, 'odoo.maya_core.employee.created')
    self.publisher.published.clear()
    # El IBAN se censura igual que aquí el correo personal (no se usa el IBAN en el test: su
    # restricción reescribe el campo)
    self.assertIn('iban', type(employee)._maya_audit_redacted)
    self.startPatcher(patch.object(type(employee), '_maya_audit_redacted', ('personal_email',)))
    # Como la API v1: sudo, con quien se autenticó con su token de Keycloak en el contexto
    employee.sudo().with_context(maya_audit_user_id=owner.id).write({
      'phone_extension': '1234',
      'personal_email': 'privado@example.com',
      'comments': 'no auditado',
    })
    self.commit()
    [message] = self.published('maya.audit')
    self.assertEqual(message.routing_key, 'odoo.maya_core.employee.updated')
    self.assertEqual(message.body['user_id'], 'kc-empleada-c7')
    self.assertEqual(message.body['previous_value'], {'phone_extension': None, 'personal_email': None})
    self.assertEqual(message.body['new_value'], {'phone_extension': '1234', 'personal_email': '***'})
    self.assertNotIn('privado@example.com', str(message.body), 'el valor censurado no sale de Odoo')


class TestLogs(MessagingCase):

  def test_log_is_published_even_on_rollback(self):
    self.Messaging._publish_log('high', 'Fallo al descargar de Aules', error_code='AULES_TIMEOUT',
                                metadata={'cron_id': 7})
    self.rollback()
    [message] = self.published('maya.logs')
    self.assertEqual(message.routing_key, 'odoo.high')
    self.assertEqual(message.body['app'], 'odoo')
    self.assertEqual(message.body['severity'], 'high')
    self.assertEqual(message.body['message'], 'Fallo al descargar de Aules')
    self.assertEqual(message.body['error_code'], 'AULES_TIMEOUT')
    self.assertEqual(message.body['metadata'], {'cron_id': 7})
    self.assertTrue(message.body['occurred_at'].endswith('Z'))

  def test_log_is_published_once_on_commit(self):
    self.Messaging._publish_log('bogus', 'algo')
    self.commit()
    self.rollback()
    [message] = self.published('maya.logs')
    self.assertEqual(message.routing_key, 'odoo.other', 'severidad desconocida → other')

  def test_publisher_failure_does_not_break_commit(self):
    self.publisher.fail = True
    self.Messaging._publish_log('high', 'algo')
    self.env['maya_core.signature.batch'].create({'name': 'Lote'})
    with self.assertLogs(maya_messaging._logger.name, level='ERROR'):
      self.commit()  # no lanza
    self.assertEqual(self.published(), [])

  def test_cron_failure_publishes_business_error(self):
    model = self.env['ir.model']._get('res.partner')
    cron = self.env['maya_core.ir.cron'].create({
      'name': 'Tarea C7 que falla',
      'model_id': model.id,
      'state': 'code',
      'code': "raise UserError('Aules no responde')",
      'key': 'C7TST',
      'interval_number': 1,
      'interval_type': 'days',
    })
    with self.assertLogs('odoo.addons.maya_core.models.ir.ir_cron', level='ERROR'):
      cron.method_direct_trigger()
    self.commit()
    [message] = self.published('maya.logs')
    self.assertEqual(message.routing_key, 'odoo.high')
    self.assertIn('Tarea C7 que falla', message.body['message'])
    self.assertEqual(message.body['metadata']['cron_id'], cron.id)
    self.assertEqual(message.body['metadata']['key'], 'C7TST')
    self.assertIn('Aules no responde', message.body['metadata']['error'])


class TestNotifications(MessagingCase):

  def setUp(self):
    super().setUp()
    self.env['ir.config_parameter'].sudo().set_param('web.base.url', 'https://odoo.ceedcv')
    self.with_sub = self.env['res.users'].create({
      'name': 'Con sub', 'login': 'con.sub.c7@example.com', 'oauth_uid': 'kc-con-sub'})
    self.without_sub = self.env['res.users'].create({
      'name': 'Sin sub', 'login': 'sin.sub.c7@example.com'})

  def test_notification_contract(self):
    self.Messaging._notify(self.with_sub | self.without_sub, 'signature.batch.done',
                           title='Lote firmado', body='<b>hola</b>', channels=['app', 'email'],
                           severity='high', url='/web#id=1&model=maya_core.signature.batch')
    self.assertEqual(self.published(), [], 'nada antes del commit')
    self.commit()
    messages = self.published('maya.notifications')
    self.assertEqual([m.routing_key for m in messages], [
      'odoo.signature.batch.done.app.critical',
      'odoo.signature.batch.done.email.critical',
    ], 'un mensaje por canal; el usuario sin oauth_uid no recibe nada')
    self.assertEqual(messages[0].message_id, messages[1].message_id, 'mismo message_id en las copias')
    body = messages[0].body
    self.assertEqual(body['recipient_keycloak_id'], 'kc-con-sub')
    self.assertEqual(body['app'], 'odoo')
    self.assertEqual(body['type'], 'signature.batch.done')
    self.assertEqual(body['title'], 'Lote firmado')
    self.assertEqual(body['body'], '<b>hola</b>', 'Odoo no escapa: lo hace quien pinta (n8n, dashboard)')
    self.assertEqual(body['channels'], ['app', 'email'])
    self.assertEqual(body['severity'], 'high')
    self.assertTrue(body['is_critical'])
    self.assertEqual(body['scope'], 'user')
    self.assertEqual(body['url'], 'https://odoo.ceedcv/web#id=1&model=maya_core.signature.batch')
    self.assertEqual(body['metadata'], {})

  def test_notification_not_sent_on_rollback(self):
    self.Messaging._notify(self.with_sub, 'test.c7', title='t')
    self.rollback()
    self.assertEqual(self.published(), [])

  def test_notification_validation(self):
    with self.assertRaises(ValueError):
      self.Messaging._notify(self.with_sub, 'test.c7', channels=['fax'])
    with self.assertRaises(ValueError):
      self.Messaging._notify(self.with_sub, 'test.c7', severity='urgente')
    with self.assertRaises(ValueError):
      self.Messaging._notify(self.with_sub, 'Tipo Con Espacios')
    with self.assertRaises(ValueError):
      self.Messaging._notify(self.env['res.users'], 'test.c7')

  def test_record_url_uses_base_url(self):
    batch = self.env['maya_core.signature.batch'].create({'name': 'Lote'})
    self.assertEqual(self.Messaging._record_url(batch),
                     'https://odoo.ceedcv/web#id=%s&model=maya_core.signature.batch&view_type=form' % batch.id)


class TestAttachments(MessagingCase):
  """C9: adjuntos por referencia en metadata.attachments[] (el fichero no viaja en el mensaje)."""

  def test_attachment_refs(self):
    raw = b'contenido del adjunto de prueba C9'
    attachment = self.env['ir.attachment'].create({
      'name': 'informe.txt', 'raw': raw, 'mimetype': 'text/plain'})
    [ref] = self.Messaging._attachment_refs(attachment)
    self.assertEqual(ref, {
      'source': 'odoo',
      'model': 'ir.attachment',
      'id': attachment.id,
      'name': 'informe.txt',
      'mimetype': attachment.mimetype,
      'size': len(raw),
      'sha256': hashlib.sha256(raw).hexdigest(),
    })

  def test_field_attachment_refs_and_notification(self):
    raw = b'%PDF-1.4 firmado'
    batch = self.env['maya_core.signature.batch'].create({'name': 'Lote'})
    document = self.env['maya_core.signature.batch_document'].create({
      'batch_id': batch.id, 'res_model': 'res.partner', 'res_id': 1, 'filename': 'doc.pdf',
      'signed_pdf': base64.b64encode(raw),
    })
    refs = self.Messaging._field_attachment_refs(document, 'signed_pdf', 'documento-firmado.pdf')
    self.assertEqual(len(refs), 1)
    self.assertEqual(refs[0]['name'], 'documento-firmado.pdf')
    self.assertEqual(refs[0]['sha256'], hashlib.sha256(raw).hexdigest())
    self.assertEqual(refs[0]['size'], len(raw))

    user = self.env['res.users'].create({'name': 'Firmante', 'login': 'firmante.c7@example.com',
                                         'oauth_uid': 'kc-firmante'})
    self.Messaging._notify(user, 'signature.batch.done', title='Firmado', channels=['email'],
                           attachments=refs)
    self.commit()
    [message] = self.published('maya.notifications')
    self.assertEqual(message.routing_key, 'odoo.signature.batch.done.email')
    self.assertEqual(message.body['metadata']['attachments'], refs)
    self.assertNotIn(base64.b64encode(raw).decode(), str(message.body), 'el fichero no va en el mensaje')

  def test_notify_accepts_attachment_records(self):
    attachment = self.env['ir.attachment'].create({'name': 'a.txt', 'raw': b'abc', 'mimetype': 'text/plain'})
    user = self.env['res.users'].create({'name': 'U', 'login': 'u.c7@example.com', 'oauth_uid': 'kc-u'})
    self.Messaging._notify(user, 'test.c7', title='t', channels=['email'], attachments=attachment)
    self.commit()
    [message] = self.published('maya.notifications')
    self.assertEqual(message.body['metadata']['attachments'][0]['id'], attachment.id)

  def test_invalid_attachment_refs_are_rejected(self):
    good = {'source': 'odoo', 'model': 'ir.attachment', 'id': 1, 'name': 'a.txt',
            'mimetype': 'text/plain', 'size': 3, 'sha256': hashlib.sha256(b'abc').hexdigest()}
    self.assertEqual(maya_messaging.check_attachment_refs([good]), [good])
    for bad in (dict(good, sha256='ABC'), dict(good, id=0), dict(good, size=-1), dict(good, name=''),
                {k: v for k, v in good.items() if k != 'mimetype'}):
      with self.assertRaises(ValueError):
        maya_messaging.check_attachment_refs([bad])
