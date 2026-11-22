# Design

How the score is meant to work, why, and what was tried and dropped along the way.

## Goals

1. **Sound good enough to leave on all day.** If it's tiring or ugly, nobody will want to listen, and the information doesn't matter.
2. **Keep the attack information.** A listener should be able to recover what happened from the audio alone.
3. **Work live.** The same system should run on live traffic and not only on pre-rendered files.

## Principles

- **Alert by change rather than volume.** People tune out steady sound, and loud alerts can cause alert fatigue. Each state should sound different to clearly indicate change while maintaining good sound.
- **Match intensity to evidence.** An INFO alert should barely register while an ET MALWARE alert should clearly change the music.
- **Leave space.** Part 1 showed that dense sound masks events. A sparse baseline leaves room for changes to stand out.
- **One musical element per fact.** Two facts never share a sound dimension, so it's always clear what changed.
- **The sound is an attention cue and not a dashboard.** The music should tell an analyst that something changed and roughly what kind of thing. Exact IPs, hostnames and hashes stay on screen.

## The facts the music has to carry

Based on what SOC monitoring tools usually report and what an analyst asks during triage (Is it real? How bad? Is it ongoing? Is it spreading? Is data leaving?):

| # | Fact | Example from the captures |
|---|---|---|
| 1 | Stage changes and when they happen | baseline → infection → C2 |
| 2 | Strength of evidence | ET INFO vs ET MALWARE |
| 3 | Check-in rhythm (beaconing interval and regularity) | WarmCookie, about every 5.8 s |
| 4 | Number of servers contacted | WarmCookie 1, FormBook 15 |
| 5 | Behavior type | steady beaconing, roaming servers, one long session |
| 6 | Duration, and whether it's still going | RMS, a 37-minute session |
| 7 | Data volume and direction | RMS, 434 KB up and about 14 MB down |
| 8 | Key one-time events | FormBook's second EXE download |
| 9 | Overall activity level | new flows per 10 s |

Left out on purpose: exact indicators (IPs, domains, hashes), which ears can't carry, and the number of infected hosts, which can't be tested, at least with these malware captures.

"Behavior type" replaced an earlier "which malware family" goal. Since analysts usually get family names from signatures, not from the traffic itself, so recognizing behavior is the more realistic thing to test.

## Mapping

| # | Fact | Musical element | Status |
|---|---|---|---|
| 1 | Stage | Arrangement: layers fade in by state | **Done** |
| 2 | Evidence | Size of the accent each alert gets; only strong evidence changes the stage | Planned |
| 3 | Check-in rhythm | One pizzicato note per check-in | **Done** (not yet snapped to the beat) |
| 4 | Servers | A different pitch and stereo position for each destination | Planned |
| 5 | Behavior type | No sound of its own; it emerges from 3, 4 and 6 | Follows from 3, 4 and 6 |
| 6 | Duration | A low drone that lasts as long as a session | Planned (needs flow end times) |
| 7 | Data volume / direction | The drone's level and register follow bytes | Planned (needs byte counts) |
| 8 | Key one-time events | A distinct short motif | Planned |
| 9 | Activity level | Extra percussion density | Planned |

Stage, evidence and check-ins are always active, while the rest only sounds when that behavior is happening so as to avoid clutter.

**Snapping check-ins to the beat** will move each one by up to one sixteenth note (about 0.18 s at 86 BPM). Beacon intervals are measured in seconds, so the rhythm should survive. This is a deliberate trade between accuracy and musicality, and the amount it shifts timing will be measured.

## Score

**Key and tempo:** D minor at 86 BPM. Originally, I wanted to create a similar sound to tracks from Ours Samplus, one of which was in E minor at about 87 BPM, but D minor at 86 had far more matching loops, and the feel matters more than the exact key. Loops at 172 BPM lock in as double-time.

**Layers:**

| State | What you hear |
|---|---|
| Baseline | Jazz-hop groove: Rhodes, upright bass, acoustic guitar, soft boom-bap drums |
| Infection | A dark violin joins (8 bars) |
| C2 | A dark orchestra feel: a driving cello pattern, dark low strings, a second string layer and taiko. The baseline drops 4 dB, and the drums keep going. Every C2 event plays a plucked cello note on D. |

C2 is meant to sound like the same piece getting darker, not a different song. It's recognizable because it adds **low register and driving rhythm**, while the violin in infection is sustained and high.

**FMOD layout:** one continuous `Level` parameter (0 baseline, 1 infection, 2 C2) with a Seek modulator (0.5 per second, about 2 seconds per step). All loops start together and loop side by side, and each track's volume is automated against `Level`. See the [Part 2 README](../README.md#the-score).

## Decisions

| Decision | Why | Instead of |
|---|---|---|
| Sonify the timeline, not packets | Part 1's packet mapping was mostly noise, with common traffic masking events | Packet-to-sound mapping (Part 1) |
| FMOD (game audio engine) | The score works like game music: layers that follow state, built from real recordings, with musical fades. It also already worked. | Pure Data. Pd would suit fine-grained, data-driven mapping and an open-source Linux version, so it's worth revisiting for live mode. |
| Continuous `Level` with Seek | Labeled parameters are discrete, so volume jumped instead of fading | Labeled `State` parameter |
| All loops always running, faded by volume | Layers stay on the beat whenever they enter, so tension and threat can be rhythmic | Layers starting when their state begins (they'd start off the beat) |
| Real recorded loops only | Synthesized sounds felt fake (Part 1, and a synthesized v1 here) | Procedurally generated tones |
| Jazz-hop baseline | Warm and easy to leave on, in the style of Ours Samplus and Tokyo jazz-hop | Busier chillhop |
| Orchestral C2 | Escalates the violin's mood and blends with the groove while still sounding clearly different | **Phonk** (tested: cowbell melody, 808 drums). It felt out of place like a different genre, double-time and much louder. |
| Pizzicato check-in | Short, pitched and orchestral. It sits above the low-heavy C2 mix without being loud, and it can be retuned per server. | A synthesized blip |
| Machine-learning polish only as a separate stage | Keeps the live-versus-polished comparison clean | Generating the live layers with AI |

Genres considered for the overall direction: lo-fi/chillhop, trip-hop, ambient, downtempo/dub techno, cinematic, nightcore, Tokyo jazz-hop and phonk. Nightcore was ruled out right away (dense, tiring, usually edits of other people's songs).

## Evaluation plan

Each capture will be rendered three ways:

1. **Plain:** direct sonification like Part 1
2. **Live score:** this system
3. **Polished:** the live recording re-arranged with a music model in a mode that keeps melody, chords and structure

For each version: try to decode the nine facts back out of the audio (stage onset times, check-in count and intervals, distinct pitches as server count, and so on), compare captures of the same behavior, and keep listening notes. The question is how many facts survive each step.
