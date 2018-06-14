#!/usr/bin/python3
"""P2プロモ用プログラム
   インターフェース部クラス
"""
gTpEnv = True # 環境チェック, TrueでTibbo-Piとみなす
import os, sys
import _thread as thread
import time
try:
    import smbus
    import RPi.GPIO as GPIO
    import subprocess
except:
    gTpEnv = False

# 定数宣言 ---------------------------------------------------------------
SLOT_SETTING_NONE = 0x00
SLOT_SETTING_SERI = 0x01
SLOT_SETTING_I2C  = 0x02
SLOT_SETTING_SPI  = 0x03
LINE_SETTING_NONE  = 0
LINE_SETTING_A_IN  = 1
LINE_SETTING_D_IN  = 2
LINE_SETTING_D_OUT = 3 # オープンドレイン

SPI_WAIT = 0.01 # SPIアクセス後のwait秒
CHECK_WAIT = 0.01 # GPIO edge, Serial イベントの定期チェックwait秒 
PIC_RST_CMD = 0xA0
PIC_WRITE_ADDR = 0x80

# クラス宣言 -------------------------------------------------------------
class TpLock():
    """
        排他処理用クラス
    """

    def __init__(self, lock_num):
        """ コンストラクタ
            指定した個数分のlockを確保する
        """
        self.lock = []
        for i in range(lock_num): self.lock.append(thread.allocate_lock())

    def acquire(self, pos):
        """ 該当の箇所のlockを取得する 
            pos : 該当のlockの場所
        """
        self.lock[pos].acquire(1)

    def release(self, pos):
        """ 該当の箇所のlockを解放する 
            pos : 該当のlockの場所
        """
        self.lock[pos].release()

