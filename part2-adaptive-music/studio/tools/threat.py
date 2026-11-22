"""Builds threat.wav: cello + two string layers + taiko, 8 bars (D minor, 86 BPM).

    python3 build_threat.py <loops_dir> <out_dir>

Needs numpy, soundfile and the rubberband CLI (for the two tempo changes).
"""
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

SR = 44100
LEN4 = int(round(4 * 4 * 60 / 86 * SR))
UP = Path(sys.argv[1])
OUT = Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)


def src(tag):
    return next(UP.glob(f"*{tag}*.wav"))


def stretch(tag, n):
    tmp = OUT / f"_tmp_{tag}.wav"
    subprocess.run(["rubberband", "-q", "--fine", "-D", f"{n / SR:.6f}", str(src(tag)), str(tmp)], check=True)
    x, _ = sf.read(tmp, always_2d=True)
    tmp.unlink()
    return fit(x, n)


def load(tag, n):
    x, _ = sf.read(src(tag), always_2d=True)
    return fit(x, n)


def fit(x, n):
    return np.tile(x, (int(np.ceil(n / len(x))), 1))[:n]


def declick(x, a=0.003, b=0.010):
    x = x.copy()
    a, b = int(a * SR), int(b * SR)
    x[:a] *= np.linspace(0, 1, a)[:, None]
    x[-b:] *= np.linspace(1, 0, b)[:, None]
    return x


def at(x, db):
    return x * 10 ** ((db - 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)) / 20)


def save(path, x, peak_db=-1.0):
    x = x * min(1.0, 10 ** (peak_db / 20) / np.abs(x).max())
    sf.write(path, x, SR, subtype="PCM_16")
    return x


cello = at(declick(load("james-blake-cello", LEN4)), -23)
dark = at(declick(load("strings-prodtiptoe", LEN4)), -25)
jysk = at(declick(stretch("jysk-strings", 2 * LEN4)), -28)  # 88 -> 86 BPM
taiko = at(declick(stretch("rising-tension-taiko", LEN4)), -23)  # 170 -> 172 BPM

threat = fit(cello + dark + taiko, 2 * LEN4) + jysk
save(OUT / "threat.wav", threat)
print("threat.wav", round(len(threat) / SR, 3), "s")
