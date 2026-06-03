# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import timedelta

from odoo import fields
from odoo.tests import Form, TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestOfflinePrefetch(TransactionCase):

    def test_categories_include_stock_and_sale(self):
        categories = self.env['offline.prefetch'].get_categories()
        category_ids = {c['id'] for c in categories}
        self.assertIn('stock_picking_outgoing', category_ids)
        self.assertIn('sale_order', category_ids)

    def test_collect_me_scope(self):
        result = self.env['offline.prefetch'].collect(
            ['sale_order'],
            hours=2,
            scope='me',
        )
        self.assertEqual(result['hours'], 2)
        self.assertEqual(result['scope'], 'me')
        self.assertIn('manifest', result)
        self.assertIn('partners', result)
        self.assertEqual(self.env.user.offline_prefetch_hours, 2)

    def test_collect_all_scope(self):
        result = self.env['offline.prefetch'].collect(
            ['stock_picking_internal'],
            hours=4,
            scope='all',
        )
        self.assertEqual(result['scope'], 'all')
        self.assertEqual(result['hours'], 4)

    def test_collect_finds_scheduled_picking(self):
        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'outgoing'),
            ('company_id', '=', self.env.company.id),
        ], limit=1)
        self.assertTrue(picking_type)
        scheduled = fields.Datetime.now() + timedelta(hours=1)
        with Form(self.env['stock.picking']) as picking_form:
            picking_form.picking_type_id = picking_type
            picking_form.scheduled_date = scheduled
        picking = picking_form.save()
        picking.write({'user_id': self.env.user.id})

        result = self.env['offline.prefetch'].collect(
            ['stock_picking_outgoing'],
            hours=2,
            scope='me',
        )
        manifest_models = {entry['model']: entry['res_ids'] for entry in result['manifest']}
        self.assertIn(picking.id, manifest_models.get('stock.picking', []))

    def test_company_domain_on_model_with_company(self):
        domain = self.env['offline.prefetch']._company_domain('stock.picking')
        self.assertEqual(domain, [('company_id', 'in', self.env.companies.ids)])
