#!/usr/bin/env python3
"""
SYNAX Bit-Exact MIT/PhysioNet WFDB Binary Reader (`src/synax/biomedical/wfdb_reader.py`)
========================================================================================
Zero-mandatory-dependency WFDB reader supporting:
  - `.hea` multi-channel header specifications (Format 212, 16, 61)
  - `.dat` binary sample decoding with:
      * 16-bit signed WFDB checksum verification (`checksum` in `.hea`)
      * Initial-sample (`init_val`) verification
      * Official `WFDB_INVALID_SAMPLE` sentinel (`-2048` in fmt 212, `-32768` in fmt 16)
        mapped to IEEE-754 `NaN` so SYNAX `IMMUNE` (`heal` / `clamp`) handles genuine
        clinical electrode dropouts & ADC saturation without silent corruption.
  - `.atr` MIT binary annotation streams (`SKIP`, `RHYTHM` '+', `VFON` '[', `VFOFF` ']',
    `NOISE` '~', beat annotations, and `AUX` rhythm labels).

Non-Clinical Research Notice:
  Intended solely for retrospective physiological signal-processing research on public
  PhysioNet datasets (e.g., CUDB, VFDB). Not for clinical diagnosis or patient care.
========================================================================================
"""

from __future__ import annotations

import math
import re
import struct
from array import array
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple, Union

try:
    import numpy as _np
except ImportError:  # pragma: no cover
    _np = None  # type: ignore[assignment]


# Standard MIT WFDB annotation type codes (`ecgcodes.h`)
MIT_ANNOTATION_SYMBOLS: Dict[int, str] = {
    0: "NOTQRS",
    1: "N",      # Normal beat
    2: "L",      # Left bundle branch block beat
    3: "R",      # Right bundle branch block beat
    4: "a",      # Aberrated atrial premature beat
    5: "V",      # Premature ventricular contraction
    6: "F",      # Fusion of ventricular and normal beat
    7: "J",      # Nodal (junctional) premature beat
    8: "A",      # Atrial premature beat
    9: "S",      # Supraventricular premature or ectopic beat
    10: "E",     # Ventricular escape beat
    11: "J_ESC", # Nodal escape beat
    12: "/",     # Paced beat
    13: "Q",     # Unclassifiable beat
    14: "~",     # Signal quality change / noise
    16: "|",     # Isolated QRS-like artifact
    18: "s",     # ST segment change
    19: "T",     # T-wave change
    20: "*",     # Systole
    21: "D",     # Diastole
    22: '"',     # Comment annotation
    23: "=",     # Measurement annotation
    24: "p",     # P-wave peak
    25: "B",     # Bundle branch block beat
    26: "^",     # Non-conducted pacer spike
    27: "t",     # T-wave peak
    28: "+",     # Rhythm change (`AUX` carries `(VF`, `(N`, etc.)
    29: "u",     # U-wave peak
    30: "?",     # Learning
    31: "!",     # Ventricular flutter wave (`FLWAV`)
    32: "[",     # Ventricular flutter/fibrillation ONSET (`VFON` — used in CUDB!)
    33: "]",     # Ventricular flutter/fibrillation OFFSET (`VFOFF` — used in CUDB!)
    34: "e",     # Atrial escape beat
    35: "n",     # Supraventricular escape beat
    36: "@",     # Link to external data
    37: "x",     # Non-conducted P-wave
    38: "f",     # Fusion of paced and normal beat
    39: "(",     # Waveform onset (`WFON`)
    40: ")",     # Waveform end (`WFOFF`)
    41: "r",     # R-on-T premature ventricular contraction
}


@dataclass(frozen=True)
class WFDBChannelSpec:
    file_name: str
    fmt: int
    adc_gain: float
    baseline: int
    units: str
    adc_res: int
    adc_zero: int
    init_val: int
    checksum: int
    block_size: int
    description: str


@dataclass(frozen=True)
class WFDBHeader:
    record_name: str
    num_signals: int
    fs: float
    num_samples: int
    channels: Tuple[WFDBChannelSpec, ...]
    comments: Tuple[str, ...] = ()


