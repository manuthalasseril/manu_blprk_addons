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
    _name = "stock.exchange"
    _inherit = ['sale.order']
    _description = "Stock Exchange"

    name = fields.Char(string='Exchange Reference')
    
    @api.multi
    def unlink(self):
        for order in self:
            if order.state not in ('draft'):
                raise UserError(_('You can not delete a record on this stage!.'))
        return super(StockExchange, self).unlink()


    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code('stock.exchange') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('stock.exchange') or _('New')
        result = super(StockExchange, self).create(vals)
        return result


class StockExchangeLine(models.Model):
    _name = "stock.exchange.line"
    _inherit = ['sale.order.line']
    
    org_price_unit = fields.Float('Unit Price', required=True, digits=dp.get_precision('Product Price'), default=0.0)

    org_price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', readonly=True, store=True)
    org_price_tax = fields.Float(compute='_compute_amount', string='Total Tax', readonly=True, store=True)
    org_price_total = fields.Monetary(compute='_compute_amount', string='Total', readonly=True, store=True)

    org_tax_id = fields.Many2many('account.tax', string='Taxes', domain=['|', ('active', '=', False), ('active', '=', True)])
    
    org_product_id = fields.Many2one('product.product', string='Product', domain=[('sale_ok', '=', True)], change_default=True, ondelete='restrict')
    org_product_uom_qty = fields.Float(string='Ordered Quantity', digits=dp.get_precision('Product Unit of Measure'), required=True, default=1.0)
    org_product_uom = fields.Many2one('uom.uom', string='Unit of Measure')


