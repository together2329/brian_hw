"""Reproducibility checks for fixed-seed random generation behavior."""

from __future__ import annotations

import random
import sys
import unittest
from pathlib import Path

_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

import config


class ReproducibilityChecks(unittest.TestCase):
    """Validate deterministic random streams and derived trial fingerprints."""

    @staticmethod
    def _trial_fingerprint(seed: int, num_trials: int) -> list[tuple[int, int, int, int]]:
        """Generate a compact deterministic fingerprint of random trial parameters.

        Mirrors the random sources used by constrained-random cocotb tests at a
        lightweight level: length, src index, dst index, and pattern selector.
        """
        rng = random.Random(seed)
        max_words = min(32, config.DEPTH - 1)

        fp: list[tuple[int, int, int, int]] = []
        for _ in range(num_trials):
            src_word = rng.randint(0, config.DEPTH - max_words - 1)
            dst_word = rng.randint(0, config.DEPTH - max_words - 1)
            length = rng.randint(1, max_words)
            mode = rng.randint(0, 3)
            fp.append((src_word, dst_word, length, mode))
        return fp

    def test_fixed_seed_produces_identical_fingerprint(self):
        a = self._trial_fingerprint(seed=12345, num_trials=20)
        b = self._trial_fingerprint(seed=12345, num_trials=20)
        self.assertEqual(a, b)

    def test_different_seed_changes_fingerprint(self):
        a = self._trial_fingerprint(seed=12345, num_trials=20)
        b = self._trial_fingerprint(seed=54321, num_trials=20)
        self.assertNotEqual(a, b)

    def test_config_seed_and_num_random_are_stable_inputs(self):
        a = self._trial_fingerprint(seed=config.SEED, num_trials=config.NUM_RANDOM)
        b = self._trial_fingerprint(seed=config.SEED, num_trials=config.NUM_RANDOM)
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
