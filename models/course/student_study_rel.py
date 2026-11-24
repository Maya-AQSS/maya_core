# -*- coding: utf-8 -*-

from odoo import models, fields, api

class StudentStudyRel(models.Model):
  """
  Se crea como tabla de relación (pivote) entre Student y Study para dar soporte a un campo 
  intermedio (group)
  """
  _name = 'maya_core.student_study_rel'
  _description = 'Relación entre estudiantes y estudios'
  _rec_name = 'short_description'

  student_id = fields.Many2one(
    'maya_core.student', 
    string='Estudiante', 
    required=True, 
    ondelete='cascade'
  )
  study_id = fields.Many2one(
    'maya_core.study', 
    string='Estudio', 
    required=True, 
    ondelete='cascade'
  )

  group = fields.Char(string='Grupo')

  # Fechas de matrícula y baja
  enrollment_date = fields.Date(
    string='Fecha de matrícula', 
    default=fields.Date.context_today
  )
  unenrollment_date = fields.Date(string='Fecha de baja')

  # Campo activo calculado en función de la fecha de baja
  active = fields.Boolean(
    string='Activo', 
    compute='_compute_active', 
    store=True, 
    default=True
  )
  
  study_name = fields.Char(related='study_id.name', string='Curso', store=False)
  study_teaching = fields.Many2one(related='study_id.company_id', string='Enseñanza', store=False)

  school_year_id = fields.Many2one('maya_core.school_year', string = 'Curso escolar', ondelete = 'cascade')

  short_description = fields.Char(string = 'Descripción corta', compute = '_compute_short_description')


  # Constraints para evitar duplicados (un estudiante solo puede estar
  # una vez en el mismo curso)
  _unique_student_study = models.Constraint('unique(student_id, study_id, school_year_id)', 'Este estudiante ya está matriculado en este curso a este estudio.')

  @api.depends('unenrollment_date')
  def _compute_active(self):
    for record in self:
      # Si tiene fecha de baja asignada, el alumno pasa a estar inactivo
      record.active = not bool(record.unenrollment_date)

  @api.depends('study_id', 'group')
  def _compute_short_description(self):
    for record in self:
      record.short_description = f"{record.study_id.name} ({record.group})"
