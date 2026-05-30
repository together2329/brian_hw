from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any

from pyuvm import uvm_scoreboard

_MODEL_DIR = Path(__file__).resolve().parents[2] / "model"
_TC_DIR = Path(__file__).resolve().parents[2] / "tc"
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_RUNTIME_DIR = Path(
    os.environ.get("COMMON_AI_AGENT_ROOT") or _PROJECT_ROOT
) / "workflow" / "tb-gen" / "runtime"
for path in (_MODEL_DIR, _TC_DIR, _RUNTIME_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from equivalence_scoreboard import EquivalenceScoreboard  # noqa: E402
from functional_model import FunctionalModel  # noqa: E402
from mctp_assembler_scenarios import (  # noqa: E402
    DEFAULT_LOCAL_EID,
    DEFAULT_SRAM_BASE,
    DEFAULT_SRAM_LIMIT,
    parse_descriptor_words,
    parse_status,
)


def _scenario_goal_map(ip_dir: Path) -> dict[str, list[str]]:
    goals_path = ip_dir / "verify" / "equivalence_goals.json"
    if not goals_path.is_file():
        return {}
    doc = json.loads(goals_path.read_text(encoding="utf-8"))
    out: dict[str, list[str]] = {}
    for goal in doc.get("goals") or []:
        if not isinstance(goal, dict) or goal.get("blocked"):
            continue
        gid = str(goal.get("goal_id") or "")
        contract = goal.get("stimulus_contract") if isinstance(goal.get("stimulus_contract"), dict) else {}
        scenario_id = str(contract.get("transaction_type") or "")
        if scenario_id.startswith("SC_"):
            out.setdefault(scenario_id, []).append(gid)
        elif gid.startswith("EQ_SCENARIO_"):
            inferred = gid.removeprefix("EQ_SCENARIO_")
            out.setdefault(inferred, []).append(gid)
    return out


class MctpScoreboard(uvm_scoreboard):
    """Compare RTL observations against FunctionalModel and EQ scenario goals."""

    def __init__(self, name: str, ip_dir: Path, parent=None):
        super().__init__(name, parent)
        self.ip_dir = ip_dir
        self.ip = ip_dir.name
        self.fm = FunctionalModel()
        self.drained_fm_descriptors: list[Any] = []
        self.failures: list[str] = []
        self.events: list[dict[str, Any]] = []
        self._event_path = ip_dir / "sim" / "scoreboard_events.jsonl"
        self._scenario_goals = _scenario_goal_map(ip_dir)
        self._eq: EquivalenceScoreboard | None = None

    def _eq_adapter(self) -> EquivalenceScoreboard:
        if self._eq is None:
            model_path = self.ip_dir / "model" / "functional_model.py"
            module_name = f"{self.ip}_functional_model"
            if module_name not in sys.modules and model_path.is_file():
                spec = importlib.util.spec_from_file_location(module_name, model_path)
                if spec is not None and spec.loader is not None:
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = module
                    spec.loader.exec_module(module)
            self._eq = EquivalenceScoreboard(
                self.ip,
                root=_PROJECT_ROOT,
                events_path=self._event_path,
                reset_events=False,
            )
        return self._eq

    def reset_oracle(self) -> None:
        self.fm.reset()
        self.drained_fm_descriptors.clear()
        self.fm.configure(
            enable=True,
            local_eid=DEFAULT_LOCAL_EID,
            sram_base=DEFAULT_SRAM_BASE,
            sram_limit=DEFAULT_SRAM_LIMIT,
            dest_filter_enable=True,
            mtu_bytes=64,
        )

    def begin_test_evidence(self) -> None:
        self.events.clear()
        self.failures.clear()
        self._event_path.parent.mkdir(parents=True, exist_ok=True)
        self._event_path.write_text("", encoding="utf-8")

    def apply_apb_setup(self, writes) -> None:
        for w in writes:
            self.fm.apb_write(w.addr, w.data)

    def feed_tlps(self, tlps: list[list[int]]) -> None:
        for tlp in tlps:
            self.fm.process_tlp({"tlp_bytes": tlp})

    def note_descriptor_drain(self, count: int = 1) -> None:
        """Mirror software DESC_POP: move FM head descriptors into drained history."""
        for _ in range(count):
            if not self.fm.descriptor_fifo:
                break
            self.drained_fm_descriptors.append(self.fm.descriptor_fifo.pop(0))

    def _all_fm_descriptors(self) -> list[Any]:
        return list(self.drained_fm_descriptors) + list(self.fm.descriptor_fifo)

    def _record_eq_goals(
        self,
        scenario_id: str,
        rtl_observed: dict[str, Any],
        passed: bool,
        mismatch: str,
        coverage_refs: list[str] | None = None,
    ) -> None:
        goal_ids = list(self._scenario_goals.get(scenario_id, []))
        if not goal_ids:
            return
        eq = self._eq_adapter()
        seen: set[str] = set()
        for goal_id in goal_ids:
            if not goal_id or goal_id in seen or goal_id not in eq.goals:
                continue
            seen.add(goal_id)
            try:
                eq.record(
                    goal_id,
                    scenario_id=scenario_id,
                    stimulus={"scenario_id": scenario_id, "kind": scenario_id},
                    rtl_observed=rtl_observed,
                    passed=passed,
                    mismatch=mismatch,
                    coverage_refs=coverage_refs or [scenario_id],
                )
            except Exception as exc:
                self.failures.append(f"{goal_id}: {exc}")

    def record(
        self,
        scenario_id: str,
        rtl_observed: dict[str, Any],
        passed: bool,
        mismatch: str = "",
        coverage_refs: list[str] | None = None,
    ) -> dict[str, Any]:
        row = {
            "goal_id": scenario_id,
            "scenario_id": scenario_id,
            "cycle": 0,
            "stimulus": {"scenario_id": scenario_id},
            "fl_expected": {
                "descriptor_count": len(self.fm.descriptor_fifo),
                "packet_drop_count": self.fm.counters["packet_drop_count"],
                "assembly_drop_count": self.fm.counters["assembly_drop_count"],
            },
            "rtl_observed": rtl_observed,
            "passed": passed,
            "mismatch": mismatch,
            "coverage_refs": coverage_refs if coverage_refs is not None else [scenario_id],
        }
        self.events.append(row)
        if not passed:
            self.failures.append(f"{scenario_id}: {mismatch}")
        self._event_path.parent.mkdir(parents=True, exist_ok=True)
        with self._event_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
        self._record_eq_goals(
            scenario_id,
            rtl_observed,
            passed,
            mismatch,
            coverage_refs=row["coverage_refs"],
        )
        return row

    def check_apb_regs(self, scenario_id: str, control: int) -> None:
        expected = 0x0000_0004
        passed = (control & 0x3E) == (expected & 0x3E)
        self.record(
            scenario_id,
            {"control": control},
            passed,
            "" if passed else f"control reset mismatch expected~0x{expected:08x} got 0x{control:08x}",
        )

    def check_burst_checkpoint(
        self,
        scenario_id: str,
        *,
        checkpoint,
        status: int,
        packet_drop_count: int,
    ) -> None:
        parsed = parse_status(status)
        rtl_obs = {
            "active_context_count": parsed["active_context_count"],
            "packet_drop_count": packet_drop_count,
            "status": status,
        }
        mismatch_parts: list[str] = []
        if checkpoint.active_context_count is not None:
            if parsed["active_context_count"] != checkpoint.active_context_count:
                mismatch_parts.append(
                    f"active_context_count rtl={parsed['active_context_count']} "
                    f"expected={checkpoint.active_context_count}"
                )
        if checkpoint.packet_drop_count is not None:
            if packet_drop_count < checkpoint.packet_drop_count:
                mismatch_parts.append(
                    f"packet_drop_count rtl={packet_drop_count} expected>={checkpoint.packet_drop_count}"
                )
        passed = not mismatch_parts
        self.record(
            scenario_id,
            rtl_obs,
            passed,
            "; ".join(mismatch_parts),
            coverage_refs=[scenario_id, "context_queue"],
        )

    def check_descriptors(
        self,
        scenario_id: str,
        *,
        desc_words_list: list[tuple[int, int, int, int]],
        sram_payloads: list[list[int] | None],
        expect_count: int,
        packet_drop_count: int = 0,
        assembly_drop_count: int = 0,
        error_status: int = 0,
        active_context_count: int | None = None,
        expect_final_active_contexts: int | None = None,
    ) -> None:
        all_fm = self._all_fm_descriptors()
        fm_desc = len(all_fm)
        rtl_obs: dict[str, Any] = {
            "desc_count": len(desc_words_list),
            "packet_drop_count": packet_drop_count,
            "assembly_drop_count": assembly_drop_count,
            "error_status": error_status,
            "desc_words": desc_words_list[0] if desc_words_list else None,
            "sram_bytes": sram_payloads[0] if sram_payloads else None,
            "active_context_count": active_context_count,
        }
        if fm_desc < expect_count or len(desc_words_list) < expect_count:
            self.record(
                scenario_id,
                rtl_obs,
                False,
                f"expected {expect_count} descriptors fm={fm_desc} rtl={len(desc_words_list)}",
            )
            return
        remaining_fm = list(all_fm)
        for idx in range(expect_count):
            words = desc_words_list[idx]
            parsed = parse_descriptor_words(*words)
            fm_desc_obj = None
            fm_match_idx = -1
            for cand_idx, candidate in enumerate(remaining_fm):
                if (
                    candidate.source_eid == parsed.get("source_eid")
                    and candidate.message_tag == parsed.get("message_tag")
                    and candidate.tag_owner == parsed.get("tag_owner")
                ):
                    fm_desc_obj = candidate
                    fm_match_idx = cand_idx
                    break
            if fm_desc_obj is None:
                self.record(
                    scenario_id,
                    {**rtl_obs, "descriptor_index": idx},
                    False,
                    f"desc[{idx}] no FM match for source={parsed.get('source_eid')} tag={parsed.get('message_tag')}",
                )
                return
            remaining_fm.pop(fm_match_idx)
            if parsed.get("payload_byte_count") != fm_desc_obj.payload_byte_count:
                self.record(
                    scenario_id,
                    {**rtl_obs, "descriptor_index": idx},
                    False,
                    f"desc[{idx}] payload_byte_count fm={fm_desc_obj.payload_byte_count} "
                    f"rtl={parsed.get('payload_byte_count')}",
                )
                return
            if parsed.get("source_eid") != fm_desc_obj.source_eid:
                self.record(
                    scenario_id,
                    {**rtl_obs, "descriptor_index": idx},
                    False,
                    f"desc[{idx}] source_eid fm={fm_desc_obj.source_eid} rtl={parsed.get('source_eid')}",
                )
                return
            sram_bytes = sram_payloads[idx] if idx < len(sram_payloads) else None
            if sram_bytes is not None:
                start = fm_desc_obj.sram_start_addr
                count = fm_desc_obj.payload_byte_count
                expected: list[int] = []
                for wr in self.fm.sram_writes:
                    for offset, byte in enumerate(wr["bytes"]):
                        addr = wr["addr"] + offset
                        if start <= addr < start + count:
                            expected.append(byte)
                expected = expected[:count]
                if sram_bytes[: len(expected)] != expected:
                    self.record(
                        scenario_id,
                        {**rtl_obs, "descriptor_index": idx},
                        False,
                        f"desc[{idx}] sram mismatch fm={expected[:8]} rtl={sram_bytes[:8]}",
                    )
                    return
        if expect_final_active_contexts is not None and active_context_count != expect_final_active_contexts:
            self.record(
                scenario_id,
                rtl_obs,
                False,
                f"final active_context_count rtl={active_context_count} expected={expect_final_active_contexts}",
            )
            return
        self.record(scenario_id, rtl_obs, True)

    def check_scenario(
        self,
        scenario_id: str,
        *,
        desc_status: int,
        desc_words: tuple[int, int, int, int] | None,
        packet_drop_count: int,
        assembly_drop_count: int,
        error_status: int = 0,
        active_context_count: int | None = None,
        sram_bytes: list[int] | None,
        expect_descriptor: bool,
        expect_packet_drop: bool,
        expect_assembly_drop: bool,
        expect_active_contexts: int | None = None,
    ) -> None:
        desc_count = desc_status & 0xF
        fm_desc = len(self.fm.descriptor_fifo)
        fm_pkt = self.fm.counters["packet_drop_count"]
        fm_asm = self.fm.counters["assembly_drop_count"]

        rtl_obs = {
            "desc_count": desc_count,
            "packet_drop_count": packet_drop_count,
            "assembly_drop_count": assembly_drop_count,
            "error_status": error_status,
            "active_context_count": active_context_count,
            "desc_words": desc_words,
            "sram_bytes": sram_bytes,
        }

        if expect_descriptor:
            if desc_count == 0 or fm_desc == 0:
                self.record(scenario_id, rtl_obs, False, "expected descriptor but fifo empty")
                return
            fm_desc_obj = self.fm.descriptor_fifo[0]
            parsed = parse_descriptor_words(*desc_words) if desc_words else {}
            if parsed.get("payload_byte_count") != fm_desc_obj.payload_byte_count:
                self.record(
                    scenario_id,
                    rtl_obs,
                    False,
                    f"payload_byte_count fm={fm_desc_obj.payload_byte_count} rtl={parsed.get('payload_byte_count')}",
                )
                return
            if sram_bytes is not None:
                expected = []
                for wr in self.fm.sram_writes:
                    expected.extend(wr["bytes"])
                expected = expected[: fm_desc_obj.payload_byte_count]
                if sram_bytes[: len(expected)] != expected:
                    self.record(
                        scenario_id,
                        rtl_obs,
                        False,
                        f"sram payload mismatch fm={expected[:8]} rtl={sram_bytes[:8]}",
                    )
                    return
            self.record(scenario_id, rtl_obs, True)
            return

        if expect_packet_drop:
            passed = desc_count == 0 and fm_pkt >= 1 and (
                packet_drop_count >= 1 or bool(rtl_obs.get("error_status"))
            )
            if passed and expect_active_contexts is not None:
                passed = active_context_count == expect_active_contexts
            mismatch = ""
            if not passed:
                mismatch = (
                    f"packet drop mismatch rtl={packet_drop_count} fm={fm_pkt} desc={desc_count}"
                )
                if expect_active_contexts is not None and active_context_count != expect_active_contexts:
                    mismatch += (
                        f"; active_context_count rtl={active_context_count} "
                        f"expected={expect_active_contexts}"
                    )
            self.record(
                scenario_id,
                {**rtl_obs, "error_status": rtl_obs.get("error_status", 0)},
                passed,
                mismatch,
            )
            return

        if expect_assembly_drop:
            passed = assembly_drop_count >= 1 and fm_asm >= 1 and desc_count == 0
            self.record(
                scenario_id,
                rtl_obs,
                passed,
                "" if passed else f"assembly drop mismatch rtl={assembly_drop_count} fm={fm_asm} desc={desc_count}",
            )
            return

        self.record(scenario_id, rtl_obs, True)

    def write_events(self) -> None:
        return

    def final_check(self) -> None:
        self.write_events()
        if self.failures:
            preview = "; ".join(self.failures[:8])
            suffix = "" if len(self.failures) <= 8 else f"; ... +{len(self.failures) - 8} more"
            raise AssertionError(f"{len(self.failures)} scoreboard mismatch(es): {preview}{suffix}")
