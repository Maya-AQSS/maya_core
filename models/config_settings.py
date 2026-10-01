# -*- coding: utf-8 -*-
from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    moodle_user = fields.Char(string = 'Usuario acceso a Moodle', config_parameter='maya_core.moodle_user',
                              help = 'Usuario (clave) definido en .maya_moodleteacher')
    moodle_url = fields.Char(string = 'URL del servidor de Moodle', config_parameter='maya_core.moodle_url')

    moodle_user_admin = fields.Char(string = 'Administrador acceso a Moodle', config_parameter='maya_core.moodle_user_admin',
                              help = 'Usuario (clave) definido en .maya_moodleteacher con permisos de administración en Moodle')
    
    alias_mail_maya = fields.Char(string = 'Alias servidor de correo Maya', config_parameter='maya_core.alias_maya_mail',
                              help = 'Alias en la configuración de Odoo del servidor de correo que envia correo con el nombre de Maya')
    
    alias_mail_center = fields.Char(string = 'Alias servidor de correo Centro', config_parameter='maya_core.alias_mail_center',
                              help = 'Alias en la configuración de Odoo del servidor de correo que envia correo con el nombre del centro')

    itaca_students_data = fields.Char(string = 'Ubicación datos de alumnado', config_parameter='maya_core.itaca_students_data_folder',
                              help = 'Ubicación del fichero .csv que contiene los datos de los alumnos de Itaca para ser matriculados. Se genera con upload_itaca_students')
