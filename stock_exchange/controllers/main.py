# -*- coding: utf-8 -*-

from odoo import http
from odoo.exceptions import AccessError
from odoo.http import request


class ExchangeController(http.Controller):

    @http.route('/stock_exchange/picking', type='json', auth='user')
    def get_exchange_picking(self, picking_id):
        if not picking_id:  # to check
            return {}
        picking_id = int(picking_id)
        exchange_pickings = []
        Picking = request.env['stock.picking']
        # check and raise
        if not Picking.check_access_rights('read', raise_exception=False):
            return {}
        try:
            Picking.browse(picking_id).check_access_rule('read')
        except AccessError:
            return {}
        else:
            picking = Picking.browse(picking_id)
            for exchange_picking in picking.exchange_picking_ids:
                exchange_pickings.append(
                    {
                        'name': exchange_picking.name,
                        'state': exchange_picking.state,
                        'date': 'Generete me!',
                    }
                )
        return {
            'exchange_pickings': exchange_pickings,
        }
