# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class SessionSchedule(models.Model):
  """
  Define los horarios de las sesiones por día de la semana y ubicación
  """

  _name = 'maya_core.session_schedule'
  _description = 'Horarios de sesiones'
  _order = 'week_day'

  name = fields.Char(
      'Descripción', 
      required = True, 
      size= 10,
      translate = True, 
      help='Descripción de la sesión.')
  week_day = fields.Selection([
      ('0L', 'Lunes'),
      ('1M', 'Martes'),
      ('2X', 'Miércoles'),
      ('3J', 'Jueves'),
      ('4V', 'Viernes'),
  ], string = 'Día de la semana', help = 'Día de la semana de la sesión.', required = True)

  start_time = fields.Float(
    string = 'Hora de inicio', 
    required = True,
    help = "Hora de inicio de la sesión.",
    group_operator=False
  )

  end_time = fields.Float(
    string = 'Hora de fin',
    required = True,
    help = "Hora de fin de la sesión.",
    group_operator=False
  )

  duration = fields.Float(
    string = 'Duración (Horas)', 
    compute = '_compute_duration', 
    group_operator=False
  )

  active = fields.Boolean('Activa', default=True)

  location_id = fields.Many2one('maya_core.location', string = 'Ubicación')

  @api.depends('start_time', 'end_time')
  def _compute_duration(self):
    for record in self:
      if record.end_time > record.start_time:
        record.duration = record.end_time - record.start_time
      else:
        record.duration = 0.0 

  @api.constrains('start_time', 'end_time', 'week_day', 'location_id')
  def _check_overlap(self):
      """
      Comprueba que la sesión que se crea no solapa con ningúna existente
      """
      for record in self:

        domain = [
          # Ignora el registro que se está creando
          ('id', '!=', record.id),                   
          # Comprobar que sea en la misma localización y día de la semana
          ('location_id', '=', record.location_id.id),
          ('week_day', '=', record.week_day),  
          # Comprobar solapamiento        
          ('start_time', '<', record.end_time),        
          ('end_time', '>', record.start_time),        
        ]
    
        overlapping_sessions = self.search_count(domain)

        if overlapping_sessions > 0:
          raise ValidationError(_("Error: Ya existe una sesión en esta ubicación y día que se solapa con este horario."))
        