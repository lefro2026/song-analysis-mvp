import os
import shutil
import tempfile
import numpy as np
import librosa
from pydub import AudioSegment

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
    ext = uploaded_file.name.split(".")[-1].lower()
    temp_dir = tempfile.mkdtemp()

    input_path = os.path.join(temp_dir, f"input.{ext}")
    output_path = os.path.join(temp_dir, "converted.wav")

    try:
        # アップロードファイルを保存
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
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass


def analyze_audio_file(uploaded_file):
    y, sr = load_audio_from_uploaded_file(uploaded_file)

    if len(y) == 0:
        raise ValueError("音声データが空です。")

    analyzed_duration = len(y) / sr

    frame_length = 2048
    hop_length = 512

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
        raise ValueError("音高を検出できませんでした。")

    max_pitch_hz = float(np.max(valid_f0))
    mean_pitch_hz = float(np.mean(valid_f0))

    high_pitch_threshold_hz = librosa.note_to_hz(HIGH_PITCH_THRESHOLD_NOTE)
    seconds_per_frame = hop_length / sr

    voiced_frames = np.sum(~np.isnan(f0))
    voiced_duration = voiced_frames * seconds_per_frame

    high_pitch_mask = (~np.isnan(f0)) & (f0 >= high_pitch_threshold_hz)
    high_pitch_frames = np.sum(high_pitch_mask)

    high_pitch_duration = high_pitch_frames * seconds_per_frame

    if voiced_duration > 0:
        high_pitch_ratio = high_pitch_duration / voiced_duration
    else:
        high_pitch_ratio = 0.0

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
