# -*- coding: utf-8 -*-

from odoo import models, fields, _

class Location(models.Model):
  """
  Define las ubicaciones
  """
    
  _name = 'maya_core.location'
  _description = 'Ubicaciones'

  name = fields.Char(_('Nombre'), required = True, translate = True)
  description = fields.Text(_('Descripción'), translate=True, help=_('Usos permitidos, normas de acceso y cualquier información relevante.'))

  # Añadidos campos que faltaban por definir de dirección y teléfono móvil
  address = fields.Char(string=_('Dirección'), required = True, help=_('Dirección de la ubicación física.'))
  phone_number = fields.Char(string=_('Teléfono'), required = False, help=_('Número de teléfono del departamento docente.'))


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
