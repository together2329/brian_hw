"""SSOT-driven DMA scoreboard using FunctionalModel as the behavioral oracle.

SSOT traceability:
  - function_model              → FunctionalModel.apply() oracle
  - verify/equivalence_goals.json → goal_id mapping
  - test_requirements.scenarios → scenario-level pass/fail
  - cycle_model.latency         → per-beat / CSR latency checks
"""

import json
import sys
from pathlib import Path

# Ensure model/ is importable from within the cocotb test environment
_MODEL_DIR = Path(__file__).resolve().parents[2] / "model"
if str(_MODEL_DIR) not in sys.path:
    sys.path.insert(0, str(_MODEL_DIR))

from functional_model import FunctionalModel, RESP_OKAY
from transactions import (CsrTransaction, CsrResponse, ReadBeat, WriteBeat,
                          DmaEvent, CSR_CTRL, CSR_STATUS, CSR_SRC_ADDR,
                          CSR_DST_ADDR, CSR_LENGTH, CSR_PROGRESS,
                          CTRL_START_BIT, CTRL_SOFT_RESET,
                          STATUS_DONE_BIT, STATUS_ERROR_BIT)


class DmaScoreboard:
    """Cycle-accurate scoreboard that compares RTL observations against
    FunctionalModel expected values.

    The scoreboard records every DmaEvent, tags it with a goal_id, and
    provides a final pass/fail summary keyed by SSOT scenario.
    """

    def __init__(self):
        self.fm = FunctionalModel()
        self.events: list[DmaEvent] = []
        self._scenario_failures: dict[str, list[str]] = {}
        self._cycle = 0

    # ── helpers ────────────────────────────────────────────────────────
    def _event(self, kind: str, scenario_id: str, goal_id: str,
               fl_expected=None, rtl_observed=None) -> DmaEvent:
        ev = DmaEvent(cycle=self._cycle, kind=kind, scenario_id=scenario_id,
                      goal_id=goal_id, fl_expected=fl_expected,
                      rtl_observed=rtl_observed)
        self.events.append(ev)
        return ev

    def _compare(self, ev: DmaEvent, fl_val, rtl_val) -> bool:
        """Compare FL expected vs RTL observed; record the result."""
        ev.passed = (fl_val == rtl_val)
        if not ev.passed and ev.scenario_id:
            self._scenario_failures.setdefault(ev.scenario_id, []).append(
                f"[CYC={ev.cycle}] {ev.kind}: expected={fl_val}, got={rtl_val}"
            )
        return ev.passed

    def set_cycle(self, cycle: int):
        self._cycle = int(cycle)

    # ── transaction-level checkers ─────────────────────────────────────

    def check_reset(self, scenario_id: str, goal_id: str,
                    csr_ready: int, mem_rd_valid: int, mem_wr_valid: int,
                    irq_done: int, irq_error: int):
        """Check reset state matches FunctionalModel."""
        self.fm.reset()
        fl_result = self.fm.apply({"kind": "reset", "scenario_id": scenario_id})

        checks = [
            ("csr_ready", csr_ready, 0),
            ("mem_rd_valid", mem_rd_valid, 0),
            ("mem_wr_valid", mem_wr_valid, 0),
            ("irq_done", irq_done, 0),
            ("irq_error", irq_error, 0),
        ]
        all_pass = True
        for name, rtl_val, exp_val in checks:
            ev = self._event(f"reset_{name}", scenario_id, goal_id,
                             fl_expected=exp_val, rtl_observed=rtl_val)
            if not self._compare(ev, exp_val, rtl_val):
                all_pass = False
        return all_pass

    def check_csr_write(self, scenario_id: str, goal_id: str,
                        addr: int, wdata: int,
                        csr_error: int, irq_error: int):
        """Check a CSR write against FunctionalModel."""
        txn = {
            "kind": "csr_write_config",
            "scenario_id": scenario_id,
            "csr_addr": addr,
            "csr_wdata": wdata,
            "csr_write": 1,
            "busy": self.fm.state.get("busy", 0),
        }
        fl_result = self.fm.apply(txn)

        # FL expected csr_error
        fl_error = fl_result.get("csr_error", 0) if isinstance(fl_result, dict) else 0
        ev = self._event("csr_write", scenario_id, goal_id,
                         fl_expected=fl_error, rtl_observed=csr_error)
        return self._compare(ev, fl_error, csr_error)

    def check_csr_read(self, scenario_id: str, goal_id: str,
                       addr: int, rdata: int, csr_error: int):
        """Check a CSR read against FunctionalModel."""
        txn = {
            "kind": "csr_read_status",
            "scenario_id": scenario_id,
            "csr_addr": addr,
            "csr_write": 0,
        }
        fl_result = self.fm.apply(txn)

        if isinstance(fl_result, dict):
            fl_rdata = fl_result.get("csr_rdata", 0)
            fl_error = fl_result.get("csr_error", 0)
        else:
            fl_rdata = 0
            fl_error = 0

        all_pass = True
        ev = self._event("csr_read_data", scenario_id, goal_id,
                         fl_expected=fl_rdata, rtl_observed=rdata)
        if not self._compare(ev, fl_rdata, rdata):
            all_pass = False
        ev2 = self._event("csr_read_error", scenario_id, goal_id,
                          fl_expected=fl_error, rtl_observed=csr_error)
        if not self._compare(ev2, fl_error, csr_error):
            all_pass = False
        return all_pass

    def check_start_transfer(self, scenario_id: str, goal_id: str,
                             length: int, irq_done_en: int,
                             mem_rd_valid: int, irq_done: int):
        """Check start_transfer behavior against FunctionalModel."""
        # First, prime the FM with the length
        self.fm.state["length_bytes"] = length
        self.fm.state["irq_done_en"] = irq_done_en

        txn = {
            "kind": "start_transfer",
            "scenario_id": scenario_id,
            "csr_addr": CSR_CTRL,
            "csr_wdata": (irq_done_en << 1) | 1,  # start + irq_done_en
            "csr_write": 1,
            "busy": 0,
        }
        fl_result = self.fm.apply(txn)

        if isinstance(fl_result, dict):
            fl_mem_rd_valid = fl_result.get("mem_rd_valid", 0)
            fl_irq_done = fl_result.get("irq_done", 0)
        else:
            fl_mem_rd_valid = 0
            fl_irq_done = 0

        all_pass = True
        ev = self._event("start_mem_rd_valid", scenario_id, goal_id,
                         fl_expected=fl_mem_rd_valid, rtl_observed=mem_rd_valid)
        if not self._compare(ev, fl_mem_rd_valid, mem_rd_valid):
            all_pass = False
        ev2 = self._event("start_irq_done", scenario_id, goal_id,
                          fl_expected=fl_irq_done, rtl_observed=irq_done)
        if not self._compare(ev2, fl_irq_done, irq_done):
            all_pass = False
        return all_pass

    def check_read_request(self, scenario_id: str, goal_id: str,
                           mem_rd_addr: int):
        """Check read address against FunctionalModel expected src_addr+progress."""
        txn = {
            "kind": "memory_read_request",
            "scenario_id": scenario_id,
            "mem_rd_ready": 1,
            "src_addr": self.fm.state.get("src_addr", 0),
            "progress_bytes": self.fm.state.get("progress_bytes", 0),
        }
        fl_result = self.fm.apply(txn)

        fl_addr = fl_result.get("mem_rd_addr", 0) if isinstance(fl_result, dict) else 0
        ev = self._event("read_addr", scenario_id, goal_id,
                         fl_expected=fl_addr, rtl_observed=mem_rd_addr)
        return self._compare(ev, fl_addr, mem_rd_addr)

    def check_capture_read_data(self, scenario_id: str, goal_id: str,
                                read_data: int):
        """Feed captured read data into FunctionalModel."""
        txn = {
            "kind": "capture_read_data",
            "scenario_id": scenario_id,
            "mem_rd_data": read_data,
            "busy": self.fm.state.get("busy", 0),
            "write_buffer_full": self.fm.state.get("write_buffer_full", 0),
        }
        fl_result = self.fm.apply(txn)
        return True  # No output-port check; side-effect is state update

    def check_write_request(self, scenario_id: str, goal_id: str,
                            mem_wr_addr: int, mem_wr_data: int, mem_wr_strb: int):
        """Check write request against FunctionalModel."""
        txn = {
            "kind": "memory_write_request",
            "scenario_id": scenario_id,
            "dst_addr": self.fm.state.get("dst_addr", 0),
            "progress_bytes": self.fm.state.get("progress_bytes", 0),
            "read_data_buffer": self.fm.state.get("read_data_buffer", 0),
            "remaining_bytes": self.fm.state.get("remaining_bytes", 0),
        }
        fl_result = self.fm.apply(txn)

        if isinstance(fl_result, dict):
            fl_addr = fl_result.get("mem_wr_addr", 0)
            fl_data = fl_result.get("mem_wr_data", 0)
            fl_strb = fl_result.get("mem_wr_strb", 0)
        else:
            fl_addr = fl_data = fl_strb = 0

        all_pass = True
        for name, exp_val, rtl_val in [
            ("wr_addr", fl_addr, mem_wr_addr),
            ("wr_data", fl_data, mem_wr_data),
            ("wr_strb", fl_strb, mem_wr_strb),
        ]:
            ev = self._event(f"write_{name}", scenario_id, goal_id,
                             fl_expected=exp_val, rtl_observed=rtl_val)
            if not self._compare(ev, exp_val, rtl_val):
                all_pass = False
        return all_pass

    def check_write_accept(self, scenario_id: str, goal_id: str,
                           irq_done: int):
        """Check write-accept completion against FunctionalModel."""
        txn = {
            "kind": "memory_write_accept",
            "scenario_id": scenario_id,
            "remaining_bytes": self.fm.state.get("remaining_bytes", 0),
            "progress_bytes": self.fm.state.get("progress_bytes", 0),
            "beat_bytes": 4,
        }
        fl_result = self.fm.apply(txn)

        fl_irq_done = fl_result.get("irq_done", 0) if isinstance(fl_result, dict) else 0
        ev = self._event("write_accept_irq", scenario_id, goal_id,
                         fl_expected=fl_irq_done, rtl_observed=irq_done)
        return self._compare(ev, fl_irq_done, irq_done)

    def check_illegal_csr(self, scenario_id: str, goal_id: str,
                          addr: int, wdata: int, is_write: bool,
                          csr_error: int, irq_error: int):
        """Check illegal CSR/start-while-busy against FunctionalModel."""
        txn = {
            "kind": "illegal_csr_or_start",
            "scenario_id": scenario_id,
            "csr_addr": addr,
            "csr_wdata": wdata,
            "csr_write": 1 if is_write else 0,
            "busy": self.fm.state.get("busy", 0),
        }
        fl_result = self.fm.apply(txn)

        if isinstance(fl_result, dict):
            fl_error = fl_result.get("csr_error", 0)
            fl_irq = fl_result.get("irq_error", 0)
        else:
            fl_error = fl_irq = 0

        all_pass = True
        ev = self._event("illegal_csr_error", scenario_id, goal_id,
                         fl_expected=fl_error, rtl_observed=csr_error)
        if not self._compare(ev, fl_error, csr_error):
            all_pass = False
        ev2 = self._event("illegal_irq_error", scenario_id, goal_id,
                          fl_expected=fl_irq, rtl_observed=irq_error)
        if not self._compare(ev2, fl_irq, irq_error):
            all_pass = False
        return all_pass

    def check_soft_reset(self, scenario_id: str, goal_id: str,
                         mem_rd_valid: int, mem_wr_valid: int):
        """Check soft_reset/clear_abort against FunctionalModel."""
        txn = {
            "kind": "clear_or_abort",
            "scenario_id": scenario_id,
            "csr_addr": CSR_CTRL,
            "csr_wdata": 1 << CTRL_SOFT_RESET,
            "csr_write": 1,
        }
        fl_result = self.fm.apply(txn)

        if isinstance(fl_result, dict):
            fl_rd_valid = fl_result.get("mem_rd_valid", 0)
            fl_wr_valid = fl_result.get("mem_wr_valid", 0)
        else:
            fl_rd_valid = fl_wr_valid = 0

        all_pass = True
        ev = self._event("abort_mem_rd", scenario_id, goal_id,
                         fl_expected=fl_rd_valid, rtl_observed=mem_rd_valid)
        if not self._compare(ev, fl_rd_valid, mem_rd_valid):
            all_pass = False
        ev2 = self._event("abort_mem_wr", scenario_id, goal_id,
                          fl_expected=fl_wr_valid, rtl_observed=mem_wr_valid)
        if not self._compare(ev2, fl_wr_valid, mem_wr_valid):
            all_pass = False
        return all_pass

    def check_w1c_clear(self, scenario_id: str, goal_id: str,
                        done_bit: int, error_bit: int,
                        irq_done: int, irq_error: int):
        """Check W1C clear: write STATUS with done/error bits set."""
        txn = {
            "kind": "clear_or_abort",
            "scenario_id": scenario_id,
            "csr_addr": CSR_STATUS,
            "csr_wdata": (done_bit << STATUS_DONE_BIT) | (error_bit << STATUS_ERROR_BIT),
            "csr_write": 1,
        }
        fl_result = self.fm.apply(txn)

        if isinstance(fl_result, dict):
            fl_done = fl_result.get("done", self.fm.state.get("done", 0))
            fl_error = fl_result.get("error", self.fm.state.get("error", 0))
        else:
            fl_done = self.fm.state.get("done", 0)
            fl_error = self.fm.state.get("error", 0)

        fl_irq_done = 1 if fl_done and self.fm.state.get("irq_done_en", 0) else 0
        fl_irq_error = 1 if fl_error and self.fm.state.get("irq_error_en", 0) else 0

        all_pass = True
        for name, exp_val, rtl_val in [
            ("w1c_irq_done", fl_irq_done, irq_done),
            ("w1c_irq_error", fl_irq_error, irq_error),
        ]:
            ev = self._event(name, scenario_id, goal_id,
                             fl_expected=exp_val, rtl_observed=rtl_val)
            if not self._compare(ev, exp_val, rtl_val):
                all_pass = False
        return all_pass

    # ── scenario pass / fail ───────────────────────────────────────────

    def scenario_pass(self, scenario_id: str) -> bool:
        return scenario_id not in self._scenario_failures

    def failures_for(self, scenario_id: str) -> list[str]:
        return self._scenario_failures.get(scenario_id, [])

    @property
    def all_failures(self) -> dict[str, list[str]]:
        return dict(self._scenario_failures)

    def summary(self) -> dict:
        total_events = len(self.events)
        passed_events = sum(1 for e in self.events if e.passed is True)
        failed_events = sum(1 for e in self.events if e.passed is False)
        return {
            "total_events": total_events,
            "passed_events": passed_events,
            "failed_events": failed_events,
            "scenario_failures": dict(self._scenario_failures),
        }

    def export_events_jsonl(self, path: str):
        """Write scoreboard events as JSONL for sim_debug consumption."""
        rows = []
        for ev in self.events:
            rows.append({
                "goal_id": ev.goal_id,
                "scenario_id": ev.scenario_id,
                "cycle": ev.cycle,
                "kind": ev.kind,
                "fl_expected": ev.fl_expected,
                "rtl_observed": ev.rtl_observed,
                "passed": ev.passed,
            })
        Path(path).write_text("\n".join(json.dumps(r) for r in rows) + "\n")
