import streamlit as st
from analysis import analyze_audio_file, get_key_profile
from plotter import create_volume_plot, create_pitch_plot

st.set_page_config(
    page_title="Song Analysis MVP",
    page_icon="icon.png",
    layout="centered"
)

if "is_analyzing" not in st.session_state:
    st.session_state.is_analyzing = False

if "run_analysis" not in st.session_state:
    st.session_state.run_analysis = False

if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None

if "analysis_error" not in st.session_state:
    st.session_state.analysis_error = None


if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0


st.markdown("""
<style>
            

/* ===== 通常(ライトモード) ===== */

.metric-label {
    color: #64748b;
}

.metric-value {
    color: #0f172a;
}

.settings-guide {
    background: #eef6ff;
    color: #0f172a;
    border: 1px solid #93c5fd;
}

/* ===== ダークモード時のみ変更 ===== */

@media (prefers-color-scheme: dark) {


    .settings-guide {
        background: #0f172a !important;
        color: #e2e8f0 !important;
        border: 1px solid #3b82f6 !important;
    }

    .sub-text,
    .stCaption,
    p {
        color: #cbd5e1 !important;
    }

    .comment-box {
        background: #111827 !important;
        color: #f8fafc !important;
    }

}
            

.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 900px;
}

h1 {
    font-size: 3rem !important;
    font-weight: 800 !important;
}

.section-title {
    font-size: 1.55rem;
    font-weight: 800;
    margin-top: 1.4rem;
    margin-bottom: 0.5rem;
}

.sub-text {
    color: #64748b;
    font-size: 0.95rem;
    margin-bottom: 0.5rem;
}

@keyframes fadeSlideIn {
    from {
        opacity: 0;
        transform: translateY(14px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.animated-panel {
    animation: fadeSlideIn 0.45s ease-out;
}

[data-testid="stFileUploader"] {
    background: #fff8dc !important;
    border: 3px dashed #f59e0b !important;
    border-radius: 22px !important;
    padding: 24px !important;
    margin-top: 10px !important;
    margin-bottom: 10px !important;
}

[data-testid="stFileUploader"] button {
    background: linear-gradient(90deg, #f59e0b, #ea580c) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 800 !important;
    padding: 12px 24px !important;
    font-size: 18px !important;
    box-shadow: 0 8px 18px rgba(245,158,11,0.28) !important;
}


/* 通常ライトモード */
.settings-guide {
    background: #eef6ff;
    color: #0f172a;
    border: 1px solid #93c5fd;
    border-radius: 16px;
    padding: 0.95rem 1rem;
    margin-top: 1rem;
    margin-bottom: 0.6rem;
}

/* ダークモード時のみ変更 */
@media (prefers-color-scheme: dark) {
    .settings-guide {
        background: #06163a !important;
        color: #f8fafc !important;
        border: 1px solid #2563eb !important;
    }
}

div.stButton > button {
    background: #cbd5e1 !important;
    color: #475569 !important;
    font-weight: 800 !important;
    font-size: 1.35rem !important;
    border: none !important;
    border-radius: 18px !important;
    padding: 1.15rem 1rem !important;
    min-height: 72px !important;
    box-shadow: none !important;
}

@keyframes shineMove {
    0% { left: -80%; }
    55% { left: 130%; }
    100% { left: 130%; }
}

.result-card {
    background: #fffdf5;
    border: 1px solid #f3e6b0;
    border-radius: 18px;
    padding: 1.2rem;
    margin-top: 1rem;
}
</style>
""", unsafe_allow_html=True)


st.title("Song Analysis MVP")
st.write("アカペラ音声をアップロードすると、全区間を簡易解析できます。")
st.info("使い方: 録音した wav / m4a をアップロードして「解析する」を押してください。")
st.caption("対応形式: wav / m4a ｜ 分析可能時間: 0〜5分 ｜ アカペラ推奨")


st.markdown('<div class="section-title">① 音声ファイルをアップロード</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-text">まず、解析したい録音ファイルを追加してください。</div>', unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "ここに音声ファイルを追加してください",
    type=["wav", "m4a"],
    label_visibility="visible",
    key=f"audio_uploader_{st.session_state.uploader_key}"
)

