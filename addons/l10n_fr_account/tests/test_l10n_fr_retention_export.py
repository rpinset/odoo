# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.addons.account_edi_ubl_cii.tests.common import TestUblCiiCommon
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestL10nFrRetentionExport(TestUblCiiCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.retention_clause = (
            'Retenue de garantie de 5 % (loi n°71-584 du 16 juillet 1971). '
            'Libérable un an après réception des travaux.'
        )

    def _create_retention_invoice(self):
        invoice = self.init_invoice(
            'out_invoice',
            partner=self.partner_a,
            products=self.product_a,
            post=True,
        )
        invoice.write({
            'l10n_fr_has_retention_guarantee': True,
            'l10n_fr_retention_clause_note': self.retention_clause,
        })
        return invoice

    def test_ubl_bis3_export_retention_abu_note(self):
        invoice = self._create_retention_invoice()
        builder = self.env['account.edi.xml.ubl_bis3']
        xml_bytes, errors = builder._export_invoice(invoice)
        self.assertFalse(errors)
        xml_str = xml_bytes.decode()
        self.assertIn('#ABU#', xml_str)
        self.assertIn(self.retention_clause, xml_str)

    def test_cii_export_retention_subject_code(self):
        invoice = self._create_retention_invoice()
        builder = self.env['account.edi.xml.cii']
        xml_bytes, errors = builder._export_invoice(invoice)
        self.assertFalse(errors)
        xml_str = xml_bytes.decode()
        self.assertIn('<ram:SubjectCode>ABU</ram:SubjectCode>', xml_str)
        self.assertIn(self.retention_clause, xml_str)

    def test_sale_order_prepare_invoice_propagation(self):
        partner = self.partner_a
        order = self.env['sale.order'].create({
            'partner_id': partner.id,
            'l10n_fr_has_retention_guarantee': True,
            'l10n_fr_retention_clause_note': self.retention_clause,
            'order_line': [(0, 0, {
                'product_id': self.product_a.id,
                'product_uom_qty': 1.0,
                'price_unit': 500.0,
                'tax_id': [(6, 0, self.tax_15_p.ids)],
            })],
        })
        order.action_confirm()
        invoice_vals = order._prepare_invoice()
        self.assertTrue(invoice_vals.get('l10n_fr_has_retention_guarantee'))
        self.assertEqual(invoice_vals.get('l10n_fr_retention_clause_note'), self.retention_clause)

    def test_export_constraint_missing_clause(self):
        invoice = self._create_retention_invoice()
        invoice.l10n_fr_retention_clause_note = False
        builder = self.env['account.edi.xml.ubl_bis3']
        _, errors = builder._export_invoice(invoice)
        self.assertTrue(errors)
