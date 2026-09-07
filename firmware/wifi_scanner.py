#!/usr/bin/env python3
"""W1 — Wi-Fi Scanner (offscreen beacon scanner + AP inventory).

Simulates an RF channel walk over synthetic beacon bytes: builds distinct
lab APs (visible + hidden SSIDs) as byte-exact beacons, "scans" them by
parsing back off the wire, validates MAC formats + channel allocation, and
emits an AP inventory to JSON. Passive byte-level only — no radio.

Hidden-SSID note: hidden APs transmit beacons with a zero-length SSID IE and
announce "hidden" via the null/probe-request mechanism; this scanner preserves
that signal instead of guessing.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter

try:
    from firmware import frame_core as fc
except ImportError:
    try:
        import frame_core as fc
    except ImportError:
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "firmware"))
        import frame_core as fc

START_TS = 1700000000.0


def mac_valid(mac: str) -> bool:
    if len(mac) != 17:
        return False
    try:
        parts = mac.split(":")
        return len(parts) == 6 and all(len(p) == 2 for p in parts) \
            and all(0 <= int(p, 16) <= 255 for p in parts)
    except ValueError:
        return False


def validate_mac_stream(mac: str) -> bool:
    return mac_valid(mac)


# ----------------------------------------------------------------------
# Synthetic lab AP population + beacon bytes
# ----------------------------------------------------------------------

def build_ap_roster() -> list[dict]:
    aps = []
    for i in range(10):
        mac = f"00:11:22:{i:02x}:{i * 3 & 0xFF:02x}:{i * 7 & 0xFF:02x}"
        hidden = i % 3 == 0          # every 3rd AP hidden
        ssid = "" if hidden else f"lab-scanner-{i}"
        aps.append({"bssid": mac, "channel": 1 + (i % 5) * 4,
                    "hidden": hidden, "ssid": ssid})
    return aps


def build_ap_beacons(aps: list[dict]) -> list[dict]:
    frames = []
    seq = 0
    for i, ap in enumerate(aps):
        seq = (seq + 1) & 0xFFFF
        b = fc.build_beacon(ap["bssid"], ssid=ap["ssid"], timestamp=3000 + i,
                            beacon_interval=100, seq_num=seq)
        frames.append({"ts": START_TS + 0.05 * i, "bssid": ap["bssid"],
                       "channel": ap["channel"], "hidden": ap["hidden"],
                       "ssid": ap["ssid"], "data": b + fc.fcs(b)})
    return frames


def write_scan_fixture(path: str) -> int:
    frames = build_ap_beacons(build_ap_roster())
    fc.write_pcap(path, [f["data"] for f in frames], ts=frames[0]["ts"])
    return len(frames)


# ----------------------------------------------------------------------
# Scan pipeline (parse the beacon bytes back off the wire)
# ----------------------------------------------------------------------

HIDDEN_SSID_SENTINEL = "<hidden>"


def _hidden(ssid: str) -> bool:
    return ssid in ("", HIDDEN_SSID_SENTINEL)


def scan_pcap(path: str) -> dict:
    aps = []
    for rec in fc.read_pcap(path):
        data = rec["data"]
        if not fc.verify_fcs(data):
            continue
        payload = data[:-4]
        try:
            fields, _ = fc.parse_mgmt_header(payload)
            if fields["subtype_val"] != fc.FC_SUBTYPE_BEACON:
                continue
            p, _ = fc.parse_beacon(payload)
        except ValueError:
            continue
        aps.append({"bssid": fields["bssid"], "channel": None,
                    "ssid": p["ssid"], "hidden": _hidden(p["ssid"]),
                    "beacon_interval": p["beacon_interval"],
                    "seq": fields["seq_num"], "ts": rec["ts"]})
    return summarize(aps)


def scan_bytes(frames: list[dict]) -> dict:
    aps = []
    for f in frames:
        payload = f["data"][:-4]
        fields, _ = fc.parse_mgmt_header(payload)
        p, _ = fc.parse_beacon(payload)
        aps.append({"bssid": fields["bssid"], "channel": f["channel"],
                    "ssid": p["ssid"], "hidden": _hidden(p["ssid"]),
                    "beacon_interval": p["beacon_interval"],
                    "seq": fields["seq_num"], "ts": f["ts"]})
    return summarize(aps)


def summarize(aps: list[dict]) -> dict:
    visible = [a for a in aps if not a["hidden"]]
    hidden = [a for a in aps if a["hidden"]]
    bad_macs = [a["bssid"] for a in aps if not mac_valid(a["bssid"])]
    known = [a for a in aps if a.get("channel") is not None]
    channels = Counter(a["channel"] for a in known)
    return {
        "aps_seen": len(aps),
        "visible": len(visible),
        "hidden": len(hidden),
        "channels_known": len(known),
        "channels_unknown": len(aps) - len(known),
        "channel_map": dict(sorted(channels.items())),
        "invalid_macs": bad_macs,
        "scan_ok": not bad_macs,
    }


# ----------------------------------------------------------------------
# CLI / demo
# ----------------------------------------------------------------------

def build_args_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="w1-wifi-scanner",
        description="Offscreen 'RF' scan: byte-exact synthetic lab beacons, parse-back AP "
                    "inventory with hidden-SSID detection and MAC validation. "
                    "Pure-stdlib bytes; passive; no radio.")
    p.add_argument("--pcap", metavar="PATH", help="scan a pcap fixture")
    p.add_argument("--gen-fixture", metavar="PATH", help="write synthetic scan fixture")
    p.add_argument("--json", metavar="PATH", help="write JSON report")
    return p


def print_scan(scan: dict) -> None:
    print("=" * 62)
    print(" W1 — Wi-Fi Scanner (offscreen beacon scan)")
    print("=" * 62)
    print(f"\n[+] APs seen: {scan['aps_seen']}  visible: {scan['visible']}  "
          f"hidden: {scan['hidden']}  radio_emitted=False")
    print(f"[+] channel map: {scan['channel_map']}")
    print(f"[+] invalid MACs: {scan['invalid_macs'] or 'none'}  "
          f"scan_ok={scan['scan_ok']}")
    print("=" * 62)


def main(argv=None) -> int:
    args = build_args_parser().parse_args(argv)
    if args.pcap:
        scan = scan_pcap(args.pcap)
    else:
        aps = build_ap_roster()
        frames = build_ap_beacons(aps)
        scan = scan_bytes(frames)
        print(f"[+] synthesized {len(aps)} lab APs as bytes")
    print_scan(scan)
    if args.gen_fixture:
        d = os.path.dirname(args.gen_fixture)
        if d:
            os.makedirs(d, exist_ok=True)
        n = write_scan_fixture(args.gen_fixture)
        print(f"\n[+] fixture -> {args.gen_fixture} ({n} beacons)")
    if args.json:
        d = os.path.dirname(args.json)
        if d:
            os.makedirs(d, exist_ok=True)
        with open(args.json, "w") as f:
            json.dump({"name": "w1-wifi-scanner", "radio_emitted": False, **scan},
                      f, indent=2, default=str)
    return 0


def run_demo() -> int:
    return main([])


if __name__ == "__main__":
    raise SystemExit(main())