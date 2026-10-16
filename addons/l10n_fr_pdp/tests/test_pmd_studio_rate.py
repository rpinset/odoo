from odoo.tests import tagged

from odoo.addons.l10n_fr_pdp.tests.common import TestL10nFrPdpCommon


@tagged('post_install_l10n', 'post_install', '-at_install')
class TestPmdStudioRate(TestL10nFrPdpCommon):

    def test_empty_studio_rate_uses_ecb_wording(self):
        self.company.x_studio_peppol_late_payment_penalty_rate = 0.0
        invoice = self._create_french_invoice()
        note = invoice._l10n_fr_pdp_get_pmd_note()
        self.assertIn('European Central Bank', note)
        self.assertNotIn('annual rate of 10%', note)

    def test_studio_rate_is_snapshotted_on_post(self):
        self.company.x_studio_peppol_late_payment_penalty_rate = 12.5
        invoice = self._create_french_invoice()
        self.assertIn('12.5%', invoice._l10n_fr_pdp_get_pmd_note())
        invoice.action_post()
        self.assertEqual(invoice.x_studio_peppol_late_payment_penalties_rate, 12.5)
        self.company.x_studio_peppol_late_payment_penalty_rate = 18.0
        self.assertIn('12.5%', invoice._l10n_fr_pdp_get_pmd_note())

    def test_settings_write_studio_rate(self):
        self.env['res.config.settings'].create({
            'company_id': self.company.id,
            'l10n_fr_pdp_late_payment_penalty_rate': 9.5,
        })
        self.assertEqual(self.company.x_studio_peppol_late_payment_penalty_rate, 9.5)
