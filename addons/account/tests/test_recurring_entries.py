# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from dateutil.relativedelta import relativedelta
from freezegun import freeze_time

from odoo import fields
from odoo.tests import tagged
from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged('post_install', '-at_install')
class TestAccountMoveRecurringEntries(AccountTestInvoicingCommon):
    """Test recurring entries functionality with new frequencies."""

    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)
        
        # Create a base journal entry for testing
        cls.test_move = cls.env['account.move'].create({
            'move_type': 'entry',
            'date': fields.Date.from_string('2024-01-15'),
            'journal_id': cls.company_data['default_journal_misc'].id,
            'line_ids': [
                (0, 0, {
                    'account_id': cls.company_data['default_account_expense'].id,
                    'name': 'Test recurring line',
                    'debit': 100.0,
                    'credit': 0.0,
                }),
                (0, 0, {
                    'account_id': cls.company_data['default_account_payable'].id,
                    'name': 'Test recurring line',
                    'debit': 0.0,
                    'credit': 100.0,
                }),
            ],
        })

    def test_apply_delta_recurring_entries_bimonthly(self):
        """Test bimonthly recurring entries (every 2 months)."""
        date_origin = fields.Date.from_string('2024-01-15')
        date_current = fields.Date.from_string('2024-01-15')
        
        # Test first recurrence
        next_date = self.env['account.move']._apply_delta_recurring_entries(
            date_current, date_origin, 'bimonthly'
        )
        self.assertEqual(next_date, fields.Date.from_string('2024-03-15'))
        
        # Test second recurrence
        date_current = next_date
        next_date = self.env['account.move']._apply_delta_recurring_entries(
            date_current, date_origin, 'bimonthly'
        )
        self.assertEqual(next_date, fields.Date.from_string('2024-05-15'))

    def test_apply_delta_recurring_entries_four_months(self):
        """Test every 4 months recurring entries."""
        date_origin = fields.Date.from_string('2024-01-31')
        date_current = fields.Date.from_string('2024-01-31')
        
        # Test first recurrence
        next_date = self.env['account.move']._apply_delta_recurring_entries(
            date_current, date_origin, 'four_months'
        )
        self.assertEqual(next_date, fields.Date.from_string('2024-05-31'))
        
        # Test second recurrence
        date_current = next_date
        next_date = self.env['account.move']._apply_delta_recurring_entries(
            date_current, date_origin, 'four_months'
        )
        self.assertEqual(next_date, fields.Date.from_string('2024-09-30'))  # September has 30 days

    def test_apply_delta_recurring_entries_semi_annually(self):
        """Test semi-annual recurring entries (every 6 months)."""
        date_origin = fields.Date.from_string('2024-02-28')
        date_current = fields.Date.from_string('2024-02-28')
        
        # Test first recurrence
        next_date = self.env['account.move']._apply_delta_recurring_entries(
            date_current, date_origin, 'semi_annually'
        )
        self.assertEqual(next_date, fields.Date.from_string('2024-08-28'))
        
        # Test second recurrence
        date_current = next_date
        next_date = self.env['account.move']._apply_delta_recurring_entries(
            date_current, date_origin, 'semi_annually'
        )
        self.assertEqual(next_date, fields.Date.from_string('2025-02-28'))

    def test_copy_recurring_entries_bimonthly(self):
        """Test the copy of bimonthly recurring entries."""
        # Set up bimonthly recurrence
        self.test_move.auto_post = 'bimonthly'
        self.test_move.auto_post_until = fields.Date.from_string('2024-07-31')
        
        # Post the move
        self.test_move.action_post()
        
        # Copy recurring entries
        self.test_move._copy_recurring_entries()
        
        # Check that a new move was created with the correct date
        new_move = self.env['account.move'].search([
            ('auto_post_origin_id', '=', self.test_move.id),
            ('date', '=', fields.Date.from_string('2024-03-15'))
        ])
        self.assertTrue(new_move)
        self.assertEqual(new_move.auto_post, 'bimonthly')
        self.assertEqual(new_move.state, 'draft')
        
    def test_copy_recurring_entries_until_date(self):
        """Test that recurring entries stop at auto_post_until date."""
        # Set up bimonthly recurrence with end date
        self.test_move.auto_post = 'bimonthly'
        self.test_move.auto_post_until = fields.Date.from_string('2024-02-28')
        
        # Post the move
        self.test_move.action_post()
        
        # Copy recurring entries
        self.test_move._copy_recurring_entries()
        
        # Check that a new move was NOT created (next date would be March 15)
        new_move = self.env['account.move'].search([
            ('auto_post_origin_id', '=', self.test_move.id)
        ])
        self.assertFalse(new_move)

    def test_standard_frequencies_still_work(self):
        """Ensure standard frequencies (monthly, quarterly, yearly) still work."""
        date_origin = fields.Date.from_string('2024-01-15')
        date_current = fields.Date.from_string('2024-01-15')
        
        # Test monthly
        next_date = self.env['account.move']._apply_delta_recurring_entries(
            date_current, date_origin, 'monthly'
        )
        self.assertEqual(next_date, fields.Date.from_string('2024-02-15'))
        
        # Test quarterly
        next_date = self.env['account.move']._apply_delta_recurring_entries(
            date_current, date_origin, 'quarterly'
        )
        self.assertEqual(next_date, fields.Date.from_string('2024-04-15'))
        
        # Test yearly
        next_date = self.env['account.move']._apply_delta_recurring_entries(
            date_current, date_origin, 'yearly'
        )
        self.assertEqual(next_date, fields.Date.from_string('2025-01-15'))
