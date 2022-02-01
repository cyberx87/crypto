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
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    user_name = fields.Char('Name', required=False)
    lastname_father = fields.Char('Father Lastname', required=False)
    lastname_mother = fields.Char('Mother Lastname', required=False)
    birthdate = fields.Date('Birthdate', required=False)
    user = fields.Char('User', required=False)
    identifier = fields.Char('Identifier', required=False)
    ix_user_ids = fields.One2many('ix.user', 'partner_id', 'Users')

    _sql_constraints = [('user_unique', 'unique (user)', "This user already exists!")]

    @api.onchange('user_name', 'lastname_father', 'lastname_mother')
    def set_display_name(self):
        for rec in self:
            display_name = '%s %s %s' % (rec.user_name or '', rec.lastname_father or '', rec.lastname_mother or '')
            rec.name = display_name.replace('  ', ' ').strip()
