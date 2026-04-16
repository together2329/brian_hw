"""Unit tests for config.py environment override parsing and validation."""

from __future__ import annotations

import importlib.util
import os
import unittest
from pathlib import Path
from typing import Dict, Optional

_CONFIG_PATH = Path(__file__).with_name("config.py")
_DMA_ENV_KEYS = [
    "DMA_DATA_WIDTH",
    "DMA_ADDR_WIDTH",
    "DMA_LEN_WIDTH",
    "DMA_DEPTH",
    "DMA_NUM_RANDOM",
    "DMA_SEED",
    "DMA_CLK_PERIOD_NS",
    "DMA_RESET_CYCLES",
]


class ConfigEnvOverrideTests(unittest.TestCase):
    """Covers decimal/hex env parsing and explicit validation failures."""

    def _load_config(self, overrides: Dict[str, Optional[str]]):
        """Load config.py with temporary environment variable overrides."""
        backup = {k: os.environ.get(k) for k in _DMA_ENV_KEYS}
        try:
            for key in _DMA_ENV_KEYS:
                os.environ.pop(key, None)

            for key, value in overrides.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

            spec = importlib.util.spec_from_file_location("config_for_test", _CONFIG_PATH)
            self.assertIsNotNone(spec)
            self.assertIsNotNone(spec.loader)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        finally:
            for key in _DMA_ENV_KEYS:
                os.environ.pop(key, None)
            for key, value in backup.items():
                if value is not None:
                    os.environ[key] = value

    def test_valid_decimal_overrides(self):
        cfg = self._load_config(
            {
                "DMA_DATA_WIDTH": "512",
                "DMA_ADDR_WIDTH": "32",
                "DMA_LEN_WIDTH": "16",
                "DMA_DEPTH": "1024",
                "DMA_NUM_RANDOM": "20",
                "DMA_SEED": "12345",
                "DMA_CLK_PERIOD_NS": "10",
                "DMA_RESET_CYCLES": "5",
            }
        )

        self.assertEqual(cfg.DATA_WIDTH, 512)
        self.assertEqual(cfg.ADDR_WIDTH, 32)
        self.assertEqual(cfg.DEPTH, 1024)
        self.assertEqual(cfg.NUM_RANDOM, 20)
        self.assertEqual(cfg.SEED, 12345)
        self.assertEqual(cfg.WORD_BYTES, 64)
        self.assertEqual(cfg.LANES_PER_WORD, 16)
        self.assertEqual(cfg.ADDR_LSB, 6)

    def test_valid_hex_overrides(self):
        cfg = self._load_config(
            {
                "DMA_DATA_WIDTH": "0x200",
                "DMA_ADDR_WIDTH": "0x20",
                "DMA_LEN_WIDTH": "0x10",
                "DMA_DEPTH": "0x400",
                "DMA_NUM_RANDOM": "0x14",
                "DMA_SEED": "0x3039",
                "DMA_CLK_PERIOD_NS": "0xA",
                "DMA_RESET_CYCLES": "0x5",
            }
        )

        self.assertEqual(cfg.DATA_WIDTH, 512)
        self.assertEqual(cfg.ADDR_WIDTH, 32)
        self.assertEqual(cfg.LEN_WIDTH, 16)
        self.assertEqual(cfg.DEPTH, 1024)
        self.assertEqual(cfg.NUM_RANDOM, 20)
        self.assertEqual(cfg.SEED, 12345)

    def test_invalid_non_integer_override_has_clear_error(self):
        with self.assertRaisesRegex(
            ValueError,
            "^DMA_DATA_WIDTH must be an integer, got 'abc'$",
        ):
            self._load_config({"DMA_DATA_WIDTH": "abc"})

    def test_invalid_byte_alignment_error(self):
        with self.assertRaisesRegex(
            ValueError,
            "^DMA_DATA_WIDTH must be byte-aligned \(multiple of 8\), got 500$",
        ):
            self._load_config({"DMA_DATA_WIDTH": "500"})

    def test_invalid_lane_alignment_error(self):
        with self.assertRaisesRegex(
            ValueError,
            "^DMA_DATA_WIDTH must be lane-aligned \(multiple of 32\), got 24$",
        ):
            self._load_config({"DMA_DATA_WIDTH": "24"})

    def test_invalid_power_of_two_word_bytes_error(self):
        with self.assertRaisesRegex(
            ValueError,
            "^Derived WORD_BYTES must be a power of two for alignment math, got 12$",
        ):
            self._load_config({"DMA_DATA_WIDTH": "96"})

    def test_invalid_addr_width_too_small_error(self):
        with self.assertRaisesRegex(
            ValueError,
            "^DMA_ADDR_WIDTH too small for configured memory: need 16 bits for 65536 bytes, got 8$",
        ):
            self._load_config({"DMA_ADDR_WIDTH": "8"})

    def test_missing_env_uses_defaults_and_derived_values_are_sane(self):
        cfg = self._load_config({})

        # Defaults
        self.assertEqual(cfg.DATA_WIDTH, 512)
        self.assertEqual(cfg.ADDR_WIDTH, 32)
        self.assertEqual(cfg.LEN_WIDTH, 16)
        self.assertEqual(cfg.DEPTH, 1024)
        self.assertEqual(cfg.NUM_RANDOM, 20)
        self.assertEqual(cfg.SEED, 12345)
        self.assertEqual(cfg.CLK_PERIOD_NS, 10)
        self.assertEqual(cfg.RESET_CYCLES, 5)

        # Derived-parameter sanity
        self.assertEqual(cfg.WORD_BYTES, cfg.DATA_WIDTH // 8)
        self.assertEqual(cfg.LANES_PER_WORD, cfg.DATA_WIDTH // 32)
        self.assertEqual(1 << cfg.ADDR_LSB, cfg.WORD_BYTES)
        self.assertEqual(cfg.MEM_BYTES, cfg.DEPTH * cfg.WORD_BYTES)
        self.assertGreaterEqual(cfg.ADDR_WIDTH, cfg.REQUIRED_ADDR_WIDTH)
        self.assertGreater(cfg.MAX_LEN_WORDS, 0)


if __name__ == "__main__":
    unittest.main()
