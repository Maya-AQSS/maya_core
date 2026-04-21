# -*- coding: utf-8 -*-

from odoo import models, fields, _
from odoo.exceptions import UserError

class Location(models.Model):
  """
  Define las ubicaciones
  """
    
  _name = 'maya_core.location'
  _description = 'Ubicaciones'

  name = fields.Char(_('Nombre'), required = True, translate = True)
  description = fields.Text(_('Descripción'), translate=True, help=_('Usos permitidos, normas de acceso y cualquier información relevante.'))

  address = fields.Char(string=_('Dirección'), required = True, help=_('Dirección de la ubicación física.'))

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

  def unlink(self):
    for record in self:
      # Si hay espacios de trabajo asignados a esta ubicación no es posible eliminarla
      num_places = self.env["maya_core.place"].search_count([
          ("location_id", "=", record.id)
      ])
        
      if num_places > 0:
        raise UserError(
            _("No se puede eliminar la ubicación '%s' porque tiene %s espacios de trabajo definidos.") % (record.name, num_places)
        )
        
    return super().unlink()
