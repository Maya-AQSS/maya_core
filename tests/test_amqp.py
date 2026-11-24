# -*- coding: utf-8 -*-
"""
Transporte AMQP (support/amqp.py) con una conexión simulada: no hace falta RabbitMQ.

Corre con los tests de Odoo (--test-tags /maya_core) y también fuera de Odoo, solo con pika:
  python3 -m unittest discover -s tests -p 'test_amqp.py'   (desde la raíz del módulo)
"""
import json
import time
import unittest
import uuid

try:
  from odoo.tests import BaseCase
  from odoo.addons.maya_core.support import amqp
except ImportError:  # fuera de Odoo
  import importlib.util
  import pathlib
  from unittest import TestCase as BaseCase
  _spec = importlib.util.spec_from_file_location(
    'maya_core_amqp', pathlib.Path(__file__).resolve().parents[1] / 'support' / 'amqp.py')
  amqp = importlib.util.module_from_spec(_spec)
  _spec.loader.exec_module(amqp)


class FakeChannel:
  def __init__(self, factory):
    self.factory = factory
    self.is_open = True

  def basic_publish(self, exchange, routing_key, body, properties, mandatory):
    if self.factory.publish_errors:
      error = self.factory.publish_errors.pop(0)
      if error is not None:
        if not amqp._is_unroutable(error):  # pylint: disable=protected-access
          self.is_open = False  # un error de red deja el canal inservible
        raise error
    self.factory.published.append({
      'exchange': exchange, 'routing_key': routing_key, 'body': body,
      'properties': properties, 'mandatory': mandatory, 'connection': self.factory.connections[-1],
    })


class FakeConnection:
  def __init__(self):
    self.is_open = True
    self.closed = False

  def close(self):
    self.is_open = False
    self.closed = True


class FakeFactory:
  """Sustituye a pika.BlockingConnection: cuenta conexiones y guarda lo publicado."""

  def __init__(self):
    self.connections = []
    self.published = []
    self.connect_errors = 0
    self.publish_errors = []

  def __call__(self, settings):
    if self.connect_errors:
      self.connect_errors -= 1
      raise ConnectionRefusedError('RabbitMQ no responde')
    connection = FakeConnection()
    self.connections.append(connection)
    return connection, FakeChannel(self)


class Clock:
  def __init__(self):
    self.now = 1000.0

  def __call__(self):
    return self.now


SETTINGS = amqp.Settings(host='rabbitmq.test', password='secreto', app_id='odoo', retry_after=30.0,
                         pending_max=5)


def message(n=0, exchange='maya.logs', routing_key='odoo.high'):
  return amqp.Message(exchange, routing_key, {'n': n, 'texto': 'adjunto ñ'})


