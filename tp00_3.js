module.exports = function (RED) {
    "use strict";

    // #00_3 Two direct I/O lines, +5V power, ground

    var TpCommon = require('./tpCommon');

    function TP_00_3Node(config) {
        RED.nodes.createNode(this, config);

        // config
        var node = this;
        this.config = config;

        // common 
        var tc = new TpCommon("tp00_3", node);

        // Launch python
        tc.execPy([config.tpSlot, config.communication, config.host]);

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
    RED.nodes.registerType("Tibbit-00_3", TP_00_3Node);

    function TP_00_3_InNode(config) {
        RED.nodes.createNode(this, config);

        // config
        var node = this;
        this.config = config;

        // common
        var tc = new TpCommon("tp00_3_in", node);

        // Launch python
        tc.execPy([config.tpSlot, config.communication, config.host]);

        // On Node Output
        tc.onOutput(function (msg, payload) {

            msg.payload = payload;
            node.send(msg);

        });

    }
    RED.nodes.registerType("Tibbit-00_3 in", TP_00_3_InNode);
}

