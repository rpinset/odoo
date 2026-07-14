import re

from odoo import models

from odoo.addons.account_edi_ubl_cii.models.account_edi_common import FloatFmt

NOTE_CODE_RE = re.compile(r'^#([A-Z]{3})#')

PDP_CUSTOMIZATION_ID = 'urn:cen.eu:en16931:2017'  # Not accepted by SuperPDP due to missing validator

PAID_STATES = frozenset({'in_payment', 'paid'})


class AccountEdiXmlUbl21Fr(models.AbstractModel):
    _name = "account.edi.xml.ubl_21_fr"
    _inherit = 'account.edi.xml.ubl_bis3'
    _description = "France UBL 2.1 E-Invoicing Format"

    # -------------------------------------------------------------------------
    # EXPORT
    # -------------------------------------------------------------------------

    def _export_invoice_filename(self, invoice):
        return f"{invoice.name.replace('/', '_')}_ubl_21_fr.xml"

    def _export_invoice(self, invoice, convert_fixed_taxes=True):
        # Use new helpers
        return self._export_invoice_new(invoice)

    def _export_invoice_constraints_new(self, invoice, vals):
        # EXTENDS account.edi.xml.ubl_bis3
        constraints = super()._export_invoice_constraints_new(invoice, vals)

        for partner_type in ('supplier', 'customer'):
            partner = vals[partner_type]
            commercial_partner = partner.commercial_partner_id
            if commercial_partner.peppol_eas != '0225' or not commercial_partner.peppol_endpoint:
                constraints[f"ubl_21_fr_{partner_type}_pdp_identifier_required"] = self.env._("The following partner's PDP identifier is missing: %s", commercial_partner.display_name)
            id_type, id_value = commercial_partner._l10n_fr_pdp_get_base_identifier()
            if not id_type or not id_value:
                constraints[f"ubl_21_fr_{partner_type}_siret_required"] = self.env._("The following partner's SIREN or SIRET is missing: %s", commercial_partner.display_name)
            if not commercial_partner.vat or commercial_partner.vat == '/':
                constraints[f"ubl_21_fr_{partner_type}_vat_required"] = self.env._("The following partner's VAT is missing: %s", commercial_partner.display_name)

        if vals['document_type'] == 'credit_note' and not (invoice.reversed_entry_id.name or invoice.reversed_entry_id.invoice_date):
            constraints[f"ubl_21_fr_{partner_type}_refund_invoice_reference"] = self.env._("The original journal entry's name or issue date are missing: %s", vals['invoice'].name)

        return constraints

    def _add_invoice_header_nodes(self, document_node, vals):
        # EXTENDS account.edi.xml.ubl_bis3
        invoice = vals['invoice']
        super()._add_invoice_header_nodes(document_node, vals)

        # Les valeurs autorisées pour le Cadre (Mode de Facturation) sont:
        # B1 : Dépôt d'une facture de bien
        # S1 : Dépôt d'une facture de prestation de service
        # M1 : Dépôt d'une facture double (livraison de bien et services qui ne sont pas accessoires l'une de l'autre)
        # B2 : Dépôt d'une facture de bien déjà payée
        # S2 : Dépôt d'une facture de prestation de service déjà payée
        # M2 : Dépôt d'une facture double déjà payée
        # B4 : Dépôt d'une facture définitive (après acompte) de bien
        # S4 : Dépôt d'une facture définitive (après acompte) de service
        # M4 : Dépôt d'une facture définitive (après acompte) double
        # S5 : Dépôt par un sous-traitant d'une facture de prestation de service
        # S6 : Dépôt par un cotraitant d'une facture de prestation de service
        # B7 : Dépôt d'une facture de bien ayant fait l'objet d'un e-reporting (TVA déjà collectée)
        # S7 : Dépôt d'une facture de prestation de service ayant fait l'objet d'un e-reporting (TVA déjà collectée)

        profile_id = invoice._l10n_fr_pdp_get_profile_id()
        document_node.update({
            'cbc:CustomizationID': {'_text': PDP_CUSTOMIZATION_ID},
            'cbc:ProfileID': {'_text': profile_id},
        })

        # [BR-FR-05] Add mandatory notes with defaults if not already present
        # Initialize / Listify 'cbc:Note'
        existing_note = document_node.get('cbc:Note')
        if not existing_note or not isinstance(document_node.get('cbc:Note'), list):
            document_node['cbc:Note'] = [existing_note] if existing_note else []
        # [BR-FR-06] A coded note (#XXX#...) must not occur more than once: skip codes
        # already present on the invoice (e.g. manually added by the user).
        existing_codes = {
            match.group(1)
            for note in document_node['cbc:Note']
            if isinstance(note, dict) and (match := NOTE_CODE_RE.match(note.get('_text') or ''))
        }
        # Add default notes
        for code, default_content in invoice._l10n_fr_pdp_get_default_notes().items():
            if code in existing_codes:
                continue
            document_node['cbc:Note'].append({
                '_text': f"#{code}#{default_content}",
            })

        # [BG-11] Cas DGFiP #29 — assujetti unique (Art. 256 C CGI): while EN 16931 has no
        # dedicated block for the VAT group, the AFNOR/DGFiP guidance re-uses the Seller Tax
        # Representative Party to carry its name, VAT number and postal address.
        if tax_representative_node := self._l10n_fr_pdp_get_tax_representative_party_node(vals):
            document_node['cac:TaxRepresentativeParty'] = tax_representative_node

        # Règles de gestion G1.52
        if vals['document_type'] == 'credit_note':
            document_node['cac:BillingReference'] = {
                'cac:InvoiceDocumentReference': {
                    'cbc:ID': {'_text': invoice.reversed_entry_id.name},
                    'cbc:IssueDate': {'_text': invoice.reversed_entry_id.invoice_date},
                }
            }

    def _l10n_fr_pdp_get_tax_representative_party_node(self, vals):
        """[BG-11] Cas DGFiP #29 — name, VAT number and postal address of the VAT group
        ("assujetti unique") this company is a member of."""
        invoice = vals['invoice']
        company = invoice.company_id
        if not company.l10n_fr_is_tva_group_member or not company.l10n_fr_tva_group_id:
            return None
        tva_group_partner = company.l10n_fr_tva_group_id.partner_id
        return {
            'cac:PartyName': {
                'cbc:Name': {'_text': tva_group_partner.name},
            },
            'cac:PartyTaxScheme': {
                'cbc:CompanyID': {'_text': tva_group_partner.vat},
                'cac:TaxScheme': {'cbc:ID': {'_text': 'VAT'}},
            },
            'cac:PostalAddress': self._get_address_node({**vals, 'partner': tva_group_partner}),
        }

    def _ubl_add_buyer_reference_node(self, vals):
        super()._ubl_add_buyer_reference_node(vals)
        invoice = vals['invoice']
        if invoice._l10n_fr_pdp_has_vat_on_debits():
            vals['document_node']['cac:InvoicePeriod'] = {
                'cbc:DescriptionCode': {'_text': '3'},
            }

    def _add_invoice_payment_terms_nodes(self, document_node, vals):
        # EXTENDS account_edi_ubl_cii
        super()._add_invoice_payment_terms_nodes(document_node, vals)
        invoice = vals['invoice']
        payment_term = invoice.invoice_payment_term_id
        if not payment_term.early_discount or not payment_term.discount_percentage:
            return
        # [BT-20] Structured early payment discount note, generated for every
        # `early_pay_discount_computation` mode instead of relying only on the free-text
        # note field on the payment term (G5).
        document_node.setdefault('cac:PaymentTerms', {})['cbc:Note'] = {
            '_text': invoice._l10n_fr_pdp_get_early_discount_note(),
        }

    def _ubl_add_party_identification_nodes(self, vals):
        super()._ubl_add_party_identification_nodes(vals)
        partner = vals['party_vals']['partner']
        commercial_partner = partner.commercial_partner_id

        id_type, party_id = commercial_partner._l10n_fr_pdp_get_base_identifier()
        if id_type == 'siret':
            party_id_scheme = "0009"
        else:  # id_type == 'siren'
            party_id_scheme = "0002"
        # [UBL-SR-16] Buyer identifier shall occur maximum once
        party_identifications = [{
            'cbc:ID': {'_text': party_id, 'schemeID': party_id_scheme},
        }]
        # [BT-29] Cas DGFiP #29 — assujetti unique (Art. 256 C CGI): the seller's private
        # identifier also carries the VAT group's SIREN, with scheme identifier 0231
        # (AFNOR XP Z12-012 Annexe A).
        if partner == vals.get('supplier'):
            invoice = vals['invoice']
            company = invoice.company_id
            if company.l10n_fr_is_tva_group_member and (tva_group_siren := company.l10n_fr_tva_group_siren):
                party_identifications.append({
                    'cbc:ID': {'_text': tva_group_siren, 'schemeID': '0231'},
                })
        vals['party_node']['cac:PartyIdentification'] = party_identifications

    def _ubl_add_party_legal_entity_nodes(self, vals):
        # EXTENDS account.edi.xml.ubl_bis3
        super()._ubl_add_party_legal_entity_nodes(vals)
        partner = vals['party_vals']['partner']
        commercial_partner = partner.commercial_partner_id

        vals['party_node']['cac:PartyLegalEntity'] = {
            'cbc:RegistrationName': {'_text': commercial_partner.name},
            'cbc:CompanyID': {
                '_text': commercial_partner._l10n_fr_pdp_get_siren(),
                'schemeID': '0002',
            },
        }
        # [BT-33] CompanyLegalForm: only applies to the seller (BG-4), built from the
        # legal form and share capital of the invoicing company.
        if partner == vals.get('supplier'):
            invoice = vals['invoice']
            if legal_form_text := invoice._l10n_fr_pdp_get_company_legal_form_text():
                vals['party_node']['cac:PartyLegalEntity']['cbc:CompanyLegalForm'] = {'_text': legal_form_text}

    def _ubl_add_line_price_node(self, vals, in_foreign_currency=True):
        # OVERRIDE
        line_node = vals['line_node']
        base_line = vals['line_vals']['base_line']
        suffix = '_currency' if in_foreign_currency else ''
        currency = base_line['currency_id'] if in_foreign_currency else vals['company_currency']
        price_amount = base_line['tax_details'][f'raw_gross_price_unit{suffix}']

        line_node['cac:Price'] = {
            'cbc:PriceAmount': {
                '_text': FloatFmt(price_amount, min_dp=1, max_dp=6),
                'currencyID': currency.name,
            },
            'cac:AllowanceCharge': {
                "cbc:ChargeIndicator": [{
                    "_text": 'false',
                }],
                # Discount amount
                "cbc:Amount": [{
                    "_text": FloatFmt(0, min_dp=1, max_dp=6),
                    "currencyID": currency.name,
                }],
                # Pre-discount amount
                'cbc:BaseAmount': {
                    '_text': FloatFmt(price_amount, min_dp=1, max_dp=6),
                    'currencyID': currency.name,
                },
            }
        }
