# -*- coding: utf-8 -*-
from odoo import api, models, fields
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
  
  dni = fields.Char(string = 'DNI', size = 9, required = True)
  name = fields.Char(string = 'Nombre', required = True)
  surname = fields.Char(string = 'Apellidos', required = True)
  phone_extension = fields.Char(string = "Extensión", size = 6)
  work_email = fields.Char(string = 'Email', related = 'user_id.email')
  employee_info = fields.Char(string = 'Nombre completo', compute = '_compute_full_employee_info')

  employee_type = fields.Selection([
        ('profesor', 'Profesor/a'),
        ('pas', 'PAS'),
        ], string ='Tipo de empleado', default = 'profesor', required = True,
        help = "Permite categorizar a los empleados en profesores o personal de administración.")
  
  position_type = fields.Selection([
        ('AJC', 'Adjudicaciones julio carrera'),
        ('AJT', 'Adjudicaciones julio interino'),
        ('AS', 'Adjudicaciones septiembre'),
        ('PRM', 'Definitiva'),
        ('ESP', 'Específica'),
        ('ESPJ', 'Puesto específico'),
        ('SUP', 'Suprimida'),
        ], string ='Tipo de plaza', default = 'ESPJ', required = True,
        help = "Tipo de plaza que el empleado/a tienen asignada.")
  
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
  
  departament_ids = fields.Many2many('maya_core.departament', required = True, string = 'Departamentos y equipos')
  """ roles_ids = fields.Many2many('maya_core.rol', string = 'Cargos')
   """
  active = fields.Boolean('Activo', related='user_id.active', help = 'Indica si el usuario maya_core asociado está activo')
  
  """ subjects_ids = fields.One2many('maya_core.subject_employee_rel', 'employee_id', string = 'Módulos') """

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

  def _compute_full_employee_info(self):
    for record in self:
      if record.surname != False and record.name != False:
        record.employee_info = record.surname + ', ' + record.name
      else: 
        record.employee_info = False    

  @api.onchange('car_registration_number_1')
  def _onchange_car_registration_number_1_upper(self):
    if self.car_registration_number_1:
        self.car_registration_number_1 = self.car_registration_number_1.upper()
  
  @api.constrains('car_registration_number_1')
  def _check_car_registration_number_1(self):
    regex = r'^[0-9]{4}[A-Z]{3}$'
    for record in self:
      if record.car_registration_number_1 and not re.match(regex, record.car_registration_number_1):
          raise ValidationError(
              "La matrícula debe tener exactamente 4 números seguidos de 3 letras mayúsculas. "
              "Ejemplo válido: 1234ABC"
          )
      
  @api.onchange('car_registration_number_2')
  def _onchange_car_registration_number_2_upper(self):
    if self.car_registration_number_2:
        self.car_registration_number_2 = self.car_registration_number_2.upper()

  @api.constrains('car_registration_number_2')
  def _check_car_registration_number_2(self):
    regex = r'^[0-9]{4}[A-Z]{3}$'
    for record in self:
      if record.car_registration_number_2 and not re.match(regex, record.car_registration_number_2):
          raise ValidationError(
              "La matrícula debe tener exactamente 4 números seguidos de 3 letras mayúsculas. "
              "Ejemplo válido: 1234ABC"
          )
      
  @api.onchange('car_registration_number_3')
  def _onchange_codigo_upper(self):
    if self.car_registration_number_1:
        self.car_registration_number_3 = self.car_registration_number_3.upper()

  @api.constrains('car_registration_number_3')
  def _check_car_registration_number_3(self):
    regex = r'^[0-9]{4}[A-Z]{3}$'
    for record in self:
      if record.car_registration_number_3 and not re.match(regex, record.car_registration_number_3):
          raise ValidationError(
              "La matrícula debe tener exactamente 4 números seguidos de 3 letras mayúsculas. "
              "Ejemplo válido: 1234ABC"
          )