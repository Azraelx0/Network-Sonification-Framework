# Part 2: Adaptive Music Engine

A malware capture becomes an attack timeline, and the timeline drives a live adaptive score. The music changes when the attack changes.

## How it works

```
Lab laptop (Ubuntu)                                 Desktop (Windows 11)
pcap -> Suricata 8.0.3 -> eve.json -> timeline.py ---UDP 9500---> listener.py -> FMOD Engine 2.03.15
                                         |                                      (NetworkScore banks)
                                         v
                                    timelines/*.json
```

1. **Suricata** (ET Open rules, `TZ=UTC`, `-k none`) produces alerts and flow records for each capture.
2. **`sensor/timeline.py`** sorts the events (eve.json isn't time-ordered), classifies alerts as `download`, `c2`, `malware` or `info`, adds an `activity` reading every 10 s with the number of new flows, removes duplicates (same type, same second), and tracks the attack state: `baseline -> infection -> c2`. It saves the timeline to `timelines/` and, with `--play`, sends each event over UDP at real speed or faster.
3. **`studio/listener.py`** receives each event and drives FMOD through the FMOD Studio C API (Python `ctypes`). The state sets a continuous `Level` parameter (baseline 0, infection 1, C2 2), and every `c2` event triggers a check-in sound.
4. **FMOD** fades the layers in and out as `Level` glides between values.

### Message format

```json
{"t": 354.117, "time": "02:13:26", "type": "c2", "state": "c2", "family": "FormBook",
 "detail": "ET MALWARE FormBook CnC Checkin (GET) M5", "dest": "...", "flows": null}
```

## Running it

**Desktop (PowerShell):** build the banks in FMOD Studio (F7) first.

```powershell
cd part2-adaptive-music\studio
python .\listener.py --demo   # baseline -> infection -> c2 with no laptop needed
python .\listener.py          # listen for the laptop; press q to stop
```

**Laptop (bash):**

```bash
cd part2-adaptive-music/sensor
python3 timeline.py 2026-08-09-First-to-Last              # build the timeline only
python3 timeline.py 2026-08-09-First-to-Last --play --speed 5
```

`PC_IP` in `timeline.py` must match the desktop's address. Captures: `2024-08-15-WarmCookie`, `2026-08-09-First-to-Last`, `2026-10-01-Natureforce`. `--speed` only changes how fast events are sent; the audio always plays at normal speed.

### Requirements

- Laptop: Suricata 8.x with ET Open rules, Python 3. Suricata output goes in `~/sonification/output/<capture>/eve.json`, outside the repo.
- Desktop: FMOD Studio 2.03.15 (to edit and build), FMOD Engine 2.03.15 (the listener loads its `fmod.dll` and `fmodstudio.dll`), Python 3.
- Sound files are not in the repo (see [Sounds](#sounds)).

## The score

FMOD project: `studio/fmod/NetworkScore.fspro`.

**`Network` event:** one continuous parameter, `Level` (0 to 2), with a Seek modulator at 0.5 per second, so each change glides over about 2 seconds. All four loops start together when the event starts and loop side by side, so they stay on the beat no matter when a layer fades in.

| Track | Sound | Volume by Level |
|---|---|---|
| Audio 1 | `baseline.wav`: Rhodes, upright bass, guitar | 0 dB, dropping to -4 dB from 1 to 2 |
| Audio 2 | `tension.wav`: dark violin | silent at 0, full at 1 |
| Audio 3 | `threat.wav`: cello ostinato, dark strings, taiko | silent at 1, full at 2 |
| Audio 4 | `drums.wav`: soft boom-bap | constant |

**`Checkin` event:** a single cello pizzicato on D, played once per C2 event.

Everything is in **D minor at 86 BPM**. Loops are 4 bars (11.163 s) or 8 bars (22.326 s).

## Sounds

The sounds are Looperman loops plus one CC0 sample from Freesound. They are **not committed**, because Looperman's license doesn't allow redistributing loops as-is. The loops and credits are listed in [`docs/sources.md`](docs/sources.md).

### Recreating the sound files

`studio/tools/` has optional helper scripts that make recreating the project easier. They turn the downloaded loops into the five files FMOD uses, with the same edits as the originals: matching loop lengths, two small tempo changes (pitch unchanged), tiny fades so loops don't click when they repeat, and volume balancing. No other effects are applied and the mixing itself is done in FMOD.

1. Download the loops in `docs/sources.md` into one folder, keeping Looperman's file names, and download the pizzicato from Freesound.
2. Run the scripts (needs Python with `numpy` and `soundfile`; `build_threat.py` also needs the [Rubber Band](https://breakfastquay.com/rubberband/) command-line tool):

```bash
cd part2-adaptive-music/studio
python3 tools/build_stems.py <loops_dir> sounds          # baseline.wav, drums.wav, tension.wav
python3 tools/build_threat.py <loops_dir> sounds         # threat.wav
python3 tools/build_checkin.py <pizzicato.wav> sounds sounds/threat.wav sounds   # checkin.wav + a preview
```

3. Copy the five WAVs into `fmod/Assets`, open the project in FMOD Studio and build (F7).

## More

- [`docs/design.md`](docs/design.md): the facts the music has to carry, the mapping, sound design decisions and what was rejected
- [`analysis/timeline-summary.md`](analysis/timeline-summary.md): what each capture's timeline looks like, and what that means for the music
- [`Field Notes/`](Field-Notes): session notes

## Known limitations

- `listener.py` is Windows-only (the FMOD DLLs).
- Check-ins play when they arrive as they aren't snapped to the beat yet.
- `timeline.py` only records when a flow **starts**, so a long C2 session shows up as one event (see Natureforce in the analysis).
- Any `ET MALWARE` alert moves the state straight to `c2`, even without a C2 alert.
- Natureforce's RMS label comes from the analyst's alert only. ET Open caught the download but not the C2.