@dataclass
class WFDBAnnotation:
    sample: int
    code: int
    symbol: str
    subtype: int = 0
    chan: int = 0
    num: int = 0
    aux: str = ""


@dataclass(frozen=True)
class RhythmSegment:
    start_sample: int
    end_sample: int
    raw_label: str
    canonical_class: str  # "VF_VFL" | "VT" | "NSR" | "OTHER_NONSHOCK" | "ASYSTOLE" | "NOISE"


@dataclass
class WFDBRecord:
    header: WFDBHeader
    signals_mv: List[array]           # `array('f')` per channel in mV (`NaN` for invalid ADC sentinels)
    invalid_adc_counts: List[int]     # Number of `WFDB_INVALID_SAMPLE` sentinels per channel
    checksum_verified: List[bool]     # Whether 16-bit signed WFDB checksum matched `.hea`
    init_val_verified: List[bool]     # Whether sample[0] matched `init_val` in `.hea`
    annotations: List[WFDBAnnotation] = field(default_factory=list)
    rhythm_segments: List[RhythmSegment] = field(default_factory=list)


_GAIN_RE = re.compile(
    r"^(?P<gain>[+-]?\d+(?:\.\d+)?)(?:\((?P<base>[+-]?\d+)\))?(?:/(?P<units>\S+))?$"
)


def _parse_gain_token(token: str, default_zero: int) -> Tuple[float, int, str]:
    m = _GAIN_RE.match(token.strip())
    if not m:
        return 200.0, default_zero, "mV"
    gain = float(m.group("gain"))
    if gain == 0.0:
        gain = 200.0
    base = int(m.group("base")) if m.group("base") is not None else None
    units = m.group("units") or "mV"
    return gain, (base if base is not None else default_zero), units


def read_wfdb_header(hea_path: Union[str, Path]) -> WFDBHeader:
    p = Path(hea_path)
    raw_lines = p.read_text(encoding="latin-1").splitlines()
    comments: List[str] = []
    spec_lines: List[str] = []
    for ln in raw_lines:
        s = ln.strip()
        if not s:
            continue
        if s.startswith("#"):
            comments.append(s[1:].strip())
        else:
            spec_lines.append(s)

    if not spec_lines:
        raise ValueError(f"Empty WFDB header: {p}")

    head_parts = spec_lines[0].split()
    rec_name = head_parts[0].split("/")[0]
    num_signals = int(head_parts[1])
    fs_tok = head_parts[2].split("/")[0] if len(head_parts) > 2 else "250"
    fs = float(fs_tok)
    num_samples = int(head_parts[3]) if len(head_parts) > 3 else 0

    channels: List[WFDBChannelSpec] = []
    for idx in range(num_signals):
        parts = spec_lines[1 + idx].split(None, 8)
        file_name = parts[0]
        fmt = int(parts[1].split("+")[0].split("x")[0])
        gain_tok = parts[2] if len(parts) > 2 else "200"
        adc_res = int(parts[3]) if len(parts) > 3 else 12
        adc_zero = int(parts[4]) if len(parts) > 4 else 0
        init_val = int(parts[5]) if len(parts) > 5 else 0
        checksum = int(parts[6]) if len(parts) > 6 else 0
        block_size = int(parts[7]) if len(parts) > 7 else 0
        desc = parts[8].strip() if len(parts) > 8 else f"CH{idx}"
        gain, baseline, units = _parse_gain_token(gain_tok, adc_zero)
        channels.append(
            WFDBChannelSpec(
                file_name=file_name,
                fmt=fmt,
                adc_gain=gain,
                baseline=baseline,
                units=units,
                adc_res=adc_res,
                adc_zero=adc_zero,
                init_val=init_val,
                checksum=checksum,
                block_size=block_size,
                description=desc,
            )
        )

    return WFDBHeader(
        record_name=rec_name,
        num_signals=num_signals,
        fs=fs,
        num_samples=num_samples,
        channels=tuple(channels),
        comments=tuple(comments),
    )


def _to_int16_signed(val: int) -> int:
    u = val & 0xFFFF
    return u - 65536 if u >= 32768 else u


