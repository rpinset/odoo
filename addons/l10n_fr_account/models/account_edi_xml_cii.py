# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class AccountEdiXmlCii(models.AbstractModel):
    _inherit = 'account.edi.xml.cii'

    def _get_exchanged_document_vals(self, invoice):
        vals = super()._get_exchanged_document_vals(invoice)
        included_note_list = list(vals.get('included_note_list') or [])
        for code, content in invoice._l10n_fr_edi_get_subject_notes().items():
            included_note_list.append({'content': content, 'subject_code': code})
        vals['included_note_list'] = included_note_list
        return vals

    def _export_invoice_constraints(self, invoice, vals):
        constraints = super()._export_invoice_constraints(invoice, vals)
        if invoice.l10n_fr_has_retention_guarantee and not (invoice.l10n_fr_retention_clause_note or '').strip():
            constraints['l10n_fr_retention_clause_required'] = self.env._(
                "The retention clause note is required when retention guarantee is enabled.",
            )
        return constraints
