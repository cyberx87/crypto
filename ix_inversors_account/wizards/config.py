# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import zeep
import logging

_logger = logging.getLogger(__name__)


class ConfigurationWizard(models.TransientModel):
    _name = 'ix.config.wizard'
    _description = 'ix.config.wizard'

    def register_payment_all(self):
        self.env['ix.daily.payment'].register_payment_all()

    def update_all_inversions(self):
        self.env['ix.user'].search([]).update_all_inversions()
