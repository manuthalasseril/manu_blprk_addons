# -*- coding: utf-8 -*-
# Copyright 2020 Manu Varghese [manuthalasseril@gmail.com]

{
    'name': 'Base Oauth2 Authorization Services',
    'version': '1.0.0',
    'category': 'API',
    'author': 'Manu Varghese [manuthalasseril@gmail.com]',
    'license': 'AGPL-3',
    'summary': 'Oauth2 Authorization Services',
    'description': """
                Oauth2 Authorization Services
    """,
    'depends': ['mail', 'base_rest'],
    'data': [
        'security/ir.model.access.csv',
        'views/oauth_app.xml',
        'views/oauth_app_token.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'auto_install': False,
}
