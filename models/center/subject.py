from odoo import api, models, fields, _

class Subject(models.Model):
  """
  Define una asignatura (módulo en ciclos formativos)
  """
    
  _name = 'maya_core.subject'
  _description = 'Asignatura'

  abbr = fields.Char(size = 8, required = True, translate = True, string = "Abreviatura")
  code = fields.Char(size = 11, required = True, string = "Código")
  name = fields.Char(required = True, translate = True, string = _("Nombre"))
  year = fields.Selection([('1', '1º'), ('2', '2º')], required = True, default = '1', string = _("Curso"))

  optional = fields.Boolean(default = False, string = _("Optativa"))
  
  # tutorias
  group_tutoring_hours = fields.Integer(default = 2, string = _("Horas de tutorías colectivas"), help=_("Número de horas de tutoría colectiva semanal para esta asignatura."))
  individual_tutoring_hours = fields.Integer(default = 2, string = _("Horas de tutorías colectivas"), help=_("Número de horas de tutoría colectiva semanal para esta asignatura."))

  total_hours = fields.Integer(default = 100, string=_("Horas totales"), help=_("Número total de horas para esta asignatura."))
  week_hours = fields.Integer(default = 2, string=_("Horas semanales"), help=_("Número de horas semanales para esta asignatura (según currículo)."))
  week_hours_teacher = fields.Integer(default = 2, string=_("Horas semanales profesor"), help=_("Número de horas semanales para el profesor."))
  
  studies_ids = fields.Many2many('maya_core.study', string = _('Estudios'), help = _('Estudios en los que se imparte'))

  employees_ids = fields.One2many('maya_core.subject_employee_rel', 'subject_id', string = _('Profesorado')) 

  # Aulas virtuales asigndas a este módulo
  classrooms_ids = fields.One2many('maya_core.subject_classroom_rel', 'subject_id', string = _('Aulas virtuales'))


  def get_classroom_by_study_id(self, study):
    """
    Devuelve el aula virtual asociada a este módulo para un ciclo determinado
    """
    self.ensure_one()
     
    return self.classrooms_ids.filtered(lambda t: t.study_id.id == study.id)['classroom_id']