odoo.define('web.exchange_picking', function (require) {
"use strict";

var AbstractField = require('web.AbstractField');
var concurrency = require('web.concurrency');
var core = require('web.core');
var field_registry = require('web.field_registry');

var QWeb = core.qweb;
var _t = core._t;

var FieldExchangePicking = AbstractField.extend({
	
    init: function () {
        this._super.apply(this, arguments);
        this.dm = new concurrency.DropMisordered();
    },
    _getExchangePickingData: function (picking_id) {
        var self = this;
        return this.dm.add(this._rpc({
            route: '/stock_exchange/picking',
            params: {
            	picking_id: picking_id,
            },
        })).then(function (data) {
            self.pickingData = data;
        });
    },
    _render: function () {
        if (!this.recordData.id) {
            return this.$el.html(QWeb.render("exchange_picking", {}));
        }

        var self = this;
        return this._getExchangePickingData(this.recordData.id).then(function () {
            self.$el.html(QWeb.render("exchange_picking", self.pickingData));
        });
    },
});

field_registry.add('exchange_picking', FieldExchangePicking);

return FieldExchangePicking;

});
