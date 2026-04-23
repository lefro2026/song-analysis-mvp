import streamlit as st
from analysis import analyze_audio_file
from plotter import create_volume_plot, create_pitch_plot

st.set_page_config(page_title="Song Analysis MVP", layout="wide")

st.title("Song Analysis MVP")
st.write("アカペラのサビ区間を簡易解析します。")

uploaded_file = st.file_uploader(
    "音声ファイルをアップロードしてください(wav / m4a)",
    type=["wav", "m4a"]
)

col1, col2 = st.columns(2)
with col1:
    start_sec = st.number_input("開始秒", min_value=0.0, value=0.0, step=1.0)
with col2:
    end_sec = st.number_input("終了秒", min_value=1.0, value=30.0, step=1.0)

analyze_button = st.button("解析する")

if analyze_button:
    if uploaded_file is None:
        st.error("音声ファイルをアップロードしてください。")
    elif end_sec <= start_sec:
        st.error("終了秒は開始秒より大きくしてください。")
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
                st.write(f'解析区間: {result["analyzed_duration"]:.2f} 秒')
                st.write(f'最高音Hz: {result["max_pitch_hz"]:.2f}')
                st.write(f'平均音高Hz: {result["mean_pitch_hz"]:.2f}')
                st.write(f'高音しきい値: {result["high_pitch_threshold_note"]} ({result["high_pitch_threshold_hz"]:.2f} Hz)')

        except Exception as e:
            st.error(f"解析中にエラーが発生しました: {e}")
