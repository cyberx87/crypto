# -*- encoding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class IxPlan(models.Model):
    _name = 'ix.plan'
    _description = 'ix.plan'
    _inherit = 'image.mixin'
    _order = 'amount'

    name = fields.Char('Name', required=True)
    active = fields.Boolean('Active', default=True)
    amount = fields.Integer('Amount', default=100)
    currency_id = fields.Many2one('res.currency', 'Currency', default=lambda s: s.env.ref("base.USD"), required=True)
    type = fields.Selection([('start', 'Start'), ('upgrade', 'Upgrade')], 'Type')
    payment_type = fields.Selection([('btc', 'BTC'), ('usdt_trc20', 'USDT (trc20)')], 'Payment Type')
    user_id = fields.Many2one('ix.user', 'User', required=False)
