import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

MIN = 1.5           # 閾値の下限
MAX = 3.0           # 閾値の上限
time = 10.0

# CSVファイルの読み込み，認証データ1人目には学習データに用いた被験者の別データを正解として格納
attack_file = np.loadtxt('attack.csv', delimiter = ",", dtype = float, 
                    skiprows = 1, usecols = range(0,33)) # 認証データ
train_file = np.loadtxt('train.csv', delimiter = ",", dtype = float, 
                   skiprows = 1, usecols = range(0,33))  # 学習データ
attack_tester = pd.read_csv('attack.csv', usecols = ['Tester'], encoding = 'shift-jis') # 認証データ
train_tester = pd.read_csv('train.csv', usecols = ['Tester'], encoding = 'shift-jis')  # 学習データ


# 配列作成，ループ用に+0.1(MIN~MAXまではMAX-MIN+0.1要素ある)
MAX += 0.1
# ループ用に整数化
int_MIN = int(MIN*10)
int_MAX = int(MAX*10)

# x軸の初期化，閾値の配列を作成
x = np.arange(MIN, MAX, 0.1)
# 計算結果配列の初期化，閾値数の配列を作成，閾値ごとに結果を格納
FRR = np.zeros(int_MAX-int_MIN) # False Rejection Rate(本人拒否率)
FAR = np.zeros(int_MAX-int_MIN) # False Acceptance Rate(他人受入率)
TAR = np.zeros(int_MAX-int_MIN) # True Acceptance Rate(本人受入率)
TRR = np.zeros(int_MAX-int_MIN) # True Rejection Rate(他人拒否率)

# カウンタ変数の初期化
loop = threshold = row = 0

# ベクトル距離計算と閾値判定
for thresholds in range(int_MIN, int_MAX):  # 閾値移動ループ
    
    for attack in attack_file:              # 認証データ変更ループ
        if (attack[-1] <= time):
            attack = np.delete(attack, -1)
            # 認証データ1つにつき，学習データ全てに対して距離計算
            for train in train_file:
                if (train[-1] <= time):
                    train = np.delete(train, -1)
                    
                    distance = np.linalg.norm(attack-train) # ベクトル距離計算
                    # 距離が閾値以下なら，受け入れる
                    if (distance <= (thresholds/10)):   # ループ用に整数化してあるので÷10
                        if (attack_tester.iat[row, 0] == 'Fujii'): # 認証データが正解(本人)
                            TAR[threshold] += 1 # 本人受入数
                        else:                                    # 認証データが攻撃(他人)
                            FAR[threshold] += 1 # 他人受入数
                    # 距離が閾値より大きいなら，弾く
                    elif (distance > (thresholds/10)):
                        if (attack_tester.iat[row, 0] == 'Fujii'): # 正解(本人)の場合
                            FRR[threshold] += 1 # 本人拒否数
                        else:                                    # 攻撃(他人)の場合
                            TRR[threshold] += 1 # 他人拒否数
                    loop += 1
        else:
            row += 1

    print(FRR[threshold])
    print(FAR[threshold])
    print(TAR[threshold])
    print(TRR[threshold])
    # 確率計算
    FRR[threshold] = (FRR[threshold]/loop)*100
    FAR[threshold] = (FAR[threshold]/loop)*100
    TAR[threshold] = (TAR[threshold]/loop)*100
    TRR[threshold] = (TRR[threshold]/loop)*100

    # 次の閾値に変更
    threshold += 1  # 計算結果配列の格納先を移動
    loop = row = 0        # 計算回数の初期化

# 確率計算と結果の表示
for i in range(threshold):  # 閾値数回(配列要素数)だけ計算

    # 結果表示
    text = "Threshold: {:.1f}"
    print(text.format(MIN))
    MIN += 0.1
    text = "False Rejection Rate: {:.1f}"
    print(text.format(FRR[i]))
    text = "False Acceptance Rate: {:.1f}"
    print(text.format(FAR[i]))
    text = "True Acceptance Rate: {:.1f}"
    print(text.format(TAR[i]))
    text = "True Rejection Rate: {:.1f}"
    print(text.format(TRR[i]))
    print('\n')
    
# 結果を描画
plt.xlabel("Threshold")
plt.ylabel("Rate")
plt.plot(x, FRR, 'red', label="False Rejection Rate")
plt.plot(x, FAR, 'blue', label="False Acceptance Rate")
plt.plot(x, TAR, 'yellow', label="True Acceptance Rate")
plt.plot(x, TRR, 'green', label="True Rejection Rate")
plt.legend()    # 凡例の表示
plt.show()