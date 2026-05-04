from odoo import models, fields

class MayaCoreTag(models.Model):
    _name = 'maya_core.tag'
    _description = 'Etiquetas Generales'

    name = fields.Char(string='Nombre de la etiqueta', required=True)
    color = fields.Integer(string='Color')