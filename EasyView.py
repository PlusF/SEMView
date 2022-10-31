import func
import os
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox


class EasyHomeWindow(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.master.title('EasySEMView')
        self.create_widgets()

    def create_widgets(self):
        self.folders_var = tk.StringVar()
        self.dir = os.getcwd()
        self.padx = 10
        self.pady = 5
        self.num_folders = 0

        self.button_add_folder = tk.Button(self.master, text='追加', command=self.add_folder, activeforeground='red', relief=tk.RAISED)
        self.list_folder = tk.Listbox(self.master, listvariable=self.folders_var, width=50, justify=tk.LEFT)
        self.list_folder.bind('<<ListboxSelect>>', self.delete_folder)
        self.label_size_pixel = tk.Label(self.master, text='画像サイズ [px]：')
        self.x_pixel = tk.IntVar(value=1280)
        self.y_pixel = tk.IntVar(value=960)
        self.entry_x_pixel = tk.Entry(self.master, textvariable=self.x_pixel, width=10)
        self.label_cross_pixel = tk.Label(self.master, text='x')
        self.entry_y_pixel = tk.Entry(self.master, textvariable=self.y_pixel, width=10)
        self.button_view = tk.Button(self.master, text='実行', command=self.view, activeforeground='red', relief=tk.RAISED)

        self.button_add_folder.grid(row=0, column=0, columnspan=4, pady=self.pady)
        self.list_folder.grid(row=1, column=0, columnspan=4, pady=self.pady)
        self.label_size_pixel.grid(row=2, column=0, pady=self.pady)
        self.entry_x_pixel.grid(row=2, column=1, pady=self.pady)
        self.label_cross_pixel.grid(row=2, column=2, pady=self.pady)
        self.entry_y_pixel.grid(row=2, column=3, pady=self.pady)
        self.button_view.grid(row=4, column=0, columnspan=4, pady=self.pady)

    def view(self):
        if self.num_folders == 0:
            messagebox.showerror('Sorry', '1つ以上のフォルダを選択してください')
        else:
            # 選択したフォルダ内のtxtデータを読み込み
            list_view = [self.list_folder.get(i) for i in range(self.num_folders)]
            pixel = (self.x_pixel.get(), self.y_pixel.get())
            dict_df = func.read_txt(list_view)
            # ウィンドウ作成
            self.root_view = tk.Toplevel(self)
            self.notebook = ttk.Notebook(self.root_view)
            for value in dict_df.values():
                self.tab_tmp = tk.Frame(master=self.notebook)
                self.frame_tmp = func.EasyViewer(master=self.tab_tmp, dir=value.dir, df=value.df, pixel=pixel)
                self.notebook.add(self.tab_tmp, text=value.dir[value.dir.rfind(os.sep)+1:])
            self.notebook.pack()

    def add_folder(self):
        # カレントディレクトリからフォルダ検索
        fld = filedialog.askdirectory(initialdir=self.dir)
        self.list_folder.insert(tk.END, fld)
        # 選択したフォルダのあるディレクトリに移動
        slash_index = fld[:-1].rfind('/')
        self.dir = fld[:slash_index+1]
        self.num_folders += 1

    def delete_folder(self, event):
        idx = self.list_folder.curselection()[0]
        ret = messagebox.askyesno('確認', 'リストからこのフォルダを削除しますか？')
        if ret:
            self.list_folder.delete(idx)
            self.num_folders -= 1


if __name__ == '__main__':
    root = tk.Tk()
    app_home = EasyHomeWindow(master=root)
    app_home.mainloop()
