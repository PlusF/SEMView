# SEMView
Viewer for SEM Images

### 必要なライブラリ
* pandas
* pillow
### 使い方
1. Pythonの環境構築をし，pipで上記ライブラリをインストール．
2. SEMView.pyとfunc.pyが同じディレクトリにあることを確認して，SEMView.pyを実行．
3. 以下のような画面が表示される．`追加`から見たいフォルダを選択し，`実行`．
![img.png](img.png)
4. 左側にSEM像の位置，大きさが表示される．スケールバーは信用しないでください．
5. 右クリックで原点設定（緑になる）できて，左クリックした像（赤くなる）の相対座標が出る．
![img_1.png](img_1.png)