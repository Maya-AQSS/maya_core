# -*- coding: utf-8 -*-
"""
Publicador AMQP de Maya para Odoo (estándar de mensajería v1 de maya_platform/messaging).

Este fichero no importa Odoo: es el transporte. La parte de Odoo (qué se publica y cuándo) está en
models/messaging/ y siempre publica después del commit (cr.postcommit).

Reglas que cumple:
  - Propiedades AMQP del contrato: content_type=application/json, delivery_mode=2, message_id (UUID),
    timestamp en segundos, app_id y la cabecera x-maya-schema-version: 1.
  - Una conexión por proceso, abierta la primera vez que se publica (nunca al importar ni al arrancar):
    con `workers > 0`, Odoo hace fork de los workers y una conexión heredada del proceso padre no se usa
    ni se cierra (se comprueba el pid y se limpia con os.register_at_fork).
  - Nunca lanza excepciones ni se queda esperando: confirmaciones del broker con plazo
    (TCP_USER_TIMEOUT), un reintento con conexión nueva si la anterior estaba muerta y, si RabbitMQ no
    responde, los mensajes esperan en memoria (como mucho `pending_max`) y no se vuelve a intentar
    conectar hasta pasados `retry_after` segundos.
  - Candado: pika no es seguro entre hilos (Odoo con `workers = 0` atiende con hilos).

Configuración (variable de entorno > odoo.conf > valor por defecto):

  | Entorno               | odoo.conf                  | Defecto  |
  |-----------------------|----------------------------|----------|
  | RABBITMQ_HOST         | maya_rabbitmq_host         | (vacío: publicador desactivado) |
  | RABBITMQ_PORT         | maya_rabbitmq_port         | 5672     |
  | RABBITMQ_VHOST        | maya_rabbitmq_vhost        | /maya    |
  | RABBITMQ_USER         | maya_rabbitmq_user         | odoo     |
  | RABBITMQ_PASSWORD     | maya_rabbitmq_password     | (vacío: publicador desactivado) |
  | MAYA_MESSAGING_APP    | maya_messaging_app         | odoo     |
  | MAYA_RABBITMQ_TIMEOUT | maya_rabbitmq_timeout      | 3 (s)    |
"""
import atexit
import collections
import dataclasses
import json
import logging
import os
import socket
import threading
import time
import uuid

try:
  import pika
  import pika.exceptions
except ImportError:  # sin pika el módulo carga igual, con el publicador desactivado
  pika = None

_logger = logging.getLogger(__name__)

SCHEMA_VERSION = '1'
SCHEMA_HEADER = 'x-maya-schema-version'
CONTENT_TYPE = 'application/json'
PERSISTENT = 2

# clave → (variable de entorno, opción de odoo.conf, valor por defecto)
_OPTIONS = {
  'host': ('RABBITMQ_HOST', 'maya_rabbitmq_host', ''),
  'port': ('RABBITMQ_PORT', 'maya_rabbitmq_port', 5672),
  'vhost': ('RABBITMQ_VHOST', 'maya_rabbitmq_vhost', '/maya'),
  'user': ('RABBITMQ_USER', 'maya_rabbitmq_user', 'odoo'),
  'password': ('RABBITMQ_PASSWORD', 'maya_rabbitmq_password', ''),
  'app_id': ('MAYA_MESSAGING_APP', 'maya_messaging_app', 'odoo'),
  'timeout': ('MAYA_RABBITMQ_TIMEOUT', 'maya_rabbitmq_timeout', 3.0),
}


@dataclasses.dataclass(frozen=True)
class Settings:
  host: str = ''
  port: int = 5672
  vhost: str = '/maya'
  user: str = 'odoo'
  password: str = dataclasses.field(default='', repr=False)
  app_id: str = 'odoo'
  timeout: float = 3.0
  retry_after: float = 30.0   # segundos sin intentar conectar tras un fallo
  pending_max: int = 1000     # mensajes en memoria, como mucho, mientras RabbitMQ no responde

  @property
  def enabled(self):
    return bool(self.host and self.password and pika is not None)

  @classmethod
  def load(cls, conf_get=None, environ=None):
    """Lee la configuración. `conf_get(clave)` devuelve una opción de odoo.conf (o None)."""
    environ = os.environ if environ is None else environ
    values = {}
    for key, (env_name, conf_name, default) in _OPTIONS.items():
      value = environ.get(env_name)
      if value in (None, '') and conf_get is not None:
        value = conf_get(conf_name)
      if value in (None, '', False):
        value = default
      if isinstance(value, str) and key != 'password':
        value = value.strip()
      values[key] = value
    try:
      values['port'] = int(values['port'])
    except (TypeError, ValueError):
      _logger.warning('maya messaging: puerto de RabbitMQ no válido (%r), uso 5672', values['port'])
      values['port'] = 5672
    try:
      values['timeout'] = max(0.5, float(values['timeout']))
    except (TypeError, ValueError):
      values['timeout'] = 3.0
    return cls(**values)


