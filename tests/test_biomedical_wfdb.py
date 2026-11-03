#!/usr/bin/env python3
"""
SYNAX Biomedical WFDB Reader Unit Tests (`tests/test_biomedical_wfdb.py`)
Synthetic, download-free round-trip tests for Format 212 decoding, checksum verification,
invalid-sample (-2048 -> NaN) mapping, MIT annotation parsing, and rhythm reconstruction.
"""

import math
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from synax.biomedical.wfdb_reader import (  # noqa: E402
    extract_rhythm_segments,
    read_wfdb_annotations,
    read_wfdb_record,
)


def _pack212(samples):
    out = bytearray()
    if len(samples) % 2:
        samples = list(samples) + [0]
    for i in range(0, len(samples), 2):
        a, b = samples[i] & 0xFFF, samples[i + 1] & 0xFFF
        out += bytes([a & 0xFF, ((a >> 8) & 0x0F) | (((b >> 8) & 0x0F) << 4), b & 0xFF])
    return bytes(out)


def _ann_word(code, val):
    w = ((code & 0x3F) << 10) | (val & 0x3FF)
    return bytes([w & 0xFF, (w >> 8) & 0xFF])


def _aux(text):
    raw = text.encode("latin-1")
    pad = raw + (b"\x00" if len(raw) % 2 else b"")
    return _ann_word(63, len(raw)) + pad


def _signed16(v):
    v &= 0xFFFF
    return v - 65536 if v >= 32768 else v


def test_roundtrip():
    ch0 = [100, -200, 2047, -2047, -2048, 0, 5, -5]
    ch1 = [1, 2, 3, 4, 5, 6, 7, 8]
    inter = [v for pair in zip(ch0, ch1) for v in pair]
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        (d / "t1.dat").write_bytes(_pack212(inter))
        (d / "t1.hea").write_text(
            "t1 2 250 8\n"
            f"t1.dat 212 200 12 0 {ch0[0]} {_signed16(sum(ch0))} 0 ECG\n"
            f"t1.dat 212 200 12 0 {ch1[0]} {_signed16(sum(ch1))} 0 ECG\n"
        )
        # '+' (N at 0, '+' (VFL at 3, '~' unreadable at 5, '~' recovered at 6, EOF
        atr = (_ann_word(28, 0) + _aux("(N") + _ann_word(28, 3) + _aux("(VFL")
               + _ann_word(14, 2) + _ann_word(61, 1023) + _ann_word(14, 1) + _ann_word(0, 0))
        (d / "t1.atr").write_bytes(atr)

        rec = read_wfdb_record(d / "t1")
        assert rec.checksum_verified == [True, True], rec.checksum_verified
        assert rec.init_val_verified == [True, True]
        assert rec.invalid_adc_counts == [1, 0]
        assert math.isnan(rec.signals_mv[0][4])
        assert abs(rec.signals_mv[0][0] - 0.5) < 1e-6
        assert abs(rec.signals_mv[0][2] - 2047 / 200.0) < 1e-6

        anns = read_wfdb_annotations(d / "t1.atr")
        assert [a.sample for a in anns] == [0, 3, 5, 6]
        assert anns[1].aux == "(VFL" and anns[2].subtype == 1023

        segs = [(s.start_sample, s.end_sample, s.canonical_class) for s in rec.rhythm_segments]
        assert segs == [(0, 3, "NSR"), (3, 5, "VF_VFL"), (5, 6, "NOISE"), (6, 8, "VF_VFL")], segs
    print("  ✓ Format 212 decode + checksum + init + invalid-sample NaN mapping")
    print("  ✓ MIT annotation AUX/SUB parsing and rhythm/noise interval reconstruction")


def test_cudb_bracket_markers():
    from synax.biomedical.wfdb_reader import WFDBAnnotation
    anns = [WFDBAnnotation(sample=100, code=32, symbol="["), WFDBAnnotation(sample=300, code=33, symbol="]")]
    segs = [(s.start_sample, s.end_sample, s.canonical_class) for s in extract_rhythm_segments(anns, 400)]
    assert segs == [(0, 100, "NSR"), (100, 300, "VF_VFL"), (300, 400, "NSR")], segs
    print("  ✓ CUDB VFON '[' / VFOFF ']' bracket interval reconstruction")


if __name__ == "__main__":
    print("🫀 SYNAX Biomedical WFDB Reader Tests")
    test_roundtrip()
    test_cudb_bracket_markers()
    print("✅ Biomedical WFDB tests passed.")
