import os
import math
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
import numpy as np
import pandas as pd
from PIL import Image, ImageTk, ImageEnhance


# SEM像を見るためのウィンドウ
class Viewer(tk.Frame):
    def __init__(self, master, dir: str, df: pd.DataFrame):
        super().__init__(master)
        self.master = master
        self.dir = dir
        self.df = df
        self.filenames = sorted(list(self.df.index))
        self.center_x = self.df.x.mean()
        self.center_y = self.df.y.mean()
        self.zoom_org_x = self.center_x
        self.zoom_org_y = self.center_y
        self.create_widgets()
        self.bind_events()
        self.initial_draw()

    def create_widgets(self):
        # 必要な変数の宣言
        self.width = 640
        self.height = 480
        self.selected_tag = tk.StringVar()
        self.std_rect_tag = None
        self.std_x = 0
        self.std_y = 0
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
        self.label_selected_filename = tk.Label(self.frame_pro, textvariable=self.selected_tag)
        self.label_scale_zoom = tk.Label(self.frame_pro, text='拡大/縮小')
        self.scale_zoom = tk.Scale(self.frame_pro, variable=self.zoom_val, command=self.draw, orient=tk.HORIZONTAL, length=200, from_=3, to_=600,
                                   resolution=1, showvalue=False)
        self.button_reset_zoom = tk.Button(self.frame_pro, command=self.reset_zoom, text='Reset', activeforeground='red', relief=tk.RAISED)
        self.label_scale_rotate = tk.Label(self.frame_pro, text='回転')
        self.scale_rotate = tk.Scale(self.frame_pro, variable=self.rotarion_val, command=self.draw, orient=tk.HORIZONTAL, length=200, from_=-45,
                                     to_=45, resolution=0.1, showvalue=True)
        self.button_reset_rotation = tk.Button(self.frame_pro, command=self.reset_rotation, text='Reset', activeforeground='red', relief=tk.RAISED)

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
        self.button_brightness_down = tk.Button(self.frame_con, command=lambda: self.change_brightness(-1), text='-', relief=tk.RAISED)
        self.scale_brightness = tk.Scale(self.frame_con, variable=self.brightness_val, command=None, orient=tk.HORIZONTAL, length=self.width / 2,
                                         from_=1, to_=500, resolution=1, showvalue=False)
        self.scale_brightness.bind('<ButtonRelease-1>', self.show_img)
        self.button_brightness_up = tk.Button(self.frame_con, command=lambda: self.change_brightness(1), text='+', relief=tk.RAISED)
        self.button_contrast_down = tk.Button(self.frame_con, command=lambda: self.change_contrast(-1), text='-', relief=tk.RAISED)
        self.scale_contrast = tk.Scale(self.frame_con, variable=self.contrast_val, command=None, orient=tk.HORIZONTAL, length=self.width / 2, from_=1,
                                       to_=500, resolution=1, showvalue=False)
        self.button_contrast_up = tk.Button(self.frame_con, command=lambda: self.change_contrast(1), text='+', relief=tk.RAISED)
        self.scale_contrast.bind('<ButtonRelease-1>', self.show_img)

        self.label_brightness.grid(row=0, column=0)
        self.button_brightness_down.grid(row=0, column=1)
        self.scale_brightness.grid(row=0, column=2)
        self.button_brightness_up.grid(row=0, column=3)
        self.label_contrast.grid(row=1, column=0)
        self.button_contrast_down.grid(row=1, column=1)
        self.scale_contrast.grid(row=1, column=2)
        self.button_contrast_up.grid(row=1, column=3)

    def bind_events(self):
        # スクロール関係
        self.master.master.master.bind("<MouseWheel>", self.mouse_y_scroll)
        self.master.master.master.bind("<Shift-MouseWheel>", self.mouse_x_scroll)
        self.master.master.master.bind("<Control-MouseWheel>", self.mouse_zoom)
        # キー関係
        self.master.master.master.bind("<KeyPress>", self.press_key)

    def press_key(self, event):
        if event.keysym == 'a':
            self.move_x_val.set(self.move_x_val.get() - 20)
            self.draw()
        elif event.keysym == 'd':
            self.move_x_val.set(self.move_x_val.get() + 20)
            self.draw()
        elif event.keysym == 'w':
            self.move_y_val.set(self.move_y_val.get() - 20)
            self.draw()
        elif event.keysym == 's':
            self.move_y_val.set(self.move_y_val.get() + 20)
            self.draw()
        elif event.keysym == 'r':
            self.reset_zoom()
            self.reset_rotation()
        elif event.keysym in ['Right', 'Down']:
            index = self.filenames.index(self.selected_tag.get())
            next_index = index + 1 if index < len(self.filenames) - 1 else 0
            next_tag = self.filenames[next_index]
            self.select_rect_by_tag(next_tag)
        elif event.keysym in ['Left', 'Up']:
            index = self.filenames.index(self.selected_tag.get())
            pre_index = index - 1
            pre_tag = self.filenames[pre_index]
            self.select_rect_by_tag(pre_tag)

    # SEM画像の座標をプロット
    def initial_draw(self):
        for index, item in self.df.iterrows():
            x = (item.x - self.center_x) * self.zoom_val.get() + self.width / 2
            y = (item.y - self.center_y) * self.zoom_val.get() + self.height / 2
            img_size = item.img_size * self.zoom_val.get()
            tag = str(index)
            self.canvas.create_rectangle(x, y, x + img_size[0], y + img_size[1], tags=tag,
                                         fill='white', activeoutline='red')
            self.canvas.lift(tag)
            self.canvas.tag_bind(tag, '<Button-1>', self.get_select_rect_by_tag(tag))
            self.canvas.tag_bind(tag, '<Button-2>', self.set_std)
            self.canvas.tag_bind(tag, '<Button-3>', self.set_std)
        self.canvas.lift('scale_bar')
        self.canvas.lift('scale_val')
        self.select_rect_by_tag(self.filenames[0])

    def get_select_rect_by_tag(self, tag):
        return lambda e: self.select_rect_by_tag(tag)

    def select_rect_by_tag(self, tag):
        pre_tag = self.selected_tag.get()
        if pre_tag == self.std_rect_tag:
            self.canvas.itemconfig(pre_tag, fill='green')
        else:
            self.canvas.itemconfig(pre_tag, fill='white')
        self.selected_tag.set(tag)
        self.canvas.itemconfig(tag, fill='red')
        self.show_img()
        self.calc_coord()
        self.zoom_org_x = self.df.x[tag] - self.center_x
        self.zoom_org_y = self.df.y[tag] - self.center_y
        # scrollの位置を調整する
        if pre_tag == '':  # 初回
            dx = self.center_x - self.df.x[tag]
            dy = self.center_y - self.df.y[tag]
        else:
            dx = self.df.x[pre_tag] - self.df.x[tag]
            dy = self.df.y[pre_tag] - self.df.y[tag]
        self.move_x_val.set(self.move_x_val.get() + dx * self.zoom_val.get())
        self.move_y_val.set(self.move_y_val.get() + dy * self.zoom_val.get())

    def calc_coord(self):
        # 回転処理
        x = self.df.x[self.selected_tag.get()] - self.std_x
        y = self.df.y[self.selected_tag.get()] - self.std_y
        x, y = self.calc_rot(x, y)
        self.selected_x.set(round(x, 3))
        self.selected_y.set(-1 * round(y, 3))

    def calc_rot(self, x, y):
        theta = math.radians(self.rotarion_val.get())
        rot_matrix = np.array(
            [
                [math.cos(theta), -1 * math.sin(theta)],
                [math.sin(theta), math.cos(theta)]
            ])
        x, y = np.dot(rot_matrix, np.array([x, y]))
        return x, y

    def mouse_x_scroll(self, event):
        if event.delta > 0:
            self.move_x_val.set(self.move_x_val.get() - 20)
        elif event.delta < 0:
            self.move_x_val.set(self.move_x_val.get() + 20)
        self.draw()

    def mouse_y_scroll(self, event):
        if event.delta > 0:
            self.move_y_val.set(self.move_y_val.get() - 20)
        elif event.delta < 0:
            self.move_y_val.set(self.move_y_val.get() + 20)
        self.draw()

    def mouse_zoom(self, event):
        if event.delta > 0:
            self.zoom_val.set(self.zoom_val.get() * 1.1)
        elif event.delta < 0:
            self.zoom_val.set(self.zoom_val.get() * 1/1.1)
        self.draw()

    def show_img(self, event=None):
        if self.selected_tag.get() == '':
            return
        self.canvas_img.delete('all')
        img = Image.open(os.path.join(self.dir, f'{self.selected_tag.get()}.tif'))
        img = self.brightness(img)
        img = self.contrast(img)
        img = img.resize((640, 480))
        self.img_show = ImageTk.PhotoImage(image=img)
        self.canvas_img.create_image(self.width / 2, self.height / 2, image=self.img_show)

    def set_std(self, event):
        event.widget.itemconfig(self.std_rect_tag, fill='white')
        self.std_rect_tag = self.canvas.gettags(self.canvas.find_closest(event.x, event.y)[0])[0]
        self.std_x = self.df.x[self.std_rect_tag]
        self.std_y = self.df.y[self.std_rect_tag]
        event.widget.itemconfig(self.std_rect_tag, fill='green')

    def draw(self, event=None):
        for index, item in self.df.iterrows():
            # 全体の中心を基準に
            x = item.x - self.center_x
            y = item.y - self.center_y
            # 回転処理 θ [rad]
            x, y = self.calc_rot(x, y)
            # 選択中の場所を中心に拡大縮小
            x = (x - self.zoom_org_x) * self.zoom_val.get() + self.zoom_org_x
            y = (y - self.zoom_org_y) * self.zoom_val.get() + self.zoom_org_y
            # 移動処理と描画用の座標に補正
            x += self.width / 2 - self.move_x_val.get()
            y += self.height / 2 - self.move_y_val.get()
            img_size = item.img_size * self.zoom_val.get()
            self.canvas.coords(str(index), x, y, x + img_size[0], y + img_size[1])
        self.zoom_scale_bar()
        self.calc_coord()

    def reset_rotation(self):
        self.rotarion_val.set(0)
        self.draw()

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
        self.draw()

    def change_brightness(self, val):
        self.brightness_val.set(self.scale_brightness.get() + val)
        self.show_img()

    def brightness(self, img):
        self.brightness_val.set(self.scale_brightness.get())
        img_enhancer = ImageEnhance.Brightness(img)
        enhanced_img = img_enhancer.enhance(self.brightness_val.get() * 0.02)
        return enhanced_img

    def change_contrast(self, val):
        self.contrast_val.set(self.scale_contrast.get() + val)
        self.show_img()

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
        img = Image.new('RGB', self.pixel)
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
            img.paste(img_tmp, (int((x - x0) * mag), int((y - y0) * mag)))

        img = self.brightness(img)
        img = self.contrast(img)
        self.img = img.resize((self.pixel[0], self.pixel[1]))
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
