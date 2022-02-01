# -*- encoding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime

PAYOUT_COMMISSION = 5


class IxInversion(models.Model):
    _name = 'ix.inversion'
    _description = 'ix.inversion'
    _inherit = 'image.mixin'
    _order = 'user_owner_id,date_start'

    name = fields.Char('User', required=True, compute='set_name')
    parent_id = fields.Many2one('ix.inversion', 'Previous Inversion')
    same_plan_count = fields.Integer('Same plan count', default=1)
    active = fields.Boolean('Active', default=True)
    date_start = fields.Date('Start Date', compute='set_start_date')
    type = fields.Selection([('start', 'Start'), ('upgrade', 'Upgrade')], 'Type', compute='set_type')
    payment_type = fields.Selection([('btc', 'BTC'), ('usdt_trc20', 'USDT (trc20)')], 'Payment Type', default='btc')
    user_id = fields.Many2one('ix.user', 'User', required=True, ondelete='cascade')
    user_image_1920 = fields.Binary(related="user_id.image_1920")
    user_image_128 = fields.Binary(related="user_id.image_128")
    user_owner_id = fields.Many2one(related="user_id.owner_id", store=True)
    plan_id = fields.Many2one('ix.plan', 'Plan', required=True, default=lambda s: s.env.ref('ix_inversors_account.plan_100'))
    currency_id = fields.Many2one(related="plan_id.currency_id", default=lambda s: s.env.ref("base.USD"))
    image_128 = fields.Binary(related="plan_id.image_128")
    image_1920 = fields.Binary(related="plan_id.image_1920")
    amount_plan = fields.Integer(related='plan_id.amount', store=True)
    amount_maximum = fields.Integer('Amount Maximum', compute='set_amount_maximum', store=True)
    amount_sponsor = fields.Float('Sponsor Commissions', digits=(18, 2), compute='set_amount_all', store=True)
    amount_binary = fields.Float('Binary Bonus', digits=(18, 2), compute='set_amount_all', store=True)
    amount_daily = fields.Float('Daily Bonus', digits=(18, 2), compute='set_amount_all', store=True)
    amount_payout = fields.Float('Payouts Released', digits=(18, 2), compute='set_amount_all', store=True)
    amount_payout_parent = fields.Float('Parent Payouts Released', digits=(18, 2), compute='set_amount_all', store=True)
    amount_payout_fee = fields.Float('Payouts Fee', digits=(18, 2), compute='set_amount_all', store=True)
    amount_available = fields.Float('Available Amount', digits=(18, 2), compute='set_amount_all', store=True)
    amount_error = fields.Float('Reduced Fee', digits=(18, 2))
    amount_total_payment_before = fields.Float('Total Payments Before', digits=(18, 2), compute='set_amount_all', store=True)
    amount_total_payment = fields.Float('Total Payments', digits=(18, 2), compute='set_amount_all', store=True)
    amount_payment_per = fields.Float('Payments %', digits=(18, 2), compute='set_amount_all', store=True)
    amount_total_left = fields.Float('Total Left Payments', digits=(18, 2), compute='set_amount_all', store=True)
    amount_can_pay = fields.Boolean('Available Payment', compute='set_amount_can_pay', store=True)
    amount_plan_purchase_fee = fields.Float('Purchase fee', default=1)
    amount_plan_purchase = fields.Float('Total Plan Purchase', digits=(18, 2), compute='set_amount_plan_purchase', store=True)
    amount_gain = fields.Float('$ Wined', digits=(18, 2), compute='set_amount_gain', store=True)
    has_pending_payments = fields.Boolean('Has Pending Payments', compute='set_has_pending_payments', store=True)
    line_ids = fields.One2many('ix.inversion.line', 'inversion_id', 'Inversions')

    @api.depends('amount_payout', 'amount_plan_purchase')
    def set_amount_gain(self):
        for rec in self:
            rec.amount_gain = rec.amount_payout - rec.amount_plan_purchase

    @api.depends('line_ids.state_payment')
    def set_has_pending_payments(self):
        for rec in self:
            rec.has_pending_payments = any(rec.line_ids.filtered(lambda s: s.state_payment == 'pending'))

    @api.depends('amount_plan_purchase_fee', 'plan_id', 'parent_id', 'same_plan_count', 'amount_plan')
    def set_amount_plan_purchase(self):
        for rec in self:
            amount_plan_purchase = rec.amount_plan * rec.same_plan_count - rec.parent_id.amount_plan + rec.parent_id.amount_plan_purchase
            rec.amount_plan_purchase = amount_plan_purchase + rec.amount_plan_purchase_fee

    @api.depends('amount_plan')
    def set_amount_maximum(self):
        for rec in self:
            rec.amount_maximum = rec.amount_plan * rec.same_plan_count * 3

    @api.depends('amount_plan', 'amount_available', 'line_ids', 'active')
    def set_amount_can_pay(self):
        for rec in self:
            rec.amount_can_pay = rec.amount_available >= rec.amount_plan / 10

    @api.depends('parent_id')
    def set_type(self):
        for rec in self:
            rec.type = 'upgrade' if rec.parent_id and rec.parent_id.plan_id.amount < rec.plan_id.amount else 'start'

    @api.depends('line_ids')
    def set_start_date(self):
        for rec in self:
            line_ids = rec.line_ids.filtered(lambda s: s.imported or s.amount_credit_str or s.amount_debit_str)
            if line_ids:
                line_ids = line_ids[len(line_ids) - 1]
            rec.date_start = line_ids.date.date() if line_ids else fields.Date.today()

    @api.depends('line_ids', 'plan_id', 'active', 'same_plan_count', 'amount_plan_purchase_fee', 'amount_error', 'parent_id')
    def set_amount_all(self):
        for rec in self:
            amount_payout_fee_before = rec.parent_id.amount_payout_fee + rec.parent_id.amount_error if rec.parent_id else 0
            amount_payout_before = rec.parent_id.amount_payout or 0
            amount_total_payment_before = rec.parent_id.amount_total_payment
            if rec.parent_id.same_plan_count > 1:
                amount_total_payment_before -= rec.parent_id.amount_maximum / rec.parent_id.same_plan_count

            sponsor_lines = rec.line_ids.filtered(lambda s: s.amount_type in ['sponsor commission'])
            binary_lines = rec.line_ids.filtered(lambda s: s.amount_type in ['binary bonus'])
            daily_lines = rec.line_ids.filtered(lambda s: s.amount_type in ['daily bonus'])
            payout_lines = rec.line_ids.filtered(lambda s: s.amount_type in ['Payout released'])

            amount_sponsor = sum(sponsor_lines.mapped('amount_credit'))
            amount_binary = sum(binary_lines.mapped('amount_credit'))
            amount_daily = sum(daily_lines.mapped('amount_credit'))
            amount_payout = sum(payout_lines.mapped('amount_debit'))

            amount_total_payment = sum([amount_sponsor, amount_binary, amount_daily]) + amount_total_payment_before
            amount_payout_fee = sum(payout_lines.mapped('amount_payment_fee'))
            amount_available = amount_total_payment - amount_payout - amount_payout_fee - rec.amount_error - amount_total_payment_before

            amount_payout_parent = rec.parent_id.amount_maximum / rec.parent_id.same_plan_count if rec.parent_id.same_plan_count > 1 else 0

            rec.amount_sponsor = amount_sponsor
            rec.amount_binary = amount_binary
            rec.amount_daily = amount_daily
            rec.amount_payout = amount_payout + amount_payout_before
            rec.amount_payout_parent = amount_payout_parent
            rec.amount_payout_fee = amount_payout_fee + amount_payout_fee_before
            rec.amount_total_payment_before = amount_total_payment_before
            rec.amount_total_payment = amount_total_payment
            rec.amount_total_left = rec.amount_maximum - amount_total_payment
            rec.amount_available = amount_available
            rec.amount_payment_per = rec.amount_maximum and amount_total_payment * 100 / rec.amount_maximum or 0

    @api.depends('user_id', 'plan_id', 'active')
    def set_name(self):
        for rec in self:
            parent_plan = '%s/' % rec.parent_id.plan_id.name if rec.parent_id else ''
            name = '%s-%s%s' % (rec.user_id.name or '', parent_plan or '', rec.plan_id.name or '')
            if not rec.active:
                name += ' (Inactive)'
            rec.name = name

    def create_ix_daily_payment(self, date, amount):
        for rec in self:
            # if date >= rec.date_start:
            rec.line_ids.set_date_date()
            dt_date = datetime(date.year, date.month, date.day, 10, 0, 0)
            res = rec.line_ids.filtered(
                lambda s: s.date_date.strftime('%d/%m/%Y') == dt_date.strftime('%d/%m/%Y') and s.amount_type == 'daily bonus' and s.user_id == rec.user_id)
            amount_value = amount * rec.plan_id.amount / 100
            if res:
                vals = {}
                if res.amount_credit != amount_value:
                    vals.update({'amount_credit': amount_value})
                if res.date != dt_date:
                    vals.update({'date': dt_date})
                if res.user_from != rec.user_id.name:
                    vals.update({'user_from': rec.user_id.name})
                if vals:
                    res.write(vals)
            else:
                rec.line_ids.create({
                    'date': dt_date,
                    'amount_type': 'daily bonus',
                    'amount_credit': amount_value,
                    'inversion_id': rec.id,
                    'user_id': rec.user_id.id,
                    'user_from': rec.user_id.name,
                })

    def fill_ix_daily_payment(self):
        """
        Set daily.payment object from inversion line
        :return: Void
        """
        daily_env = self.env['ix.daily.payment']
        daily_ids = daily_env.search([])
        for rec in self:
            daily_lines = rec.line_ids.filtered(lambda s: s.amount_type == 'daily bonus')
            for line in daily_lines:
                if ' ' in line.amount_credit_str:
                    value = line.amount_credit_str.split(' ')[1].strip('()%')
                    daily_id = daily_ids.filtered(lambda s: s.date.strftime('%d/%m/%Y') == line.date.strftime('%d/%m/%Y'))
                    if daily_id:
                        daily_id.name = value
                    else:
                        daily_env.create({
                            'date': line.date_date,
                            'name': value,
                            'imported': True,
                        })

    @api.model
    def create(self, vals):
        result = super().create(vals)
        if result.user_id.active_inversion_id:
            result.user_id.active_inversion_id.active = False
        result.user_id.active_inversion_id = result
        return result


