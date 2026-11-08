#!/usr/bin/env python3
"""
netscape.py - sonify network captures as environmental soundscapes.

Turns a Wireshark capture into a stereo WAV where network activity becomes
the sounds of a place (a forest, a coastline). The mapping from packets to
sounds lives in a JSON file so it can be designed, documented, and versioned
separately from the code.

How the mapping works:
  KEYNOTE  - overall packet rate drives a continuous bed (wind, surf).
  SIGNALS  - each protocol family becomes a "species" of discrete sound.
             Packet size sets pitch (bigger packets = lower sounds).
             Bare SYNs and RSTs get their own sharp sound.
  SPACE    - each host gets a position in the stereo field. With --target,
             traffic from the target sits right and traffic to it sits left.

Packets are grouped into short time bins so floods don't become thousands of
individual notes: more packets in a bin = louder and denser events.

Usage:
  python netscape.py capture.pcapng -m mappings/forest.json -o out.wav
  python netscape.py packets.csv    -m mappings/coastal.json -o out.wav --target 192.168.56.20

Input: a .pcap/.pcapng (requires tshark on your PATH) or a CSV exported with:
  tshark -r capture.pcapng -T fields -E header=y -E separator=, -E quote=d \
    -E occurrence=f -e frame.time_relative -e frame.len -e frame.protocols \
    -e ip.src -e ip.dst -e arp.src.proto_ipv4 -e tcp.flags.syn \
    -e tcp.flags.ack -e tcp.flags.reset > packets.csv

Optional: --samples DIR uses your own field recordings instead of synthesized
sounds. Put WAV files in DIR/<voice name>/ (e.g. samples/bird/*.wav,
samples/wind/*.wav). Any voice without a folder falls back to synthesis.

Requires: numpy, scipy
"""

import argparse
import csv
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
from collections import Counter, defaultdict

import numpy as np
from scipy import signal
from scipy.io import wavfile

SR = 44100

TSHARK_FIELDS = [
    "frame.time_relative", "frame.len", "frame.protocols",
    "ip.src", "ip.dst", "arp.src.proto_ipv4",
    "tcp.flags.syn", "tcp.flags.ack", "tcp.flags.reset",
]


# ---------------------------------------------------------------- loading ---

def flag(value):
    return str(value).strip().lower() in ("1", "true")


def load_packets(path):
    if path.lower().endswith((".pcap", ".pcapng", ".cap")):
        tshark = shutil.which("tshark")
        if not tshark:
            sys.exit("tshark not found. Install Wireshark (with tshark) or export a CSV first.")
        cmd = [tshark, "-r", path, "-T", "fields", "-E", "header=y",
               "-E", "separator=,", "-E", "quote=d", "-E", "occurrence=f"]
        for f in TSHARK_FIELDS:
            cmd += ["-e", f]
        out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
        rows = list(csv.DictReader(out.splitlines()))
    else:
        with open(path, newline="") as fh:
            rows = list(csv.DictReader(fh))

    packets = []
    for r in rows:
        try:
            t = float(r.get("frame.time_relative") or 0)
            length = int(float(r.get("frame.len") or 0))
        except ValueError:
            continue
        packets.append({
            "t": t,
            "len": length,
            "layers": (r.get("frame.protocols") or "").lower().split(":"),
            "src": r.get("ip.src") or r.get("arp.src.proto_ipv4") or "",
            "dst": r.get("ip.dst") or "",
            "syn": flag(r.get("tcp.flags.syn", "")),
            "ack": flag(r.get("tcp.flags.ack", "")),
            "rst": flag(r.get("tcp.flags.reset", "")),
        })
    if not packets:
        sys.exit("No packets found in input.")
    t0 = min(p["t"] for p in packets)
    for p in packets:
        p["t"] -= t0
    return packets


def classify(p, mapping):
    """Return the voice name for one packet."""
    flags = mapping.get("flags", {})
    if p["rst"] and "rst" in flags:
        return flags["rst"]
    if p["syn"] and not p["ack"] and "syn" in flags:
        return flags["syn"]
    for layer, voice in mapping["protocols"]:
        if layer in p["layers"]:
            return voice
    return mapping.get("default", "rustle")


def pan_for(p, target):
    """0 = hard left, 1 = hard right."""
    if target:
        if p["src"] == target:
            return 0.85
        if p["dst"] == target:
            return 0.15
        return 0.5
    h = int(hashlib.md5(p["src"].encode()).hexdigest(), 16) % 1000 / 1000
    return 0.15 + 0.7 * h


