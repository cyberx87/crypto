# -*- encoding: utf-8 -*-
#
# Module written to Odoo, Open Source Management Solution
#
# Copyright (c) 2019 WEDOO - http://www.wedoo.tech/
# All Rights Reserved.
# Developer(s): Daniel Betancourt Mendoza
#               (dbm@wedoo.tech)
########################################################################
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
########################################################################
from odoo import models, fields, api


class IxCurrency(models.Model):
    _name = 'ix.crypto.currency'
    _description = 'Crypto Currency'
    _rec_name = 'display_name'

    name = fields.Char('Name', required=True)
    display_name = fields.Char('Name', compute='_set_display_name')
    short_name = fields.Char('Short Name', required=True)

    _sql_constraints = [('short_name_unique', 'unique (short_name)', "This currency already exists!")]

    @api.depends('name', 'short_name')
    def name_get(self):
        res = []
        for record in self:
            name = record.name or ''
            if record.short_name:
                name = '%s(%s)' % (name, record.short_name)
            res.append((record.id, name))
        return res

    @api.depends('name', 'short_name')
    def _set_display_name(self):
        for record in self:
            record.display_name = '%s (%s)' % (record.name,
                                               record.short_name or '')


class IxExchange(models.Model):
    _name = 'ix.crypto.exchange'
    _description = 'Crypto Exchange'

    name = fields.Char('Name', required=True)
    wallet_ids = fields.One2many('ix.crypto.wallet', 'exchange_id', 'Wallets')
    description = fields.Text('Description')

    _sql_constraints = [('name_unique', 'unique (name)', "This exchange already exists!")]


class IxWallet(models.Model):
    _name = 'ix.crypto.wallet'
    _description = 'Crypto Wallet'
    _rec_name = 'display_name'

    name = fields.Char('Name', required=True)
    display_name = fields.Char('Name', compute='_set_display_name')
    path = fields.Char('Path', required=True)
    currency_id = fields.Many2one('ix.crypto.currency', 'Currency', required=True)
    exchange_id = fields.Many2one('ix.crypto.exchange', 'Exchange')

    _sql_constraints = [('path_unique', 'unique (path)', "This path already exists in other wallet!")]

    @api.depends('name', 'path', 'currency_id', 'exchange_id')
    def _set_display_name(self):
        for record in self:
            record.display_name = '%s-%s (%s)' % (record.name,
                                                  record.exchange_id.name or '',
                                                  record.currency_id.short_name or '')
