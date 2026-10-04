# -*- coding: utf-8 -*-
"""
Endpoint v1 para notificar que el fichero de datos de Itaca está listo para ser procesado.

POST /api/v1/student/notify-itaca-datafile-ready
Authorization: Bearer <api_key>
Content-Type: application/json

{
    "filename": "nombre_del_fichero.csv"
}
"""
import os
import json
import logging
import threading

import odoo
from odoo import api, http, SUPERUSER_ID
from odoo.http import request
from odoo.modules.registry import Registry

from ..api_auth import ApiBaseController, error_response, json_response

_logger = logging.getLogger(__name__)

class StudentController(ApiBaseController):

  @http.route(
      '/api/v1/student/notify-itaca-datafile-ready',
      type='http',
      auth='none',        # Autenticación gestionada manualmente vía API Key en _authenticate_app
      methods=['POST'],
      csrf=False, 
      cors='*',
      save_session=False,
  )
  def notify_itaca_datafile_ready(self, **kwargs):
    """
    Endpoint M2M para notificar que un fichero de datos de Ítaca está listo para procesar.
    Solo requiere autenticar la aplicación remitente mediante API Key.
    """
    # 1. Validar la aplicación remitente (API Key)
    app_user, err = self._authenticate(
        require_human_user=False, 
        required_group='maya_core.group_itaca_integration'  # solo las app de ese grupo
    )
    if err:
        return err

    # 2. Obtener el path del fichero
    folder_path = request.env['ir.config_parameter'].sudo().get_param('maya_core.itaca_students_data_folder')
    if not folder_path:
      _logger.error("No se ha definido la ubicación del fichero de datos de alumnos de Ítaca en la configuración.")
      return error_response(
          'La ubicación del fichero de datos de alumnos de Ítaca no está configurado en los Ajustes del sistema Maya | Core.',
          'MISSING_CONFIGURATION',
          400
      )

    # 3. Parsear el body JSON
    try:
      body = json.loads(request.httprequest.data or '{}')
    except json.JSONDecodeError:
      return error_response('El cuerpo de la petición no es JSON válido.', 'INVALID_JSON', 400)

    filename = body.get('filename') or kwargs.get('filename')
    if not filename:
      return error_response('El parámetro "filename" es obligatorio en el payload.', 'MISSING_PARAM', 400)
    
    # 4. Validar que el fichero existe
    full_filepath = os.path.join(folder_path, filename)

    if not os.path.isfile(full_filepath):
        _logger.warning("El fichero especificado '%s' no existe en la ruta '%s'.", filename, folder_path)
        return error_response(
            f'El fichero "{filename}" no existe en el servidor o la ruta no es accesible.',
            'FILE_NOT_FOUND',
            404
        )

    # 5. Lanzar la importación en un hilo secundario en segundo plano
    db_name = request.db
    thread = threading.Thread(
        target=self._run_import_in_thread,
        args=(db_name, filename),
        name=f"ItacaImportThread-{filename}"
    )
    thread.start()

    # 4. Responder inmediatamente a la aplicación solicitante
    return json_response(
        {
            'success': True,
            'status': 'queued',
            'message': f'Notificación recibida. El fichero "{filename}" se procesará en segundo plano.',
        },
        status=202,  # 202 Accepted
    )

  def _run_import_in_thread(self, db_name, filename):
    """
    Método auxiliar ejecutado en un hilo independiente.
    Crea su propia transacción y entorno de Odoo.
    Agnóstico a la compañía y con permisos de SUPERUSER_ID para procesar todos los alumnos.
    """
    _logger.info("Iniciando hilo secundario para procesar el fichero de Ítaca: %s", filename)
        
    registry = Registry(db_name)
    with registry.cursor() as cr:
      # Creamos el entorno con SUPERUSER_ID y permitimos acceso multientidad/multicompañía
      env = odoo.api.Environment(cr, SUPERUSER_ID, {})
      company_ids = env['res.company'].sudo().search([]).ids

      env = env(context=dict(env.context, allowed_company_ids=company_ids))
      
      try:
        # Invocamos la función del modelo 'maya_core.student' pasando el nombre del fichero
        student_model = env['maya_core.student'].sudo()
        student_model.process_itaca_import(filename)
        
        cr.commit()
        _logger.info("Procesamiento del fichero %s completado con éxito.", filename)
      except IOError as e: # falla la creacion del informe.. pero mantenemos la matricula
        cr.commit()
        _logger.error("No se pudo generar el informe de la importación: %s", str(e))
      except Exception as e:
        cr.rollback()
        _logger.exception('Error procesando la importación asíncrona de Ítaca (%s): %s', filename, e)