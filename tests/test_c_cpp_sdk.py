#!/usr/bin/env python3
"""
SYNAX C11 & C++17 SDK Integration Test (`tests/test_c_cpp_sdk.py`)
=============================================================================
Compiles and executes both:
  1. A C11 consumer of `include/synax.h` linked against `libsynax_myelin`
  2. A C++17 RAII consumer of `include/synax.hpp` linked against `libsynax_myelin`
Verifies `synax_axon_bind_compiled_kernels`, `synax_axon_transmit`, IEEE-754
anomaly healing count parity, and O(1) myelination state transition!
=============================================================================
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from synaxc import SynaxCompiler


def _ensure_myelin_shared_lib() -> Path:
    ext = "dylib" if sys.platform == "darwin" else "so"
    lib_path = REPO_ROOT / f"libsynax_myelin.{ext}"
    if not lib_path.exists():
        c_src = REPO_ROOT / "synax_myelin_engine.c"
        cmd = ["clang", "-O3", "-shared", "-fPIC", "-std=c11", str(c_src), "-lm", "-o", str(lib_path)]
        if sys.platform != "darwin":
            cmd.append("-ldl")
        subprocess.run(cmd, check=True)
    return lib_path


class TestCCppSDK(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.lib_path = _ensure_myelin_shared_lib()
        cls.include_dir = REPO_ROOT / "include"
        cls.compiler = SynaxCompiler()
        cls.comp = cls.compiler.compile(
            str(REPO_ROOT / "examples" / "hemodynamic_cpp.sx"),
            bench_n=65_536,
            bench_repeats=5,
            verbose=False,
        )

    def test_01_c11_public_header_and_runtime(self) -> None:
        c_prog = r"""
#include "synax.h"
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>

int main(int argc, char** argv) {
    assert(argc == 3);
    SynaxAxonChannel* ch = synax_axon_create("c11_sdk_test", 16, 2);
    assert(ch != NULL);
    assert(synax_axon_get_state(ch) == AXON_STATE_UNMYELINATED);

    int rc = synax_axon_bind_compiled_kernels(ch, argv[1], argv[2], "sdk_winner");
    assert(rc == 0);

    float a[16], b[16], out[16];
    for (int i = 0; i < 16; ++i) {
        a[i] = 90.0f;
        b[i] = 10.0f;
    }
    a[3] = NAN;
    b[7] = INFINITY;

    for (int step = 0; step < 4; ++step) {
        assert(synax_axon_transmit(ch, a, b, out, 16) == 0);
    }

    assert(synax_axon_get_state(ch) == AXON_STATE_MYELINATED);
    assert(strcmp(synax_axon_get_kernel_name(ch), "sdk_winner") == 0);
    assert(fabsf(out[0] - 80.0f) < 1e-4f);
    assert(fabsf(out[3] - (-10.0f)) < 1e-4f); /* heal(0.0): 0.0 - 10.0 = -10.0 */
    assert(fabsf(out[7] - 90.0f) < 1e-4f);    /* heal(0.0) on channel b: 90.0 - 0.0 = 90.0 */

    AxonStats st = synax_axon_get_stats(ch);
    assert(st.total_transmissions == 4);
    assert(st.healed_anomalies_count == 8); /* 2 anomalies * 4 bursts */

    /* Dendritic Reduction API verification (ABI v1) */
    float d_arr[4] = {1.0f, 2.0f, 3.0f, 4.0f};
    assert(fabsf(synax_dendritic_sum(d_arr, 4) - 10.0f) < 1e-5f);
    assert(fabsf(synax_dendritic_mean(d_arr, 4) - 2.5f) < 1e-5f);
    assert(fabsf(synax_dendritic_l2_norm(d_arr, 4) - 5.477225f) < 1e-4f);
    assert(fabsf(synax_dendritic_dot(d_arr, d_arr, 4) - 30.0f) < 1e-5f);

    synax_axon_destroy(ch);
    printf("C11_SDK_OK\n");
    return 0;
}
"""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_p = Path(tmp)
            src_f = tmp_p / "test_c11.c"
            bin_f = tmp_p / "test_c11_bin"
            src_f.write_text(c_prog, encoding="utf-8")

            rpath_flag = f"-Wl,-rpath,{self.lib_path.parent}"
            subprocess.run(
                [
                    "clang", "-std=c11", "-Wall", "-Werror",
                    f"-I{self.include_dir}",
                    str(src_f), str(self.lib_path), rpath_flag,
                    "-lm", "-o", str(bin_f),
                ],
                check=True,
            )
            run_res = subprocess.run(
                [str(bin_f), str(self.comp.baseline_o1_dylib_path), str(self.comp.winner_dylib_path)],
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertIn("C11_SDK_OK", run_res.stdout)

    def test_02_cpp17_raii_header_and_move_semantics(self) -> None:
        cpp_prog = r"""
