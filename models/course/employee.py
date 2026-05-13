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
  
  dni = fields.Char(_('DNI'), related="user_id.login", readonly = True, store = True)
  name = fields.Char(string = _('Nombre'), related="user_id.name", readonly = True, store = True)
  surname = fields.Char(string = _('Apellidos'), related="user_id.surname", readonly = True, store = True)
  phone_extension = fields.Char(string = _("Extensión"), size = 6)
  work_email = fields.Char(string = 'Email', related = 'user_id.email', store = True)
  employee_info = fields.Char(string = _('Nombre completo'), compute = '_compute_full_employee_info')

  employee_type = fields.Selection([
        ('profesor', _('Profesor/a')),
        ('pas', 'PAS'),
        ], string = _('Tipo de empleado'), default = 'profesor', required = True,
        help = "Permite categorizar a los empleados en profesores o personal de administración.")
  
  position_type = fields.Selection([
        ('AJC', _('Adjudicaciones julio carrera')),
        ('AJT', _('Adjudicaciones julio interino')),
        ('AS', _('Adjudicaciones septiembre')),
        ('PRM', _('Definitiva')),
        ('CMS', _('Comisión servicios')),
        ('CES', _('Específica')),
        ('ESPJ', _('Puesto específico')),
        ('SUP', _('Suprimida')),
        ], string = _('Tipo de plaza'), default = 'ESPJ',
        help = _("Tipo de plaza que el empleado/a tienen asignada en el curso actual."))

  car_registration_number_1 = fields.Char(string = _('Matrícula principal'), size = 7)
  car_registration_number_2 = fields.Char(string = _('Matrícula secundaria'), size = 7)
  car_registration_number_3 = fields.Char(string = _('Matrícula terciaria'), size = 7)

  # sustituciones. Simulo un One2one con dos many2one, un one2many y funciones calculadas
  sick_leave = fields.Boolean(default = False)
  replaced_by_id = fields.Many2one('maya_core.employee', string=_('Sustituye a'), 
                                    compute='_compute_teacher', 
                                    inverse='_teacher_inverse')
  replaces_id = fields.Many2one('maya_core.employee', string='Sustituye a')
  replaced_by_ids = fields.One2many('maya_core.employee', 'replaces_id')

  team_ids = fields.Many2many('maya_core.team', required = True, string = _('Departamentos y equipos'))
  """ roles_ids = fields.Many2many('maya_core.rol', string = 'Cargos')
   """
  active = fields.Boolean('Activo', related='user_id.active', help = 'Indica si el usuario maya_core asociado está activo')

  lang = fields.Char(
    string=_('Idioma'),
    compute='_compute_lang',
    inverse='_inverse_lang',
    store=True,
    help=_('Idioma configurado por defecto para el usuario vinculado. Para su modificación utilizar el módulo maya-dashboard o modificar el usuario de Odoo'))
  )
  
  subjects_ids = fields.One2many('maya_core.subject_employee_rel', 'employee_id', string = _('Asignaturas/Módulos'))

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