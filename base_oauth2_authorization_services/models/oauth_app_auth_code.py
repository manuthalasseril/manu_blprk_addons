# -*- coding: utf-8 -*-
# Copyright 2020 Manu Varghese [manuthalasseril@gmail.com]

import logging
from oauthlib import common as oauthlib_common
from datetime import datetime, timedelta
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import (
    UserError, MissingError, AccessError, AccessDenied, ValidationError)

_logger = logging.getLogger(__name__)


class RestOuthApplicationAuthCode(models.Model):
    _name = 'rest.oauth.app.auth.code'
    _rec_name = 'oauth_app_token_id'
    
    oauth_app_token_id = fields.Many2one('rest.oauth.app.token', ondelete='cascade', string="Rest Oauth Application Token", required=True, readonly=True, copy=False)
    auth_code = fields.Many2one('rest.oauth.token', readonly=True, copy=False)
    expiry_auth_code = fields.Datetime(related='auth_code.expire', compute_sudo=True, readonly=True, copy=False)
    
    _sql_constraints = [
        ('auth_code_uniq', 'unique (auth_code)', 'The auth_code must be unique!'),
    ]  
    
    def action_generate_auth_code(self): 
        self.ensure_one()       
        res_field = 'auth_code'
        oauth_app_id = self.oauth_app_token_id.oauth_app_id
        expire = oauth_app_id.expiry_auth_code
        self.env['rest.oauth.token'].action_generate_field_token(res_models=self, res_field=res_field, expire=expire)
        
    @api.model
    def generate_auth_vals(self, oauth_app_token_id):
        oauth_app_token = self.env['rest.oauth.app.token'].browse(oauth_app_token_id)
        oauth_app_token_id = oauth_app_token.id
        vals = {'oauth_app_token_id': oauth_app_token_id}
        oauth_app_auth_code = self.create(vals)
        oauth_app_auth_code.action_generate_auth_code()
        res = {
                'auth_code': oauth_app_auth_code.auth_code.token,
                'expiry_auth_code': oauth_app_auth_code.expiry_auth_code,
            }
        return res

    @api.model
    def check_auth_code(self, auth_code):
        today = fields.Datetime.now()
        oauth_app_auth_code = self.search([
                            ('auth_code.token', '=', auth_code),
                            ('auth_code.expire', '>', today),
                        ])
        return oauth_app_auth_code

    @api.model
    def get_token_auth_code(self, auth_code):
        oauth_app_token = self.oauth_app_token_id
        oauth_app_auth_code = self.check_auth_code(auth_code)
        if oauth_app_auth_code:
            oauth_app_token = oauth_app_auth_code.oauth_app_token_id
        return oauth_app_token

    @api.model
    def get_oauthapp_auth_code(self, auth_code):
        oauth_app = self.oauth_app_token_id.oauth_app_id
        oauth_app_auth_code = self.check_auth_code(auth_code)
        if oauth_app_auth_code:
            oauth_app = oauth_app_auth_code.oauth_app_token_id.oauth_app_id
        return oauth_app
    
    