# Sources

## Captures

All captures are from malware-traffic-analysis.net. Pcaps are not stored in this repo.

| Capture | Exercise page | Family (label status) |
|---|---|---|
| 2024-08-15 WarmCookie | https://www.malware-traffic-analysis.net/2024/08/15/index.html | WarmCookie (confirmed by ET Open alerts) |
| 2026-08-09 First to Last | https://www.malware-traffic-analysis.net/2026/08/09/index.html | FormBook (confirmed by ET Open alerts) |
| 2026-10-01 Natureforce | https://www.malware-traffic-analysis.net/2026/10/01/index.html | RMS RAT (per analyst alert) |

### Notes
- Suricata 8.0.3 with ET Open rules, run with TZ=UTC and -k none.
- Natureforce C2 appears in the pcap as 195.63.128.106; the write-up lists 195.64.128.106.
- Natureforce EXE (runner_ilove.exe) SHA-256: b789adce70c028a6d17be45ec34667aa95586350ee0c4057e75b138b1ad35061

## Sounds

Audio files are not committed. Looperman loops are royalty-free for registered users but may not be redistributed as-is. To rebuild the sounds, download the loops below and run the scripts in `studio/tools/`.

### Loops (Looperman)

| Used in | Loop | Uploader | BPM / key | Processing |
|---|---|---|---|---|
| baseline | [Clocks - Epiano - Part 4](https://www.looperman.com/loops/detail/436900/clocks-epiano-part-4-free-86bpm-rnb-rhodes-piano-loop) | prodTebas | 86 / Dm | level |
| baseline | [Clocks - Acoustic Bass - Part 1](https://www.looperman.com/loops/detail/436896/clocks-acoustic-bass-part-1-free-86bpm-rnb-bass-guitar-loop) | prodTebas | 86 / Dm | level, declick (ends mid-note) |
| baseline | [Clocks - Guitar Chords - Part 2](https://www.looperman.com/loops/detail/436898/clocks-guitar-chords-part-2-free-86bpm-rnb-acoustic-guitar-loop) | prodTebas | 86 / Dm | level |
| baseline (optional) | [Skipit Horns](https://www.looperman.com/loops/detail/406142/skipit-horns-free-86bpm-soul-brass-loop) | Antronical | 86 / Dm | level |
| drums | [East Side 90s](https://www.looperman.com/loops/detail/432181/east-side-90s-free-86bpm-boom-bap-drum-loop) | TheAttic | 86 | 2 bars repeated to 4 |
| tension | [Southside x Cubeats Type Violin](https://www.looperman.com/loops/detail/371921/southside-x-cubeats-type-violin-free-86bpm-trap-violin-loop) | DaraOnTheTrack | 86 / Dm | level, declick |
| threat | [James Blake Cello](https://www.looperman.com/loops/detail/429206/james-blake-cello-free-172bpm-electronic-strings-loop) | Tham0s | 172 / Dm | level |
| threat | [Strings - Prodtiptoe](https://www.looperman.com/loops/detail/309057/strings-prodtiptoe-free-86bpm-hip-hop-strings-loop) | prodtiptoe | 86 / Dm | level |
| threat | [Jysk Strings](https://www.looperman.com/loops/detail/400239/jysk-strings-free-88bpm-orchestral-strings-loop) | Antronical | 88 / Dm | stretched to 86 |
| threat | [Rising Tension - Taiko Drums](https://www.looperman.com/loops/detail/339315/rising-tension-taiko-drums-170bpm-free-170bpm-cinematic-drum-loop) | HennieDame | 170 | stretched to 172 |

Antronical asks for credit on their loops.

### One-shots

| Used in | Sound | Author | License |
|---|---|---|---|
| check-in | [Cello Section - tight pizzicato - D5](https://freesound.org/people/sgossner/sounds/372755/) (VSCO 2 Community Edition) | sgossner / Versilian Studios | CC0 |

### Tried and not used

| Loop | Uploader | Why not |
|---|---|---|
| [Six Days - Drums 808](https://www.looperman.com/loops/detail/433723/six-days-drums-808-free-172bpm-trap-drum-loop) | T3Voon | Phonk C2 layer, felt out of place |
| [Memphis Cowbell](https://www.looperman.com/loops/detail/398830/memphis-cowbell-free-165bpm-trap-bells-loop) | IIMSICK | Phonk C2 layer, felt out of place |
| [Rusta Strings](https://www.looperman.com/loops/detail/400133/rusta-strings-free-88bpm-cinematic-strings-loop) | Antronical | Threat option B, too bright |

## Musical references

- *Cascadia*, Aaron Alden with Palo Alto Networks: an album made from security telemetry (composed by hand, not live)
- Ours Samplus, especially "Behind the Moon", "Blue Bird", "Minor Alpha" and "Open a Door" (with Boztown)
