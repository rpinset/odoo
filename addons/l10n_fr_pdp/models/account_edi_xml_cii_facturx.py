from odoo import models


class AccountEdiXmlCII(models.AbstractModel):
    _inherit = "account.edi.xml.cii"

    def _get_exchanged_document_vals(self, invoice):
        # Extend `account_edi_xml_cii` to add mandatory default notes [BR-FR-05]
        result = super()._get_exchanged_document_vals(invoice)

        result['included_note_list'].extend([
            {
                'subject_code': code,
                'content': content,
            } for code, content in invoice._l10n_fr_pdp_get_default_notes().items()
        ])

        return result

    def _export_invoice_vals(self, invoice):
        vals = super()._export_invoice_vals(invoice)
        if not invoice.l10n_fr_is_company_french:
            return vals

        seller = invoice.company_id.partner_id.commercial_partner_id
        if siren := seller._l10n_fr_pdp_get_siren():
            vals['seller_specified_legal_organization'] = siren

        buyer_id_type, buyer_id_value = invoice.commercial_partner_id._l10n_fr_pdp_get_base_identifier()
        if buyer_id_type in ('siren', 'siret') and buyer_id_value:
            vals['buyer_specified_legal_organization'] = buyer_id_value[:9]

        vals['business_process_profile_id'] = invoice._l10n_fr_pdp_get_profile_id()
        return vals
