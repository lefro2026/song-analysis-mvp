import numpy as np
import librosa


def hz_to_note_name(freq: float) -> str:
    if np.isnan(freq) or freq <= 0:
        return "N/A"
    midi = int(round(librosa.hz_to_midi(freq)))
    return librosa.midi_to_note(midi)


def build_comment(max_pitch_note: str, high_pitch_duration: float, high_pitch_ratio: float) -> str:
    comments = []

    comments.append(f"最高音は {max_pitch_note} でした。")

    if high_pitch_duration < 2.0:
        comments.append("高音区間は短めです。")
    elif high_pitch_duration < 5.0:
        comments.append("高音区間はある程度あります。")
    else:
        comments.append("高音を保てている時間が長めです。")

    if high_pitch_ratio < 0.15:
        comments.append("全体としては高音の割合は控えめです。")
    elif high_pitch_ratio < 0.35:
        comments.append("高音は適度に含まれています。")
    else:
        comments.append("高音の占める割合が大きめです。")

    return " ".join(comments)