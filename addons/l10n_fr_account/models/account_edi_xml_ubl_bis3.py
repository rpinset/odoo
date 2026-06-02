# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class AccountEdiXmlUblBis3(models.AbstractModel):
    _inherit = 'account.edi.xml.ubl_bis3'

    def _ubl_add_notes_nodes(self, vals):
        super()._ubl_add_notes_nodes(vals)
        invoice = vals.get('invoice')
        if not invoice:
            return
        for note_text in invoice._l10n_fr_edi_get_subject_note_ubl_texts():
            vals['document_node']['cbc:Note'].append({'_text': note_text})

    def _export_invoice_constraints(self, invoice, vals):
        constraints = super()._export_invoice_constraints(invoice, vals)
        if invoice.l10n_fr_has_retention_guarantee and not (invoice.l10n_fr_retention_clause_note or '').strip():
            constraints['l10n_fr_retention_clause_required'] = self.env._(
                "The retention clause note is required when retention guarantee is enabled.",
            )
        return constraints
