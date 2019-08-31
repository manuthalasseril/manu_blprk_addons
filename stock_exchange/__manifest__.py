# -*- coding: utf-8 -*-
{
    'name': 'Stock Exchange',
    'version': '12.0.1.0.0',
    'category': 'Warehouse',
    'author': 'Manu Varghese [manuthalasseril@gmail.com]',
    'license': 'AGPL-3',
    'depends': ['sale_stock', 'purchase_stock', 'stock_account'],
    'data': [
        'data/ir_sequence_data.xml',
        #'security/exchange_security.xml',
        #'security/ir.model.access.csv',
        'views/exchange_templates.xml',
        'views/sale_view.xml',
        'views/exchange_view.xml',
        'wizard/stock_wiz.xml',
        
    ],
    'qweb': [
        'static/src/xml/exchange_picking.xml',
    ],
    'installable': True,
    'images': [
        'static/description/icon.png',
    ],
}
