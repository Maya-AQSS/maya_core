import logging
import datetime
import re

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from ..support.constants import CRON_CONTEXTS
from dataclasses import dataclass, field

_logger = logging.getLogger(__name__)


class CronRegister(models.Model):
  """
  Registra plantillas de todas las tareas cron posibles existentes
  Maya repasa todas ellas y genera tareas según el contexto 
  """
  _name = 'maya_core.cron_register'

  module = fields.Char(string = 'Módulo origen', help = 'Nombre del módulo que registra la tarea', compute= '_set_module', store = True)
  key = fields.Char(string = 'Clave', size = 5, required = True,  help = 'Clave para identificar la plantilla. Debe ser único')
  state = fields.Char(size = 4, default = 'code') 
  code = fields.Char(required = True,  help = 'Método a ejecutar')
  context = fields.Char(string = 'Contexto', size = 4, required = True, help = 'Contexto en el que trabaja la tarea programada')
  name = fields.Char(string = 'Descripción', size = 80, required = True)
  model = fields.Char(size = 60, required = True, help = 'Nombre del modelo en el que estará el código a ejecutar')
  interval_number = fields.Integer(default = 1, help = 'Veces que se repite en el tipo de intervalo')
  interval_type = fields.Char(default = 'days', help = 'Unidad del intervalo')
  numbercall = fields.Integer(default = -1, help = 'Número de veces que será ejecutada la tarea')
  nextcall_day = fields.Char(required = True, help = 'Día de la primera ejecución. Soporta: \
                                                        día -> 2023/12/22 (ISO Format),\
                                                        campo de otro modelo (school_year) -> school_year.date_init, \
                                                        día de la creación de la tarea -> today.\n\
                                                      Las dos últimas opcones admiten signo + y - para añadir o restar\
                                                      unidades de tipo interval_type: today + 2')
  nextcall_hour = fields.Char(required = True, help = 'Hora de la siguiente ejecución (ej: 18:20:50)')
  literal_nextcall_day = fields.Char(compute = '_compute_literal_nextcall_day')
  doall = fields.Boolean(default = True, help = 'Si el servidor cae, cuando se reinicie lanzará las tareas no ejecutadas')
  
  _unique_key = models.Constraint('unique(key)', 'El código de la plantilla tiene que ser único.')

  @api.constrains('interval_type')
  def _check_interval_type(self):
    for record in self:
      if record.interval_type not in ['minutes', 'hours', 'work_days', 'days', 'weeks', 'months']:
        raise ValidationError('Tipo de intervalo no soportado')
      
  @api.constrains('context')
  def _check_context(self):
    for record in self:
      if record.context not in CRON_CONTEXTS:
        raise ValidationError('Tipo de contexto no soportado')
      
  @api.constrains('nextcall_day')
  def _check_nextcall_day(self):
    for record in self:

      match = re.match(self._get_pattern_nextcall_day(), self.nextcall_day.lower())

      if match == None:
        try:
          datetime.date.fromisoformat(record.nextcall_day)
        except ValueError:
          raise ValidationError('Formato de día en nextcall no soportado')
        

  @api.constrains('nextcall_hour')
  def _check_nextcall_hour(self):
    for record in self:
      try:
        datetime.time.fromisoformat(record.nextcall_hour)
      except ValueError:
        raise ValidationError('Formato de hora en nextcall no soportado')

  @api.depends('key')
  def _set_module(self):
    # TODO comprobar que el módulo sea un módulo de confianza
    for record in self:
      # obtenego el módulo del id externo
      record.module = list(record.get_external_id().values())[0].split('.')[0]
  

  def is_nextcall_day_in_format_iso(self) -> bool: 
    self.ensure_one()
    try:
      datetime.date.fromisoformat(self.nextcall_day)
    except ValueError:
      return False
    
    return True

  @api.depends('nextcall_day')
  def _compute_literal_nextcall_day(self):
    for record in self:
    
      match = re.match(self._get_pattern_nextcall_day(), record.nextcall_day.lower())
      record.literal_nextcall_day = '{}|{}|{}'.format(match.group(1), 
                                                      match.group(3) if match.group(3) else '',
                                                      match.group(4) if match.group(4) else '')

  def _get_pattern_nextcall_day(self) -> str:
    fields = self.env["maya_core.school_year"]._fields

    valid_dates = [ field for field in fields if field.startswith("date_")]
    valid_dates_regex = '|'.join(map(re.escape, valid_dates))

    return r'^(today|(school_year\.({})))?([+-]\d+)?$'.format(valid_dates_regex)