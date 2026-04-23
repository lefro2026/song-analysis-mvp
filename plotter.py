import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np

mpl.rcParams["font.family"] = ["Yu Gothic", "Meiryo", "MS Gothic", "DejaVu Sans"]
mpl.rcParams["axes.unicode_minus"] = False


def create_volume_plot(times_rms, rms):
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(times_rms, rms)
    ax.set_title("音量の推移")
    ax.set_xlabel("時間 (秒)")
    ax.set_ylabel("RMS")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    return fig


def create_pitch_plot(times_f0, f0, tick_values, tick_labels):
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(times_f0, f0)
    ax.set_title("音高の推移")
    ax.set_xlabel("時間 (秒)")
    ax.set_ylabel("音高 (Hz)")
    ax.set_yticks(tick_values)
    ax.set_yticklabels(tick_labels)
    ax.grid(alpha=0.3)

    valid_f0 = f0[~np.isnan(f0)]
    if len(valid_f0) > 0:
        y_min = np.min(valid_f0) * 0.95
        y_max = np.max(valid_f0) * 1.05
        ax.set_ylim(y_min, y_max)

    fig.tight_layout()
    return fig