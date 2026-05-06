from odoo import models, fields, api, _
from odoo.exceptions import  UserError
import secrets
from datetime import timedelta

import logging

_logger = logging.getLogger(__name__)

class SignatureBatch(models.Model):
  """
  Lote de documentos para firma digital
  """
  _name = 'maya_core.signature.batch'
  _description = 'Lote de Firma Electrónica'
  _order = 'create_date desc'
    
  name = fields.Char('Nombre', required=True, default='Nuevo lote')
  state = fields.Selection([
        ('draft', 'Borrador'),
        ('ready', 'Listo para firmar'),
        ('processing', 'Firmando'),
        ('done', 'Completado'),
        ('error', 'Error'),
        ('cancelled', 'Cancelado'),
  ], default='draft', string='Estado', tracking=True)
    
  user_id = fields.Many2one('res.users', 'Usuario', default=lambda self: self.env.user, required=True)
  document_ids = fields.One2many('maya_core.signature.batch_document', 'batch_id', 'Documentos')
  document_count = fields.Integer('Documentos', compute='_compute_counts', store=True)
  signed_count = fields.Integer('Firmados', compute='_compute_counts', store=True)
  error_count = fields.Integer('Errores', compute='_compute_counts', store=True)
  
  create_date = fields.Datetime('Fecha creación', readonly=True)
  sign_date = fields.Datetime('Fecha firma', readonly=True)
  
  session_token = fields.Char('Token de sesión', readonly=True, copy=False)
  token_expiry = fields.Datetime('Token expira', readonly=True, copy=False)
    

  @api.depends('document_ids.state')
  def _compute_counts(self):
    for batch in self:
      batch.document_count = len(batch.document_ids)
      batch.signed_count = len(batch.document_ids.filtered(lambda d: d.state == 'signed'))
      batch.error_count = len(batch.document_ids.filtered(lambda d: d.state == 'error'))
  
  def action_prepare_signature(self):
    """
    Prepara el lote para firma (genera documentos si es necesario)
    """
    self.ensure_one()
    
    if not self.document_ids:
      raise UserError(_('El lote no tiene documentos. Es necesario añadir documentos primero.'))
    
    # genero los PDFs de los documentos que no los tengan
    for doc in self.document_ids:
      if not doc.pdf_content:
        doc._generate_pdf()
      
      self.state = 'ready'
      
      return {
        'type': 'ir.actions.client',
        'tag': 'display_notification',
        'params': {
            'title': _('Listo'),
            'message': _('El lote está listo para firmar'),
            'type': 'success',
        }
      }
    
  def action_sign_automatically(self):
    """
    Devuelve la URL del protocolo maya://sign para firmar electrónicamente de manera automática
    """
    self.ensure_one()
    
    if self.state not in ['ready', 'error']:
      raise UserError(_('El lote debe estar en estado "Listo para firmar"'))
    
    # Generar token de sesión que expira en 10 minutos
    token = secrets.token_urlsafe(32)
    expiry = fields.Datetime.now() + timedelta(minutes=10)
    
    self.write({
      'session_token': token,
      'token_expiry': expiry,
      'state': 'processing'
    })
    
    base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
    protocol_url = f"maya://sign?batch={self.id}&token={token}&url={base_url}&db={self.env.cr.dbname}"
    
    _logger.info(f"Lanzando protocolo de firma para lote {self.id}")
    
    # Por ahora no los paso a maya_signer
    """  'batch_name': self.name,
        'document_count': self.document_count, """
    
    return protocol_url, self.id 
  
  @api.model
  def validate_session_token(self, batch_id, token):
    """
    Valida el token de sesión.
    Llamado desde el servicio local de firma vía XML-RPC
    """
    batch = self.browse(batch_id)
    
    if not batch.exists():
        return {'valid': False, 'error': 'Lote no encontrado'}
    
    if not batch.session_token or batch.session_token != token:
        return {'valid': False, 'error': 'Token inválido'}
    
    if not batch.token_expiry or fields.Datetime.now() > batch.token_expiry:
        return {'valid': False, 'error': 'Token expirado'}
    
    if batch.state != 'processing':
        return {'valid': False, 'error': f'Estado inválido: {batch.state}'}
    
    return {
        'valid': True,
        'batch_name': batch.name,
        'user_name': batch.user_id.name,
    } 
  
  @api.model
  def finalize_batch(self, batch_id, token, success_count, error_count):
    """
    Finaliza el lote después de la firma
    Llamado desde el servicio local vía XML-RPC
    """
    # Valido el token
    validation = self.validate_session_token(batch_id, token)
    if not validation['valid']:
      raise UserError(validation['error'])
      
    batch = self.browse(batch_id)
      
    if error_count == 0:
      state = 'done'
    elif success_count > 0:
      state = 'done'  # Parcialmente completado
    else:
      state = 'error'
      
    batch.write({
      'state': state,
      'sign_date': fields.Datetime.now(),
      'session_token': False,  # Invalidar token
    })
      
    _logger.info(f"Lote {batch_id} finalizado: {success_count} firmados, {error_count} errores")
      
    return {
      'success': True,
      'state': state,
      'message': f'Firmados: {success_count}, Errores: {error_count}'
      }

