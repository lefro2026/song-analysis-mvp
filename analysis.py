import io
import tempfile
import numpy as np
import librosa

from utils import hz_to_note_name, build_comment


HIGH_PITCH_THRESHOLD_NOTE = "A4"


def build_adaptive_pitch_ticks(valid_f0: np.ndarray):
    if len(valid_f0) == 0:
        tick_notes = ["C3", "C4", "C5"]
        tick_values = [librosa.note_to_hz(n) for n in tick_notes]
        return tick_values, tick_notes

    min_midi = int(np.floor(librosa.hz_to_midi(np.min(valid_f0))))
    max_midi = int(np.ceil(librosa.hz_to_midi(np.max(valid_f0))))

    min_oct = max(24, ((min_midi - 3) // 12) * 12)
    max_oct = min(96, ((max_midi + 9) // 12) * 12)

    tick_midis = list(range(min_oct, max_oct + 1, 12))
    tick_notes = [librosa.midi_to_note(m) for m in tick_midis]
    tick_values = [librosa.midi_to_hz(m) for m in tick_midis]
    return tick_values, tick_notes


def load_audio_from_uploaded_file(uploaded_file):
    suffix = "." + uploaded_file.name.split(".")[-1].lower()

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    y, sr = librosa.load(tmp_path, sr=None, mono=True)
    return y, sr


def cut_audio_segment(y, sr, start_sec, end_sec):
    start_sample = int(start_sec * sr)
    end_sample = int(end_sec * sr)
    return y[start_sample:end_sample]


def analyze_audio_file(uploaded_file, start_sec: float, end_sec: float):
    y, sr = load_audio_from_uploaded_file(uploaded_file)
    y_cut = cut_audio_segment(y, sr, start_sec, end_sec)

    if len(y_cut) == 0:
        raise ValueError("指定区間の音声が空です。開始秒と終了秒を確認してください。")

    analyzed_duration = len(y_cut) / sr

    frame_length = 2048
    hop_length = 512

    rms = librosa.feature.rms(
        y=y_cut,
        frame_length=frame_length,
        hop_length=hop_length
    )[0]
    times_rms = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop_length)

    f0, voiced_flag, voiced_prob = librosa.pyin(
        y_cut,
        fmin=librosa.note_to_hz("C2"),
        fmax=librosa.note_to_hz("C6"),
        sr=sr,
        frame_length=frame_length,
        hop_length=hop_length
    )

    times_f0 = librosa.times_like(f0, sr=sr)
    valid_f0 = f0[~np.isnan(f0)]

    if len(valid_f0) == 0:
        raise ValueError("音高をうまく検出できませんでした。アカペラ音声か確認してください。")

    max_pitch_hz = float(np.max(valid_f0))
    mean_pitch_hz = float(np.mean(valid_f0))

    high_pitch_threshold_hz = librosa.note_to_hz(HIGH_PITCH_THRESHOLD_NOTE)
    seconds_per_frame = hop_length / sr

    voiced_frames = np.sum(~np.isnan(f0))
    voiced_duration = voiced_frames * seconds_per_frame

    high_pitch_mask = (~np.isnan(f0)) & (f0 >= high_pitch_threshold_hz)
    high_pitch_frames = np.sum(high_pitch_mask)
    high_pitch_duration = high_pitch_frames * seconds_per_frame
    high_pitch_ratio = high_pitch_duration / voiced_duration if voiced_duration > 0 else 0.0

    max_pitch_note = hz_to_note_name(max_pitch_hz)
    mean_pitch_note = hz_to_note_name(mean_pitch_hz)

    comment = build_comment(
        max_pitch_note=max_pitch_note,
        high_pitch_duration=high_pitch_duration,
        high_pitch_ratio=high_pitch_ratio,
    )

    pitch_tick_values, pitch_tick_labels = build_adaptive_pitch_ticks(valid_f0)

    return {
        "sr": sr,
        "analyzed_duration": analyzed_duration,
        "rms": rms,
        "times_rms": times_rms,
        "f0": f0,
        "times_f0": times_f0,
        "max_pitch_hz": max_pitch_hz,
        "mean_pitch_hz": mean_pitch_hz,
        "max_pitch_note": max_pitch_note,
        "mean_pitch_note": mean_pitch_note,
        "high_pitch_threshold_hz": high_pitch_threshold_hz,
        "high_pitch_threshold_note": HIGH_PITCH_THRESHOLD_NOTE,
        "high_pitch_duration": high_pitch_duration,
        "high_pitch_ratio": high_pitch_ratio,
        "pitch_tick_values": pitch_tick_values,
        "pitch_tick_labels": pitch_tick_labels,
        "comment": comment,
    }