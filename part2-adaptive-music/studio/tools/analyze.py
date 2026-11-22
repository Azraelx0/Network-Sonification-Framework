"""Prints length, bars at 86/172 BPM, detected tempo, likely key and loudness for each WAV.

    python3 analyze.py loop1.wav loop2.wav ...

Needs librosa.
"""

import sys
import numpy as np
import librosa
import soundfile as sf

KEYS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
# Krumhansl-Schmuckler profiles
MAJ = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
MIN = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])


def key_of(chroma):
    best = []
    for i in range(12):
        best.append((np.corrcoef(np.roll(MAJ, i), chroma)[0, 1], KEYS[i] + " major"))
        best.append((np.corrcoef(np.roll(MIN, i), chroma)[0, 1], KEYS[i] + " minor"))
    best.sort(reverse=True)
    return best[:3]


for path in sys.argv[1:]:
    info = sf.info(path)
    y, sr = librosa.load(path, sr=None, mono=True)
    dur = len(y) / sr
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr).mean(axis=1)
    rms = 20 * np.log10(np.sqrt(np.mean(y ** 2)) + 1e-12)
    peak = 20 * np.log10(np.abs(y).max() + 1e-12)
    name = path.split("0-", 1)[-1] if "0-" in path else path
    print(f"{name}")
    print(f"  {info.samplerate} Hz, {info.channels} ch, {info.subtype}, {dur:.3f} s")
    print(f"  bars@86: {dur / (4 * 60 / 86):.2f}  bars@172: {dur / (4 * 60 / 172):.2f}  detected tempo ~{float(np.atleast_1d(tempo)[0]):.1f}")
    print(f"  key guesses: " + ", ".join(f"{k} ({c:.2f})" for c, k in key_of(chroma)))
    print(f"  rms {rms:.1f} dBFS, peak {peak:.1f} dBFS")
