"""Scoreboard: DMA region comparison and functional coverage tracking."""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

import config
from patterns import PatternMode


# ------------------------------------------------------------------
# Region Comparison
# ------------------------------------------------------------------


@dataclass
class MismatchDetail:
    """Detailed mismatch data for one word index."""

    word_index: int
    expected: int
    actual: int
    xor: int
    differing_lane_indices: list[int]


@dataclass
class CompareResult:
    """Result of comparing two memory regions."""

    match: bool
    src_addr: int
    dst_addr: int
    length: int
    compared_words: int
    expected_words: int
    actual_words: int
    mismatches: list[MismatchDetail] = field(default_factory=list)

    @property
    def mismatch_count(self) -> int:
        return len(self.mismatches)

    @property
    def length_match(self) -> bool:
        return self.expected_words == self.actual_words


def _word_mask() -> int:
    return (1 << config.DATA_WIDTH) - 1


def _lane_diff_indices(xor_value: int) -> list[int]:
    lanes: list[int] = []
    lane_mask = (1 << 32) - 1
    for lane in range(config.LANES_PER_WORD):
        if (xor_value >> (lane * 32)) & lane_mask:
            lanes.append(lane)
    return lanes


def compare_region(
    expected: list[int],
    actual: list[int],
    src_addr: int = 0,
    dst_addr: int = 0,
    length: int = 0,
) -> CompareResult:
    """Compare expected vs actual memory region data.

    Returns a structured result with lane-level mismatch diagnostics.
    """
    mask = _word_mask()
    mismatches: list[MismatchDetail] = []

    compared_words = min(len(expected), len(actual))
    for i in range(compared_words):
        exp = int(expected[i]) & mask
        act = int(actual[i]) & mask
        if exp != act:
            diff = exp ^ act
            mismatches.append(
                MismatchDetail(
                    word_index=i,
                    expected=exp,
                    actual=act,
                    xor=diff,
                    differing_lane_indices=_lane_diff_indices(diff),
                )
            )

    return CompareResult(
        match=(len(mismatches) == 0 and len(expected) == len(actual)),
        src_addr=src_addr,
        dst_addr=dst_addr,
        length=length,
        compared_words=compared_words,
        expected_words=len(expected),
        actual_words=len(actual),
        mismatches=mismatches,
    )


# ------------------------------------------------------------------
# Functional Coverage
# ------------------------------------------------------------------


class CoverageTracker:
    """Tracks functional coverage for DMA transfers."""

    def __init__(self):
        self.lengths: dict[int, int] = defaultdict(int)
        self.overlaps: dict[str, int] = defaultdict(int)
        self.regions: dict[str, int] = defaultdict(int)
        self.patterns: dict[int, int] = defaultdict(int)
        self._total_transfers = 0
        self._total_pass = 0
        self._total_fail = 0

    def record_transfer(
        self,
        length: int,
        src_addr: int,
        dst_addr: int,
        pattern_mode: int = 0,
        passed: bool = True,
    ):
        """Record a single DMA transfer for coverage."""
        self._total_transfers += 1
        if passed:
            self._total_pass += 1
        else:
            self._total_fail += 1

        self.lengths[length] += 1
        overlap = self._classify_overlap(src_addr, dst_addr, length)
        self.overlaps[overlap] += 1

        region_id = self._classify_region(src_addr, dst_addr)
        self.regions[region_id] += 1
        self.patterns[int(pattern_mode)] += 1

    @staticmethod
    def _classify_overlap(src_addr: int, dst_addr: int, length: int) -> str:
        word_bytes = config.WORD_BYTES
        src_end = src_addr + length * word_bytes
        dst_end = dst_addr + length * word_bytes

        if src_addr == dst_addr:
            return "full_overlap"
        if src_addr < dst_end and dst_addr < src_end:
            return "partial_overlap"
        return "no_overlap"

    @staticmethod
    def _classify_region(src_addr: int, dst_addr: int) -> str:
        page = 1024
        src_page = src_addr // page
        dst_page = dst_addr // page
        return f"src_pg{src_page}_dst_pg{dst_page}"

    @property
    def total_transfers(self) -> int:
        return self._total_transfers

    @property
    def pass_rate(self) -> float:
        if self._total_transfers == 0:
            return 0.0
        return self._total_pass / self._total_transfers

    def coverage_summary(self) -> dict[str, Any]:
        """Return summary dictionary for JSON/reporting."""
        return {
            "transfers": self._total_transfers,
            "pass": self._total_pass,
            "fail": self._total_fail,
            "pass_rate": self.pass_rate,
            "length_bins": {str(k): v for k, v in sorted(self.lengths.items())},
            "overlap_bins": {k: v for k, v in sorted(self.overlaps.items())},
            "region_bins": {k: v for k, v in sorted(self.regions.items())},
            "pattern_bins": {
                str(PatternMode(k)): v
                for k, v in sorted(self.patterns.items())
            },
        }

    def export_json(self, filepath: str):
        """Export coverage summary to a JSON file."""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.coverage_summary(), f, indent=2, default=str)

    def report(self) -> str:
        """Return a human-readable coverage report string."""
        lines = []
        lines.append("=" * 60)
        lines.append("DMA FUNCTIONAL COVERAGE REPORT")
        lines.append("=" * 60)
        lines.append(f"Total transfers : {self._total_transfers}")
        lines.append(f"Pass            : {self._total_pass}")
        lines.append(f"Fail            : {self._total_fail}")
        lines.append(f"Pass rate       : {self.pass_rate:.1%}")
        lines.append("")

        lines.append(f"Length bins     : {len(self.lengths)} unique lengths")
        for k, v in sorted(self.lengths.items()):
            lines.append(f"  length={k:>5d}  count={v}")

        lines.append(f"Overlap bins    : {dict(self.overlaps)}")
        lines.append(f"Region bins     : {len(self.regions)} unique regions")
        for k, v in sorted(self.regions.items()):
            lines.append(f"  {k}  count={v}")

        lines.append("Pattern bins    :")
        for k, v in sorted(self.patterns.items()):
            lines.append(f"  {PatternMode(k)!s:<25s}  count={v}")

        lines.append("=" * 60)
        return "\n".join(lines)
