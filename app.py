import streamlit as st
from analysis import analyze_audio_file
from plotter import create_volume_plot, create_pitch_plot

st.set_page_config(page_title="Song Analysis MVP", layout="wide")

st.title("Song Analysis MVP")
st.write("アカペラ音声を全区間で簡易解析します。")
st.caption("対応形式: wav / m4a、分析可能時間: 0〜5分")

with st.expander("アップロード方法を見る"):
    st.markdown("""
### iPhoneからアップロードする方法
1. **ボイスメモ**で録音する  
2. 録音を開いて**共有**を押す  
3. **ファイルに保存**を選ぶ  
4. このアプリでそのファイルをアップロードする  

### Androidからアップロードする方法
1. 端末の**録音アプリ**で録音する  
2. 録音一覧から対象ファイルを開く  
3. **共有**を押す  
4. ファイルとして保存するか、このアプリにアップロードする  

※ Androidは機種によって録音アプリ名が異なります  
例: Pixel = Recorder、Galaxy = Voice Recorder
""")

uploaded_file = st.file_uploader(
    "音声ファイルをアップロードしてください（wav / m4a）",
    type=["wav", "m4a"]
)

analyze_button = st.button("解析する")

if analyze_button:
    if uploaded_file is None:
        st.error("音声ファイルをアップロードしてください。")
    else:
        try:
            with st.spinner("解析中です..."):
                result = analyze_audio_file(uploaded_file)

            st.success("解析が完了しました。")

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("最高音", result["max_pitch_note"])
            col2.metric("平均音高", result["mean_pitch_note"])
            col3.metric("高音維持時間", f'{result["high_pitch_duration"]:.2f} 秒')
            col4.metric("高音割合", f'{result["high_pitch_ratio"] * 100:.1f}%')

            st.write("### コメント")
            st.write(result["comment"])

            st.write("### 音量の推移")
            volume_fig = create_volume_plot(result["times_rms"], result["rms"])
            st.pyplot(volume_fig)

            st.write("### 音高の推移")
            pitch_fig = create_pitch_plot(
                result["times_f0"],
                result["f0"],
                result["pitch_tick_values"],
                result["pitch_tick_labels"],
            )
            st.pyplot(pitch_fig)

            with st.expander("詳細値を見る"):
                st.write(f'サンプリング周波数: {result["sr"]} Hz')
                st.write(f'分析時間: {result["analyzed_duration"]:.2f} 秒')
                st.write(f'静音除去後の長さ: {result["trimmed_duration"]:.2f} 秒')
                st.write(f'最高音Hz: {result["max_pitch_hz"]:.2f}')
                st.write(f'平均音高Hz: {result["mean_pitch_hz"]:.2f}')
                st.write(
                    f'高音しきい値: {result["high_pitch_threshold_note"]} '
                    f'({result["high_pitch_threshold_hz"]:.2f} Hz)'
                )

        except Exception as e:
            st.error(f"解析中にエラーが発生しました: {e}")
