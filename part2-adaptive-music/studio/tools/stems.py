"""Builds baseline.wav, drums.wav and tension.wav (D minor, 86 BPM).

    python3 build_stems.py <loops_dir> <out_dir>

loops_dir holds the downloaded Looperman WAVs (matched by name).
Needs numpy and soundfile.
"""
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

SR = 44100
BAR = 4 * 60 / 86
LEN4 = int(round(4 * BAR * SR))  # 11.163 s
UP = Path(sys.argv[1])
OUT = Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)


def load(tag):
    path = next(UP.glob(f"*{tag}*.wav"))
    x, sr = sf.read(path, always_2d=True)
    assert sr == SR
    return x


def fit(x, n):
    # trim or tile to exactly n samples
    reps = int(np.ceil(n / len(x)))
    return np.tile(x, (reps, 1))[:n]


def declick(x, fade_in=0.003, fade_out=0.010):
    # some loops are cut mid-note; tiny fades stop the click when FMOD wraps them
    x = x.copy()
    a, b = int(fade_in * SR), int(fade_out * SR)
    x[:a] *= np.linspace(0, 1, a)[:, None]
    x[-b:] *= np.linspace(1, 0, b)[:, None]
    return x


def rms_db(x):
    return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)


def at(x, db):
    return x * 10 ** ((db - rms_db(x)) / 20)


def save(name, x, peak_db=-1.0):
    peak = np.abs(x).max()
    limit = 10 ** (peak_db / 20)
    if peak > limit:
        x = x * limit / peak
    sf.write(OUT / name, x, SR, subtype="PCM_16")
    print(f"{name}: {len(x) / SR:.3f} s, rms {rms_db(x):.1f} dBFS, peak {20 * np.log10(np.abs(x).max()):.1f} dBFS")
    return x


rhodes = at(declick(fit(load("epiano"), LEN4)), -24)
bass = at(declick(fit(load("acoustic-bass"), LEN4)), -22)
guitar = at(declick(fit(load("guitar-chords"), LEN4)), -29)
jazz_drums = at(fit(load("east-side-90s"), LEN4), -20)
violin = at(declick(fit(load("cubeats-type-violin"), 2 * LEN4)), -27)

save("baseline.wav", rhodes + bass + guitar)
save("drums.wav", jazz_drums)
save("tension.wav", violin)
