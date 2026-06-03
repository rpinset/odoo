# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models
from odoo.fields import Domain


class OfflinePrefetch(models.AbstractModel):
    _inherit = 'offline.prefetch'

    @api.model
    def _search_records(self, spec, hours, scope):
        if spec['model'] != 'sale.order.line':
            return super()._search_records(spec, hours, scope)
        order_spec = {
            'model': 'sale.order',
            'date_field': 'date_order',
            'extra_domain': spec.get('extra_domain'),
        }
        orders = super()._search_records(order_spec, hours, scope)
        if not orders:
            return self.env['sale.order.line']
        domain = Domain([('order_id', 'in', orders.ids)])
        if scope == 'me':
            domain &= self._me_domain('sale.order.line')
        return self.env['sale.order.line'].search(domain, limit=2000)

    @api.model
    def _offline_prefetch_categories(self):
        categories = super()._offline_prefetch_categories()
        if not self._is_module_installed('sale'):
            return categories

        categories['sale_order'] = {
            'label': 'Sales Orders',
            'module': 'sale',
            'sequence': 30,
            'specs': [{
                'model': 'sale.order',
                'action_xmlid': 'sale.action_orders',
                'date_field': 'date_order',
            }],
        }
        categories['sale_order_line'] = {
            'label': 'Sales Order Lines',
            'module': 'sale',
            'sequence': 31,
            'specs': [{
                'model': 'sale.order.line',
                'action_xmlid': 'sale.action_orders',
            }],
        }
        return categories
