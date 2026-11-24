# -*- coding: utf-8 -*-

from odoo import models, fields

class Rol(models.Model):
    """
    Define los posibles roles del profesorado
    """
      
    _name = 'maya_core.rol'
    _description = 'Rol de profesorado'

    _rec_name = 'rol'
    _order = 'team_id, study_id'

    rol = fields.Char('Cargo', size = 6, required = True)
    study_id = fields.Many2one('maya_core.study', string = 'Ciclo')
    team_id = fields.Many2one('maya_core.team', 'Departamento')
    description = fields.Char('Descripción', required = True)
    