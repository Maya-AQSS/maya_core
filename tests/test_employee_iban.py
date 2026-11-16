# -*- coding: utf-8 -*-
"""
IBAN del empleado: _check_iban solo valida y el valor se normaliza al crear y al escribir. Antes la
restricción reescribía el campo y, al reescribirlo, volvía a lanzarse sin fin.

  odoo -d <bd de pruebas> -i maya_core --test-tags /maya_core --stop-after-init
"""
from odoo.exceptions import ValidationError
from odoo.fields import Command
from odoo.tests import TransactionCase

# Ejemplos válidos del registro IBAN: España (24 caracteres) y Malta (31: agrupado no cabe en el campo)
IBAN_ES = 'ES9121000418450200051332'
IBAN_ES_AGRUPADO = 'ES91 2100 0418 4502 0005 1332'
IBAN_MT = 'MT84MALT011000012345MTLCAST001S'


class TestEmployeeIban(TransactionCase):

  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    cls.team = cls.env['maya_core.team'].create({'name': 'Equipo IBAN', 'abbr': 'EIB'})

  def _employee(self, login, **vals):
    user = self.env['res.users'].create({'name': 'Empleado', 'surname': 'IBAN', 'login': login})
    return self.env['maya_core.employee'].create(dict(
      vals, user_ids=[Command.link(user.id)], team_ids=[Command.set(self.team.ids)]))

  def test_create_normalizes_and_groups(self):
    employee = self._employee('iban.alta@example.com', iban=IBAN_ES.lower())
    self.assertEqual(employee.iban, IBAN_ES_AGRUPADO)

  def test_write_normalizes_spaces_and_dashes(self):
    employee = self._employee('iban.cambio@example.com')
    employee.write({'iban': ' es91-2100-0418-4502 0005 1332 '})
    self.assertEqual(employee.iban, IBAN_ES_AGRUPADO)
    # Escribir otro campo no toca el IBAN
    employee.write({'phone_extension': '1234'})
    self.assertEqual(employee.iban, IBAN_ES_AGRUPADO)

  def test_long_iban_is_kept_compact(self):
    """Agrupado ocuparía 38 caracteres y el campo admite 34: se guarda entero y sin espacios."""
    employee = self._employee('iban.largo@example.com', iban=IBAN_MT)
    self.assertEqual(employee.iban, IBAN_MT)

  def test_invalid_checksum_is_rejected(self):
    with self.assertRaises(ValidationError):
      self._employee('iban.malo@example.com', iban='ES0021000418450200051332')

  def test_invalid_length_and_characters_are_rejected(self):
    employee = self._employee('iban.corto@example.com')
    with self.assertRaises(ValidationError):
      employee.write({'iban': 'ES91 2100'})
    with self.assertRaises(ValidationError):
      employee.write({'iban': 'ES91 2100 0418 4502 0005 133*'})

  def test_iban_can_be_cleared(self):
    employee = self._employee('iban.borrar@example.com', iban=IBAN_ES)
    employee.write({'iban': False})
    self.assertFalse(employee.iban)
