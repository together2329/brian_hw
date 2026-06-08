from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from src.atlas_slash_handlers import make_slash_handlers


LOCK_SCRIPT = ROOT / "workflow" / "req-gen" / "scripts" / "lock_requirement_set.py"


class _FakeClientSession:
    def __init__(self, session_id: str = "") -> None:
        self.session_id = session_id
        self.events: list[tuple[str, dict]] = []

    def emit(self, event: str, **payload) -> None:
        self.events.append((event, payload))


def _write_locked_contract_bundle(root: Path, ip: str) -> None:
    root.mkdir(parents=True, exist_ok=True)
    draft = {
        "ip": ip,
        "requirements": [
            {
                "requirement_id": "REQ_001",
                "title": "Timer control interface",
                "statement": "The timer shall expose a clocked control interface.",
                "required": True,
                "obligation_refs": ["OBL_001"],
            }
        ],
        "obligations": [
            {
                "obligation_id": "OBL_001",
                "requirement_refs": ["REQ_001"],
                "statement": "The control interface shall accept a valid command and produce ready.",
                "contract_refs": ["CR_CTRL"],
                "structural_contract_refs": ["SC_CTRL_IO"],
                "behavioral_contract_refs": ["BC_CTRL_READY"],
            }
        ],
        "contract_refs": [
            {
                "contract_ref_id": "CR_CTRL",
                "title": "Control interface contract",
                "obligation_refs": ["OBL_001"],
                "stage_contracts": [{"stage": "ssot", "check": "project control contract into Design Spec"}],
            }
        ],
        "structural_contracts": [
            {
                "id": "SC_CTRL_IO",
                "obligations": ["OBL_001"],
                "clock_domains": [{"id": "main_clk", "clock_signal": "clk"}],
                "reset_domains": [{"id": "main_rst", "reset_signal": "rst_n", "clock_domain": "main_clk"}],
                "interfaces": [{"id": "ctrl", "signals": ["valid", "ready"], "clock_domain": "main_clk"}],
                "signals": [
                    {"name": "clk", "dir": "input", "width": 1, "timing": {"kind": "clock"}},
                    {"name": "rst_n", "dir": "input", "width": 1, "timing": {"kind": "reset"}},
                    {"name": "valid", "dir": "input", "width": 1, "timing": {"kind": "sync", "clock_domain": "main_clk"}},
                    {"name": "ready", "dir": "output", "width": 1, "timing": {"kind": "sync", "clock_domain": "main_clk"}},
                ],
            }
        ],
        "behavioral_contracts": [
            {
                "id": "BC_CTRL_READY",
                "obligations": ["OBL_001"],
                "decision_table": [
                    {
                        "when": "valid == 1",
                        "then": {"ready": 1},
                        "latency": {"min_cycles": 0, "max_cycles": 1},
                    }
                ],
                "cycle": {"clock": "clk", "reset": "rst_n", "latency": {"valid_to_ready_cycles": "0..1"}},
                "stage_contracts": [
                    {"stage": "ssot", "check": "function_model transaction mirrors decision_table"},
                    {"stage": "cycle_model", "check": "cycle_model latency mirrors contract cycle latency"},
                    {"stage": "sim", "validator": "check_evidence_contract.py"},
                ],
            }
        ],
        "evidence_plan": [
            {
                "evidence_id": "EV_CR_CTRL",
                "contract_ref": "CR_CTRL",
                "artifact": "yaml/<ip>.ssot.yaml",
                "validator": "check_design_spec_trace.py",
                "pass_condition": "Design Spec projects CR_CTRL",
            },
            {
                "evidence_id": "EV_SC_CTRL",
                "contract_ref": "SC_CTRL_IO",
                "artifact": "rtl/rtl_todo_plan.json",
                "validator": "derive_rtl_todos.py --audit-rtl",
                "pass_condition": "top IO direction/width/timing matches SC_CTRL_IO",
            },
            {
                "evidence_id": "EV_BC_READY",
                "contract_ref": "BC_CTRL_READY",
                "artifact": "sim/scoreboard_events.jsonl",
                "validator": "check_evidence_contract.py",
                "pass_condition": "ready rows match BC_CTRL_READY decision table",
            },
        ],
    }
    draft_path = root / f"{ip}_draft.json"
    draft_path.write_text(json.dumps(draft), encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            str(LOCK_SCRIPT),
            ip,
            "--root",
            str(root),
            "--draft",
            str(draft_path),
            "--approved-by",
            "brian",
        ],
        check=False,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr


