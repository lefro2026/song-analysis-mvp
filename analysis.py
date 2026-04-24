import os
import shutil
import tempfile
import numpy as np
import librosa
from pydub import AudioSegment

from utils import hz_to_note_name, hz_to_karaoke_note_name, build_comment


MAX_DURATION_SEC = 5 * 60


def get_key_profile(key_mode: str):
    profiles = {
        "低め男性キー": {
            "threshold_note": "G4",
            "threshold_karaoke": "mid2G",
        },
        "高め男性キー": {
            "threshold_note": "A4",
            "threshold_karaoke": "hiA",
        },
        "低め女性キー": {
            "threshold_note": "C5",
            "threshold_karaoke": "hiC",
        },
        "高め女性キー": {
            "threshold_note": "D5",
            "threshold_karaoke": "hiD",
        },
    }

    profile = profiles.get(key_mode, profiles["高め男性キー"])
    threshold_hz = librosa.note_to_hz(profile["threshold_note"])

    return {
        "threshold_note": profile["threshold_note"],
        "threshold_karaoke": profile["threshold_karaoke"],
        "threshold_hz": threshold_hz,
    }


def format_note(freq: float, note_style: str):
    if note_style == "A4 / C5 形式":
        return hz_to_note_name(freq)
    return hz_to_karaoke_note_name(freq)


def build_adaptive_pitch_ticks(valid_f0: np.ndarray, note_style: str):
    if len(valid_f0) == 0:
        tick_notes = ["C3", "C4", "C5"]
        tick_values = [librosa.note_to_hz(n) for n in tick_notes]
        tick_labels = [
            hz_to_karaoke_note_name(v) if note_style == "mid / hi 形式" else hz_to_note_name(v)
            for v in tick_values
        ]
        return tick_values, tick_labels

    min_midi = int(np.floor(librosa.hz_to_midi(np.min(valid_f0))))
    max_midi = int(np.ceil(librosa.hz_to_midi(np.max(valid_f0))))

    min_oct = max(24, ((min_midi - 3) // 12) * 12)
    max_oct = min(96, ((max_midi + 9) // 12) * 12)

    tick_midis = list(range(min_oct, max_oct + 1, 12))
    tick_values = [librosa.midi_to_hz(m) for m in tick_midis]

    if note_style == "mid / hi 形式":
        tick_labels = [hz_to_karaoke_note_name(v) for v in tick_values]
    else:
        tick_labels = [hz_to_note_name(v) for v in tick_values]

    return tick_values, tick_labels


def load_audio_from_uploaded_file(uploaded_file):
    ext = uploaded_file.name.split(".")[-1].lower()
    temp_dir = tempfile.mkdtemp()

    input_path = os.path.join(temp_dir, f"input.{ext}")
    output_path = os.path.join(temp_dir, "converted.wav")

    try:
        with open(input_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        if ext == "m4a":
            audio = AudioSegment.from_file(input_path, format="m4a")
            audio = audio.set_channels(1)
            audio.export(output_path, format="wav")
            y, sr = librosa.load(output_path, sr=None, mono=True)
        else:
            y, sr = librosa.load(input_path, sr=None, mono=True)

        return y, sr

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def trim_silence(y, top_db=25):
    y_trimmed, _ = librosa.effects.trim(y, top_db=top_db)
    return y_trimmed


def analyze_audio_file(uploaded_file, key_mode, note_style, progress_callback=None):
    def progress(percent, message):
        if progress_callback:
            progress_callback(percent, message)

    progress(5, "音声ファイルを読み込んでいます...")
    y, sr = load_audio_from_uploaded_file(uploaded_file)

    if len(y) == 0:
        raise ValueError("音声データが空です。")

    analyzed_duration = len(y) / sr

    if analyzed_duration <= 0:
        raise ValueError("音声の長さを取得できませんでした。")

    if analyzed_duration > MAX_DURATION_SEC:
        raise ValueError("分析できる長さは 0〜5分 です。5分以内の音声をアップロードしてください。")

    progress(20, "静音区間を整理しています...")
    y = trim_silence(y, top_db=25)

    if len(y) == 0:
        raise ValueError("静音を除くと有効な音声がありませんでした。")

    trimmed_duration = len(y) / sr

    frame_length = 2048
    hop_length = 512

    progress(35, "音量の推移を計算しています...")
    rms = librosa.feature.rms(
        y=y,
        frame_length=frame_length,
        hop_length=hop_length
    )[0]

    times_rms = librosa.frames_to_time(
        np.arange(len(rms)),
        sr=sr,
        hop_length=hop_length
    )

    progress(55, "音の高さを解析しています...")
    f0, voiced_flag, voiced_prob = librosa.pyin(
        y,
        fmin=librosa.note_to_hz("C2"),
        fmax=librosa.note_to_hz("C6"),
        sr=sr,
        frame_length=frame_length,
        hop_length=hop_length
    )

    times_f0 = librosa.times_like(f0, sr=sr)
    valid_f0 = f0[~np.isnan(f0)]

    if len(valid_f0) == 0:
        raise ValueError("音高を検出できませんでした。アカペラ音声か確認してください。")

    progress(75, "高音区間を集計しています...")

    max_pitch_hz = float(np.max(valid_f0))
    mean_pitch_hz = float(np.mean(valid_f0))

    profile = get_key_profile(key_mode)
    high_pitch_threshold_hz = profile["threshold_hz"]

    seconds_per_frame = hop_length / sr

    voiced_frames = np.sum(~np.isnan(f0))
    voiced_duration = voiced_frames * seconds_per_frame

    high_pitch_mask = (~np.isnan(f0)) & (f0 >= high_pitch_threshold_hz)
    high_pitch_frames = np.sum(high_pitch_mask)
    high_pitch_duration = high_pitch_frames * seconds_per_frame
    high_pitch_ratio = high_pitch_duration / voiced_duration if voiced_duration > 0 else 0.0

    max_pitch_note = format_note(max_pitch_hz, note_style)
    mean_pitch_note = format_note(mean_pitch_hz, note_style)

    if note_style == "A4 / C5 形式":
        threshold_display = profile["threshold_note"]
    else:
        threshold_display = profile["threshold_karaoke"]

    progress(90, "結果をまとめています...")

    comment = build_comment(
        max_pitch_note=max_pitch_note,
        high_pitch_duration=high_pitch_duration,
        high_pitch_ratio=high_pitch_ratio,
    )

    pitch_tick_values, pitch_tick_labels = build_adaptive_pitch_ticks(valid_f0, note_style)

    progress(100, "完了しました。")

    return {
        "sr": sr,
        "analyzed_duration": analyzed_duration,
        "trimmed_duration": trimmed_duration,
        "rms": rms,
        "times_rms": times_rms,
        "f0": f0,
        "times_f0": times_f0,
        "max_pitch_hz": max_pitch_hz,
        "mean_pitch_hz": mean_pitch_hz,
        "max_pitch_note": max_pitch_note,
        "mean_pitch_note": mean_pitch_note,
        "high_pitch_threshold_hz": high_pitch_threshold_hz,
        "high_pitch_threshold_display": threshold_display,
        "high_pitch_duration": high_pitch_duration,
        "high_pitch_ratio": high_pitch_ratio,
        "pitch_tick_values": pitch_tick_values,
        "pitch_tick_labels": pitch_tick_labels,
        "comment": comment,
        "key_mode": key_mode,
    }