class TpP2Interface():
    global gTpEnv

    def __init__(self):
        """ コンストラクタ
        """
        if gTpEnv: # Tibbo-Pi環境（以下全メソッドで同様）
            # 排他処理用設定
            self.__gpio_lock = TpLock(5)
            self.__line_lock = TpLock(10)

            # ハードウェア設定
            self.__i2c = smbus.SMBus(1)
            GPIO.setmode(GPIO.BCM)
            self.__path = os.path.dirname(os.path.abspath(__file__))
            subprocess.call(['/bin/sh', self.__path + '/c/ch.sh', self.__path + '/c/spi_access'])
            subprocess.call(['/bin/sh', self.__path + '/c/ch.sh', self.__path + '/c/i2c_read_tp22'])
            subprocess.call(['/bin/sh', self.__path + '/c/ch.sh', self.__path + '/c/i2c_write_tp22'])
            subprocess.call(['/bin/sh', self.__path + '/c/ch.sh', self.__path + '/c/tp22_temp'])
            subprocess.call(['/bin/sh', self.__path + '/c/ch.sh', self.__path + '/c/end_tp22.sh'])

            # パラメータ定義
            self.__gpio_in_edge_table = []
            self.__spi_cs_table = [25, 8, 5, 7]	
            self.__serial_int_table = [19, 16, 26, 20, 21]	
            self.__ex_gpio_int_table = [13]	
            self.__rp_led_table = [17, 18, 27, 22]	
            self.__kind_table = [[0, 0, 0, 0] for i in range(10)]
            self.gpio_event_callback = None
            self.serial_event_callback = None

            # PIC用SPI設定
            self.__pic_spi_mode = 0x03
            self.__pic_spi_khz = 250
            self.__pic_spi_endian = 1
            self.__pic_spi_wait_ms = 0

            # Tibbit#22用設定
            self.__tb22_addr = '0x0D'
            self.__tb22_kbaud = 15

        else: # 非Tibbo-Pi環境（以下全メソッドで同様, dummy値を返すこともあり）
            pass

    def board_init(self):
        """ 基板初期化
        """
        if gTpEnv:
            GPIO.setwarnings(False)
            self.__rp_gpio_init()
            self.i2c_select(0)
            # PIC初期化
            self.__pic_spi_access(PIC_WRITE_ADDR, [PIC_RST_CMD])

    def spi_init(self, lock):
        """ SPI初期化
            lock : SPIアクセス時thread lock
        """
        self.__spi_lock = lock

    def serial_init(self, callback, slot, baud, flow, parity):
        """ Serial初期化
        """
        #print('serial_init', callback, slot, baud, flow, parity)
        if slot % 2 == 0: return # 奇数slotのみ対応
        if gTpEnv:
            # PIC設定
            self.__slot_set(slot, SLOT_SETTING_SERI)
            pos = slot - 1
            addr = pos + 0x01 + PIC_WRITE_ADDR
            data = self.__serial_data(baud, flow, parity)
            self.__pic_spi_access(addr, [data])
            # 受信時callback設定
            if self.serial_event_callback is None:
                self.serial_event_callback = callback
                # 取りこぼしが発生するのでevent登録ではなくloopで処理する
                #pin = self.__serial_int_table[pos]
                #GPIO.add_event_detect(pin, GPIO.FALLING, callback = self.__serial_event_callback, bouncetime = 10) 
                thread.start_new_thread(self.__check_serial_thread, ())

    def serial_write(self, slot, vals):
        """ Serial書き込み
        """
        #print('serial_write', slot, vals)
        vals = [b for b in vals]
        
        if slot % 2 == 0: return # 奇数slotのみ対応
        pos = int((slot - 1) / 2)
        if gTpEnv:
            num_addr = pos + 0x6F
            dat_addr = pos + 0x79 + PIC_WRITE_ADDR
            while len(vals):
                dmy = [0]
                buff_num = 250 - self.__pic_spi_access(num_addr, dmy)[0]
                if buff_num >= len(vals):
                    self.__pic_spi_access(dat_addr, vals)
                    vals.clear()
                elif buff_num <= 0: # バッファあふれならwait
                    time.sleep(0.01)
                else:
                    self.__pic_spi_access(dat_addr, vals[:buff_num])
                    del vals[:buff_num]

    def spi_access(self, slot, mode, speed, endian, wait_ms, address, vals):
        """ SPI書き込み・読み出し
            slot    : 0 ~ 10, 0=PIC
            mode    : SPIモード, 0~3
            speed   : SPI速度, ~500KHz
            endian  : bit endian, 1=big(bit7から), 0=little(bit0から)
            wait_ms : address書き込み後のwait, PICでは1ms以上必要
            address : レジスタアドレス
            vals    : 書き込みデータ（リスト）
        """
        #print('spi_access', slot, mode, speed, endian, wait_ms, hex(address), vals)
        data = vals[:] # 実コピー
        if gTpEnv:
            c_cmd = self.__path +\
                '/c/spi_access ' +\
                str(mode) + ' ' +\
                str(speed) + ' ' +\
                str(endian) + ' ' +\
                '0x' + format(int(address), '02x') + ' ' +\
                str(wait_ms) + ' ' +\
                str(slot) + ' ' +\
                str(len(data))
            for elem in data: c_cmd += ' 0x' + format(elem, '02x')
            #print(c_cmd)
            self.__spi_lock.acquire(1)
            try:
                c_ret = subprocess.Popen(c_cmd,
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        shell=True)
            except:
                raise
            finally:
                self.__spi_lock.release()
            c_return = c_ret.wait()
            ret_bin = c_ret.stdout.readlines()
            #print(c_return, ret_bin)
            c_return -= 256 if c_return > 127 else c_return
            if c_return != 0:
                raise ValueError('SPI access error! : c_return = ' + str(c_return))
            ret_str = str(ret_bin[0])[2:-1]
            ret_str_sep = ret_str.split(',')
            ret = []
            for elem in ret_str_sep:
                ret.append(int(elem[2:], 16)) 
            #print(ret)
            return ret
        else:
            return data

    def gpio_event_init(self, callback, slot, line):
        """ ダイレクトGPIO入力event用設定
        """
        if gTpEnv:
            self.__line_set(slot, line, LINE_SETTING_D_IN)
            # callback 登録
            if self.gpio_event_callback is None:
                self.gpio_event_callback = callback
                # 取りこぼしが発生するのでevent登録ではなくloopで処理する
                #pin = self.__ex_gpio_int_table[0]
                #GPIO.add_event_detect(pin, GPIO.FALLING, callback = self.__gpio_event_callback, bouncetime = 10) 
                thread.start_new_thread(self.__check_gpio_thread, ())
            # Slot & Line 登録
            self.__gpio_in_edge_table.append([slot, line])

    def analog_read(self, slot, line):
        """ GPIO読み出し
            slot : 1 ~ 8
            line : 1 ~ 4
        """
        if slot > 8:
                raise ValueError('Analog read slot error! : slot = ' + str(slot))
        if gTpEnv:
            self.__line_set(slot, line, LINE_SETTING_A_IN)
            addr = (slot - 1) * 4 + (line - 1) + 0x3D
            dmy = [0]
            dat = self.__pic_spi_access(addr, dmy)
            #print('analog_read', slot, line, hex(addr), dat)
            return dat[0]
        else:
            return 0

    def gpio_read(self, slot, line):
        """ GPIO読み出し
            slot : 1 ~ 10
            line : 1 ~ 4
        """
        #print('gpio_read', slot, line)
        return self.__gpio_read(0x2E, slot, line)

    def gpio_write(self, slot, line, val):
        """ GPIO書き込み
            slot : 1 ~ 10
            line : 1 ~ 4
            val  : 0 or 1
        """
        self.__line_set(slot, line, LINE_SETTING_D_OUT)
        lock_pos = int((slot - 1) / 2)
        addr = lock_pos + 0x29
        dmy = [0]
        self.__gpio_lock.acquire(lock_pos) # 過去データorするため排他開始
        try:
            old = self.__pic_spi_access(addr, dmy)[0]
            # MSB:S1A,S1B,S1C,S1D,S2A,S2B,S2C,S2D:LSB のようなならび
            bit = 1 << (4 - line)
            if slot % 2 == 1: # 奇数slotは下位4bit
                bit <<= 4
            dat = old | bit if val == 1 else old & (~(bit))
            addr += PIC_WRITE_ADDR
            #print('gpio_write', slot, line, val, hex(addr), hex(dat))
            self.__pic_spi_access(addr, [dat])
        except:
            raise
        finally:
            self.__gpio_lock.release(lock_pos) # 排他解放

    def rp_button_init(self, callback):
        """ 基板ボタン用設定
        """
        self.rb_button_callback = callback
        GPIO.add_event_detect(24, GPIO.BOTH, callback = self.__rp_button_callback, bouncetime = 10) # MD
        GPIO.add_event_detect(23, GPIO.BOTH, callback = self.__rp_button_callback, bouncetime = 10) # RST

    def rp_buzzer(self, on):
        """ ラズパイブザーOn/Off
        """
        #print('rp_buzzer', on)
        GPIO.output(6, on)

    def rp_led(self, num, on):
        """ ラズパイLED On/Off
        """
        #print('rp_led', num, on)
        on = 1 if on == 0 else 0
        GPIO.output(self.__rp_led_table[num - 1], on)

    def tp22_temp(self, slot):
        """ Tibbit#22, RTD読み出し
            slot    : 1 ~ 10
            戻り    : 16bit (0x1234 など)
        """
        if gTpEnv:
            c_cmd = self.__path +\
                '/c/tp22_temp ' +\
                str(slot) + ' ' +\
                str(self.__tb22_kbaud) 
            #print(c_cmd)

            c_ret = subprocess.Popen(c_cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    shell=True)

            c_return = c_ret.wait()
            ret_bin = c_ret.stdout.readlines()
            #print(c_return, ret_bin)
            c_return -= 256 if c_return > 127 else c_return
            self.__i2c_end_tp22()
            if c_return != 0:
                raise ValueError('tp22_temp error! : c_return = ' + str(c_return))
            ret_str = str(ret_bin[0])[2:-1]
            ret = int(ret_str[2:], 16)
            #print(ret)
            return ret
        else:
            pass

    def i2c_read_tp22(self, slot, num):
        """ Tibbit#22, I2C読み出し
            slot    : 1 ~ 10
            num     : 読み込みbyte数
        """
        #print('i2c_read_tp22', slot, num)
        if gTpEnv:
            c_cmd = os.path.dirname(os.path.abspath(__file__)) +\
                '/c/i2c_read_tp22 ' +\
                str(slot) + ' ' +\
                str(self.__tb22_kbaud) + ' ' +\
                self.__tb22_addr + ' ' +\
                str(num)
            #print(c_cmd)

            c_ret = subprocess.Popen(c_cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    shell=True)

            c_return = c_ret.wait()
            ret_bin = c_ret.stdout.readlines()
            #print(c_return, ret_bin)
            c_return -= 256 if c_return > 127 else c_return
            self.__i2c_end_tp22()
            if c_return != 0:
                raise ValueError('i2c_read_tp22 error! : c_return = ' + str(c_return))
            ret_str = str(ret_bin[0])[2:-1]
            ret_str_sep = ret_str.split(',')
            ret = []
            for elem in ret_str_sep:
                ret.append(int(elem[2:], 16)) 
            #print(ret)
            return ret
        else:
            pass

    def i2c_write_tp22(self, slot, data, addr = 0):
        """ Tibbit#22, I2C書き込み
            slot    : 1 ~ 10
            data    : 1byteのみ、書き込みデータ
            addr    : 指定されていたらSPIアドレス、0x80以上のはず
        """
        #print('i2c_write_tp22', slot, data, addr)
        if gTpEnv:
            c_cmd = os.path.dirname(os.path.abspath(__file__)) +\
                '/c/i2c_write_tp22 ' +\
                str(slot) + ' ' +\
                str(self.__tb22_kbaud) + ' ' +\
                self.__tb22_addr + ' ' +\
                '0x' + format(int(data), '02x') 
            if addr != 0: c_cmd += ' 0x' + format(int(addr), '02x')
            #print(c_cmd)

            c_ret = subprocess.Popen(c_cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    shell=True)

            c_return = c_ret.wait()
            ret_bin = c_ret.stdout.readlines()
            #print(c_return, ret_bin)
            c_return -= 256 if c_return > 127 else c_return
            self.__i2c_end_tp22()
            if c_return != 0:
                raise ValueError('i2c_write_tp22 error! : c_return = ' + str(c_return))
        else:
            pass

    def i2c_read(self, address, cmd, num):
        """ I2C読み出し
            address : I2Cアドレス
            cmd     : 読み込み時コマンド（1byte）
            num     : 読み込みbyte数
        """
        return self.__i2c.read_i2c_block_data(address, cmd, num)

    def i2c_write_1byte(self, address, data):
        """ I2C 1byte書き込み
            address : I2Cアドレス
            data    : データ（1byte）
        """
        self.__i2c.write_byte(address, data)          

    def i2c_write_2byte(self, address, dat1, dat2):
        """ I2C 2byte書き込み
            address : I2Cアドレス
            dat1    : データ（1byteめ）
            dat2    : データ（2byteめ）
        """
        self.__i2c.write_byte_data(address, dat1, dat2)          

    def i2c_select(self, slot=0):
        """ I2C用slot選択
            slot : 0(未選択), 1~10
        """
        if slot >= 1 and slot <= 5:
            self.i2c_write_1byte(0x71, 0)
            self.i2c_write_1byte(0x70, 0x08 | (slot - 0))
        elif slot >= 6 and slot <= 10:
            self.i2c_write_1byte(0x70, 0)
            self.i2c_write_1byte(0x71, 0x08 | (slot - 5))
        else:
            self.i2c_write_1byte(0x70, 0)
            self.i2c_write_1byte(0x71, 0)

    def dbg_pic_reg_print(self, addr, num):
        """ Debug用PICレジスタ表示
            addr : 0x00～0x7F
            num  : byte数
        """
        dat = [0] * num
        ret = self.__pic_spi_access(addr, dat)
        for i, v in enumerate(ret): print(hex(i + addr), hex(v))

    # 内部メソッド ---

    def __i2c_end_tp22(self):
        while True:
            try:
                self.i2c_select(0)
                break
            except:
                subprocess.call(self.__path + '/c/end_tp22.sh', shell=True)

    #def serial_event_callback_test(self, pin):
    #    self.__serial_event_callback(pin)
    def __serial_event_callback(self, pin):
        #print(pin)
        pos = self.__serial_int_table.index(pin)
        slot = pos * 2 + 1
        if gTpEnv:
            num_addr = pos + 0x6A
            dat_addr = pos + 0x74
            while True:
                dmy = [0]
                buff_num = self.__pic_spi_access(num_addr, dmy)[0]
                if buff_num == 0: break
                dmy = [0] * buff_num
                data = self.__pic_spi_access(dat_addr, dmy)
                #print(slot, buff_num, data)
                self.serial_event_callback(slot, data)

    def __serial_data(self, baud, flow, parity):
        # ボーレート
        if baud == 2400:
            ret = 0
        elif baud == 4800:
            ret = 1
        elif baud == 14400:
            ret = 3
        elif baud == 19200:
            ret = 4
        elif baud == 38400:
            ret = 5
        elif baud == 57600:
            ret = 6
        elif baud == 115200:
            ret = 7
        else: # 9600 or other(default)
            ret = 2
        ret <<= 4

        # フロー制御
        ret += flow << 2

        # パリティ
        ret += parity        

        return ret

    def __pic_spi_access(self, address, vals):
        #begin_time = time.time()

        ret = self.spi_access(
                0,
                self.__pic_spi_mode,
                self.__pic_spi_khz,
                self.__pic_spi_endian,
                self.__pic_spi_wait_ms,
                address, vals)
        #time.sleep(SPI_WAIT)
        #end_time = time.time()
        #dt = end_time - begin_time
        #print('dt_ms =', dt * 1000)
        return ret

    def __rp_gpio_init(self):
        # I2C
        #RPIO.setup(2, RPIO.ALT0)
        #RPIO.setup(3, RPIO.ALT0)
        # SPI
        for pin in self.__spi_cs_table: 
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, 0) # 起動時Low
        # exGPIO
        for pin in self.__ex_gpio_int_table: 
            GPIO.setup(pin, GPIO.IN, pull_up_down = GPIO.PUD_UP)
        # Serial
        for pin in self.__serial_int_table: 
            GPIO.setup(pin, GPIO.IN, pull_up_down = GPIO.PUD_UP)
        # 基板LED
        for pin in self.__rp_led_table: 
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, 1) # 起動時消灯
        # 基板SW
        GPIO.setup(24, GPIO.IN, pull_up_down = GPIO.PUD_UP) # MD
        GPIO.setup(23, GPIO.IN, pull_up_down = GPIO.PUD_UP) # RST
        # 基板BZ
        GPIO.setup(6, GPIO.OUT)

    def __gpio_read(self, addr, slot, line):
        self.__line_set(slot, line, LINE_SETTING_D_IN)
        addr = int((slot - 1) / 2) + addr
        dmy = [0]
        dat = self.__pic_spi_access(addr, dmy)[0]
        # MSB:S1A,S1B,S1C,S1D,S2A,S2B,S2C,S2D:LSB のようなならび
        bit = 1 << (4 - line)
        if slot % 2 == 1: # 奇数slotは上位4bit
            bit <<= 4
        ret = 0 if dat & bit == 0 else 1
        #print('gpio_read', slot, line, hex(addr), hex(dat), ret)
        return ret

    def __gpio_edge_check(self, dat, up, slot, line):
        """ pinのエッジを調べる
            dat  : PICの0x33～0x3Cのエッジ情報10byte
            up   : 立ち上がりエッジを調べる場合True、下がりならFalse
            slot : 1～10
            line : 1～4
        """
        #print('__gpio_edge_check', dat, up, slot, line)
        bit = 1 << (4 - line)
        if slot % 2 == 1: # 奇数slotは上位4bit
            bit <<= 4
        indx = int((slot - 1) / 2)
        if up == False: indx += 5
        ret = 0 if dat[indx] & bit == 0 else 1
        #print('__gpio_edge_check', slot, line, up, indx, dat[indx], ret)
        return ret

    #def gpio_event_callback_test(self, pin):
    #    self.__gpio_event_callback(pin)
    def __gpio_event_callback(self, pin):
        #print(pin)
        # 全エッジ情報読み出し
        dat = [0] * 10
        ret = self.__pic_spi_access(0x33, dat)
        for elem in self.__gpio_in_edge_table:
            # 立ち上がりエッジ確認
            if self.__gpio_edge_check(ret, True, elem[0], elem[1]) == 1:
                #print('Rise callback : slot =', elem[0], 'line =', elem[1])
                self.gpio_event_callback(elem[0], elem[1], 1)
            # 立ち下がりエッジ確認
            if self.__gpio_edge_check(ret, False, elem[0], elem[1]) == 1:
                #print('Fall callback : slot =', elem[0], 'line =', elem[1])
                self.gpio_event_callback(elem[0], elem[1], 0)

    def __rp_button_callback(self, pin):
        if (pin == 24):
            on = 1 if GPIO.input(24) == 0 else 0
            self.rb_button_callback('MD', on)
        else:
            on = 1 if GPIO.input(23) == 0 else 0
            self.rb_button_callback('RST', on)

    def __i2c_read_1byte_after_write(self, address, data):
        return self.__i2c.read_byte_data(address, data)

    def __slot_set(self, slot, kind):
        """ Slot設定
            slot : 1 ~ 10
        """
        #print('__slot_set', slot, kind)
        addr = (slot - 1) * 3 + 0x8B
        self.__pic_spi_access(addr, [kind])

    def __line_set(self, slot, line, kind):
        #print('__line_set', slot, line, kind)
        # 設定済みか確認
        if self.__kind_table[slot - 1][line - 1] == kind: return
        self.__kind_table[slot - 1][line - 1] = kind

        # 設定開始
        # 現在情報読み込み 
        lock_pos = slot - 1
        addr = lock_pos * 3 + 0x0B
        self.__line_lock.acquire(lock_pos) # 過去データorするため排他開始
        try:
            if line == 1 or line == 2: # A or B
                dmy = [0]
                val = self.__pic_spi_access(addr + 1, dmy)
                if line == 1: # A 
                    val[0] = (val[0] & 0x0F) | (kind << 4)
                else: # B
                    val[0] = (val[0] & 0xF0) | (kind)
            else: # C or D
                dmy = [0, 0]
                val = self.__pic_spi_access(addr + 1, dmy)
                if line == 3: # C
                    val[1] = (val[1] & 0x0F) | (kind << 4)
                else: # D
                    val[1] = (val[1] & 0xF0) | (kind)
            # 現在情報とorして書き込み
            val.insert(0, SLOT_SETTING_NONE)
            #print(hex(addr), val, kind)
            self.__pic_spi_access(PIC_WRITE_ADDR + addr, val)
        except:
            raise
        finally:
            self.__line_lock.release(lock_pos) # 排他解放

    def __check_gpio_thread(self):
        """ event登録のかわりにloopで処理
        """
        while True:
            pin = self.__ex_gpio_int_table[0]
            if GPIO.input(pin) == 0:
                self.__gpio_event_callback(pin)
            time.sleep(CHECK_WAIT)

    def __check_serial_thread(self):
        """ event登録のかわりにloopで処理
        """
        while True:
            for pin in self.__serial_int_table:
                if GPIO.input(pin) == 0:
                    self.__serial_event_callback(pin)
            time.sleep(CHECK_WAIT)

# main部 -----------------------------------------------------------------

if __name__ == '__main__':
    argv = sys.argv
    inter = TpP2Interface()
    lock = thread.allocate_lock()
    inter.spi_init(lock)
    inter.board_init()

