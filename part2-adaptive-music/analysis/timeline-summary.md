# Timeline Summary

What each capture's timeline looks like, and what that means for the music. Reproduce with:

```bash
python3 analysis/summarize_timelines.py
```

## Overview

| Capture | Length | State changes | C2 events | Gap between C2 events | Destinations |
|---|---|---|---|---|---|
| WarmCookie (2024-08-15) | 32.7 min | baseline → infection at 2.3 min → c2 at 3.3 min | 305 | median 5.7 s, mean 5.8 s (0.2–51.1 s) | 1 |
| FormBook (2026-08-09) | 14.0 min | baseline → **c2** at 5.9 min (no infection stage) | 18 | median 24.6 s, mean 27.3 s (12.1–59.6 s) | 15 IPs |
| RMS (2026-10-01) | 40.0 min | baseline → infection at 3.2 min → c2 **8 s later** | **1** | n/a | 1 |

`activity` events (new flows per 10 s) make up most of the remaining events: 197, 85 and 241.

## WarmCookie: the full arc

The only capture that goes through all three states with time to hear each one. An EXE download (ET INFO) starts infection, and the first CnC alert a minute later starts C2. After that, 305 check-ins go to a single server (72.5.43.29) about every 5.8 seconds for half an hour.

**In the music:** baseline, then the violin, then the orchestra, followed by a steady pluck roughly every 6 seconds. Regular beaconing becomes a regular rhythm, so this is the clearest test of fact 3 (check-in rhythm).

## FormBook: a detection gap becomes a missing stage

The first strong alert is a CnC check-in at 5.9 minutes, so the timeline goes straight from baseline to C2. The only download alert (`ET HUNTING SUSPICIOUS Dotted Quad Host MZ Response`, the second EXE) comes five minutes after C2 starts. The initial infection didn't trigger an ET Open rule, so the timeline never saw it, and neither does the music: the violin stage never plays alone.

The 18 check-ins go to 15 different IPs about every 25 seconds. Several are Cloudflare addresses, so hostnames are probably a better count of distinct servers than IPs.

**In the music:** a sudden jump from calm to the orchestra, then sparse plucks. Right now every pluck is the same note, so the "15 different servers" fact is lost. That's what per-destination pitch and pan (fact 4) is meant to fix.

## RMS (Natureforce): a long session that's almost silent

A download from 107.175.82.242:9000 starts infection, and 8 seconds later a single flow to the C2 server (195.63.128.106) begins. That flow stays open for about 37 minutes (434 KB up, about 14 MB down), but `timeline.py` only records when flows **start**, so the entire session is **one** C2 event.

**In the music:** the orchestra comes in and keeps playing, but nothing marks that the session is still active, how long it lasts or how much data moves. A listener hears "something is wrong" with no detail.

This is a concrete example of attack information lost **before** any sound is made: duration and data volume (facts 6 and 7) don't exist in the timeline. Fixing it needs flow end times and byte counts (Suricata flow records have totals at flow end; bytes over time needs something like `tshark -z io,stat`).

## Takeaways

1. **The music can only carry what detection sees.** FormBook's missing infection stage and RMS's single C2 event are both gaps in the input, not in the sound design.
2. **The three captures test different facts:** WarmCookie tests rhythm, FormBook tests destinations, and RMS tests duration and volume. Together they cover the main behavior types.
3. **Event count doesn't equal importance.** RMS has the longest C2 activity and the fewest C2 events. The mapping has to represent ongoing state, not just discrete events.
