#!C:/Users/atsu3/anaconda3/python.exe
# -*- coding: utf-8 -*-
import sys
import serial
from time import sleep
import slackweb


USB_PORT = 'COM6'
SLACK_URL = ''


def main():
    # Ajaxデータの受け取り
    key = sys.stdin.read().rstrip()

    if key in ['down', 'up']:
        do_fishing_action(key)
    elif key in ['front', 'back', 'left', 'right']:
        move_location(key)


def do_fishing_action(key):
    """釣り動作の実行（リールの制御）
    Args:
        key (string): アプリ上で入力されたキー
    """

    # シリアル通信（Arduino）の初期化
    ser = serial.Serial(USB_PORT, 9600)
    ser.reset_input_buffer()
    sleep(2)

    if key == 'down':
        data = '0'
    elif key == 'up':
        data = '1'

    # Arduinoに接続してリールを制御
    ser.write(data.encode('UTF-8'))
    ser.readline().rstrip().decode(encoding='UTF-8')

    # シリアル通信の終了
    ser.close()


def move_location(key):
    """竿の移動（Slackに移動方向を通知）
    Args:
        key (string): アプリ上で入力されたキー
    """

    # Slack通知の初期化
    slack = slackweb.Slack(url=SLACK_URL)

    if key == 'front':
        text = '前'
    elif key == 'back':
        text = '後'
    elif key == 'left':
        text = '左'
    elif key == 'right':
        text = '右'
    slack.notify(text=(text + 'へ移動！'))


if __name__ == '__main__':
    main()