@dataclasses.dataclass(frozen=True)
class Message:
  """Un mensaje listo para publicar. `body` es un dict que se serializa a JSON."""
  exchange: str
  routing_key: str
  body: dict
  message_id: str = dataclasses.field(default_factory=lambda: str(uuid.uuid4()))
  timestamp: int = dataclasses.field(default_factory=lambda: int(time.time()))

  def encoded_body(self):
    return json.dumps(self.body, ensure_ascii=False, separators=(',', ':'), default=str).encode('utf-8')

  def properties(self, app_id):
    """Propiedades AMQP del contrato (ESTANDAR.md § 5)."""
    return pika.BasicProperties(
      content_type=CONTENT_TYPE,
      delivery_mode=PERSISTENT,
      message_id=self.message_id,
      timestamp=self.timestamp,
      app_id=app_id,
      headers={SCHEMA_HEADER: SCHEMA_VERSION},
    )


def _default_connect(settings):
  """Abre conexión y canal con confirmaciones del broker. Devuelve (conexión, canal)."""
  params = pika.ConnectionParameters(
    host=settings.host,
    port=settings.port,
    virtual_host=settings.vhost,
    credentials=pika.PlainCredentials(settings.user, settings.password),
    # Sin latidos AMQP: con un BlockingConnection ocioso nadie los atendería y el broker cerraría la
    # conexión cada pocos minutos. Las conexiones muertas las detecta TCP (keepalive y
    # TCP_USER_TIMEOUT), que además pone plazo a la espera de la confirmación.
    heartbeat=0,
    connection_attempts=1,
    retry_delay=0,
    socket_timeout=settings.timeout,
    stack_timeout=settings.timeout * 2,
    blocked_connection_timeout=settings.timeout * 2,
    tcp_options={
      'TCP_KEEPIDLE': 60,
      'TCP_KEEPINTVL': 10,
      'TCP_KEEPCNT': 3,
      'TCP_USER_TIMEOUT': int(settings.timeout * 1000),
    },
    client_properties={'connection_name': '%s@%s:%s' % (settings.app_id, socket.gethostname(), os.getpid())},
  )
  connection = pika.BlockingConnection(params)
  try:
    channel = connection.channel()
    channel.confirm_delivery()
  except Exception:
    _close_quietly(connection)
    raise
  return connection, channel


def _close_quietly(connection):
  try:
    if connection is not None and connection.is_open:
      connection.close()
  except Exception:  # pylint: disable=broad-except
    pass


def _is_unroutable(error):
  return pika is not None and isinstance(error, pika.exceptions.UnroutableError)


