"""Dry-run tests for sim/cocotb/Makefile env propagation and guard behavior."""

from __future__ import annotations

import os
import shutil
import subprocess
import unittest
from pathlib import Path


class MakefileDryRunTests(unittest.TestCase):
    """Validate smoke/regress/stress target variable propagation via `make -n`."""

    @classmethod
    def setUpClass(cls):
        cls.makefile_dir = Path(__file__).resolve().parent.parent

    def _run_make(self, *args: str, env: dict | None = None):
        cmd = ["make", "-C", str(self.makefile_dir), *args]
        return subprocess.run(cmd, text=True, capture_output=True, env=env)

    def test_smoke_dry_run_propagates_seed_num_random_and_artifact_tag(self):
        proc = self._run_make("-n", "smoke")
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        out = proc.stdout + proc.stderr
        self.assertIn("DMA_SEED=101", out)
        self.assertIn("DMA_NUM_RANDOM=5", out)
        self.assertIn("DMA_ARTIFACT_TAG=smoke_seed101_n5", out)

    def test_regress_dry_run_propagates_seed_num_random_and_artifact_tag(self):
        proc = self._run_make("-n", "regress")
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        out = proc.stdout + proc.stderr
        self.assertIn("DMA_SEED=12345", out)
        self.assertIn("DMA_NUM_RANDOM=20", out)
        self.assertIn("DMA_ARTIFACT_TAG=regress_seed12345_n20", out)

    def test_stress_dry_run_propagates_seed_num_random_and_artifact_tag(self):
        proc = self._run_make("-n", "stress")
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        out = proc.stdout + proc.stderr
        self.assertIn("DMA_SEED=424242", out)
        self.assertIn("DMA_NUM_RANDOM=100", out)
        self.assertIn("DMA_ARTIFACT_TAG=stress_seed424242_n100", out)

    def test_check_cocotb_fails_with_clear_message_when_unavailable(self):
        proc = self._run_make("check-cocotb")
        out = proc.stdout + proc.stderr
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("cocotb-config not found in PATH", out)

    def test_sim_target_fails_fast_with_same_guard_message_when_unavailable(self):
        # Keep `make` available but hide cocotb-config by restricting PATH
        # to the make binary directory only.
        make_path = shutil.which("make")
        self.assertIsNotNone(make_path)

        env = os.environ.copy()
        env["PATH"] = str(Path(make_path).parent)

        proc = self._run_make("sim", env=env)
        out = proc.stdout + proc.stderr
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("cocotb-config not found in PATH", out)


if __name__ == "__main__":
    unittest.main()
