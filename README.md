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
- Attacking infrastructure without authorization
- Any activity that violates applicable laws or regulations
- Commercial use without proper licensing

### No Warranty
This software is provided "AS IS" without warranty of any kind. The author is not responsible for any misuse or damage caused by this software.

### Responsible Disclosure
If you discover vulnerabilities using this tool, follow responsible disclosure practices:
1. Report to the vendor/owner privately
2. Allow reasonable time for remediation
3. Do not exploit beyond proof of concept

## License

MIT
