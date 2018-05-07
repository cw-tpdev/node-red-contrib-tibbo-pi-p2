module.exports = function (RED) {
    "use strict";

    // RTC and NVRAM with backup #42

    var TpCommon = require('./tpCommon');

    function TP_42Node(config) {
        RED.nodes.createNode(this, config);

        // config
        var node = this;
        this.config = config;

        // common
        var tc = new TpCommon("tp42", node);

        // Launch python
        tc.execPy([config.tpSlot]);

        // On Node Input
        tc.onInput(function (msg) {

            return msg.payload;
        });

        // On Node Output
        tc.onOutput(function (msg, payload) {

            msg.payload = payload;
            node.send(msg);

        });

    }
    RED.nodes.registerType("Tibbit-42", TP_42Node);

    function TP_42_OutNode(config) {
        RED.nodes.createNode(this, config);

        // config
        var node = this;
        this.config = config;

        // common
        var tc = new TpCommon("tp42_out", node);

        // Launch python
        tc.execPy([config.tpSlot, config.host]);

        // On Node Input
        tc.onInput(function (msg) {

            return msg.payload;
        });

        // On Node Output
        tc.onOutput();

    }
    RED.nodes.registerType("Tibbit-42 out", TP_42_OutNode);
}

