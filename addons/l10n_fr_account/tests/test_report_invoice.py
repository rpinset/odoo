from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests.common import tagged


@tagged('post_install_l10n', 'post_install', '-at_install')
class TestL10nFrReportInvoiceLegalMentions(AccountTestInvoicingCommon):
    """[Art. L.441-10 / R.123-237 Code de commerce] Mandatory legal mentions on the invoice PDF."""

    @classmethod
    @AccountTestInvoicingCommon.setup_country('fr')
    def setUpClass(cls):
        super().setUpClass()
        cls.company_data['company'].write({
            'l10n_fr_legal_form': 'sarl',
            'l10n_fr_share_capital': 50000,
            'siret': '96851575905899',
            'city': 'Rennes',
        })

    def test_legal_registration_mention(self):
        invoice = self._create_invoice_one_line()
        mention = invoice._l10n_fr_get_legal_registration_mention()
        self.assertIn('SARL', mention)
        self.assertIn('50,000.00', mention)
        self.assertIn('RCS Rennes 968515759', mention)

    def test_legal_registration_mention_without_legal_form(self):
        self.company_data['company'].l10n_fr_legal_form = False
        invoice = self._create_invoice_one_line()
        mention = invoice._l10n_fr_get_legal_registration_mention()
        self.assertNotIn('SARL', mention)
        self.assertIn('RCS Rennes 968515759', mention)

    def test_late_payment_mention(self):
        invoice = self._create_invoice_one_line()
        mention = invoice._l10n_fr_get_late_payment_mention()
        self.assertIn('L.441-10', mention)
        self.assertIn('D.441-5', mention)
        self.assertIn('40', mention)

    def test_early_discount_mention_absent(self):
        invoice = self._create_invoice_one_line()
        self.assertEqual(invoice._l10n_fr_get_early_discount_mention(), "No discount for early payment.")

    def test_early_discount_mention_present(self):
        payment_term = self.env['account.payment.term'].create({
            'name': 'Early discount 2%/10d',
            'early_discount': True,
            'discount_percentage': 2.0,
            'discount_days': 10,
            'line_ids': [(0, 0, {'value': 'balance', 'nb_days': 30})],
        })
        invoice = self._create_invoice_one_line(invoice_payment_term_id=payment_term.id)
        mention = invoice._l10n_fr_get_early_discount_mention()
        self.assertIn('2.0', mention)
        self.assertIn('10', mention)

    def test_report_renders(self):
        invoice = self._create_invoice_one_line(post=True)
        html = self.env['ir.actions.report']._render_qweb_html('account.account_invoices', invoice.ids)[0]
        self.assertIn(b'SARL', html)
