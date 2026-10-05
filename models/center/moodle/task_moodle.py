# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class TaskMoodle(models.Model):
  """
  Define una tarea de moodle que comunica con Maya. No permite que en una misma aula virtual
  existan dos tareas con la misma key
  """

  _name = 'maya_core.task_moodle'
  _description = 'Tarea de Moodle'

  moodle_id = fields.Integer('Identificador Moodle', required = True)
  key = fields.Char('Clave', required = True, help = 'Clave de búsqueda. Tiene que ser única para cada tarea y aula')
  classroom_id = fields.Many2one('maya_core.classroom') 
  description = fields.Char('Descripción de la tarea')
  study_abbr = fields.Char(string = 'Estudio', size = 5)
  
  _sql_constraints = [ 
    ('unique_key', '', ''),
    ('unique_moodle_id', '', ''),
  ]

  _unique_key = models.Constraint('unique(key, classroom_id)', 'La clave de búsqueda tiene que ser única para cada tarea y aula.')
  _unique_moodle_id = models.Constraint('unique(moodle_id)', 'El identificador de moodle tiene que ser único.')
  
    