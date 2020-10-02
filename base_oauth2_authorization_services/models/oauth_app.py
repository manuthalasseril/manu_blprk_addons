# -*- coding: utf-8 -*-
# Copyright 2020 Manu Varghese [manuthalasseril@gmail.com]

import logging
from base64 import b64encode, b64decode
from oauthlib import common as oauthlib_common
from datetime import datetime, timedelta
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import (
    UserError, MissingError, AccessError, AccessDenied, ValidationError)

_logger = logging.getLogger(__name__)


class RestOuthToken(models.Model):
    _name = 'rest.oauth.token'
    _rec_name = 'token'
    
    @api.model
    def _get_unique_token(self):
        token = oauthlib_common.generate_token()
        while self.search_count([('token', '=', token)]):
            token = oauthlib_common.generate_token()
        return token
        
    @api.depends('res_model', 'res_id')
    def _compute_res_name(self):
        for token in self:
            token.res_name = (token.res_model and token.res_id and token.res_field) and \
                '_'.join([str(token.res_id), self.env[token.res_model].browse(token.res_id).display_name, token.res_field])
    
    type = fields.Selection(selection=[
                                ('bearer', "Bearer"),
                            ], required=True, default='bearer')    
    token = fields.Char(required=True, readonly=True, copy=False, default=_get_unique_token)
    expire = fields.Datetime(readonly=True, copy=False)    
    res_model_id = fields.Many2one('ir.model', 'Related Model', required=True, readonly=True, copy=False, ondelete='cascade')
    res_model = fields.Char('Related Model Name', related='res_model_id.model', compute_sudo=True, store=True, readonly=True, copy=False)
    res_id = fields.Many2oneReference(string='Related ID', required=True, readonly=True, copy=False, model_field='res_model')
    res_name = fields.Char('Related Name', compute='_compute_res_name', compute_sudo=True, store=True, readonly=True, copy=False)
    res_field = fields.Char('Related Field', required=True, readonly=True, copy=False)
    
    _sql_constraints = [
        ('token_res_uniq', 'unique (token,res_model_id,res_field)', 'The token must be unique per model and field!')
    ]
    
    @api.model
    def get_res_vals(self, res_model, res_field=None):
        res_model.ensure_one()
        res_model = res_model.sudo()
        vals = {
                'res_id': res_model.id,
                'res_model_id': res_model.env['ir.model']._get(res_model._name).id
            }
        if res_field:
            vals.update({'res_field': res_field})
        return vals
    
    @api.model
    def action_generate_field_token(self, res_models, res_field, expire=0):
        for res_model in res_models:
            res_model.mapped(res_field).unlink()
            vals = self.get_res_vals(res_model=res_model, res_field=res_field)
            if expire:
                expire = datetime.now() + timedelta(seconds=expire)
                vals.update({'expire': expire})  
            record = self.create(vals)
            res_model.write({res_field: record.id})
    
class RestOuthApplicationOld(models.Model):
    _name = 'rest.oauth.application'
    _inherit = ['mail.thread']

class RestOuthApplication(models.Model):
    _name = 'rest.oauth.app'
    _inherit = ['mail.thread']
    
    name = fields.Char(required=True, copy=False)    
    active = fields.Boolean(default=True)
    description = fields.Text()
    type_client = fields.Selection(selection=[
                                ('public', "Public"),
                                ('confidential', "Confidential")
                            ], string="Client Type", required=True, default='confidential')
    type_auth_grant = fields.Selection(selection=[
                                ('auth_code', "Authorization Code"),
                                ('implicit', "Implicit"),
                                ('password', "Resource Owner Password"),
                                ('credential', 'Client Credentials'),
                                ('refresh_token', 'Refresh Token')
                            ], string="Auth Grant Type", required=True, default='auth_code')
    client_id = fields.Many2one('rest.oauth.token', copy=False)
    client_secret = fields.Many2one('rest.oauth.token', copy=False)
    expiry_auth_code = fields.Integer(default=180)
    expiry_access_token = fields.Integer(default=14400)   
    expiry_refresh_token = fields.Integer(default=14400)
    scope = fields.Char()
    odoo_oauth2client_uri = fields.Char()
    auth_redirect_uri = fields.Text(required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('run', 'Running'),
        ('cancel', 'Cancelled'),
        ], string='Status', readonly=True, copy=False, tracking=3, default='draft')
    
    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'The name must be unique!'),
        ('client_id_uniq', 'unique (client_id)', 'The client_id must be unique!'),
        ('client_secret_uniq', 'unique (client_secret)', 'The client_secret must be unique!'),
    ]

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {}, name=_("%s (copy)") % (self.name))
        return super(RestOuthApplication, self).copy(default)    

    def unlink(self):
        for app in self: 
            if app.state in ('run'):
                raise UserError(_('You can not delete the application from a running state!'))           
            app.client_id.unlink()  
            app.client_secret.unlink() 
        return super(RestOuthApplication, self).unlink()
    
    @api.model
    def generate_basic_auth_header(self, client_id, client_secret):        
        client_pass = "{0}:{1}".format(client_id, client_secret)
        auth_string = b64encode(client_pass.encode("utf-8"))
        auth_headers = {
                "Authorization": "Basic " + auth_string.decode("utf-8"),
            }
        return auth_headers
    
    @api.model
    def get_basic_decode_auth_header(self, client_pass): 
        client_id, client_secret = '', ''
        try:
            client_pass = client_pass.split(' ')[1] 
            client_pass = b64decode(client_pass.encode("utf-8"))
            client_pass = client_pass.decode("utf-8")
            client_pass = client_pass.split(':')
            client_id = client_pass[0]    
            client_secret = client_pass[1]             
        except Exception as e:
            client_id, client_secret = '', ''
        return client_id, client_secret
        
    def action_draft(self):
        return self.write({'state': 'draft'})
        
    def action_run(self):
        return self.write({'state': 'run'})
    
    def action_cancel(self):
        return self.write({'state': 'cancel'})
    
    def action_generate_client_id(self):        
        res_field = 'client_id'
        OauthToken = self.env['rest.oauth.token']
        OauthToken.action_generate_field_token(res_models=self, res_field=res_field)
    
    def action_generate_client_secret(self):        
        res_field = 'client_secret'
        OauthToken = self.env['rest.oauth.token']
        OauthToken.action_generate_field_token(res_models=self, res_field=res_field)
    
    
