from odoo import Command
from odoo.tests import tagged

from .common import TestL10nFrPdpCommon


@tagged('post_install_l10n', 'post_install', '-at_install')
class TestL10nFrPdpVatMentions(TestL10nFrPdpCommon):
    """[BR-FR-05] BT-8 and VATEX-FR tax templates (Cas régimes fiscaux : franchise 293 B,
    autoliquidation BTP, intracom 262 ter, TVA sur débits)."""

    def test_vat_on_debits_bt8_present_on_invoice_exigibility(self):
        # `tva_acq_normale` / `tva_acq_specifique` default to `tax_exigibility='on_invoice'`.
        invoice = self._create_french_invoice()
        self.assertTrue(invoice._l10n_fr_pdp_has_vat_on_debits())
        self.assertNotIn('TVD', invoice._l10n_fr_pdp_get_default_notes())
        xml, errors = self.env['account.edi.xml.ubl_21_fr']._export_invoice(invoice)
        self.assertFalse(errors)
        self.assertIn(b'<cbc:DescriptionCode>3</cbc:DescriptionCode>', xml)

    def test_vat_on_debits_bt8_absent_on_payment_exigibility(self):
        tax_on_payment = self.env['account.chart.template'].ref('tva_normale_encaissement')
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner_a.id,
            'invoice_date': '2017-01-01',
            'date': '2017-01-01',
            'invoice_line_ids': [
                Command.create({
                    'product_id': self.product_a.id,
                    'quantity': 1.0,
                    'tax_ids': [Command.set(tax_on_payment.ids)],
                }),
            ],
        })
        self.assertFalse(invoice._l10n_fr_pdp_has_vat_on_debits())
        self.assertNotIn('TVD', invoice._l10n_fr_pdp_get_default_notes())

    def test_franchise_tax_templates_are_tagged(self):
        franchise_good = self.env['account.chart.template'].ref('tva_sale_franchise_good_0')
        franchise_service = self.env['account.chart.template'].ref('tva_sale_franchise_service_0')
        self.assertEqual(franchise_good.ubl_cii_tax_category_code, 'E')
        self.assertEqual(franchise_good.ubl_cii_tax_exemption_reason_code, 'VATEX_FR-FRANCHISE')
        self.assertEqual(franchise_service.ubl_cii_tax_category_code, 'E')
        self.assertEqual(franchise_service.ubl_cii_tax_exemption_reason_code, 'VATEX_FR-FRANCHISE')

    def test_autoliquidation_btp_tax_template_is_tagged(self):
        autoliq_btp = self.env['account.chart.template'].ref('tva_sale_autoliq_btp_0')
        self.assertEqual(autoliq_btp.ubl_cii_tax_category_code, 'AE')
        self.assertEqual(autoliq_btp.ubl_cii_tax_exemption_reason_code, 'VATEX-FR-AE')

    def test_intracom_and_export_tax_templates_are_tagged(self):
        cases = [
            ('tva_sale_good_export_0', 'G', 'VATEX_EU_G'),
            ('tva_sale_service_export_0', 'O', 'VATEX_EU_O'),
            ('tva_sale_good_intra_0', 'K', 'VATEX_EU_IC'),
            ('tva_sale_service_intra_0', 'AE', 'VATEX_EU_AE'),
        ]
        for xmlid, category_code, exemption_code in cases:
            tax = self.env['account.chart.template'].ref(xmlid)
            self.assertEqual(tax.ubl_cii_tax_category_code, category_code, xmlid)
            self.assertEqual(tax.ubl_cii_tax_exemption_reason_code, exemption_code, xmlid)

    def test_franchise_fiscal_position_maps_to_franchise_taxes(self):
        fiscal_position = self.env['account.chart.template'].ref('fiscal_position_template_franchise')
        normale = self.env['account.chart.template'].ref('tva_normale')
        franchise_good = self.env['account.chart.template'].ref('tva_sale_franchise_good_0')
        mapped = fiscal_position.map_tax(normale)
        self.assertEqual(mapped, franchise_good)

    def test_autoliq_btp_fiscal_position_maps_to_autoliq_btp_tax(self):
        fiscal_position = self.env['account.chart.template'].ref('fiscal_position_template_autoliq_btp')
        normale_encaissement = self.env['account.chart.template'].ref('tva_normale_encaissement')
        autoliq_btp = self.env['account.chart.template'].ref('tva_sale_autoliq_btp_0')
        mapped = fiscal_position.map_tax(normale_encaissement)
        self.assertEqual(mapped, autoliq_btp)
