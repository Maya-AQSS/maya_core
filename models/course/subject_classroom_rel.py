# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class SubjectClassroomRel(models.Model): 
  """
  Se crea como tabla de relación (pivote) entre Subject y Classroom para dar soporte a un campo 
  intermedio (study_id)
  """
  _name = 'maya_core.subject_classroom_rel' 
  _description = 'Relación entre classroom y subject' 
  _rec_name = 'subject_and_study'

  classroom_id = fields.Many2one('maya_core.classroom', required = True, string = 'Aula virtual') 
  subject_id = fields.Many2one('maya_core.subject', required = True, string = 'Módulo') 

  # estudio de la asignatura en el que está asociada el aula
  study_id = fields.Many2one('maya_core.study', required = True, string = 'Ciclo')

  subject_and_study = fields.Char(compute = '_compute_subject_and_study', string = _('Asignatura (Estudio)'))

  _sql_constraints = [ 
    ('unique_subject_classroom_rel', 'unique(classroom_id, subject_id, study_id)', 
       'Sólo puede haber una relación por aula, ciclo y asignatura.'),
  ]

  @api.depends('study_id','subject_id')
  def _compute_subject_and_study(self):
    for record in self:
      if record.subject_id.name == False or record.study_id.abbr == False:
        record.subject_and_study = ''
      else:
        record.subject_and_study = f'{record.subject_id.name} ({record.study_id.abbr})'

  @api.onchange('subject_id')
  def change_subject(self):
    self.ensure_one()
    if self.subject_id.studies_ids != False:
      allow_studies = [study.id for study in self.subject_id.studies_ids]
      return {'domain': { 'study_id': [('id','in', allow_studies)]}}