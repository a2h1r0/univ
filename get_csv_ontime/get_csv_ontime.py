import serial
from time import sleep
import os.path
import csv
import math

ser = serial.Serial('COM5', 9600)   # Arduino1号機
ser2 = serial.Serial('COM6', 9600)  # Arduino2号機
filename = 'attack.csv'               # データ保存先ファイル
time = 120                           # データ取得時間(秒単位)
tester = "Yamada"                     # 正解ラベル(被験者名)

sleep(1)    # ポート準備に1秒待機**これがないとシリアル通信がうまく動かない**

exist = 0                       # 分岐処理用
if os.path.isfile(filename):    # データ保存ファイルの存在確認
    exist = 1
    
with open(filename, 'a', newline='') as f:
    writer = csv.writer(f)

    if exist == 0:      # ファイルが新規作成の場合，ラベルを付与する
        writer.writerow(["in0","in1","in2","in3","in4","in5","in6","in7","in8",
                         "in9","inA","inB","inC","inあ","inい","inう",
                         "in10","in11","in12","in13","in14","in15","in16",
                         "in17","in18","in19","inD","inE","inF","inア","inイ",
                         "inウ","Time","Tester"])
    elif exist == 1:    # ファイルが既存の場合，ラベルを付与しない
        print("File exist. Didn't give label.")
   
    # データの取得と書き込み
    while True:
        # シリアル通信
        ser.write("!".encode('UTF-8'))
        voltage = ser.readline().decode('UTF-8').rstrip().split()
        ser2.write("?".encode('UTF-8'))
        voltage2 = ser2.readline().decode('UTF-8').rstrip().split()
        
        # 時間を秒単位へ変換(小数点以下2桁，それ以下切り上げ)
        voltage2[-1] = (math.ceil(int(voltage2[-1])/10**4))/10**2
        
        # 経過時間がデータ取得時間を超えると，ファイルへ書き込みせずに終了
        if (voltage2[-1] > time):
            break

        voltage.extend(voltage2)    # 1号機と2号機のデータを結合
        voltage.append(tester)      # 最終列に正解ラベル(被験者名)を追加
        
        writer.writerow(voltage)    # ファイルへ書き込み

ser.close()
ser2.close()
print("Finish")