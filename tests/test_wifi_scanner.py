#!/usr/bin/env python3
"""Byte-exact unit tests for w1-wifi-scanner."""

import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from firmware import wifi_scanner as ws
from firmware import frame_core as fc


class MacValidationTest(unittest.TestCase):
    def test_valid(self):
        self.assertTrue(ws.mac_valid("00:11:22:33:44:55"))
        self.assertTrue(ws.validate_mac_stream("00:11:22:aa:bb:cc"))

    def test_invalid(self):
        for bad in ("nope", "00:11:22:33:44", "00:11:22:33:44:55:66",
                    "00:11:22:33:44:zz", "00:11:22:33:44:5"):
            self.assertFalse(ws.mac_valid(bad))


class RosterTest(unittest.TestCase):
    def test_roster_lab_oui(self):
        aps = ws.build_ap_roster()
        self.assertEqual(len(aps), 10)
        for ap in aps:
            self.assertTrue(ap["bssid"].startswith("00:11:22"))
            self.assertIn(ap["channel"], (1, 5, 9, 13, 17))

    def test_hidden_ap_present(self):
        aps = ws.build_ap_roster()
        self.assertTrue(any(ap["hidden"] for ap in aps))


class ScanTest(unittest.TestCase):
    def test_scan_bytes_roundtrip(self):
        frames = ws.build_ap_beacons(ws.build_ap_roster())
        scan = ws.scan_bytes(frames)
        self.assertEqual(scan["aps_seen"], 10)
        self.assertTrue(scan["scan_ok"])
        self.assertEqual(scan["hidden"], 4)   # i%3==0 -> 0,3,6,9

    def test_hidden_ssid_empty(self):
        frames = ws.build_ap_beacons(ws.build_ap_roster())
        scan = ws.scan_bytes([f for f in frames if f["hidden"]])
        self.assertGreaterEqual(scan["hidden"], 1)
        self.assertEqual(scan["visible"], 0)


class FixtureTest(unittest.TestCase):
    def test_fixture_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "scan.pcap")
            n = ws.write_scan_fixture(path)
            self.assertEqual(n, 10)
            scan = ws.scan_pcap(path)
            self.assertEqual(scan["aps_seen"], 10)


class CLITest(unittest.TestCase):
    def test_demo_exit_zero(self):
        self.assertEqual(ws.run_demo(), 0)

    def test_json_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "o.json")
            rc = ws.main(["--json", out])
            self.assertEqual(rc, 0)
            data = json.load(open(out))
            self.assertFalse(data["radio_emitted"])
            self.assertEqual(data["aps_seen"], 10)


if __name__ == "__main__":
    unittest.main()