from odoo import models, fields, _
from odoo.exceptions import  UserError
import base64

class SignatureBatchDocument(models.Model):
  """
  Documento individual dentro de un lote
  """
  _name = 'maya_core.signature.batch_document'
  _description = 'Documento en lote de Firma'
  _order = 'sequence, id'
  
  batch_id = fields.Many2one('maya_core.signature.batch', 'Lote', required=True, ondelete='cascade', index=True)
  sequence = fields.Integer('Secuencia', default=10) # orden 
  
  # referencia al documento original
  res_model = fields.Char('Modelo', required=True, index=True)
  res_id = fields.Integer('ID Registro', required=True, index=True)
  
  # contenido
  filename = fields.Char('Nombre archivo', required=True)
  pdf_content = fields.Binary('PDF sin firmar', attachment=True)
  signed_pdf = fields.Binary('PDF firmado', attachment=True)
  signed_pdf_filename = fields.Char('Nombre PDF Firmado', readonly=True)
  
  state = fields.Selection([
    ('draft', 'Pendiente'),
    ('signed', 'Firmado'),
    ('error', 'Error'),
  ], default='draft', string='Estado')
  
  sign_date = fields.Datetime('Fecha firma')
  error_message = fields.Text('Error')
  
  # Campo computado para mostrar info del documento
  document_info = fields.Char('Documento', compute='_compute_document_info', store=False)
  
  def _compute_document_info(self):
    for doc in self:
      if doc.res_model and doc.res_id:
        try:
          record = self.env[doc.res_model].browse(doc.res_id)
          if record.exists():
              doc.document_info = record.display_name
          else:
              doc.document_info = f'{doc.res_model} #{doc.res_id} (eliminado)'
        except Exception:
          doc.document_info = f'{doc.res_model} #{doc.res_id}'
      else:
        doc.document_info = doc.filename

  def _generate_pdf(self):
    """
    Genera el PDF del documento original
    Este método debe ser llamado antes de firmar
    """
    self.ensure_one()
    
    if not self.res_model or not self.res_id:
      raise UserError(_('No hay documento asociado'))
    
    record = self.env[self.res_model].browse(self.res_id)
    
    if not record.exists():
      raise UserError(_('El documento original no existe'))
    
    # genero el pdf a partir de la función proporcionada en el mixin
    if hasattr(record, '_get_pdf_for_signature'):
      pdf_content = record._get_pdf_for_signature()
      self.pdf_content = base64.b64encode(pdf_content)
    else:
      raise UserError(_(f'El modelo {self.res_model} no soporta generación de PDF para firma'))

