# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import ValidationError

# BT-21 subject code — contractual reserve clause (DGFiP cas 26).
L10N_FR_RETENTION_NOTE_SUBJECT_CODE = 'ABU'


class AccountMove(models.Model):
    _inherit = 'account.move'

    l10n_fr_has_retention_guarantee = fields.Boolean(
        string='Retention Guarantee',
        copy=True,
        help='Enable when the invoice includes a contractual retention guarantee clause (cas 26).',
    )
    l10n_fr_retention_clause_note = fields.Text(
        string='Retention Clause',
        copy=True,
        help='BT-22 contractual reserve clause text exported with BT-21 subject code ABU.',
    )

    @api.constrains('l10n_fr_has_retention_guarantee', 'l10n_fr_retention_clause_note', 'move_type')
    def _check_l10n_fr_retention_clause_note(self):
        for move in self:
            if (
                move.l10n_fr_has_retention_guarantee
                and move.is_sale_document(include_receipts=False)
                and not (move.l10n_fr_retention_clause_note or '').strip()
            ):
                raise ValidationError(self.env._(
                    "The retention clause note is required on '%(invoice)s' when retention guarantee is enabled.",
                    invoice=move.display_name,
                ))

    @api.onchange('l10n_fr_has_retention_guarantee')
    def _onchange_l10n_fr_has_retention_guarantee(self):
        if not self.l10n_fr_has_retention_guarantee:
            self.l10n_fr_retention_clause_note = False

    def _l10n_fr_edi_get_subject_notes(self):
        """Return BT-21 coded notes as {subject_code: content} for French EDI export."""
        self.ensure_one()
        if not self.l10n_fr_has_retention_guarantee:
            return {}
        note = (self.l10n_fr_retention_clause_note or '').strip()
        if not note:
            return {}
        return {L10N_FR_RETENTION_NOTE_SUBJECT_CODE: note}

    def _l10n_fr_edi_get_subject_note_ubl_texts(self):
        """Return UBL cbc:Note values using the French #CODE#content pattern."""
        self.ensure_one()
        return [
            f'#{code}#{content}'
            for code, content in self._l10n_fr_edi_get_subject_notes().items()
        ]
