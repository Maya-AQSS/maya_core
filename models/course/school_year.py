# -*- coding: utf-8 -*-

import datetime
from odoo import api, models, fields, _
from odoo.exceptions import ValidationError, AccessDenied

from datetime import date
import toolz
import logging

_logger = logging.getLogger(__name__)

class SchoolYear(models.Model):
  """
  Define información del curso escolar
  """
      
  _name = 'maya_core.school_year'
  _description = 'Curso escolar'

  # hay un curso escolar por cada enseñanza
  company_id = fields.Many2one(
      'res.company', 
      string='Tipo de enseñanza',
      required=True, 
      default=lambda self: self.env.company,
      index=True
  )

  name = fields.Char(readonly = True, compute = '_compute_name', string = 'Curso')
  state = fields.Selection([
      ('0', 'Borrador'),
      ('1', 'En curso'),
      ('2', 'Finalizado')
      ], string = 'Estado del curso', default = '0')
  
  date_init = fields.Date(string = 'Fecha de inicio oficial')

  # estructura de datos con las fechas 
  # dates = { 'init_lective': { 'date': '', 'desc': 'Inicio clases', 'type': 'G'}}

  # inicio real de las clases
  date_init_lective = fields.Date(string = 'Fecha de inicio real', compute = '_compute_date_init_lective', readonly = False, store = True)
  # jornadas de bienvenida
  date_welcome_day = fields.Date(string = 'Jornadas de bienvenida', compute = '_compute_welcome_day', store = True)


  ######################
  #  SEGUNDO CURSO
  ######################
  # inicio primera evaluación
  date_1term2_ini = fields.Date(string = 'Inicio primera evaluación', compute = '_compute_1term2_ini') 
  # fin de las clases de la primera evaluación de segundo
  date_1term2_end = fields.Date(string = 'Fin clases primera evaluación', compute = '_compute_1term2_end', readonly = False, store = True) 
  # inicio examenes 1 evaluación de segundo. En caso de readonly True hay que forzar su grabación en el XML con force_save
  date_1term2_exam_ini = fields.Date(string = 'Inicio exámenes primera evaluación', compute = '_compute_1term2_exam_ini', readonly = False, store = True) 
  # fin exámenes 1 evaluación de segundo
  date_1term2_exam_end = fields.Date(string = 'Fin exámenes primera evaluación', compute = '_compute_1term2_exam_end', store = True) 
  # duración primera evaluación segundo
  duration_1term2 = fields.Integer(string = 'Duración (semanas)', compute = '_compute_duration_1term2')
  # inicio segunda evaluación
  date_2term2_ini = fields.Date(string = 'Inicio segunda evaluación', compute = '_compute_2term2_ini', store = True) 
  # fin de las clases de la segunda evaluación de segundo
  date_2term2_end = fields.Date(string = 'Fin clases segunda evaluación', compute = '_compute_2term2_end', readonly = False, store = True) 
  # inicio examenes 2 evaluación de segundo
  date_2term2_exam_ini = fields.Date(string = 'Inicio exámenes segunda evaluación', compute = '_compute_2term2_exam_ini', readonly = False, store = True) 
  # fin exámenes 2 evaluación de segundo
  date_2term2_exam_end = fields.Date(string = 'Fin exámenes segunda evaluación', compute = '_compute_2term2_exam_end', store = True) 
  # duración segunda evaluación segundo
  duration_2term2 = fields.Integer(string = 'Duración (semanas)', compute = '_compute_duration_2term2')
  # inicio examenes ordinaria de segundo
  date_ord2_exam_ini = fields.Date(string = 'Inicio exámenes ordinaria', compute = '_compute_ord2_exam_ini', readonly = False, store = True) 
  # fin exámenes ordinaria de segundo
  date_ord2_exam_end = fields.Date(string = 'Fin exámenes ordinaria', compute = '_compute_ord2_exam_end', store = True) 
  # inicio examenes extraordinaria de segundo
  date_extraord2_exam_ini = fields.Date(string = 'Inicio exámenes extraordinaria', compute = '_compute_extraord2_exam_ini', readonly = False, store = True) 
  # fin exámenes extraordinaria de segundo
  date_extraord2_exam_end = fields.Date(string = 'Fin exámenes extraordinaria', compute = '_compute_extraord2_exam_end', store = True) 
  # anulación de matrícula
  date_cancellation2 = fields.Date(string = 'Fin anulación de matrícula', compute = '_compute_cancellation2') 
  # renuncia convocatoria ordinaria
  date_waiver_ord2 = fields.Date(string = 'Fin renuncia convocatoria ordinaria', compute = '_compute_waiver_ord2') 
  # renuncia convocatoria extraordinaria
  date_waiver_extraord2 = fields.Date(string = 'Fin renuncia convocatoria extraordinaria', compute = '_compute_waiver_extraord2') 

  # PRIMERO
  # fin de las clases de la primera evaluación de primero
  date_1term1_end = fields.Date(string = 'Fin clases primera evaluación', compute = '_compute_1term1_end', readonly = False, store = True) 
  # inicio examenes 1 evaluación de segundo. En caso de readonly True hay que forzar su grabación en el XML con force_save
  date_1term1_exam_ini = fields.Date(string = 'Inicio exámenes primera evaluación', compute = '_compute_1term1_exam_ini', readonly = False, store = True) 
  # fin exámenes 1 evaluación de primero
  date_1term1_exam_end = fields.Date(string = 'Fin exámenes primera evaluación', compute = '_compute_1term1_exam_end', store = True) 
  # duración primera evaluación primero
  duration_1term1 = fields.Integer(string = 'Duración (semanas)', compute = '_compute_duration_1term1')
  # inicio segunda evaluación primero
  date_2term1_ini = fields.Date(string = 'Inicio segunda evaluación', compute = '_compute_2term1_ini', store = True) 
  # fin de las clases de la segunda evaluación de primero
  date_2term1_end = fields.Date(string = 'Fin clases segunda evaluación', compute = '_compute_2term1_end', readonly = False, store = True) 
  # inicio examenes 2 evaluación de primero
  date_2term1_exam_ini = fields.Date(string = 'Inicio exámenes segunda evaluación', compute = '_compute_2term1_exam_ini', readonly = False, store = True) 
  # fin exámenes 2 evaluación de primero
  date_2term1_exam_end = fields.Date(string = 'Fin exámenes segunda evaluación', compute = '_compute_2term1_exam_end', store = True) 
  # duración segunda evaluación primero
  duration_2term1 = fields.Integer(string = 'Duración (semanas)', compute = '_compute_duration_2term1')
  # inicio examenes ordinaria de primero
  date_ord1_exam_ini = fields.Date(string = 'Inicio exámenes ordinaria', compute = '_compute_ord1_exam_ini', readonly = False, store = True) 
  # fin exámenes ordinaria de primero
  date_ord1_exam_end = fields.Date(string = 'Fin exámenes ordinaria', compute = '_compute_ord1_exam_end', store = True) 
  # inicio exámenes extraordinaria de primero
  date_extraord1_exam_ini = fields.Date(string = 'Inicio exámenes extraordinaria', compute = '_compute_extraord1_exam_ini', readonly = False, store = True) 
  # fin exámenes extraordinaria de segundo
  date_extraord1_exam_end = fields.Date(string = 'Fin exámenes extraordinaria', compute = '_compute_extraord1_exam_end', store = True) 
  # anulación de matrícula primero
  date_cancellation1 = fields.Date(string = 'Fin anulación de matrícula', compute = '_compute_cancellation1') 
  # renuncia convocatoria ordinaria primero
  date_waiver_ord1 = fields.Date(string = 'Fin renuncia convocatoria ordinaria', compute = '_compute_waiver_ord1') 
  # renuncia convocatoria extraordinaria primero
  date_waiver_extraord1 = fields.Date(string = 'Fin renuncia convocatoria extraordinaria', compute = '_compute_waiver_extraord1') 

  holidays_ids = fields.One2many('maya_core.holiday', 'school_year_id')
  cron_ids = fields.One2many('maya_core.ir.cron', 'school_year_id')

  # report calendario escolar  
  school_calendar_version = fields.Integer(string = 'Versión calendario escolar', default = 1, store = True, readonly = True)
  school_calendar_update_keys = ['init_lective', 'date_init_lective', 'date_welcome_day', 'date_1term2_end', 
    'date_1term2_exam_ini', 'date_1term2_exam_end', 'date_2term2_ini', 'date_2term2_end', 'date_ord2_exam_ini',
    'date_ord2_exam_end','date_extraord2_exam_ini', 'date_extraord2_exam_end', 
    'date_1term1_end', 'date_1term1_exam_ini', 'date_1term1_exam_end', 'date_2term1_ini', 'date_2term1_end', 
    'date_ord1_exam_ini', 'date_ord1_exam_end','date_extraord1_exam_ini', 'date_extraord1_exam_end', 'state']

  # TODO: constraints para que se mantenga el orden cronológico de las fechas
  
  @api.model_create_multi
  def create(self, vals_list):
    """
    Sobreescritura de create:
    - Inicializa school_calendar_version a 1.
    - Valida que no exista ya un curso 'en curso' para la misma compañía.
    """

    if self.env.company == self.env.ref('base.main_company'):
      raise ValidationError("No se pueden crear cursos escolares en el tipo de estudios padre. Por favor, cambia a otro tipo de estudios.")
    
    for vals in vals_list:
      if not vals.get('date_init'):
        raise ValidationError("No se puede crear un curso escolar si no se define una fecha de inicio.")

    for vals in vals_list:
      vals['school_calendar_version'] = 1
    records = super().create(vals_list)
    # Disparamos la constraint también en create para cursos que ya nacen activos
    records._check_one_active_per_company()
    return records
  

  def write(self, vals):
    """
    Sobreescritura de write:
    - Solo el administrador puede editar.
    - Incrementa school_calendar_version cuando cambian fechas relevantes en un curso activo.
    - Valida que no queden dos cursos activos en la misma compañía.
    """
    """ desactivacion temporal
    if not self.env.user.has_group('maya_core.group_ROOT'):
      raise AccessDenied(_('Sólo el administrador puede editar un curso')) """

    # Incrementar versión del calendario si cambian campos relevantes
    if any(key in vals for key in self.school_calendar_update_keys):
      for record in self:
        if record.state == '1' or vals.get('state') == '1':
          vals['school_calendar_version'] = record.school_calendar_version + 1
          break  # todos los registros del recordset se actualizan con los mismos vals

    result = super().write(vals)

    # Si se ha cambiado el estado o la compañía, revalidamos
    if 'state' in vals or 'company_id' in vals:
      self._check_one_active_per_company()

    return result


  # ###########
  # GENERALES
  # ###########

  @api.constrains('state', 'company_id')
  def _check_one_active_per_company(self):
    """
    Solo puede haber un curso escolar con state='1' (En curso) por compañía.
    """
    for record in self:
      if record.state != '1':
        continue
      duplicates = self.search([
        ('state', '=', '1'),
        ('company_id', '=', record.company_id.id),
        ('id', '!=', record.id),
      ])
      if duplicates:
        raise ValidationError(
          _('Ya existe un curso escolar en curso para la compañía "%s". '
            'Finaliza el curso actual antes de activar uno nuevo.')
          % record.company_id.name
        )

  # la fecha de inicio no puede ser fin de semana
  @api.constrains('date_init')
  def _check_date_init(self):
    for record in self:
      if record.date_init.weekday() == 5 or record.date_init.weekday() == 6:
        raise ValidationError('La fecha de inicio no puede ser fin de semana')

  @api.depends('date_init')
  def _compute_name(self):
    for record in self:
      if record.date_init == False:
        record.name = ''
      else:
        record.name = '%s/%s' % (record.date_init.year, record.date_init.year + 1)

  @api.depends('date_init')
  def _compute_date_init_lective(self):
    for record in self:
      if record.date_init == False:
        record.date_init_lective = ''
      elif record.date_init.weekday() >= 2:
        record.date_init_lective = record.date_init + datetime.timedelta(days = 7 - record.date_init.weekday())
      else:
        record.date_init_lective = record.date_init

  @api.constrains('date_init_lective')
  def _check_date_init_lective(self):
    for record in self:
      if record.date_init_lective.weekday() >= 4:
        raise ValidationError('La fecha de inicio lectiva no puede ser ni viernes ni fin de semana')

  @api.depends('date_init_lective')
  def _compute_welcome_day(self):
    for record in self:
      if record.date_init_lective == False:
        record.date_welcome_day = ''
      else: 
        record.date_welcome_day = record.date_init_lective - datetime.timedelta(days = 4)

  # ###########
  # SEGUNDO
  # ###########

  @api.depends('date_init_lective')
  def _compute_1term2_ini(self):
    for record in self:
      if record.date_init_lective == False:
        record.date_1term2_ini = ''
      else: 
        record.date_1term2_ini = record.date_init_lective

  @api.depends('date_init_lective')
  def _compute_1term2_end(self):
    for record in self:
      if record.date_init_lective == False:
        record.date_1term2_end = ''
      else: 
        record.date_1term2_end = record.date_init_lective + datetime.timedelta(weeks=9) + datetime.timedelta(days = 4 - record.date_init_lective.weekday())

  @api.constrains('date_1term2_end')
  def _check_date_1term2_end(self):
    for record in self:
      if record.date_1term2_end.weekday() == 5 or record.date_1term2_end.weekday() == 6:
        raise ValidationError('La fecha de fin de evaluación no puede ser fin de semana')

  @api.depends('date_1term2_end','date_init_lective')    
  def _compute_duration_1term2(self):
    for record in self:
      if record.date_1term2_end != False and record.date_init_lective != False:
        record.duration_1term2 = (record.date_1term2_end - record.date_init_lective).days // 7 + 1
      else:
        record.duration_1term2 = 0
             
  @api.depends('date_1term2_end', 'holidays_ids.date')
  def _compute_1term2_exam_ini(self):
    for record in self:
      if record.date_1term2_end == False:
        record.date_1term2_exam_ini = ''
      else: 
        record.date_1term2_exam_ini = record.date_1term2_end + datetime.timedelta(days=3)

      # obtener los festivos del día de la constitucion e inmaculada
      constitucion_holiday = next((holiday for holiday in record.holidays_ids if holiday.key == 'constitucion'), None)
      inma_holiday = next((holiday for holiday in record.holidays_ids if holiday.key == 'inmaculada'), None)
   
      if constitucion_holiday == None or inma_holiday == None:
        continue
      # si en la semana de exámenes está el día 6/12 o el 8/12, retraso los exámenes una semana
      elif (constitucion_holiday.date >= record.date_1term2_exam_ini and constitucion_holiday.date < record.date_1term2_exam_end) or \
        (inma_holiday.date >= record.date_1term2_exam_ini and inma_holiday.date < record.date_1term2_exam_end):
        record.date_1term2_exam_ini = record.date_1term2_exam_ini + datetime.timedelta(weeks = 1)
        record.date_1term2_exam_end = record.date_1term2_exam_end + datetime.timedelta(weeks = 1)
        record.date_1term2_end = record.date_1term2_end + datetime.timedelta(weeks = 1)

  @api.constrains('date_1term2_exam_ini')
  def _check_date_1term2_exam_ini(self):
    for record in self:
      if record.date_1term2_exam_ini.weekday() != 0:
        raise ValidationError('La fecha de inicio de exámenes tiene que ser un lunes')
  
  @api.depends('date_1term2_exam_ini')
  def _compute_1term2_exam_end(self):
    for record in self:
      if record.date_1term2_exam_ini == False:
        record.date_1term2_exam_end = ''
      else: 
        record.date_1term2_exam_end = record.date_1term2_exam_ini + datetime.timedelta(days=4)

  @api.depends('date_1term2_exam_end')
  def _compute_2term2_ini(self):
    for record in self:
      if record.date_1term2_exam_end == False:
        record.date_2term2_ini = ''
      else: 
        record.date_2term2_ini = record.date_1term2_exam_end + datetime.timedelta(days = 3)

  @api.depends('date_2term2_ini', 'duration_1term2')
  def _compute_2term2_end(self):
    for record in self:
      if record.date_2term2_ini == False:
        record.date_2term2_end = ''
      else:
        # 20 + 2 (ya que Navidad al final son siempre dos semanas no lectivas). 
        # Eso lo ubica al principio de la semana 21, asi que -1 y sumanos para alcanzar el viernes 
        record.date_2term2_end = record.date_2term2_ini + datetime.timedelta(weeks = 21 - record.duration_1term2) + datetime.timedelta(days = 4)
      
  @api.constrains('date_2term2_end')
  def _check_date_2term2_end(self):
    for record in self:
      if record.date_2term2_end.weekday() == 5 or record.date_2term2_end.weekday() == 6:
        raise ValidationError('La fecha de fin de evaluación no puede ser fin de semana')

  @api.depends('date_2term2_end','date_2term2_ini')    
  def _compute_duration_2term2(self):
    for record in self:
      if record.date_2term2_end != False and record.date_2term2_ini != False:
        record.duration_2term2 = (record.date_2term2_end - record.date_2term2_ini).days // 7 + 1 - 2 # - 2 por la dos de navidad 
      else:
        record.duration_2term2 = 0
             
  @api.depends('date_2term2_end')
  def _compute_2term2_exam_ini(self):
    for record in self:
      if record.date_2term2_end == False:
        record.date_2term2_exam_ini = ''
      else: 
        record.date_2term2_exam_ini = record.date_2term2_end + datetime.timedelta(days=3)

  @api.constrains('date_2term2_exam_ini')
  def _check_date_2term2_exam_ini(self):
    for record in self:
      if record.date_2term2_exam_ini != False: 
        if record.date_2term2_exam_ini.weekday() != 0:
          raise ValidationError('La fecha de inicio de exámenes tiene que ser un lunes')
  
  @api.depends('date_2term2_exam_ini')
  def _compute_2term2_exam_end(self):
    for record in self:
      if record.date_2term2_exam_ini == False:
        record.date_2term2_exam_end = ''
      else: 
        record.date_2term2_exam_end = record.date_2term2_exam_ini + datetime.timedelta(days=4)

  @api.depends('date_2term2_exam_ini')
  def _compute_ord2_exam_ini(self):
    for record in self:
      if record.date_2term2_ini == False:
        record.date_ord2_exam_ini = ''
      else: 
        record.date_ord2_exam_ini = record.date_2term2_exam_ini + datetime.timedelta(weeks = 2)

  @api.constrains('date_ord2_exam_ini')
  def _check_date_ord2_exam_ini(self):
    for record in self:
      if record.date_ord2_exam_ini != False: 
        if record.date_ord2_exam_ini.weekday() != 0:
          raise ValidationError('La fecha de inicio de exámenes tiene que ser un lunes')
  
  @api.depends('date_ord2_exam_ini')
  def _compute_ord2_exam_end(self):
    for record in self:
      if record.date_ord2_exam_ini == False:
        record.date_ord2_exam_end = ''
      else: 
        record.date_ord2_exam_end = record.date_ord2_exam_ini + datetime.timedelta(days=4)

  @api.depends('date_2term1_exam_ini')
  def _compute_extraord2_exam_ini(self):
    for record in self:
      if record.date_2term2_ini == False:
        record.date_extraord2_exam_ini = ''
      else: 
        record.date_extraord2_exam_ini = record.date_2term1_exam_ini + datetime.timedelta(weeks = 1)

  @api.constrains('date_extraord2_exam_ini')
  def _check_date_extraord2_exam_ini(self):
    for record in self:
      if record.date_extraord2_exam_ini != False: 
        if record.date_extraord2_exam_ini.weekday() != 0:
          raise ValidationError('La fecha de inicio de exámenes tiene que ser un lunes')
  
  @api.depends('date_extraord2_exam_ini')
  def _compute_extraord2_exam_end(self):
    for record in self:
      if record.date_extraord2_exam_ini == False:
        record.date_extraord2_exam_end = ''
      else: 
        record.date_extraord2_exam_end = record.date_extraord2_exam_ini + datetime.timedelta(days = 4)
  
  @api.depends('date_init')
  def _compute_cancellation2(self):
    for record in self:
      if record.date_init == False:
        record.date_cancellation2 = ''
      else:
        record.date_cancellation2 = datetime.datetime(record.date_init.year, 12, 31)
        
  @api.depends('date_ord2_exam_ini')
  def _compute_waiver_ord2(self):
    for record in self:
      if record.date_ord2_exam_ini == False:
        record.date_waiver_ord2 = ''      
      else:
        record.date_waiver_ord2 = record.date_ord2_exam_ini - datetime.timedelta(days = 10)

  @api.depends('date_extraord2_exam_ini')
  def _compute_waiver_extraord2(self):
    for record in self:
      if record.date_extraord2_exam_ini == False:
        record.date_waiver_extraord2 = ''      
      else:
         record.date_waiver_extraord2 = record.date_extraord2_exam_ini - datetime.timedelta(days = 10)

  # ###########
  # PRIMERO
  # ###########
  @api.depends('date_init_lective', 'date_1term1_exam_ini')
  def _compute_1term1_end(self):
    for record in self:
      if record.date_init_lective == False:
        record.date_1term1_end = ''
      else: 
        # 15 + 2 (2 por las semanas de navidad, -1 por que sumo luego los 4 dias hasta el viernes)
        record.date_1term1_end = record.date_init_lective + datetime.timedelta(weeks = 16) + datetime.timedelta(days = 4 - record.date_init_lective.weekday())
        #record.date_1term1_end = record.date_1term1_end + datetime.timedelta(weeks = 1)

      # obtener los festivos de Navidad
      christmas_holiday = next((holiday for holiday in record.holidays_ids if holiday.key == 'navidad'), None)
      if christmas_holiday == None:
        continue

      if record.date_1term1_exam_ini == False:
         continue

      # si la navidad acaba después de los exámenes 
      # y al menos doy una semana lectiva entre fiestas y examenes
      if (christmas_holiday.date_end.weekday() < 3 and (record.date_1term1_exam_ini - christmas_holiday.date_end).days <= 0) or \
        (christmas_holiday.date_end.weekday() >= 3 and (record.date_1term1_exam_ini - christmas_holiday.date_end).days < 7):
        more_weeks = 0
        if christmas_holiday.date_end.weekday() >= 3 and (record.date_1term1_exam_ini - christmas_holiday.date_end).days <=0:
          more_weeks = (christmas_holiday.date_end - record.date_1term1_exam_ini).days // 7 + 1
        record.date_1term1_exam_ini = record.date_1term1_exam_ini + datetime.timedelta(weeks = 1) + datetime.timedelta(weeks = more_weeks)
        record.date_1term1_exam_end = record.date_1term1_exam_end + datetime.timedelta(weeks = 1) + datetime.timedelta(weeks = more_weeks)
        record.date_1term1_end = record.date_1term1_end + datetime.timedelta(weeks = 1) + datetime.timedelta(weeks = more_weeks)
    
  @api.depends('date_1term1_end', 'holidays_ids.date')
  def _compute_1term1_exam_ini(self):
    for record in self:
      if record.date_1term1_end == False:
        record.date_1term1_exam_ini = ''
      else: 
        record.date_1term1_exam_ini = record.date_1term1_end + datetime.timedelta(days = 3)

        christmas_holiday = next((holiday for holiday in record.holidays_ids if holiday.key == 'navidad'), None)
        if christmas_holiday == None:
          continue

        if (christmas_holiday.date_end.weekday() < 3 and (record.date_1term1_exam_ini - christmas_holiday.date_end).days <= 0) or \
        (christmas_holiday.date_end.weekday() >= 3 and (record.date_1term1_exam_ini - christmas_holiday.date_end).days < 7):
          # en caso de que la fecha de fin de fiestas sea mucho más posterior que la de inicio de exámenes
          more_weeks = 0
          if christmas_holiday.date_end.weekday() >= 3 and (record.date_1term1_exam_ini - christmas_holiday.date_end).days <=0:
            more_weeks = (christmas_holiday.date_end - record.date_1term1_exam_ini).days // 7 + 1

          record.date_1term1_exam_ini = record.date_1term1_exam_ini + datetime.timedelta(weeks = 1 + more_weeks)
          record.date_1term1_end = record.date_1term1_end + datetime.timedelta(weeks = 1 + more_weeks)
  
  @api.constrains('date_1term1_end')
  def _check_date_1term1_end(self):
    for record in self:
      if record.date_1term1_end != False:
        if record.date_1term1_end.weekday() == 5 or record.date_1term1_end.weekday() == 6:
          raise ValidationError('La fecha de fin de evaluación no puede ser fin de semana')

  @api.depends('date_1term1_end','date_init_lective')    
  def _compute_duration_1term1(self):
    for record in self:
      if record.date_1term1_end != False and record.date_init_lective != False:
        record.duration_1term1 = ((record.date_1term1_end - record.date_init_lective).days - 14) // 7 + 1
      else:
        record.duration_1term1 = 0

  @api.constrains('date_1term1_exam_ini')
  def _check_date_1term1_exam_ini(self):
    for record in self:
      if record.date_1term1_exam_ini != False:
        if record.date_1term1_exam_ini.weekday() != 0:
          raise ValidationError('La fecha de inicio de exámenes tiene que ser un lunes')
  
  @api.depends('date_1term1_exam_ini')
  def _compute_1term1_exam_end(self):
    for record in self:
      if record.date_1term1_exam_ini == False:
        record.date_1term1_exam_end = ''
      else: 
        record.date_1term1_exam_end = record.date_1term1_exam_ini + datetime.timedelta(days = 4)
  
  @api.depends('date_1term1_exam_end')
  def _compute_2term1_ini(self):
    for record in self:
      if record.date_1term1_exam_end == False:
        record.date_2term1_ini = ''
      else: 
        record.date_2term1_ini = record.date_1term1_exam_end + datetime.timedelta(days = 3)
        
  @api.depends('date_2term1_ini', 'duration_1term1')
  def _compute_2term1_end(self):
    for record in self:
      if record.date_2term1_ini == False:
        record.date_2term1_end = ''
      else:
        # 30 + 1 (ya que pascua al final es siempre una semana no lectivas) 
        # Eso lo ubica al principio de la semana 31, asi que -1 y sumanos para alcanzar el viernes 
        record.date_2term1_end = record.date_2term1_ini + datetime.timedelta(weeks = 30 - record.duration_1term1) + datetime.timedelta(days = 4)
      
  @api.constrains('date_2term1_end')
  def _check_date_2term1_end(self):
    for record in self:
      if record.date_2term1_end != False:
        if record.date_2term1_end.weekday() == 5 or record.date_2term1_end.weekday() == 6:
          raise ValidationError('La fecha de fin de evaluación no puede ser fin de semana')

  @api.depends('date_2term1_end','date_2term1_ini')
  def _compute_duration_2term1(self):
    for record in self:
      if record.date_2term1_end != False and record.date_2term1_ini != False:
        record.duration_2term1 = (record.date_2term1_end - record.date_2term1_ini).days // 7 + 1 - 1 # - 1 por la dos pascua 
      else:
        record.duration_2term1 = 0
             
  @api.depends('date_2term1_end')
  def _compute_2term1_exam_ini(self):
    for record in self:
      if record.date_2term1_end == False:
        record.date_2term1_exam_ini = ''
      else: 
        record.date_2term1_exam_ini = record.date_2term1_end + datetime.timedelta(days = 3)

  @api.constrains('date_2term1_exam_ini')
  def _check_date_2term1_exam_ini(self):
    for record in self:
      if record.date_2term1_exam_ini != False: 
        if record.date_2term1_exam_ini.weekday() != 0:
          raise ValidationError('La fecha de inicio de exámenes tiene que ser un lunes')
  
  @api.depends('date_2term1_exam_ini')
  def _compute_2term1_exam_end(self):
    for record in self:
      if record.date_2term1_exam_ini == False:
        record.date_2term1_exam_end = ''
      else: 
        record.date_2term1_exam_end = record.date_2term1_exam_ini + datetime.timedelta(days=4)
 
  @api.depends('date_2term1_exam_ini')
  def _compute_ord1_exam_ini(self):
    for record in self:
      if record.date_2term1_ini == False:
        record.date_ord1_exam_ini = ''
      else: 
        record.date_ord1_exam_ini = record.date_2term1_exam_ini + datetime.timedelta(weeks = 3)

  @api.constrains('date_ord1_exam_ini')
  def _check_date_ord1_exam_ini(self):
    for record in self:
      if record.date_ord1_exam_ini != False: 
        if record.date_ord1_exam_ini.weekday() != 0:
          raise ValidationError('La fecha de inicio de exámenes tiene que ser un lunes')
  
  @api.depends('date_2term1_exam_ini')
  def _compute_ord1_exam_end(self):
    for record in self:
      if record.date_ord1_exam_ini == False:
        record.date_ord1_exam_end = ''
      else: 
        record.date_ord1_exam_end = record.date_ord1_exam_ini + datetime.timedelta(days=4)

  @api.depends('date_ord1_exam_ini')
  def _compute_extraord1_exam_ini(self):
    for record in self:
      if record.date_ord1_exam_ini == False:
        record.date_extraord1_exam_ini = ''
      else: 
        record.date_extraord1_exam_ini = record.date_ord1_exam_ini + datetime.timedelta(weeks = 4)

  @api.constrains('date_extraord1_exam_ini')
  def _check_date_extraord1_exam_ini(self):
    for record in self:
      if record.date_extraord1_exam_ini != False: 
        if record.date_extraord1_exam_ini.weekday() != 0:
          raise ValidationError('La fecha de inicio de exámenes tiene que ser un lunes')
  
  @api.depends('date_extraord1_exam_ini')
  def _compute_extraord1_exam_end(self):
    for record in self:
      if record.date_extraord1_exam_ini == False:
        record.date_extraord1_exam_end = ''
      else: 
        record.date_extraord1_exam_end = record.date_extraord1_exam_ini + datetime.timedelta(days = 4)
  
  @api.depends('date_init')
  def _compute_cancellation1(self):
    for record in self:
      if record.date_init == False:
        record.date_cancellation1 = ''
      else:
        record.date_cancellation1 = datetime.datetime(record.date_init.year, 12, 31)
        
  @api.depends('date_ord1_exam_ini')
  def _compute_waiver_ord1(self):
    for record in self:
      if record.date_ord1_exam_ini == False:
        record.date_waiver_ord1 = ''      
      else:
        record.date_waiver_ord1 = record.date_ord1_exam_ini - datetime.timedelta(days = 10)

  @api.depends('date_extraord1_exam_ini')
  def _compute_waiver_extraord1(self):
    for record in self:
      if record.date_extraord1_exam_ini == False:
        record.date_waiver_extraord1 = ''      
      else:
        record.date_waiver_extraord1 = record.date_extraord1_exam_ini - datetime.timedelta(days = 10)

  # ###########
  # FESTIVOS
  # ###########
  @api.onchange('date_init')
  def _calculate_holidays(self):
    for record in self:
      if self._origin.date_init != False:
        # si el año anterior es igual al que se acaba de cambiar no se hace nada
        if self._origin.date_init.year == record.date_init.year:
          continue

      if record.date_init == False:
        continue

      # fiestas de navidad
      date_christmas_holidayI = datetime.datetime(record.date_init.year, 12, 23) # de partida es el 23/12
   
      if date_christmas_holidayI.weekday() == 0: # cae lunes
        date_christmas_holidayI = datetime.datetime(record.date_init.year, 12, 21)
      elif date_christmas_holidayI.weekday() == 1:  # cae martes
        date_christmas_holidayI = datetime.datetime(record.date_init.year, 12, 20)
      elif date_christmas_holidayI.weekday() == 6: # cae domingo
        date_christmas_holidayI = datetime.datetime(record.date_init.year, 12, 22)

      date_christmas_holidayE = datetime.datetime(record.date_init.year + 1, 1, 6) # de partida es el 6/1
      if date_christmas_holidayE.weekday() >= 3 and date_christmas_holidayE.weekday() <= 5:
        date_christmas_holidayE = date_christmas_holidayE + datetime.timedelta(days = 6 - date_christmas_holidayE.weekday())

      # fallas
      date_fallas_holidayI = datetime.datetime(record.date_init.year + 1, 3, 15) # de partida es el 15/3
      if date_fallas_holidayI.weekday() == 0: # cae lunes
        date_fallas_holidayI = datetime.datetime(record.date_init.year, 3, 12)
      elif date_fallas_holidayI.weekday() == 1:  # cae martes
        date_fallas_holidayI = datetime.datetime(record.date_init.year + 1, 3, 20)
      elif date_fallas_holidayI.weekday() == 6: # cae domingo
        date_fallas_holidayI = datetime.datetime(record.date_init.year + 1, 3, 14)

      date_fallas_holidayE = datetime.datetime(record.date_init.year + 1, 3, 19) # de partida es el 19/3
      if date_fallas_holidayE.weekday() >= 3 and date_fallas_holidayE.weekday() <= 5:
        date_fallas_holidayE = date_fallas_holidayE + datetime.timedelta(days = 6 - date_fallas_holidayE.weekday())

      # elimino todos los registros "en el aire", pero se recuperan en el caso de que se cancele la modificación
      # del school_year
      record.holidays_ids = [(5, 0 ,0)]
      # añade nuevos registro, pero los mantiene en "el aire" hasta que se grabe el school_year
      record.holidays_ids = [(0, 0, {
        'school_year_id': self._origin.id,
        'description': 'Día Comunidad Valenciana', 
        'date': datetime.datetime(record.date_init.year, 10, 9), 
        'date_end': datetime.datetime(record.date_init.year, 10, 9) }),
        (0, 0, {
        'school_year_id': self._origin.id,
        'description': 'Día Hispanidad', 
        'date': datetime.datetime(record.date_init.year, 10, 12), 
        'date_end': datetime.datetime(record.date_init.year, 10, 12) }),
        (0, 0, {
        'school_year_id': self._origin.id,
        'description': 'Todos los santos', 
        'date': datetime.datetime(record.date_init.year, 11, 1), 
        'date_end': datetime.datetime(record.date_init.year, 11, 1) }),
        (0, 0, {
        'school_year_id': self._origin.id,
        'description': 'Constitución', 
        'date': datetime.datetime(record.date_init.year, 12, 6), 
        'date_end': datetime.datetime(record.date_init.year, 12, 6),
        'key': 'constitucion' }),
        (0, 0, {
        'school_year_id': self._origin.id,
        'description': 'Inmaculada', 
        'date': datetime.datetime(record.date_init.year, 12, 8), 
        'date_end': datetime.datetime(record.date_init.year, 12, 8),
        'key': 'inmaculada' }),
        (0, 0, {
        'school_year_id': self._origin.id,
        'description': 'Navidades', 
        'date': date_christmas_holidayI,
        'date_end': date_christmas_holidayE,
        'key': 'navidad' }),
        (0, 0, {
        'school_year_id': self._origin.id,
        'description': 'San Vicente Martir', 
        'date': datetime.datetime(record.date_init.year + 1, 1, 22), 
        'date_end': datetime.datetime(record.date_init.year + 1, 1, 22) }),
        (0, 0, {
        'school_year_id': self._origin.id,
        'description': 'Fallas', 
        'date': date_fallas_holidayI,
        'date_end': date_fallas_holidayE }),
        (0, 0, {
        'school_year_id': self._origin.id,
        'description': 'Pascuas', 
        'date': self._calc_easter(record.date_init.year + 1) + datetime.timedelta(days = -3),
        'date_end': self._calc_easter(record.date_init.year + 1) + datetime.timedelta(days = 8) }),
        (0, 0, {
        'school_year_id': self._origin.id,
        'description': '1º Mayo', 
        'date': datetime.datetime(record.date_init.year + 1, 5, 1), 
        'date_end': datetime.datetime(record.date_init.year + 1, 5, 1) })
        ]  


  @api.onchange('date_init')
  def _calculate_task(self):
    """
    Punto de entrada. Limpia los crons y llama a los métodos
    de cada módulo. Cada módulo extiende _get_cron_tasks()
    para añadir sus propias tareas.
    """
    self.ensure_one()
    if not self.date_init:
      return

    # Limpiar tareas existentes
    self.cron_ids = [(5, 0, 0)]

    # Recopilar tareas de todos los módulos instalados
    cron_ids = self._get_cron_tasks()
    self.cron_ids = cron_ids

  def _get_cron_tasks(self):
    """
    Devuelve la lista de tareas cron del módulo maya_core.
    Los módulos que dependan de maya_core deben extender
    este método llamando a super() y añadiendo sus tareas.
  
    Crea las tareas cron de:
    - matriculación
    - descarga de convalidaciones
    """
    self.ensure_one()

    # se obtienen todos los id de los ciclos 
    cron_ids = []
    studies = self.env['maya_core.study'].search([])
 
    # creación de cron jobs para todos los ciclos de manera simultánea
    cron_templates_all_studies_simultaneously = ['CHDL']

    for template in cron_templates_all_studies_simultaneously:
      cron_template = self.env['maya_core.cron_register'].search([('key', '=', template)])
      if len(cron_template.ids) == 0 or len(cron_template.ids) > 1:
        _logger.error(f'No se encuentra ningún cron_register o hay más de uno con la key {template}')
        continue

      task_name = f'{cron_template.name}'
      job_data = {}
      task_data = self.cron_template2task(cron_template, task_name, **job_data)
      task = (0, 0, task_data)
      cron_ids.append(task)  

    # creación de cron jobs para los ciclos de manera independiente
    _logger.info('Creando cron por ciclo de manera independiente => aulas de tutoria')
    for study in studies:
      # módulos de tutoria
      _logger.info(f'Ciclo -> {study.abbr}')
      tut_subjects = [ subject for subject in study.subjects_ids if subject['code'][:3] == 'TUT']

      _logger.info(f'Tutorias: {tut_subjects}')
      if not tut_subjects:
        _logger.error('No hay módulos de tutoria asignados en {}'.format(study.abbr))
        continue

      # únicamente módulos de tutoria que tengan aulas distintas
      distinct_subject_tut = [subject for subject in list(toolz.unique(tut_subjects, key = lambda x: x.get_classroom_by_study_id(study)))]
    
      # por cada aula de tutoria que haya en ese ciclo
      for subject in distinct_subject_tut:   
        classroom_id = subject.get_classroom_by_study_id(study)

        if classroom_id.moodle_id == 0:
          _logger.error(f'No hay definida en Maya un aula virtual de tutoria para {study.name}')
          continue

        ## MATRICULA 
        cron_template = self.env['maya_core.cron_register'].search([('key', '=', 'MTAL')])
        task_name = 'Matricula alumnos de {} en Maya {}'.format(study.abbr, 
              '/{}'.format(subject.year) if len(list(distinct_subject_tut)) > 1 else '')

        job_data = { 'classroom_id': classroom_id.moodle_id,
                     'course_id': study.id,
                     'subject_id': subject.id}

        task_data = self.cron_template2task(cron_template, task_name, **job_data)
        task = (0, 0, task_data)

        cron_ids.append(task)

        """ ## CONVALIDACIONES ESTE BLOQUE HAYQUE LLEVARSELO  A MAYA_VALID
        cron_template = self.env['maya_core.cron_register'].search([('key', '=', 'DVAL')])
        task_name = 'Descarga datos convalidaciones {} desde Aules {}'.format(course.abbr, 
              '/{}'.format(subject.year) if len(list(distinct_subject_tut)) > 1 else '')
        
        job_data = { 'validation_classroom_id': classroom_id.moodle_id,
                     'course_id': course.id,
                     'subject_id': subject.id,
                     'validation_task_id': classroom_id.get_task_id_by_key('validation') }

        task_data = self.cron_template2task(cron_template, task_name, **job_data)
        task = (0, 0, task_data)

        cron_ids.append(task)

        ## RECLAMACIONES CONVALIDACIONES
        cron_template = self.env['maya_core.cron_register'].search([('key', '=', 'DVAC')])
        task_name = 'Descarga datos reclamación convalidaciones {} desde Aules {}'.format(course.abbr, 
              '/{}'.format(subject.year) if len(list(distinct_subject_tut)) > 1 else '')

        job_data = { 'validation_classroom_id': classroom_id.moodle_id, 
                     'course_id': course.id,
                     'subject_id': subject.id,
                     'validation_task_id': classroom_id.get_task_id_by_key('validation_claim')}

        task_data = self.cron_template2task(cron_template, task_name, **job_data)
        task = (0, 0, task_data)

        cron_ids.append(task)

        ## NOTIFICACIONES ALUMNADO
        cron_template = self.env['maya_core.cron_register'].search([('key', '=', 'NOTV')])
        task_name = 'Notifica estado convalidaciones {} desde Aules {}'.format(course.abbr, 
              '/{}'.format(subject.year) if len(list(distinct_subject_tut)) > 1 else '')
      
        job_data = { 'validation_classroom_id': classroom_id.moodle_id, 
                     'course_id': course.id,
                     'validation_task_id': classroom_id.get_task_id_by_key('validation'), 
                     'validation_claim_task_id': classroom_id.get_task_id_by_key('validation_claim'), 
                     }
        
        task_data = self.cron_template2task(cron_template, task_name, **job_data)
        task = (0, 0, task_data)

        cron_ids.append(task)

        ## NOTIFICACIONES RECLAMACION ALUMNADO
        cron_template = self.env['maya_core.cron_register'].search([('key', '=', 'NTCV')])
        task_name = 'Notifica estado reclamación convalidaciones {} desde Aules {}'.format(course.abbr, 
              '/{}'.format(subject.year) if len(list(distinct_subject_tut)) > 1 else '')

        job_data = { 'validation_classroom_id': classroom_id.moodle_id, 
                     'course_id': course.id, 
                     'validation_claim_task_id': classroom_id.get_task_id_by_key('validation_claim')}
        
        task_data = self.cron_template2task(cron_template, task_name, **job_data)
        task = (0, 0, task_data)

        cron_ids.append(task)

        ## CONVALIDACIONES COMPETENCIAS
        cron_template = self.env['maya_core.cron_register'].search([('key', '=', 'DVUC')])
        task_name = 'Descarga datos convalidaciones por competencias {} desde Aules {}'.format(course.abbr, 
              '/{}'.format(subject.year) if len(list(distinct_subject_tut)) > 1 else '')
        
        job_data = { 'validation_classroom_id': classroom_id.moodle_id,
                     'course_id': course.id,
                     'subject_id': subject.id,
                     'validation_task_id': classroom_id.get_task_id_by_key('competence'), 
                     'val_type': 1 }
        
        task_data = self.cron_template2task(cron_template, task_name, **job_data)
        task = (0, 0, task_data)

        cron_ids.append(task)

         ## NOTIFICACIONES ALUMNADO
        cron_template = self.env['maya_core.cron_register'].search([('key', '=', 'NVUC')])
        task_name = 'Notifica estado convalidaciones por competencias {} desde Aules {}'.format(course.abbr, 
              '/{}'.format(subject.year) if len(list(distinct_subject_tut)) > 1 else '')
        
        job_data = { 'validation_classroom_id': classroom_id.moodle_id, 
                     'course_id': course.id,
                     'validation_task_id': classroom_id.get_task_id_by_key('competence'), 
                     'validation_claim_task_id': classroom_id.get_task_id_by_key('competence_claim'), 
                     'val_type': 1 }
        
        task_data = self.cron_template2task(cron_template, task_name, **job_data)
        task = (0, 0, task_data)

        cron_ids.append(task) """

    # añade nuevos registro, pero los mantiene en "el aire" hasta que se grabe el school_year 
    self.cron_ids = cron_ids

    return 
  
     
  @staticmethod
  def _calc_easter(year):
    '''
    Gauss algorithm to calculate the date of easter in a given year
    note // forces integer division in Python3
    returns a date object

    https://www.daniweb.com/programming/software-development/code/463551/another-look-at-easter-dates-python
    '''
    month = 3
    # determine the Golden number
    golden = (year % 19) + 1
    # determine the century number
    century = year // 100 + 1
    # correct for the years who are not leap years
    xx = (3 * century) // 4 - 12
    # moon correction
    yy = (8 * century + 5) // 25 - 5
    # find Sunday
    zz = (5 * year) // 4 - xx - 10
    # determine epact
    # age of moon on January 1st of that year
    # (follows a cycle of 19 years)
    ee = (11 * golden + 20 + yy - xx) % 30
    if ee == 24:
      ee += 1
    if ee == 25 and golden > 11:
      ee += 1
    # get the full moon
    moon = 44 - ee
    if moon < 21:
      moon += 30
    # up to Sunday
    day = (moon + 7) - ((zz + moon) % 7)
    # possibly up a month in easter_date
    if day > 31:
      day -= 31
      month = 4

    return datetime.datetime(year, month, day)

  def school_year_to_current_action(self):
    """
    Convierte el curso en pantalla en el curso actual, poniendo el anterior actual a finalizado.
    Sólo funciona con cursos en borrador.
    El flujo es: borrador -> actual -> finalizado -> borrador
    """
    if not self.env.is_admin():
        raise AccessDenied(_('Sólo el administrador puede convertir un curso en actual'))

    for record in self:
        # Buscamos el curso activo SOLO de la misma compañía
        current = self.env['maya_core.school_year'].search([
            ('state', '=', '1'),
            ('company_id', '=', record.company_id.id),
        ])

        assert len(current) < 2, (
            f'Inconsistencia de datos: hay {len(current)} cursos activos '
            f'para la compañía "{record.company_id.name}"'
        )

        # Finalizar el curso activo actual de esta compañía
        if current:
            current.state = '2'

        # Activar este curso
        record.state = '1'

    # Desactivar todos los usuarios salvo el admin
    """ admin_partner_id = self.env.ref('base.partner_admin')
    self.env.cr.execute(
        "UPDATE res_users SET active=FALSE WHERE partner_id != %s",
        (admin_partner_id.id,)
    ) """
  

  def school_year_to_draft_action(self):
    """
    Convierte el curso en pantalla en borrador. Sólo funciona con cursos finalizados
    El flujo es:  borrador -> actual -> finalizado -> borrador
    """

    # no tiene mucho sentido ya que es ua opción que se ejecuta desde la vista formulario 
    # por lo que sólo afecta a un registo
    for record in self:
        record.state = '0'

  def update_dates(self):
    self.dates['init_lective'] = { 
      'date': self.date_init_lective,
      'desc': self._fields['date_init_lective'].string, 
      'type': 'G'
    }

    self.dates['date_welcome_day'] = { 
      'date': self.date_welcome_day, 
      'desc': self._fields['date_welcome_day'].string,
      'type': 'G'
    }

    self.dates['1term2_end'] = { 
      'date': self.date_1term2_end,
      'desc': self._fields['date_1term2_end'].string, 
      'type': 'S'
    }

    self.dates['date_1term2_exam_ini'] = { 
      'date': self.date_1term2_exam_ini,
      'desc': self._fields['date_1term2_exam_ini'].string, 
      'type': 'S',
      # días que dura este evento, además del día indicado
      'dur': self.date_1term2_exam_end - self.date_1term2_exam_ini
    }

    self.dates['date_1term2_exam_end'] = { 
      'date': self.date_1term2_exam_end,
      'desc': self._fields['date_1term2_exam_end'].string, 
      'type': 'S',
      'dur': self.date_1term2_exam_ini - self.date_1term2_exam_end,
    }
    
    self.dates['date_2term2_ini'] = { 
      'date': self.date_2term2_ini,
      'desc': self._fields['date_2term2_ini'].string, 
      'type': 'S',
    }

    self.dates['date_2term2_end'] = { 
      'date': self.date_2term2_end,
      'desc': self._fields['date_2term2_end'].string, 
      'type': 'S',
    }

    self.dates['date_2term2_exam_ini'] = { 
      'date': self.date_2term2_exam_ini,
      'desc': self._fields['date_2term2_exam_ini'].string, 
      'type': 'S',
      'dur': self.date_2term2_exam_end - self.date_2term2_exam_ini
    }

    self.dates['date_2term2_exam_end'] = { 
      'date': self.date_2term2_exam_end,
      'desc': self._fields['date_2term2_exam_end'].string, 
      'type': 'S',
      'dur': self.date_2term2_exam_ini - self.date_2term2_exam_end,
    }

    self.dates['date_ord2_exam_ini'] = { 
      'date': self.date_ord2_exam_ini,
      'desc': self._fields['date_ord2_exam_ini'].string, 
      'type': 'S',
      'dur': self.date_ord2_exam_end - self.date_ord2_exam_ini,
    }

    self.dates['date_ord2_exam_end'] = { 
      'date': self.date_ord2_exam_end,
      'desc': self._fields['date_ord2_exam_end'].string, 
      'type': 'S',
      'dur': self.date_ord2_exam_ini - self.date_ord2_exam_end,
    }

    self.dates['date_extraord2_exam_ini'] = { 
      'date': self.date_extraord2_exam_ini,
      'desc': self._fields['date_extraord2_exam_ini'].string, 
      'type': 'S',
      'dur': self.date_extraord2_exam_end - self.date_extraord2_exam_ini,
    }

    self.dates['date_extraord2_exam_end'] = { 
      'date': self.date_extraord2_exam_end,
      'desc': self._fields['date_extraord2_exam_end'].string, 
      'type': 'S',
      'dur': self.date_extraord2_exam_ini - self.date_extraord2_exam_end,
    }
    
    self.dates['date_cancellation2'] = { 
      'date': self.date_cancellation2,
      'desc': self._fields['date_cancellation2'].string, 
      'type': 'S',
    }
  
    self.dates['date_waiver_ord2'] = { 
      'date': self.date_waiver_ord2,
      'desc': self._fields['date_waiver_ord2'].string, 
      'type': 'S',
    }
  
    self.dates['date_waiver_extraord2'] = { 
      'date': self.date_waiver_extraord2,
      'desc': self._fields['date_waiver_extraord2'].string, 
      'type': 'S',
    }

    self.dates['1term1_end'] = { 
      'date': self.date_1term1_end,
      'desc': self._fields['date_1term1_end'].string, 
      'type': 'P'
    }

    self.dates['date_1term1_exam_ini'] = { 
      'date': self.date_1term1_exam_ini,
      'desc': self._fields['date_1term1_exam_ini'].string, 
      'type': 'P',
      # días que dura este evento, además del día indicado
      'dur': self.date_1term1_exam_end - self.date_1term1_exam_ini
    }

    self.dates['date_1term1_exam_end'] = { 
      'date': self.date_1term1_exam_end,
      'desc': self._fields['date_1term1_exam_end'].string, 
      'type': 'P',
      'dur': self.date_1term1_exam_ini - self.date_1term1_exam_end,
    }
    
    self.dates['date_2term1_ini'] = { 
      'date': self.date_2term1_ini,
      'desc': self._fields['date_2term1_ini'].string, 
      'type': 'P',
    }

    self.dates['date_2term1_end'] = { 
      'date': self.date_2term1_end,
      'desc': self._fields['date_2term1_end'].string, 
      'type': 'P',
    }

    self.dates['date_2term1_exam_ini'] = { 
      'date': self.date_2term1_exam_ini,
      'desc': self._fields['date_2term1_exam_ini'].string, 
      'type': 'P',
      'dur': self.date_2term1_exam_end - self.date_2term1_exam_ini
    }

    self.dates['date_2term1_exam_end'] = { 
      'date': self.date_2term1_exam_end,
      'desc': self._fields['date_2term1_exam_end'].string, 
      'type': 'P',
      'dur': self.date_2term1_exam_ini - self.date_2term1_exam_end,
    }
    
    self.dates['date_ord1_exam_ini'] = { 
      'date': self.date_ord1_exam_ini,
      'desc': self._fields['date_ord1_exam_ini'].string, 
      'type': 'P',
      'dur': self.date_ord1_exam_end - self.date_ord1_exam_ini,
    }

    self.dates['date_ord1_exam_end'] = { 
      'date': self.date_ord1_exam_end,
      'desc': self._fields['date_ord1_exam_end'].string, 
      'type': 'P',
      'dur': self.date_ord1_exam_ini - self.date_ord1_exam_end,
    }

    self.dates['date_extraord1_exam_ini'] = { 
      'date': self.date_extraord1_exam_ini,
      'desc': self._fields['date_extraord1_exam_ini'].string, 
      'type': 'P',
      'dur': self.date_extraord1_exam_end - self.date_extraord1_exam_ini,
    }

    self.dates['date_extraord1_exam_end'] = { 
      'date': self.date_extraord1_exam_end,
      'desc': self._fields['date_extraord1_exam_end'].string, 
      'type': 'P',
      'dur': self.date_extraord1_exam_ini - self.date_extraord1_exam_end,
    } 
    
    self.dates['date_cancellation1'] = { 
      'date': self.date_cancellation1,
      'desc': self._fields['date_cancellation1'].string, 
      'type': 'P',
    }
  
    self.dates['date_waiver_ord1'] = { 
      'date': self.date_waiver_ord1,
      'desc': self._fields['date_waiver_ord1'].string, 
      'type': 'P',
    }
     
    self.dates['date_waiver_extraord1'] = { 
      'date': self.date_waiver_extraord1,
      'desc': self._fields['date_waiver_extraord1'].string, 
      'type': 'P',
    }

    for holiday in self.holidays_ids:
      holiday_dto = { 
        'date': holiday.date,
        'desc': holiday.description,
        'type': 'H'
      }

      holiday_end_dto = { 
        'date': holiday.date_end,
        'desc': holiday.description,
        'type': 'H'
      }

      if(holiday.date != holiday.date_end):
        holiday_dto['dur'] = holiday.date_end - holiday.date
        holiday_end_dto['dur'] = holiday.date - holiday.date_end

      self.dates[holiday.description] = holiday_dto
      self.dates[holiday.description] = holiday_end_dto

  def create_task_action(self):
    """
    Lanza la función de regeneración de tareas
    """
    self._calculate_task()

  def cron_template2task(self, cron_template, task_name, **job_data):
    task_data =  {}

    #task_data['school_year_id'] = self.ids[0]
    task_data['context'] = cron_template.context

    task_data['key'] = cron_template.key
    task_data['group_label'] = cron_template.key

    task_data['name'] = task_name
    task_data['active'] = True
    task_data['state'] = cron_template.state
    task_data['interval_number'] = cron_template.interval_number
    task_data['interval_type'] = cron_template.interval_type

    parameters = ", ".join(["=".join([key, str(val)]) for key, val in job_data.items()])
    if len(job_data) == 0:
      task_data['code'] = 'model.{}()'.format(cron_template.code)
    else:
      task_data['code'] = 'model.{}({})'.format(cron_template.code, parameters)
    task_data['doall'] = bool(cron_template.doall)
    task_data['numbercall'] = cron_template.numbercall
     
    task_data['model_id'] = self.env.ref(f'{cron_template.module}.model_{cron_template.module}_{cron_template.model}').ids[0]
    
    if cron_template.is_nextcall_day_in_format_iso():
      task_data['nextcall'] = cron_template['nextcall_day'] + cron_template['nextcall_hour']
    else:
      day = cron_template.literal_nextcall_day.split('|')
      if day[0] == 'today':
        value = date.today()
      else:
        value = getattr(self, day[1])
    
      if len(day[2]) != 0:
        incr_days = int(day[2])
      else:
        incr_days = 0        

      calldate = value + datetime.timedelta(days = incr_days)
      task_data['nextcall'] = str(calldate) + ' ' + cron_template.nextcall_hour

    return task_data
  
  def action_server_show_current_course(self):
    """
    Devuelve una acción de ventana apuntando al curso activo de la compañía actual.
    """
    course = self.env['maya_core.school_year'].sudo().search([
      ('state', '=', '1'),
      ('company_id', '=', self.env.company.id),
    ], limit=1)
    return {
      "type": "ir.actions.act_window",
      "res_model": "maya_core.school_year",
      "view_mode": "form",
      "res_id": course.id if course else False,
    }