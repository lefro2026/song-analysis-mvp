import streamlit as st
from analysis import analyze_audio_file
from plotter import create_volume_plot, create_pitch_plot

st.set_page_config(page_title="Song Analysis MVP", layout="centered")

# ===== CSS =====
st.markdown("""
<style>
/* 全体の余白を少し整える */
.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
}

/* 解析ボタンを目立たせる */
div.stButton > button {
    background: linear-gradient(90deg, #2563eb, #1d4ed8);
    color: white;
    font-weight: 700;
    font-size: 1.1rem;
    border: none;
    border-radius: 12px;
    padding: 0.85rem 1rem;
    box-shadow: 0 4px 14px rgba(37, 99, 235, 0.25);
    transition: all 0.2s ease-in-out;
}

div.stButton > button:hover {
    background: linear-gradient(90deg, #1d4ed8, #1e40af);
    transform: translateY(-1px);
    box-shadow: 0 6px 18px rgba(37, 99, 235, 0.35);
}

div.stButton > button:focus {
    outline: none;
    box-shadow: 0 0 0 0.2rem rgba(37, 99, 235, 0.25);
}

/* アップロード欄を少し強調 */
section[data-testid="stFileUploader"] {
    border: 1px solid rgba(100, 116, 139, 0.25);
    border-radius: 14px;
    padding: 0.5rem;
    background: #fafafa;
}

/* 補助説明用のカード */
.help-card {
    background: #f8fafc;
    border: 1px solid rgba(148, 163, 184, 0.25);
    border-radius: 14px;
    padding: 1rem 1rem 0.7rem 1rem;
    margin-top: 0.5rem;
    margin-bottom: 1rem;
}

.help-title {
    font-size: 1rem;
    font-weight: 700;
    margin-bottom: 0.3rem;
    color: #1e3a8a;
}

/* セクション見出しの余白 */
.section-title {
    margin-top: 1.2rem;
    margin-bottom: 0.4rem;
    font-weight: 700;
    font-size: 1.1rem;
}
</style>
""", unsafe_allow_html=True)

# ===== Header =====
st.title("Song Analysis MVP")
st.write("アカペラ音声をアップロードすると、全区間を簡易解析できます。")
st.info("使い方: 録音した wav / m4a をアップロードして「解析する」を押してください。")
st.caption("対応形式: wav / m4a | 分析可能時間: 0〜5分 | アカペラ推奨")

# ===== Upload area =====
st.markdown('<div class="section-title">音声ファイルをアップロードしてください</div>', unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    label="",
    type=["wav", "m4a"],
    label_visibility="collapsed"
)

# ===== Main action =====
analyze_button = st.button("解析する", use_container_width=True)

# ===== Help area =====
st.markdown(
    """
    <div class="help-card">
        <div class="help-title">アップロード方法がわからない場合</div>
        <div>iPhone / Android で録音した音声をアップロードする手順を確認できます。</div>
    </div>
    """,
    unsafe_allow_html=True
)

with st.expander("iPhone / Android からアップロードする方法"):
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

# ===== Analyze =====
if analyze_button:
    if uploaded_file is None:
        st.error("音声ファイルをアップロードしてください。")
    else:
        try:
            with st.spinner("解析中です..."):
                result = analyze_audio_file(uploaded_file)

            st.success("解析が完了しました。")

            st.write("## 結果")

            col1, col2 = st.columns(2)
            col3, col4 = st.columns(2)

            with col1:
                st.metric("最高音", result["max_pitch_note"])
            with col2:
                st.metric("平均音高", result["mean_pitch_note"])
            with col3:
                st.metric("高音維持時間", f'{result["high_pitch_duration"]:.2f} 秒')
            with col4:
                st.metric("高音割合", f'{result["high_pitch_ratio"] * 100:.1f}%')

            st.write("### この音声の傾向")
            st.write(result["comment"])

            st.write("### 音量の推移")
            st.caption("録音中の音の強さの変化です。絶対的な声量評価ではなく、流れを見るための参考です。")
            volume_fig = create_volume_plot(result["times_rms"], result["rms"])
            st.pyplot(volume_fig)

            st.write("### 音高の推移")
            st.caption("時間ごとの音の高さの変化です。高い音がどこで出ているかを確認できます。")
            pitch_fig = create_pitch_plot(
                result["times_f0"],
                result["f0"],
                result["pitch_tick_values"],
                result["pitch_tick_labels"],
            )
            st.pyplot(pitch_fig)

            with st.expander("詳細値を見る"):
                st.write(f'サンプリング周波数: {result["sr"]} Hz')
                st.write(f'分析前の長さ: {result["analyzed_duration"]:.2f} 秒')
                st.write(f'静音除去後の長さ: {result["trimmed_duration"]:.2f} 秒')
                st.write(f'最高音Hz: {result["max_pitch_hz"]:.2f}')
                st.write(f'平均音高Hz: {result["mean_pitch_hz"]:.2f}')
                st.write(
                    f'高音しきい値: {result["high_pitch_threshold_note"]} '
                    f'({result["high_pitch_threshold_hz"]:.2f} Hz)'
                )

        except Exception:
            st.error("解析に失敗しました。対応形式は wav / m4a、長さは5分以内か確認してください。")
