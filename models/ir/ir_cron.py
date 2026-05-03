# coding: utf-8
# Copyright (C) 2018 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
# https://github.com/OCA/server-tools/blob/8.0/cron_inactivity_period/models/ir_cron.py

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

class IrCron(models.Model):
  """
  Ejemplo de herencia de prototipo
  Herencia del modelo ir.cron
  Lo que hace es crear otro modelo (y por tanto otra tabla) basada en el modelo ir.cron
  para incluir otros campos

  El objetivo es que sean ejecutados externamente por n8n, no por Odoo
  """
  _inherit = 'ir.cron'
  _name = 'maya_core.ir.cron'

  context = fields.Selection([
    ('FPC', 'General para todos los ciclos (todos los estudiantes).'), # convalidaciones o renuncias, etc
    ('FPD', 'General para todos los departamentos (todos los profesores).'), # explicación de procedimientos, cumplimentación de formularios, etc
    ('FPE', 'General para todos los empleados (todo el claustro de FP).'), 
    ('DEP', 'Asociada a un departamento'), # mensajes de bienvenida, explicación de procedimientos, etc
    ('COUR', 'Asociada a un Ciclo'), #  mensaje de bienvenida, convocatoria de reuniones, apertura o fin de plazos
    ('SUBJ', 'Asociada a un Módulo.'),
    ], string ='Contexto', 
    help = 'Contexto en el que trabaja la tarea programada')

  # Objectoid al que va asociado el cron, 
  # no confundir con el modelo que tiene el código a ejecutar.
  school_year_id = fields.Many2one('maya_core.school_year', string = 'Curso escolar', ondelete = 'cascade')

  key = fields.Char('Key')
  
  group_label = fields.Selection([
    ('MTAL', 'Matricula alumnos'), 
    ('CAAL', 'Comprobación de asistencia en Aules'), 
    ('DVAL', 'Descarga convalidaciones'), 
    ('DVAC', 'Descarga reclamaciones convalidaciones'),
    ('DVUC', 'Descarga convalidaciones por competencias'), 
    ('NOTV', 'Notificación del estado de las convalidaciones'), 
    ('NVUC', 'Notificación del estado de las convalidaciones por competencias'), 
    ('NTCV', 'Notificación del estado de reclamaciones sobre convalidaciones'),
    ('CHDL', 'Comprobación de fechas límites convalidaciones superadas'), 
    ],string = "Etiqueta de grupo")
     
  def method_direct_trigger(self):
    self.check_access_rights('write')
    for cron in self:
      try:
        cron.with_user(cron.user_id).with_context({'lastcall': cron.lastcall}).ir_actions_server_id.run()
        cron.lastcall = fields.Datetime.now()
      except Exception as e:
        _logger.error(f'Se ha producido una excepción el cron_id {cron.id}, name {cron.name}: {str(e)}')
    
    return True 
  
  def run_cron(self):
    self.method_direct_trigger()

