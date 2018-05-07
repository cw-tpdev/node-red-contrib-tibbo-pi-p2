import sys
from tp00_3 import Tp00_3
import tpUtils
from constant import *
import json


class Tp30:
    """
    #30 Ambient humidity meter
    """

    def __init__(self, slot, host=None):
        """
        コンストラクタ
        """

        self.slot = slot
        self.comm = I2C
        self.host = host

        # アドレス
        self.i2c_addr = 0x27

        # tp00_3
        self.tp00_3 = Tp00_3(self.slot, self.comm, self.host)
        self.tp00_3.start()

    def get_data(self):
        """
        値を取得します。
        """
        send_data = []
        send_data.append(
            {"act": "r", "add": self.i2c_addr, "cmd": 0x00, "len": 4})
        _result = self.tp00_3.send(json.dumps(send_data))

        # jsonで受け取る
        result_data = json.loads(_result.decode())
        result = result_data[0]

        # TODO ソースのチェックと、湿度計・温度計での確認はしたい。

        # データから変換
        humd = ((result[0] & 0x3F) * 256 + result[1]) / 16383 * 100
        temp = (result[2] * 64 + (result[3] >> 2)) / 16383 * 165 - 40
        humd = round(humd, 1)
        temp = round(temp, 1)

        rtn = {}
        rtn['humd'] = humd
        rtn['temp'] = temp
        return rtn


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
        tp30 = Tp30(slot, host)
    except Exception as e:
        tpUtils.stderr(str(e.args))
        sys.exit(0)

    while True:
        try:
            data = input()
            recv_data = tp30.get_data()
            # jsonで取得する
            tpUtils.nodeOut(json.dumps(recv_data))
        except KeyboardInterrupt:
            sys.exit(0)
        except Exception as e:
            tpUtils.stderr(str(e.args))
