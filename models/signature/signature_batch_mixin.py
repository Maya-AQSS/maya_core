from odoo import models, fields, api, _
from odoo.exceptions import  UserError
import base64

import logging

_logger = logging.getLogger(__name__)


class SignatureMixin(models.AbstractModel):
  """
  Mixin para añadir capacidad de firma electrónica a un modelo
  """
  _name = 'maya_core.signature.mixin'
  _description = 'Mixin de firma electrónica'
  
  signed_pdf = fields.Binary('PDF Firmado', attachment=True, readonly=True)
  signed_pdf_filename = fields.Char('Nombre PDF Firmado', readonly=True)
  is_signed = fields.Boolean('Firmado', compute='_compute_is_signed', store=True, readonly=True)
  signature_date = fields.Datetime('Fecha firma', readonly=True)
  signature_user_id = fields.Many2one('res.users', 'Firmado por', readonly=True)
  
  @api.depends('signed_pdf')
  def _compute_is_signed(self):
    for record in self:
      record.is_signed = bool(record.signed_pdf)

      # Si cambió de False a True (se acaba de firmar)
      if bool(record.signed_pdf):
        # Llamar a un hook que cada modelo puede implementar
        if hasattr(record, '_on_document_signed'):
          record._on_document_signed()

  def action_add_to_signature_batch(self):
    """
    Método a implementar en cada modelo
    Por defecto genera y muestra el lote
    """
     
    batch = self._create_batch()

    base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
    menu = self.env.ref('maya_core.signature_batch_menu')
    action = self.env.ref('maya_core.signature_action_signature_batch')
    
    # URL vista signature_batch
    url = f"{base_url}/web#id={batch.id}&model=maya_core.signature.batch&view_type=form&menu_id={menu.id}&action={action.id}"
    
    return {
        'type': 'ir.actions.act_url',
        'url': url,
        'target': 'self', # en la misma pestaña
    }
 
  def _create_batch(self):
    """
    Añade los registros seleccionados a un nuevo lote de firma
    """
    if not self:
      raise UserError(_('No hay registros seleccionados'))
    
    # creo el batch
    batch_name = f"{self._description} - {fields.Date.today()}"
    batch = self.env['maya_core.signature.batch'].create({
      'name': batch_name,
      'state': 'draft',
    })
    
    # añado documentos al lote
    sequence = 10
    for record in self:
      # Genero PDF
      try:
        pdf_content = record._get_pdf_for_signature()

        if not pdf_content: # en caso de que no se haya generado se pasa al siguiente
          continue

        filename = record._get_signature_filename()
        
        self.env['maya_core.signature.batch_document'].create({
          'batch_id': batch.id,
          'sequence': sequence,
          'res_model': record._name,
          'res_id': record.id,
          'filename': filename,
          'pdf_content': base64.b64encode(pdf_content),
          'state': 'draft',
        })
        
        sequence += 10
          
      except Exception as e:
        _logger.error(f"Error generando PDF para {record._name}({record.id}): {e}")
        continue
    
    batch.action_prepare_signature()

    return batch

  def _get_pdf_for_signature(self):
    """
    Método a implementar en cada modelo
    Debe devolver el contenido del PDF en bytes
    """
    raise NotImplementedError(
        f'El modelo {self._name} debe implementar _get_pdf_for_signature()'
    )
  
  def _get_signature_filename(self) -> str:
    """
    Método a implementar en cada modelo
    Debe devolver el nombre del archivo para firma
    """
    self.ensure_one()
    return f"{self._name}_{self.id}.pdf"
