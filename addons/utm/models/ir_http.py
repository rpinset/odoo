# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models
from odoo.http import request, Response
from odoo.tools import SQL


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def get_utm_domain_cookies(cls):
        return request.httprequest.host

    @classmethod
    def _set_utm(cls, response):
        # Make sure response is an odoo Response.
        response = Response.load(response)
        domain = cls.get_utm_domain_cookies()
        if request and request.params and not request.env.cr.readonly:
            utm_mixin = request.env['utm.mixin']
            for url_param, field_name, cookie_name in utm_mixin.tracking_fields():
                if url_param in request.params:
                    value = request.params[url_param]
                    if isinstance(value, str) and value.strip():
                        field = utm_mixin._fields.get(field_name)
                        if field and field.type == 'many2one':
                            record = utm_mixin._find_or_create_record(field.comodel_name, value.strip())
                            request.env.cr.execute(
                                SQL(
                                    "UPDATE %s SET visit_count = visit_count + 1 WHERE id = %s",
                                    SQL.identifier(record._table),
                                    record.id,
                                )
                            )
        for url_parameter, __, cookie_name in request.env['utm.mixin'].tracking_fields():
            if url_parameter in request.params and request.cookies.get(cookie_name) != request.params[url_parameter]:
                response.set_cookie(cookie_name, request.params[url_parameter], max_age=31 * 24 * 3600, domain=domain, cookie_type='optional')

    @classmethod
    def _post_dispatch(cls, response):
        cls._set_utm(response)
        super()._post_dispatch(response)
