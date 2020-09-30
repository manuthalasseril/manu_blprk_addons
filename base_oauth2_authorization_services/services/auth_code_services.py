# -*- coding: utf-8 -*-
# Copyright 2020 Manu Varghese [manuthalasseril@gmail.com]

import logging
from werkzeug.wrappers import Response as WResponse
from werkzeug import urls, utils
from werkzeug.exceptions import BadRequest
from odoo.http import request, Response
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.addons.component.core import Component
from odoo.addons.base_rest.components.service import skip_secure_params, skip_secure_response
from odoo.exceptions import (
    UserError, MissingError, AccessError, AccessDenied, ValidationError)
from ..controllers.main import _REST_NAME

_logger = logging.getLogger(__name__)

class AuthCodeService(Component):
    _inherit = 'base.rest.service'
    _name = 'auth.code.service'
    _usage = 'code'
    _collection = '.'.join([_REST_NAME, 'auth', 'code', 'services'])
    _description = """
        Auth Code authorize Service to generate auth code for an application.
    """
    
    def _validator_search(self):
        return {
            'response_type': {'type': 'string', 'required': True},
            'client_id': {'type': 'string', 'required': True},
            'redirect_uri': {'type': 'string', 'required': True},
            'scope': {'type': 'string', 'required': True},
            'state': {'type': 'string', 'required': True},
        }

    #@skip_secure_params
    @skip_secure_response    
    def search(self, **params):
        """
            Service used to get auth code
        """
        _logger.info(_("Requested Auth Code Service..."))
        try:
            response_type = params.get('response_type')
            client_id = params.get('client_id')
            redirect_uri = params.get('redirect_uri')
            scope = params.get('scope')
            state = params.get('state')
            if response_type not in ['code']:
                raise UserError(_('The value of \"response_type" must be "code"'))
            encoded_params = urls.url_encode({
                'code': 'gg',
                'state': 'dd'
            })
            redirect_uri = '?'.join([redirect_uri, encoded_params])
            return utils.redirect(redirect_uri)
        except Exception as e:
            raise e
        
    #def _validator_return_search(self):
    #    return Response
    
    