# -*- coding: utf-8 -*-
# Copyright 2020 Manu Varghese [manuthalasseril@gmail.com]

import logging
import json
import werkzeug.urls
import werkzeug.utils
import urllib
from urllib.parse import urljoin, urlparse, unquote
from werkzeug.exceptions import BadRequest
from odoo.http import request
from odoo.addons.auth_oauth.controllers.main import OAuthLogin

_logger = logging.getLogger(__name__)

class RestOAuthLogin(OAuthLogin):
        
    def list_providers(self):
        providers = super(RestOAuthLogin, self).list_providers()        
        for provd in providers:
            provider = request.env['auth.oauth.provider'].sudo().search([('id', '=', provd['id'])])
            if provider.redirect_uri or provider.response_type:
                auth_link = provd['auth_link']
                auth_link = urlparse(unquote(auth_link))
                auth_link_params = auth_link.query
                querys = auth_link_params.split("&")
                params = {}
                for qs in querys:
                    querys = qs.split("=")
                    params[querys[0]] = querys[1]
                if provider.redirect_uri:
                    params['redirect_uri'] = provider.redirect_uri
                if provider.response_type:
                    params['response_type'] = provider.response_type
                if provider.odoo_oauth2client_uri:
                    params['odoo_oauth2client_uri'] = provider.odoo_oauth2client_uri
                provd['auth_link'] = "%s?%s" % (provd['auth_endpoint'], werkzeug.url_encode(params))
        return providers