def _decode_dat_signals(
    dat_path: Path, channels: Sequence[WFDBChannelSpec], num_samples: int
) -> Tuple[List[array], List[int], List[bool], List[bool]]:
    n_sig = len(channels)
    fmt = channels[0].fmt
    raw_bytes = dat_path.read_bytes()
    total_vals = num_samples * n_sig

    if fmt == 212:
        if _np is not None:
            n_triplets = (total_vals + 1) // 2
            needed = n_triplets * 3
            buf = _np.frombuffer(raw_bytes[:needed], dtype=_np.uint8).reshape(-1, 3)
            b0 = buf[:, 0].astype(_np.int32)
            b1 = buf[:, 1].astype(_np.int32)
            b2 = buf[:, 2].astype(_np.int32)
            s0 = b0 | ((b1 & 0x0F) << 8)
            s1 = b2 | ((b1 & 0xF0) << 4)
            s0 = _np.where(s0 >= 2048, s0 - 4096, s0)
            s1 = _np.where(s1 >= 2048, s1 - 4096, s1)
            interleaved = _np.empty(n_triplets * 2, dtype=_np.int32)
            interleaved[0::2] = s0
            interleaved[1::2] = s1
            interleaved = interleaved[:total_vals].reshape(num_samples, n_sig)

            signals_mv: List[array] = []
            invalid_counts: List[int] = []
            csum_ok: List[bool] = []
            init_ok: List[bool] = []

            for ch_idx, spec in enumerate(channels):
                col = interleaved[:, ch_idx]
                csum_calc = _to_int16_signed(int(_np.sum(col, dtype=_np.int64)))
                csum_ok.append(csum_calc == spec.checksum)
                init_ok.append(int(col[0]) == spec.init_val if num_samples > 0 else True)

                inv_mask = col == -2048
                inv_cnt = int(_np.count_nonzero(inv_mask))
                invalid_counts.append(inv_cnt)

                phys = (col.astype(_np.float32) - _np.float32(spec.baseline)) / _np.float32(spec.adc_gain)
                if inv_cnt > 0:
                    phys[inv_mask] = _np.float32(_np.nan)
                arr = array("f")
                arr.frombytes(phys.astype("<f4", copy=False).tobytes())
                signals_mv.append(arr)
            return signals_mv, invalid_counts, csum_ok, init_ok

        # Pure-Python fallback for Format 212
        decoded: List[int] = []
        n_triplets = (total_vals + 1) // 2
        mv_view = memoryview(raw_bytes)
        for i in range(n_triplets):
            base_i = i * 3
            b0 = mv_view[base_i]
            b1 = mv_view[base_i + 1]
            b2 = mv_view[base_i + 2]
            u0 = b0 | ((b1 & 0x0F) << 8)
            u1 = b2 | ((b1 & 0xF0) << 4)
            decoded.append(u0 - 4096 if u0 >= 2048 else u0)
            decoded.append(u1 - 4096 if u1 >= 2048 else u1)
        decoded = decoded[:total_vals]
        invalid_sentinel = -2048

    elif fmt in (16, 61):
        endian = "<" if fmt == 16 else ">"
        raw_ints = struct.unpack(f"{endian}{total_vals}h", raw_bytes[: total_vals * 2])
        decoded = list(raw_ints)
        invalid_sentinel = -32768
    else:
        raise ValueError(f"Unsupported WFDB signal format: {fmt}")

    signals_mv = []
    invalid_counts = []
    csum_ok = []
    init_ok = []
    for ch_idx, spec in enumerate(channels):
        ch_raw = decoded[ch_idx::n_sig]
        csum_calc = _to_int16_signed(sum(ch_raw))
        csum_ok.append(csum_calc == spec.checksum)
        init_ok.append(ch_raw[0] == spec.init_val if ch_raw else True)
        arr = array("f")
        inv_cnt = 0
        base = float(spec.baseline)
        gain = float(spec.adc_gain)
        for v in ch_raw:
            if v == invalid_sentinel:
                arr.append(float("nan"))
                inv_cnt += 1
            else:
                arr.append((v - base) / gain)
        signals_mv.append(arr)
        invalid_counts.append(inv_cnt)

    return signals_mv, invalid_counts, csum_ok, init_ok