def test_to_ssot_uses_locked_truth_bundle_instead_of_missing_legacy_slots(tmp_path: Path):
    ip = "timer_v11"
    project_root = tmp_path
    workflow_root = tmp_path / "workflow"
    source_root = ROOT
    _write_locked_contract_bundle(project_root, ip)

    messages: list[tuple[str, str, str]] = []
    workflow_results: list[tuple[str, str]] = []
    queued: list[str] = []
    active_history: list[tuple[str, str]] = []

    def append_session_message(session: str, role: str, text: str) -> None:
        messages.append((session, role, text))

    def append_workflow_history(workflow: str, role: str, text: str) -> None:
        messages.append((workflow, role, text))

    def queue_prompt(_client: _FakeClientSession, prompt: str) -> None:
        queued.append(prompt)

    handlers = make_slash_handlers(
        PROJECT_ROOT=project_root,
        SOURCE_ROOT=source_root,
        WORKFLOW_ROOT=workflow_root,
        _SSOT_IMPORT_EXTENSIONS={".md", ".json", ".yaml", ".yml", ".sv", ".v"},
        _STAGE_RUNNERS={},
        _active_ssot_ip=ip,
        _append_active_history=lambda role, text: active_history.append((role, text)),
        _append_session_message=append_session_message,
        _append_workflow_history=append_workflow_history,
        _atlas_active_session_cv=None,
        _canonical_session_string=lambda name: f"{name}/default",
        _cmd_refresh_wiki=None,
        _collect_import_files=lambda _ip, _paths: ([], []),
        _command_ip=lambda _args, client_session=None: ip,
        _emit_ssot_approval_ready=lambda _ip, _state: None,
        _emit_workflow_result=lambda msg, tool: workflow_results.append((tool, msg)),
        _ensure_new_ip_structure=lambda _ip, kind=None: None,
        _ensure_ssot_draft=lambda _ip, kind=None: None,
        _extract_import_candidates=lambda files: [],
        _generated=[],
        _graph={},
        _ip_root=lambda name: project_root / name,
        _load_ssot_state=lambda _ip: {},
        _merge_import_candidates=lambda state, candidates: (state, []),
        _missing_ssot_decisions=lambda _ip, _state: [
            "purpose",
            "bus_interface",
            "register_map",
            "clock_reset",
            "interrupt",
        ],
        _new_ip_initial_workflow="default",
        _new_ssot_state=lambda _ip: {"kind": "draft"},
        _parse_import_args=lambda args: (ip, [], None),
        _parse_new_ip_args=lambda args: (ip, "kind", None),
        _python_cmd=lambda: "python3",
        _queue_prompt_for_session=queue_prompt,
        _refresh_ip_wiki_pages=None,
        _relative_project_path=lambda path: Path(path).resolve().relative_to(project_root.resolve()).as_posix(),
        _render_approved_ssot_spec=lambda _ip, _state: "[WEB TO SSOT SPEC] locked truth spec",
        _render_new_ip_plan=lambda _ip, _kind: "",
        _render_ssot_llm_qna_prompt=lambda _ip, _state, _missing: "",
        _run_command=lambda *args, **kwargs: "",
        _save_ssot_state=lambda _ip, _state: None,
        _script_project_root=lambda _ip: project_root,
        _set_active_ssot_ip=lambda _ip: None,
        _split_slash=lambda text: (text.strip().split()[0].lstrip("/"), text.strip().split()[1:]),
        _ssot_session_for_ip=lambda _ip: f"{_ip}/ssot-gen",
        _ssot_yaml_path=lambda _ip: f"{_ip}/yaml/{_ip}.ssot.yaml",
        _start_sim_human_gate_qna=lambda _ip, _session: None,
        _valid_ip_name=lambda name: bool(name),
    )

    client = _FakeClientSession()
    assert handlers["_handle_to_ssot_gate"]("/to-ssot", client) is True

    result_text = "\n".join(msg for _tool, msg in workflow_results)
    assert "blocked: timer_v11 still has missing SSOT decisions" not in result_text
    assert "[to-ssot] timer_v11 — queueing LLM SSOT write." in result_text
    assert "`timer_v11/req/requirements_index.json`" in result_text
    assert "`timer_v11/req/obligations.json`" in result_text
    assert "`timer_v11/req/structural_contracts.json`" in result_text
    assert "`timer_v11/req/behavioral_contracts.json`" in result_text

    queued_text = "\n".join(queued)
    assert "Source-of-truth inputs (READ these first):" in queued_text
    assert "`timer_v11/req/approval_manifest.json`" in queued_text
    assert "`timer_v11/req/structural_contracts.json`" in queued_text
    assert "`timer_v11/req/behavioral_contracts.json`" in queued_text
    assert "Derive missing SSOT Preview fields from locked requirements" in queued_text
    assert "locked req/ wins on conflicts" in queued_text


