import os
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
from reader import read_metadata_in_folders
from viewer import Viewer


class HomeWindow(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.master.title('SEMView')
        self.create_widgets()

    def create_widgets(self):
        self.folders_var = tk.StringVar()
        self.dir = os.getcwd()
        self.padx = 10
        self.pady = 10
        self.num_folders = 0

        self.button_add_folder = tk.Button(self.master, text='追加', command=self.add_folder, activeforeground='red', relief=tk.RAISED)
        self.list_folder = tk.Listbox(self.master, listvariable=self.folders_var, width=80)
        self.list_folder.bind('<<ListboxSelect>>', self.delete_folder)
        self.button_view = tk.Button(self.master, text='実行', command=self.view, activeforeground='red', relief=tk.RAISED)

        self.button_add_folder.pack(pady=self.pady)
        self.list_folder.pack(padx=self.padx)
        self.button_view.pack(pady=self.pady)

    def view(self):
        if self.num_folders == 0:
            messagebox.showerror('Sorry', '1つ以上のフォルダを選択してください')
        else:
            # 選択したフォルダ内のtxtデータを読み込み
            self.list_view = [self.list_folder.get(i) for i in range(self.num_folders)]
            self.dict_df = read_metadata_in_folders(self.list_view)
            # ウィンドウ作成
            self.root_view = tk.Toplevel(self)
            self.notebook = ttk.Notebook(self.root_view)
            for value in self.dict_df.values():
                self.tab_tmp = tk.Frame(master=self.notebook)
                self.frame_tmp = Viewer(master=self.tab_tmp, dir=value.dir, df=value.df)
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


if __name__ == '__main__':
    root = tk.Tk()
    app_home = HomeWindow(master=root)
    app_home.mainloop()
