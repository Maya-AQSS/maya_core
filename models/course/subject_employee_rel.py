# -*- coding: utf-8 -*-

from odoo import models, fields

class SubjectEmployeeRel(models.Model): 
  """
  Se crea como tabla de relación (pivote) entre Subject y Employee para dar soporte a un campo intermedio
  Sólo tiene sentido cuando el empleado sea un profesor
  """
  _name = 'maya_core.subject_employee_rel' 
  _description = 'Relación entre employee y subject' 

  subject_id = fields.Many2one('maya_core.subject', required = True)
  employee_id = fields.Many2one('maya_core.employee', required = True) 

  # estudio en el que imparte la asignatura
  study_id = fields.Many2one('maya_core.study', required = True)

  _unique_subject_employee_rel = models.Constraint('unique(employee_id, subject_id, study_id)', 'Sólo puede haber una relación por empleado, asignatura y estudio.')