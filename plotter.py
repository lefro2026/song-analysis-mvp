import numpy as np
import librosa
import plotly.graph_objects as go


def hz_to_note_name(freq):
    if freq is None or np.isnan(freq) or freq <= 0:
        return "N/A"
    midi = int(round(librosa.hz_to_midi(freq)))
    return librosa.midi_to_note(midi)


def create_volume_plot(times_rms, rms):
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=times_rms,
            y=rms,
            mode="lines",
            name="音量",
            hovertemplate="時間: %{x:.2f}秒<br>音量: %{y:.4f}<extra></extra>",
        )
    )

    fig.update_layout(
        title="音量の推移",
        xaxis_title="時間（秒）",
        yaxis_title="RMS",
        height=360,
        margin=dict(l=40, r=20, t=50, b=40),
    )

    return fig


def create_pitch_plot(times_f0, f0, tick_values, tick_labels, high_pitch_threshold_hz=None):
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

    fig.add_trace(
        go.Scatter(
            x=times_array[normal_mask],
            y=f0_array[normal_mask],
            mode="markers",
            name="通常音域",
            marker=dict(size=5),
            customdata=normal_notes,
            hovertemplate="時間: %{x:.2f}秒<br>音高: %{customdata}<br>周波数: %{y:.2f}Hz<extra></extra>",
        )
    )

    if high_pitch_threshold_hz is not None:
        fig.add_trace(
            go.Scatter(
                x=times_array[high_mask],
                y=f0_array[high_mask],
                mode="markers",
                name="高音域",
                marker=dict(size=6),
                customdata=high_notes,
                hovertemplate="時間: %{x:.2f}秒<br>音高: %{customdata}<br>周波数: %{y:.2f}Hz<extra></extra>",
            )
        )

        threshold_note = hz_to_note_name(high_pitch_threshold_hz)

        fig.add_hline(
            y=high_pitch_threshold_hz,
            line_dash="dash",
            annotation_text=f"高音しきい値: {threshold_note}",
            annotation_position="top left",
        )

    fig.update_layout(
        title="音高の推移",
        xaxis_title="時間（秒）",
        yaxis_title="音高",
        height=420,
        margin=dict(l=40, r=20, t=50, b=40),
        hovermode="closest",
    )

    fig.update_yaxes(
        tickmode="array",
        tickvals=tick_values,
        ticktext=tick_labels,
    )

    return fig