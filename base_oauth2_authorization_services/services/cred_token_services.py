# -*- coding: utf-8 -*-
# Copyright 2020 Manu Varghese [manuthalasseril@gmail.com]

import logging
import requests
import odoo
from odoo import http, tools
from odoo.http import request, Response
from werkzeug.wrappers import Response as WZresponse
from werkzeug import urls, utils
from odoo.tools.misc import ustr
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.tools.translate import _
from odoo.addons.component.core import Component
from odoo.addons.base_rest.components.service import to_int, skip_secure_params, skip_secure_response
from odoo.addons.base_rest.http import JSONEncoder
from odoo.exceptions import (
    UserError, MissingError, AccessError, AccessDenied, ValidationError)
from odoo.exceptions import (
    UserError, MissingError, AccessError, AccessDenied, ValidationError)
from werkzeug.exceptions import (
    Forbidden, NotFound, BadRequest, HTTPException)
from ..controllers.main import _REST_NAME

_logger = logging.getLogger(__name__)


class CredTokenService(Component):
    _inherit = 'base.rest.service'
    _name = 'cred.token.service'
    _usage = 'token'
    _collection = '.'.join([_REST_NAME, 'cred', 'token', 'services'])
    _description = """
        Resource Owner Credentials authorize Service to generate token for an application.
    """

    @skip_secure_params
    def create(self, **params):
        """
            This method is used for generating token
        """
        try:
            db_name = params.get('db_name', None)
            username = params['username'] if params.get('username') else None
            password = params['password'] if params.get('password') else None                
            if not db_name:      
                db_name = request.httprequest.headers.get('db_name', tools.config.get('db_name', False))
            if not username or not password:
                info = _("Empty value for 'username' or 'password'!")
                _logger.error(info)
                raise http.SessionExpiredException(info)
            if not db_name:
                info = _("Empty value for 'db_name'!")
                _logger.error(info)
                raise http.SessionExpiredException(_(info))
            try:
                request.session.authenticate(db_name, username, password)
            except Exception as e:
                err = odoo.tools.exception_to_unicode(e)
                _logger.exception(err)
                raise http.SessionExpiredException(_("Wrong login/password (%s") % (err))
            uid = request.session.uid          
            if uid:                
                authorization_header = request.httprequest.headers.get('Authorization')
                if not authorization_header:
                    authorization_header = request.httprequest.headers.get('HTTP_AUTHORIZATION')
                if not authorization_header:
                    error_msg = _('The "Authorization" header is missing')
                    _logger.error(error_msg)
                    raise ValidationError(error_msg)
                OuthApplication = self.env['rest.oauth.app'].sudo()
                client_id, client_secret = OuthApplication.get_basic_decode_auth_header(authorization_header) 
                if not client_id or not client_secret:
                    error_msg = _('The "client_id" or "client_secret" is wrong')
                    _logger.error(error_msg)
                    raise ValidationError(error_msg)
                oauth_app = OuthApplication.search([('client_id', '=', client_id), ('client_secret', '=', client_secret)])
                if not oauth_app:
                    error_msg = _('The "client_id" or "client_secret" are not belongs to the registered app!')
                    _logger.error(error_msg)
                    raise ValidationError(error_msg)
                OuthAppToken = request.env['rest.oauth.app.token'].sudo() 
                user = self.env['res.users'].sudo().browse(uid)
                           
                vals = {
                    'oauth_app_id': oauth_app.id,
                    'user_id': user.id,
                }
                oauth_app_token = OuthAppToken.create(vals)
                oauth_app_token.action_generate_access_token()
                oauth_app_token.action_generate_refresh_token()
                token_vals = oauth_app_token.get_token_vals(oauth_app_token.id)
                token_vals.update({
                            'user_context': request.session.get_context(),
                            'company_id': self.env.user.company_id.id if uid else 'null',
                        })
                return {            
                        'name': _("OK"),
                        'code': 200,
                        'description': _("Login was successfull"),
                        'data': token_vals,
                    }
            else:
                raise http.SessionExpiredException(_("Wrong login/password"))
        except Exception as e:
            request.is_frontend = False
            if getattr(e, 'args', ()):
                e = [ustr(a) for a in e.args]
                e = e[0]
            err = odoo.tools.exception_to_unicode(e)
            _logger.exception(err)
            raise http.SessionExpiredException(err)

    def _validator_create(self):
        return {
                'db_name': {'type': 'string'},
                'username': {'type': 'string', 'required': True, 'empty': False}, 
                'password': {'type': 'string', 'required': True, 'empty': False},                
            }

    def _validator_return_create(self):
        return {            
            'name': {'type': 'string', 'required': True, 'empty': False},
            'code': {'type': 'integer', 'required': True, 'empty': False},
            'description': {'type': 'string', 'required': True, 'empty': False},
            'data': {
                    'type': 'dict',                    
                    'schema': {
                        'access_token': {'type': 'string'},
                        'refresh_token': {'type': 'string'},
                        'token_type': {'type': 'string'},
                        'expires_in':{                                                 
                                    'type': 'integer',
                                    'coerce': to_int,
                                    },
                        'company_id': {                                    
                                    'type': 'integer',
                                    'coerce': to_int,
                                },
                        'user_context': {
                                'type': 'dict',                    
                                'schema': {
                                    'uid': {                                    
                                        'type': 'integer',
                                        'coerce': to_int,
                                    },
                                    'lang': {'type': 'string'},
                                    'tz': {'type': 'string'},
                                },                            
                            },
                        },
                    }
                }
        
