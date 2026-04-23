# Song Analysis MVP

アカペラのサビ区間を簡易解析するWebアプリです。

## 機能
- 音声ファイルアップロード
- 開始秒・終了秒の指定
- 音量の推移グラフ
- 音高の推移グラフ
- 最高音
- 平均音高
- 高音維持時間
- 高音割合
- 簡易コメント

## 想定入力
- アカペラ音声
- 30秒〜1分程度
- サビ区間

## 起動方法

```bash
pip install -r requirements.txt
streamlit run app.py