# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models


class OfflinePrefetch(models.AbstractModel):
    _inherit = 'offline.prefetch'

    @api.model
    def _offline_prefetch_categories(self):
        categories = super()._offline_prefetch_categories()
        if not self._is_module_installed('stock'):
            return categories

        picking_specs = [
            ('stock_picking_incoming', 'incoming', 'Receipts', 'stock.action_picking_tree_incoming', 10),
            ('stock_picking_outgoing', 'outgoing', 'Deliveries', 'stock.action_picking_tree_outgoing', 11),
            ('stock_picking_internal', 'internal', 'Internal Transfers', 'stock.action_picking_tree_internal', 12),
        ]
        for cat_id, code, label, action_xmlid, sequence in picking_specs:
            categories[cat_id] = {
                'label': label,
                'module': 'stock',
                'sequence': sequence,
                'specs': [{
                    'model': 'stock.picking',
                    'action_xmlid': action_xmlid,
                    'date_field': 'scheduled_date',
                    'extra_domain': [('picking_type_id.code', '=', code)],
                }],
            }

        categories['stock_move'] = {
            'label': 'Stock Moves',
            'module': 'stock',
            'sequence': 20,
            'specs': [{
                'model': 'stock.move',
                'action_xmlid': 'stock.stock_move_action',
                'date_field': 'date',
            }],
        }
        categories['stock_move_line'] = {
            'label': 'Stock Move Lines',
            'module': 'stock',
            'sequence': 21,
            'specs': [{
                'model': 'stock.move.line',
                'action_xmlid': 'stock.stock_move_line_action',
                'date_field': 'date',
            }],
        }
        return categories