def read_wfdb_annotations(atr_path: Union[str, Path]) -> List[WFDBAnnotation]:
    """Parse binary MIT/WFDB `.atr` annotation file."""
    p = Path(atr_path)
    if not p.exists():
        return []
    data = p.read_bytes()
    n_bytes = len(data)
    pos = 0
    curr_sample = 0
    pending_skip = 0
    anns: List[WFDBAnnotation] = []

    while pos + 2 <= n_bytes:
        word = data[pos] | (data[pos + 1] << 8)
        pos += 2
        code = (word >> 10) & 0x3F
        val = word & 0x03FF

        if code == 0 and val == 0:
            break  # EOF
        elif code == 59:  # SKIP
            if val == 0:
                if pos + 4 > n_bytes:
                    break
                # PDP-11 word order: high 16-bit word first, low 16-bit word second
                hi = data[pos] | (data[pos + 1] << 8)
                lo = data[pos + 2] | (data[pos + 3] << 8)
                pos += 4
                raw32 = (hi << 16) | lo
                if raw32 >= 0x80000000:
                    raw32 -= 0x100000000
                pending_skip += raw32
            else:
                pending_skip += val
        elif code == 60:  # NUM
            if anns:
                anns[-1].num = val
        elif code == 61:  # SUB
            if anns:
                anns[-1].subtype = val
        elif code == 62:  # CHN
            if anns:
                anns[-1].chan = val
        elif code == 63:  # AUX
            byte_len = val
            padded = (byte_len + 1) & ~1
            aux_bytes = data[pos : pos + byte_len]
            pos += padded
            aux_str = aux_bytes.rstrip(b"\x00").decode("latin-1", errors="replace").strip()
            if anns:
                anns[-1].aux = aux_str
        else:
            curr_sample += pending_skip + val
            pending_skip = 0
            sym = MIT_ANNOTATION_SYMBOLS.get(code, f"CODE_{code}")
            anns.append(WFDBAnnotation(sample=curr_sample, code=code, symbol=sym))

    return anns


def canonicalize_rhythm_label(raw_label: str) -> str:
    """
    Map MIT-BIH / CUDB rhythm auxiliary strings and bracket markers into
    canonical AHA AED rhythm categories:
      - "VF_VFL"         : Ventricular fibrillation or ventricular flutter (`(VF`, `(VFIB`, `(VFL`, `[`)
      - "VT"             : Ventricular tachycardia (`(VT`)
      - "NSR"            : Normal sinus rhythm (`(N`, `(NSR`)
      - "ASYSTOLE"       : Asystole (`(ASYS`)
      - "NOISE"          : Annotated unreadable noise (`(NOISE`, `~`)
      - "OTHER_NONSHOCK" : Other organized non-shockable rhythms (`(AFIB`, `(SVTA`, `(SBR`, `(B`, `(T`, `(NOD`, `(PM`, `(PREX`, etc.)
    """
    tok = raw_label.strip().lstrip("(").upper()
    if tok in ("VF", "VFIB", "VFL", "VFON_BRACKET"):
        return "VF_VFL"
    if tok in ("VT",):
        return "VT"
    if tok in ("N", "NSR", "SINUS"):
        return "NSR"
    if tok in ("ASYS", "ASYSTOLE"):
        return "ASYSTOLE"
    if "NOISE" in tok or tok == "~":
        return "NOISE"
    return "OTHER_NONSHOCK"


