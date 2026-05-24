#!/usr/bin/env python3
"""
Functional Model for real_llm_counter_demo — 8-bit saturating up/down counter.

SSOT authority: yaml/real_llm_counter_demo.ssot.yaml
Transactions: FM_CLEAR, FM_LOAD, FM_INC, FM_DEC, FM_HOLD, FM_INVALID

This model is the locked behavioral oracle for RTL verification.
Do not modify to match RTL — open a human gate for semantic changes.
"""

from __future__ import annotations
import json
import sys
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Constants from SSOT
# ---------------------------------------------------------------------------
WIDTH = 8
SAT_MAX = (1 << WIDTH) - 1   # 255
SAT_MIN = 0
ACCEPTED_WIDTH = 32
ACCEPTED_MASK = (1 << ACCEPTED_WIDTH) - 1

CMD_CLEAR = 0
CMD_LOAD  = 1
CMD_INC   = 2
CMD_DEC   = 3
CMD_HOLD  = 4
# 5, 6, 7 are reserved → treated as HOLD for count; status records actual cmd

# ---------------------------------------------------------------------------
# Transaction dataclass
# ---------------------------------------------------------------------------
@dataclass
class Transaction:
    """Single command transaction accepted by the counter."""
    cmd: int            # 3-bit command encoding
    cmd_valid: int = 1  # must be 1 for acceptance
    load_value: int = 0 # 8-bit value sampled when cmd == CMD_LOAD

