import os
import numpy as np
import pandas as pd
from dataclasses import dataclass


# 座標、倍率データ格納用のクラス
@dataclass
class SemData:
    index: int
    dir: str
    df: pd.DataFrame


def read_metadata(file_path):
    df = pd.read_csv(file_path)
    df = df['[SemImageFile]'].str.split('=', expand=True)
    df.set_index(0, inplace=True)
    # SEMの記録ではy座標は下向きが正っぽい？
    x = int(df.loc['StagePositionX'][1]) / 1000000  # mm
    y = int(df.loc['StagePositionY'][1]) / 1000000  # mm
    mag = int(df.loc['Magnification'][1])
    data_size = np.array(list(map(int, df.loc['DataSize'][1].split('x'))))  # 1280x960など
    pixel_size = float(df.loc['PixelSize'][1]) / 1000000  # mm / pixel
    img_size = data_size * pixel_size  # mm
    return x, y, mag, img_size


# リスト内のフォルダにあるテキストファイルを読み込み、DataFrameに格納、まとめる
def read_metadata_in_folders(folders):
    dict_df = {}
    for i, folder in enumerate(folders):
        folder = folder.strip('"')  # windowsの「パスをコピー」ボタンでは""がついてきてしまうため
        txt_list = []
        if folder == '':
            continue
        for name in os.listdir(folder):
            if '.txt' in name:
                txt_list.append(name[:-4])

        # txtファイルの中身を読み込み，データの成型
        data = []
        for name in txt_list:
            x, y, mag, img_size = read_metadata(os.path.join(folder, f'{name}.txt'))
            # SEMの記録ではy座標は下向きが正っぽい？
            data.append([name, x, y, mag, img_size])
        df_tmp = pd.DataFrame(data=data, columns=['name', 'x', 'y', 'mag', 'img_size'])
        df_tmp.set_index('name', inplace=True)
        df_tmp.sort_values(by=["mag"], ascending=True, inplace=True)

        dict_df[i] = SemData(i, folder, df_tmp)

    return dict_df
