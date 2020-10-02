# -*- coding: utf-8 -*-
# Copyright 2020 Manu Varghese [manuthalasseril@gmail.com]

import logging
from oauthlib import common as oauthlib_common
from datetime import datetime, timedelta
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import (
    UserError, MissingError, AccessError, AccessDenied, ValidationError)

_logger = logging.getLogger(__name__)

class RestOuthApplicationToken(models.Model):
    _name = 'rest.oauth.app.token'
    _rec_name = 'oauth_app_id'    
    
    oauth_app_id = fields.Many2one('rest.oauth.app', required=True, ondelete='cascade', string="Rest Oauth Application", readonly=True, copy=False)
    user_id = fields.Many2one('res.users', required=True,  readonly=True, copy=False)
    location_uri = fields.Char(readonly=True, copy=False)
    access_token = fields.Many2one('rest.oauth.token', readonly=True, copy=False)
    expiry_access_token = fields.Datetime(related='access_token.expire', compute_sudo=True, readonly=True, copy=False)
    refresh_token = fields.Many2one('rest.oauth.token', readonly=True, copy=False)
    expiry_refresh_token = fields.Datetime(related='refresh_token.expire', compute_sudo=True, readonly=True, copy=False)
    state = fields.Selection([
        ('valid', 'Valid'),
        ('invalid', 'Invalid'),
        ], string='Status', readonly=True, copy=False, default='valid')    
    
    _sql_constraints = [
        ('access_token_uniq', 'unique (access_token)', 'The access_token must be unique!'),
        ('refresh_token_uniq', 'unique (refresh_token)', 'The refresh_token must be unique!'),
    ]

    @api.model
    def check_access_token(self, access_token):
        today = fields.Datetime.now()
        oauth_app_token = self.search([
                            ('state', '=', 'valid'),
                            ('access_token.token', '=', access_token),
                            ('access_token.expire', '>', today),
                        ])
        return oauth_app_token

    @api.model
    def check_refresh_token(self, refresh_token):
        today = fields.Datetime.now()
        oauth_app_token = self.search([
                            ('state', '=', 'valid'),
                            ('refresh_token.token', '=', refresh_token),
                            ('refresh_token.expire', '>', today),
                        ])
        return oauth_app_token
    
    def action_generate_access_token(self): 
        self.ensure_one()       
        res_field = 'access_token'
        expire = self.oauth_app_id.expiry_access_token
        self.env['rest.oauth.token'].action_generate_field_token(res_models=self, res_field=res_field, expire=expire)   
    
    def action_generate_refresh_token(self): 
        self.ensure_one()       
        res_field = 'refresh_token'
        expire = self.oauth_app_id.expiry_refresh_token
        self.env['rest.oauth.token'].action_generate_field_token(res_models=self, res_field=res_field, expire=expire)   
        
    @api.model
    def get_token_vals(self, oauth_app_token_id):
        oauth_app_token = self.browse(oauth_app_token_id)
        res = {}
        if oauth_app_token.state == 'valid':
            res.update({
                    'access_token': oauth_app_token.access_token.token,
                    #'token_type': oauth_app_token.access_token.type,
                    'token_type': "Bearer",
                    'expires_in': oauth_app_token.oauth_app_id.expiry_access_token,
                    'refresh_token': oauth_app_token.refresh_token.token,
                })
        return res  
    
    @api.model
    def get_user_vals(self, access_token):
        oauth_app_token = self.check_access_token(access_token)
        res = {}
        if oauth_app_token.state == 'valid':
            res.update({
                'user_id': oauth_app_token.user_id.id,
                })
        return res
    
    def action_invalid(self): 
        self.write({'state': 'invalid'})
        
        
    
        