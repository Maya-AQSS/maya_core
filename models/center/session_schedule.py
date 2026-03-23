# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class SessionSchedule(models.Model):
  """
  Define los horarios de las sesiones por día de la semana y ubicación
  """

  _name = 'maya_core.session_schedule'
  _description = 'Horarios de sesiones'

  name = fields.Char(
      _('Descripción'), 
      required = True, 
      size= 10,
      translate = True, 
      help=_('Descripción de la sesión.'))
  week_day = fields.Selection([
      ('L', _('Lunes')),
      ('M', _('Martes')),
      ('X', _('Miércoles')),
      ('J', _('Jueves')),
      ('V', _('Viernes')),
  ], string = _('Día de la semana'), help = _('Día de la semana de la sesión.'), required = True)

  start_time = fields.Float(
    string = _('Hora de inicio'), 
    required = True,
    help = _("Hora de inicio de la sesión."),
    group_operator=False
  )

  end_time = fields.Float(
    string = _('Hora de fin'), 
    required = True,
    help = _("Hora de fin de la sesión."),
    group_operator=False
  )

  duration = fields.Float(
    string = _('Duración (Horas)'), 
    compute = '_compute_duration', 
    store = True,
    group_operator=False
  )

  active = fields.Boolean('Activa', default=True)

  location_id = fields.Many2one('maya_core.location', string = _('Ubicación'))

  @api.depends('start_time', 'end_time')
  def _compute_duration(self):
    for record in self:
      if record.end_time > record.start_time:
        record.duration = record.end_time - record.start_time
      else:
        record.duration = 0.0