# ------------------------------------------------------------ synthesis ---
# Each voice: f(rng, size) -> mono float array. size is 0 (tiny) .. 1 (full MTU).

def _t(dur):
    n = max(1, int(dur * SR))
    return n, np.arange(n) / SR


def _bandnoise(rng, n, lo, hi, order=2):
    sos = signal.butter(order, [lo, hi], btype="band", fs=SR, output="sos")
    y = signal.sosfilt(sos, rng.standard_normal(n))
    return y / (np.std(y) + 1e-9)


def v_bird(rng, size):
    dur = rng.uniform(0.08, 0.18)
    n, t = _t(dur)
    base = 5200 - 3000 * size
    f = base * (1 + 0.35 * np.sin(np.pi * t / dur))
    f *= 1 + 0.03 * np.sin(2 * np.pi * rng.uniform(25, 45) * t)
    return 0.5 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / dur) ** 2


def v_cricket(rng, size):
    f = rng.uniform(4200, 4800) - 600 * size
    pulse, gap, count = 0.018, 0.012, 3
    n, t = _t(count * (pulse + gap))
    gate = ((t % (pulse + gap)) < pulse).astype(float)
    win = np.hanning(64)
    gate = np.convolve(gate, win / win.sum(), mode="same")
    return 0.35 * np.sin(2 * np.pi * f * t) * gate


def v_drop(rng, size):
    n, t = _t(0.12)
    f0 = rng.uniform(500, 900) * (1.4 - 0.8 * size)
    f = f0 * (1 + 2.5 * (1 - np.exp(-t / 0.02)))
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.03)
    y[:40] *= np.linspace(0, 1, 40)
    return 0.6 * y


def v_knock(rng, size):
    hits, spacing = int(rng.integers(3, 6)), 0.06
    n, _ = _t(hits * spacing + 0.05)
    y = np.zeros(n)
    hn, t = _t(0.04)
    f = 900 - 400 * size
    hit = (np.sin(2 * np.pi * f * t) + 0.5 * rng.standard_normal(hn) * np.exp(-t / 0.003))
    hit *= np.exp(-t / 0.008)
    for i in range(hits):
        s = int(i * spacing * SR)
        y[s:s + hn] += hit[: max(0, min(hn, n - s))]
    return 0.5 * y


def v_snap(rng, size):
    n, t = _t(0.03)
    return 0.35 * _bandnoise(rng, n, 1500, 7000) * np.exp(-t / 0.004)


def v_rustle(rng, size):
    dur = rng.uniform(0.15, 0.35)
    n, t = _t(dur)
    grains = np.convolve((rng.random(n) < 0.02).astype(float), np.hanning(200), mode="same")
    return 0.08 * _bandnoise(rng, n, 2000, 9000) * grains * np.sin(np.pi * t / dur)


def v_gull(rng, size):
    dur = rng.uniform(0.25, 0.45)
    n, t = _t(dur)
    f = (1800 - 700 * size) * (1.25 - 0.45 * t / dur)
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = np.sin(ph) + 0.5 * np.sin(2 * ph) + 0.25 * np.sin(3 * ph)
    y *= 1 + 0.4 * np.sin(2 * np.pi * 14 * t)
    return 0.2 * y * np.sqrt(np.sin(np.pi * t / dur)) * np.exp(-t / (dur * 0.7))


def v_bell(rng, size):
    n, t = _t(1.2)
    f = rng.uniform(600, 720) * (1.2 - 0.5 * size)
    y = sum(a * np.sin(2 * np.pi * f * r * t) * np.exp(-t / (0.5 / math.sqrt(r)))
            for r, a in [(1, 1), (2.76, 0.5), (5.4, 0.25), (8.93, 0.12)])
    y[:90] *= np.linspace(0, 1, 90)
    return 0.2 * y


def v_foghorn(rng, size):
    dur = 1.5
    n, t = _t(dur)
    f = 70 + 40 * (1 - size)
    y = sum(np.sin(2 * np.pi * f * k * t) / k for k in range(1, 9))
    e = np.minimum(1, t / 0.2) * np.minimum(1, (dur - t) / 0.4)
    return 0.15 * y * e


