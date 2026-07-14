# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


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
