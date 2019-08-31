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

    org_picking_id = fields.Many2one(related="sale_id.org_picking_id", string="Origin Picking", store=True, readonly=False)
    exchange_picking_ids = fields.One2many('stock.picking', 'org_picking_id', string='Exchange Order Pickings')
    
    
    