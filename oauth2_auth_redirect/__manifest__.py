# -*- coding: utf-8 -*-
# Copyright 2020 Manu Varghese [manuthalasseril@gmail.com]

{
    'name': 'Oauth2 Auth Redirect',
    'version': '1.0.0',
    'category': 'API',
    'author': 'Manu Varghese [manuthalasseril@gmail.com]',
    'license': 'AGPL-3',
    'summary': 'Oauth2 Auth Redirect',
    'description': """
                Oauth2 Auth Redirect
    """,
    'depends': ['auth_oauth'],
    'data': [
        'views/auth_oauth_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}
