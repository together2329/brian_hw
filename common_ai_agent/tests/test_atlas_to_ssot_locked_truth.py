from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from src.atlas_slash_handlers import make_slash_handlers


class _FakeClientSession:
    def __init__(self) -> None:
        self.events: list[tuple[str, dict]] = []

    def emit(self, event: str, **payload) -> None:
        self.events.append((event, payload))


def test_to_ssot_uses_locked_truth_bundle_instead_of_missing_legacy_slots(tmp_path: Path):
    ip = "timer_v11"
    project_root = tmp_path
    workflow_root = tmp_path / "workflow"
    source_root = ROOT
    req_dir = project_root / ip / "req"
    req_dir.mkdir(parents=True)
    (req_dir / "approval_manifest.json").write_text(
        json.dumps({"status": "requirements_locked", "bundle_sha256": "abc123"}),
        encoding="utf-8",
    )
    for name, payload in {
        "requirements_index.json": {"requirements": []},
        "obligations.json": {"obligations": []},
        "contract_refs.json": {"contract_refs": []},
        "evidence_plan.json": {"evidence_plan": []},
    }.items():
        (req_dir / name).write_text(json.dumps(payload), encoding="utf-8")
    (req_dir / "locked_truth.md").write_text("# locked truth\n", encoding="utf-8")

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

    queued_text = "\n".join(queued)
    assert "Source-of-truth inputs (READ these first):" in queued_text
    assert "`timer_v11/req/approval_manifest.json`" in queued_text
    assert "Derive missing SSOT Preview fields from locked requirements" in queued_text
    assert "locked req/ wins on conflicts" in queued_text
