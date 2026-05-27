# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.exceptions import ValidationError

import re

class Employee(models.Model):
  """
  Define un empleado del centro
  """

  _name = 'maya_core.employee'
  _description = 'Empleado del centro (profesor o PAS)'
  _order = 'surname'
  _rec_name = 'employee_info' 

  # simulación de un One2one
  # en user hay un many2one y aqui un one2many
  user_ids = fields.One2many('res.users', 'maya_employee_id')
  # creo un campo que obtenga su valor y que pueda darle valor al employee_id 
  # a partir de user_ids
  user_id = fields.Many2one('res.users', 
                            compute = '_compute_user_id', 
                            inverse = '_user_inverse',
                            store=True)
  
  dni = fields.Char('DNI', related="user_id.login", readonly = True, store = True)
  name = fields.Char(string = 'Nombre', related="user_id.name", readonly = True, store = True)
  surname = fields.Char(string = 'Apellidos', related="user_id.surname", readonly = True, store = True)
  phone_extension = fields.Char(string ="Extensión", size = 6)
  work_email = fields.Char(string = 'Email', related = 'user_id.email', store = True)
  personal_email = fields.Char(string = 'Email personal', help = 'Email personal del empleado')
  employee_info = fields.Char(string = 'Nombre completo', compute = '_compute_full_employee_info')

  employee_type = fields.Selection([
        ('profesor', 'Profesor/a'),
        ('pas', 'PAS'),
        ], string = 'Tipo de empleado', default = 'profesor', required = True,
        help = "Permite categorizar a los empleados en profesores o personal de administración.")
  
  position_type = fields.Selection([
        ('AJC', 'Adjudicaciones julio carrera'),
        ('AJT', 'Adjudicaciones julio interino'),
        ('AS', 'Adjudicaciones septiembre'),
        ('PRM', 'Definitiva'),
        ('CMS', 'Comisión servicios'),
        ('CES', 'Específica'),
        ('ESPJ', 'Puesto específico'),
        ('SUP', 'Suprimida'),
        ], string = 'Tipo de plaza', default = 'ESPJ',
        help = "Tipo de plaza que el empleado/a tienen asignada en el curso actual.")

  car_registration_number_1 = fields.Char(string = 'Matrícula principal', size = 7)
  car_registration_number_2 = fields.Char(string = 'Matrícula secundaria', size = 7)
  car_registration_number_3 = fields.Char(string = 'Matrícula terciaria', size = 7)

  # sustituciones. Simulo un One2one con dos many2one, un one2many y funciones calculadas
  sick_leave = fields.Boolean(default = False)
  replaced_by_id = fields.Many2one('maya_core.employee', string='Sustituye a', 
                                    compute='_compute_teacher', 
                                    inverse='_teacher_inverse')
  replaces_id = fields.Many2one('maya_core.employee', string='Sustituye a')
  replaced_by_ids = fields.One2many('maya_core.employee', 'replaces_id')

  team_ids = fields.Many2many('maya_core.team', required = True, string = 'Departamentos y equipos')
  """ roles_ids = fields.Many2many('maya_core.rol', string = 'Cargos')
   """
  active = fields.Boolean('Activo', related='user_id.active', help = 'Indica si el usuario maya_core asociado está activo')

  lang = fields.Char(
    string='Idioma',
    compute='_compute_lang',
    inverse='_inverse_lang',
    store=True,
    help='Idioma configurado por defecto para el usuario vinculado. Para su modificación utilizar el módulo maya-dashboard o modificar el usuario de Odoo'
  )
  
  
  subjects_ids = fields.One2many('maya_core.subject_employee_rel', 'employee_id', string = 'Asignaturas/Módulos')

  mentor_id = fields.Many2one('maya_core.employee', string='Mentor/a')

  iban = fields.Char(
        string='IBAN',
        size=34,                    # Longitud máxima de un IBAN
        tracking=True,
        help='International Bank Account Number'
    )
  
  comments = fields.Text(string = 'Observaciones', help = 'Información sobre el empleado.')

  supervisor_id = fields.Many2one(
      'maya_core.employee', 
      string='Supervisor/a',
      domain="[('id', 'in', available_supervisor_ids)]" # Filtra usando el campo computado
  )
  
  available_supervisor_ids = fields.Many2many('maya_core.employee', compute='_compute_available_supervisors')

  keys = fields.Selection([
        ('HO', 'Entregadas'),
        ('RT', 'Devueltas'),
        ('PN', 'Pendiente de devolución'),
        ], string = 'Estado llaves', default = False,
        help = "Estado en el que se encuentra la entrega de llaves.")

  date_keys_handover = fields.Date(string='Entrega de llaves',help = "Fecha en la que se hace la entrega de llaves.")
  date_keys_return = fields.Date(string='Devolución de llaves',help = "Fecha en la que se hace la devolución de llaves.")

  @api.depends('user_ids')
  def _compute_user_id(self):
    """
    Asigna el usuario como primer elemento de la relación doble uno a muchos
    """
    for record in self:
      if len(record.user_ids) > 0:
        record.user_id = record.user_ids[0] 

  def _user_inverse(self):
    """
    En el caso de que el user_id cambie, se modifica el maya_employee_id de ese user_id
    """
    for record in self:
      if len(record.user_ids) > 0:
        # borramos la referencia previa
        user = record.env['res.users'].browse(record.user_ids[0].id)
        user.maya_employee_id = False
    
      record.user_id.maya_employee_id = record

  @api.depends('replaced_by_ids')
  def _compute_teacher(self):
    for record in self:
      if len(record.replaced_by_ids) > 0:
        record.replaced_by_id = record.replaced_by_ids[0]

  def _teacher_inverse(self):
    for record in self:
      if len(record.replaced_by_ids) > 0:
        # delete previous reference
        teacher = self.env['maya_core.employee'].browse(record.replaced_by_ids[0].id)
        teacher.replaces_id = False
      # set new reference
      record.replaced_by_id.replaces_id = record

  @api.depends('user_id', 'user_id.lang')
  def _compute_lang(self):
    for record in self:
      record.lang = record.user_id.lang if record.user_id else False

  def _inverse_lang(self):
    """
    Cuando se cambia el idioma del empleado, lo propaga al usuario vinculado.
    Valida que el idioma esté activo en Odoo antes de aplicarlo.
    """
    for record in self:
      if not record.user_id or not record.lang:
        continue
      active_lang = record.env['res.lang'].search([
        ('code', '=', record.lang),
        ('active', '=', True),
      ], limit=1)
      if not active_lang:
        raise ValidationError(
          _('El idioma "%s" no está activo en Odoo. '
            'Actívalo primero en Ajustes → Idiomas.') % record.lang
        )
      record.user_id.sudo().write({'lang': record.lang})

  def _compute_full_employee_info(self):
    for record in self:
      if record.surname != False and record.name != False:
        record.employee_info = record.surname + ', ' + record.name
      else: 
        record.employee_info = False    

  _CAR_REGEX = r'^[0-9]{4}[A-Z]{3}$'
  _CAR_ERROR = _(
    "La matrícula debe tener exactamente 4 números seguidos de 3 letras mayúsculas. "
    "Ejemplo válido: 1234ABC"
  )

  @api.onchange('car_registration_number_1')
  def _onchange_car_registration_number_1_upper(self):
    if self.car_registration_number_1:
        self.car_registration_number_1 = self.car_registration_number_1.upper()
        
  @api.onchange('car_registration_number_2')
  def _onchange_car_registration_number_2_upper(self):
    if self.car_registration_number_2:
        self.car_registration_number_2 = self.car_registration_number_2.upper()
    
  @api.onchange('car_registration_number_3')
  def _onchange_codigo_upper(self):
    if self.car_registration_number_1:
        self.car_registration_number_3 = self.car_registration_number_3.upper()

  @api.constrains('car_registration_number_1','car_registration_number_2','car_registration_number_3')
  def _check_car_registration_numbers(self):
    for record in self:
      for plate in (record.car_registration_number_1,record.car_registration_number_2,record.car_registration_number_3):
        if plate and not re.match(self._CAR_REGEX, plate):
          raise ValidationError(self._CAR_ERROR)
        
  @api.constrains('iban')
  def _check_iban(self):
    for record in self:
      if record.iban:
        # Limpia espacios y pasa a mayúsculas
        iban_clean = record.iban.replace(' ', '').upper()
        
        try:
          # Usa la validación oficial de Odoo
          self.env['res.partner.bank']._validate_iban(iban_clean)
          # Opcional: guardar siempre formateado
          record.iban = ' '.join([iban_clean[i:i+4] for i in range(0, len(iban_clean), 4)])
        except Exception:
          raise ValidationError(_("El IBAN introducido no es válido."))
        
  @api.constrains('personal_email')
  def _check_email_format(self):
    email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    for record in self:
      if record.personal_email and not re.match(email_regex, record.personal_email):
        raise ValidationError(_("El formato del correo electrónico no es válido."))
      
  @api.depends('team_ids') 
  def _compute_available_supervisors(self):
    try:
      # Buscamos el registro real del team usando su XML_ID externo
      target_team = self.env.ref('maya_core.dep_ed')  # refrencia del equipo directivo
    except ValueError:
      # Salvaguarda por si el módulo aún no ha cargado el archivo de datos del team
      target_team = False

    if target_team:
      # Buscamos todos los empleados que tengan este equipo asignado en su Many2many
      supervisors = self.env['maya_core.employee'].search([
          ('team_ids', 'in', target_team.id)
      ])
      valid_ids = supervisors.ids
    else:
      valid_ids = []

    for record in self:
      # Asignamos la lista de IDs permitidos a cada registro
      record.available_supervisor_ids = [(6, 0, valid_ids)]

  @api.constrains('keys', 'date_keys_handover', 'date_keys_return')
  def _check_keys_dates(self):
    """
    Verifica que las fechas de entrega y devolución de llaves estén completas según el estado.
    """
    for record in self:
      if record.keys in ('HO', 'PN') and not record.date_keys_handover:
        raise ValidationError(_(
            "El estado actual requiere obligatoriamente una 'Fecha de entrega de llaves'."
        ))
      
      if record.keys == 'PN' and record.date_keys_handover:
        raise ValidationError(_(
            "No puede existir una 'Fecha de entrega de llaves' si el estado es 'Pendiente de devolución'."
        ))
      
      if record.keys == 'RT':
        if not record.date_keys_handover or not record.date_keys_return:
          raise ValidationError(_(
              "El estado 'Devueltas' requiere tanto la 'Fecha de entrega' como la 'Fecha de devolución'."
          ))
      
  @api.onchange('keys')
  def _onchange_keys_populate_dates(self):
    """
    Rellena automáticamente la fecha de hoy si el usuario cambia el estado,
    ahorrando clics en la interfaz.
    """
    today = fields.Date.context_today(self)
    if self.keys == 'HO':
      if not self.date_keys_handover:
          self.date_keys_handover = today
      self.date_keys_return = False # Al entregar, limpiamos una posible fecha de devolución previa
        
    elif self.keys == 'PN':
      self.date_keys_return = False
        
    elif self.keys == 'RT':
      if not self.date_keys_return:
        self.date_keys_return = today
      if not self.date_keys_handover:
        self.date_keys_handover = today

  @api.constrains('iban')
  def _check_iban(self):
    """
    Verifica el formato y la validez del IBAN.
    Generado por Gemini 3.5 Flash
    """
    for record in self:
      if not record.iban:
        continue
        
      # 1. Limpieza total de espacios, guiones y pasar a mayúsculas
      iban_clean = record.iban.replace(' ', '').replace('-', '').upper()
      
      # 2. Validación de longitud básica (mínimo 15, máximo 34 caracteres)
      if not (15 <= len(iban_clean) <= 34):
        raise ValidationError(_("El IBAN no tiene una longitud válida."))
      
      # 3. Algoritmo oficial de validación IBAN (Módulo 97)
      # Reordenar: mover los 4 primeros caracteres al final
      reordered_iban = iban_clean[4:] + iban_clean[:4]
      
      # Convertir letras a números (A=10, B=11, ..., Z=35)
      numeric_iban = ""
      for char in reordered_iban:
          if char.isdigit():
              numeric_iban += char
          elif char.isalpha():
              numeric_iban += str(ord(char) - ord('A') + 10)
          else:
              raise ValidationError(_("El IBAN contiene caracteres no permitidos."))
      
      # Validar matemáticamente aplicando la operación por 97
      if int(numeric_iban) % 97 != 1:
          raise ValidationError(_("El código IBAN introducido no es válido (Fallo de checksum)."))
      
      # 4. Formatear automáticamente en bloques de 4 caracteres para mejorar la UX
      record.iban = ' '.join([iban_clean[i:i+4] for i in range(0, len(iban_clean), 4)])

  @api.onchange('iban')
  def _onchange_iban_upper(self):
    """
    Convierte el IBAN a mayúsculas al modificarlo.
    """
    if self.iban:
        self.iban = self.iban.upper()