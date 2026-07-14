# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    l10n_fr_deee_category = fields.Selection(
        selection=[
            ('gem', "Large household appliances"),
            ('pam', "Small household appliances"),
            ('ecran', "Screens and monitors"),
            ('eclairage', "Lighting equipment"),
            ('petit_it', "Small IT and telecom equipment"),
            ('outillage', "Electric and electronic tools"),
            ('other', "Other electrical/electronic equipment"),
        ],
        string="DEEE Category (FR)",
        help="Category of the waste electrical and electronic equipment (WEEE/DEEE) "
             "eco-organism this product belongs to, used to justify the eco-participation "
             "amount charged (Art. L.541-10-20 of the Code de l'environnement).",
    )
    l10n_fr_deee_amount = fields.Monetary(
        string="Eco-Participation (DEEE)",
        currency_field='currency_id',
        help="Unit amount of the eco-participation (DEEE) passed on to the customer for "
             "this product. Must be disclosed separately on the invoice (Art. L.541-10-20 "
             "of the Code de l'environnement).",
    )
