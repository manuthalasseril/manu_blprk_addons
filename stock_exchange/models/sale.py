# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from functools import partial
from itertools import groupby

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import formatLang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare


from odoo.addons import decimal_precision as dp

from werkzeug.urls import url_encode


class StockExchange(models.Model):
    _inherit = "sale.order"
    
    is_exchange = fields.Boolean(string="Is Exchange", readonly=True)
    org_order_id = fields.Many2one('sale.order', string='Origin Order', readonly=True)
    org_picking_id = fields.Many2one('stock.picking', string='Origin Picking', readonly=True)

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New') and vals.get('is_exchange', False):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code('stock.exchange') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('stock.exchange') or _('New')
        result = super(StockExchange, self).create(vals)
        return result    

    def _force_exh_inv_lines_to_invoice_policy_order(self, mode):
        for line in self.order_line:
            if mode == 'inv' and line.price_unit > 0:
                pass
            elif mode == 'cn' and line.price_unit < 0:
                pass
            elif mode == 'exh_prod' and line.is_exh_prod and line.price_unit == 0:
                pass
            else:
                continue
            if self.state in ['sale', 'done']:
                line.qty_to_invoice = line.product_uom_qty - line.qty_invoiced
            else:
                line.qty_to_invoice = 0
                        

class StockExchangeLine(models.Model):
    _inherit = "sale.order.line"

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'real_price_unit', 'tax_id')
    def _compute_real_amount(self):
        for line in self:
            amount_discount = line.price_unit * float((line.discount or 0.0) / 100.0)
            price = line.real_price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_shipping_id)
            line.update({
                'real_price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'real_price_total': taxes['total_included'],
                'real_price_subtotal': taxes['total_excluded'],
                'amount_discount': amount_discount,
            })

    
    is_exchange = fields.Boolean(related='order_id.is_exchange', store=True, string='Is Exchange', readonly=True)
    is_exh_prod = fields.Boolean(string='Is Exchange Other Product', readonly=True, default=False)
    sale_line_id = fields.Many2one('sale.order.line', string='Sale Line', readonly=True)
    sale_price_unit = fields.Float('Sale Unit Price', readonly=True, digits=dp.get_precision('Product Price'), default=0.0)
    sale_price_subtotal = fields.Monetary(string='Sale Subtotal', readonly=True)
    sale_price_tax = fields.Float(string='Sale Total Tax', readonly=True)
    sale_price_total = fields.Monetary(string='Sale Total', readonly=True)
    
    sale_tax_id = fields.Many2many('account.tax', string='Sale Taxes', readonly=True, domain=['|', ('active', '=', False), ('active', '=', True)])
    
    sale_product_id = fields.Many2one('product.product', string='Sale Product', readonly=True, domain=[('sale_ok', '=', True)], change_default=True, ondelete='restrict')
    sale_product_uom_qty = fields.Float(string='Sale Qty', readonly=True, digits=dp.get_precision('Product Unit of Measure'))
    sale_product_uom = fields.Many2one('uom.uom', string='Sale UOM', readonly=True)
    org_move_id = fields.Many2one('stock.move', string='Origin Stock Move')

    
    
    real_price_unit = fields.Float('Real Product Unit Price', readonly=True, digits=dp.get_precision('Product Price'), default=0.0)
    real_price_subtotal = fields.Monetary(compute='_compute_real_amount', string='Real Subtotal', readonly=True, store=True)
    real_price_tax = fields.Float(compute='_compute_real_amount', string='Real Total Tax', readonly=True, store=True)
    real_price_total = fields.Monetary(compute='_compute_real_amount', string='Real Total', readonly=True, store=True)
    amount_discount = fields.Monetary(compute='_compute_real_amount', string='Discount Amount', readonly=True, store=True)

    
    