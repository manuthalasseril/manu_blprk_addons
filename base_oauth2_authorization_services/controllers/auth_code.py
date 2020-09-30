# -*- coding: utf-8 -*-
# Copyright 2020 Manu Varghese [manuthalasseril@gmail.com]

import logging
from odoo import http
from odoo.http import request
from werkzeug import urls, utils
from urllib.parse import urljoin, urlparse
from odoo.tools.translate import _
from odoo.exceptions import (
    UserError, MissingError, AccessError, AccessDenied, ValidationError)
from .main import _REST_NAME

_logger = logging.getLogger(__name__)
rest_auth_code_endpoint = '/'.join(['',_REST_NAME, 'auth', 'code']) 
   
class RestAuth(http.Controller):
    
    @http.route([rest_auth_code_endpoint], type='http', auth='user')#, csrf=False
    def rest_request_auth_code(self, **kwargs):
        response_type = kwargs.get('response_type', None)
        client_id = kwargs.get('client_id', None)
        redirect_uri = kwargs.get('redirect_uri', None)
        scope = kwargs.get('scope', None)
        state = kwargs.get('state', None)        
        user = request.env.user
        print ()
        if None in [response_type,client_id, redirect_uri, scope, state]:
            raise ValidationError(_('The following parameters are must: response_type, client_id, redirect_uri, scope.'))            
        if response_type not in ['code']:
            raise ValidationError(_('The value of "response_type" must be "code"'))
        
        OuthApplication = request.env['rest.oauth.app'].sudo()
        oauthapp = OuthApplication.search([('client_id', '=', client_id)])
        if not oauthapp:
            raise AccessDenied(_('The "client_id" is wrong'))
        auth_redirect_uri = urljoin(redirect_uri, urlparse(redirect_uri).path)
        auth_redirect_uris = [x.strip() for x in oauthapp.auth_redirect_uri.split(',')]
        if auth_redirect_uri not in auth_redirect_uris:
            raise AccessDenied(_('The value of "redirect_uri" is wrong'))
            
        
        encoded_params = urls.url_encode({
                'code': 'gg',
                'state': 'dd'
            })
        redirect_uri = '?'.join([redirect_uri, encoded_params])
        return utils.redirect(redirect_uri)
            
    