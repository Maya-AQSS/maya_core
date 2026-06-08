# -*- coding: utf-8 -*-
"""
Endpoint v1 para modificar datos del empleado autenticado.

PATCH /api/v1/employee/me
Authorization: Bearer <api_key>
Content-Type: application/json

Body (todos los campos son opcionales):
{
    "phone_extension": "1234",
    "employee_type":   "profesor",
    "position_type":   "PRM",
    "car_registration_number_1": "1234ABC",
    "car_registration_number_2": "5678DEF",
    "car_registration_number_3": "",
    "sick_leave": false,
    "lang": "es_ES"
}

Campos ignorados (no modificables vía API):
  name, surname, dni, work_email, user_id, active, subjects_ids, team_ids,
  replaced_by_id, replaces_id, employee_info
"""
import json
import logging

from odoo import http
from odoo.http import request
from odoo.exceptions import ValidationError

from ..api_auth import ApiBaseController, json_response, error_response

_logger = logging.getLogger(__name__)


# Campos que la API PERMITE modificar y su tipo de validación básica
ALLOWED_FIELDS = {
    'phone_extension':          str,
    'car_registration_number_1': str,
    'car_registration_number_2': str,
    'car_registration_number_3': str,
    'lang':                     str,
}

class EmployeeController(ApiBaseController):

    @http.route(
        '/api/v1/employee/me',
        type='http',
        auth='none',        # auth='none': gestionamos la auth manualmente con Bearer
        methods=['PATCH'],
        csrf=False,
        cors='*',
        save_session=False,
    )
    def update_employee(self):
      """
      Actualiza los campos permitidos del empleado vinculado al usuario autenticado.
      Solo modifica los campos enviados en el body. Campos no permitidos son ignorados.
      """

      # Parsear body (necesario antes de autenticar)
      try:
        body = json.loads(request.httprequest.data or '{}')
      except json.JSONDecodeError:
        return error_response('El cuerpo no es JSON válido.', 'INVALID_JSON', 400)

      # Autenticación doble: app + usuario humano
      user, err = self._authenticate(body)
      if err:
          return err

      # Obtener empleado vinculado al usuario 
      employee, err = self._get_employee(user)
      if err:
        return err

      # Parsear body JSON 
      try:
        body = json.loads(request.httprequest.data or '{}')
      except json.JSONDecodeError:
        return error_response(
            'El cuerpo de la petición no es JSON válido.',
            'INVALID_JSON',
            400,
        )

      if not isinstance(body, dict):
        return error_response(
            'El cuerpo debe ser un objeto JSON.',
            'INVALID_BODY',
            400,
        )

      # Filtrar campos: solo los permitidos, ignorar el resto 
      ignored_fields = [k for k in body if k not in ALLOWED_FIELDS]
      update_vals = {}

      for field, expected_type in ALLOWED_FIELDS.items():
        if field not in body:
          continue  # no enviado → no se toca

        value = body[field]

        # Permitir null/empty string para "limpiar" un campo opcional
        if value is None or value == '':
          update_vals[field] = value if expected_type == str else False
          continue

        # Validación de tipo básica
        if not isinstance(value, expected_type):
          return error_response(
              f'El campo "{field}" debe ser de tipo {expected_type.__name__}.',
              'INVALID_FIELD_TYPE',
              400,
          )

      # Limpiar strings
      for field in list(update_vals.keys()) + [k for k in body if k in ALLOWED_FIELDS]:
        if field in body and isinstance(body[field], str):
          update_vals[field] = body[field].strip()

      # Validaciones de dominio
      if 'lang' in update_vals and update_vals['lang']:
        active_lang = request.env['res.lang'].sudo().search([
            ('code', '=', update_vals['lang']),
            ('active', '=', True),
        ], limit=1)
        if not active_lang:
          return error_response(
              f'El idioma "{update_vals["lang"]}" no está activo en Odoo.',
              'LANG_NOT_ACTIVE',
              400,
          )

      # Nada que actualizar 
      if not update_vals:
          return json_response({
              'success': True,
              'message': 'No se enviaron campos modificables.',
              'ignored_fields': ignored_fields,
              'employee_id': employee.id,
          })

      # Aplicar cambios
      try:
          employee.sudo().write(update_vals)
          _logger.info(
              'API v1: empleado id=%s actualizado por user_id=%s. Campos: %s',
              employee.id, user.id, list(update_vals.keys()),
          )
      except ValidationError as e:
          return error_response(str(e), 'VALIDATION_ERROR', 422)
      except Exception as e:
          _logger.exception(
              'API v1: error inesperado actualizando empleado id=%s', employee.id
          )
          return error_response(
              'Error interno al actualizar el empleado.',
              'INTERNAL_ERROR',
              500,
          )

      # Respuesta exitosa 
      return json_response({
          'success': True,
          'employee_id': employee.id,
          'updated_fields': list(update_vals.keys()),
          'ignored_fields': ignored_fields,
      })