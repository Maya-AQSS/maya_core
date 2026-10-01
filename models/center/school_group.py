from odoo import models, fields, api

class SchoolGroup(models.Model):
    """
    Define un grupo de alumnos en un centro escolar (ej. 2CFSDAM)
    """
    _name = 'maya_core.school_group'
    _description = 'Grupo de alumnos, clase'
    _order = 'company_id, study_id, code'

    name = fields.Char(string='Nombre del Grupo', required=True, 
        translate=True, help="Nombre descriptivo del grupo, ej. 1º DAW - Grupo A"
    )
    
    code = fields.Char(string='Código', required=True, 
        size=11, index=True, help="Código identificador del grupo, ej. 1DAWA"
    )

    # El tipo de enseñanza coincide con la compañía configurada en Odoo
    company_id = fields.Many2one(
        'res.company', 
        string='Tipo de Enseñanza',
        required=True, 
        default=lambda self: self.env.company
    )

    # Relación con el estudio (Ciclo, Bachillerato, etc.)
    study_id = fields.Many2one(
        'maya_core.study', 
        string='Estudio', 
        required=True,
        ondelete='restrict',
        # Filtra los estudios para mostrar solo los pertenecientes al mismo tipo de enseñanza
        domain="[('company_id', '=', company_id)]"
    )

    # Restricción SQL para evitar duplicar el código dentro del mismo tipo de enseñanza
    _unique_codo_company = models.Constraint('unique(code, company_id)', 'El código del grupo debe ser único por tipo de enseñanza.')