is_file_uploaded = uploaded_file is not None

if is_file_uploaded:
    st.success("音声ファイルが追加されました。")
else:
    with st.expander("アップロード方法がわからない場合"):
        st.markdown("""
**iPhone**  
ボイスメモ → 共有 → ファイルに保存 → このアプリでアップロード

**Android**  
録音アプリ → 保存 / 共有 → このアプリでアップロード
""")


if is_file_uploaded:
    st.markdown("""
    <div class="animated-panel settings-guide">
        <b>解析設定を変更できます（任意）</b><br>
        よくわからない場合は、そのままでOKです。
    </div>
    """, unsafe_allow_html=True)

    with st.expander("解析設定を変更する", expanded=False):
        key_mode = st.selectbox(
            "歌うキーの傾向",
            ["高め男性キー", "低め男性キー", "低め女性キー", "高め女性キー"],
            index=0,
            disabled=st.session_state.is_analyzing
        )

        profile = get_key_profile(key_mode)

        st.caption(
            f"高音しきい値: {profile['threshold_karaoke']} "
            f"({profile['threshold_note']}, {profile['threshold_hz']:.2f}Hz)"
        )

        note_style = st.radio(
            "音名の表示形式",
            ["mid / hi 形式", "A4 / C5 形式"],
            index=0,
            horizontal=True,
            disabled=st.session_state.is_analyzing
        )
else:
    key_mode = "高め男性キー"
    note_style = "mid / hi 形式"


st.markdown('<div class="section-title">② 解析する</div>', unsafe_allow_html=True)

if st.session_state.is_analyzing:
    st.markdown('<div class="sub-text">解析中です。完了までお待ちください。</div>', unsafe_allow_html=True)

elif is_file_uploaded:
    st.markdown('<div class="sub-text">準備完了です。下のボタンを押すと解析を開始します。</div>', unsafe_allow_html=True)

    st.markdown("""
    <style>
    div.stButton > button {
        position: relative !important;
        overflow: hidden !important;
        background: linear-gradient(90deg, #2563eb, #1d4ed8) !important;
        color: white !important;
        box-shadow: 0 10px 24px rgba(37,99,235,0.35) !important;
    }

    div.stButton > button::after {
        content: "";
        position: absolute;
        top: 0;
        left: -80%;
        width: 55%;
        height: 100%;
        background: linear-gradient(
            120deg,
            transparent,
            rgba(255,255,255,0.55),
            transparent
        );
        animation: shineMove 2.2s infinite;
    }
    </style>
    """, unsafe_allow_html=True)

else:
    st.markdown('<div class="sub-text">音声ファイルを追加すると、解析できます。</div>', unsafe_allow_html=True)


button_label = "解析中です..." if st.session_state.is_analyzing else "解析する"

analyze_button = st.button(
    button_label,
    use_container_width=True,
    disabled=(not is_file_uploaded) or st.session_state.is_analyzing
)

if analyze_button:
    st.session_state.is_analyzing = True
    st.session_state.run_analysis = True
    st.session_state.analysis_result = None
    st.session_state.analysis_error = None
    st.rerun()


if st.session_state.run_analysis and st.session_state.is_analyzing:
    try:
        st.info("解析中です。しばらくお待ちください。")

        progress_bar = st.progress(0)
        progress_text = st.empty()

        def update_progress(percent, message):
            progress_bar.progress(percent)
            progress_text.write(message)

        result = analyze_audio_file(
            uploaded_file=uploaded_file,
            key_mode=key_mode,
            note_style=note_style,
            progress_callback=update_progress
        )

        st.session_state.analysis_result = result
        st.session_state.analysis_error = None

    except Exception as e:
        st.session_state.analysis_error = str(e)
        st.session_state.analysis_result = None

    finally:
        st.session_state.is_analyzing = False
        st.session_state.run_analysis = False

        # 解析完了後、アップロード欄をリセットする
        st.session_state.uploader_key += 1

        st.rerun()


if st.session_state.analysis_error:
    st.error("解析に失敗しました。")
    st.caption(st.session_state.analysis_error)


