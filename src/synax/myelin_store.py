#!/usr/bin/env python3
"""
SYNAX MYELIN PERSISTENT OPTIMIZATION STORE (src/synax/myelin_store.py)
=============================================================================
Hardware-fingerprinted, SHA-256 tamper-evident optimization memory indexing
compiled `.sx` kernels by `(ir_hash, hw_fingerprint)`.
=============================================================================
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from synax_security import SynaxSecurityGuard
from synaxc import get_hafiza_root
from .hardware import HardwareFingerprint, detect_hardware_fingerprint, fingerprint_to_dict


class MyelinOptimizationStore:
    """Manages `(ir_hash, hw_fingerprint)` persistent optimization entries."""

    def __init__(self, root: Optional[Path] = None, hw: Optional[HardwareFingerprint] = None):
        self.root = root or get_hafiza_root()
        self.hw = hw or detect_hardware_fingerprint()

    def entry_dir(self, ir_hash: str) -> Path:
        return self.root / ir_hash

    def load_verified_report(self, ir_hash: str, require_matching_hw: bool = True) -> Optional[Dict[str, Any]]:
        rpath = self.entry_dir(ir_hash) / "rapor.json"
        if not rpath.exists():
            return None
        ok_sig, _ = SynaxSecurityGuard.verify_json_file(str(rpath))
        if not ok_sig:
            return None
        try:
            data = json.loads(rpath.read_text(encoding="utf-8"))
        except Exception:
            return None
        if require_matching_hw:
            stored_hw = data.get("hw_fingerprint")
            if stored_hw and stored_hw != self.hw.fingerprint_id:
                return None
        return data

    def list_entries(self) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for rpath in sorted(self.root.glob("*/rapor.json")):
            ok_sig, status = SynaxSecurityGuard.verify_json_file(str(rpath))
            try:
                data = json.loads(rpath.read_text(encoding="utf-8"))
                data["_signature_valid"] = ok_sig
                data["_signature_status"] = status
                results.append(data)
            except Exception:
                continue
        return results

    def hardware_metadata(self) -> Dict[str, Any]:
        return fingerprint_to_dict(self.hw)
