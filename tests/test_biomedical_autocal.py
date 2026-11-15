#!/usr/bin/env python3
"""
Unit & Firmware Integration Tests for SYNAX Biomedical Zero-Drift Calibrator
(`tests/test_biomedical_autocal.py`)
"""

from __future__ import annotations

import math
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from synax.biomedical_autocal import (
    AutonomicZeroDriftCalibrator,
    format_autocal_telegram_report,
    generate_device_firmware_header,
    run_autocal_convergence_simulation,
    synax_zero_drift_calibrated,
)
from synax.telegram_bot import SynaxTelegramBot


class TestBiomedicalAutocal(unittest.TestCase):
    def test_01_contractive_lyapunov_convergence_all_profiles(self) -> None:
        for prof in ("ecg", "ibp", "ventilator", "spo2"):
            rep = run_autocal_convergence_simulation(profile_key=prof, epochs=16)
            self.assertTrue(rep.lyapunov_monotone_verified, f"Lyapunov not monotone for {prof}")
            self.assertGreater(rep.final_uncalibrated_drift, rep.initial_uncalibrated_drift)
            self.assertLess(rep.final_calibrated_error, rep.initial_calibrated_error * 0.01)
            self.assertGreater(rep.convergence_suppression_pct, 99.9)
            self.assertGreaterEqual(rep.total_nan_inf_healed, 4)

    def test_02_decorator_bestows_autocal_on_host_software(self) -> None:
        drift_step = {"k": 0}

        @synax_zero_drift_calibrated(standard_reference=0.0, contraction_gamma=0.65)
        def acquire_drifting_sensor() -> list[float]:
            drift_step["k"] += 1
            bias = 3.5 * drift_step["k"]
            return [bias, bias + 0.01, bias - 0.01, float("nan"), bias]

        out1 = acquire_drifting_sensor()
        out2 = acquire_drifting_sensor()
        out3 = acquire_drifting_sensor()
        self.assertTrue(all(math.isfinite(x) for x in out1 + out2 + out3))
        # Calibrated mean should stay locked near 0.0 despite bias growing to +10.5
        mean3 = sum(out3) / len(out3)
        self.assertLess(abs(mean3), 1.5)

    def test_03_c99_and_q16_firmware_header_generation_and_compile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            hdr = generate_device_firmware_header("ecg", tmp_dir / "synax_autocal_firmware.h")
            self.assertTrue(hdr.exists())
            content = hdr.read_text(encoding="utf-8")
            self.assertIn("synax_autocal_q16_reset_step", content)
            self.assertIn("synax_autocal_f32_reset_step", content)

            cc = shutil.which("cc") or shutil.which("gcc") or shutil.which("clang")
            if cc and sys.platform != "win32":
                test_c = tmp_dir / "test_fw.c"
                bin_out = tmp_dir / "test_fw_bin"
                test_c.write_text(
                    '#include <stdio.h>\n'
                    '#include <assert.h>\n'
                    '#include "synax_autocal_firmware.h"\n'
                    'int main(void) {\n'
                    '    synax_autocal_f32_t st;\n'
                    '    synax_autocal_f32_init(&st, 0.0f);\n'
                    '    float e1 = synax_autocal_f32_reset_step(&st, 10.0f);\n'
                    '    float e2 = synax_autocal_f32_reset_step(&st, 10.0f);\n'
                    '    float e3 = synax_autocal_f32_reset_step(&st, 10.0f);\n'
                    '    assert(fabsf(e3) < fabsf(e2) && fabsf(e2) < fabsf(e1));\n'
                    '    synax_autocal_q16_t qst;\n'
                    '    synax_autocal_q16_init(&qst);\n'
                    '    int32_t qe1 = synax_autocal_q16_reset_step(&qst, 655360);\n'
                    '    int32_t qe2 = synax_autocal_q16_reset_step(&qst, 655360);\n'
                    '    assert(qe2 < qe1);\n'
                    '    printf("FW_OK e1=%.4f e3=%.6f\\n", e1, e3);\n'
                    '    return 0;\n'
                    '}\n',
                    encoding="utf-8",
                )
                proc = subprocess.run([cc, "-O2", str(test_c), "-lm", "-o", str(bin_out)], capture_output=True, text=True)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                run_p = subprocess.run([str(bin_out)], capture_output=True, text=True)
                self.assertEqual(run_p.returncode, 0)
                self.assertIn("FW_OK", run_p.stdout)

    def test_04_telegram_bot_calibrate_command(self) -> None:
        bot = SynaxTelegramBot()
        reply = bot.handle_command_text("/calibrate ibp")
        self.assertIn("SYNAX Otonom Biyomedikal Sıfır-Sapma", reply)
        self.assertIn("IEC 60601-2-34", reply)
        self.assertIn("Lyapunov Monoton Kararlılık: True", reply)


if __name__ == "__main__":
    unittest.main()
