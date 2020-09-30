# -*- coding: utf-8 -*-
# Copyright 2020 Manu Varghese [manuthalasseril@gmail.com]

import logging
from odoo.addons.base_rest.controllers.main import RestController

_logger = logging.getLogger(__name__)

_REST_NAME = 'base_rest'

class RestAuth(RestController):
    _root_path = '/'.join(['',_REST_NAME, 'authx/'])
    _collection_name = '.'.join([_REST_NAME, 'auth', 'code', 'services'])
    _default_auth = 'public'