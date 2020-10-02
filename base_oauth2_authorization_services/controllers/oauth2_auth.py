# -*- coding: utf-8 -*-
# Copyright 2020 Manu Varghese [manuthalasseril@gmail.com]

import logging
import json
import werkzeug
import requests
from odoo import http, tools
from odoo.http import request, Response
from werkzeug.wrappers import Response as WZresponse
from werkzeug import urls, utils
from urllib.parse import urljoin, urlparse, unquote
from odoo.tools.misc import ustr
from odoo.tools.translate import _
from odoo.exceptions import (
    UserError, MissingError, AccessError, AccessDenied, ValidationError)
from werkzeug.exceptions import (
    Forbidden, NotFound, BadRequest, HTTPException)
from odoo.addons.auth_oauth.controllers.main import fragment_to_query_string
from .main import _REST_NAME

_logger = logging.getLogger(__name__)
http_status_codes = {
                     'ok': 200,
                     'created': 201,
                     'accepted': 202,
                     'redirect': 302,
                     'bad_request': 400,
                     'unauthorized': 401,
                     'forbidden': 403,
                     'not_found': 404,
                     'method_not_allowed': 405,
                     'not_acceptable': 406,
                     'internal_server_error': 500,
                     'not_implemented': 501,
                     'service_unavailable': 503,
                    }
rest_auth_code_endpoint = '/'.join(['',_REST_NAME, 'auth', 'code']) 
rest_auth_odoo_endpoint = '/'.join(['',_REST_NAME, 'auth', 'odoo']) 
rest_auth_token_endpoint = '/'.join(['',_REST_NAME, 'auth', 'token'])
#odoo_oauth2client_endpoint = '/auth_oauth/signin'
   
