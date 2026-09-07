# W1 — WiFi Scanner + Signal Mapper

ESP32-C6 WiFi scanner with signal strength visualization and channel mapping.

## Overview

This project implements a standalone WiFi scanner that:
- Scans all nearby WiFi networks on each channel
- Displays RSSI-based signal strength bars
- Hops through channels 1-13 automatically
- Generates channel occupancy and signal strength maps
- Tracks encryption types (WPA/WPA2/WPA3)

## Hardware

| Component | Connection | Role |
|-----------|------------|------|
| ESP32-C6 Dev Board | Main board | WiFi scanning, serial output |

## Features

- **RSSI Signal Map**: Visual bar representation of signal strength
- **Channel Occupancy Map**: AP density per channel
- **Channel Hopping**: Automatic sweep across 2.4 GHz channels
- **Encryption Detection**: Identifies WPA/WPA2/WPA3/WEP/OPEN networks

## Serial Output

```
+----------------------------------------------+
|    W1 WiFi Scanner + Signal Mapper           |
|    Board: ESP32-C6                           |
+----------------------------------------------+
Starting scan on channel 1

=== Scan #1 | Channel 1 | 8 networks found ===

+----------------------------------------------+
|        WiFi Signal Strength Map              |
+----------------------------------------------+
| CH01 [#### ] -45 dBm WPA2 MyNetwork         |
| CH06 [##   ] -72 dBM WPA3 GuestNet          |
| CH11 [#####] -28 dBM WPA2 CorpWiFi          |
+----------------------------------------------+
```

## Build & Flash

```bash
arduino-cli compile --fqbn esp32:esp32:esp32c6 firmware/
arduino-cli upload --fqbn esp32:esp32:esp32c6 --port /dev/ttyUSB0 firmware/
```

## Legal Disclaimer

**IMPORTANT: Read before use.**

This project is provided for **educational and authorized security testing purposes only**. 

### Authorization Requirements
- You MUST have explicit written permission from the network owner before using this tool
- Unauthorized interception of network communications is illegal under federal and state laws
- This tool should ONLY be used on networks you own or have written authorization to test

### Legal Framework
- **Computer Fraud and Abuse Act (CFAA)**: Unauthorized access to computer systems is a federal crime
- **Wiretap Act (18 U.S.C. § 2511)**: Interception of electronic communications without consent is illegal
- **State Laws**: Many states have additional computer crime and wiretapping statutes
- **GDPR/CCPA**: Data collection may be subject to privacy regulations

### Acceptable Use
- Testing security of your own networks
- Authorized penetration testing with written scope
- Academic research in controlled lab environments
- Security education and training

### Prohibited Use
- Intercepting communications on networks you don't own
- Attacking infrastructure without authorization (this build scans/replays only bytes, no radio)
- Any activity that violates applicable laws or regulations
- Commercial use without proper licensing

### Regulatory Framework (Passive Scanning)
- **Federal Communications Act (47 U.S.C. § 333)**: Willful interference with authorized radio communications is prohibited.
- **47 CFR Part 15**: Unauthorized intentional radiators are regulated; this scanner is byte-level only and emits nothing.
- **CFAA / ECPA / Wiretap Act**: Scanning or capturing wireless frames without authorization may violate federal and state computer-access and interception laws.

## Live Lab Test Plan

Offline (this repo, no radio):
1. `python3 firmware/wifi_scanner.py` — synthesize 10 lab APs (6 visible + 4 hidden SSIDs)
   as bytes, parse them back, validate MACs; scan_ok=true, exit 0.
2. `python3 firmware/wifi_scanner.py --gen-fixture reports/scan.pcap --pcap reports/scan.pcap
   --json reports/w1.json` — fixture round-trip (exit 0).
3. `python3 -m unittest discover -s tests` — byte-exact parse-back + MAC-validation tests (exit 0).

Authorized lab:
4. Capture 60s of authorized lab beacons (passive, linktype 105) and run
   `--pcap captures/lab.pcap`; confirm visible/hidden inventory matches the lab channel plan.
5. `green = permitted`: passive, unamplified scanning of devices you own; no frames injected.

## Metrics

- Beacon builder (byte-exact, frame_core): SSID IE (visible + zero-length hidden), interval 100,
  FCS append/verify, seq monotonic
- Scan pipeline: parse-back off the wire -> AP inventory {bssid, ssid, hidden, interval, seq, ts};
  hidden SSIDs reported as `<hidden>` (preserved, not guessed)
- MAC validation: 6-octet colon-form strict check; invalid MACs collected, scan_ok flag
- Channel map: label distribution over 1/5/9/13/17; pcap path reports channels as unknown
- pcap classic (linktype 105) fixture generate + scan; captures/ and reports/ gitignored
- Offline: all beacons synthesized as bytes; no radio, no wall-clock data

- Test suite: `python3 -m unittest discover -s tests`
- Reports: `reports/` (gitignored)

## License

MIT
