"""Centralized DMA verification parameters with env overrides and validation.

This module computes commonly used derived parameters and performs import-time
sanity checks so configuration issues fail fast with actionable error messages.
"""

from __future__ import annotations

import os


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _env_int(name: str, default: int) -> int:
    """Read an integer environment variable with clear error messaging."""
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return int(raw, 0)  # allow decimal / hex style input
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got {raw!r}") from exc


def _is_power_of_two(value: int) -> bool:
    return value > 0 and (value & (value - 1)) == 0


# ---------------------------------------------------------------------------
# Base parameters (env-overridable)
# ---------------------------------------------------------------------------

# DUT bus widths
DATA_WIDTH = _env_int("DMA_DATA_WIDTH", 512)
ADDR_WIDTH = _env_int("DMA_ADDR_WIDTH", 32)
LEN_WIDTH = _env_int("DMA_LEN_WIDTH", 16)

# RAM model
DEPTH = _env_int("DMA_DEPTH", 1024)

# Test control
NUM_RANDOM = _env_int("DMA_NUM_RANDOM", 20)
SEED = _env_int("DMA_SEED", 12345)

# Clock/reset controls
CLK_PERIOD_NS = _env_int("DMA_CLK_PERIOD_NS", 10)  # 100 MHz default
RESET_CYCLES = _env_int("DMA_RESET_CYCLES", 5)


# ---------------------------------------------------------------------------
# Derived parameters
# ---------------------------------------------------------------------------

WORD_BYTES = DATA_WIDTH // 8
LANES_PER_WORD = DATA_WIDTH // 32
ADDR_LSB = WORD_BYTES.bit_length() - 1  # equals clog2(WORD_BYTES) if power-of-two

MAX_LEN_WORDS = (1 << LEN_WIDTH) - 1
MEM_BYTES = DEPTH * WORD_BYTES
MAX_BYTE_ADDR = MEM_BYTES - 1 if MEM_BYTES > 0 else 0
REQUIRED_ADDR_WIDTH = max(1, MAX_BYTE_ADDR.bit_length())


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def _validate() -> None:
    # Basic positivity / ranges
    if DATA_WIDTH <= 0:
        raise ValueError(f"DMA_DATA_WIDTH must be > 0, got {DATA_WIDTH}")
    if ADDR_WIDTH <= 0:
        raise ValueError(f"DMA_ADDR_WIDTH must be > 0, got {ADDR_WIDTH}")
    if LEN_WIDTH <= 0:
        raise ValueError(f"DMA_LEN_WIDTH must be > 0, got {LEN_WIDTH}")
    if DEPTH <= 0:
        raise ValueError(f"DMA_DEPTH must be > 0, got {DEPTH}")
    if NUM_RANDOM < 0:
        raise ValueError(f"DMA_NUM_RANDOM must be >= 0, got {NUM_RANDOM}")
    if CLK_PERIOD_NS <= 0:
        raise ValueError(f"DMA_CLK_PERIOD_NS must be > 0, got {CLK_PERIOD_NS}")
    if RESET_CYCLES <= 0:
        raise ValueError(f"DMA_RESET_CYCLES must be > 0, got {RESET_CYCLES}")

    # Width compatibility checks
    if DATA_WIDTH % 8 != 0:
        raise ValueError(f"DMA_DATA_WIDTH must be byte-aligned (multiple of 8), got {DATA_WIDTH}")
    if DATA_WIDTH % 32 != 0:
        raise ValueError(
            f"DMA_DATA_WIDTH must be lane-aligned (multiple of 32), got {DATA_WIDTH}"
        )

    # Derived-parameter sanity checks
    if WORD_BYTES <= 0:
        raise ValueError(f"Derived WORD_BYTES must be > 0, got {WORD_BYTES}")
    if LANES_PER_WORD <= 0:
        raise ValueError(f"Derived LANES_PER_WORD must be > 0, got {LANES_PER_WORD}")
    if not _is_power_of_two(WORD_BYTES):
        raise ValueError(
            f"Derived WORD_BYTES must be a power of two for alignment math, got {WORD_BYTES}"
        )
    if (1 << ADDR_LSB) != WORD_BYTES:
        raise ValueError(
            "Derived ADDR_LSB mismatch: "
            f"(1 << ADDR_LSB)={1 << ADDR_LSB} != WORD_BYTES={WORD_BYTES}"
        )

    # Address-space sanity: bus must cover full RAM byte range
    if REQUIRED_ADDR_WIDTH > ADDR_WIDTH:
        raise ValueError(
            "DMA_ADDR_WIDTH too small for configured memory: "
            f"need {REQUIRED_ADDR_WIDTH} bits for {MEM_BYTES} bytes, got {ADDR_WIDTH}"
        )

    # Length sanity relative to encoding and RAM depth
    if MAX_LEN_WORDS <= 0:
        raise ValueError(
            f"Derived MAX_LEN_WORDS must be > 0, got {MAX_LEN_WORDS} (LEN_WIDTH={LEN_WIDTH})"
        )

    # Informational sanity relationships between encoded length and memory depth.
    # These are intentionally non-fatal because both regimes can be valid:
    #   - MAX_LEN_WORDS > DEPTH : length encoding can represent larger values than RAM span.
    #   - MAX_LEN_WORDS < DEPTH : a single transfer cannot cover full RAM.
    # Runtime APIs perform per-transfer bounds checks against DEPTH.


_validate()
