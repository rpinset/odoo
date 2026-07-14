# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    l10n_fr_rounding_difference_loss_account_id = fields.Many2one('account.account', check_company=True)
    l10n_fr_rounding_difference_profit_account_id = fields.Many2one('account.account', check_company=True)
    l10n_fr_legal_form = fields.Selection(
        selection=[
            ('ei', "EI"),
            ('eurl', "EURL"),
            ('sarl', "SARL"),
            ('sas', "SAS"),
            ('sasu', "SASU"),
            ('sa', "SA"),
            ('snc', "SNC"),
            ('sci', "SCI"),
            ('scs', "SCS"),
            ('sca', "SCA"),
            ('scop', "SCOP"),
            ('association', "Association loi 1901"),
            ('other', "Other"),
        ],
        string="Legal Form (FR)",
        help="Legal form of the company. Used to build the mandatory legal mention "
             "on invoices (Art. R.123-237 of the Code de commerce).",
    )
    l10n_fr_share_capital = fields.Monetary(
        string="Share Capital",
        currency_field='currency_id',
        help="Share capital of the company. Used to build the mandatory legal mention "
             "on invoices when the legal form is a company with share capital "
             "(Art. R.123-237 of the Code de commerce).",
    )
    l10n_fr_is_tva_group_member = fields.Boolean(
        string="Member of a VAT Group (Assujetti Unique)",
        help="Check this box if this company is a member of a VAT group (\"assujetti unique\", "
             "Art. 256 C of the Code Général des Impôts). The VAT group's SIREN and VAT number "
             "must then be reported on this company's invoices (DGFiP use case #29).",
    )
    l10n_fr_tva_group_id = fields.Many2one(
        comodel_name='res.company',
        string="VAT Group (Assujetti Unique)",
        help="The VAT group (\"assujetti unique\") this company is a member of. Its SIREN and "
             "VAT number are reported on the invoices issued by this company (DGFiP use case #29, "
             "Art. 256 C of the Code Général des Impôts).",
    )
    l10n_fr_tva_group_siren = fields.Char(
        string="VAT Group SIREN",
        compute='_compute_l10n_fr_tva_group_siren',
        help="SIREN of the VAT group (\"assujetti unique\"), derived from its SIRET/company registry.",
    )

    @api.depends('l10n_fr_tva_group_id.siret', 'l10n_fr_tva_group_id.company_registry')
    def _compute_l10n_fr_tva_group_siren(self):
        for company in self:
            registry = company.l10n_fr_tva_group_id.siret or company.l10n_fr_tva_group_id.company_registry or ''
            company.l10n_fr_tva_group_siren = registry[:9] if len(registry) in (9, 14) else False
