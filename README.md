# Network Sonification Framework

Turning malware network traffic into sound, and measuring what survives the trip.

## Research question

**Can network traffic be turned into music that sounds good without losing what it reveals about an attack?**

Turning a packet capture into sound has been done before. What prior work doesn't do is measure how much of the attack is still recoverable once the sound is made to be pleasant. This project builds a pipeline from capture to music, renders each capture three ways (plain sonification, live adaptive score, polished version), and compares how much attack information each one keeps.

The long-term goal is a live monitoring tool: music an admin or SOC analyst can leave on all day, where a change in the music means something on the network changed.

## Structure

```
part1-soundscapes/        Part 1: packets mapped directly to nature sounds
  netscape.py             pcap -> soundscape WAV renderer
  mappings/               forest and coastal mappings (JSON)
  Field Notes/            listening notes

part2-adaptive-music/     Part 2: attack timelines driving an adaptive score
  sensor/                 timeline.py (Suricata eve.json -> timeline, UDP playback)
  studio/                 listener.py (UDP -> FMOD), FMOD project, sound tools
  timelines/              timelines for each capture (JSON)
  analysis/               timeline statistics
  docs/                   design, sources and credits
  Field Notes/            session notes
```

## Part 1: Soundscapes

Every packet became a sound in a forest or coastal soundscape (protocol = species, packet size = pitch, host = stereo position). It mostly produced noise. Common traffic like HTTPS dominated, loud voices masked quieter ones (gull cries buried an entire coastal render), and the renderer held everything in memory, so captures had to be compressed with `--speed 15`.

The main lesson: how traffic is mapped to sound is never neutral, and mapping everything means hearing nothing. See [`part1-soundscapes/Field Notes`](part1-soundscapes/Field%20Notes).

## Part 2: Adaptive music engine

Instead of sonifying packets, Part 2 sonifies **what the packets mean**. Suricata turns a capture into alerts and flows, a timeline script turns those into attack states and events, and the timeline drives an adaptive score in FMOD the way game music follows gameplay.

```
pcap -> Suricata (eve.json) -> timeline.py -> UDP JSON -> listener.py -> FMOD score
        [lab laptop]                                      [desktop]
```

- **Baseline:** warm jazz-hop groove (Rhodes, upright bass, guitar, soft drums)
- **Infection:** a dark violin joins
- **C2:** a dark orchestra enters (driving cello, low strings, taiko), the groove drops back, and every C2 check-in plays a plucked cello note

Details: [`part2-adaptive-music/README.md`](part2-adaptive-music/README.md) and [`docs/design.md`](part2-adaptive-music/docs/design.md).

## Status

| Stage | Status |
|---|---|
| Understand: Suricata + timelines for 3 captures | Done |
| Perform live: adaptive score in FMOD driven over UDP | Working with real recorded loops; full capture runs next |
| Map all nine attack facts to sound | Stage and check-ins done; the rest designed |
| Polish (re-arrangement of recordings) | Planned |
| Compare plain / live / polished versions | Planned |

## Captures

Three public exercises from [malware-traffic-analysis.net](https://www.malware-traffic-analysis.net): WarmCookie, FormBook and RMS RAT. Pcaps and malware archives are never stored in this repo. See [`docs/sources.md`](part2-adaptive-music/docs/sources.md).

## Safety

Malware archives live only on an isolated lab laptop and stay outside the repo. Pcaps are analyzed offline with Suricata and are never replayed onto a real interface.