def test_to_ssot_uses_session_scoped_locked_truth_bundle(tmp_path: Path):
    ip = "timer_v12"
    atlas_root = tmp_path / "atlas"
    workspace_root = atlas_root / "brian" / "brian_session"
    workflow_root = tmp_path / "workflow"
    source_root = ROOT
    _write_locked_contract_bundle(workspace_root, ip)

    messages: list[tuple[str, str, str]] = []
    workflow_results: list[tuple[str, str]] = []
    queued: list[str] = []
    active_history: list[tuple[str, str]] = []

    def append_session_message(session: str, role: str, text: str) -> None:
        messages.append((session, role, text))

    def append_workflow_history(workflow: str, role: str, text: str) -> None:
        messages.append((workflow, role, text))

    def queue_prompt(_client: _FakeClientSession, prompt: str) -> None:
        queued.append(prompt)

    def relative_project_path(path: Path) -> str:
        return Path(path).resolve().relative_to(atlas_root.resolve()).as_posix()

    def ip_root_for_session(name: str, client_session: _FakeClientSession | None = None) -> Path:
        if getattr(client_session, "session_id", "") == "brian/brian_session/timer_v12/default":
            return workspace_root / name
        return atlas_root / name

    handlers = make_slash_handlers(
        PROJECT_ROOT=atlas_root,
        SOURCE_ROOT=source_root,
        WORKFLOW_ROOT=workflow_root,
        _SSOT_IMPORT_EXTENSIONS={".md", ".json", ".yaml", ".yml", ".sv", ".v"},
        _STAGE_RUNNERS={},
        _active_ssot_ip=ip,
        _append_active_history=lambda role, text: active_history.append((role, text)),
        _append_session_message=append_session_message,
        _append_workflow_history=append_workflow_history,
        _atlas_active_session_cv=None,
        _canonical_session_string=lambda name: f"{name}/default",
        _cmd_refresh_wiki=None,
        _collect_import_files=lambda _ip, _paths: ([], []),
        _command_ip=lambda _args, client_session=None: ip,
        _emit_ssot_approval_ready=lambda _ip, _state: None,
        _emit_workflow_result=lambda msg, tool: workflow_results.append((tool, msg)),
        _ensure_new_ip_structure=lambda _ip, kind=None: None,
        _ensure_ssot_draft=lambda _ip, kind=None: None,
        _extract_import_candidates=lambda files: [],
        _generated=[],
        _graph={},
        _ip_root=lambda name: atlas_root / name,
        _ip_root_for_session=ip_root_for_session,
        _load_ssot_state=lambda _ip: {},
        _merge_import_candidates=lambda state, candidates: (state, []),
        _missing_ssot_decisions=lambda _ip, _state: [
            "purpose",
            "bus_interface",
            "register_map",
            "clock_reset",
            "interrupt",
            "memory_map",
            "parameters",
            "submodule_structure",
            "test_expectation",
        ],
        _new_ip_initial_workflow="default",
        _new_ssot_state=lambda _ip: {"kind": "draft"},
        _parse_import_args=lambda args: (ip, [], None),
        _parse_new_ip_args=lambda args: (ip, "kind", None),
        _python_cmd=lambda: "python3",
        _queue_prompt_for_session=queue_prompt,
        _refresh_ip_wiki_pages=None,
        _relative_project_path=relative_project_path,
        _render_approved_ssot_spec=lambda _ip, _state: "[WEB TO SSOT SPEC] locked truth spec",
        _render_new_ip_plan=lambda _ip, _kind: "",
        _render_ssot_llm_qna_prompt=lambda _ip, _state, _missing: "",
        _run_command=lambda *args, **kwargs: "",
        _save_ssot_state=lambda _ip, _state: None,
        _script_project_root=lambda _ip: atlas_root,
        _script_project_root_for_session=lambda _ip, client_session=None: workspace_root,
        _set_active_ssot_ip=lambda _ip: None,
        _split_slash=lambda text: (text.strip().split()[0].lstrip("/"), text.strip().split()[1:]),
        _ssot_session_for_ip=lambda _ip: f"{_ip}/ssot-gen",
        _ssot_yaml_path=lambda _ip: atlas_root / _ip / "yaml" / f"{_ip}.ssot.yaml",
        _ssot_yaml_path_for_session=lambda _ip, client_session=None: ip_root_for_session(_ip, client_session) / "yaml" / f"{_ip}.ssot.yaml",
        _start_sim_human_gate_qna=lambda _ip, _session: None,
        _valid_ip_name=lambda name: bool(name),
    )

    client = _FakeClientSession(session_id="brian/brian_session/timer_v12/default")
    assert handlers["_handle_to_ssot_gate"]("/to-ssot", client) is True

    result_text = "\n".join(msg for _tool, msg in workflow_results)
    assert "blocked: timer_v12 still has missing SSOT decisions" not in result_text
    assert "[to-ssot] timer_v12 - queueing LLM SSOT write." not in result_text
    assert "[to-ssot] timer_v12" in result_text
    assert "queueing LLM SSOT write" in result_text
    assert "`brian/brian_session/timer_v12/req/requirements_index.json`" in result_text
    assert "`brian/brian_session/timer_v12/req/structural_contracts.json`" in result_text
    assert "`brian/brian_session/timer_v12/req/behavioral_contracts.json`" in result_text
    assert "`brian/brian_session/timer_v12/req/approval_manifest.json`" in result_text

    queued_text = "\n".join(queued)
    assert f"PROJECT_ROOT: `{workspace_root}`" in queued_text
    assert f"IP_ROOT:      `{workspace_root / ip}`" in queued_text
    assert f"Write the canonical SSOT YAML for IP `{ip}`" in queued_text
    assert str(workspace_root / ip / "yaml" / f"{ip}.ssot.yaml") in queued_text
    assert "`timer_v12/req/structural_contracts.json`" in queued_text
    assert "`timer_v12/req/behavioral_contracts.json`" in queued_text
    assert "Derive missing SSOT Preview fields from locked requirements" in queued_text


