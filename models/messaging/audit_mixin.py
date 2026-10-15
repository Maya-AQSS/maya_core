# -*- coding: utf-8 -*-
"""
Mixin de auditoría: los cambios en los campos elegidos de un modelo se publican en maya.audit
(`<app>.<modelo>.<created|updated|deleted>`) después del commit.

  class Employee(models.Model):
    _name = 'maya_core.employee'
    _inherit = ['maya_core.audit.mixin']
    _maya_audit_fields = ('phone_extension', 'iban', ...)   # solo estos generan eventos
    _maya_audit_redacted = ('iban',)                         # el valor no sale de Odoo: '***'

Quién: el usuario de `maya_audit_user_id` en el contexto (p. ej. el de la API, que se autentica con un
token de Keycloak y trabaja con sudo) o el usuario del entorno.
"""
from odoo import api, models

REDACTED = '***'
_NESTED_KEY = 'maya_audit_in_progress'


class MayaAuditMixin(models.AbstractModel):
  _name = 'maya_core.audit.mixin'
  _description = 'Auditoría Maya (maya.audit)'

  _maya_audit_fields = ()
  _maya_audit_redacted = ()
  _maya_audit_entity = None   # entity_type; por defecto, el nombre del modelo

  # ------------------------------------------------------------------ ORM
  @api.model_create_multi
  def create(self, vals_list):
    if not self._maya_audit_active():
      return super().create(vals_list)
    records = super(MayaAuditMixin, self._maya_audit_nested()).create(vals_list)
    fnames = self._maya_audit_tracked(self._maya_audit_fields)
    for record in records:
      after = record._maya_audit_snapshot(fnames)
      record._maya_audit_publish('created', None, after)
    return records.with_env(self.env)

  def write(self, vals):
    fnames = self._maya_audit_tracked(vals)
    if not fnames or not self._maya_audit_active():
      return super().write(vals)
    before = {record.id: record._maya_audit_snapshot(fnames) for record in self}
    result = super(MayaAuditMixin, self._maya_audit_nested()).write(vals)
    for record in self:
      after = record._maya_audit_snapshot(fnames)
      changed = [f for f in fnames if before[record.id][f] != after[f]]
      if changed:
        record._maya_audit_publish('updated',
                                   {f: before[record.id][f] for f in changed},
                                   {f: after[f] for f in changed})
    return result

  def unlink(self):
    if not self._maya_audit_active():
      return super().unlink()
    fnames = self._maya_audit_tracked(self._maya_audit_fields)
    before = [(record.id, record._maya_audit_snapshot(fnames)) for record in self]
    result = super().unlink()
    for record_id, snapshot in before:
      self.browse(record_id)._maya_audit_publish('deleted', snapshot, None)
    return result

  # ------------------------------------------------------------------ internos
  def _maya_audit_active(self):
    """Hay campos que auditar y no estamos dentro de otra escritura auditada de este modelo
    (p. ej. una restricción que reescribe el valor formateado)."""
    return bool(self._maya_audit_fields) and self._name not in self.env.context.get(_NESTED_KEY, ())

  def _maya_audit_nested(self):
    nested = tuple(self.env.context.get(_NESTED_KEY, ())) + (self._name,)
    return self.with_context(**{_NESTED_KEY: nested})

  def _maya_audit_tracked(self, fnames):
    return [f for f in self._maya_audit_fields if f in fnames and f in self._fields]

  def _maya_audit_snapshot(self, fnames):
    """Valores comparables (sin censurar) de los campos auditados, leídos con sudo."""
    self.ensure_one()
    record = self.sudo()
    snapshot = {}
    for fname in fnames:
      field = self._fields[fname]
      value = record[fname]
      if field.type == 'many2one':
        value = value.id or None
      elif field.type in ('one2many', 'many2many'):
        value = sorted(value.ids)
      elif field.type in ('date', 'datetime'):
        value = value.isoformat() if value else None
      elif field.type == 'binary':
        value = bool(value)
      elif field.type != 'boolean' and value is False:
        value = None
      snapshot[fname] = value
    return snapshot

  def _maya_audit_render(self, snapshot):
    """Lo que sale de Odoo: los campos censurados, como '***' (o vacíos si lo estaban)."""
    if snapshot is None:
      return None
    rendered = {}
    for fname, value in snapshot.items():
      if fname in self._maya_audit_redacted and value not in (None, False, ''):
        value = REDACTED
      rendered[fname] = value
    return rendered

  def _maya_audit_publish(self, action, before, after):
    self.ensure_one()
    self.env['maya_core.messaging']._publish_audit(
      self._maya_audit_entity or self._name,
      self.id,
      action,
      previous_value=self._maya_audit_render(before),
      new_value=self._maya_audit_render(after),
    )