class RestAuth(http.Controller):
    
    @http.route([rest_auth_code_endpoint], type='http', auth='user')#, csrf=False
    def rest_request_auth_code_implicit(self, **kwargs):
        _logger.info(_("Requested Auth Code Service..."))        
        try:
            response_type = kwargs.get('response_type', None)
            client_id = kwargs.get('client_id', None)
            return_redirect = kwargs.get('return_redirect', True) 
            redirect_uri = kwargs.get('redirect_uri', None)
            odoo_oauth2client_uri = kwargs.get('odoo_oauth2client_uri', None)
            scope = kwargs.get('scope', None)
            state = kwargs.get('state', None)        
            user = request.env.user
            if None in [response_type,client_id, redirect_uri, scope, state]:
                error_msg = _('The following parameters are must: response_type, client_id, redirect_uri, scope.')
                _logger.error(error_msg)
                return self.generate_response(http_status_codes['not_acceptable'], error_msg)
            if response_type not in ['code', 'token']:
                error_msg = _('The value of "response_type" must be either "code" or "token"')
                _logger.error(error_msg)
                return self.generate_response(http_status_codes['not_acceptable'], error_msg)
            if return_redirect not in [True, False]:
                error_msg = _('The value of "return_redirect" must be either "True" or "False"')
                _logger.error(error_msg)  
                return self.generate_response(http_status_codes['not_acceptable'], error_msg)
            redirect_uri = unquote(redirect_uri)
            OuthApplication = request.env['rest.oauth.app']
            oauth_app = OuthApplication.search([('client_id', '=', client_id)])
            if not oauth_app:
                error_msg = _('The "client_id" is wrong')
                _logger.error(error_msg)  
                return self.generate_response(http_status_codes['unauthorized'], error_msg)
            auth_redirect_uri = urljoin(redirect_uri, urlparse(redirect_uri).path)
            auth_redirect_uri = redirect_uri
            auth_redirect_uris = [x.strip() for x in oauth_app.auth_redirect_uri.split(',')]
            if auth_redirect_uri not in auth_redirect_uris:
                error_msg = _('The value of "redirect_uri" is wrong')
                _logger.error(error_msg)  
                return self.generate_response(http_status_codes['unauthorized'], error_msg)
            OuthAppToken = request.env['rest.oauth.app.token']
            OuthAppAuthCode = request.env['rest.oauth.app.auth.code']
            vals = {
                    'oauth_app_id': oauth_app.id,
                    'user_id': user.id,
                    'location_uri': redirect_uri,
                }
            oauth_app_token = OuthAppToken.create(vals)
            res = {}
            if response_type == 'code' and oauth_app.type_auth_grant == 'auth_code':
                auth_code_vals = OuthAppAuthCode.generate_auth_vals(oauth_app_token.id)
                auth_code = auth_code_vals.get('auth_code')
                res.update({
                        'code': auth_code,
                        'scope': scope,
                        'state': state,
                        'redirect_uri': redirect_uri,
                        'odoo_oauth2client_uri': odoo_oauth2client_uri,
                    })
            elif response_type == 'token' and oauth_app.type_auth_grant == 'implicit':
                oauth_app_token.action_generate_access_token()
                token_vals = oauth_app_token.get_token_vals(oauth_app_token.id)
                res.update(token_vals) 
            else:
                error_msg = _('The requested application cant found!')
                _logger.error(error_msg)  
                return self.generate_response(http_status_codes['not_found'], error_msg)
            if return_redirect:
                encoded_params = urls.url_encode(res)
                redirect_uri = '?'.join([redirect_uri, encoded_params])
                _logger.info(_("Requested auth_code redirected to redirect_uri"))
                return utils.redirect(redirect_uri)
            else:
                _logger.info(_("Requested auth_code returned"))  
                return self.generate_response(http_status_codes['created'], res)
        except Exception as e:
            if getattr(e, 'args', ()):
                e = [ustr(a) for a in e.args]
                e = e[0]
            error_msg = tools.exception_to_unicode(e)
            _logger.exception(error_msg)
            #_logger.error(error_msg)  
            return self.generate_response(http_status_codes['internal_server_error'], error_msg)
            

    @http.route(rest_auth_odoo_endpoint, type='http', auth='none', csrf=False)
    def rest_request_auth_odoo(self, **kwargs):
        #To Do: Need to cjeck can easily be attacked. if then, find another solution
        _logger.info(_("Requested Odoo Auth Service..."))
        try:
            code = kwargs.get('code', None)
            scope = kwargs.get('scope', None)
            state = kwargs.get('state', None)
            redirect_uri = kwargs.get('redirect_uri', None)
            odoo_oauth2client_uri = kwargs.get('odoo_oauth2client_uri', None)
            if None in [code, state, odoo_oauth2client_uri]: 
                error_msg = _('The following parameters are must: code, state, odoo_oauth2client_uri')
                _logger.error(error_msg)    
                return self.generate_response(http_status_codes['not_acceptable'], error_msg)
            redirect_uri = unquote(redirect_uri)
            odoo_oauth2client_uri = unquote(odoo_oauth2client_uri)
            OuthAppAuthCode = request.env['rest.oauth.app.auth.code']
            oauth_app = OuthAppAuthCode.get_oauthapp_auth_code(code) 
            if not oauth_app:
                error_msg = _('The auth code is either expired or not found')
                _logger.error(error_msg)  
                return self.generate_response(http_status_codes['unauthorized'], error_msg)
            auth_redirect_uri = urljoin(redirect_uri, urlparse(redirect_uri).path)
            auth_redirect_uri = redirect_uri
            auth_redirect_uris = [x.strip() for x in oauth_app.auth_redirect_uri.split(',')]
            if auth_redirect_uri not in auth_redirect_uris:
                error_msg = _('The value of "redirect_uri" is wrong')
                _logger.error(error_msg)  
                return self.generate_response(http_status_codes['unauthorized'], error_msg)
            odoo_oauth2client_uri = urljoin(odoo_oauth2client_uri, urlparse(odoo_oauth2client_uri).path)
            odoo_oauth2client_uri = odoo_oauth2client_uri
            if odoo_oauth2client_uri != oauth_app.odoo_oauth2client_uri:
                error_msg = _('The value of "odoo_oauth2client_uri" is wrong')
                _logger.error(error_msg)  
                return self.generate_response(http_status_codes['bad_request'], error_msg)
            client_id = oauth_app.client_id
            client_secret = oauth_app.client_secret
            gen_auth_headers = oauth_app.generate_basic_auth_header(client_id, client_secret)
            params = {
                    'code': code,
                    'grant_type': 'authorization_code',
                    'redirect_uri': redirect_uri,
                    'scope': scope,
                    'state': state,
                }
            encoded_params = urls.url_encode(params)            
            base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
            auth_token_uri = urls.url_join(base_url, rest_auth_token_endpoint)
            auth_token_uri = '?'.join([auth_token_uri, encoded_params])
            _logger.info(_("Requested auth_code redirected from odoo endpoint to access_token endpoint"))
            res = requests.request('GET', auth_token_uri, data=params, headers=gen_auth_headers)
            status = res.status_code
            try:
                response = res.json()
            except Exception as e:
                response = res.text
                return self.generate_response(status, response)
            oauth_app_token = OuthAppAuthCode.get_token_auth_code(code)
            encoded_params = urls.url_encode(response)
            odoo_oauth2client_uri = '?'.join([odoo_oauth2client_uri, encoded_params])
            _logger.info(_("Requested auth_code redirected from access_token endpoint to odoo_oauth2client endpoint"))
            return utils.redirect(odoo_oauth2client_uri)
        except Exception as e:
            if getattr(e, 'args', ()):
                e = [ustr(a) for a in e.args]
                e = e[0]
            error_msg = tools.exception_to_unicode(e)
            _logger.exception(error_msg)
            return self.generate_response(http_status_codes['internal_server_error'], error_msg)
        
        
    @http.route(rest_auth_token_endpoint, type='http', auth='none', csrf=False)
    def rest_request_auth_token(self, **kwargs):
        _logger.info(_("Requested Auth Token Service...")) 
        try:
            grant_type = kwargs.get('grant_type', None)
            code = kwargs.get('code', None)
            redirect_uri = kwargs.get('redirect_uri', None)
            if grant_type != 'authorization_code':
                error_msg = _('The "grant_type" must be authorization_code')
                _logger.error(error_msg)  
                return self.generate_response(http_status_codes['not_acceptable'], error_msg)
            if None in [code, redirect_uri]:
                error_msg = _('The following parameters are must: code, redirect_uri')
                _logger.error(error_msg)  
                return self.generate_response(http_status_codes['not_acceptable'], error_msg)
            authorization_header = request.httprequest.headers.get('Authorization')
            if not authorization_header:
                authorization_header = request.httprequest.headers.get('HTTP_AUTHORIZATION')
            if not authorization_header:
                error_msg = _('The "Authorization" header is missing')
                _logger.error(error_msg)  
                return self.generate_response(http_status_codes['not_acceptable'], error_msg)
            redirect_uri = unquote(redirect_uri)
            OuthAppAuthCode = request.env['rest.oauth.app.auth.code']
            oauth_app = OuthAppAuthCode.get_oauthapp_auth_code(code) 
            if not oauth_app:
                error_msg = _('The auth code is either expired or not found')
                _logger.error(error_msg)  
                return self.generate_response(http_status_codes['unauthorized'], error_msg)
            auth_redirect_uri = urljoin(redirect_uri, urlparse(redirect_uri).path)
            auth_redirect_uri = redirect_uri
            auth_redirect_uris = [x.strip() for x in oauth_app.auth_redirect_uri.split(',')]
            if auth_redirect_uri not in auth_redirect_uris:
                error_msg = _('The value of "redirect_uri" is wrong')
                _logger.error(error_msg)  
                return self.generate_response(http_status_codes['unauthorized'], error_msg)
            client_id = oauth_app.client_id
            client_secret = oauth_app.client_secret
            gen_auth_headers = oauth_app.generate_basic_auth_header(client_id, client_secret)
            authorization = gen_auth_headers.get('Authorization')
            if authorization != authorization_header:
                error_msg = _('Either client_id or client_secret wrong or wrongly encoded!')
                _logger.error(error_msg)  
                return self.generate_response(http_status_codes['unauthorized'], error_msg)
            oauth_app_token = OuthAppAuthCode.get_token_auth_code(code)
            oauth_app_token.action_generate_access_token()
            oauth_app_token.action_generate_refresh_token()
            token_vals = oauth_app_token.get_token_vals(oauth_app_token.id)
            OuthAppAuthCode.check_auth_code(code).action_invalid()   
            return self.generate_response(http_status_codes['created'], token_vals)
        except Exception as e:
            if getattr(e, 'args', ()):
                e = [ustr(a) for a in e.args]
                e = e[0]
            error_msg = tools.exception_to_unicode(e)
            _logger.exception(error_msg)
            return self.generate_response(http_status_codes['internal_server_error'], error_msg)
        
    def generate_response(self, status_code, data={}, headers=[]):
        _logger.info(_("Generating response with status code %s!") %(str(status_code)))       
        try:
            if data:
                try:
                    data = isinstance(data, str) and data or json.dumps(data)
                except ValueError:
                    data = str(data)            
            response = request.make_response(data, headers)
            response.status_code = status_code
            return response
        except Exception as e:#To Do: Is it needed? recursive?
            if getattr(e, 'args', ()):
                e = [ustr(a) for a in e.args]
                e = e[0]
            error_msg = tools.exception_to_unicode(e)
            _logger.exception(error_msg)
            return self.generate_response(http_status_codes['internal_server_error'], error_msg)
        
        
            
    