def test_ssot_stage_commands_use_session_scoped_ssot_path(tmp_path: Path):
    ip = "timer_v12"
    atlas_root = tmp_path / "atlas"
    workspace_root = atlas_root / "brian" / "brian_session"
    workflow_root = tmp_path / "workflow"
    source_root = ROOT
    ip_dir = workspace_root / ip
    ssot_path = ip_dir / "yaml" / f"{ip}.ssot.yaml"
    ssot_path.parent.mkdir(parents=True)
    ssot_path.write_text("top_module:\n  name: timer_v12\n", encoding="utf-8")

    rtl_script = workflow_root / "rtl-gen" / "scripts" / "ssot_to_rtl.py"
    fl_script = workflow_root / "fl-model-gen" / "scripts" / "emit_fl_model.py"
    for script, label in ((rtl_script, "rtl"), (fl_script, "fl")):
        script.parent.mkdir(parents=True, exist_ok=True)
        script.write_text(
            "import argparse\n"
            "parser = argparse.ArgumentParser()\n"
            "parser.add_argument('ip')\n"
            "parser.add_argument('--root', required=True)\n"
            "args = parser.parse_args()\n"
            f"print('{label} root=' + args.root)\n",
            encoding="utf-8",
        )

    messages: list[tuple[str, str, str]] = []
    workflow_results: list[tuple[str, str]] = []
    queued: list[str] = []
    active_history: list[tuple[str, str]] = []

    def append_session_message(session: str, role: str, text: str) -> None:
        messages.append((session, role, text))

    def append_workflow_history(workflow: str, role: str, text: str) -> None:
        messages.append((workflow, role, text))

    def ip_root_for_session(name: str, client_session: _FakeClientSession | None = None) -> Path:
        if getattr(client_session, "session_id", "") == "brian/brian_session/timer_v12/default":
            return workspace_root / name
        return atlas_root / name

    handlers = make_slash_handlers(
        PROJECT_ROOT=atlas_root,
        SOURCE_ROOT=source_root,
        WORKFLOW_ROOT=workflow_root,
        _SSOT_IMPORT_EXTENSIONS={".md", ".json", ".yaml", ".yml", ".sv", ".v"},
        _STAGE_RUNNERS={
            "ssot-fl-model": {"workflow": "fl-model-gen", "template": "ssot-fl-model", "artifact_hint": "model/functional_model.py"},
            "ssot-rtl": {"workflow": "rtl-gen", "template": "ssot-rtl", "artifact_hint": "rtl/<ip>.sv"},
        },
        _active_ssot_ip=ip,
        _append_active_history=lambda role, text: active_history.append((role, text)),
        _append_session_message=append_session_message,
        _append_workflow_history=append_workflow_history,
        _atlas_active_session_cv=None,
        _canonical_session_string=lambda name: f"{name}/default",
        _cmd_refresh_wiki=None,
        _collect_import_files=lambda _ip, _paths: ([], []),
        _command_ip=lambda _args, client_session=None: ip,
        _emit_ssot_approval_ready=lambda _ip, _state: None,
        _emit_workflow_result=lambda msg, tool: workflow_results.append((tool, msg)),
        _ensure_new_ip_structure=lambda _ip, kind=None: None,
        _ensure_ssot_draft=lambda _ip, kind=None: None,
        _extract_import_candidates=lambda files: [],
        _generated=[],
        _graph={},
        _ip_root=lambda name: atlas_root / name,
        _ip_root_for_session=ip_root_for_session,
        _load_ssot_state=lambda _ip: {},
        _merge_import_candidates=lambda state, candidates: (state, []),
        _missing_ssot_decisions=lambda _ip, _state: [],
        _new_ip_initial_workflow="default",
        _new_ssot_state=lambda _ip: {"kind": "draft"},
        _parse_import_args=lambda args: (ip, [], None),
        _parse_new_ip_args=lambda args: (ip, "kind", None),
        _python_cmd=lambda: sys.executable,
        _queue_prompt_for_session=lambda _client, prompt: queued.append(prompt),
        _refresh_ip_wiki_pages=None,
        _relative_project_path=lambda path: Path(path).resolve().relative_to(atlas_root.resolve()).as_posix(),
        _render_approved_ssot_spec=lambda _ip, _state: "",
        _render_new_ip_plan=lambda _ip, _kind: "",
        _render_ssot_llm_qna_prompt=lambda _ip, _state, _missing: "",
        _run_command=lambda *args, **kwargs: "",
        _save_ssot_state=lambda _ip, _state: None,
        _script_project_root=lambda _ip: atlas_root,
        _script_project_root_for_session=lambda _ip, client_session=None: workspace_root,
        _set_active_ssot_ip=lambda _ip: None,
        _split_slash=lambda text: (text.strip().split()[0].lstrip("/"), text.strip().split()[1:]),
        _ssot_session_for_ip=lambda _ip: f"{_ip}/ssot-gen",
        _ssot_yaml_path=lambda _ip: atlas_root / _ip / "yaml" / f"{_ip}.ssot.yaml",
        _ssot_yaml_path_for_session=lambda _ip, client_session=None: ip_root_for_session(_ip, client_session) / "yaml" / f"{_ip}.ssot.yaml",
        _start_sim_human_gate_qna=lambda _ip, _session, **_kwargs: None,
        _valid_ip_name=lambda name: bool(name),
    )

    client = _FakeClientSession(session_id="brian/brian_session/timer_v12/default")
    assert handlers["_run_stage_command"]("/ssot-fl-model", client) is True
    assert handlers["_run_stage_command"]("/ssot-rtl", client) is True
    assert handlers["_run_stage_command"]("/gen-rtl", client) is True

    result_text = "\n".join(msg for _tool, msg in workflow_results)
    assert "SSOT not found at timer_v12/yaml/timer_v12.ssot.yaml" not in result_text
    assert "SSOT not found" not in result_text
    assert "timer_v12" in result_text
