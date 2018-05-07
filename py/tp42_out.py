from datetime import datetime

from lib.tcpClient import TcpClient
import tpUtils
import sys
import json
from constant import *


class Tp42_out:
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

    def convert_node_to_python_w_1(self, msg):
        """
        ミリ秒（テキスト）をSPI通信フォーマットに変換
        [
        {"add" : "0x86", "v" : ["0x18"]},
        {"add" : "0x85", "v" : ["0x02"]},
        {"add" : "0x84", "v" : ["0x22"]},
        {"add" : "0x82", "v" : ["0x14"]},
        {"add" : "0x81", "v" : ["0x43"]},
        {"add" : "0x80", "v" : ["0x30"]}
        ]
        """

        '''
        WRITE = 0x80
        ADDR_YEAR = 0x06
        ADDR_MONTH = 0x05
        ADDR_DAY = 0x04
        ADDR_HOUR = 0x02
        ADDR_MINUTE = 0x01
        ADDR_SEC = 0x00

        ### TODO 時差部分について考慮なし
        ### どのような形でもらうか一度検討してから
        dt = datetime.now()

        send = '['
        # 年 
        addr = ADDR_YEAR | WRITE
        value = tpUtils.dec_to_bcd(dt.year-2000)
        send += '{"add" : "%s", "v" : ["%s"]}' % (tpUtils.hex_z_fill(addr),tpUtils.hex_z_fill(value)) + ','
        # 月 
        addr = ADDR_MONTH | WRITE
        value = tpUtils.dec_to_bcd(dt.month)
        send += '{"add" : "%s", "v" : ["%s"]}' % (tpUtils.hex_z_fill(addr),tpUtils.hex_z_fill(value)) + ','
        # 日 
        addr = ADDR_DAY | WRITE
        value = tpUtils.dec_to_bcd(dt.day)
        send += '{"add" : "%s", "v" : ["%s"]}' % (tpUtils.hex_z_fill(addr),tpUtils.hex_z_fill(value)) + ','
        # 時 
        addr = ADDR_HOUR | WRITE
        value = tpUtils.dec_to_bcd(dt.hour)
        send += '{"add" : "%s", "v" : ["%s"]}' % (tpUtils.hex_z_fill(addr),tpUtils.hex_z_fill(value)) + ','
        # 分 
        addr = ADDR_MINUTE | WRITE
        value = tpUtils.dec_to_bcd(dt.minute)
        send += '{"add" : "%s", "v" : ["%s"]}' % (tpUtils.hex_z_fill(addr),tpUtils.hex_z_fill(value)) + ','
        # 秒 
        addr = ADDR_SEC | WRITE
        value = tpUtils.dec_to_bcd(dt.second)
        send += '{"add" : "%s", "v" : ["%s"]}' % (tpUtils.hex_z_fill(addr),tpUtils.hex_z_fill(value))

        send += ']'

        return send
        '''

    def get_data(self, msg):
        """
        ミリ秒（テキスト）をSPI通信フォーマットに変換
        [
        {"add" : "0x86", "v" : ["0x18"]},
        {"add" : "0x85", "v" : ["0x02"]},
        {"add" : "0x84", "v" : ["0x22"]},
        {"add" : "0x82", "v" : ["0x14"]},
        {"add" : "0x81", "v" : ["0x43"]},
        {"add" : "0x80", "v" : ["0x30"]}
        ]
        """

        WRITE = 0x80
        ADDR_YEAR = 0x06
        ADDR_MONTH = 0x05
        ADDR_DAY = 0x04
        ADDR_HOUR = 0x02
        ADDR_MINUTE = 0x01
        ADDR_SEC = 0x00

        # TODO 時差部分について考慮なし
        #dt = datetime.now()

        msg = msg.replace('"', '')

        send_data = []
        # 年
        addr = ADDR_YEAR | WRITE
        send_data.append({"add": addr, "v": [tpUtils.dec_to_bcd(int(msg[2:4]))]})
        # 月
        addr = ADDR_MONTH | WRITE
        send_data.append({"add": addr, "v": [tpUtils.dec_to_bcd(int(msg[5:7]))]})
        # 日
        addr = ADDR_DAY | WRITE
        send_data.append({"add": addr, "v": [tpUtils.dec_to_bcd(int(msg[8:10]))]})
        # 時
        addr = ADDR_HOUR | WRITE
        send_data.append(
            {"add": addr, "v": [tpUtils.dec_to_bcd(int(msg[11:13]))]})
        # 分
        addr = ADDR_MINUTE | WRITE
        send_data.append(
            {"add": addr, "v": [tpUtils.dec_to_bcd(int(msg[14:16]))]})
        # 秒
        addr = ADDR_SEC | WRITE
        send_data.append(
            {"add": addr, "v": [tpUtils.dec_to_bcd(int(msg[17:19]))]})

        # print(json.dumps(send_data))
        self.send(json.dumps(send_data))

        #print("send finish")
        '''
        send = '['
        # 年 
        addr = ADDR_YEAR | WRITE
        send += '{"add" : "%s", "v" : ["0x%s"]}' % (tpUtils.hex_z_fill(addr),msg[2:4]) + ','
        # 月 
        addr = ADDR_MONTH | WRITE
        send += '{"add" : "%s", "v" : ["0x%s"]}' % (tpUtils.hex_z_fill(addr),msg[5:7]) + ','
        # 日 
        addr = ADDR_DAY | WRITE
        send += '{"add" : "%s", "v" : ["0x%s"]}' % (tpUtils.hex_z_fill(addr),msg[8:10]) + ','
        # 時 
        addr = ADDR_HOUR | WRITE
        send += '{"add" : "%s", "v" : ["0x%s"]}' % (tpUtils.hex_z_fill(addr),msg[11:13]) + ','
        # 分 
        addr = ADDR_MINUTE | WRITE
        send += '{"add" : "%s", "v" : ["0x%s"]}' % (tpUtils.hex_z_fill(addr),msg[14:16]) + ','
        # 秒 
        addr = ADDR_SEC | WRITE
        send += '{"add" : "%s", "v" : ["0x%s"]}' % (tpUtils.hex_z_fill(addr),msg[17:19]) 

        send += ']'
        '''
        # print(send)
        # return send


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
        tp42_out = Tp42_out(slot, host)

        tp42_out.start()
    except Exception as e:
        tpUtils.stderr(str(e.args))
        sys.exit(0)

    while True:
        try:
            data = input()

            # TODO 文字列配列で受領 2018/10/11 12:13:14
            tp42_out.get_data(data)
        except KeyboardInterrupt:
            sys.exit(0)
        except Exception as e:
            tpUtils.stderr(str(e.args))
