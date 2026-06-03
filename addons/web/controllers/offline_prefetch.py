# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http
from odoo.exceptions import AccessError, UserError
from odoo.http import request


class OfflinePrefetchController(http.Controller):

    @http.route('/web/offline/categories', type='jsonrpc', auth='user', readonly=True)
    def categories(self):
        if not request.env.user._is_internal():
            raise AccessError(request.env._("Only internal users can prefetch offline data."))
        return request.env['offline.prefetch'].get_categories()

    @http.route('/web/offline/prefetch', type='jsonrpc', auth='user')
    def prefetch(self, category_ids, hours=2, scope='me'):
        if not request.env.user._is_internal():
            raise AccessError(request.env._("Only internal users can prefetch offline data."))
        if not category_ids:
            raise UserError(request.env._("Select at least one category to collect."))
        return request.env['offline.prefetch'].collect(category_ids, hours=hours, scope=scope)

    @http.route('/web/offline/preferences', type='jsonrpc', auth='user', readonly=True)
    def preferences(self):
        user = request.env.user
        return {
            'hours': user.offline_prefetch_hours or 2,
            'scope': user.offline_prefetch_scope or 'me',
            'category_ids': user.offline_prefetch_category_keys or [],
        }
