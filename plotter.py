import numpy as np
import librosa
import plotly.graph_objects as go


def hz_to_note_name(freq):
    if freq is None or np.isnan(freq) or freq <= 0:
        return "N/A"
    midi = int(round(librosa.hz_to_midi(freq)))
    return librosa.midi_to_note(midi)


# =========================
# カラー設定
# =========================

# 通常音域（青）
NORMAL_POINT_COLOR = "#38bdf8"

# 高音域
HIGH_POINT_COLOR = "#facc15"
HIGH_POINT_BORDER = "#fef3c7"

# ホバー表示
HOVER_BG_COLOR = "#ffffff"
HOVER_BORDER_COLOR = "#2563eb"
HOVER_TEXT_COLOR = "#0f172a"

def common_hoverlabel():
    return dict(
        bgcolor=HOVER_BG_COLOR,
        bordercolor=HOVER_BORDER_COLOR,
        font=dict(
            color=HOVER_TEXT_COLOR,
            size=14
        )
    )


def apply_hover_style(fig):
    fig.update_traces(
        hoverlabel=common_hoverlabel()
    )

    fig.update_layout(
        hoverlabel=common_hoverlabel()
    )

    return fig


def apply_common_layout(fig, height):
    fig.update_layout(
        height=height,
        margin=dict(l=48, r=28, t=58, b=48),

        paper_bgcolor="#0f172a",
        plot_bgcolor="#0f172a",

        font=dict(color="#f8fafc"),

        showlegend=False,
        hovermode="closest",

        xaxis=dict(
            gridcolor="rgba(255,255,255,0.20)",
            zerolinecolor="rgba(255,255,255,0.20)",
            tickfont=dict(color="#e2e8f0"),
            title_font=dict(color="#f8fafc"),
        ),

        yaxis=dict(
            gridcolor="rgba(255,255,255,0.20)",
            zerolinecolor="rgba(255,255,255,0.20)",
            tickfont=dict(color="#e2e8f0"),
            title_font=dict(color="#f8fafc"),
        ),
    )

    apply_hover_style(fig)

    return fig


def create_volume_plot(times_rms, rms):
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=times_rms,
            y=rms,
            mode="lines",
            name="音量",
            line=dict(
                width=3,
                color=NORMAL_POINT_COLOR
            ),
            fill="tozeroy",
            fillcolor="rgba(56,189,248,0.18)",
            hovertemplate=(
                "時間 %{x:.2f}秒<br>"
                "音量 %{y:.4f}"
                "<extra></extra>"
            ),
            hoverlabel=common_hoverlabel(),
        )
    )

    fig.update_layout(
        title=dict(
            text="音量の推移",
            font=dict(size=18, color="#f8fafc")
        ),
        xaxis_title="時間（秒）",
        yaxis_title="RMS",
    )

    apply_common_layout(fig, 360)

    return fig


def create_pitch_plot(
    times_f0,
    f0,
    tick_values,
    tick_labels,
    high_pitch_threshold_hz=None
):
    fig = go.Figure()

    f0_array = np.array(f0, dtype=float)
    times_array = np.array(times_f0, dtype=float)

    valid_mask = ~np.isnan(f0_array)

    normal_mask = valid_mask.copy()
    high_mask = np.zeros_like(valid_mask, dtype=bool)

    if high_pitch_threshold_hz is not None:
        high_mask = valid_mask & (f0_array >= high_pitch_threshold_hz)
        normal_mask = valid_mask & (f0_array < high_pitch_threshold_hz)

    normal_notes = [hz_to_note_name(v) for v in f0_array[normal_mask]]
    high_notes = [hz_to_note_name(v) for v in f0_array[high_mask]]

    # 通常音域
    fig.add_trace(
        go.Scatter(
            x=times_array[normal_mask],
            y=f0_array[normal_mask],
            mode="markers",
            marker=dict(
                size=6,
                color=NORMAL_POINT_COLOR,
                opacity=0.90
            ),
            customdata=normal_notes,
            hovertemplate=(
                "時間 %{x:.2f}秒<br>"
                "音高 %{customdata}<br>"
                "周波数 %{y:.2f}Hz"
                "<extra></extra>"
            ),
            hoverlabel=common_hoverlabel(),
        )
    )

    # 高音域
    if high_pitch_threshold_hz is not None:
        fig.add_trace(
            go.Scatter(
                x=times_array[high_mask],
                y=f0_array[high_mask],
                mode="markers",
                marker=dict(
                    size=7,
                    color=HIGH_POINT_COLOR,
                    opacity=0.95,
                    line=dict(
                        width=1,
                        color=HIGH_POINT_BORDER
                    )
                ),
                customdata=high_notes,
                hovertemplate=(
                    "時間 %{x:.2f}秒<br>"
                    "音高 %{customdata}<br>"
                    "周波数 %{y:.2f}Hz"
                    "<extra></extra>"
                ),
                hoverlabel=common_hoverlabel(),
            )
        )

        fig.add_hline(
            y=high_pitch_threshold_hz,
            line_dash="dash",
            line_color="#f8fafc",
            line_width=2,
        )

    fig.update_layout(
        title=dict(
            text="音高の推移",
            font=dict(size=18, color="#f8fafc")
        ),
        xaxis_title="時間（秒）",
        yaxis_title="音高",
    )

    fig.update_yaxes(
        tickmode="array",
        tickvals=tick_values,
        ticktext=tick_labels,
    )

    apply_common_layout(fig, 420)

    return fig