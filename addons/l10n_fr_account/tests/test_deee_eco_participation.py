from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests.common import tagged


@tagged('post_install_l10n', 'post_install', '-at_install')
class TestDeeeEcoParticipation(AccountTestInvoicingCommon):

    @classmethod
    @AccountTestInvoicingCommon.setup_country('fr')
    def setUpClass(cls):
        super().setUpClass()
        cls.deee_product = cls.env['product.product'].create({
            'name': 'Screen 24"',
            'l10n_fr_deee_category': 'ecran',
            'l10n_fr_deee_amount': 2.5,
        })

    def test_deee_amount_defaulted_from_product(self):
        """The eco-participation amount should be copied from the product onto the invoice line."""
        invoice = self._create_invoice_one_line(product_id=self.deee_product)
        line = invoice.invoice_line_ids.filtered(lambda l: l.product_id == self.deee_product)
        self.assertEqual(line.l10n_fr_deee_amount, 2.5)

    def test_deee_amount_zero_without_eco_tax(self):
        """Products without an eco-participation amount should not carry any value on the line."""
        invoice = self._create_invoice_one_line(product_id=self.product_a)
        line = invoice.invoice_line_ids.filtered(lambda l: l.product_id == self.product_a)
        self.assertEqual(line.l10n_fr_deee_amount, 0.0)

    def test_deee_amount_editable_after_creation(self):
        """The computed default must remain editable (precompute pattern), e.g. for a manual correction."""
        invoice = self._create_invoice_one_line(product_id=self.deee_product)
        line = invoice.invoice_line_ids.filtered(lambda l: l.product_id == self.deee_product)
        line.l10n_fr_deee_amount = 3.0
        self.assertEqual(line.l10n_fr_deee_amount, 3.0)

    def test_deee_amount_on_note_line(self):
        """Section/note lines should never carry an eco-participation amount."""
        invoice = self._create_invoice_one_line(product_id=self.product_a)
        invoice.write({
            'invoice_line_ids': [
                Command.create({'name': 'Note', 'display_type': 'line_note'}),
            ],
        })
        note_line = invoice.invoice_line_ids.filtered(lambda l: l.display_type == 'line_note')
        self.assertEqual(note_line.l10n_fr_deee_amount, 0.0)
