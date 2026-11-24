# -*- coding: utf-8 -*-

from odoo import api, models, fields
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from ...support.helper import read_csv, clean_str


class SubjectStudentRel(models.Model):
  """
  Se crea como tabla de relación (pivote) entre Subject y Student para dar soporte a un campo intermedio
  """
  _name = 'maya_core.subject_student_rel'
  _description = 'Relación entre student y subject'

  subject_id = fields.Many2one('maya_core.subject', required = True)
  student_id = fields.Many2one('maya_core.student', required = True)

  # ciclo en el que está matriculado
  study_id = fields.Many2one('maya_core.study', required = True)

  # curso escolar
  school_year_id = fields.Many2one('maya_core.school_year', string = 'Curso escolar', ondelete = 'cascade')

  # número que determina los flags asociados al estado del record
  status_flags = fields.Integer(default = 0)

  subject_name = fields.Char(related='subject_id.name', string='Módulo | Asignatura', store=False)
  subject_code = fields.Char(related='subject_id.code', string='Código', store=False)
  subject_study = fields.Char(related='study_id.code', string='Estudios', store=False)

  _unique_subject_student_rel = models.Constraint('unique(student_id, subject_id, study_id, school_year_id)', 'Sólo puede haber una relación por estudiante, estudio, asignatura y curso escolar.')

  @api.model
  def process_itaca_enrolments(self, filename):
    """
    Matricula a los alumnos en sus asignaturas según el fichero de contenidos de Ítaca
    (columnas 'alumno', 'curso', 'ensenanza', 'contenido1'...'contenidoN'):
    1. El alumno se obtiene por NIA, el estudio a partir del curso de Ítaca asignado a los
       grupos (school_group.itaca_course_code) y la asignatura por su código dentro del estudio.
    2. Si la matrícula ya existe no se hace nada; si no existe se crea en el curso escolar activo.
    3. Las matrículas del curso escolar activo, de los estudios que aparecen en el fichero, que
       ya no aparecen en él se eliminan.
    4. Genera un informe con las altas y bajas por estudio y los errores encontrados.

    :param filename: Nombre del fichero CSV de matrículas de Ítaca
    """
    # 1. Carga y validación del fichero
    filepath = self.env['ir.config_parameter'].sudo().get_param('maya_core.itaca_students_data_folder')
    if not filepath:
      raise Exception("No se ha definido la ruta de la carpeta de datos de Ítaca.")

    csv_file = Path(filepath) / filename
    if not csv_file.exists():
      raise Exception(f"El fichero de matrículas no existe en la ruta: {csv_file}")

    try:
      # dtype=str para no perder los ceros a la izquierda de los códigos (ej. 0175)
      df, _ = read_csv(csv_file, dtype=str)
    except Exception as e:
      raise Exception(f"Error al leer el fichero CSV de matrículas: {str(e)}")

    content_cols = [col for col in df.columns if col.startswith('contenido')]

    # 2. Precarga de datos para no buscar por cada línea
    nias = {clean_str(nia) for nia in df['alumno']} - {''}
    students = {
      s.nia: s for s in self.env['maya_core.student'].search([('nia', 'in', list(nias))])
    }

    # un curso de Ítaca puede estar en varios grupos (ej. 1CFSAFI_A y 1CFSAFI_B)
    course_studies = defaultdict(lambda: self.env['maya_core.study'])
    for group in self.env['maya_core.school_group'].search([('itaca_course_code', '!=', False)]):
      course_studies[group.itaca_course_code] |= group.study_id

    codes = {clean_str(code) for code in df[content_cols].stack()} - {''}
    subjects_by_code = defaultdict(lambda: self.env['maya_core.subject'])
    for subject in self.env['maya_core.subject'].search([('code', 'in', list(codes))]):
      subjects_by_code[subject.code] |= subject

    # OJO esto funciona por que solo hay un año escolar activo por compañia
    active_school_years = {
      sy.company_id.id: sy.id
      for sy in self.env['maya_core.school_year'].search([('state', '=', '1')])
    }

    errors = defaultdict(set)     # mensaje de error -> NIAs afectados
    file_keys = set()             # (student_id, subject_id, study_id, school_year_id) del fichero
    file_study_ids = set()        # estudios que aparecen en el fichero
    protected_keys = set()        # matrículas que no se eliminan por no poder resolverse la línea
    protected_students = set()    # alumnos con algún curso no resuelto: no se eliminan sus matrículas

    # 3. Recorrer el fichero
    for _, row in df.iterrows():
      nia = clean_str(row.get('alumno'))
      course_code = clean_str(row.get('curso'))

      student = students.get(nia)
      if not student:
        errors["El alumno no existe en Maya"].add(nia or 'Sin NIA')
        continue

      studies = course_studies.get(course_code)
      if not studies:
        errors[f"El curso de Ítaca '{course_code}' no está asignado a ningún grupo"].add(nia)
        protected_students.add(student.id)
        continue

      if len(studies) > 1:
        errors[f"El curso de Ítaca '{course_code}' está asignado a grupos de varios estudios ({', '.join(studies.mapped('code'))})"].add(nia)
        protected_students.add(student.id)
        continue

      study = studies
      school_year_id = active_school_years.get(study.company_id.id)
      if not school_year_id:
        errors[f"No hay curso escolar activo para el estudio {study.code}"].add(nia)
        protected_students.add(student.id)
        continue

      file_study_ids.add(study.id)

      for col in content_cols:
        code = clean_str(row.get(col))
        if not code:
          continue

        subjects = subjects_by_code.get(code)
        if not subjects:
          errors[f"El contenido '{code}' no existe en el listado de asignaturas"].add(nia)
          continue

        study_subjects = subjects.filtered(lambda s: study in s.studies_ids)
        if len(study_subjects) != 1:
          if study_subjects:
            errors[f"Hay varias asignaturas con el código '{code}' en el estudio {study.code}"].add(nia)
          else:
            errors[f"La asignatura '{code}' no pertenece al estudio {study.code}"].add(nia)
          protected_keys.update((student.id, s.id, study.id, school_year_id) for s in subjects)
          continue

        file_keys.add((student.id, study_subjects.id, study.id, school_year_id))

    # 4. Altas y bajas
    existing = {
      (r.student_id.id, r.subject_id.id, r.study_id.id, r.school_year_id.id): r
      for r in self.search([
        ('study_id', 'in', list(file_study_ids)),
        ('school_year_id', 'in', list(active_school_years.values())),
      ])
    }

    new_rels = self.create([
      {
        'student_id': student_id,
        'subject_id': subject_id,
        'study_id': study_id,
        'school_year_id': school_year_id,
      }
      for student_id, subject_id, study_id, school_year_id in file_keys - existing.keys()
    ])

    removed_rels = self.browse([
      rel.id for key, rel in existing.items()
      if key not in file_keys and key not in protected_keys and key[0] not in protected_students
    ])

    # 5. Informe (las bajas se describen antes de eliminarlas)
    report = [f"Informe de matrículas en asignaturas. Fichero: {filename}"]
    report += self._itaca_enrolments_report_section('Altas de matrícula', new_rels)
    report += self._itaca_enrolments_report_section('Bajas de matrícula', removed_rels)

    report.append("\n###################")
    report.append("Errores")
    report.append("###################")
    for msg, msg_nias in sorted(errors.items()):
      report.append(f"{msg} -> {len(msg_nias)} alumno(s): {', '.join(sorted(msg_nias))}")
    if protected_students:
      report.append(f"\nNo se han eliminado matrículas de {len(protected_students)} alumno(s) con algún curso de Ítaca no resuelto.")

    removed_rels.unlink()

    date_str = datetime.now().strftime("%y%m%d%H%M")
    log_file = Path(filepath) / f"informe_matriculas_asignaturas_itaca_{date_str}.txt"
    try:
      with open(log_file, 'w', encoding='utf-8') as f:
        for line in report:
          f.write(f"{line}\n")
    except IOError as e:
      raise e

    return

  @api.model
  def _itaca_enrolments_report_section(self, title, rels):
    """
    Devuelve las líneas del informe de matrículas agrupadas por estudio
    """
    lines = ["\n###################", title, "###################"]

    for study in rels.study_id.sorted('code'):
      study_rels = rels.filtered(lambda r: r.study_id == study).sorted(
        lambda r: (r.student_id.surname, r.subject_id.code)
      )
      lines.append(f"\n[{study.code}] {study.name}: {len(study_rels)}")
      for rel in study_rels:
        lines.append(
          f"  NIA: {rel.student_id.nia} | {rel.student_id.student_info} "
          f"| {rel.subject_id.code} - {rel.subject_id.name}"
        )

    lines.append(f"\nTotal: {len(rels)}")
    return lines
