module.exports = function (RED) {
    "use strict";

    // Two low-power relays #03-1

    var TpCommon = require('./tpCommon');

    function TP_03_1_OutNode(config) {
        RED.nodes.createNode(this, config);

        // config
        var node = this;
        this.config = config;

        // common
        var tc = new TpCommon("tp03_1_out", node);

        // Launch python
        tc.execPy([config.tpSlot, config.host]);

        // On Node Input
        tc.onInput(function (msg) {

            return msg.payload;
        });

        // On Node Output
        tc.onOutput();
    }
    RED.nodes.registerType("Tibbit-03_1 out", TP_03_1_OutNode);
}
