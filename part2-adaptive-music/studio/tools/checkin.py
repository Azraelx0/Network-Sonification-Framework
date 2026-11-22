"""Prepares checkin.wav from the VSCO 2 cello pizzicato and renders a full preview.

    python3 build_checkin.py <pizz.wav> <stems_dir> <threat.wav> <out_dir>
"""
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

SR = 44100
src, stems, threat_path, out = (Path(p) for p in sys.argv[1:5])
out.mkdir(parents=True, exist_ok=True)


def fit(x, n):
    return np.tile(x, (int(np.ceil(n / len(x))), 1))[:n]


def db(x):
    return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)


# trim leading silence, keep ~0.8 s, gentle tail fade so it never cuts off
pizz, sr = sf.read(src, always_2d=True)
assert sr == SR
env = np.abs(pizz).max(axis=1)
start = max(0, np.argmax(env > env.max() * 0.02) - int(0.001 * SR))
pizz = pizz[start:start + int(0.8 * SR)].copy()
fade = int(0.25 * SR)
pizz[-fade:] *= np.linspace(1, 0, fade)[:, None] ** 2

base, _ = sf.read(stems / "baseline.wav", always_2d=True)
drums, _ = sf.read(stems / "drums.wav", always_2d=True)
violin, _ = sf.read(stems / "tension.wav", always_2d=True)
threat, _ = sf.read(threat_path, always_2d=True)

# level: the pluck's first 150 ms sits ~4 dB above the full C2 mix
c2_mix = fit(base, len(threat)) * 10 ** (-4 / 20) + fit(drums, len(threat)) + fit(violin, len(threat)) + threat
attack = pizz[: int(0.15 * SR)]
pizz *= 10 ** ((db(c2_mix) + 4 - db(attack)) / 20)
pizz *= min(1.0, 10 ** (-1 / 20) / np.abs(pizz).max())
sf.write(out / "checkin.wav", pizz, SR, subtype="PCM_16")
print(f"checkin.wav {len(pizz) / SR:.3f} s, peak {20 * np.log10(np.abs(pizz).max()):.1f} dBFS")

# preview: 2 loops baseline, 3 loops infection, 5 loops c2 with baseline ducked 4 dB and
# check-ins every ~5.8 s (WarmCookie's average gap)
seg = len(base)
n = seg * 10
t = np.arange(n) / SR
s = seg / SR
lvl = np.where(t < 2 * s, 0, np.where(t < 5 * s, np.minimum((t - 2 * s) / 2, 1), np.minimum(1 + (t - 5 * s) / 2, 2)))
ten = np.clip(lvl, 0, 1)[:, None]
thr = np.clip(lvl - 1, 0, 1)[:, None]
duck = (10 ** (-4 * np.clip(lvl - 1, 0, 1) / 20))[:, None]
mix = fit(base, n) * duck + fit(drums, n) + fit(violin, n) * ten + fit(threat, n) * thr
for at_s in np.arange(5 * s + 1.0, n / SR - 1, 5.8):
    i = int(at_s * SR)
    mix[i:i + len(pizz)] += pizz[: n - i]
mix /= max(1, np.abs(mix).max() / 0.95)
sf.write(out / "preview_full.wav", mix, SR)
print("preview_full.wav", round(n / SR, 1), "s; C2 starts at", round(5 * s, 1), "s")
