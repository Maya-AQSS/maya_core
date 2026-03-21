# -*- coding: utf-8 -*-

from odoo import models, fields,_

class Departament(models.Model):
  """
  Define los departamentos didácticos y equipos
  """
      
  _name = 'maya_core.departament'
  _description = 'Departamento didácticos y equipos de trabajo'
  _order = 'name'

  name = fields.Char('Departamento', required=True, translate=True)
  abbr = fields.Char('Abreviatura', required=True, size=5 )

  primary = fields.Boolean(_('Primer nivel'), default=True, help=_('Indica si el departamento es de carácter didáctico (primer nivel) o simplemente es una agrupación interna (equipo). Todo el personal debe estar asignado a un departamento de primer nivel.'))