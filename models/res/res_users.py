# -*- coding: utf-8 -*-

from odoo import fields, models

class Users(models.Model):
  """
  Ejemplo de herencia de clase
  Herencia del modelo res.users
  Lo que hace es modificar el modelo res.users para incluir el campo maya_employee_id, que
  se añadirá a la tabla res_users de la base de datos
  Ese campo es accesible por cualquier otro módulo
  """
  _inherit = 'res.users'

  maya_employee_id = fields.Many2one('maya_core.employee', string='Empleado', check_company=False)