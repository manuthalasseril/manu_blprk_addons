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
    
    oauth_app_id = fields.Many2one('rest.oauth.app', ondelete='cascade', string="Rest Oauth Application", required=True, readonly=True, copy=False)
    user_id = fields.Many2one('res.users', required=True,  readonly=True, copy=False)
    location_uri = fields.Char(required=True, readonly=True, copy=False)
    access_token = fields.Many2one('rest.oauth.token', readonly=True, copy=False)
    expiry_access_token = fields.Datetime(related='access_token.expire', compute_sudo=True, readonly=True, copy=False)
    refresh_token = fields.Many2one('rest.oauth.token', readonly=True, copy=False)
    expiry_refresh_token = fields.Datetime(related='access_token.expire', compute_sudo=True, readonly=True, copy=False)    
    
    _sql_constraints = [
        ('access_token_uniq', 'unique (access_token)', 'The access_token must be unique!'),
        ('refresh_token_uniq', 'unique (refresh_token)', 'The refresh_token must be unique!'),
    ]   
    
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
        
        