def v_lap(rng, size):
    n, t = _t(0.25)
    f0 = rng.uniform(200, 400) * (1.4 - 0.8 * size)
    f = f0 * (1 + 1.2 * (1 - np.exp(-t / 0.05)))
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.07)
    y += 0.3 * _bandnoise(rng, n, 300, 2000) * np.exp(-t / 0.05)
    y[:80] *= np.linspace(0, 1, 80)
    return 0.4 * y


VOICES = {
    "bird": v_bird, "cricket": v_cricket, "drop": v_drop, "knock": v_knock,
    "snap": v_snap, "rustle": v_rustle, "gull": v_gull, "bell": v_bell,
    "foghorn": v_foghorn, "lap": v_lap,
}


# Beds: f(rng, intensity_per_sample) -> mono array
def bed_wind(rng, inten):
    n = len(inten)
    t = np.arange(n) / SR
    gust = 0.6 + 0.4 * np.sin(2 * np.pi * 0.07 * t + rng.uniform(0, 6))
    return _bandnoise(rng, n, 150, 1100) * gust * (0.02 + 0.12 * inten)


def bed_stream(rng, inten):
    n = len(inten)
    return _bandnoise(rng, n, 800, 5000) * (0.015 + 0.09 * inten)


def bed_surf(rng, inten):
    n = len(inten)
    t = np.arange(n) / SR
    swell = (0.5 + 0.5 * np.sin(2 * np.pi * t / 7 + rng.uniform(0, 6))) ** 2
    sos = signal.butter(2, 700, btype="low", fs=SR, output="sos")
    y = signal.sosfilt(sos, rng.standard_normal(n))
    y /= np.std(y) + 1e-9
    return y * (0.3 + 0.7 * swell) * (0.025 + 0.14 * inten)


BEDS = {"wind": bed_wind, "stream": bed_stream, "surf": bed_surf}


# -------------------------------------------------------------- samples ---

def load_samples(root):
    bank = {}
    if not root:
        return bank
    for name in sorted(os.listdir(root)):
        d = os.path.join(root, name)
        if not os.path.isdir(d):
            continue
        clips = []
        for fn in sorted(os.listdir(d)):
            if not fn.lower().endswith(".wav"):
                continue
            sr, data = wavfile.read(os.path.join(d, fn))
            x = data.astype(np.float64)
            if data.dtype.kind == "i":
                x /= np.iinfo(data.dtype).max
            elif data.dtype.kind == "u":
                x = x / np.iinfo(data.dtype).max * 2 - 1
            if x.ndim > 1:
                x = x.mean(axis=1)
            if sr != SR:
                x = np.interp(np.arange(0, len(x), sr / SR), np.arange(len(x)), x)
            x /= np.max(np.abs(x)) + 1e-9
            clips.append(x)
        if clips:
            bank[name] = clips
            print(f"  loaded {len(clips)} sample(s) for '{name}'")
    return bank


def sample_voice(clips, rng, size):
    x = clips[int(rng.integers(len(clips)))]
    rate = 1.3 - 0.6 * size  # bigger packets play lower/slower
    idx = np.arange(0, len(x) - 1, rate)
    return 0.5 * np.interp(idx, np.arange(len(x)), x)


