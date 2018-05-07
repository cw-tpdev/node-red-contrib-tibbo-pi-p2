from datetime import datetime

from lib.tcpClient import TcpClient
import tpUtils
import sys
import json
from constant import *


class Tp42:
    """
    #42 RTC and NVRAM with backup
    """

    def __init__(self, slot, host=None):
        """
        コンストラクタ
        """
        self.slot = slot
        self.comm = SPI
        self.host = host

    def start(self):
        """
        開始処理
        TCPサーバーに接続します。
        """
        self.tcp_client = TcpClient()
        self.tcp_client.connect_by_conf(self.host, self.slot, self.comm)

    def send(self, msg):
        """
        データを送信します。
        """
        recv_data = self.tcp_client.send(msg)
        return recv_data

    def get_data(self):
        """
        ミリ秒（テキスト）をSPI通信フォーマットに変換
        [
        {"add" : "0x06", "v" : [0x00]},
        {"add" : "0x05", "v" : [0x00]},
        {"add" : "0x04", "v" : [0x00]},
        {"add" : "0x02", "v" : [0x00]},
        {"add" : "0x01", "v" : [0x00]},
        {"add" : "0x00", "v" : [0x00]}
        ]
        """

        READ = 0x00
        ADDR_YEAR = 0x06
        ADDR_MONTH = 0x05
        ADDR_DAY = 0x04
        ADDR_HOUR = 0x02
        ADDR_MINUTE = 0x01
        ADDR_SEC = 0x00

        #msg = msg.replace('"','')

        send_data = []
        # 年
        addr = ADDR_YEAR | READ
        send_data.append({"add": addr, "v": [0x00]})
        # 月
        addr = ADDR_MONTH | READ
        send_data.append({"add": addr, "v": [0x00]})
        # 日
        addr = ADDR_DAY | READ
        send_data.append({"add": addr, "v": [0x00]})
        # 時
        addr = ADDR_HOUR | READ
        send_data.append({"add": addr, "v": [0x00]})
        # 分
        addr = ADDR_MINUTE | READ
        send_data.append({"add": addr, "v": [0x00]})
        # 秒
        addr = ADDR_SEC | READ
        send_data.append({"add": addr, "v": [0x00]})

        recv = self.send(json.dumps(send_data))
        return self.convert(recv)

        '''
        send = '['
        # 年 
        addr = ADDR_YEAR | READ
        send += '{"add" : "%s", "v" : [0x00]}' % (tpUtils.hex_z_fill(addr)) + ','
        # 月 
        addr = ADDR_MONTH | READ
        send += '{"add" : "%s", "v" : [0x00]}' % (tpUtils.hex_z_fill(addr)) + ','
        # 日 
        addr = ADDR_DAY | READ
        send += '{"add" : "%s", "v" : [0x00]}' % (tpUtils.hex_z_fill(addr)) + ','
        # 時 
        addr = ADDR_HOUR | READ
        send += '{"add" : "%s", "v" : [0x00]}' % (tpUtils.hex_z_fill(addr)) + ','
        # 分 
        addr = ADDR_MINUTE | READ
        send += '{"add" : "%s", "v" : [0x00]}' % (tpUtils.hex_z_fill(addr)) + ','
        # 秒 
        addr = ADDR_SEC | READ
        send += '{"add" : "%s", "v" : [0x00]}' % (tpUtils.hex_z_fill(addr)) + ','

        send += ']'
        '''

        '''
        #print(send)
        return recv
        '''

    def convert(self, msg):
        """
        RTCから取得した値を返却値に変更
        """

        # TODO 取得した値を部分的にマスクする必要があるかも
        buff = json.loads(msg)

        # 年
        year = 2000+tpUtils.bcd_to_dec(buff[0][0])
        # 月
        month = tpUtils.bcd_to_dec(buff[1][0])
        # 日
        day = tpUtils.bcd_to_dec(buff[2][0])
        # 時
        hour = tpUtils.bcd_to_dec(buff[3][0])
        # 分
        minute = tpUtils.bcd_to_dec(buff[4][0])
        # 秒
        sec = tpUtils.bcd_to_dec(buff[5][0])

        dt = datetime(year, month, day, hour, minute, sec)

        # print(str(dt))
        return str(dt)


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
        tp42 = Tp42(slot, host)

        tp42.start()
    except Exception as e:
        tpUtils.stderr(str(e.args))
        sys.exit(0)

    while True:
        try:
            data = input()
            recv = tp42.get_data()
            tpUtils.nodeOut(recv)
        except KeyboardInterrupt:
            sys.exit(0)
        except Exception as e:
            tpUtils.stderr(str(e.args))
