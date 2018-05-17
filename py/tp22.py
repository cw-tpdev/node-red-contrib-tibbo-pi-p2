
import sys
from tp00 import Tp00
import tpUtils
from constant import *
import json
import time


class Tp22:
    """
    #22 RTD Temperature Meter
    """

    def __init__(self, slot, host=None):
        """
        コンストラクタ
        """

        # TODO 00ではないので修正

        self.slot = slot
        self.comm = I2C
        self.host = host

        # アドレス
        self.i2c_addr = 0x0D

        # tp00
        self.tp00 = Tp00(self.slot, self.comm, self.host)
        self.tp00.start()

    def get_data(self):
        """
        データを取得します。
        """
        # send_data = []
        # send_data.append(
        #     {"act": "w", "add": self.i2c_addr, "cmd": 0x80, "v": [0x00]})
        # self.tp00.send(json.dumps(send_data))
        # time.sleep(0.3)

        # send_data = []
        # send_data.append(
        #     {"act": "w", "add": self.i2c_addr, "cmd": 0x85, "v": [0x00]})
        # self.tp00.send(json.dumps(send_data))
        # time.sleep(0.3)

        # send_data = []
        # send_data.append(
        #     {"act": "w", "add": self.i2c_addr, "cmd": 0x86, "v": [0x00]})
        # self.tp00.send(json.dumps(send_data))
        # time.sleep(0.3)

        # send_data = []
        # send_data.append(
        #     {"act": "w", "add": self.i2c_addr, "cmd": 0x83, "v": [0xFF]})
        # self.tp00.send(json.dumps(send_data))
        # time.sleep(0.3)

        # send_data = []
        # send_data.append(
        #     {"act": "w", "add": self.i2c_addr, "cmd": 0x84, "v": [0xFF]})
        # self.tp00.send(json.dumps(send_data))
        # time.sleep(0.3)

        # # 設定書き込み
        # send_data = []
        # send_data.append(
        #     {"act": "w", "add": self.i2c_addr, "cmd": 0x80, "v": [0xC2]})
        # self.tp00.send(json.dumps(send_data))
        # time.sleep(0.3)

        # 以下読み込んで見る
        send_data = []
        # send_data.append(
        #     {"act": "w", "add": self.i2c_addr, "cmd": 0x80, "v": [0x1A]})
        # self.tp00.send(json.dumps(send_data))
        # time.sleep(0.3)

        # send_data = []
        # send_data.append(
        #     {"act": "w", "add": self.i2c_addr, "cmd": 0x80, "v": [0x3]})
        # self.tp00.send(json.dumps(send_data))
        # time.sleep(0.3)

        # send_data = []
        # send_data.append(
        #     {"act": "w", "add": self.i2c_addr, "cmd": 0x80, "v": [0x1B]})
        # self.tp00.send(json.dumps(send_data))
        # time.sleep(0.3)

        #------------------------
        # バージョンをだしてみる ここから
        #------------------------

        # バージョン取るために0x3を書き込み
        send_data = []
        send_data.append(
            {"act": "w", "add": self.i2c_addr, "cmd": 0x80, "v": [0x3]})
        #self.tp00.send(json.dumps(send_data))
        #time.sleep(0.05)

        # 読み込み
        #send_data = []
        send_data.append(
            {"act": "r", "add": self.i2c_addr, "cmd": 0x80, "len": 16})
        _result = self.tp00.send(json.dumps(send_data))
        result_data = json.loads(_result.decode())
        result_data = result_data[0]

        ver = ''
        for verchr in result_data:
            ver = ver + chr(verchr)

        print(result_data)
        print(ver)
        time.sleep(0.3)

        #------------------------
        # バージョンをだしてみる ここまで
        #------------------------

        send_data = []
        send_data.append(
            {"act": "w", "add": self.i2c_addr, "cmd": 0x80, "v": [0x1]})
        self.tp00.send(json.dumps(send_data))
        time.sleep(0.5)

        # send_data = []
        # send_data.append(
        #     {"act": "w", "add": self.i2c_addr, "cmd": 0x80, "v": []})
        # self.tp00.send(json.dumps(send_data))
        # time.sleep(0.5)

        # 読み込み
        send_data = []
        send_data.append(
            {"act": "r", "add": self.i2c_addr, "cmd": 0x80, "len": 1})
        _result = self.tp00.send(json.dumps(send_data))
        result_data = json.loads(_result.decode())
        result_data = result_data[0]
        print(result_data)

        send_data = []
        send_data.append(
            {"act": "r", "add": 0xff, "cmd": 0x80, "len": 5})
        _result = self.tp00.send(json.dumps(send_data))
        result_data = json.loads(_result.decode())
        result_data = result_data[0]
        print(result_data)

        # TODO ここでLOW待ち

        # 読み込み
        # send_data = []
        # send_data.append(
        #     {"act": "r", "add": self.i2c_addr, "cmd": 0x80, "len": 1}) # 8 + 2くらい？
        # _result = self.tp00.send(json.dumps(send_data))
        # result_data = json.loads(_result.decode())
        # result_data = result_data[0]
        # print(result_data)


if __name__ == '__main__':

    argvs = sys.argv
    if (len(argvs) <= 1):
        tpUtils.stderr('Need argv! [1]: slot')
        sys.exit(0)

    try:
        slot = argvs[1]
        host = None
        if (len(argvs) > 2):
            host = argvs[2]
        tp22 = Tp22(slot, host)
    except Exception as e:
        tpUtils.stderr(str(e.args))
        sys.exit(0)

    while True:
        try:
            data = input()
            recv_data = tp22.get_data()
            tpUtils.nodeOut(recv_data)
        except KeyboardInterrupt:
            sys.exit(0)
        except Exception as e:
            tpUtils.stderr(str(e.args))
