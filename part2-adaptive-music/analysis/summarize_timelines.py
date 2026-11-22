"""Prints the state changes, check-in timing and destinations for each timeline.

    python3 summarize_timelines.py [timelines_dir]
"""
import json
import statistics
import sys
from collections import Counter
from pathlib import Path

folder = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "timelines")

for path in sorted(folder.glob("*.json")):
    events = json.loads(path.read_text())
    counts = Counter(e["type"] for e in events)
    print(f"{path.stem}: {len(events)} events over {events[-1]['t'] / 60:.1f} min  {dict(counts)}")

    state = None
    for e in events:
        if e["state"] != state:
            state = e["state"]
            print(f"  {e['time']} (+{e['t'] / 60:.1f} min)  -> {state:<9} {e['detail']}")

    c2 = [e for e in events if e["type"] == "c2"]
    if len(c2) > 1:
        gaps = [b["t"] - a["t"] for a, b in zip(c2, c2[1:])]
        dests = {e["dest"] for e in c2}
        print(f"  c2 events: {len(c2)}, gap median {statistics.median(gaps):.1f} s, "
              f"mean {statistics.mean(gaps):.1f} s, range {min(gaps):.1f}-{max(gaps):.1f} s, "
              f"{len(dests)} destination(s)")
    else:
        print(f"  c2 events: {len(c2)}")
    print()
