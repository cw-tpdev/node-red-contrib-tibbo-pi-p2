import socket
import select
import sys
import tpUtils
import _thread as thread
import time


class TcpServer:
    """
    TCP Server
    """

    def __init__(self, callback_recv, info):
        """
        コンストラクタ

        callback_recv: 受信時のコールバック関数
        info: 受信時に渡す設定情報など
        """

        # バッファサイズ
        self.bufsize = 1024
        # 送信区切り文字
        self.buf_split = b"-TP-EOT-"

        # 受信時のイベント
        self.callback_recv = callback_recv
        self.info = info

    def recv(self, host, port):
        """
        受信イベント
        """

        while True:

            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            self.sock.bind((host, port))
            self.sock.listen(0)

            tpUtils.stdout("Server listening on %s %d" % (host, (port)))

            # 接続待機
            self.clientsock, client_address = self.sock.accept()

            # 一つのクライアントのみ接続可能にするため閉じる
            self.sock.close()

            while True:

                try:
                    # 受信
                    rcvmsg = self.clientsock.recv(self.bufsize)
                    #tpUtils.stdout('Received -> %s' % (rcvmsg))
                except Exception:
                    # コネクション切断等のエラー時はコネクションの再接続を行う。
                    break

                # 切断時
                if rcvmsg == b'':
                    # コネクション切断時は再接続を行う。
                    break

                if self.callback_recv != None:

                    # コールバック
                    send_data = self.handler(
                        self.callback_recv, self.info, rcvmsg)

                    try:
                       # メッセージを返します
                        if (send_data is None or send_data == ''):
                            # Noneという文字列を返却
                            self.clientsock.send('None'.encode())
                        elif type(send_data) == str:
                            # 文字
                            self.clientsock.send(send_data.encode())
                        else:
                            # bytes
                            self.clientsock.send(send_data)
                    except Exception:
                        # コネクション切断等のエラー時はコネクションの再接続を行う。
                        break

            # クローズ
            self.clientsock.close()
            # コネクション切断時は再接続を行う。
            tpUtils.stdout("Socket erroor reconnect %s %d" % (host, port))

    def send(self, send_data):
        """
        送信処理
        """
        if hasattr(self, 'sock') == False or self.sock is None:
            return
        if hasattr(self, 'clientsock') == False or self.clientsock is None:
            return

        try:
            # メッセージを返します
            if type(send_data) == str:
                self.clientsock.send(send_data.encode() + self.buf_split)
            else:
                self.clientsock.send(send_data + self.buf_split)
        except ConnectionAbortedError:
            # クライアントが切断した場合
            return

    def handler(self, func, *args):
        """
        ハンドラー
        """
        return func(*args)
