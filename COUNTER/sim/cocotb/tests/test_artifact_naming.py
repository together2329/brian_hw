"""Unit tests for deterministic artifact naming helper in test_dma.py."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

# Ensure local cocotb test modules (config.py, test_dma.py) are importable.
_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

import test_dma


class ArtifactNamingTests(unittest.TestCase):
    """Validate DMA_ARTIFACT_TAG override and seed/NUM_RANDOM fallback behavior."""

    def setUp(self):
        self._saved_tag = os.environ.get("DMA_ARTIFACT_TAG")
        self._saved_seed = test_dma.config.SEED
        self._saved_num_random = test_dma.config.NUM_RANDOM

    def tearDown(self):
        if self._saved_tag is None:
            os.environ.pop("DMA_ARTIFACT_TAG", None)
        else:
            os.environ["DMA_ARTIFACT_TAG"] = self._saved_tag

        test_dma.config.SEED = self._saved_seed
        test_dma.config.NUM_RANDOM = self._saved_num_random

    def test_artifact_name_uses_explicit_dma_artifact_tag(self):
        os.environ["DMA_ARTIFACT_TAG"] = "regress_seed12345_n20"
        test_dma.config.SEED = 1
        test_dma.config.NUM_RANDOM = 2

        name = test_dma._artifact_name("dma_coverage")
        self.assertEqual(name, "dma_coverage_regress_seed12345_n20.json")

    def test_artifact_name_falls_back_to_seed_num_random_when_tag_missing(self):
        os.environ.pop("DMA_ARTIFACT_TAG", None)
        test_dma.config.SEED = 424242
        test_dma.config.NUM_RANDOM = 100

        name = test_dma._artifact_name("dma_stress_coverage")
        self.assertEqual(name, "dma_stress_coverage_seed424242_n100.json")


if __name__ == "__main__":
    unittest.main()
