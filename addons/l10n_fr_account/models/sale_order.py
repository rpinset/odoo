# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    l10n_fr_has_retention_guarantee = fields.Boolean(
        string='Retention Guarantee',
        copy=True,
        help='Enable when the order includes a contractual retention guarantee clause (cas 26).',
    )
    l10n_fr_retention_clause_note = fields.Text(
        string='Retention Clause',
        copy=True,
        help='BT-22 contractual reserve clause propagated to customer invoices.',
    )

    @api.constrains('l10n_fr_has_retention_guarantee', 'l10n_fr_retention_clause_note')
    def _check_l10n_fr_retention_clause_note(self):
        for order in self:
            if order.l10n_fr_has_retention_guarantee and not (order.l10n_fr_retention_clause_note or '').strip():
                raise ValidationError(self.env._(
                    "The retention clause note is required on order '%(order)s' when retention guarantee is enabled.",
                    order=order.display_name,
                ))

    @api.onchange('l10n_fr_has_retention_guarantee')
    def _onchange_l10n_fr_has_retention_guarantee(self):
        if not self.l10n_fr_has_retention_guarantee:
            self.l10n_fr_retention_clause_note = False

    def _prepare_invoice(self):
        invoice_vals = super()._prepare_invoice()
        invoice_vals.update({
            'l10n_fr_has_retention_guarantee': self.l10n_fr_has_retention_guarantee,
            'l10n_fr_retention_clause_note': self.l10n_fr_retention_clause_note if self.l10n_fr_has_retention_guarantee else False,
        })
        return invoice_vals
