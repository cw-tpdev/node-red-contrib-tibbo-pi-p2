module.exports = function (RED) {
    "use strict";

    // TP Button

    var TpCommon = require('./tpCommon');

    function TPC_ButtonInNode(config) {
        RED.nodes.createNode(this, config);

        // config
        var node = this;
        this.config = config;

        // common
        var tc = new TpCommon("tpcButton", node);

        // Launch python
        tc.execPy([config.host]);

        // On Node Output
        tc.onOutput(function (msg, payload) {

            // to JSON
            msg.payload = JSON.parse(payload);
            node.send(msg);

        });

    }
    RED.nodes.registerType("tp-button in", TPC_ButtonInNode);
}

