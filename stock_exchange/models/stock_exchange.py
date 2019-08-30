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
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Stock Exchange"
    _order = 'date_exchange desc, id desc'

    name = fields.Char(string='Exchange Reference', required=True, copy=False, readonly=True, states={'draft': [('readonly', False)]}, index=True, default=lambda self: _('New'))
    origin = fields.Char(string='Source Document', help="Reference of the document that generated this sales order request.")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', track_sequence=3, default='draft')
    date_exchange = fields.Datetime(string='Exchange Date', required=True, readonly=True, index=True, states={'draft': [('readonly', False)]}, copy=False, default=fields.Datetime.now)
    create_date = fields.Datetime(string='Creation Date', readonly=True, index=True)
    confirmation_date = fields.Datetime(string='Confirmation Date', readonly=True, index=True, copy=False)
    user_id = fields.Many2one('res.users', string='Responsible', index=True, track_visibility='onchange', track_sequence=2, default=lambda self: self.env.user)
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account', readonly=True, states={'draft': [('readonly', False)]}, copy=False)

    #exchange_line = fields.One2many('exchange.line', 'exchange_id', string='Exchange Lines', states={'cancel': [('readonly', True)], 'done': [('readonly', True)]}, copy=True, auto_join=True)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env['res.company']._company_default_get('sale.order'))
    
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
    _rec_name = 'product_id'
    _description = "Stock Exchange Line"
    _order = 'exchange_id, sequence, id'
    
    exchange_id = fields.Many2one('stock.exchange', string='Exchange Reference', required=True, ondelete='cascade', index=True, copy=False)
    name = fields.Text(string='Description', default="Exchange", required=True)
    sequence = fields.Integer(string='Sequence', default=10) 
    org_price_unit = fields.Float('Unit Price', required=True, digits=dp.get_precision('Product Price'), default=0.0)

    org_price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', readonly=True, store=True)
    org_price_tax = fields.Float(compute='_compute_amount', string='Total Tax', readonly=True, store=True)
    org_price_total = fields.Monetary(compute='_compute_amount', string='Total', readonly=True, store=True)

    org_tax_id = fields.Many2many('account.tax', string='Taxes', domain=['|', ('active', '=', False), ('active', '=', True)])
    
    org_product_id = fields.Many2one('product.product', string='Product', domain=[('sale_ok', '=', True)], change_default=True, ondelete='restrict')
    org_product_uom_qty = fields.Float(string='Ordered Quantity', digits=dp.get_precision('Product Unit of Measure'), required=True, default=1.0)
    org_product_uom = fields.Many2one('uom.uom', string='Unit of Measure')

    
    
       
    price_unit = fields.Float('Unit Price', required=True, digits=dp.get_precision('Product Price'), default=0.0)

    price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', readonly=True, store=True)
    price_tax = fields.Float(compute='_compute_amount', string='Total Tax', readonly=True, store=True)
    price_total = fields.Monetary(compute='_compute_amount', string='Total', readonly=True, store=True)

    tax_id = fields.Many2many('account.tax', string='Taxes', domain=['|', ('active', '=', False), ('active', '=', True)])
    
    product_id = fields.Many2one('product.product', string='Product', domain=[('sale_ok', '=', True)], change_default=True, ondelete='restrict')
    product_uom_qty = fields.Float(string='Ordered Quantity', digits=dp.get_precision('Product Unit of Measure'), required=True, default=1.0)
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure')



