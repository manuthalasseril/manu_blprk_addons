# -*- coding: utf-8 -*-

from collections import defaultdict

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_round, float_is_zero, pycompat

from odoo.addons import decimal_precision as dp

import logging
_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = "product.template"
    
    uom_category_id = fields.Many2one('uom.category', string='Unit of Measure Category', related='uom_id.category_id', readonly=True)

class ProductProduct(models.Model):
    _inherit = "product.product"
    
    uom_category_id = fields.Many2one('uom.category', string='Unit of Measure Category', related='product_tmpl_id.uom_category_id', readonly=True)
    
    

class StockMove(models.Model):
    _inherit = "stock.move"

    @api.depends('sale_line_id.qty_invoiced', 'purchase_line_id.qty_invoiced')
    def _get_invoice_qty(self):
        for move in self:
            qty_invoiced = 0.0
            if move.sale_line_id:
                qty_invoiced = move.sale_line_id.qty_invoiced
            elif move.purchase_line_id:
                qty_invoiced = move.purchase_line_id.qty_invoiced
            move.qty_invoiced = qty_invoiced
    
    
    qty_invoiced = fields.Float(
        compute='_get_invoice_qty', string='Invoiced Quantity', store=True, readonly=True,
        digits=dp.get_precision('Product Unit of Measure'))
    to_exchange = fields.Boolean(string="To Exchange")


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.depends('org_picking_id', 'exchange_picking_ids')
    def _get_exchange_data(self):
        for picking in self:
            picking.update({
                'exchange_pickings_count': len(picking.exchange_picking_ids),
            })

    org_picking_id = fields.Many2one(related="sale_id.org_picking_id", string="Original Sale Picking", store=True, readonly=False)
    exchange_picking_ids = fields.One2many('stock.picking', 'org_picking_id', string='Exchange Order Pickings', readonly=False)
    exchange_pickings_count = fields.Integer(string='Exchange Order Pickings Count', compute='_get_exchange_data', readonly=True)    

    @api.multi
    def action_view_exchange_delivery(self):
        self.ensure_one()
        action = self.env.ref('stock.action_picking_tree_all').read()[0]
        pickings = self.mapped('exchange_picking_ids')
        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids)]
        elif pickings:
            action['views'] = [(self.env.ref('stock.view_picking_form').id, 'form')]
            action['res_id'] = pickings.id
        return action
    
    
    