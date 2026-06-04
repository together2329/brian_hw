from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
TB_PATH = REPO / "mctp_assembler_v3" / "tb" / "cocotb" / "test_mctp_datapath.py"
RUNNER_PATH = REPO / "mctp_assembler_v3" / "tb" / "cocotb" / "test_runner.py"
STIMULUS_PATH = REPO / "mctp_assembler_v3" / "tb" / "cocotb" / "mctp_stimulus.py"
TOP_RTL_PATH = REPO / "mctp_assembler_v3" / "rtl" / "mctp_assembler_v3.sv"


def _install_cocotb_stubs() -> None:
    cocotb = types.ModuleType("cocotb")
    clock = types.ModuleType("cocotb.clock")
    triggers = types.ModuleType("cocotb.triggers")

    def test_decorator():
        def decorate(function):
            return function

        return decorate

    class Clock:
        def __init__(self, *args, **kwargs):
            pass

        def start(self):
            return None

    async def clock_cycles(*args, **kwargs):
        return None

    async def with_timeout(awaitable, *args, **kwargs):
        return await awaitable

    setattr(cocotb, "test", test_decorator)
    setattr(cocotb, "start_soon", lambda awaitable: None)
    setattr(clock, "Clock", Clock)
    setattr(triggers, "ClockCycles", clock_cycles)
    setattr(triggers, "with_timeout", with_timeout)
    sys.modules["cocotb"] = cocotb
    sys.modules["cocotb.clock"] = clock
    sys.modules["cocotb.triggers"] = triggers


def _install_tb_dependency_stubs() -> None:
    scoreboard = types.ModuleType("equivalence_scoreboard")
    stimulus = types.ModuleType("mctp_stimulus")

    class EquivalenceScoreboard:
        pass

    class Packet:
        pass

    setattr(scoreboard, "EquivalenceScoreboard", EquivalenceScoreboard)
    setattr(stimulus, "Packet", Packet)
    sys.modules["equivalence_scoreboard"] = scoreboard
    sys.modules["mctp_stimulus"] = stimulus


def _load_datapath_module():
    _install_cocotb_stubs()
    _install_tb_dependency_stubs()
    spec = importlib.util.spec_from_file_location("mctp_v3_datapath_test", TB_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_recorder_enriches_axi_bresp_contract_alias() -> None:
    module = _load_datapath_module()
    recorder = object.__new__(module._Recorder)

    observed = recorder._enrich(
        "EQ_SCENARIO_SC_MAX_TU",
        "SC_MAX_TU",
        {"kind": "FM_DECODE_VDM", "scenario_id": "SC_MAX_TU"},
        {"s_axi_bresp": 0, "bresp": 0},
    )

    assert observed["bresp_next"] == 0


def test_official_runner_invokes_datapath_recorder_after_generic_goals() -> None:
    text = RUNNER_PATH.read_text(encoding="utf-8")

    assert 'modules = os.environ.get("COCOTB_MODULES") or f"test_{ip},test_mctp_datapath"' in text
    assert "module=modules" in text
    assert 'check_scoreboard = "test_mctp_datapath" in' in text


def test_drop_class_monitor_reads_real_last_drop_class_observable() -> None:
    text = STIMULUS_PATH.read_text(encoding="utf-8")

    assert 'self.acc["drop_class_o"] = self._rd("last_drop_class")' in text
    assert 'self._rd("drop_class_o")' not in text


def test_top_does_not_add_drop_class_alias_sink() -> None:
    text = TOP_RTL_PATH.read_text(encoding="utf-8")

    assert "assign drop_class_o = last_drop_class;" not in text
    assert "_unused_drop_class_o" not in text


def test_pd_malformed_reason_is_not_synthesized_by_scoreboard() -> None:
    text = TB_PATH.read_text(encoding="utf-8")

    assert "real_reason or 1" not in text


def test_pd_malformed_scenario_requires_real_ingress_observable() -> None:
    text = TB_PATH.read_text(encoding="utf-8")

    assert 'omal["ingress_malformed_valid"] == 1' in text
    assert 'omal["ingress_malformed_reason"] == S.PD_MALFORMED_TLP' in text


def test_top_wires_ingress_malformed_into_status_and_monitor_observables() -> None:
    text = TOP_RTL_PATH.read_text(encoding="utf-8")

    assert "wire         ingress_malformed_valid;" in text
    assert "wire [5:0]   ingress_malformed_reason;" in text
    assert ".malformed_tlp_valid(ingress_malformed_valid)" in text
    assert ".malformed_tlp_reason(ingress_malformed_reason)" in text
    assert "assign axi_write_malformed_pulse = ingress_malformed_valid | vdm_drop_valid | mctp_drop_valid;" in text


def test_monitor_reads_ingress_malformed_observables() -> None:
    text = STIMULUS_PATH.read_text(encoding="utf-8")

    assert '"ingress_malformed_valid"' in text
    assert 'self.acc["ingress_malformed_reason"] = self._rd("ingress_malformed_reason")' in text


def _load_runner_module():
    simulator = types.ModuleType("cocotb_test.simulator")
    package = types.ModuleType("cocotb_test")

    def run(*args, **kwargs):
        raise AssertionError("runner.run should not be called by unit tests")

    setattr(simulator, "run", run)
    setattr(package, "simulator", simulator)
    sys.modules["cocotb_test"] = package
    sys.modules["cocotb_test.simulator"] = simulator
    spec = importlib.util.spec_from_file_location("mctp_v3_runner_test", RUNNER_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_runner_writes_empty_assertion_failures_for_clean_results(tmp_path: Path) -> None:
    module = _load_runner_module()
    results = tmp_path / "results.xml"
    output = tmp_path / "assertion_failures.jsonl"
    results.write_text('<testsuite tests="2" failures="0" errors="0"></testsuite>\n', encoding="utf-8")

    written = module._write_assertion_failures(results, output)

    assert written == 0
    assert output.read_text(encoding="utf-8") == ""


def test_runner_writes_assertion_failure_records_for_failed_results(tmp_path: Path) -> None:
    module = _load_runner_module()
    results = tmp_path / "results.xml"
    output = tmp_path / "assertion_failures.jsonl"
    results.write_text(
        '<testsuite tests="1" failures="1" errors="0">'
        '<testcase name="bad"><failure message="mismatch">detail</failure></testcase>'
        "</testsuite>\n",
        encoding="utf-8",
    )

    written = module._write_assertion_failures(results, output)

    rows = [line for line in output.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert written == 1
    assert len(rows) == 1
    assert '"testcase": "bad"' in rows[0]
    assert '"kind": "failure"' in rows[0]


def test_runner_treats_failed_scoreboard_row_as_assertion_failure(tmp_path: Path) -> None:
    module = _load_runner_module()
    results = tmp_path / "results.xml"
    scoreboard = tmp_path / "scoreboard_events.jsonl"
    output = tmp_path / "assertion_failures.jsonl"
    results.write_text('<testsuite tests="1" failures="0" errors="0"></testsuite>\n', encoding="utf-8")
    scoreboard.write_text(
        '{"goal_id":"EQ_BAD","passed":false,"mismatch":"rtl mismatch"}\n',
        encoding="utf-8",
    )

    written = module._write_assertion_failures(results, output, scoreboard)

    rows = [line for line in output.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert written == 1
    assert len(rows) == 1
    assert '"kind": "scoreboard"' in rows[0]
    assert '"testcase": "EQ_BAD"' in rows[0]
    assert module._sim_exit_code(1, 0, 0, written) == 1
