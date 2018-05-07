module.exports = function (RED) {
    "use strict";

    // #01 Four-line RS232 port

    var TpCommon = require('./tpCommon');

    function TP_01Node(config) {
        RED.nodes.createNode(this, config);

        // config
        var node = this;
        this.config = config;

        // cpmmon
        var tc = new TpCommon("tp01", node);

        // Launch python
        tc.execPy([config.tpSlot, config.host]);

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
    RED.nodes.registerType("Tibbit-01", TP_01Node);

    function TP_01_InNode(config) {
        RED.nodes.createNode(this, config);

        // config
        var node = this;
        this.config = config;

        // common
        var tc = new TpCommon("tp01_in", node);

        // Launch python
        tc.execPy([config.tpSlot, config.host]);

        // On Node Output
        tc.onOutput(function (msg, payload) {

            msg.payload = payload;
            node.send(msg);

        });
    }
    RED.nodes.registerType("Tibbit-01 in", TP_01_InNode);
}

