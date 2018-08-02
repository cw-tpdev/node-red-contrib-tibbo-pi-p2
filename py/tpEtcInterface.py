#!/usr/bin/python3
import os, sys
import time
from tpBoardInterface import TpBoardInterface
import tpUtils
import math

class TpEtcInterface:
    """
    特殊なTibbitや外部インターフェースの設定を行います。
    """

    def __init__(self, board_inter):
        """
        コンストラクタ

        board_inter : tpBoardInterfaceのインスタンス
        """

        # 設定
        self.__inter = board_inter
        self.__tp22_wait_max_ms = 100
        self.__RTD_A = 3.9080e-3
        self.__RTD_B = -5.870e-7

    def tp22_get_temp(self, slot, pt_kind):
        """
        Tibbit #22 温度測定用
            slot    : 'S01' ~ 'S10'
            pt_kind : 'PT100', 'PT200', 'PT500', 'PT1000'
        """
        #print('tp22_get_temp', slot, pt_kind)
        # reset
        #self.__inter.gpio_write(slot, 'C', '0')
        #self.__inter.gpio_write(slot, 'C', '1')

        # 温度読み込み
        rtd = self.__inter.tp22_temp(slot)
        temp = self.__tp22_temp(rtd, pt_kind)
        return round(temp, 2)

    def tp22_get_ver(self, slot):
        """
        Tibbit #22 バージョン取得
            slot    : 'S01' ~ 'S10'
        """
        #print('tp22_get_ver', slot)
        self.__inter.i2c_write_tp22(slot, 0x03)
        ret = self.__inter.i2c_read_tp22(slot, 16)
        ver = ''
        for i in ret: ver += chr(i)
        #print(ver)
        return ver

   # 内部メソッド ---

    def __tp22_check(self, slot):
        begin_time = time.time()
        while True:
            ret = self.__inter.gpio_read(slot, 'D')
            if ret == 1: break # Highになるまでwait
            cur_time = time.time()
            if (cur_time - begin_time) * 1000 > self.__tp22_wait_max_ms:
                raise ValueError('Tibbit #22 wait error!')

    def __tp22_temp(self, rtd, pt_kind):
        if rtd % 2 == 1:
            raise ValueError('Tibbit #22 RTD error!')
        rtd /= 2;

        if pt_kind == 'PT100':
            normal_0_resist = 100.0
        elif pt_kind == 'PT200':
            normal_0_resist = 200.0
        elif pt_kind == 'PT500':
            normal_0_resist = 500.0
        elif pt_kind == 'PT1000':
            normal_0_resist = 1000.0
        else:
            raise ValueError('Tibbit #22 PT kind error!')

        rtd_rref = 4000.0
        a2 = 2.0 * self.__RTD_B
        b_sq = self.__RTD_A * self.__RTD_A

        rtd_resist = normal_0_resist
        resist = rtd * rtd_rref / 32768.0

        c = 1.0 - (resist / rtd_resist)
        d = b_sq - 2.0 * a2 * c

        data = math.sqrt(d)
        data = (-self.__RTD_A + data) / a2;

        return data

# main部 -----------------------------------------------------------------

if __name__ == '__main__':
    inter = TpBoardInterface('', '')
    etc = TpEtcInterface(inter)