# ---------------------------------------------------------------------------
# Functional Model
# ---------------------------------------------------------------------------
class FunctionalModel:
    """
    Cycle-independent behavioral model for real_llm_counter_demo.

    State variables (from SSOT function_model.state_variables):
      - count          : 8-bit saturating counter
      - accepted_count : 32-bit wrapping accepted-command counter
      - last_cmd       : 3-bit last accepted command encoding

    Invariants (from SSOT function_model.invariants):
      - count ∈ [0, 255]
      - zero ⇔ count == 0
      - max  ⇔ count == 255
      - cmd_ready is always 1
      - accepted_count increments on every cmd_valid && cmd_ready
      - status == last_cmd after each accepted command
    """

    def __init__(self):
        self.count: int = 0
        self.accepted_count: int = 0
        self.last_cmd: int = 0
        self.cmd_ready: int = 1  # always 1 per SSOT
        # Trace log for debugging
        self.trace: List[Dict] = []

    # -- Reset ---------------------------------------------------------------
    def reset(self) -> Dict:
        """Apply async active-low reset state."""
        self.count = 0
        self.accepted_count = 0
        self.last_cmd = 0
        return self._snapshot("reset")

    # -- Derived outputs (combinational flags) --------------------------------
    @property
    def zero(self) -> int:
        """zero flag: 1 iff count == 0."""
        return 1 if self.count == 0 else 0

    @property
    def max(self) -> int:
        """max flag: 1 iff count == 255."""
        return 1 if self.count == SAT_MAX else 0

    @property
    def status(self) -> int:
        """status output mirrors last_cmd."""
        return self.last_cmd

    # -- Snapshot for trace/checking ------------------------------------------
    def _snapshot(self, label: str) -> Dict:
        return {
            "label": label,
            "count": self.count,
            "zero": self.zero,
            "max": self.max,
            "accepted_count": self.accepted_count,
            "status": self.status,
            "cmd_ready": self.cmd_ready,
        }

    # -- Transaction helpers --------------------------------------------------
    def _increment_accepted(self):
        """Increment accepted_count with 32-bit wrapping."""
        self.accepted_count = (self.accepted_count + 1) & ACCEPTED_MASK

    # -- FM_CLEAR ------------------------------------------------------------
    def _apply_clear(self, txn: Transaction) -> Dict:
        """FM_CLEAR: count ← 0"""
        self.count = 0
        self.last_cmd = CMD_CLEAR
        self._increment_accepted()
        return self._snapshot("FM_CLEAR")

    # -- FM_LOAD -------------------------------------------------------------
    def _apply_load(self, txn: Transaction) -> Dict:
        """FM_LOAD: count ← load_value"""
        lv = txn.load_value & SAT_MAX
        self.count = lv
        self.last_cmd = CMD_LOAD
        self._increment_accepted()
        return self._snapshot("FM_LOAD")

    # -- FM_INC --------------------------------------------------------------
    def _apply_inc(self, txn: Transaction) -> Dict:
        """FM_INC: count ← min(count + 1, 255) — saturating increment."""
        self.count = min(self.count + 1, SAT_MAX)
        self.last_cmd = CMD_INC
        self._increment_accepted()
        return self._snapshot("FM_INC")

    # -- FM_DEC --------------------------------------------------------------
    def _apply_dec(self, txn: Transaction) -> Dict:
        """FM_DEC: count ← max(count - 1, 0) — saturating decrement."""
        self.count = max(self.count - 1, SAT_MIN)
        self.last_cmd = CMD_DEC
        self._increment_accepted()
        return self._snapshot("FM_DEC")

    # -- FM_HOLD -------------------------------------------------------------
    def _apply_hold(self, txn: Transaction) -> Dict:
        """FM_HOLD: count unchanged, accepted_count increments."""
        self.last_cmd = CMD_HOLD
        self._increment_accepted()
        return self._snapshot("FM_HOLD")

    # -- FM_INVALID (reserved 5-7) -------------------------------------------
    def _apply_invalid(self, txn: Transaction) -> Dict:
        """FM_INVALID: count unchanged (HOLD behavior), status records actual cmd."""
        self.last_cmd = txn.cmd & 0x7
        self._increment_accepted()
        return self._snapshot("FM_INVALID")

    # -- Main dispatch -------------------------------------------------------
    def apply(self, txn: Transaction) -> Dict:
        """
        Apply a single transaction and return the post-transaction state snapshot.

        This is the primary entry point for the scoreboard/reference model.
        """
        if txn.cmd_valid != 1:
            # No command accepted — return current state unchanged
            snap = self._snapshot("no_valid")
            self.trace.append(snap)
            return snap

        cmd = txn.cmd & 0x7

        if cmd == CMD_CLEAR:
            result = self._apply_clear(txn)
        elif cmd == CMD_LOAD:
            result = self._apply_load(txn)
        elif cmd == CMD_INC:
            result = self._apply_inc(txn)
        elif cmd == CMD_DEC:
            result = self._apply_dec(txn)
        elif cmd == CMD_HOLD:
            result = self._apply_hold(txn)
        else:
            # cmd >= 5: reserved, treated as HOLD with status = actual cmd
            result = self._apply_invalid(txn)

        self.trace.append(result)
        return result

    # -- Invariant check -----------------------------------------------------
    def check_invariants(self) -> List[str]:
        """Return list of invariant violations (empty if all pass)."""
        violations = []
        if not (0 <= self.count <= SAT_MAX):
            violations.append(f"count {self.count} out of range [0, {SAT_MAX}]")
        if self.zero != (1 if self.count == 0 else 0):
            violations.append(f"zero flag mismatch: count={self.count}, zero={self.zero}")
        if self.max != (1 if self.count == SAT_MAX else 0):
            violations.append(f"max flag mismatch: count={self.count}, max={self.max}")
        if self.cmd_ready != 1:
            violations.append(f"cmd_ready is {self.cmd_ready}, expected 1")
        if self.status != self.last_cmd:
            violations.append(f"status {self.status} != last_cmd {self.last_cmd}")
        return violations


# ---------------------------------------------------------------------------
# Self-checks
# ---------------------------------------------------------------------------
def _assert_eq(name: str, actual, expected):
    if actual != expected:
        raise AssertionError(f"FAIL [{name}]: expected {expected}, got {actual}")


def self_check_reset():
    """SC01: Reset contract — all state to zero, flags correct."""
    m = FunctionalModel()
    s = m.reset()
    _assert_eq("reset.count", s["count"], 0)
    _assert_eq("reset.zero", s["zero"], 1)
    _assert_eq("reset.max", s["max"], 0)
    _assert_eq("reset.accepted_count", s["accepted_count"], 0)
    _assert_eq("reset.status", s["status"], 0)
    _assert_eq("reset.cmd_ready", s["cmd_ready"], 1)
    print("  PASS: reset_contract")


def self_check_clear():
    """SC02: CLEAR command — count goes to 0."""
    m = FunctionalModel()
    m.reset()
    # Load a non-zero value first
    m.apply(Transaction(cmd=CMD_LOAD, load_value=0x42))
    s = m.apply(Transaction(cmd=CMD_CLEAR))
    _assert_eq("clear.count", s["count"], 0)
    _assert_eq("clear.zero", s["zero"], 1)
    _assert_eq("clear.max", s["max"], 0)
    _assert_eq("clear.accepted_count", s["accepted_count"], 2)
    _assert_eq("clear.status", s["status"], CMD_CLEAR)
    print("  PASS: clear_command")


