# Capture Sources

All captures are from malware-traffic-analysis.net. Pcaps are not stored in this repo.

| Capture | Exercise page | Family (label status) |
|---|---|---|
| 2024-08-15 WarmCookie | https://www.malware-traffic-analysis.net/2024/08/15/index.html | WarmCookie (confirmed by ET Open alerts) |
| 2026-08-09 First to Last | https://www.malware-traffic-analysis.net/2026/08/09/index.html | FormBook (confirmed by ET Open alerts) |
| 2026-10-01 Natureforce | https://www.malware-traffic-analysis.net/2026/10/01/index.html | RMS RAT (per analyst alert) |

## Notes
- Suricata 8.0.3 with ET Open rules, run with TZ=UTC and -k none.
- Natureforce C2 appears in the pcap as 195.63.128.106; the write-up lists 195.64.128.106.
- Natureforce EXE (runner_ilove.exe) SHA-256: b789adce70c028a6d17be45ec34667aa95586350ee0c4057e75b138b1ad35061