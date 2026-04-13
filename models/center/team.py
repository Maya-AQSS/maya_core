# -*- coding: utf-8 -*-

from odoo import models, fields,_

class Team(models.Model):
  """
  Define los departamentos didácticos y equipos
  """
      
  _name = 'maya_core.team'
  _description = 'Equipos: Departamentos didácticos y equipos de trabajo'
  _order = 'name'

  name = fields.Char('Nombre', required=True, translate=True)
  abbr = fields.Char('Abreviatura', required=True, size=5 )

  is_departament = fields.Boolean(_('Es un departamento'), default=True, help=_('Indica si el equipo es un departamento o simplemente es una agrupación interna (equipo). Todo el personal debe estar asignado como mínimo a un departamento.'))