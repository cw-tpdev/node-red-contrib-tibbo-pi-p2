module.exports = function (RED) {
    "use strict";

    // tp initialize

    var fs = require('fs');
    var os = require('os');

    var TpCommon = require('./tpCommon');
    var flowJsonDir = RED.settings.userDir;
    var spawn = require('child_process').spawn;
    var outputFile = __dirname + '/config/config.json'
    var nodeName = 'tp-initialize';

    // Node-Red起動時に、flows.jsonの中身を確認し、このノードを先頭に移動する(デプロイ時は対応しない)
    moveNodeFromFlowsJson();

    function TP_InitializeNode(config) {
        RED.nodes.createNode(this, config);
        var node = this;

        // config
        this.make = config.make;

        // start
        node.log("start");

        // stopped
        node.status({ fill: "grey", shape: "ring", text: "initialize.status.stopped" });

        try {

            // create config.json
            if (this.make) {
                createTibboPiSettingsFile(outputFile, node);
                node.log("created settings file!");
            }

        } catch (err) {
            // fail
            node.warn("error : " + err);
            return
        }

        // common
        var tc = new TpCommon("tpConnect", node);

        // Launch python
        node.child = spawn(tc.cmdPy, ["-u", tc.getPyPath("tpConnect"), outputFile]);

        // Python error
        node.child.stderr.on('data', function (data) {
            node.error("err: " + data);
        });

        // python stdout
        node.child.stdout.on('data', function (data) {

            var d = data.toString().trim().split("\n");
            for (var i = 0; i < d.length; i++) {

                if (d[i].indexOf('Successfully connected!') === 0) {
                    // started
                    node.status({ fill: "green", shape: "dot", text: "initialize.status.started" });
                } else {
                    node.log("data: " + d[i]);
                }
            }

        });

        // On Close
        node.on('close', function (done) {

            node.log("close");

            // stopped
            node.status({ fill: "grey", shape: "ring", text: "initialize.status.stopped" });

            if (node.child != null) {
                node.child.kill('SIGINT');
                node.child = null;
                done();
            } else {
                done();
            }

        });
    }
    RED.nodes.registerType(nodeName, TP_InitializeNode);

    /* TibboPi付属機能 */
    function readTibboPiCtrl(slotInfo, opJson, node) {

        var baseTCPPort = 13000;

        // slot
        var slot = 'S00';

        // 通信
        var comm = slotInfo.communication;

        // host
        var host = slotInfo.host;
        if (!host || !host.trim()) {
            host = 'localhost';
        }

        // 無効の場合は設定は出力しない
        var connectedStatus = slotInfo.connectedStatus;
        if (connectedStatus == 'disabled') {
            return opJson;
        }

        if (!slot || !comm || !slot.trim() || !comm.trim()) {
            return opJson;
        }

        // 既に設定済みのホスト・スロット番号・通信方式をチェック
        var match = opJson.filter(function (item, index) {
            if (item.host == host && item.slot == slot && item.comm == comm) return true;
        });
        if (match.length > 0) {
            node.error("err: There are multiple nodes of the same setting. host:" + host + " type:" + comm);
            return opJson;
        }

        // tcpポートの設定
        var port = baseTCPPort;

        if (comm == 'TP_BUZZER') {
            port = port + 11;
        } else if (comm == 'TP_LED') {
            port = port + 21;
        } else if (comm == 'TP_BUTTON') {
            port = port + 31;
        }

        // setteings
        var setteings = {};

        var tmpJson = {
            "host": host,
            "slot": slot,
            "comm": comm,
            "settings": setteings
        };

        if (slotInfo.outputOnly) {
            // 出力のみ(イベント)
            tmpJson["portEvent"] = port + 1;
        } else {
            // イン・インアウトノード
            tmpJson["port"] = port;
        }

        opJson.push(tmpJson);

        return opJson;
    }

    /* スロット機能 */
    function readSlotCtrl(slotInfo, opJson, node) {

        var baseTCPPort = 14000;

        // slot
        var slot = slotInfo.tpSlot;

        // 通信
        var comm = slotInfo.communication;

        // host
        var host = slotInfo.host;
        if (!host || !host.trim()) {
            host = 'localhost';
        }

        // 無効の場合は設定は出力しない
        var connectedStatus = slotInfo.connectedStatus;
        if (connectedStatus == 'disabled') {
            return opJson;
        }

        if (!slot || !comm || !slot.trim() || !comm.trim()) {
            return opJson;
        }

        // tcpポートの設定(base+Slot+comm)
        var port = baseTCPPort;
        port = port + (Number(slot.slice(1)) * 10);

        if (comm == 'GPIO') {
            port = port + 1;
        } else if (comm == 'I2C') {
            port = port + 3;
        } else if (comm == 'SPI') {
            port = port + 5;
        } else if (comm == 'Serial') {
            port = port + 7;
        }

        // GPIOの情報取得
        if (comm == 'GPIO') {
            // ピン情報
            var p1 = slotInfo.pinA;
            var p2 = slotInfo.pinB;
            var p3 = slotInfo.pinC;
            var p4 = slotInfo.pinD;

            var setteings = {};
            var pin = [];

            if (p1 && p1 != 'other') {
                pin.push({ "name": "A", "status": p1 });
            }
            if (p2 && p2 != 'other') {
                pin.push({ "name": "B", "status": p2 });
            }
            if (p3 && p3 != 'other') {
                pin.push({ "name": "C", "status": p3 });
            }
            if (p4 && p4 != 'other') {
                pin.push({ "name": "D", "status": p4 });
            }
        }

        // I2Cの情報取得
        if (comm == 'I2C') {
            // ピン情報
            var setteings = {};
            var pin = [];
            pin.push({ "name": "A", "status": "SCL" });
            pin.push({ "name": "B", "status": "SDA" });
        }

        // SPIの情報取得
        if (comm == 'SPI') {
            // ピン情報
            var speed = slotInfo.spiSpeed;
            var mode = slotInfo.spiMode;
            var endian = slotInfo.spiEndian;

            var setteings = { "speed": speed, "mode": mode, "endian": endian };
            var pin = [];
            pin.push({ "name": "A", "status": "CS" });
            pin.push({ "name": "B", "status": "SCLK" });
            pin.push({ "name": "C", "status": "MOSI" });
            pin.push({ "name": "D", "status": "MISO" });
        }

        // Serialの情報取得
        if (comm == 'Serial') {

            // ピン情報
            var hardwareFlow = slotInfo.hardwareFlow;
            var baudRate = slotInfo.seriBaudRate;
            var dataBits = slotInfo.seriDataBits;
            var parity = slotInfo.seriParity;
            var stopBits = slotInfo.seriStopBits;
            var splitInput = slotInfo.seriSplitInput;
            var onTheCharactor = slotInfo.seriOnTheCharactor;
            var afterATimeoutOf = slotInfo.seriAfterATimeoutOf;
            var intoFixedLengthOf = slotInfo.seriIntoFixedLengthOf;

            var setteings = {
                "hardwareFlow": hardwareFlow,
                "baudRate": baudRate,
                "dataBits": dataBits,
                "parity": parity,
                "stopBits": stopBits,
                "splitInput": splitInput,
                "onTheCharactor": onTheCharactor,
                "afterATimeoutOf": afterATimeoutOf,
                "intoFixedLengthOf": intoFixedLengthOf
            };

            var pin = [];
            if (slotInfo.pinA) {
                pin.push({ "name": "A", "status": slotInfo.pinA });
            }
            if (slotInfo.pinB) {
                pin.push({ "name": "B", "status": slotInfo.pinB });
            }
            if (slotInfo.pinC) {
                pin.push({ "name": "C", "status": slotInfo.pinC });
            }
            if (slotInfo.pinD) {
                pin.push({ "name": "D", "status": slotInfo.pinD });
            }
        }

        // 同じスロットで、ラインに別な設定がないかチェック
        var match = opJson.filter(function (item, index) {
            if (item.host == host && item.slot == slot) return true;
        });
        if (match.length > 0) {
            for (let idx in match) {
                for (var idxNewPin in pin) {
                    // 存在チェック
                    for (var idxPin in match[idx]["pin"]) {
                        if (match[idx]["pin"][idxPin]['name'] == pin[idxNewPin]['name']) {
                            // 同じピンに対して、別なのpinの設定は不可
                            if (match[idx]["pin"][idxPin]['status'] != pin[idxNewPin]['status']) {
                                node.error("err: There is another setting on the same line. host:" + host + " slot:" + slot + " line:" + match[idx]["pin"][idxPin]['name']);
                                return opJson;
                            }
                        }
                    }
                }
            }
        }

        // 既に設定済みのホスト・スロット番号・通信方式をチェック
        var match = opJson.filter(function (item, index) {
            if (item.host == host && item.slot == slot && item.comm == comm) return true;
        });

        if (match.length == 0) {

            var tmpJson = {
                "host": host,
                "slot": slot,
                "comm": comm,
                "settings": setteings,
                "pin": pin
            };

            if (slotInfo.outputOnly) {
                // 出力のみ(イベント)
                tmpJson["portEvent"] = port + 1;
            } else {
                // イン・インアウトノード
                tmpJson["port"] = port;
            }

            opJson.push(tmpJson);
        } else {

            // 既存の設定に追加
            for (let idx in match) {

                // ポートを追加
                if (slotInfo.outputOnly) {
                    if (match[idx]["portEvent"]) {
                        // 同じポートへの設定はNG
                        node.error("err: There are multiple nodes of the same setting. host:" + host + " slot:" + slot + " comm:" + comm);
                    }
                    // 出力のみ(イベント)
                    match[idx]["portEvent"] = port + 1;
                } else {
                    if (match[idx]["port"]) {
                        // 同じポートへの設定はNG
                        node.error("err: There are multiple nodes of the same setting. host:" + host + " slot:" + slot + " comm:" + comm);
                    }
                    // イン・インアウトノード
                    match[idx]["port"] = port;
                }

                // pinを追加
                for (var idxNewPin in pin) {
                    // 存在チェック
                    var isExist = false;
                    for (var idxPin in match[idx]["pin"]) {
                        if (match[idx]["pin"][idxPin]['name'] == pin[idxNewPin]['name']) {
                            isExist = true;
                            break;
                        }
                    }
                    if (!isExist) {
                        match[idx]["pin"].push(pin[idxNewPin]);
                    }
                }
            }
        }

        return opJson;
    }

    /* node-redのフローファイルからスロット情報取得 */
    function createTibboPiSettingsFile(outputFile, node) {

        // flowの取得
        var json = getFlowsJson();

        // tp Initializeの複数ノードチェック
        var initList = json.filter(function (item, index) {
            if (nodeName == item['type']) return true;
        });
        if (initList.length > 1) {
            node.error("err: There are multiple tp initialize.");
        }

        // スロット情報のみ抽出
        var sInfoList = json.filter(function (item, index) {
            if ('tpSlot' in item) return true;
        });

        var opJson = [];
        for (var i in sInfoList) {

            // 各ノード設定保存
            var slotInfo = sInfoList[i];
            // スロット情報の取得
            var slot = slotInfo.tpSlot;

            if (slot == 'S00') {
                // TibboPiのボタン、ブザー、LEDの設定
                opJson = readTibboPiCtrl(slotInfo, opJson, node);
            } else {
                // Slotの設定
                opJson = readSlotCtrl(slotInfo, opJson, node);
            }
        }

        // save
        fs.writeFileSync(outputFile, JSON.stringify(opJson, null, '    '));
    }

    /* flows.jsonの中身を取得 */
    function getFlowsJson() {

        // flowsパス取得
        var fileName = getFlowsPath();

        // flow.jsonファイル読込
        var json_body = fs.readFileSync(fileName, 'utf-8');
        return JSON.parse(json_body);

    }

    /* flows.jsonのパスを取得 */
    function getFlowsPath() {

        // flowFile名取得
        var flowFile = RED.settings.flowFile;

        // flowsパス取得
        var fileName = null;
        if (!flowFile) {
            var hostname = os.hostname();
            fileName = flowJsonDir + '/flows_' + hostname + '.json';
        } else {
            fileName = flowJsonDir + '/' + flowFile;
        }

        return fileName;
    }

    /* flows.jsonの中身を確認し、このノードを先頭に移動する */
    function moveNodeFromFlowsJson() {

        // flowsパス取得
        var fileName = getFlowsPath();

        // 中身を取得
        var json = getFlowsJson();

        // 並び替えが必要かチェック
        for (var i = 0; i < json.length; i++) {
            if (json[i]['type'] == nodeName) {
                // 不要
                return;
            } else if (('tpSlot' in json[i])) {
                // 並び替え
                break;
            }
        }

        // 並び替え
        var opJson = [];
        for (var i = 0; i < json.length; i++) {
            if (json[i]['type'] == nodeName) {
                opJson.push(json[i]);
            }
        }
        for (var i = 0; i < json.length; i++) {
            if (json[i]['type'] != nodeName) {
                opJson.push(json[i]);
            }
        }

        // save
        fs.writeFileSync(fileName, JSON.stringify(opJson));
    }
}