@unittest.skipIf(amqp.pika is None, 'pika no está instalado')
class TestAmqpPublisher(BaseCase):

  def setUp(self):
    super().setUp()
    self.factory = FakeFactory()
    self.clock = Clock()
    self.pid = [100]
    self.publisher = amqp.AmqpPublisher(SETTINGS, connect=self.factory, clock=self.clock,
                                        getpid=lambda: self.pid[0])

  def test_contract_properties(self):
    """Propiedades AMQP obligatorias del estándar (ESTANDAR.md § 5)."""
    msg = message()
    self.assertEqual(self.publisher.publish([msg]), 1)
    sent = self.factory.published[0]
    props = sent['properties']
    self.assertEqual(props.content_type, 'application/json')
    self.assertEqual(props.delivery_mode, 2)
    self.assertEqual(props.message_id, msg.message_id)
    self.assertEqual(str(uuid.UUID(props.message_id)), props.message_id)
    self.assertIsInstance(props.timestamp, int)
    self.assertLess(abs(props.timestamp - time.time()), 5, 'timestamp en segundos, no en milisegundos')
    self.assertEqual(props.app_id, 'odoo')
    self.assertEqual(props.headers, {'x-maya-schema-version': '1'})
    self.assertTrue(sent['mandatory'])
    self.assertEqual(json.loads(sent['body'].decode('utf-8')), {'n': 0, 'texto': 'adjunto ñ'})
    self.assertIn('ñ'.encode('utf-8'), sent['body'])

  def test_connection_is_lazy_and_reused(self):
    self.assertEqual(self.factory.connections, [], 'no se conecta al crear el publicador')
    self.assertEqual(self.publisher.publish([message(1), message(2)]), 2)
    self.assertEqual(self.publisher.publish([message(3)]), 1)
    self.assertEqual(len(self.factory.connections), 1, 'una sola conexión por proceso')

  def test_reconnects_once_when_connection_died(self):
    self.publisher.publish([message(1)])
    first = self.factory.connections[0]
    self.factory.publish_errors = [ConnectionResetError('el broker se reinició')]
    self.assertEqual(self.publisher.publish([message(2)]), 1)
    self.assertEqual(len(self.factory.connections), 2)
    self.assertTrue(first.closed)
    self.assertEqual(self.factory.published[-1]['connection'], self.factory.connections[1])

  def test_broker_down_keeps_messages_and_waits(self):
    self.factory.connect_errors = 1
    self.assertEqual(self.publisher.publish([message(1)]), 0)
    self.assertEqual(self.publisher.pending(), 1)
    # Dentro de la espera no se intenta conectar (no se bloquea cada petición)
    self.clock.now += 10
    self.assertEqual(self.publisher.publish([message(2)]), 0)
    self.assertEqual(self.factory.connections, [])
    self.assertEqual(self.publisher.pending(), 2)
    # Pasada la espera, salen los pendientes en orden y después el nuevo
    self.clock.now += 30
    self.assertEqual(self.publisher.publish([message(3)]), 3)
    self.assertEqual([json.loads(p['body'])['n'] for p in self.factory.published], [1, 2, 3])
    self.assertEqual(self.publisher.pending(), 0)

  def test_pending_messages_are_bounded(self):
    self.factory.connect_errors = 1
    with self.assertLogs(amqp._logger.name, level='ERROR'):  # pylint: disable=protected-access
      self.publisher.publish([message(n) for n in range(8)])
    self.assertEqual(self.publisher.pending(), SETTINGS.pending_max)
    self.clock.now += 31
    self.publisher.publish([])
    self.assertEqual([json.loads(p['body'])['n'] for p in self.factory.published], [3, 4, 5, 6, 7],
                     'se pierden los más antiguos')

  def test_fork_does_not_reuse_parent_connection(self):
    self.publisher.publish([message(1)])
    parent = self.factory.connections[0]
    self.pid[0] = 200  # proceso hijo (worker de Odoo)
    self.assertEqual(self.publisher.publish([message(2)]), 1)
    self.assertEqual(len(self.factory.connections), 2)
    self.assertFalse(parent.closed, 'la conexión del padre no se cierra desde el hijo')

  def test_after_fork_hook_resets_state(self):
    self.factory.connect_errors = 1
    self.publisher.publish([message(1)])
    self.publisher._after_fork_in_child()  # pylint: disable=protected-access
    self.assertEqual(self.publisher.pending(), 0, 'los pendientes del padre los envía el padre')
    self.assertEqual(self.publisher.publish([message(2)]), 1, 'el hijo no hereda la espera')

  def test_unroutable_message_is_dropped(self):
    self.factory.publish_errors = [amqp.pika.exceptions.UnroutableError([])]
    with self.assertLogs(amqp._logger.name, level='ERROR'):  # pylint: disable=protected-access
      self.assertEqual(self.publisher.publish([message(1), message(2)]), 1)
    self.assertEqual(self.publisher.pending(), 0)
    self.assertEqual(json.loads(self.factory.published[0]['body'])['n'], 2)

  def test_disabled_without_host_or_password(self):
    for settings in (amqp.Settings(host='', password='x'), amqp.Settings(host='h', password='')):
      publisher = amqp.AmqpPublisher(settings, connect=self.factory)
      self.assertEqual(publisher.publish([message()]), 0)
    self.assertEqual(self.factory.connections, [])

  def test_never_raises(self):
    def broken(settings):
      raise TypeError('fallo inesperado')
    publisher = amqp.AmqpPublisher(SETTINGS, connect=broken, clock=self.clock)
    with self.assertLogs(amqp._logger.name, level='WARNING'):  # pylint: disable=protected-access
      self.assertEqual(publisher.publish([message()]), 0)

  def test_close_only_own_connection(self):
    self.publisher.publish([message(1)])
    self.pid[0] = 200
    self.publisher.close()
    self.assertFalse(self.factory.connections[0].closed)


class TestSettings(BaseCase):

  def test_precedence_env_then_conf_then_default(self):
    conf = {'maya_rabbitmq_host': 'conf-host', 'maya_rabbitmq_vhost': '/conf',
            'maya_rabbitmq_password': ' conf secreto ', 'maya_rabbitmq_port': '5673'}
    env = {'RABBITMQ_HOST': 'env-host', 'RABBITMQ_PORT': ''}
    settings = amqp.Settings.load(conf.get, environ=env)
    self.assertEqual(settings.host, 'env-host')
    self.assertEqual(settings.vhost, '/conf')
    self.assertEqual(settings.port, 5673)
    self.assertEqual(settings.user, 'odoo')
    self.assertEqual(settings.app_id, 'odoo')
    self.assertEqual(settings.password, ' conf secreto ', 'la contraseña no se recorta')
    self.assertNotIn('secreto', repr(settings))

  def test_defaults_disable_publisher(self):
    settings = amqp.Settings.load(lambda key: None, environ={})
    self.assertEqual(settings.vhost, '/maya')
    self.assertEqual(settings.port, 5672)
    self.assertFalse(settings.enabled)


if __name__ == '__main__':
  unittest.main()
