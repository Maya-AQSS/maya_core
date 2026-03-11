# -*- coding: utf-8 -*-

from odoo import models, fields

class Departament(models.Model):
  """
  Define los departamentos didácticos
  """
      
  _name = 'maya_core.departament'
  _description = 'Departamento didáctico'

  name = fields.Char('Departamento', required=True, translate=True)
  abbr = fields.Char('Abreviatura', required=True, size=5 )
  