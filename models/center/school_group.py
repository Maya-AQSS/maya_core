from odoo import models, fields, api
from datetime import datetime
from pathlib import Path
import pandas as pd

from ...support.helper import clean_str

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

    itaca_course_code = fields.Char(string='Código de curso de Ítaca',
        index=True, help="Código del curso en Ítaca al que pertenece el grupo"
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
    _unique_code_company = models.Constraint('unique(code, company_id)', 'El código del grupo debe ser único por tipo de enseñanza.')

    @api.model
    def adjust_study_code(self, group_code: str):
        """
        Recibe el código de un grupo y devuelve una tupla con
        (study_id, company_id) correspondiente.

        :param group_code: Código del grupo a buscar (ej. '1DAWA')
        :return: Tupla (int, int) con los IDs de (study_id, company_id) o (False, False) si no existe.
        """
        if not group_code:
            return False, False

        # Búsqueda con sudo() para omitir reglas de registro/multicompañía al consultar
        group_rec = self.sudo().search([('code', '=', group_code)], limit=1)

        if group_rec:
            return group_rec.study_id.id, group_rec.company_id.id

        return False, False

    @api.model
    def assign_itaca_courses(self, filename):
        """
        Asigna a cada grupo su código de curso de Ítaca a partir del fichero de grupos
        (columnas 'curso' y 'grupo').
        - Si el grupo no tiene código de curso asignado, se le asigna.
        - Si ya lo tiene y coincide, no se hace nada.
        - Si ya lo tiene y no coincide, no se modifica y se anota en el informe.

        :param filename: Nombre del fichero CSV de grupos de Ítaca
        """
        filepath = self.env['ir.config_parameter'].sudo().get_param('maya_core.itaca_students_data_folder')
        if not filepath:
            raise Exception("No se ha definido la ruta de la carpeta de datos de Ítaca.")

        csv_file = Path(filepath) / filename
        if not csv_file.exists():
            raise Exception(f"El fichero de grupos no existe en la ruta: {csv_file}")

        try:
            # dtype=str para que los códigos de curso no se interpreten como números
            df = pd.read_csv(csv_file, dtype=str)
        except Exception as e:
            raise Exception(f"Error al leer el fichero CSV de grupos: {str(e)}")

        errors = []

        for _, row in df.iterrows():
            group_code = clean_str(row.get('grupo'))
            course_code = clean_str(row.get('curso'))
            if not group_code or not course_code:
                errors.append(f"Línea incompleta en el fichero de grupos: curso='{course_code}', grupo='{group_code}'.")
                continue

            # El código de grupo es único por tipo de enseñanza: puede haber varios
            groups = self.sudo().search([('code', '=', group_code)])
            if not groups:
                errors.append(f"(Grupo {group_code}): No existe en Maya.")
                continue

            for group in groups:
                if not group.itaca_course_code:
                    group.itaca_course_code = course_code
                elif group.itaca_course_code != course_code:
                    errors.append(
                        f"(Grupo {group_code} | {group.company_id.name}): El código de curso de Ítaca asignado "
                        f"'{group.itaca_course_code}' no coincide con el del fichero '{course_code}'."
                    )

        # Generación del fichero de log con los errores acumulados
        if errors:
            date_str = datetime.now().strftime("%y%m%d%H%M")
            log_file = Path(filepath) / f"informe_asignacion_cursos_itaca_{date_str}.txt"
            try:
                with open(log_file, 'w', encoding='utf-8') as f:
                    for err in errors:
                        f.write(f"{err}\n")
            except IOError as e:
                raise e

        return