class AmqpPublisher:
  """Publica mensajes con una conexión por proceso. `publish()` nunca lanza excepciones."""

  def __init__(self, settings, connect=None, clock=time.monotonic, getpid=os.getpid):
    self.settings = settings
    self._connect = connect or _default_connect
    self._clock = clock
    self._getpid = getpid
    self._lock = threading.Lock()
    self._pid = None
    self._connection = None
    self._channel = None
    self._down_until = 0.0
    self._pending = collections.deque()

  # ------------------------------------------------------------------ API
  def publish(self, messages):
    """Publica `messages` (lista de Message) y los pendientes. Devuelve cuántos confirmó el broker."""
    messages = list(messages)
    if not self.settings.enabled:
      if messages:
        _logger.debug('maya messaging: publicador desactivado; %s mensaje(s) sin enviar', len(messages))
      return 0
    if not self._lock.acquire(timeout=self.settings.timeout * 2):
      _logger.warning('maya messaging: publicador ocupado; %s mensaje(s) quedan pendientes', len(messages))
      self._keep(messages)
      return 0
    try:
      self._check_fork()
      batch = self._take_pending() + messages
      if not batch:
        return 0
      if self._clock() < self._down_until:
        self._keep(batch)
        return 0
      sent = 0
      for index, message in enumerate(batch):
        try:
          self._send(message)
          sent += 1
        except Exception as error:  # pylint: disable=broad-except
          if _is_unroutable(error):
            # Ninguna cola recibe esta clave: falta topología. Reintentar no lo arregla.
            _logger.error('maya messaging: mensaje %s sin destino en %s (%s); se descarta',
                          message.message_id, message.exchange, message.routing_key)
            continue
          self._down_until = self._clock() + self.settings.retry_after
          self._reset()
          _logger.warning('maya messaging: RabbitMQ no responde (%s: %s); %s mensaje(s) pendientes, '
                          'nuevo intento dentro de %ss', type(error).__name__, error,
                          len(batch) - index, int(self.settings.retry_after))
          self._keep(batch[index:])
          break
      return sent
    except Exception:  # pylint: disable=broad-except
      _logger.exception('maya messaging: error inesperado al publicar')
      return 0
    finally:
      self._lock.release()

  def close(self):
    """Cierra la conexión de este proceso (nunca la heredada de un proceso padre)."""
    with self._lock:
      self._reset()

  def pending(self):
    return len(self._pending)

  # ------------------------------------------------------------ internos
  def _check_fork(self):
    pid = self._getpid()
    if self._pid != pid:
      # Conexión heredada del proceso padre (o ninguna todavía): no se usa ni se cierra, el socket es
      # del padre. Los pendientes del padre los envía el padre.
      if self._pid is not None:
        self._pending.clear()
      self._connection = self._channel = None
      self._down_until = 0.0
      self._pid = pid

  def _send(self, message):
    for attempt in (1, 2):
      if self._channel is None or not self._channel.is_open:
        self._reset()
        self._connection, self._channel = self._connect(self.settings)
      try:
        self._channel.basic_publish(
          exchange=message.exchange,
          routing_key=message.routing_key,
          body=message.encoded_body(),
          properties=message.properties(self.settings.app_id),
          mandatory=True,
        )
        return
      except Exception as error:  # pylint: disable=broad-except
        if _is_unroutable(error):
          raise
        # La conexión pudo morir mientras estaba ociosa (reinicio del broker): una vez más con otra
        self._reset()
        if attempt == 2:
          raise

  def _reset(self):
    if self._pid == self._getpid():
      _close_quietly(self._connection)
    self._connection = self._channel = None

  def _take_pending(self):
    taken = []
    while self._pending:
      try:
        taken.append(self._pending.popleft())
      except IndexError:  # otro hilo la vació a la vez
        break
    return taken

  def _keep(self, messages):
    if not messages:
      return
    self._pending.extend(messages)
    overflow = len(self._pending) - self.settings.pending_max
    for _ in range(max(0, overflow)):
      try:
        lost = self._pending.popleft()
      except IndexError:
        break
      _logger.error('maya messaging: cola en memoria llena; se pierde el mensaje %s (%s, %s)',
                    lost.message_id, lost.exchange, lost.routing_key)

  def _after_fork_in_child(self):
    self._lock = threading.Lock()
    self._pending.clear()
    self._connection = self._channel = None
    self._down_until = 0.0
    self._pid = None


# ------------------------------------------------------- publicador del proceso
_publisher = None
_publisher_lock = threading.Lock()


def get_publisher(conf_get=None):
  """Publicador único del proceso (la configuración se lee la primera vez que se usa)."""
  global _publisher  # pylint: disable=global-statement
  if _publisher is None:
    with _publisher_lock:
      if _publisher is None:
        settings = Settings.load(conf_get)
        if not settings.enabled:
          reason = 'falta pika' if pika is None else 'sin RABBITMQ_HOST o RABBITMQ_PASSWORD'
          _logger.info('maya messaging: publicador desactivado (%s)', reason)
        _publisher = AmqpPublisher(settings)
  return _publisher


def _after_fork_in_child():
  global _publisher_lock  # pylint: disable=global-statement
  _publisher_lock = threading.Lock()
  if _publisher is not None:
    _publisher._after_fork_in_child()  # pylint: disable=protected-access


def _flush_at_exit():
  publisher = _publisher
  if publisher is None:
    return
  if publisher.pending():
    publisher.publish([])
  publisher.close()


if hasattr(os, 'register_at_fork'):
  os.register_at_fork(after_in_child=_after_fork_in_child)
atexit.register(_flush_at_exit)
