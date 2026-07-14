from odoo.tests import tagged

from .common import TestL10nFrPdpCommon


@tagged('post_install_l10n', 'post_install', '-at_install')
class TestL10nFrPdpCas29TvaGroup(TestL10nFrPdpCommon):
    """DGFiP use case #29 — VAT group ("assujetti unique", Art. 256 C CGI):
    #TXD# note, BT-29 (SIREN, scheme 0231) and BG-11 (TaxRepresentativeParty)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data['company']
        cls.tva_group_company = cls.env['res.company'].create({
            'name': 'Groupe TVA Unique SAS',
            'vat': 'FR12345678901',
            'siret': '552100554',
        })

    def test_no_tva_group_note_by_default(self):
        invoice = self._create_french_invoice()
        self.assertNotIn('TXD', invoice._l10n_fr_pdp_get_default_notes())

    def test_tva_group_note_and_siren_when_member(self):
        self.company.write({
            'l10n_fr_is_tva_group_member': True,
            'l10n_fr_tva_group_id': self.tva_group_company.id,
        })
        invoice = self._create_french_invoice()
        self.assertEqual(invoice._l10n_fr_pdp_get_default_notes().get('TXD'), "MEMBRE_ASSUJETTI_UNIQUE")
        self.assertEqual(self.company.l10n_fr_tva_group_siren, '552100554')

    def test_tax_representative_party_node_built_from_tva_group(self):
        self.company.write({
            'l10n_fr_is_tva_group_member': True,
            'l10n_fr_tva_group_id': self.tva_group_company.id,
        })
        invoice = self._create_french_invoice()
        builder = self.env['account.edi.xml.ubl_21_fr']
        node = builder._l10n_fr_pdp_get_tax_representative_party_node({'invoice': invoice})
        self.assertEqual(node['cac:PartyLegalEntity']['cbc:RegistrationName']['_text'], 'Groupe TVA Unique SAS')
        self.assertEqual(node['cac:PartyTaxScheme']['cbc:CompanyID']['_text'], 'FR12345678901')

    def test_no_tax_representative_party_node_when_not_member(self):
        invoice = self._create_french_invoice()
        builder = self.env['account.edi.xml.ubl_21_fr']
        self.assertIsNone(builder._l10n_fr_pdp_get_tax_representative_party_node({'invoice': invoice}))
