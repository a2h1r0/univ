import sys
import numpy as np
import csv
from natsort import natsorted
import glob
import os
os.chdir(os.path.dirname(__file__))


MODEL = 'Series_5'  # 表示するスマートウォッチ
TARGET_RATES = [60, 65, 70, 75, 80, 85, 90, 95, 100]  # 取得した目標心拍数
DISPLAYS = [['Legion7', 'Display A'], ['OSOYOO', 'Display B'],
            ['KeDei', 'Display C']]  # 表示するディスプレイ
DIRS = ['1st', '2nd', '3rd']  # フォルダ分け

INITIALIZATION_TIME = 30  # キャリブレーション時間


def main():
    for display in DISPLAYS:
        for directory in DIRS:
            files = natsorted(glob.glob('../generate_heart_rate/data/AppleWatch/' +
                                        MODEL + '/' + display[0] + '/' + directory + '/*.csv'))
            diffs = []
            sample_num = []

            if len(TARGET_RATES) != len(files):
                print('\nパラメータに誤りがあります。\n')
                sys.exit()

            # 心拍数ごとにデータを取得
            for target_rate, data in zip(TARGET_RATES, files):
                with open(data) as f:
                    reader = csv.reader(f)
                    next(reader)

                    values = []
                    for row in reader:
                        if int(row[0]) > INITIALIZATION_TIME * 1000:
                            values.append(int(row[1]))

                    # 取得時間での平均値
                    average = round(sum(values) / len(values))
                    # 目標値からの差の計算
                    diffs.append(average - target_rate)
                    # サンプル数の追加
                    sample_num.append(len(values))

            # 結果の表示
            print('\n--- ' + display[1] + ' ' + directory + ' ---\n')
            for target, diff in zip(TARGET_RATES, diffs):
                print(str(target) + ': ' + str(diff))
            print('\nAverage Diff: ' + str(np.mean(diffs)))
            print('\n*** Sample Length ***')
            print('Min: ' + str(min(sample_num)))
            print('Max: ' + str(max(sample_num)) + '\n')


if __name__ == '__main__':
    main()
