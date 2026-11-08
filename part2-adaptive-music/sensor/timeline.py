import argparse
import json
import socket
import time
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

DATA_DIR = Path.home() / "sonification" / "output"
TIMELINE_DIR = Path(__file__).resolve().parent.parent / "timelines"
PC_IP = "192.168.1.212"
PORT = 9500
ACTIVITY_WINDOW = 10  # seconds per background activity reading

# Natureforce's C2 isn't flagged by ET Open, so its server comes from our flow analysis
CAPTURES = {
    "2024-08-15-WarmCookie": {"family": "WarmCookie"},
    "2026-08-09-First-to-Last": {"family": "FormBook"},
    "2026-10-01-Natureforce": {"family": "RMS", "c2_ip": "195.63.128.106"},
}


def parse_time(ts):
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S.%f%z")


def classify(signature):
    s = signature.lower()
    if "cnc" in s or "c2" in s:
        return "c2"
    if any(w in s for w in ("executable", "exe or dll", "mz response")):
        return "download"
    if s.startswith("et malware"):
        return "malware"
    return "info"


def load_events(name):
    info = CAPTURES[name]
    events, flow_starts = [], []

    with open(DATA_DIR / name / "eve.json") as f:
        for line in f:
            e = json.loads(line)
            if e["event_type"] == "alert":
                events.append({
                    "time": parse_time(e["timestamp"]),
                    "type": classify(e["alert"]["signature"]),
                    "detail": e["alert"]["signature"],
                    "dest": e.get("dest_ip"),
                })
            elif e["event_type"] == "flow":
                start = parse_time(e["flow"]["start"])
                flow_starts.append(start)
                if info.get("c2_ip") in (e.get("src_ip"), e.get("dest_ip")):
                    events.append({"time": start, "type": "c2",
                                   "detail": "C2 session (flow)", "dest": info["c2_ip"]})

    # How many new connections start in each window, including quiet ones
    if flow_starts:
        first = min(flow_starts)
        counts = Counter(int((t - first).total_seconds() // ACTIVITY_WINDOW) for t in flow_starts)
        for b in range(max(counts) + 1):
            events.append({"time": first + timedelta(seconds=b * ACTIVITY_WINDOW),
                           "type": "activity", "detail": f"{counts.get(b, 0)} new flows",
                           "flows": counts.get(b, 0)})

    return sorted(events, key=lambda e: e["time"])


def build_timeline(name):
    events = load_events(name)
    family = CAPTURES[name]["family"]
    start = events[0]["time"]
    state = "baseline"
    timeline, seen = [], set()

    for e in events:
        # Several alerts often fire for the same moment; keep one per type per second
        key = (e["type"], e["time"].replace(microsecond=0))
        if key in seen:
            continue
        seen.add(key)

        if e["type"] == "download" and state == "baseline":
            state = "infection"
        elif e["type"] in ("c2", "malware"):
            state = "c2"

        timeline.append({
            "t": round((e["time"] - start).total_seconds(), 3),
            "time": e["time"].strftime("%H:%M:%S"),
            "type": e["type"],
            "state": state,
            "family": family if e["type"] in ("c2", "malware") else None,
            "detail": e["detail"],
            "dest": e.get("dest"),
            "flows": e.get("flows"),
        })

    return timeline


def play(timeline, speed):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    t0 = time.monotonic()
    for e in timeline:
        wait = e["t"] / speed - (time.monotonic() - t0)
        if wait > 0:
            time.sleep(wait)
        sock.sendto(json.dumps(e).encode(), (PC_IP, PORT))
        if e["type"] != "activity":
            print(f'{e["time"]}  {e["state"]:<9} {e["type"]:<9} {e["detail"]}')


def main():
    parser = argparse.ArgumentParser(description="Build and play a capture's attack timeline")
    parser.add_argument("capture", choices=CAPTURES)
    parser.add_argument("--play", action="store_true", help="send the timeline to the desktop")
    parser.add_argument("--speed", type=float, default=1.0, help="playback speed, e.g. 20 for testing")
    args = parser.parse_args()

    timeline = build_timeline(args.capture)
    TIMELINE_DIR.mkdir(exist_ok=True)
    out = TIMELINE_DIR / f"{args.capture}.json"
    out.write_text(json.dumps(timeline, indent=1))

    counts = Counter(e["type"] for e in timeline)
    print(f"{len(timeline)} events saved to {out}")
    print(", ".join(f"{k}: {v}" for k, v in sorted(counts.items())))

    if args.play:
        play(timeline, args.speed)


if __name__ == "__main__":
    main()