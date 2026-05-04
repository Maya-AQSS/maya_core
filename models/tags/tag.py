from odoo import models, fields, _

class MayaCoreTag(models.Model):
    _name = 'maya_core.tag'
    _description = 'Etiquetas Generales'

    name = fields.Char(string=_('Nombre de la Etiqueta'), required=True)
    color = fields.Integer(string='Color')

    code = fields.Char(
        string='Código interno', 
        help='Identificador único para lógica de negocio. No modificar.'
    )
    _sql_constraints = [
        ('code_unique', 'unique(code)', '¡El código interno de la etiqueta debe ser único!')
    ]