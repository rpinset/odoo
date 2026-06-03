# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.fields import Domain
from odoo.http import request

SKIP_CAPTCHA_LOGIN = object()


class ResUsers(models.Model):
    _inherit = "res.users"

    offline_prefetch_hours = fields.Integer(
        string="Offline prefetch horizon (hours)",
        default=2,
        help="Default number of hours to prefetch data for offline use.",
    )
    offline_prefetch_scope = fields.Selection(
        selection=[('me', "Me"), ('all', "Everyone")],
        string="Offline prefetch scope",
        default='me',
    )
    offline_prefetch_category_keys = fields.Json(
        string="Offline prefetch categories",
        default=list,
    )

    @api.model
    def name_search(self, name='', domain=None, operator='ilike', limit=100):
        # if we have a search with a limit, move current user as the first result
        domain = Domain(domain or Domain.TRUE)
        user_list = super().name_search(name, domain, operator, limit)
        uid = self.env.uid
        # index 0 is correct not Falsy in this case, use None to avoid ignoring it
        if (index := next((i for i, (user_id, _name) in enumerate(user_list) if user_id == uid), None)) is not None:
            # move found user first
            user_tuple = user_list.pop(index)
            user_list.insert(0, user_tuple)
        elif limit is not None and len(user_list) == limit:
            # user not found and limit reached, try to find the user again
            if user_tuple := super().name_search(name, domain & Domain('id', '=', uid), operator, limit=1):
                user_list = [user_tuple[0], *user_list[:-1]]
        return user_list

    def _on_webclient_bootstrap(self):
        self.ensure_one()

    def _should_captcha_login(self, credential):
        if request and request.env.context.get('skip_captcha_login') is SKIP_CAPTCHA_LOGIN:
            return False
        return credential['type'] == 'password'
