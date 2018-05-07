module.exports = function (RED) {
    "use strict";

    // Two isolated inputs #04-1

    var TpCommon = require('./tpCommon');

    function TP_04_1_OutNode(config) {
        RED.nodes.createNode(this, config);

        // config
        var node = this;
        this.config = config;

        // common
        var tc = new TpCommon("tp04_1_out", node);

        // Launch python
        tc.execPy([config.tpSlot, config.host]);

        // On Node Input
        tc.onInput(function (msg) {

            return msg.payload;
        });

        // On Node Output
        tc.onOutput();
    }
    RED.nodes.registerType("Tibbit-04_1 out", TP_04_1_OutNode);
}
