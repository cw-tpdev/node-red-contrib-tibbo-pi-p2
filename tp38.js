module.exports = function (RED) {
    "use strict";

    // #38 Pushbutton

    var TpCommon = require('./tpCommon');

    function TP_38_InNode(config) {
        RED.nodes.createNode(this, config);

        // config
        var node = this;
        this.config = config;

        // common
        var tc = new TpCommon("tp38_in", node);

        // Launch python
        tc.execPy([config.tpSlot, config.host]);

        // On Node Output
        tc.onOutput(function (msg, payload) {

            msg.payload = parseInt(payload);
            node.send(msg);

        });

    }
    RED.nodes.registerType("Tibbit-38 in", TP_38_InNode);
}

