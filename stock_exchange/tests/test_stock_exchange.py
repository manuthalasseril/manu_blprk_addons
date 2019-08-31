# -*- coding: utf-8 -*-

from odoo.addons.sale_stock.tests.test_sale_stock import TestSaleStock
from odoo.exceptions import UserError
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestStockExchange(TestSaleStock):
    
    def test_00_sale_stock_exchange(self):
        """
        Test a SO with a product invoiced on delivery. Deliver and invoice the SO, then do a exchange
        of the picking. Check that a exchange is well generated.
        """
        # intial so
        self.partner = self.env.ref('base.res_partner_1')
        self.product = self.env.ref('product.product_delivery_01')
        so_vals = {
            'partner_id': self.partner.id,
            'partner_invoice_id': self.partner.id,
            'partner_shipping_id': self.partner.id,
            'order_line': [(0, 0, {
                'name': self.product.name,
                'product_id': self.product.id,
                'product_uom_qty': 5.0,
                'product_uom': self.product.uom_id.id,
                'price_unit': self.product.list_price})],
            'pricelist_id': self.env.ref('product.list0').id,
        }
        self.so = self.env['sale.order'].create(so_vals)

        # confirm our standard so, check the picking
        self.so.action_confirm()
        self.assertTrue(self.so.picking_ids, 'Sale Stock: no picking created for "invoice on delivery" storable products')

        # invoice in on delivery, nothing should be invoiced
        self.assertEqual(self.so.invoice_status, 'no', 'Sale Stock: so invoice_status should be "no" instead of "%s".' % self.so.invoice_status)

        # deliver completely
        pick = self.so.picking_ids
        pick.move_lines.write({'quantity_done': 5})
        pick.button_validate()

        # Check quantity delivered
        del_qty = sum(sol.qty_delivered for sol in self.so.order_line)
        self.assertEqual(del_qty, 5.0, 'Sale Stock: delivered quantity should be 5.0 instead of %s after complete delivery' % del_qty)

        # Check invoice
        self.assertEqual(self.so.invoice_status, 'to invoice', 'Sale Stock: so invoice_status should be "to invoice" instead of "%s" before invoicing' % self.so.invoice_status)
        inv_1_id = self.so.action_invoice_create()
        self.assertEqual(self.so.invoice_status, 'invoiced', 'Sale Stock: so invoice_status should be "invoiced" instead of "%s" after invoicing' % self.so.invoice_status)
        self.assertEqual(len(inv_1_id), 1, 'Sale Stock: only one invoice instead of "%s" should be created' % len(inv_1_id))
        self.inv_1 = self.env['account.invoice'].browse(inv_1_id)
        self.assertEqual(self.inv_1.amount_untaxed, self.inv_1.amount_untaxed, 'Sale Stock: amount in SO and invoice should be the same')
        self.inv_1.action_invoice_open()

        # Create return picking
        StockReturnPicking = self.env['stock.return.picking']
        default_data = StockReturnPicking.with_context(active_ids=pick.ids, active_id=pick.ids[0]).default_get(['move_dest_exists', 'original_location_id', 'product_return_moves', 'parent_location_id', 'location_id'])
        return_wiz = StockReturnPicking.with_context(active_ids=pick.ids, active_id=pick.ids[0]).create(default_data)
        return_wiz.product_return_moves.quantity = 2.0 # Return only 2
        return_wiz.product_return_moves.to_exchange = True # Refund these 2
        res = return_wiz.create_returns()
        self.exchange_order = self.env['sale.order'].search([('org_order_id', '=', self.so.id)])
        self.assertEqual(self.exchange_order.state, 'sale', 'Stock Exchange: Exchange Order status should be "sale" instead of "%s" after exchange' % self.exchange_order.state)

