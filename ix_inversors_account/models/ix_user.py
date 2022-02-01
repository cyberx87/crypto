# -*- encoding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _name = 'ix.user'
    _description = 'ix.user'
    _inherit = 'image.mixin'
    _order = 'owner_id,partner_id,name'

    name = fields.Char('User', required=True)
    owner_id = fields.Many2one('res.partner', 'Owner', required=True)
    partner_id = fields.Many2one('res.partner', 'Partner', required=True)
    parent_id = fields.Many2one('ix.user', 'Coach')
    tree_branch = fields.Selection([('right', 'Right'), ('left', 'Left')], 'Binary Tree Branch')
    active = fields.Boolean(related="partner_id.active", readonly=False, default=True)
    image_1920 = fields.Binary(related="owner_id.image_1920", readonly=False)
    user_name = fields.Char(related="partner_id.user_name", required=True, readonly=False)
    lastname_father = fields.Char(related="partner_id.lastname_father", required=True, readonly=False)
    lastname_mother = fields.Char(related="partner_id.lastname_mother", required=True, readonly=False)
    birthdate = fields.Date(related="partner_id.birthdate", required=True, readonly=False)
    identifier = fields.Char(related="partner_id.identifier", required=True, readonly=False)
    street = fields.Char(related="partner_id.street", required=True, readonly=False)
    street2 = fields.Char(related="partner_id.street2", required=False, readonly=False)
    phone = fields.Char(related="partner_id.phone", required=True, readonly=False)
    email = fields.Char(related="partner_id.email", required=True, readonly=False)
    city = fields.Char(related="partner_id.city", required=True, readonly=False, default='Puerto Padre')
    zip = fields.Char(related="partner_id.zip", required=True, readonly=False, default='77200')
    state_id = fields.Many2one(related="partner_id.state_id", readonly=False, default=lambda s: s.env.ref('base.cu'))
    country_id = fields.Many2one(related="partner_id.country_id", required=True, readonly=False, default=lambda s: s.env.ref('base.cu'))
    inversion_ids = fields.One2many('ix.inversion', 'user_id', 'Inversions')
    inversion_count = fields.Integer('Operations', compute='set_inversion_count')
    active_inversion_id = fields.Many2one('ix.inversion', 'Current Inversion')
    amount_total_payment = fields.Float(related='active_inversion_id.amount_total_payment')
    amount_maximum = fields.Integer(related='active_inversion_id.amount_maximum')
    currency_id = fields.Many2one(related='active_inversion_id.currency_id')
    amount_can_pay = fields.Boolean(related='active_inversion_id.amount_can_pay')
    amount_available = fields.Float(related='active_inversion_id.amount_available')
    amount_plan = fields.Integer(related='active_inversion_id.amount_plan')
    amount_payment_per = fields.Float(related='active_inversion_id.amount_payment_per')
    amount_gain = fields.Float(related='active_inversion_id.amount_gain')
    inversion_image_128 = fields.Binary(related='active_inversion_id.image_128', readonly=False)
    wallet_ids = fields.Many2many("ix.crypto.wallet", string='Wallets')

    _sql_constraints = [('unique_name', 'unique (name)', "This user already exists!")]

    @api.depends('inversion_ids')
    def set_inversion_count(self):
        for rec in self:
            rec.inversion_count = len(rec.active_inversion_id.line_ids)

    @api.onchange('user_name', 'lastname_father', 'lastname_mother')
    def set_display_name(self):
        for rec in self:
            display_name = '%s %s %s' % (rec.user_name or '', rec.lastname_father or '', rec.lastname_mother or '')
            rec.partner_id.name = display_name.replace('  ', ' ').strip()

    def create_ix_daily_payment(self, date, amount):
        for rec in self:
            if rec.active_inversion_id:
                rec.active_inversion_id.create_ix_daily_payment(date, amount)

    def update_all_inversions(self):
        for rec in self:
            if rec.active_inversion_id:
                rec.active_inversion_id.set_amount_all()

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        for rec in self:
            rec.country_id = self.env.ref('base.cu')
            if not rec.state_id:
                rec.state_id = rec.country_id.state_ids[0]
            if not rec.city:
                rec.city = 'Puerto Padre'
            if not rec.zip:
                rec.zip = '77200'

    def upgrade_inversion(self):
        self.ensure_one()
        next_plan_id = self.env['ix.plan'].search([('amount', '>', self.amount_plan or 0)], order='amount', limit=1)
        return {
            'name': _('Create Plan'),
            'view_mode': 'form',
            'res_model': 'ix.inversion',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('amount', '>', self.amount_plan)],
            'target': 'new',
            'context': {
                'default_user_id': self.id,
                'default_parent_id': self.active_inversion_id.id,
                'default_plan_id': next_plan_id.id or False,
            }
        }

