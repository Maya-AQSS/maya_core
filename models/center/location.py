# -*- coding: utf-8 -*-

from odoo import models, fields, _

class Location(models.Model):
  """
  Define las ubicaciones
  """
    
  _name = 'maya_core.location'
  _description = 'Departamento didáctico'

  name = fields.Char(_('Nombre'), required = True, translate = True)
  description = fields.Text(_('Descripción'), help=_('Usos permitidos, normas de acceso y cualquier información relevante.'))

  image = fields.Image(
    string = _('Fotografía'),
    max_width = 1920,
    max_height = 1080,
    attachment=True
  )

  floor_plan = fields.Image(
    string = _('Plano'),
    max_width = 3508,
    max_height = 2480,
    attachment=True
  )  # va al filestore

  map_url = fields.Char(string = _('Enlace Google Maps'), help = _('URL de Google Maps'))
