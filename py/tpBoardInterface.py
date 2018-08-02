#!/usr/bin/python3
import os, sys
import _thread as thread
import time
#from tpP1Interface import TpP1Interface
from tpP2Interface import TpP2Interface
from constant import *
import json
import tpUtils
import re

# クラス宣言 -------------------------------------------------------------
class TpBoardInterface:
    """
    Tibbo-Pi基板とのインターフェース層です。
    """

    def __init__(self, settings, callback_send):
        """
        コンストラクタ
        """
        # データ初期化
        self.__serial_recv_buf = [[] for i in range(5)] # serail 5slotぶんのバッファslot 1,3,5,7,9 の順
        self.__serial_info = [{'recv_kind':''} for i in range(5)] # serail 5slotぶんの情報
        """
        {'recv_kind':以下}
	'NONE'/'CHAR'/'LENG'/'TI
	で、それぞれ必要なら、
	{'char':1文字}
	{'leng':長さ}
	{'time':ms}
        """

        # P1/P2/P3 切り替え
        self.__board_kind = 'P2'
        if self.__board_kind == 'P1':
            self.__board = TpP1Interface()
        elif self.__board_kind == 'P2':
            self.__board = TpP2Interface()
        else: # P3
            self.__board = TpP3Interface()
        self.board = self.__board 
        
        # 排他制御用定義
        self.i2c_lock = thread.allocate_lock()
        self.spi_lock = thread.allocate_lock()
        if self.__board_kind == 'P2':
            self.__board.spi_init(self.spi_lock)

        # ボード初期化
        self.__board.board_init()
        
        # 設定
        self.__tp_button = False
        self.settings = settings
        self.__settings_check()
        
        # イベント発生用のコールバック関数をセット
        self.callback_send = callback_send

        # ブザー初期化
        self.__buzzer_init()

    def serial_write(self, slot, vals):
        """
        Serial書き込み
        slot    : 'S01' ~ 'S10'
        vals    : 書き込みデータ
        """
        # slot選択
        slot_num = tpUtils.slot_str_to_int(slot)

        # Serial書き込み
        self.__board.serial_write(slot_num, vals)

    def analog_read(self, slot, line):
        """
        GPIO アナログあ外読み出し
        slot : 'S01' ~ 'S10'
        line : 'A' ~ 'D'
        """
        slot_num = tpUtils.slot_str_to_int(slot)
        line_num = tpUtils.line_str_to_int(line)
        dat = 0

        if self.__board_kind == 'P1':
            # P1には機能なし
            return
        elif self.__board_kind == 'P2':
            dat = self.__board.analog_read(slot_num, line_num)
        else: # P3
            pass

        return dat

    def gpio_read(self, slot, line):
        """
        GPIO読み出し
        slot : 'S01' ~ 'S10'
        line : 'A' ~ 'D'
        """
        slot_num = tpUtils.slot_str_to_int(slot)
        line_num = tpUtils.line_str_to_int(line)
        dat = 0

        if self.__board_kind == 'P1':
            self.i2c_lock.acquire(1)
            dat = self.__board.gpio_read(slot_num, line_num)
            self.i2c_lock.release()
        elif self.__board_kind == 'P2':
            #self.spi_lock.acquire(1) # P2はtpP2Interface内部で排他制御
            dat = self.__board.gpio_read(slot_num, line_num)
            #self.spi_lock.release()
        else: # P3
            pass

        return dat

    def gpio_write(self, slot, line, val):
        """
        GPIO書き込み
        slot : 'S01' ~ 'S10'
        line : 'A' ~ 'D'
        val  : '0' or '1'
        """
        slot_num = tpUtils.slot_str_to_int(slot)
        line_num = tpUtils.line_str_to_int(line)

        if self.__board_kind == 'P1':
            self.i2c_lock.acquire(1)
            self.__board.gpio_write(slot_num, line_num, int(val))
            self.i2c_lock.release()
        elif self.__board_kind == 'P2':
            #self.spi_lock.acquire(1) # P2はtpP2Interface内部で排他制御
            self.__board.gpio_write(slot_num, line_num, int(val))
            #self.spi_lock.release()
            pass
        else: # P3
            pass

    def spi_access(self, slot, address, vals):
        """
        SPI書き込み・読み出し
        slot    : 'S01' ~ 'S10', 'S00'はPICだが、隠し機能
        address : レジスタアドレス 
        vals    : 書き込みデータ, 読み込み時はdammy
        """
        # slot選択
        slot_num = tpUtils.slot_str_to_int(slot)

        # P2はtpP2Interface内部で排他制御
        if self.__board_kind != 'P2': self.spi_lock.acquire(1)

        # SPI情報取得
        mode = 0
        speed = 0
        endian = 0
        for elem in self.settings:
            if elem['slot'] != slot: continue
            setting = elem['settings']
            mode = int(setting['mode']) 
            speed = int(setting['speed'])
            endian = int(setting['endian'])
            break

        # SPIアクセス
        data = self.__board.spi_access(slot_num, mode, speed, endian, 0, address, vals)

        # P2はtpP2Interface内部で排他制御
        if self.__board_kind != 'P2': self.spi_lock.release()

        return data

    def tp22_temp(self, slot):
        """
        Tibbit#22, RTD読み出し
        slot : 'S01' ~ 'S10'
        """
        slot_num = tpUtils.slot_str_to_int(slot)
        self.i2c_lock.acquire(1)
        try:
            data = self.__board.tp22_temp(slot_num)
        except:
            raise
        finally:
            self.i2c_lock.release()
        return data

    def i2c_read_tp22(self, slot, num):
        """
        Tibbit#22, I2C読み出し
        slot : 'S01' ~ 'S10'
        num  : 読み込みbyte数
        """
        slot_num = tpUtils.slot_str_to_int(slot)
        self.i2c_lock.acquire(1)
        try:
            data = self.__board.i2c_read_tp22(slot_num, num)
        except:
            raise
        finally:
            self.i2c_lock.release()
        return data

    def i2c_write_tp22(self, slot, val):
        """
        Tibbit#22, I2C書き込み
        slot : 'S01' ~ 'S10'
        val  : 書き込みデータ、1byteのみ
        """
        slot_num = tpUtils.slot_str_to_int(slot)
        self.i2c_lock.acquire(1)
        try:
            self.__board.i2c_write_tp22(slot_num, val)
        except:
            raise
        finally:
            self.i2c_lock.release()

    def i2c_write_tp22_spi(self, slot, addr, val):
        """
        Tibbit#22, I2C書き込み(内部SPIデバイス)
        slot : 'S01' ~ 'S10'
        addr : SPIアドレス、0x80以上
        val  : 書き込みデータ、1byteのみ
        """
        slot_num = tpUtils.slot_str_to_int(slot)
        self.i2c_lock.acquire(1)
        try:
            self.__board.i2c_write_tp22(slot_num, val, addr)
        except:
            raise
        finally:
            self.i2c_lock.release()

    def i2c_read(self, slot, address, cmd, num):
        """
        I2C読み出し
        slot    : 'S01' ~ 'S10'
        address : I2Cアドレス
        cmd     : 読み込み時コマンド（1byte）
        num     : 読み込みbyte数
        """
        slot_num = tpUtils.slot_str_to_int(slot)

        self.i2c_lock.acquire(1)
        try:
            self.__board.i2c_select(slot_num)
            data = self.__board.i2c_read(address, cmd, num)
        except:
            raise
        finally:
            self.__board.i2c_select() # slot選択解除
            self.i2c_lock.release()
        return data

    def i2c_write(self, slot, address, vals):
        """
        I2C書き込み
        slot    : 'S01' ~ 'S10'
        address : I2Cアドレス
        vals    : 書き込みデータ、1 or 2 byte
        """
        slot_num = tpUtils.slot_str_to_int(slot)
        if len(vals) != 1 and len(vals) != 2:
            raise ValueError('I2C write data number error! : ' + str(len(vals)))

        self.i2c_lock.acquire(1)
        try:
            self.__board.i2c_select(slot_num)
            if len(vals) == 1:
                self.__board.i2c_write_1byte(address, vals[0])
            else: # 2byte
                self.__board.i2c_write_2byte(address, vals[0], vals[1])
        except:
            raise
        finally:
            self.__board.i2c_select() # slot選択解除
            self.i2c_lock.release()

    def i2c_block_write(self, slot, address, cmd, vals):
        """
        I2Cブロック書き込み、コマンド付き
        slot    : 'S01' ~ 'S10'
        address : I2Cアドレス
        cmd     : コマンド
        vals    : 書き込みデータ、リスト
        """
        slot_num = tpUtils.slot_str_to_int(slot)
        self.i2c_lock.acquire(1)
        try:
            self.__board.i2c_select(slot_num)
            self.__board.i2c_write_block_data(address, cmd, vals)
        except:
            raise
        finally:
            self.__board.i2c_select() # slot選択解除
            self.i2c_lock.release()

    def rp_buzzer(self, time_msec, pattern):
        """
        ラズパイブザー鳴動
        time_msec : 鳴らす時間
        pattern   : パターン
        """
        time_msec_int = int(time_msec) if type(time_msec) is str else time_msec
        pattern_int = int(pattern) if type(pattern) is str else pattern
        self.__buzzer_set(time_msec_int, pattern_int)

    def rp_led(self, num, val):
        """
        ラズパイLED制御
        num : LED番号
        val : 1/0, 1=On
        """
        num_int = int(num) if type(num) is str else num
        val_int = int(val) if type(val) is str else val
        if num_int >= 1 and num_int <= 4:
            self.__board.rp_led(num_int, val_int)
        else:
            raise ValueError('Board LED number error! 1~4 : ' + str(num_int))
       
    # 内部メソッド ---

    def __serial_init(self, setting):
        """
        tibbit Seral設定
        setting : self.settingsの要素
        """
        slot_num = tpUtils.slot_str_to_int(setting['slot'])
        if slot_num % 2 == 0: # 奇数slotのみ対応
            raise ValueError('Serial slot error! : ' + str(slot_num))
        # 通信情報設定
        baud = setting['settings']['baudRate']
        flow = setting['settings']['hardwareFlow']
        parity = setting['settings']['parity']
        sep_kind = setting['settings']['splitInput']
        sep_char = setting['settings']['onTheCharactor']
        sep_time = setting['settings']['afterATimeoutOf']
        sep_leng = setting['settings']['intoFixedLengthOf']
        #print(slot_num, baud, flow, parity, sep_char, sep_time, sep_leng)
        baud_num = int(baud)
        flow_num = 1 if flow == 'on' else 0
        parity_num = 0 if parity == 'none' else 1 if parity == 'odd' else 2
        self.__board.serial_init(
                self.__serial_event_callback, 
                slot_num, 
                baud_num, 
                flow_num, 
                parity_num)

        # 受信用情報確保
        pos = int((slot_num - 1) / 2)
        if sep_kind == '1':
            self.__serial_info[pos]['recv_kind'] = 'CHAR'
            self.__serial_info[pos]['char'] = sep_char
        elif sep_kind == '2':
            self.__serial_info[pos]['recv_kind'] = 'TIME'
            self.__serial_info[pos]['time'] = int(sep_time)
            self.__serial_info[pos]['lock'] = thread.allocate_lock()
            thread.start_new_thread(self.__serial_recv_time_thread, (slot_num, int(sep_time)))
        elif sep_kind == '3':
            self.__serial_info[pos]['recv_kind'] = 'LENG'
            self.__serial_info[pos]['leng'] = int(sep_leng)
        else:
            self.__serial_info[pos]['recv_kind'] = 'NONE'
        #print(self.__serial_info)

    #def serial_event_callback_test(self, slot, val):
    #    self.__serial_event_callback(slot, val)
    def __serial_event_callback(self, slot, val):
        #print(tpUtils.slot_int_to_str(slot), send_data)

        # いったん、バッファへ受信データ格納
        pos = int((slot - 1) / 2)
        kind = self.__serial_info[pos]['recv_kind']
        try:
            if kind == 'TIME' : # 時間区切り
                self.__serial_info[pos]['lock'].acquire(1)
            self.__serial_recv_buf[pos].extend(val)
        except:
            raise
        finally:
            if kind == 'TIME' : # 時間区切り
                self.__serial_info[pos]['lock'].release()

        # 受信方法による振り分け
        if kind == 'CHAR' : # 文字区切り
            char = self.__serial_info[pos]['char']
            self.__serial_recv_char(slot, char)
        elif kind == 'TIME' : # 時間区切り
            pass # 別スレッドで対応
        elif kind == 'LENG' : # 固定長区切り
            leng = self.__serial_info[pos]['leng']
            self.__serial_recv_leng(slot, leng)
        else: # 区切りなし
            send_data = self.__serial_recv_buf[pos][:] # 実copy
            #print(tpUtils.slot_int_to_str(slot), send_data, self.__serial_recv_buf)
            self.__serial_recv_buf[pos].clear()
            self.callback_send(tpUtils.slot_int_to_str(slot), Serial, json.dumps(send_data))

    def __serial_recv_char(self, slot, char):
        """Serial受信文字区切り
        """
        #print('__serial_recv_char', slot, char, len(char))
        pos = int((slot - 1) / 2)
        if ord(char) in self.__serial_recv_buf[pos]:
            buf_pos = self.__serial_recv_buf[pos].index(ord(char))
            send_data = self.__serial_recv_buf[pos][:buf_pos + 1] # 区切り文字含め、実copy
            #print(tpUtils.slot_int_to_str(slot), send_data, self.__serial_recv_buf)
            del self.__serial_recv_buf[pos][:buf_pos + 1]
            self.callback_send(tpUtils.slot_int_to_str(slot), Serial, json.dumps(send_data))

    def __serial_recv_leng(self, slot, leng):
        """Serial受信固定長区切り
        """
        pos = int((slot - 1) / 2)
        while len(self.__serial_recv_buf[pos]):
            if len(self.__serial_recv_buf[pos]) <= leng:
                break
            else:
                send_data = self.__serial_recv_buf[pos][:leng] # 実copy
                del self.__serial_recv_buf[pos][:leng]
            #print(tpUtils.slot_int_to_str(slot), send_data, self.__serial_recv_buf)
            self.callback_send(tpUtils.slot_int_to_str(slot), Serial, json.dumps(send_data))

    def __serial_recv_time_thread(self, slot, time_ms):
        """Serial受信時間区切り
        """
        pos = int((slot - 1) / 2)
        while True:
            time.sleep(time_ms / 1000)
            if len(self.__serial_recv_buf[pos]):
                send_data = self.__serial_recv_buf[pos][:] # 実copy
                self.__serial_recv_buf[pos].clear()
                #print(tpUtils.slot_int_to_str(slot), send_data, self.__serial_recv_buf)
                self.callback_send(tpUtils.slot_int_to_str(slot), Serial, json.dumps(send_data))

    def __gpio_init(self, setting):
        """
        tibbit GPIO設定、入力変化時のみ抜出
        setting : self.settingsの要素
        """
        slot_num = tpUtils.slot_str_to_int(setting['slot'])
        for pin in setting['pin']:
            #print(pin)
            if pin['status'] == 'IN' and 'edge' in pin:
                if pin['edge'] == 'on':
                    line_num = tpUtils.line_str_to_int(pin['name'])
                    self.__board.gpio_event_init(self.__gpio_event_callback, slot_num, line_num)

    def gpio_event_init(self, slot, line):
         self.__board.gpio_event_init(self.__gpio_event_callback, slot, line)
    def __gpio_event_callback(self, slot, line, on):
        send_data = {'line': tpUtils.line_int_to_str(line), 'v': on}
        #print(tpUtils.slot_int_to_str(slot), send_data)
        self.callback_send(tpUtils.slot_int_to_str(slot), GPIO, json.dumps(send_data))
       
    #def rp_button_init(self):
    #    self.__rp_button_init()
    def __rp_button_init(self):
        """
        基板ボタン使用時、callback等初期化
        """
        self.__board.rp_button_init(self.__rp_button_callback)

    def __rp_button_callback(self, kind, on):
        if kind == 'RST':
            send_data = {'btn': 1, 'v': on}
        else: # MD
            send_data = {'btn': 2, 'v': on}
        #print(send_data)
        self.callback_send('S00', TP_BUTTON, json.dumps(send_data))
       
    def __settings_check(self):
        for setting in self.settings:
            if 'comm' not in setting: continue
            #print(setting['comm'])
            if setting['comm'] == TP_BUTTON:
                # 基板ボタン用設定
                self.__rp_button_init()
            elif setting['comm'] == TP_BUZZER:
                # BUZZERパターン動作用thread設定
                self.__buzzer_init()
            elif setting['comm'] == GPIO:
                # tibbit GPIO用設定
                self.__gpio_init(setting)
            elif setting['comm'] == Serial:
                # tibbit GPIO用設定
                self.__serial_init(setting)

    def __buzzer_init(self):
        self.__buzzer_table = [ # 鳴動パターン用テーブル
                [0, 0],
                [0, 1],
                [1, 1],
                [0.5, 0.5],
                [0.2, 0.2],
                [0.1, 0.1],
                [0.1, 0.9]]
        self.__buzzer_stop_time = 0
        self.__buzzer_run_flg = False
        self.__buzzer_on_flg = False
        thread.start_new_thread(self.__buzzer_thread, ())

    def __buzzer_set(self, time_msec, pattern):
        self.__buzzer_time_on = 0
        self.__buzzer_time_off = 0
        if pattern == 0: # 強制停止
            self.__board.rp_buzzer(0)
            self.__buzzer_run_flg = False
        elif pattern == 1: # 連続On
            self.__board.rp_buzzer(1)
            self.__buzzer_run_flg = False
        elif pattern <= 6: 
            self.__buzzer_time_on = self.__buzzer_table[pattern][0]
            self.__buzzer_time_off = self.__buzzer_table[pattern][1]
            self.__buzzer_run_flg = True
            self.__buzzer_on_flg = True
        else: # エラー
            self.__board.rp_buzzer(0)
            self.__buzzer_run_flg = False
            raise ValueError('Buzzer pattern error! 0~6 : ' + str(pattern))

        if time_msec == 0:
            self.__buzzer_stop_time = 0
        else:
            self.__buzzer_stop_time = time.time() + time_msec / 1000

    def __buzzer_thread(self):
        while(True):
            time.sleep(0.01)
            #print(self.__buzzer_run_flg, self.__buzzer_on_flg)

            # 時間確認
            if self.__buzzer_stop_time == 0:
                pass
            else:
                if time.time() >= self.__buzzer_stop_time:
                    self.__board.rp_buzzer(0)
                    self.__buzzer_stop_time = 0
                    self.__buzzer_run_flg = False

            # On/Off動作
            if self.__buzzer_run_flg == False:
                pass
            else:
                if self.__buzzer_on_flg:
                    #print('ON')
                    self.__board.rp_buzzer(1)
                    time.sleep(self.__buzzer_time_on)
                    self.__buzzer_on_flg = False
                else:
                    #print('OFF')
                    self.__board.rp_buzzer(0)
                    time.sleep(self.__buzzer_time_off)
                    self.__buzzer_on_flg = True

# main部 -----------------------------------------------------------------

if __name__ == '__main__':

    from tpConfig import TpConfig
    tp_config = TpConfig()
    inter = TpBoardInterface('', '')
