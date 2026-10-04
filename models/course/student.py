# -*- coding: utf-8 -*-
from odoo import api, models, fields
from odoo.exceptions import UserError
from odoo.fields import Domain
from datetime import datetime
import pandas as pd
from pathlib import Path

from ....maya_core.support.helper import read_csv, clean_str

class Student(models.Model):
  """
  Define un estudiante
  """

  _name = 'maya_core.student'
  _description = 'Estudiante'
  _order = 'surname'

  moodle_id = fields.Char(string = 'moodle_id', size = 9)
  nia = fields.Char(string = 'NIA', size = 9, required = True)
  name = fields.Char(string = 'Nombre', required = True)
  surname = fields.Char(string = 'Apellidos', required = True)

  # emails
  email = fields.Char(string = 'Email')
  email_support = fields.Char(string = 'Email de apoyo')
  email_coorp = fields.Char(string = 'Email corporativo')

  telephone1 = fields.Char(string = 'Teléfono 1')
  telephone2 = fields.Char(string = 'Teléfono 2')

  student_info = fields.Char(string = 'Nombre completo', compute = '_compute_full_student_info')

  # puede estar matriculado en varios estudios
  studies_ids = fields.One2many(
    'maya_core.student_study_rel', 
    'student_id', 
    string='Matrículas en estudios'
  )
  
  subjects_ids = fields.One2many('maya_core.subject_student_rel', 'student_id', order='subject_study asc, subject_name asc')

  def _compute_full_student_info(self):
    for record in self:
      record.student_info = record.surname + ', ' + record.name


  @api.model
  def process_itaca_import(self, filename):
    """
    Procesa el fichero de Ítaca:
    1. Lee el CSV.
    2. Por cada fila: busca/crea el alumno por NIA, actualiza datos y matricula.
    3. Para matrículas que no aparecen en la lista actual, las desactiva y registra la fecha de desmatriculación.
    """
    # 1. Carga y validación del fichero
    filepath = self.env['ir.config_parameter'].sudo().get_param('maya_core.itaca_students_data_folder')
    if not filepath:
      raise Exception("No se ha definido la ruta de la carpeta de datos de Ítaca.")

    csv_file = Path(filepath) / filename
    if not csv_file.exists():
      raise Exception(f"El fichero de datos no existe en la ruta: {csv_file}")

    # OJO esto funciona por que solo hay un año escolar activo por compañia
    active_school_years = {
      sy.company_id.id: sy.id
      for sy in self.env['maya_core.school_year'].search([('state', '=', 1)])
    }

    try:
      df, _ = read_csv(csv_file)
    except Exception as e:
      raise Exception(f"Error al leer el fichero CSV: {str(e)}")

    errors = []
    processed_rel_ids = set()  # Guarda los IDs de las matrículas confirmadas en este CSV
    today = fields.Date.context_today(self)

    # 2. Iterar sobre cada registro del CSV
    for index, row in df.iterrows():
      nia = str(row.get('NIA') or '').strip()
      if not nia:
        errors.append(f"El alumno {str(row.get('nombre') or '').strip()} {str(row.get('apellido1') or '').strip()} NIA especificado.")
        continue

      # a) Buscar estudiante por NIA o por Email
      student = self.search([('nia', '=', nia)], limit=1)
      
      # Búsqueda alternativa por email si el NIA fuera nuevo en Odoo
      email_corp = clean_str(row.get('email_corporativo'))

      if not email_corp:
        errors.append(f"El alumno {str(row.get('nombre') or '').strip()} {str(row.get('apellido1') or '').strip()} no tiene email corporativo especificado.")
        continue

      email1 = clean_str(row.get('email1'))
      
      if not student and (email_corp or email1):
        domain = []
        if email_corp:
            domain.append(('email_coorp', '=', email_corp))
        if email1:
            domain.append(('email', '=', email1))
        
        # Búsqueda con operador OR
        student = self.search(Domain.OR([[d] for d in domain]), limit=1)

      # Datos a actualizar/crear
      student_vals = {
        'nia': nia,
        'name': (row.get('nombre') or student.name or '').strip(),
        'surname': (row.get('apellido1') or student.surname or '').strip() + ' ' + (row.get('apellido2') or student.surname or '').strip(),
        'email_coorp': email_corp or (student.email_coorp if student else False),
        'email': email1 or (student.email if student else False),
        'email_support': (row.get('email2') or '').strip() or (student.email_support if student else False),
        'telephone1': (row.get('telefono1') or '').strip() or (student.telephone1 if student else False),
        'telephone2': (row.get('telefono2') or '').strip() or (student.telephone2 if student else False),
      }

      # b) Crear o Actualizar el estudiante
      if not student:
        student = self.create(student_vals)
      else:
        student.write(student_vals)

      # c) Obtener estudio y compañía a partir del grupo
      group_code = str(row.get('grupo') or '').strip()
      if not group_code:
        errors.append(f"(NIA {nia}): No se especificó el grupo.")
        continue

      study_id, company_id = self.env['maya_core.school_group'].adjust_study_code(group_code)
      if not study_id:
        errors.append(f"(NIA {nia}): No se encontró el estudio para el grupo '{group_code}'.")
        continue

      # d) Matricular / Reactivar al alumno en el estudio
      rel = student.studies_ids.filtered(lambda r: r.study_id.id == study_id)
      fecha_matricula = row.get('fecha_matricula') or today

      current_sy = active_school_years.get(company_id)

      if current_sy is None:
        errors.append(f"(NIA {nia}): No se encontró curso escolar activo para el estudio '{company_id}'.")
        continue

      if rel:
        # Si ya existía la relación, nos aseguramos de que esté activa y actualizamos el grupo
        vals_update = {'group': group_code, 'active': True, 'unenrollment_date': False}
        if not rel.enrollment_date:
          vals_update['enrollment_date'] = fecha_matricula
        rel.write(vals_update)
      else:
        # Crear la nueva matrícula
        rel = self.env['maya_core.student_study_rel'].create({
            'student_id': student.id,
            'study_id': study_id,
            'group': group_code,
            'enrollment_date': fecha_matricula,
            'active': True,
            'school_year_id': current_sy
        })

      # Añadimos la relación a las procesadas en el CSV actual
      processed_rel_ids.add(rel.id)

    # 3. Dar de baja a las matrículas que NO estaban en el CSV
    # Buscamos todas las matrículas activas en el sistema que no se hayan procesado hoy
    errors.append(f"\n###################")
    errors.append(f"Bajas de matrículas")
    errors.append(f"###################")

    unprocessed_rels = self.env['maya_core.student_study_rel'].search([
        ('id', 'not in', list(processed_rel_ids)),
        ('active', '=', True)
    ])

    if unprocessed_rels:
      # Registramos cada baja en la lista de errores/incidencias
      for rel in unprocessed_rels:
        student_info = rel.student_id.name or 'Sin Nombre'
        nia = rel.student_id.nia or 'Sin NIA'
        study_code = rel.study_id.code or rel.study_id.name or 'Estudio no especificado'
        group = rel.group or 'Sin Grupo'

        msg = (
            f"BAJA DETECTADA -> Estudiante: {student_info} | NIA: {nia} "
            f"| Estudio: {study_code} | Grupo: {group} "
            f"| Fecha Desmatriculación: {today}"
        )
        errors.append(msg)

      unprocessed_rels.write({
        'active': False,
        'unenrollment_date': today,
      })
     
    errors.append(f"Total de bajas el fichero: {len(unprocessed_rels)}")
      
    # 4. Generación del fichero de log con los errores acumulados
    if errors:
      date_str = datetime.now().strftime("%y%m%d%H%M")
      log_file = Path(filepath) / f"informe_importacion_alumnos_itaca_{date_str}.txt"
      try:
        with open(log_file, 'w', encoding='utf-8') as f:
          for err in errors:
            f.write(f"{err}\n")
      except IOError as e:
        raise e

    return

  # @api.model
  # def update_student_data_from_itaca(record, df, studies_dict):
  #   """
  #   Procesa un único estudiante buscando sus emails en el DataFrame df.
  #   Actualiza también los cursos y grupos en los que está matriculado
  #   En caso de no aparecer marca la matrícula como baja
  #   Devuelve una tupla (actualizado: bool, lista_de_errores)
  #   """
  #   errors = []
  #   updated = False

  #   # Busco por cualquier email válido
  #   possible_emails = [
  #       (record.email_coorp or '').strip(),
  #       (record.email or '').strip(),
  #       (record.email_support or '').strip(),
  #   ]
  #   possible_emails = [e for e in possible_emails if e]

  #   if not possible_emails:
  #     errors.append(f"El estudiante {record.student_info} no tiene ningún email para buscar en Itaca.")
  #     return updated, errors

  #   # Buscar en Itaca
  #   found_rows = pd.DataFrame()
  #   for email in possible_emails:
  #     # obtengo todas las filas  en las que el email esté en el registro del alumnno
  #     rows = df[(df['email_corporativo'] == email) | (df['email1'] == email) | (df['email2'] == email)]
  #     if not rows.empty:
  #       found_rows = rows
  #       break

  #   if found_rows.empty:
  #     errors.append(f"No se encuentra información en Itaca para {record.student_info} (emails: {', '.join(possible_emails)})")
  #     return updated, errors

  #   # Si hay varias filas compruebo que sea el mismo NIA (se puede dar el caso de 
  #   # hermanos y que el correo se el de alguno de los padres)
  #   nias = found_rows['NIA'].dropna().unique().tolist()
  #   if len(nias) > 1:
  #     errors.append(
  #       f"Varias entradas en Itaca para {record.student_info} con distintos NIA: {nias}. "
  #       f"Revisa el fichero, el email no es único."
  #     )
  #     return updated, errors

  #   nia = nias[0] if nias else None
  #   if nia:
  #     record.nia = nia

  #   # Actualizo los datos personales desde la primera fila
  #   row = found_rows.iloc[0]
  #   record.email_coorp = row.get('email_corporativo') or record.email_coorp
  #   record.email = row.get('email1') or record.email
  #   record.email_support = row.get('email2') or record.email_support
  #   record.telephone1 = row.get('telefono1') or record.telephone1
  #   record.telephone2 = row.get('telefono2') or record.telephone2
  #   updated = True

  #   # Proceso todos los cursos asociados
  #   itaca_studies = []
  #   for _, row in found_rows.iterrows():
  #     group = str(row.get('grupo')).strip() or None
  #     study_id, company_id = self.env['maya_core.school_group'].adjust_study_code(group)

  #     if not study_id:
  #       errors.append(f"Estudio para el grupo {group} no encontrado en Odoo para {record.student_info}")
  #       continue

  #     itaca_studies.append(study_id)

  #     rel = record.studies_ids.filtered(lambda r: r.study_id.id == study_id)
  #     if rel:
  #       if rel.group != group or not rel.active:
  #         rel.write({'group': group, 'active': True})
  #     else:
  #       record.env['maya_core.student_study_rel'].create({
  #           'student_id': record.id,
  #           'study_id': study_id,
  #           'group': group,
  #           'enrollment_date': row.get('fecha_matricula') or fields.Date.context_today(record)
  #       })

  #   # si no aparecen las marco como baja
  #   for rel in record.studies_ids:
  #     if rel.study_id.id not in itaca_studies:
  #         rel.active = False

  #   return updated, errors

  # def update_itaca_fields(self, filename):
  #   """
  #   Actualiza los datos desde Itaca de todos los estudiantes seleccionados
  #   """
  #   # TODO mejorar creando un diccionario por mail, pero deberia controlar que pasa con dos claves iguales
  #   filepath = self.env['ir.config_parameter'].sudo().get_param('maya_core.itaca_students_data_folder')
  #   if not filepath:
  #     raise (f'\033[0;31m[ERROR]\033[0m No se ha definido el nombre del fichero de datos de itaca')

  #   csv_file = Path(filepath) / filename
  
  #   try:
  #     df, data_stack = read_csv(csv_file)
  #   except Exception as e:
  #     raise
    
  #   errors = []
    
  #   for record in self:
  #     _, record_errors = Student.update_student_data_from_itaca(record, df, data_stack)
  #     errors.extend(record_errors)

  #   # creo un fichero de texto con los errores
  #   errors_filename = ''
  #   if len (errors)>0:
  #     date_str = datetime.now().strftime("%y%m%d%H%M")

  #     errors_filename = f"/mnt/odoo-repo/itaca/errores_itaca_{date_str}.txt" 
  #     try:
  #       with open(errors_filename, 'w', encoding='utf-8') as f:
  #           for line in errors:
  #               f.write(f"{line}\n")
        
  #       errors_filename = f'\r{len(errors)} error(es). Más información en: ' + errors_filename

  #     except IOError as e:
  #       raise UserError(f"Error al escribir en el fichero: {str(e)}")


  #   message = f'{len(self)} alumnos procesados. ' + errors_filename  