if st.session_state.analysis_result:
    result = st.session_state.analysis_result

    st.success("解析が完了しました。")

    st.markdown("""
<style>

/* =========================
   結果エリア：ライトモード
========================= */

.result-title {
    font-size: 2.2rem;
    font-weight: 900;
    margin-top: 2rem;
    margin-bottom: 0.8rem;
    text-align: center;
    color: #0f172a;
}

.metric-label {
    color: #64748b;
    font-size: 0.95rem;
    font-weight: 700;
    margin-bottom: 0.2rem;
    text-align: center;
}

.metric-value {
    font-size: 2.2rem;
    font-weight: 900;
    color: #0f172a;
    margin-bottom: 1rem;
    text-align: center;
    text-shadow: none;
}

.comment-box {
    background: #f8fafc;
    color: #0f172a;
    border-left: 5px solid #2563eb;
    border-radius: 12px;
    padding: 1rem;
    margin-top: 1rem;
    font-size: 1rem;
    line-height: 1.8;
    max-width: 760px;
    margin-left: auto;
    margin-right: auto;
}

/* =========================
   結果エリア：ダークモード
========================= */

@media (prefers-color-scheme: dark) {

    .result-title {
        color: #f8fafc !important;
    }

    .metric-label {
        color: #94a3b8 !important;
    }

    .metric-value {
        color: #f8fafc !important;
        text-shadow: 0 0 18px rgba(59, 130, 246, 0.55);
    }

    .comment-box {
        background: #111827 !important;
        color: #f8fafc !important;
        border-left: 5px solid #3b82f6 !important;
    }
}
                

</style>
""", unsafe_allow_html=True)

    st.markdown('<div class="result-title">結果</div>', unsafe_allow_html=True)

    view_mode = st.segmented_control(
        "表示内容",
        ["概要", "グラフ", "詳細"],
        default="概要",
        label_visibility="collapsed"
    )

    if view_mode == "概要":


        col1, col2 = st.columns(2)
        col3, col4 = st.columns(2)

        with col1:
            st.markdown('<div class="metric-label">最高音</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{result["max_pitch_note"]}</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="metric-label">平均音高</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{result["mean_pitch_note"]}</div>', unsafe_allow_html=True)

        with col3:
            st.markdown('<div class="metric-label">高音維持時間</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{result["high_pitch_duration"]:.2f} 秒</div>', unsafe_allow_html=True)

        with col4:
            st.markdown('<div class="metric-label">高音割合</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="metric-value">{result["high_pitch_ratio"] * 100:.1f}%</div>', unsafe_allow_html=True)


        st.markdown("### この音声の傾向")
        st.markdown(
            f'<div class="comment-box">{result["comment"]}</div>',
            unsafe_allow_html=True
        )

    elif view_mode == "グラフ":
        st.write("### 音量の推移")
        st.caption("録音中の音の強さの変化です。絶対的な声量評価ではなく、流れを見る参考です。")

        volume_fig = create_volume_plot(
            result["times_rms"],
            result["rms"]
        )
        st.plotly_chart(volume_fig, use_container_width=True, theme=None)

        st.write("### 音高の推移")
        st.caption("高音しきい値以上は別色で表示されます。")

        pitch_fig = create_pitch_plot(
            result["times_f0"],
            result["f0"],
            result["pitch_tick_values"],
            result["pitch_tick_labels"],
            result["high_pitch_threshold_hz"]
        )
        st.plotly_chart(pitch_fig, use_container_width=True, theme=None)

    elif view_mode == "詳細":
        st.write("### 詳細値")


        st.write(f"サンプリング周波数: {result['sr']} Hz")
        st.write(f"分析前の長さ: {result['analyzed_duration']:.2f} 秒")
        st.write(f"静音除去後の長さ: {result['trimmed_duration']:.2f} 秒")
        st.write(f"最高音Hz: {result['max_pitch_hz']:.2f}")
        st.write(f"平均音高Hz: {result['mean_pitch_hz']:.2f}")
        st.write(
            f"高音しきい値: {result['high_pitch_threshold_display']} "
            f"({result['high_pitch_threshold_hz']:.2f} Hz)"
        )
        st.write(f"選択モード: {result['key_mode']}")