def self_check_load():
    """SC03: LOAD command — count takes load_value."""
    m = FunctionalModel()
    m.reset()
    s = m.apply(Transaction(cmd=CMD_LOAD, load_value=0x42))
    _assert_eq("load.count", s["count"], 0x42)
    _assert_eq("load.zero", s["zero"], 0)
    _assert_eq("load.max", s["max"], 0)
    _assert_eq("load.accepted_count", s["accepted_count"], 1)
    _assert_eq("load.status", s["status"], CMD_LOAD)
    print("  PASS: load_command")


def self_check_load_boundary():
    """SC12 partial: LOAD boundary values 0, 128, 255."""
    m = FunctionalModel()
    m.reset()
    # Load 0
    s = m.apply(Transaction(cmd=CMD_LOAD, load_value=0))
    _assert_eq("load0.count", s["count"], 0)
    _assert_eq("load0.zero", s["zero"], 1)
    _assert_eq("load0.max", s["max"], 0)
    # Load 255
    s = m.apply(Transaction(cmd=CMD_LOAD, load_value=255))
    _assert_eq("load255.count", s["count"], 255)
    _assert_eq("load255.zero", s["zero"], 0)
    _assert_eq("load255.max", s["max"], 1)
    # Load 128
    s = m.apply(Transaction(cmd=CMD_LOAD, load_value=128))
    _assert_eq("load128.count", s["count"], 128)
    _assert_eq("load128.zero", s["zero"], 0)
    _assert_eq("load128.max", s["max"], 0)
    print("  PASS: load_boundary")


def self_check_inc():
    """SC04: INC command — count increments."""
    m = FunctionalModel()
    m.reset()
    m.apply(Transaction(cmd=CMD_LOAD, load_value=10))
    s = m.apply(Transaction(cmd=CMD_INC))
    _assert_eq("inc.count", s["count"], 11)
    _assert_eq("inc.zero", s["zero"], 0)
    _assert_eq("inc.max", s["max"], 0)
    _assert_eq("inc.status", s["status"], CMD_INC)
    print("  PASS: increment_command")


def self_check_inc_saturation():
    """SC05: INC at max (255) — saturates."""
    m = FunctionalModel()
    m.reset()
    m.apply(Transaction(cmd=CMD_LOAD, load_value=255))
    s = m.apply(Transaction(cmd=CMD_INC))
    _assert_eq("inc_sat.count", s["count"], 255)
    _assert_eq("inc_sat.max", s["max"], 1)
    _assert_eq("inc_sat.zero", s["zero"], 0)
    print("  PASS: increment_saturation")


def self_check_dec():
    """SC06: DEC command — count decrements."""
    m = FunctionalModel()
    m.reset()
    m.apply(Transaction(cmd=CMD_LOAD, load_value=10))
    s = m.apply(Transaction(cmd=CMD_DEC))
    _assert_eq("dec.count", s["count"], 9)
    _assert_eq("dec.zero", s["zero"], 0)
    _assert_eq("dec.max", s["max"], 0)
    _assert_eq("dec.status", s["status"], CMD_DEC)
    print("  PASS: decrement_command")


def self_check_dec_saturation():
    """SC07: DEC at min (0) — saturates."""
    m = FunctionalModel()
    m.reset()
    # count is already 0 after reset
    s = m.apply(Transaction(cmd=CMD_DEC))
    _assert_eq("dec_sat.count", s["count"], 0)
    _assert_eq("dec_sat.zero", s["zero"], 1)
    _assert_eq("dec_sat.max", s["max"], 0)
    print("  PASS: decrement_saturation")


def self_check_hold():
    """SC08: HOLD command — count unchanged."""
    m = FunctionalModel()
    m.reset()
    m.apply(Transaction(cmd=CMD_LOAD, load_value=0x55))
    s = m.apply(Transaction(cmd=CMD_HOLD))
    _assert_eq("hold.count", s["count"], 0x55)
    _assert_eq("hold.accepted_count", s["accepted_count"], 2)
    _assert_eq("hold.status", s["status"], CMD_HOLD)
    print("  PASS: hold_command")


