import os
import math
import pandas as pd
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from PIL import Image, ImageTk, ImageEnhance
from dataclasses import dataclass


# リスト内のフォルダにあるテキストファイルを読み込み、DataFrameに格納、まとめる
def read_txt(list_folder):
    dict_df = {}
    for i, folder_path in enumerate(list_folder):
        folder_path = folder_path.strip('"')  # windowsの「パスをコピー」ボタンでは""がついてきてしまうため
        txt_list = []
        if folder_path == '':
            continue
        for name in os.listdir(folder_path):
            if '.txt' in name:
                txt_list.append(name[:-4])

        # txtファイルの中身を読み込み，データの成型
        data = []
        for name in txt_list:
            df_raw = pd.read_csv(os.path.join(folder_path, f'{name}.txt'))
            df_raw = df_raw['[SemImageFile]'].str.split('=', expand=True)
            df_raw.set_index(0, inplace=True)
            # SEMの記録ではy座標は下向きが正っぽい？
            data.append([name,
                         int(df_raw.loc['StagePositionX'][1]) / 1000000,
                         int(df_raw.loc['StagePositionY'][1]) / 1000000,
                         int(df_raw.loc['Magnification'][1])])
        df_tmp = pd.DataFrame(data=data, columns=['name', 'x', 'y', 'mag'])
        df_tmp.set_index('name', inplace=True)
        df_tmp.sort_values(by=["mag"], ascending=True, inplace=True)

        dict_df[i] = SemData(i, folder_path, df_tmp)

    return dict_df


# 座標、倍率データ格納用のクラス
@dataclass
class SemData:
    index: int
    dir: str
    df: pd.core.frame.DataFrame


