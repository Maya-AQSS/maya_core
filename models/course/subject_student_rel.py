# -*- coding: utf-8 -*-

from odoo import models, fields


class SubjectStudentRel(models.Model): 
  """
  Se crea como tabla de relación (pivote) entre Subject y Student para dar soporte a un campo intermedio
  """
  _name = 'maya_core.subject_student_rel' 
  _description = 'Relación entre student y subject' 

  subject_id = fields.Many2one('maya_core.subject', required = True)
  student_id = fields.Many2one('maya_core.student', required = True) 

  # ciclo en el que está matriculado
  study_id = fields.Many2one('maya_core.study', required = True)

  # curso escolar
  school_year_id = fields.Many2one('maya_core.school_year', string = 'Curso escolar', ondelete = 'cascade')

  # número que determina los flags asociados al estado del record
  status_flags = fields.Integer(default = 0) 

  subject_name = fields.Char(related='subject_id.name', string='Módulo | Asignatura', store=False)
  subject_code = fields.Char(related='subject_id.code', string='Código', store=False)
  subject_study = fields.Char(related='study_id.code', string='Estudios', store=False)

  _unique_subject_student_rel = models.Constraint('unique(student_id, subject_id, study_id, school_year_id)', 'Sólo puede haber una relación por estudiante, estudio, asignatura y curso escolar.')