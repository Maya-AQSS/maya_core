from odoo import api, models, fields

class Subject(models.Model):
  """
  Define una asignatura (módulo en ciclos formativos)
  """
    
  _name = 'maya_core.subject'
  _description = 'Asignatura'

  abbr = fields.Char(size = 8, required = True, translate = True, string = "Abreviatura")
  code = fields.Char(size = 11, required = True, string = "Código")
  name = fields.Char(required = True, translate = True, string = "Nombre")
  year = fields.Selection([('1', '1º'), ('2', '2º')], required = True, default = '1', string = "Curso")

  optional = fields.Boolean(default = False, string = "Optativa")
  
  # tutorias
  group_tutoring_hours = fields.Integer(default = 2, string = "Horas de tutorías colectivas", help="Número de horas de tutoría colectiva semanal para esta asignatura.")
  individual_tutoring_hours = fields.Integer(default = 2, string = "Horas de tutorías colectivas", help="Número de horas de tutoría colectiva semanal para esta asignatura.")

  total_hours = fields.Integer(default = 100, string="Horas totales", help="Número total de horas para esta asignatura.")
  week_hours = fields.Integer(default = 2, string="Horas semanales", help="Número de horas semanales para esta asignatura (según currículo).")
  week_hours_teacher = fields.Integer(default = 2, string="Horas semanales profesor", help="Número de horas semanales para el profesor.")

  studies_ids = fields.Many2many('maya_core.study', string='Estudios', help='Estudios en los que se imparte')

  employees_ids = fields.One2many('maya_core.subject_employee_rel', 'subject_id', string = 'Profesorado') 

  # Aulas virtuales asigndas a este módulo
  classrooms_ids = fields.One2many('maya_core.subject_classroom_rel', 'subject_id', string = 'Aulas virtuales')


  def get_classroom_by_study_id(self, study):
    """
    Devuelve el aula virtual asociada a este módulo para un ciclo determinado
    """
    self.ensure_one()
     
    return self.classrooms_ids.filtered(lambda t: t.study_id.id == study.id)['classroom_id']