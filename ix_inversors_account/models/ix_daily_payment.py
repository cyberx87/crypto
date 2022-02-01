# -*- encoding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class IxDailyPay(models.Model):
    _name = 'ix.daily.payment'
    _description = 'ix.daily.payment'
    _inherit = 'image.mixin'
    _order = 'date desc'

    display_name = fields.Char('Name', compute='set_display_name')
    name = fields.Float('Payment %', digits=(1, 2))
    date = fields.Date('Date', required=True)
    color = fields.Integer('Color', compute='set_color')
    imported = fields.Boolean('Imported')

    _sql_constraints = [('unique_date', 'unique (date)', "This date already registered!")]

    @api.depends('color')
    def set_color(self):
        for rec in self:
            rec.color = rec.name * 100 - (110 if rec.name * 100 >= 110 else 100)

    @api.depends('name', 'date')
    def set_display_name(self):
        for rec in self:
            rec.display_name = '(%s)%s' % (str(rec.name) + '%', rec.date.strftime('%A %d/%m/%Y').title())

    @api.constrains('date', 'name')
    def constrains_all(self):
        for rec in self:
            if rec.name <= 0:
                raise ValidationError(_('The Amount must be greater than 0!'))
            if rec.date > fields.Date.today():
                raise ValidationError(_('The date must be lower or equals to today date!'))
            if rec.date.weekday() in [5, 6]:
                raise ValidationError(_('You cannot register payment in weekend day!'))
            rec.register_payment()

    def register_payment(self):
        self.ensure_one()
        available_user_ids = self.env['ix.user'].search([('active_inversion_id', '!=', False)])
        available_user_ids.create_ix_daily_payment(self.date, self.name)

    def register_payment_all(self):
        for rec in self.search([]):
            rec.register_payment()
