
from lib.tcpClient import TcpClient
import tpUtils
import sys


class Tp00_3:
    """
    #00_3 Two direct I/O lines, +5V power, ground
    """

    def __init__(self, slot, comm, host=None):
        """
        コンストラクタ
        """
        self.slot = slot
        self.comm = comm
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


if __name__ == '__main__':

    argvs = sys.argv
    if (len(argvs) <= 2):
        tpUtils.stderr('Need argv! [1]: slot [2]: communication')
        sys.exit(0)

    try:
        slot = argvs[1]
        comm = argvs[2]
        host = None
        if (len(argvs) > 3):
            host = argvs[3]
        tp00_3 = Tp00_3(slot, comm, host)
        tp00_3.start()
    except Exception as e:
        tpUtils.stderr(str(e.args))
        sys.exit(0)

    while True:
        try:
            data = input()
            recv_data = tp00_3.send(data)
            tpUtils.nodeOut(recv_data.decode('utf-8'))
        except KeyboardInterrupt:
            sys.exit(0)
        except Exception as e:
            tpUtils.stderr(str(e.args))