class IxInversionLine(models.Model):
    _name = 'ix.inversion.line'
    _description = 'ix.inversion.line'
    _order = 'date desc'

    name = fields.Char('Name', compute='set_name')
    active = fields.Boolean('Active', default=True)
    inversion_id = fields.Many2one('ix.inversion', 'Inversion', required=True)
    user_id = fields.Many2one('ix.user', 'Username', required=True)
    user_from = fields.Char('From User', default='AdminUser')
    date = fields.Datetime('Date', default=fields.Datetime.now)
    date_date = fields.Datetime('Date', compute='set_date_date', store=True)
    amount_credit = fields.Float('Credit')
    amount_debit = fields.Float('Debit')
    amount_payment_fee = fields.Float('Debit Fee', compute='set_amount_payment_fee')
    amount_credit_str = fields.Char('Credit ($)')
    amount_debit_str = fields.Char('Debit ($)')
    amount_total = fields.Float('Amount Total', help="Amount withing any commission", compute='set_amount_payment_fee')
    amount_is_debit = fields.Boolean('Is Debit', compute='set_amount_is_debit')
    imported = fields.Boolean('Imported')
    currency_id = fields.Many2one(related="inversion_id.currency_id", default=lambda s: s.env.ref("base.USD"))
    amount_type = fields.Selection([
        ('pending', 'Pending'),
        ('daily bonus', 'Daily Bonus'),
        ('binary bonus', 'Binary Bonus'),
        ('sponsor commission', 'Sponsor Commission'),
        ('Payout released', 'Payout Released'),
        ('rejected', 'Rejected'), ], 'Amount Type', default='daily bonus')
    state_payment = fields.Selection([
        ('pending', 'Pending'),
        ('done', 'Done')], 'Payment State', default='done')

    @api.depends('amount_debit')
    def set_amount_payment_fee(self):
        for rec in self:
            rec.amount_total = rec.amount_debit * 100 / (100 - PAYOUT_COMMISSION) + rec.amount_credit
            rec.amount_payment_fee = rec.amount_total - rec.amount_debit

    @api.onchange('amount_type', 'inversion_id')
    def onchange_amount_type(self):
        if self.amount_type == 'Payout released':
            self.amount_debit = self.inversion_id.amount_available * (100 - PAYOUT_COMMISSION) / 100

    @api.depends('date')
    def set_date_date(self):
        for rec in self:
            rec.date_date = rec.date.date()

    @api.depends('amount_type')
    def set_amount_is_debit(self):
        for rec in self:
            rec.amount_is_debit = rec.amount_type == 'Payout released'

    @api.depends('user_id', 'amount_type')
    def set_name(self):
        for rec in self:
            rec.name = '%s - %s (%s)' % (rec.user_id.name, rec.amount_type, rec.date)

    @api.constrains('user_id', 'amount_type', 'date', 'amount_debit')
    def constrains_all(self):
        for rec in self:
            if rec.amount_type == 'Payout released':
                # if rec.inversion_id and not rec.inversion_id.amount_can_pay:
                #     raise ValidationError(_('The payment amount most be greater than 10% of the inversion!'))
                if rec.amount_debit <= 0:
                    raise ValidationError(_('The Payout debit most be greater than zero (> 0)!'))
            elif rec.amount_type == 'sponsor commission':
                if rec.amount_credit <= 0:
                    raise ValidationError(_('The Sponsor Commission credit most be greater than zero (> 0)!'))
            elif rec.amount_type == 'binary bonus':
                if rec.amount_credit <= 0:
                    raise ValidationError(_('The Binary Bonus credit most be greater than zero (> 0)!'))
            elif rec.amount_type == 'daily bonus':
                if rec.amount_credit <= 0:
                    raise ValidationError(_('The daily bonus credit most be greater than zero (> 0)!'))
                exist = rec.search([('user_id', '=', rec.user_id.id),
                                    ('amount_type', '=', rec.amount_type),
                                    ('user_from', '=', rec.user_from),
                                    ('date', '=', rec.date),
                                    ('id', '!=', rec.id), ])
                if exist:
                    raise ValidationError(_('The daily bonus payment is already registered. Is available only one per day!'))

    def create_daily_payment(self):
        self.ensure_one()
        day_pay_env = self.env['ix.daily.payment']
        if self.amount_type == 'daily bonus':
            day_pay_id = day_pay_env.search([('date', '=', self.date_date)])
            if not day_pay_id:
                dt_date = datetime(self.date.year, self.date.month, self.date.day, 5, 0, 0) if self.date.hour < 4 else self.date
                day_pay_env.create({
                    'date': dt_date.strftime('%Y-%m-%d'),
                    'name': self.amount_credit,
                    'imported': True
                })

    @api.model
    def create(self, vals):
        user_id = self.user_id.browse(vals.get('user_id'))
        if not user_id.active_inversion_id:
            raise ValidationError(_('Invalid Inversion for user "%s". You must to create a valid Inversion first' % user_id.name))
        vals.update({'inversion_id': user_id.active_inversion_id.id})
        if 'amount_credit_str' in vals and 'amount_debit_str' in vals:
            amount_credit = vals.get('amount_credit_str').split(' ')[0]
            amount_debit = vals.get('amount_debit_str').split(' ')[0]
            vals.update({'amount_credit': amount_credit,
                         'amount_debit': amount_debit,
                         'imported': True, })
        vals.update({'active': vals.get('amount_type', '') not in ['rejected', 'pending']})
        result = self.get_existing_inv_line(vals)
        if result:
            result.create_daily_payment()
            return result
        result = super(IxInversionLine, self).create(vals)
        result.create_daily_payment()
        return result

    def get_existing_inv_line(self, vals):
        amount_type = vals.get('amount_type')
        line_ids = self.search([('amount_type', '=', amount_type),
                                ('user_id', '=', vals.get('user_id'))])
        current_date = vals.get('date')
        if isinstance(current_date, str):
            current_date = datetime.strptime(vals.get('date'), '%Y-%m-%d %H:%M:%S')
        dt_format = '%d/%m/%Y' if amount_type in ['daily bonus', 'Payout released'] else '%d/%m/%Y %H:%M:%S'
        line_id = line_ids.filtered(lambda s: s.date.strftime(dt_format) == current_date.strftime(dt_format))
        if amount_type == 'binary bonus' and len(line_id) >= 1:
            line_id = line_id.filtered(lambda s: s.user_from == vals.get('user_from'))
        elif amount_type == 'Payout released' and len(line_id) > 1:
            line_id = line_ids.filtered(lambda s: s.date.strftime('%d/%m/%Y %H:%M:%S') == current_date.strftime('%d/%m/%Y %H:%M:%S'))
        if len(line_id) == 1:
            line_id.write(vals)
            return line_id
        elif len(line_id) > 1:
            raise ValidationError(_('Review all lines or delete all before importing its because are some repeated lines.'))
