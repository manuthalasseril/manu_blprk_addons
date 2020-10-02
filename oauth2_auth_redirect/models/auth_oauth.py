# -*- coding: utf-8 -*-

from odoo import fields, models


class AuthOAuthProvider(models.Model):
    _inherit = 'auth.oauth.provider'
    
    redirect_uri = fields.Char()
    odoo_oauth2client_uri = fields.Char(string="Client Endpoint")
    response_type = fields.Selection(selection=[('code', "Code"), ('token', "Token")])    
    