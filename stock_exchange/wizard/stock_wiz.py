# -*- coding: utf-8 -*-

from collections import defaultdict

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_round, float_is_zero, pycompat

from odoo.addons import decimal_precision as dp

import logging
_logger = logging.getLogger(__name__)


class StockReturnPickingLine(models.TransientModel):
    _inherit = "stock.return.picking.line"

    to_exchange = fields.Boolean(string="To Exchange")
    ex_product_id = fields.Many2one('product.product', 
                                        domain="[('id', '!=', product_id)]",
                                        string="Exchange Other Product")
    ex_uom_id = fields.Many2one('uom.uom', 
                        readonly=True,
                        domain="[('category_id', '=', ex_uom_category_id)]",
                        string='Exchange Product UOM')
    ex_uom_category_id = fields.Many2one('uom.category', 
                                         string='Unit of Measure Category', 
                                         related='ex_product_id.uom_category_id', readonly=True)
    qty_invoiced = fields.Float(string='Invoiced Quantity', 
                                related='move_id.qty_invoiced',                                
                                readonly=True,
                                digits=dp.get_precision('Product Unit of Measure'))


    @api.onchange('ex_product_id')
    def _onchange_ex_product_id(self):
        ex_product_id = self.ex_product_id
        if ex_product_id:
            self.ex_uom_id = ex_product_id.uom_id.id
        else:
            self.ex_uom_id = False


class ReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    def _prepare_move_default_valuesX(self, return_line, new_picking):
        if return_line.to_exchange:
            sale_id = return_line.to_exchange         
            pass
            
            
        vals = {
            'product_id': return_line.product_id.id,
            'product_uom_qty': return_line.quantity,
            'product_uom': return_line.product_id.uom_id.id,
            'picking_id': new_picking.id,
            'state': 'draft',
            'date_expected': fields.Datetime.now(),
            'location_id': return_line.move_id.location_dest_id.id,
            'location_dest_id': self.location_id.id or return_line.move_id.location_id.id,
            'picking_type_id': new_picking.picking_type_id.id,
            'warehouse_id': self.picking_id.picking_type_id.warehouse_id.id,
            'origin_returned_move_id': return_line.move_id.id,
            'procure_method': 'make_to_stock',
        }
        return vals

    def _create_returns(self):
        #To Do : Check also if it is paid
        lines_notpaid = self.product_return_moves.filtered(lambda rl: rl.to_exchange and rl.quantity > rl.qty_invoiced)
        if lines_notpaid:
            product_names = lines_notpaid.mapped('product_id').mapped('name')
            #raise UserError(_("Only invoiced qty of product lines are allowed.\
            #                  Please correct the following lines: \n %s") % ',\n'.join(product_names))        
        lines_toexchange = self.product_return_moves.filtered(lambda rl: rl.to_exchange)
        if lines_toexchange:
            #OrderLine = self.env['sale.order.line']
            picking_id = self.picking_id
            sale_id = picking_id.sale_id 
            exchange_order = sale_id.copy({
                                'order_line': [],
                                'is_exchange': True,
                                'state': 'draft',
                                'origin': _("Exchange of %s") % sale_id.name,
                                'org_order_id': sale_id.id,
                                'org_picking_id': picking_id.id,
                                'picking_ids': [],
                            })
            exchange_order.onchange_partner_id()
            exchange_order.onchange_partner_shipping_id()
            for exchange_line in lines_toexchange:
                move_id = exchange_line.move_id
                sale_line = move_id.sale_line_id
                sale_price_total = sale_line.price_total
                sale_price_subtotal = sale_line.price_subtotal                 
                #org_product_id = exchange_line.product_id
                product_id = exchange_line.product_id
                uom_id = exchange_line.uom_id
                is_exh_prod = False
                if exchange_line.ex_product_id:
                    product_id = exchange_line.ex_product_id
                    uom_id = exchange_line.ex_uom_id
                    is_exh_prod = True
                product_uom_qty = exchange_line.uom_id._compute_quantity(exchange_line.quantity, uom_id)
                exchange_sale_line = sale_line.copy({
                    'order_id': exchange_order.id,
                    'name': _("Exchange of %s") % sale_line.name,
                    'sale_line_id' : sale_line.id,
                    'sale_price_unit' : sale_line.price_unit,
                    'sale_price_subtotal' : sale_price_subtotal,
                    'sale_price_tax' : sale_line.price_tax,
                    'sale_price_total' : sale_price_total,
                    'sale_tax_id' : sale_line.sale_tax_id.id,
                    'sale_product_id' : sale_line.product_id.id,
                    'sale_product_uom_qty' : sale_line.product_uom_qty,
                    'sale_product_uom' : sale_line.product_uom.id,
                    'org_move_id' : move_id.id,
                    'product_id': product_id.id,
                    'product_uom_qty': product_uom_qty,
                    'product_uom' : uom_id.id,
                    'is_exh_prod': is_exh_prod,
                    'qty_delivered_method': False,
                    'route_id': False,
                    'move_ids': [],
                })
                exchange_sale_line.product_id_change()
                exchange_sale_line.product_uom_change()
                exchange_sale_line._onchange_discount()                
                exchange_sale_line.write({
                    #'product_uom_qty': product_uom_qty,
                    #'product_uom' : uom_id.id,
                })
                #To Do : Didnt Tested! Why its so complicated? Please simplify me! 
                sale_price_unit = sale_line.price_unit
                real_price_unit = exchange_sale_line.price_unit
                
                exchange_price_total = exchange_sale_line.price_total
                exchange_price_subtotal = exchange_sale_line.price_subtotal
                price_unit = 0.0
                
                price_total = round((exchange_price_total - sale_price_total), 2)
                price_subtotal = round((exchange_price_subtotal - sale_price_subtotal), 2)
                if price_total:
                    untaxed_w_discount = price_subtotal + (exchange_sale_line.amount_discount * exchange_sale_line.product_uom_qty)                
                    taxed_w_discount = price_total + (exchange_sale_line.amount_discount * exchange_sale_line.product_uom_qty)
                    tax_factor = (float(taxed_w_discount) / float(untaxed_w_discount or 1.0)) * 100.0
                    price_unit = (float(taxed_w_discount) / float(tax_factor)) * 100.0
                    price_unit = float(price_unit) / float(exchange_sale_line.product_uom_qty)
                #if price_total > 0:
                #    price_unit = price_unit
                #elif price_total < 0:
                #    price_unit = -1 * price_unit
                exchange_sale_line.write({
                    'real_price_unit': real_price_unit,
                    'price_unit': price_unit,
                })
            exchange_invoice_ids = []
            exchange_order._compute_tax_id()  
            exchange_order.action_confirm()
            exchange_order._force_exh_inv_lines_to_invoice_policy_order(mode='inv')
            try:
                exchange_invoice_ids.extend(exchange_order.action_invoice_create()) 
            except:
                pass
            exchange_order._force_exh_inv_lines_to_invoice_policy_order(mode='cn')
            try:
                exchange_invoice_ids.extend(exchange_order.action_invoice_create()) 
            except:
                pass
            exchange_order._force_exh_inv_lines_to_invoice_policy_order(mode='exh_prod')
            try:
                exchange_invoice_ids.extend(exchange_order.action_invoice_create()) 
            except:
                pass
            self.env['account.invoice'].browse(exchange_invoice_ids).action_invoice_open()
            exchange_order.invoice_ids.filtered(lambda inv: inv.state == 'draft' and not inv.invoice_line_ids).unlink()                  
        return super(ReturnPicking, self)._create_returns()
    
    
    