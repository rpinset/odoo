# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from datetime import timedelta

from odoo import api, fields, models
from odoo.fields import Domain

_logger = logging.getLogger(__name__)

PREFETCH_LIMIT = 2000
PAST_WINDOW_HOURS = 24


class OfflinePrefetch(models.AbstractModel):
    _name = 'offline.prefetch'
    _description = 'Offline data prefetch'

    # -------------------------------------------------------------------------
    # API for the web client
    # -------------------------------------------------------------------------

    @api.model
    def get_categories(self):
        """Return prefetch categories for installed modules."""
        return [
            {'id': key, **value}
            for key, value in sorted(self._offline_prefetch_categories().items(), key=lambda item: item[1]['sequence'])
        ]

    @api.model
    def collect(self, category_ids, hours=2, scope='me'):
        """Search records to prefetch and return a manifest for the web client."""
        hours = max(1, min(16, int(hours)))
        scope = scope if scope in ('me', 'all') else 'me'
        user = self.env.user
        user.sudo().write({
            'offline_prefetch_hours': hours,
            'offline_prefetch_scope': scope,
            'offline_prefetch_category_keys': category_ids,
        })

        categories = self._offline_prefetch_categories()
        unknown = set(category_ids) - set(categories)
        if unknown:
            raise ValueError(f"Unknown offline prefetch categories: {', '.join(sorted(unknown))}")

        manifest = []
        partner_ids = set()
        for category_id in category_ids:
            category = categories[category_id]
            for spec in category['specs']:
                records = self._search_records(spec, hours, scope)
                if not records:
                    continue
                partner_ids.update(self._partner_ids_from_records(records))
                manifest.append({
                    'category_id': category_id,
                    'model': spec['model'],
                    'res_ids': records.ids[:PREFETCH_LIMIT],
                    'action_xmlid': spec['action_xmlid'],
                    'view_types': spec.get('view_types', ['list', 'form']),
                })

        partners = self.env['res.partner'].browse(partner_ids).exists()
        all_partner_ids = set(partners.ids)
        all_partner_ids.update(partners.child_ids.ids)

        return {
            'hours': hours,
            'scope': scope,
            'manifest': manifest,
            'partners': {
                'model': 'res.partner',
                'res_ids': list(all_partner_ids),
                'action_xmlid': 'base.action_partner_form',
                'view_types': ['form'],
            },
        }

    # -------------------------------------------------------------------------
    # Category registry (extended in stock, sale, ...)
    # -------------------------------------------------------------------------

    @api.model
    def _offline_prefetch_categories(self):
        return {}

    # -------------------------------------------------------------------------
    # Domain helpers
    # -------------------------------------------------------------------------

    @api.model
    def _is_module_installed(self, module_name):
        return bool(self.env['ir.module.module'].sudo().search_count([
            ('name', '=', module_name),
            ('state', '=', 'installed'),
        ]))

    @api.model
    def _time_domain(self, field_name, hours):
        now = fields.Datetime.now()
        past = now - timedelta(hours=PAST_WINDOW_HOURS)
        future = now + timedelta(hours=hours)
        return [
            '|',
            (field_name, '=', False),
            '&',
            (field_name, '>=', fields.Datetime.to_string(past)),
            (field_name, '<=', fields.Datetime.to_string(future)),
        ]

    @api.model
    def _company_domain(self):
        return [('company_id', 'in', self.env.companies.ids)]

    @api.model
    def _me_domain(self, model_name):
        user = self.env.user
        partner_id = user.partner_id.id
        clauses = []

        if follower_ids := self._follower_ids(model_name, partner_id):
            clauses.append([('id', 'in', follower_ids)])

        employee_ids = []
        if self._is_module_installed('hr') and 'hr.employee' in self.env:
            employee_ids = self.env['hr.employee'].search([('user_id', '=', user.id)]).ids

        model = self.env[model_name]
        for field_name, field in model._fields.items():
            if field.type == 'many2one':
                if field.comodel_name == 'res.users':
                    clauses.append([(field_name, '=', user.id)])
                elif field.comodel_name == 'res.partner' and partner_id:
                    clauses.append([(field_name, '=', partner_id)])
                elif field.comodel_name == 'hr.employee' and employee_ids:
                    clauses.append([(field_name, 'in', employee_ids)])
            elif field.type == 'many2many':
                if field.comodel_name == 'res.users':
                    clauses.append([(field_name, 'in', user.id)])
                elif field.comodel_name == 'res.partner' and partner_id:
                    clauses.append([(field_name, 'in', partner_id)])
                elif field.comodel_name == 'hr.employee' and employee_ids:
                    clauses.append([(field_name, 'in', employee_ids)])

        if not clauses:
            return Domain.FALSE
        return Domain.OR([Domain(c) for c in clauses])

    @api.model
    def _follower_ids(self, model_name, partner_id):
        if not partner_id or 'mail.followers' not in self.env:
            return []
        return self.env['mail.followers'].sudo().search([
            ('res_model', '=', model_name),
            ('partner_id', '=', partner_id),
        ]).mapped('res_id')

    @api.model
    def _build_domain(self, spec, hours, scope):
        domain = Domain(self._company_domain())
        if date_field := spec.get('date_field'):
            domain &= Domain(self._time_domain(date_field, hours))
        extra = spec.get('extra_domain') or []
        domain &= Domain(extra)
        if scope == 'me':
            domain &= self._me_domain(spec['model'])
        return domain

    @api.model
    def _search_records(self, spec, hours, scope):
        domain = self._build_domain(spec, hours, scope)
        return self.env[spec['model']].search(domain, limit=PREFETCH_LIMIT)

    @api.model
    def _partner_ids_from_records(self, records):
        partner_ids = set()
        for record in records:
            for field_name, field in record._fields.items():
                if field.type == 'many2one' and field.comodel_name == 'res.partner':
                    partner = record[field_name]
                    if partner:
                        partner_ids.add(partner.id)
                elif field.type == 'many2many' and field.comodel_name == 'res.partner':
                    partner_ids.update(record[field_name].ids)
        return partner_ids
