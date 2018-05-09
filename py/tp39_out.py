
import sys
from tp00_3 import Tp00_3
import json
from constant import *
import tpUtils


class Tp39_out:
    """
    #39 LED
    """

    def __init__(self, slot, host=None):
        """
        コンストラクタ
        """
        self.slot = slot
        self.comm = GPIO
        self.host = host

        # tp00_3経由にて通信
        self.tp00_3 = Tp00_3(self.slot, self.comm, self.host)
        self.tp00_3.start()

    def send(self, data):
        """
        値を送信します。
        """
        # on/offは反転
        if tpUtils.to_num(data) == 0:
            val = 1
        else:
            val = 0
        send_data = []
        tmp_data = {}
        tmp_data["line"] = 'A'
        tmp_data["v"] = val
        send_data.append(tmp_data)

        # tp00_3経由
        # Node-REDへは返却しない
        self.tp00_3.send(json.dumps(send_data))


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
        tp39_out = Tp39_out(slot, host)
    except Exception as e:
        tpUtils.stderr(str(e.args))
        sys.exit(0)

    while True:
        try:
            data = input()
            tp39_out.send(data)
            # 戻り値なし
        except KeyboardInterrupt:
            sys.exit(0)
        except Exception as e:
            tpUtils.stderr(str(e.args))