def sample_bed(clips, rng, inten):
    n = len(inten)
    x = clips[int(rng.integers(len(clips)))]
    start = int(rng.integers(len(x)))
    loop = np.tile(np.roll(x, -start), n // len(x) + 1)[:n]
    return loop * (0.05 + 0.3 * inten)


# --------------------------------------------------------------- render ---

def render(packets, mapping, args):
    rng = np.random.default_rng(args.seed)
    bank = load_samples(args.samples)

    t_end = max(p["t"] for p in packets)
    n = int((t_end / args.speed + 2.0) * SR)
    left, right = np.zeros(n), np.zeros(n)

    nbins = int(t_end / args.bin) + 1
    totals = np.zeros(nbins)
    groups = defaultdict(list)
    voice_counts = Counter()
    for p in packets:
        b = int(p["t"] / args.bin)
        v = classify(p, mapping)
        groups[(b, v)].append(p)
        totals[b] += 1
        voice_counts[v] += 1

    # Keynote bed: packet rate -> intensity (log scale), smoothed
    rate = totals / args.bin
    inten_bins = np.clip(np.log10(1 + rate) / np.log10(1 + args.max_rate), 0, 1)
    centers = (np.arange(nbins) + 0.5) * args.bin / args.speed * SR
    inten = np.interp(np.arange(n), centers, inten_bins)
    sos = signal.butter(1, 2.0, btype="low", fs=SR, output="sos")
    inten = np.clip(signal.sosfiltfilt(sos, inten), 0, 1)

    bed_name = mapping.get("bed")
    if bed_name:
        for ch in (left, right):  # independent noise per channel = stereo width
            if bed_name in bank:
                ch += sample_bed(bank[bed_name], rng, inten)
            elif bed_name in BEDS:
                ch += BEDS[bed_name](rng, inten)
            else:
                sys.exit(f"Unknown bed '{bed_name}'. Options: {', '.join(BEDS)}")

    # Signals: discrete events per (bin, voice)
    for (b, voice), pk in groups.items():
        if voice not in bank and voice not in VOICES:
            sys.exit(f"Unknown voice '{voice}'. Options: {', '.join(VOICES)}")
        count = len(pk)
        size = np.mean([np.clip((p["len"] - 60) / 1454, 0, 1) for p in pk])
        pan = np.mean([pan_for(p, args.target) for p in pk])
        gain = args.event_gain * (1 + math.log10(count))
        for _ in range(min(count, args.max_events)):
            snd = sample_voice(bank[voice], rng, size) if voice in bank else VOICES[voice](rng, size)
            snd = snd * gain
            s = int((b * args.bin + rng.uniform(0, args.bin)) / args.speed * SR)
            e = min(n, s + len(snd))
            if e <= s:
                continue
            p = np.clip(pan + rng.normal(0, 0.05), 0, 1)
            left[s:e] += snd[: e - s] * math.cos(p * math.pi / 2)
            right[s:e] += snd[: e - s] * math.sin(p * math.pi / 2)

    stereo = np.stack([left, right], axis=1)
    if args.normalize:
        stereo /= np.max(np.abs(stereo)) / 0.89 + 1e-9
    else:
        stereo = np.tanh(stereo * args.master)  # fixed gain: loudness comparable across captures
    return stereo, voice_counts


def main():
    ap = argparse.ArgumentParser(description="Sonify a network capture as a soundscape.")
    ap.add_argument("input", help=".pcap/.pcapng (needs tshark) or tshark CSV export")
    ap.add_argument("-m", "--mapping", required=True, help="mapping JSON file")
    ap.add_argument("-o", "--output", default="soundscape.wav")
    ap.add_argument("--samples", help="folder of your own recordings: DIR/<voice>/*.wav")
    ap.add_argument("--target", help="target IP: its outgoing traffic pans right, incoming left")
    ap.add_argument("--bin", type=float, default=0.1, help="time bin in seconds (default 0.1)")
    ap.add_argument("--speed", type=float, default=1.0, help=">1 compresses time (default 1 = real time)")
    ap.add_argument("--max-events", type=int, default=4, help="max sounds per voice per bin")
    ap.add_argument("--max-rate", type=float, default=2000, help="packets/sec treated as full keynote intensity")
    ap.add_argument("--event-gain", type=float, default=0.35)
    ap.add_argument("--master", type=float, default=1.0)
    ap.add_argument("--normalize", action="store_true",
                    help="peak-normalize (breaks loudness comparisons between captures)")
    ap.add_argument("--seed", type=int, default=1, help="random seed, for reproducible renders")
    args = ap.parse_args()

    with open(args.mapping) as fh:
        mapping = json.load(fh)

    print(f"Reading {args.input} ...")
    packets = load_packets(args.input)
    print(f"  {len(packets)} packets over {max(p['t'] for p in packets):.1f}s")
    print(f"Rendering with mapping '{mapping.get('name', args.mapping)}' ...")
    audio, counts = render(packets, mapping, args)

    wavfile.write(args.output, SR, (audio * 32767).astype(np.int16))
    log = {
        "input": os.path.abspath(args.input),
        "mapping": mapping,
        "settings": {k: v for k, v in vars(args).items() if k not in ("input", "mapping")},
        "packets": len(packets),
        "packets_per_voice": dict(counts.most_common()),
    }
    log_path = os.path.splitext(args.output)[0] + ".log.json"
    with open(log_path, "w") as fh:
        json.dump(log, fh, indent=2)
    print(f"Wrote {args.output} ({len(audio) / SR:.1f}s) and {log_path}")
    for v, c in counts.most_common():
        print(f"  {v:10s} {c}")


if __name__ == "__main__":
    main()
