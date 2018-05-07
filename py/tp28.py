
import sys
from tp00_3 import Tp00_3
import tpUtils
from constant import *
import json
import time


class Tp28:
    """
    #28 Ambient light sensor
    """

    def __init__(self, slot, host=None):
        """
        コンストラクタ
        """

        self.slot = slot
        self.comm = I2C
        self.host = host

        # アドレス
        self.i2c_addr = 0x23

        # tp00_3
        self.tp00_3 = Tp00_3(self.slot, self.comm, self.host)
        self.tp00_3.start()

    def get_data(self):
        """
        データを取得します。
        """
        send_data = []
        # Power Down
        send_data.append(
            {"act": "w", "add": self.i2c_addr, "cmd": 0x00, "v": [0x00]})
        # Power ON
        send_data.append(
            {"act": "w", "add": self.i2c_addr, "cmd": 0x00, "v": [0x01]})
        # Low-Res
        send_data.append(
            {"act": "w", "add": self.i2c_addr, "cmd": 0x00, "v": [0x13]})
        self.tp00_3.send(json.dumps(send_data))

        # wait
        time.sleep(0.02)

        # get data
        send_data = []
        send_data.append(
            {"act": "r", "add": self.i2c_addr, "cmd": 0x00, "len": 2})
        _result = self.tp00_3.send(json.dumps(send_data))

        # jsonで受け取る
        result_data = json.loads(_result.decode())
        result = result_data[0]

        # TODO iphoneの照度計と値が合っているかチェックしたい。

        # 値の取得
        val = (result[0] * 256 + result[1]) / 1.2

        send_data = []
        # Power Down
        send_data.append(
            {"act": "w", "add": self.i2c_addr, "cmd": 0x00, "v": [0x00]})
        self.tp00_3.send(json.dumps(send_data))

        # 小数点第一位まで取得
        return round(val, 1)


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
        tp28 = Tp28(slot, host)
    except Exception as e:
        tpUtils.stderr(str(e.args))
        sys.exit(0)

    while True:
        try:
            data = input()
            recv_data = tp28.get_data()
            tpUtils.nodeOut(recv_data)
        except KeyboardInterrupt:
            sys.exit(0)
        except Exception as e:
            tpUtils.stderr(str(e.args))