# SEM像を見るためのウィンドウ
class Viewer(tk.Frame):
    def __init__(self, master=None, dir=None, df=None):
        super().__init__(master)
        self.master = master
        self.dir = dir
        self.df = df
        self.create_widgets()
        self.plot()

    def create_widgets(self):
        # 必要な変数の宣言
        self.width = 640
        self.height = 480
        self.rect_tag = tk.StringVar()
        self.std_rect_tag = None
        self.std_x = tk.DoubleVar()
        self.std_y = tk.DoubleVar()
        self.selected_x = tk.DoubleVar()
        self.selected_y = tk.DoubleVar()
        self.move_x_val = tk.DoubleVar()
        self.move_y_val = tk.DoubleVar()
        self.zoom_val = tk.DoubleVar()
        self.zoom_val.set(30)
        self.rotarion_val = tk.DoubleVar()
        self.scale_list = ['5mm', '2mm', '1mm', '500\u03bcm']
        self.brightness_val = tk.DoubleVar()
        self.brightness_val.set(50)
        self.contrast_val = tk.DoubleVar()
        self.contrast_val.set(50)

        # master内のwidget
        self.canvas = tk.Canvas(self.master, width=self.width, height=self.height, cursor='plus', bg='ivory', bd=3, relief=tk.RIDGE)  # 撮影した点をプロットする用
        self.frame_pro = tk.Frame(self.master, width=self.width, height=self.height / 2)  # 拡大，縮小，移動など
        self.canvas_img = tk.Canvas(self.master, width=self.width, height=self.height, cursor='circle', bd=3, relief=tk.RIDGE)  # 画像表示用
        self.frame_con = tk.Frame(self.master, width=self.width, height=self.height / 2)  # 明るさ，コントラスト調整用
        self.scale_move_x = tk.Scale(self.master, variable=self.move_x_val, command=self.draw, orient=tk.HORIZONTAL, length=self.width,
                                     resolution=0.1, from_=-2 * self.width, to_=2 * self.width, showvalue=False)
        self.scale_move_y = tk.Scale(self.master, variable=self.move_y_val, command=self.draw, orient=tk.VERTICAL, length=self.height, resolution=0.1,
                                     from_=-2 * self.height, to_=2 * self.height, showvalue=False)

        self.canvas.grid(row=0, column=0, padx=0, pady=0)
        self.scale_move_x.grid(row=1, column=0)
        self.scale_move_y.grid(row=0, column=1)
        self.frame_pro.grid(row=2, column=0, padx=0, pady=0)
        self.canvas_img.grid(row=0, column=2, padx=0, pady=0)
        self.frame_con.grid(row=2, column=2, padx=0, pady=0)

        # canvas内のwidget(図形)
        # 実際の長さとピクセルについて：5mmはself.zoom_val=30のとき150px，つまりy[px]=x[mm]*self.zoom_val
        self.canvas.create_rectangle(self.width - self.zoom_val.get() * 5, self.height - 20, self.width, self.height, tags='scale_bar', fill='white',
                                     width=2, state=tk.DISABLED)
        self.canvas.create_text(self.width - 50, self.height - 10, tags='scale_val', text=self.scale_list[0])

        # frame_pro内のwidget
        self.label_description = tk.Label(self.frame_pro, text='左クリックでSEM像表示\n右クリックで原点設定(相対座標用)')
        self.label_selected_x = tk.Label(self.frame_pro, text='相対座標(x): ')
        self.label_selected_y = tk.Label(self.frame_pro, text='相対座標(y): ')
        self.label_mm_origin_x = tk.Label(self.frame_pro, text='mm')
        self.label_mm_origin_y = tk.Label(self.frame_pro, text='mm')
        self.label_std_x = tk.Label(self.frame_pro, textvariable=self.selected_x)
        self.label_std_y = tk.Label(self.frame_pro, textvariable=self.selected_y)
        self.label_selected_name = tk.Label(self.frame_pro, text='ファイル名: ')
        self.label_selected_filename = tk.Label(self.frame_pro, textvariable=self.rect_tag)
        self.label_scale_zoom = tk.Label(self.frame_pro, text='拡大/縮小')
        self.scale_zoom = tk.Scale(self.frame_pro, variable=self.zoom_val, command=self.draw, orient=tk.HORIZONTAL, length=200, from_=3, to_=600,
                                   resolution=1, showvalue=False)
        self.button_reset_zoom = tk.Button(self.frame_pro, command=self.reset_zoom, text='Reset', activeforeground='red', relief=tk.RAISED)
        self.label_scale_rotate = tk.Label(self.frame_pro, text='回転')
        self.scale_rotate = tk.Scale(self.frame_pro, variable=self.rotarion_val, command=self.draw, orient=tk.HORIZONTAL, length=200, from_=-45,
                                     to_=45, resolution=0.1, showvalue=True)
        self.button_reset_rotation = tk.Button(self.frame_pro, command=self.reset_rotatation, text='Reset', activeforeground='red', relief=tk.RAISED)

        self.label_description.grid(row=0, column=1)
        self.label_scale_zoom.grid(row=1, column=0)
        self.scale_zoom.grid(row=1, column=1)
        self.button_reset_zoom.grid(row=1, column=2)
        self.label_scale_rotate.grid(row=2, column=0)
        self.scale_rotate.grid(row=2, column=1)
        self.button_reset_rotation.grid(row=2, column=2)
        self.label_selected_x.grid(row=3, column=0)
        self.label_selected_y.grid(row=4, column=0)
        self.label_std_x.grid(row=3, column=1)
        self.label_std_y.grid(row=4, column=1)
        self.label_mm_origin_x.grid(row=3, column=2)
        self.label_mm_origin_y.grid(row=4, column=2)
        self.label_selected_name.grid(row=5, column=0)
        self.label_selected_filename.grid(row=5, column=1)

        # frame_con内のwidget
        self.label_brightness = tk.Label(self.frame_con, text='Brightness')
        self.label_contrast = tk.Label(self.frame_con, text='Contrast')
        self.scale_brightness = tk.Scale(self.frame_con, variable=self.brightness_val, command=None, orient=tk.HORIZONTAL, length=self.width / 2,
                                         from_=1, to_=500, resolution=1, showvalue=False)
        self.scale_contrast = tk.Scale(self.frame_con, variable=self.contrast_val, command=None, orient=tk.HORIZONTAL, length=self.width / 2, from_=1,
                                       to_=500, resolution=1, showvalue=False)
        self.button_reload = tk.Button(self.frame_con, command=self.show_img, text='Reload', activeforeground='red', relief=tk.RAISED)

        self.label_brightness.grid(row=0, column=0)
        self.scale_brightness.grid(row=0, column=1)
        self.label_contrast.grid(row=1, column=0)
        self.scale_contrast.grid(row=1, column=1)
        self.button_reload.grid(row=2, column=1)

    # SEM画像の座標をプロット
    def plot(self):
        self.mean_x = self.df.x.mean()
        self.mean_y = self.df.y.mean()
        self.df_tmp = self.df.copy()
        for (index, item), (index_tmp, item_tmp) in zip(self.df.iterrows(), self.df_tmp.iterrows()):
            item_tmp.x = (item.x - self.mean_x) * self.zoom_val.get() + self.width / 2
            item_tmp.y = (item.y - self.mean_y) * self.zoom_val.get() + self.height / 2
            item_tmp.mag = 1 / item.mag * self.zoom_val.get() * 30  # 'mag'の列をサイズ情報で置換する
            # SEM像の範囲と同じ大きさの長方形を描画，1000倍で120um*90um（self.zoom_val=30で3.6px*2.7px）の像とする．
            self.canvas.create_rectangle(item_tmp.x, item_tmp.y, item_tmp.x + item_tmp.mag * 4, item_tmp.y + item_tmp.mag * 3, tags=index,
                                         fill='white', activeoutline='red')
            self.canvas.lift(index)
            self.canvas.tag_bind(index, '<Button-1>', self.select)
            self.canvas.tag_bind(index, '<Button-2>', self.set_std)
            self.canvas.tag_bind(index, '<Button-3>', self.set_std)
        self.canvas.lift('scale_bar')
        self.canvas.lift('scale_val')

    def select(self, event):
        self.pre_rect_tag = self.rect_tag.get()
        self.rect_tag.set(self.canvas.gettags(self.canvas.find_closest(event.x, event.y))[0])
        self.show_img()  # tif画像を表示
        # 回転処理
        tmp_x_0 = self.df.x[self.rect_tag.get()] - self.std_x.get()
        tmp_y_0 = self.df.y[self.rect_tag.get()] - self.std_y.get()
        tmp_theta = math.radians(self.rotarion_val.get())
        tmp_x = math.cos(tmp_theta) * tmp_x_0 - math.sin(tmp_theta) * tmp_y_0
        tmp_y = math.sin(tmp_theta) * tmp_x_0 + math.cos(tmp_theta) * tmp_y_0
        self.selected_x.set(round(tmp_x, 3))
        self.selected_y.set(-1 * round(tmp_y, 3))
        event.widget.itemconfig(self.pre_rect_tag, fill='white')
        event.widget.itemconfig(self.rect_tag.get(), fill='red')

    def show_img(self):
        self.canvas_img.delete('all')
        self.img = Image.open(os.path.join(self.dir, f'{self.rect_tag.get()}.tif'))
        self.img = self.brightness(self.img)
        self.img = self.contrast(self.img)
        self.img = self.img.resize((640, 480))
        self.img_show = ImageTk.PhotoImage(image=self.img)
        self.canvas_img.create_image(self.width / 2, self.height / 2, image=self.img_show)

    def set_std(self, event):
        self.pre_std_rect_tag = self.std_rect_tag
        self.std_rect_tag = self.canvas.gettags(self.canvas.find_closest(event.x, event.y))[0]
        self.std_x.set(self.df.x[self.std_rect_tag])
        self.std_y.set(self.df.y[self.std_rect_tag])
        event.widget.itemconfig(self.pre_std_rect_tag, fill='white')
        event.widget.itemconfig(self.std_rect_tag, fill='green')

    def draw(self, event):
        for (index, item), (index_tmp, item_tmp) in zip(self.df.iterrows(), self.df_tmp.iterrows()):
            # 平均値を基準にして拡大処理
            item_tmp.x = (item.x - self.mean_x) * self.zoom_val.get()
            item_tmp.y = (item.y - self.mean_y) * self.zoom_val.get()
            # 回転処理 θ [rad]
            tmp_theta = math.radians(self.rotarion_val.get())
            tmp_x = math.cos(tmp_theta) * item_tmp.x - math.sin(tmp_theta) * item_tmp.y
            tmp_y = math.sin(tmp_theta) * item_tmp.x + math.cos(tmp_theta) * item_tmp.y
            # 移動処理と描画用の座標に補正
            tmp_x += self.width / 2 - self.move_x_val.get()
            tmp_y += self.height / 2 - self.move_y_val.get()
            item_tmp.mag = 1 / item.mag * self.zoom_val.get() * 30
            self.canvas.coords(index, tmp_x, tmp_y, tmp_x + item_tmp.mag * 4, tmp_y + item_tmp.mag * 3)
        self.zoom_scale_bar()

    def reset_rotatation(self):
        self.rotarion_val.set(0)
        self.draw(None)

    def zoom_scale_bar(self):
        tmp_zoom_val = self.zoom_val.get()
        if 3 <= tmp_zoom_val < 75:
            self.canvas.coords('scale_bar', self.width - tmp_zoom_val * 5, self.height - 20, self.width, self.height)
            self.canvas.itemconfigure('scale_val', text=self.scale_list[0])
        elif 75 <= tmp_zoom_val < 150:
            self.canvas.coords('scale_bar', self.width - tmp_zoom_val * 2, self.height - 20, self.width, self.height)
            self.canvas.itemconfigure('scale_val', text=self.scale_list[1])
        elif 150 <= tmp_zoom_val < 300:
            self.canvas.coords('scale_bar', self.width - tmp_zoom_val * 1, self.height - 20, self.width, self.height)
            self.canvas.itemconfigure('scale_val', text=self.scale_list[2])
        elif 300 <= tmp_zoom_val < 600:
            self.canvas.coords('scale_bar', self.width - tmp_zoom_val * 0.5, self.height - 20, self.width, self.height)
            self.canvas.itemconfigure('scale_val', text=self.scale_list[3])

    def reset_zoom(self):
        self.move_x_val.set(0)
        self.move_y_val.set(0)
        self.zoom_val.set(30)
        self.draw(None)

    def brightness(self, img):
        self.brightness_val.set(self.scale_brightness.get())
        img_enhancer = ImageEnhance.Brightness(img)
        enhanced_img = img_enhancer.enhance(self.brightness_val.get() * 0.02)
        return enhanced_img

    def contrast(self, img):
        self.contrast_val.set(self.scale_contrast.get())
        img_enhancer = ImageEnhance.Contrast(img)
        enhanced_img = img_enhancer.enhance(self.contrast_val.get() * 0.02)
        return enhanced_img


