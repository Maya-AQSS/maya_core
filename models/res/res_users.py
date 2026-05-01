# -*- coding: utf-8 -*-

from odoo import fields, api, models, _

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
  
  surname = fields.Char(string = _('Apellidos'), required = True)
  employee_info = fields.Char(string = _('Nombre completo'), compute = '_compute_full_employee_info', store=False)

  keycloak_user_id = fields.Char(string='Keycloak User ID')

  @api.depends('name', 'surname')
  def _compute_full_employee_info(self):
    for record in self:
      if record.surname != False and record.name != False:
        record.employee_info = f"{record.surname}, {record.name}"
      else: 
        record.employee_info = False    