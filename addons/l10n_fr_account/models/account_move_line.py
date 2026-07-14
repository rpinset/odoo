# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    l10n_fr_deee_amount = fields.Monetary(
        string="Eco-Participation (DEEE)",
        currency_field='currency_id',
        compute='_compute_l10n_fr_deee_amount', store=True, readonly=False, precompute=True,
        help="Unit amount of the eco-participation (DEEE) included in the price of this line, "
             "disclosed separately on the invoice as required by Art. L.541-10-20 of the Code "
             "de l'environnement.",
    )

    @api.depends('product_id')
    def _compute_l10n_fr_deee_amount(self):
        for line in self:
            if line.display_type in ('line_section', 'line_note') or not line.product_id:
                line.l10n_fr_deee_amount = 0.0
                continue
            line.l10n_fr_deee_amount = line.product_id.l10n_fr_deee_amount
