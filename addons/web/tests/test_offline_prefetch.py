# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import TransactionCase, tagged


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