#include "synax.hpp"
#include <cassert>
#include <cmath>
#include <iostream>
#include <vector>

int main(int argc, char** argv) {
    assert(argc == 3);
    synax::AxonChannel ch1("cpp17_raii", 32, 2);
    ch1.bind_compiled_kernels(argv[1], argv[2], "cpp17_winner");

    /* Verify move semantics */
    synax::AxonChannel ch = std::move(ch1);
    assert(ch1.raw() == nullptr);

    std::vector<float> a(32, 95.0f);
    std::vector<float> b(32, 15.0f);
    a[5] = std::numeric_limits<float>::quiet_NaN();
    b[9] = -std::numeric_limits<float>::infinity();

    std::vector<float> out;
    for (int i = 0; i < 3; ++i) {
        out = ch.transmit(a, b);
    }

    assert(ch.state() == AXON_STATE_MYELINATED);
    assert(ch.kernel_name() == "cpp17_winner");
    assert(std::fabs(out[0] - 80.0f) < 1e-4f);
    assert(std::fabs(out[5] - (-15.0f)) < 1e-4f);
    assert(std::fabs(out[9] - 95.0f) < 1e-4f);

    auto st = ch.stats();
    assert(st.total_transmissions == 3);
    assert(st.healed_anomalies_count == 6);

    /* Shape mismatch must throw std::invalid_argument */
    bool caught = false;
    try {
        std::vector<float> bad_b(10, 1.0f);
        (void)ch.transmit(a, bad_b);
    } catch (const std::invalid_argument&) {
        caught = true;
    }
    assert(caught);

    /* C++17 Dendritic Reduction helper verification */
    float d_data[4] = {2.0f, 4.0f, 6.0f, 8.0f};
    assert(std::fabs(synax::dendritic_sum(d_data, 4) - 20.0f) < 1e-5f);
    assert(std::fabs(synax::dendritic_mean(d_data, 4) - 5.0f) < 1e-5f);
    assert(std::fabs(synax::dendritic_l2_norm(d_data, 4) - std::sqrt(120.0f)) < 1e-4f);
    assert(std::fabs(synax::dendritic_dot(d_data, d_data, 4) - 120.0f) < 1e-4f);

    std::cout << "CPP17_SDK_OK\n";
    return 0;
}
"""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_p = Path(tmp)
            src_f = tmp_p / "test_cpp17.cpp"
            bin_f = tmp_p / "test_cpp17_bin"
            src_f.write_text(cpp_prog, encoding="utf-8")

            rpath_flag = f"-Wl,-rpath,{self.lib_path.parent}"
            subprocess.run(
                [
                    "clang++", "-std=c++17", "-Wall", "-Werror",
                    f"-I{self.include_dir}",
                    str(src_f), str(self.lib_path), rpath_flag,
                    "-o", str(bin_f),
                ],
                check=True,
            )
            run_res = subprocess.run(
                [str(bin_f), str(self.comp.baseline_o1_dylib_path), str(self.comp.winner_dylib_path)],
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertIn("CPP17_SDK_OK", run_res.stdout)


if __name__ == "__main__":
    print("=" * 72)
    print("🛠️  SYNAX C11 & C++17 SDK FFI TEST SUITE")
    print("=" * 72)
    unittest.main(verbosity=2)
