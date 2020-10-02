# -*- coding: utf-8 -*-
# Copyright 2020 Manu Varghese [manuthalasseril@gmail.com]

import logging
import functools
import odoo
from odoo import api, http, models, fields, tools, http, SUPERUSER_ID 
from odoo.http import request
from odoo.tools.misc import ustr
from odoo.api import Environment
from odoo.service import security
from odoo.tools.translate import _

_logger = logging.getLogger(__name__)
    
def check_access_token(func):
    @functools.wraps(func)
    def wrap(self, *args, **kwargs):
        httprequest = request.httprequest
        try:
            access_token = httprequest.headers.get('access_token', None)
            if not access_token:      
                access_token = request.params.get('access_token', None)
            if not access_token:
                info = _("Missing access token in request header or params!")
                _logger.error(info)
                raise http.SessionExpiredException(info)  
            db_name = httprequest.headers.get('db_name', None)
            if not db_name:      
                db_name = request.params.pop('db_name', odoo.tools.config.get('db_name', False))
            if not db_name:
                info = _("Database name not supplied!")
                _logger.error(info)
                raise http.SessionExpiredException(info)             
            registry = odoo.registry(db_name)
            with registry.cursor() as cr:
                env = Environment(cr, SUPERUSER_ID, {})
                OuthAppToken = env['rest.oauth.app.token']
                oauth_app_token = OuthAppToken.check_access_token(access_token)
                if not oauth_app_token:
                    info = _("The access_token is expired or not found or invalid!")
                    _logger.error(info)
                    raise http.SessionExpiredException(info)
                user = oauth_app_token.user_id
                #user_vals = oauth_app_token.get_user_vals(access_token)
                #user_id = user_vals.get('user_id')
                uid = request.session.authenticate(request.session.db, user.login, access_token)
                request.session.uid = user.id
                request.session.login = user.login
                request.session.session_token = user.id and security.compute_session_token(request.session, request.env)
                request.uid = user.id
                request.disable_db = False
                #request.session.rotate = True
                #request.session.db = db                
                request.session.get_context()  
                if not request.uid:
                    raise http.SessionExpiredException(_("Wrong Token"))                 
        except Exception as e:
            request.is_frontend = False
            if getattr(e, 'args', ()):
                e = [ustr(a) for a in e.args]
                e = e[0]
            err = odoo.tools.exception_to_unicode(e)
            _logger.exception(err)
            raise http.SessionExpiredException(err)
        return func(self, *args, **kwargs)
    return wrap

class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'    
    
    @classmethod
    @check_access_token
    def _auth_method_access_token(cls):
        request.uid = request.session.uid
        if not request.uid:
            raise http.SessionExpiredException("Session expired")
        
        
