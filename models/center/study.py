from odoo import models, fields, _

class Study(models.Model):
  """  
  Define un estudio: ciclo formativo, tipo bachillerato, etc
  """

  _name = 'maya_core.study'
  _description = 'Ciclo Formativo/Tipo de bachillerato/ESPA/FPA'

  # index=True para optimizar las búsquedas por empresa
  company_id = fields.Many2one(
      'res.company', 
      string=_('Tipo de enseñanza'),
      required=True, 
      default=lambda self: self.env.company,
      index=True
    )

  abbr = fields.Char('Abreviatura', size = 5, required = True, translate = True)
  name = fields.Char('Nombre', required = True, translate = True)
  code = fields.Char('Código', required = True, size = 7)

  grade = fields.Selection([
      ('NG', ''),
      ('GB', 'Grado Básico'),
      ('GM', 'Grado Medio'),
      ('GS', 'Grado Superior'),
      ('CE', 'Curso de Especialización')], 
      string ='Grado', default = '',
      help = "Grado del curso. Solo Ciclos Formativos")
  
  family = fields.Selection([
      ('NF', 'Sin familia'),
      ('AFD', 'Actividades Físicas y Deportivas'),
      ('AD', 'Administración y Gestión'),
      ('AG', 'Agraria'),
      ('AG', 'Artes Gráficas'),
      ('AA', 'Artes y Artesanías'),
      ('CM', 'Comercio y Marketing'),
      ('EOC', 'Edificación y Obra Civil'),
      ('EE', 'Electricidad y Electrónica'),
      ('EA', 'Energía y Agua'),
      ('FM', 'Fabricación Mecánica'),
      ('HT', 'Hostelería y Turismo'),
      ('IP', 'Imagen Personal'),
      ('IS', 'Imagen y Sonido'),
      ('IA', 'Industrias Alimentarias'),
      ('IE', 'Industrias Extractivas'),
      ('IC', 'Informática y Comunicaciones'),
      ('IM', 'Instalación y Mantenimiento'),
      ('MMC', 'Madera, Mueble y Corcho'),
      ('MP','Marítimo Pesquera'),
      ('QMC', 'Química'),
      ('SND', 'Sanidad'),
      ('SMA', 'Seguridad y Medio Ambiente'),
      ('SSCC', 'Servicios Socioculturales y a la Comunidad'),
      ('TCP', 'Textil, Confección y Piel'),
      ('TMV', 'Transporte y Mantenimiento de Vehículos'),
      ('VC', 'Vidrio y Cerámica')
    ], string ='Familia formativa', default = 'NF',
    required = True, help = "Familia formativa a la que pertenece el curso. Solo Ciclos Formativos")

  law = fields.Selection([
      ('NR', 'No reglada'),
      ('LOE', 'LOE'),
      ('LOGSE', 'LOGSE'),
      ('LFP', 'LFP'),
      ('LOMLOE', 'LOMLOE'),
      ], string ='Plan de estudios', default = 'LOMLOE', required = True,
      help = "Ley Educativa a la que está adscrito el curso.")
  
  active = fields.Boolean('Activo', default=True)

  subjects_ids = fields.Many2many('maya_core.subject', string = 'Asignaturas / Módulos')
