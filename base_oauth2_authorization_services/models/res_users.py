# -*- coding: utf-8 -*-

import logging
import requests
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessDenied, UserError

_logger = logging.getLogger(__name__)

class ResUsers(models.Model):
    _inherit = 'res.users'

    def _check_credentials(self, password):
        try:
            return super(ResUsers, self)._check_credentials(password)
        except AccessDenied:
            _logger.info("AccessDenied and checks for oauth_access_token..")
            OuthAppToken = self.env['rest.oauth.app.token']
            oauth_app_token = OuthAppToken.check_access_token(password)
            if not oauth_app_token:
                info = _("The access_token is expired or not found or invalid in user login!")
                _logger.error(info)
                raise
        except Exception:
            _logger.info("Exception during request Authentication!")
            raise
        