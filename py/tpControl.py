import time
import json
from constant import *
#from tpBoardInterface import TpBoardInterface
import tpUtils


class TpControl:
    """
    Tibbo-Pi制御を行います。
    """

    def __init__(self, settings, callback_send):
        """
        コンストラクタ

        settings：config.json(設定)
        callback_send：イベントドリブン用のコールバック関数
        """

        # 設定
        self.settings = settings

        # イベント発生用のコールバック関数をセット
        self.callback_send = callback_send

        # 基板用インターフェース準備
        #self.tp_inter = TpBoardInterface(settings, self.__send_data)

    def control(self, setting, rcv_msg):
        """
        制御を行います。

        setting: この制御に関する設定
        rcv_msg: 制御するための情報
        """
        if setting['comm'] == TP_BUZZER:
            #--------------
            # ブザー
            #--------------

            # Jsonでデータ取得
            data = json.loads(rcv_msg.decode())

            # 鳴らす時間
            time = data['time']
            # パターン
            pattern = data['ptn']

            # ブザーの制御を行う
            #self.tp_inter.rp_buzzer(time, pattern)

            # 戻り値は無し
            return

        elif setting['comm'] == TP_LED:
            #--------------
            # LED
            #--------------

            # Jsonでデータ取得
            data = json.loads(rcv_msg.decode())

            # LED番号
            no = data['no']
            # 値
            val = data['v']

            # LEDの制御を行う
            #self.tp_inter.rp_led(no, val)

            # 戻り値は無し
            return

        # 以下、通信方式により各制御を行う
        elif setting['comm'] == GPIO:
            #--------------
            # GPIO
            #--------------

            # 戻り値配列
            rtn = []

            # Jsonでデータ取得
            datas = json.loads(rcv_msg.decode())

            for data in datas:

                # ライン
                line = data['line']
                # 値
                # None もしくは''の場合は読み込み
                if 'v' in data:
                    val = data['v']
                else:
                    val = None

                # GPIOの処理を行う
                status = setting['pin'][tpUtils.line_str_to_int(
                    line) - 1]['status']
                if status == 'IN':
                    read_data = self.tp_inter.gpio_read(setting['slot'], line)
                    # 戻り値
                    rtn.append(read_data)
                elif status == 'OUT':
                    self.tp_inter.gpio_write(setting['slot'], line, val)

            # Jsonで返却
            return json.dumps(rtn)

        elif setting['comm'] == I2C:
            #--------------
            # I2c
            #--------------

            # 戻り値配列
            rtn = []

            # Jsonでデータ取得
            datas = json.loads(rcv_msg.decode())

            for data in datas:
                # 各命令を行う

                # アドレス
                address = data['add']
                # コマンド
                cmd = data['cmd']

                if data['act'] == 'r':
                    # 読み込み

                    # len
                    len = int(data['len'])

                    # I2C 読み出し処理を行う
                    read_data = self.tp_inter.i2c_read(
                        setting['slot'], address, cmd, len)
                    # 戻り値
                    rtn.append(read_data)

                elif data['act'] == 'w':
                    # 書き込み

                    # value
                    vals = data['v']

                    # I2C 書き込み処理を行う
                    self.tp_inter.i2c_write(setting['slot'], address, vals)

            # Jsonで返却
            return json.dumps(rtn)

        elif setting['comm'] == SPI:
            #--------------
            # SPI
            #--------------

            # 戻り値配列
            rtn = []

            # Jsonでデータ取得
            datas = json.loads(rcv_msg.decode())

            for data in datas:

                # アドレス
                address = data['add']
                # 値
                val = data['v']

                # TODO SPIの処理を行う。SPIの場合は必ず戻り値がある
                rtn_data = [0x02]

                # 戻り値
                rtn.append(rtn_data)

            # Jsonで返却
            return json.dumps(rtn)

        elif setting['comm'] == Serial:
            #--------------
            # Serial
            #--------------

            # TODO rcv_msg(多分bytes型)をそのまま使う

            # 戻り値は無し
            return

    def __send_data(self, slot, comm, send_msg):
        """
        データを送信します。
        """

        # slot: スロット番号
        # comm: 通信方式
        # send_msg: 送信メッセージ
        self.handler(self.callback_send, slot, comm, send_msg)

    def handler(self, func, *args):
        """
        ハンドラー
        """
        return func(*args)