def extract_rhythm_segments(
    annotations: Sequence[WFDBAnnotation], num_samples: int
) -> List[RhythmSegment]:
    """
    Reconstruct contiguous cardiologist rhythm intervals `[start_sample, end_sample)` across a record.
    Handles:
      1. `RHYTHM` (`code == 28`, `+`) with `AUX` strings `(N`, `(VFIB`, `(VT`, `(VFL`, `(ASYS`, `(NOISE`, etc. (VFDB & CUDB)
      2. `VFON` (`code == 32`, `[`) and `VFOFF` (`code == 33`, `]`) bracket markers (CUDB sustained VF onset/offset!)
      3. Unreadable signal quality intervals (`code == 14`, `~`, `subtype == 1023` i.e. `-1` unreadable until recovery)
    """
    events: List[Tuple[int, str]] = []
    active_rhythm_before_bracket = "(N"
    active_rhythm_before_noise = "(N"
    in_unreadable_noise = False

    for ann in annotations:
        if ann.code == 14:  # '~' signal quality change
            if ann.subtype == 1023:  # -1 in 10-bit signed = unreadable / disconnected / shock artifact
                if not in_unreadable_noise:
                    in_unreadable_noise = True
                    events.append((max(0, ann.sample), "(NOISE"))
            else:
                if in_unreadable_noise:
                    in_unreadable_noise = False
                    restore_lbl = ann.aux if ann.aux else active_rhythm_before_noise
                    events.append((max(0, ann.sample), restore_lbl))
        elif ann.code == 28 and ann.aux:  # '+' rhythm change
            active_rhythm_before_bracket = ann.aux
            active_rhythm_before_noise = ann.aux
            if not in_unreadable_noise:
                events.append((max(0, ann.sample), ann.aux))
        elif ann.code == 32:  # '[' VFON (onset of ventricular flutter/fibrillation)
            lbl = ann.aux if ann.aux else "(VF"
            active_rhythm_before_noise = lbl
            in_unreadable_noise = False
            events.append((max(0, ann.sample), lbl))
        elif ann.code == 33:  # ']' VFOFF (offset of ventricular flutter/fibrillation)
            lbl = ann.aux if ann.aux else active_rhythm_before_bracket
            active_rhythm_before_noise = lbl
            if not in_unreadable_noise:
                events.append((max(0, ann.sample), lbl))

    if not events:
        # CUDB records without an explicit leading `(N` before `[` start in non-VF baseline rhythm
        return [
            RhythmSegment(
                start_sample=0,
                end_sample=num_samples,
                raw_label="(N",
                canonical_class="NSR",
            )
        ]

    # Sort stably by sample; if first event starts > 0, prepend baseline rhythm `(N`
    events.sort(key=lambda x: x[0])
    if events[0][0] > 0:
        # In CUDB, recordings begin in non-fibrillatory rhythm prior to `[` (`VFON`)
        events.insert(0, (0, "(N"))

    segments: List[RhythmSegment] = []
    for idx, (s_start, raw_lbl) in enumerate(events):
        s_end = events[idx + 1][0] if (idx + 1) < len(events) else num_samples
        s_start_clamped = min(max(0, s_start), num_samples)
        s_end_clamped = min(max(0, s_end), num_samples)
        if s_end_clamped <= s_start_clamped:
            continue
        cls = canonicalize_rhythm_label(raw_lbl)
        if segments and segments[-1].canonical_class == cls and segments[-1].raw_label == raw_lbl:
            prev = segments[-1]
            segments[-1] = RhythmSegment(
                start_sample=prev.start_sample,
                end_sample=s_end_clamped,
                raw_label=prev.raw_label,
                canonical_class=prev.canonical_class,
            )
        else:
            segments.append(
                RhythmSegment(
                    start_sample=s_start_clamped,
                    end_sample=s_end_clamped,
                    raw_label=raw_lbl,
                    canonical_class=cls,
                )
            )
    return segments


def read_wfdb_record(record_prefix: Union[str, Path]) -> WFDBRecord:
    """Read `.hea`, `.dat`, and `.atr` for a WFDB record and verify 16-bit sample checksums."""
    prefix = Path(record_prefix)
    if prefix.suffix in (".hea", ".dat", ".atr"):
        prefix = prefix.with_suffix("")
    hea_path = prefix.with_suffix(".hea")
    header = read_wfdb_header(hea_path)

    # Group channels by `.dat` file (all CUDB/VFDB channels share `<rec>.dat`)
    dat_path = prefix.parent / header.channels[0].file_name
    signals_mv, invalid_counts, csum_ok, init_ok = _decode_dat_signals(
        dat_path, header.channels, header.num_samples
    )
    anns = read_wfdb_annotations(prefix.with_suffix(".atr"))
    segments = extract_rhythm_segments(anns, header.num_samples)

    return WFDBRecord(
        header=header,
        signals_mv=signals_mv,
        invalid_adc_counts=invalid_counts,
        checksum_verified=csum_ok,
        init_val_verified=init_ok,
        annotations=anns,
        rhythm_segments=segments,
    )