class EasyViewer(tk.Frame):
    def __init__(self, master=None, dir=None, df=None, pixel=(1280, 960)):
        super().__init__(master)
        self.master = master
        self.dir = dir
        self.df = df
        self.pixel = pixel  # px
        self.create_widgets()
        self.show_img()

    def create_widgets(self):
        # 必要な変数の宣言
        self.width = self.pixel[0]
        self.height = self.pixel[1]
        self.rect_tag = tk.StringVar()
        self.std_rect_tag = None
        self.std_x = tk.DoubleVar()
        self.std_y = tk.DoubleVar()
        self.selected_x = tk.DoubleVar()
        self.selected_y = tk.DoubleVar()
        self.move_x_val = tk.DoubleVar()
        self.move_y_val = tk.DoubleVar()
        self.zoom_val = tk.DoubleVar()
        self.zoom_val.set(30)
        self.rotarion_val = tk.DoubleVar()
        self.scale_list = ['5mm', '2mm', '1mm', '500\u03bcm']
        self.brightness_val = tk.DoubleVar()
        self.brightness_val.set(50)
        self.contrast_val = tk.DoubleVar()
        self.contrast_val.set(50)

        # master内のwidget
        self.canvas_img = tk.Canvas(self.master, width=self.width, height=self.height, cursor='circle', bd=3, relief=tk.RIDGE)  # 画像表示用
        self.frame_con = tk.Frame(self.master, width=self.width, height=self.height / 2)  # 明るさ，コントラスト調整用
        self.canvas_img.grid(row=1, column=0, padx=0, pady=0)
        self.frame_con.grid(row=0, column=0, padx=0, pady=0)

        # frame_con内のwidget
        self.label_brightness = tk.Label(self.frame_con, text='Brightness')
        self.label_contrast = tk.Label(self.frame_con, text='Contrast')
        self.scale_brightness = tk.Scale(self.frame_con, variable=self.brightness_val, command=None, orient=tk.HORIZONTAL, length=self.width / 2,
                                         from_=1, to_=500, resolution=1, showvalue=False)
        self.scale_contrast = tk.Scale(self.frame_con, variable=self.contrast_val, command=None, orient=tk.HORIZONTAL, length=self.width / 2, from_=1,
                                       to_=500, resolution=1, showvalue=False)
        self.button_show = tk.Button(self.frame_con, command=self.show_img, text='Show', activeforeground='red', relief=tk.RAISED)
        self.button_save = tk.Button(self.frame_con, command=self.save, text='Save', relief=tk.RAISED)

        self.label_brightness.grid(row=1, column=0)
        self.scale_brightness.grid(row=1, column=1)
        self.label_contrast.grid(row=2, column=0)
        self.scale_contrast.grid(row=2, column=1)
        self.button_show.grid(row=0, column=0)
        self.button_save.grid(row=0, column=1)

    def show_img(self):
        self.canvas_img.delete('all')

        size = {'x': 126, 'y': 95}  # 1倍でとったときのtif画像のサイズ[mm]
        self.img = Image.new('RGB', self.pixel)
        x0, y0 = self.df.x.min(), self.df.y.min()
        x1, y1 = max(self.df.x + size['x'] / self.df.mag), max(self.df.y + size['y'] / self.df.mag)
        mag = min(self.pixel[0] / (x1 - x0), self.pixel[1] / (y1 - y0))
        for name, info in self.df.iterrows():
            x = info.x  # um
            y = info.y  # um
            x_um = size['x'] / info.mag
            y_um = size['y'] / info.mag
            tiffile = os.path.join(self.dir, f'{name}.tif')
            if int(x_um * mag) <= 0 or int(y_um * mag) <= 0:
                messagebox.showerror('Error', 'Resolution is too low. Please specify higher resolution.')
                return
            img_tmp = Image.open(tiffile).resize((int(x_um * mag), int(y_um * mag)))
            self.img.paste(img_tmp, (int((x - x0) * mag), int((y - y0) * mag)))

        self.img = self.brightness(self.img)
        self.img = self.contrast(self.img)
        self.img = self.img.resize((self.pixel[0], self.pixel[1]))
        self.img_show = ImageTk.PhotoImage(image=self.img)
        self.canvas_img.create_image(self.width / 2, self.height / 2, image=self.img_show)

    def brightness(self, img):
        self.brightness_val.set(self.scale_brightness.get())
        img_enhancer = ImageEnhance.Brightness(img)
        enhanced_img = img_enhancer.enhance(self.brightness_val.get() * 0.02)
        return enhanced_img

    def contrast(self, img):
        self.contrast_val.set(self.scale_contrast.get())
        img_enhancer = ImageEnhance.Contrast(img)
        enhanced_img = img_enhancer.enhance(self.contrast_val.get() * 0.02)
        return enhanced_img

    def save(self):
        filename = filedialog.asksaveasfilename(filetypes=[("Bitmap", ".bmp"), ("PNG", ".png"), ("JPEG", ".jpg"), ("Tiff", ".tif")])
        self.img.save(filename)