def self_check_invalid():
    """SC09: Invalid command (5,6,7) — treated as HOLD, status records cmd."""
    for invalid_cmd in (5, 6, 7):
        m = FunctionalModel()
        m.reset()
        m.apply(Transaction(cmd=CMD_LOAD, load_value=0x33))
        s = m.apply(Transaction(cmd=invalid_cmd))
        _assert_eq(f"invalid_cmd{invalid_cmd}.count", s["count"], 0x33)
        _assert_eq(f"invalid_cmd{invalid_cmd}.status", s["status"], invalid_cmd)
        _assert_eq(f"invalid_cmd{invalid_cmd}.accepted_count", s["accepted_count"], 2)
    print("  PASS: invalid_command_as_hold")


def self_check_accepted_count_wrap():
    """SC10: accepted_count wraps at 2^32."""
    m = FunctionalModel()
    m.reset()
    m.accepted_count = ACCEPTED_MASK  # 0xFFFFFFFF
    s = m.apply(Transaction(cmd=CMD_HOLD))
    _assert_eq("wrap.accepted_count", s["accepted_count"], 0)
    print("  PASS: accepted_count_wrap")


def self_check_back_to_back():
    """SC11: Back-to-back INC/DEC commands."""
    m = FunctionalModel()
    m.reset()
    s = m.apply(Transaction(cmd=CMD_INC))   # 0 → 1
    _assert_eq("b2b_1.count", s["count"], 1)
    s = m.apply(Transaction(cmd=CMD_DEC))   # 1 → 0
    _assert_eq("b2b_2.count", s["count"], 0)
    s = m.apply(Transaction(cmd=CMD_INC))   # 0 → 1
    _assert_eq("b2b_3.count", s["count"], 1)
    _assert_eq("b2b_3.accepted_count", s["accepted_count"], 3)
    print("  PASS: back_to_back_commands")


def self_check_invariants():
    """Invariant checks after various command sequences."""
    m = FunctionalModel()
    m.reset()
    violations = m.check_invariants()
    _assert_eq("inv_after_reset", len(violations), 0)

    # Sequence covering all commands
    cmds = [
        Transaction(cmd=CMD_LOAD, load_value=100),
        Transaction(cmd=CMD_INC),
        Transaction(cmd=CMD_DEC),
        Transaction(cmd=CMD_HOLD),
        Transaction(cmd=CMD_CLEAR),
        Transaction(cmd=5),
        Transaction(cmd=CMD_LOAD, load_value=255),
        Transaction(cmd=CMD_INC),  # saturate
        Transaction(cmd=CMD_LOAD, load_value=0),
        Transaction(cmd=CMD_DEC),  # saturate at 0
    ]
    for txn in cmds:
        m.apply(txn)
        violations = m.check_invariants()
        if violations:
            raise AssertionError(f"Invariant violation after {txn}: {violations}")

    print("  PASS: invariants")


# ---------------------------------------------------------------------------
# Master self-check runner
# ---------------------------------------------------------------------------
ALL_SELF_CHECKS = {
    "FM_RESET":    self_check_reset,
    "FM_CLEAR":    self_check_clear,
    "FM_LOAD":     self_check_load,
    "FM_LOAD_BOUNDARY": self_check_load_boundary,
    "FM_INC":      self_check_inc,
    "FM_INC_SAT":  self_check_inc_saturation,
    "FM_DEC":      self_check_dec,
    "FM_DEC_SAT":  self_check_dec_saturation,
    "FM_HOLD":     self_check_hold,
    "FM_INVALID":  self_check_invalid,
    "FM_ACCEPTED_WRAP": self_check_accepted_count_wrap,
    "FM_BACK_TO_BACK": self_check_back_to_back,
    "FM_INVARIANTS": self_check_invariants,
}


def run_all_self_checks() -> Dict[str, str]:
    """Run every self-check; return dict of {name: PASS|FAIL}."""
    results = {}
    for name, fn in ALL_SELF_CHECKS.items():
        try:
            fn()
            results[name] = "PASS"
        except AssertionError as e:
            results[name] = f"FAIL: {e}"
        except Exception as e:
            results[name] = f"ERROR: {e}"
    return results


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 60)
    print("Functional Model Self-Check: real_llm_counter_demo")
    print("=" * 60)
    results = run_all_self_checks()
    print()
    all_pass = True
    for name, status in results.items():
        marker = "✓" if status == "PASS" else "✗"
        print(f"  {marker} {name}: {status}")
        if status != "PASS":
            all_pass = False

    print()
    if all_pass:
        print("ALL SELF-CHECKS PASSED")
        sys.exit(0)
    else:
        print("SELF-CHECKS FAILED")
        sys.exit(1)
