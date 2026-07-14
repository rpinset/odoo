from odoo.tests.common import tagged

from odoo.addons.l10n_fr_pdp.tests.common import TestL10nFrPdpCommon


@tagged('post_install_l10n', 'post_install', '-at_install')
class TestDeeeNotes(TestL10nFrPdpCommon):
    """[BR-FR-07] The #BLU# note must disclose the eco-participation (DEEE) amounts
    included in the invoice, per Art. L.541-10-20 of the Code de l'environnement."""

    def test_deee_note_added_when_line_has_eco_participation(self):
        self.product_a.l10n_fr_deee_amount = 3.5
        invoice = self._create_french_invoice()
        notes = invoice._l10n_fr_pdp_get_default_notes()
        self.assertIn('BLU', notes)
        self.assertIn('3.50', notes['BLU'])
        self.assertIn(self.product_a.display_name, notes['BLU'])

    def test_no_deee_note_without_eco_participation(self):
        invoice = self._create_french_invoice()
        notes = invoice._l10n_fr_pdp_get_default_notes()
        self.assertNotIn('BLU', notes)

    def test_deee_note_totals_multiple_lines(self):
        self.product_a.l10n_fr_deee_amount = 1.25
        self.product_b.l10n_fr_deee_amount = 0.75
        invoice = self._create_french_invoice()
        note = invoice._l10n_fr_pdp_get_deee_note()
        self.assertIn('2.00', note)  # total of the two eco-participation amounts
