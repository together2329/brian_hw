"""Slash command handlers — extracted from src/atlas_ui.py.

Phase 12 of refactor/atlas-modular: largest closure cluster (14 handlers,
~1850 lines). Factory `make_slash_handlers(**deps)` wraps them with 45
explicit kwargs mirroring the original closure-captured names so the
handler bodies need zero textual modification.

atlas_ui aliases each returned handler back to its original name so the
prompt-dispatch chain in the WebSocket loop keeps calling them unchanged.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple


def make_slash_handlers(
    *,
    PROJECT_ROOT,
    SOURCE_ROOT,
    WORKFLOW_ROOT,
    _SSOT_IMPORT_EXTENSIONS,
    _STAGE_RUNNERS,
    _active_ssot_ip,
    _append_active_history,
    _append_session_message,
    _append_workflow_history,
    _atlas_active_session_cv,
    _canonical_session_string,
    _cmd_refresh_wiki,
    _collect_import_files,
    _command_ip,
    _emit_ssot_approval_ready,
    _emit_workflow_result,
    _ensure_new_ip_structure,
    _ensure_ssot_draft,
    _extract_import_candidates,
    _generated,
    _graph,
    _ip_root,
    _ip_root_for_session=None,
    _load_ssot_state,
    _merge_import_candidates,
    _missing_ssot_decisions,
    _new_ip_initial_workflow,
    _new_ssot_state,
    _parse_import_args,
    _parse_new_ip_args,
    _python_cmd,
    _queue_prompt_for_session,
    _refresh_ip_wiki_pages,
    _relative_project_path,
    _render_approved_ssot_spec,
    _render_new_ip_plan,
    _render_ssot_llm_qna_prompt,
    _run_command,
    _save_ssot_state,
    _script_project_root,
    _script_project_root_for_session=None,
    _set_active_ssot_ip,
    _split_slash,
    _ssot_session_for_ip,
    _ssot_yaml_path,
    _ssot_yaml_path_for_session=None,
    _start_sim_human_gate_qna,
    _valid_ip_name,
) -> Dict[str, Callable]:
    """Build the 14 slash-command handlers. Kwarg names mirror the
    original closure-captured names — bodies use them directly as if
    they were the original closures."""

    def _handle_bang_shell_command(text: str, client_session: Any) -> bool:
        raw = str(text or "").strip()
        if not raw.startswith("!"):
            return False
        command = raw[1:].strip()
        if not command:
            output = "Usage: !<shell command>"
        else:
            try:
                from core.tools import run_command as _run_command
            except Exception:
                from tools import run_command as _run_command  # type: ignore
            result = str(_run_command(command, timeout=60) or "")
            output = f"$ {command}\n{result}".rstrip()
        client_session.emit("tool_result", text=output, tool="run_command", truncated=False)
        client_session.emit("agent_state", running=False)
        client_session.emit("flush")
        return True

    def _handle_import_command(text: str, client_session: Any | None = None) -> bool:
        cmd, args = _split_slash(text)
        if cmd not in ("import", "imp"):
            return False

        ip, raw_paths, err = _parse_import_args(args)
        if err:
            _emit_workflow_result(err, "import")
            return True
        _set_active_ssot_ip(ip)
        ip_dir = _ip_root(ip)
        try:
            ip_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            _emit_workflow_result(f"[SSOT IMPORT] failed to scaffold {ip}: {exc}", "import")
            return True

        state = _load_ssot_state(ip) or _new_ssot_state(ip)
        kind = str(state.get("kind") or "imported IP evidence")
        _ensure_ssot_draft(ip, kind)
        files, errors = _collect_import_files(ip, raw_paths)
        if not files:
            msg = (
                f"[SSOT IMPORT] {ip}: no importable files found\n"
                f"searched: {', '.join(raw_paths) if raw_paths else ip + '/'}\n"
                "usage: /import [path ...]  or  /import --ip <ip_name> [path ...]"
            )
            if errors:
                msg += "\n\nnotes:\n" + "\n".join(f"- {e}" for e in errors[:8])
            _append_session_message(_canonical_session_string(ip), "user", text)
            _append_session_message(_canonical_session_string(ip), "assistant", msg)
            _append_workflow_history("ssot-gen", "user", text)
            _append_workflow_history("ssot-gen", "assistant", msg)
            _append_active_history("user", text)
            _append_active_history("assistant", "```\n" + msg + "\n```")
            _emit_workflow_result(msg, "import")
            _emit_ssot_approval_ready(ip, state)
            return True

        artifacts, candidates, sources = _extract_import_candidates(ip, files)
        filled, conflicts = _merge_import_candidates(ip, kind, state, artifacts, candidates, sources)
        state.setdefault("ip", ip)
        state.setdefault("kind", kind)
        state["active_session"] = _ssot_session_for_ip(ip)
        state["last_step"] = "import"
        state["status"] = "answered" if not _missing_ssot_decisions(ip, state) else "planned"
        _save_ssot_state(ip, state)
        missing = _missing_ssot_decisions(ip, state)
        next_action = "/grill-me" if conflicts or missing else "/to-ssot"

        lines = [
            f"[SSOT IMPORT] {ip}",
            f"imported files: {len(files)}",
            f"manifest: {ip}/req/import_manifest.json",
            f"extracted decisions: {ip}/req/extracted_decisions.json",
            f"evidence wiki: {ip}/wiki/import-evidence.md",
            f"filled decisions: {', '.join(filled) if filled else '(none)'}",
            f"missing decisions: {', '.join(missing) if missing else '(none)'}",
            f"conflicts: {len(conflicts)}",
            f"next: {next_action} {ip}",
        ]
        if errors:
            lines += ["", "notes:"]
            lines.extend(f"- {e}" for e in errors[:8])
        lines += [
            "",
            "evidence:",
        ]
        artifact_paths_list = [str(a.get("path") or "") for a in artifacts if str(a.get("path") or "")]
        lines.extend(f"- {p}" for p in artifact_paths_list[:12])
        if len(artifact_paths_list) > 12:
            lines.append(f"- ... {len(artifact_paths_list) - 12} more")
        msg = "\n".join(lines)
        _append_session_message(_canonical_session_string(ip), "user", text)
        _append_session_message(_canonical_session_string(ip), "assistant", msg)
        _append_workflow_history("ssot-gen", "user", text)
        _append_workflow_history("ssot-gen", "assistant", msg)
        _append_active_history("user", text)
        _append_active_history("assistant", "```\n" + msg + "\n```")
        _emit_workflow_result(msg, "import")
        _emit_ssot_approval_ready(ip, state, missing)
        return True

    def _handle_grill_me_command(text: str, client_session: Any | None = None) -> bool:
        cmd, args = _split_slash(text)
        if cmd not in ("grill-me", "grill", "g"):
            return False
        # First arg, if it parses as a valid IP name, is the explicit
        # IP target. Anything else (e.g. "Q&A", "memory_map") is treated
        # as a topic hint and the active IP is used instead. Previously
        # we hard-rejected with "invalid IP name" any time the first
        # token failed _valid_ip_name, which made `/grill-me Q&A` blow
        # up even though the user clearly meant the active IP.
        ip_arg = args.split(None, 1)[0] if args else ""
        if ip_arg and not _valid_ip_name(ip_arg):
            ip_arg = ""  # fall through to _active_ssot_ip()
        ip = ip_arg or _active_ssot_ip()
        if not _valid_ip_name(ip):
            _emit_workflow_result(
                "[SSOT GRILL] no active IP found\n"
                "usage: /new-ip <ip_name> first, then /grill-me",
                "grill-me",
            )
            return True
        _set_active_ssot_ip(ip)
        try:
            _ip_root(ip).mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            _emit_workflow_result(f"[SSOT GRILL] failed to scaffold {ip}: {exc}", "grill-me")
            return True
        state = _load_ssot_state(ip) or _new_ssot_state(ip)
        _ensure_ssot_draft(ip, str(state.get("kind") or "TBD"))
        state["active_session"] = _ssot_session_for_ip(ip)
        state["last_step"] = "grill-me"
        _save_ssot_state(ip, state)
        missing = _missing_ssot_decisions(ip, state)
        msg = (
            f"[SSOT GRILL] {ip}: queued ssot-gen LLM to generate IP-specific Q&A.\n"
            f"backend baseline missing keys: {', '.join(missing) if missing else '(none)'}\n"
            "Fixed question templates are bypassed; questions must be derived from the current SSOT/imported evidence."
        )
        _append_session_message(_canonical_session_string(ip), "user", text)
        _append_session_message(_canonical_session_string(ip), "assistant", msg)
        _append_workflow_history("ssot-gen", "user", text)
        _append_workflow_history("ssot-gen", "assistant", msg)
        _append_active_history("user", text)
        _append_active_history("assistant", "```\n" + msg + "\n```")
        _emit_workflow_result(msg, "grill-me")
        _queue_prompt_for_session(client_session, "/mode normal")
        _queue_prompt_for_session(client_session, "/wf ssot-gen")
        _queue_prompt_for_session(client_session, _render_ssot_llm_qna_prompt(ip, str(state.get("kind") or "TBD"), state))
        client_session.emit("agent_state", running=True)
        return True

    def _handle_new_ip_command(text: str, client_session: Any | None = None) -> bool:
        cmd, args = _split_slash(text)
        if cmd not in ("new-ip", "ni"):
            return False
        ip, kind, import_paths, parse_err = _parse_new_ip_args(args)
        if parse_err:
            _emit_workflow_result(parse_err, "new-ip")
            return True
        if not _valid_ip_name(ip):
            _emit_workflow_result(
                "[SSOT PLAN] new IP name required\n"
                "usage: /new-ip <ip_name> [kind]\n"
                "example: /new-ip demo_i2c APB4 I2C controller\n"
                "then: /import <ip_name> or /import @path",
                "new-ip",
            )
            return True

        # Approval gate allows scaffold/session creation and draft SSOT
        # accumulation only. Production SSOT canonicalization remains
        # blocked until explicit approval.
        target = (PROJECT_ROOT / ip).resolve()
        try:
            target.relative_to(PROJECT_ROOT.resolve())
        except ValueError:
            _emit_workflow_result(f"[SSOT PLAN] invalid IP path: {ip}", "new-ip")
            return True
        if target.exists():
            _emit_workflow_result(
                f"[SSOT PLAN] IP `{ip}` already exists.\n"
                "Select it from IP_ID or use a different IP name.",
                "new-ip",
            )
            return True
        try:
            target.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            _emit_workflow_result(f"[SSOT PLAN] failed to scaffold {ip}: {e}", "new-ip")
            return True

        initial_workflow = _new_ip_initial_workflow()
        _set_active_ssot_ip(ip, initial_workflow)
        state = _new_ssot_state(ip, kind)
        _ensure_new_ip_structure(ip)
        _ensure_ssot_draft(ip, kind)
        import_notes = []
        if import_paths:
            import_notes.append(
                "/new-ip is structure-only; import markers were not scanned. "
                "Run `/import " + ip + " " + " ".join(import_paths) + "` to populate SSOT TODOs."
            )
        _save_ssot_state(ip, state)
        session = _canonical_session_string(ip, initial_workflow)
        plan = _render_new_ip_plan(ip, kind, state)
        if import_notes:
            plan += "\n\nImport:\n" + "\n".join(f"- {line}" for line in import_notes)
        _append_session_message(session, "user", text)
        _append_session_message(session, "assistant", plan)
        _append_workflow_history("ssot-gen", "user", text)
        _append_workflow_history("ssot-gen", "assistant", plan)
        _append_active_history("user", text)
        _append_active_history("assistant", "```\n" + plan + "\n```")
        _emit_workflow_result(plan, "new-ip")
        _emit_ssot_approval_ready(ip, state)
        # Tell legacy frontend surfaces to pivot to the newly-created IP
        # using the execution-mode default workflow.
        try:
            client_session.emit(
                "session_switch_request",
                ip=ip,
                workflow=initial_workflow,
                reason="new-ip",
            )
        except Exception:
            pass
        return True

    def _handle_ip_command(text: str, client_session: Any | None = None) -> bool:
        """`/ip <name>` — switch the active IP without spinning up a turn.

        Halts any running agent first (drains the inbox so queued
        workflow prompts don't auto-fire), repoints ATLAS_ACTIVE_IP
        plus the canonical session string, and emits commands_changed
        so the frontend refreshes /healthz and pivots the SSOT / QA /
        preview panels onto the new IP. No LLM call.
        """
        cmd, args = _split_slash(text)
        if cmd not in ("ip", "use"):  # `/use` retained as alias
            return False
        ip = _command_ip(args, client_session=client_session)
        if not _valid_ip_name(ip):
            _emit_workflow_result(
                "[IP] no active IP found\n"
                "Open/select an IP or run /new-ip <ip_name> first.",
                "ip",
            )
            return True
        client_session.request_stop()
        client_session.emit("agent_state", running=False)
        _set_active_ssot_ip(ip)
        msg = (
            f"[IP] active IP -> {ip}\n"
            f"session: {_canonical_session_string(ip)}"
        )
        _emit_workflow_result(msg, "ip")
        client_session.emit("commands_changed")
        return True

    def _handle_session_command(text: str, client_session: Any | None = None) -> bool:
        """`/session <id>` — switch the active session_id (owner namespace).

        Halts the agent, sets ATLAS_ACTIVE_SESSION to the canonical
        triple `<id>/<active-ip>/<active-workflow>`, and emits a refresh
        signal. The frontend's /healthz poll picks up the new owner and
        re-pivots the workspace UI without a page reload.
        """
        cmd, args = _split_slash(text)
        if cmd not in ("session",):
            return False
        sid = (args or "").strip().split()[0] if args else ""
        if not sid or not _valid_ip_name(sid):
            _emit_workflow_result(
                "[SESSION] missing or invalid session id\n"
                "usage: /session <session_id>\n"
                "example: /session brian",
                "session",
            )
            return True
        client_session.request_stop()
        client_session.emit("agent_state", running=False)
        ip = _active_ssot_ip() or "default"
        wf = os.environ.get("ATLAS_DEFAULT_WORKFLOW") or "default"
        _atlas_active_session_cv.set(f"{sid}/{ip}/{wf}")
        _emit_workflow_result(
            f"[SESSION] active session -> {sid}/{ip}/{wf}",
            "session",
        )
        client_session.emit("commands_changed")
        return True

    def _handle_approval_command(text: str, client_session: Any | None = None) -> bool:
        raw = (text or "").strip()
        low = raw.lower()
        if not (low.startswith("approve") or raw.startswith("승인")):
            return False
        parts = raw.split()
        ip = parts[1] if len(parts) > 1 and _valid_ip_name(parts[1]) else _active_ssot_ip()
        if not _valid_ip_name(ip):
            _emit_workflow_result(
                "[SSOT APPROVAL] no pending IP found\n"
                "usage: approve [<ip_name>]  or  승인 [<ip_name>]",
                "approve",
            )
            return True
        _set_active_ssot_ip(ip)
        state = _load_ssot_state(ip)
        if not state:
            state = _new_ssot_state(ip)
        _ensure_ssot_draft(ip, str(state.get("kind") or "TBD"))
        missing = _missing_ssot_decisions(ip, state)
        if missing:
            msg = (
                f"[SSOT APPROVAL] blocked: {ip} still has missing decisions\n"
                f"missing decisions: {', '.join(missing)}\n"
                "Use /import to seed existing evidence, then /grill-me to answer only the gaps."
            )
            _append_session_message(_canonical_session_string(ip), "user", text)
            _append_session_message(_canonical_session_string(ip), "assistant", msg)
            _append_workflow_history("ssot-gen", "user", text)
            _append_workflow_history("ssot-gen", "assistant", msg)
            _append_active_history("user", text)
            _append_active_history("assistant", "```\n" + msg + "\n```")
            _emit_workflow_result(msg, "approve")
            _emit_ssot_approval_ready(ip, state, missing)
            return True
        state["approved"] = True
        state["approved_at"] = time.time()
        state["status"] = "approved"
        state["active_session"] = _ssot_session_for_ip(ip)
        state["last_step"] = "approve"
        _save_ssot_state(ip, state)
        spec = _render_approved_ssot_spec(ip, state)
        msg = (
            f"[SSOT APPROVED] {ip}\n"
            f"YAML write is now allowed.\n"
            "Next: type /to-ssot in the Web UI when the summary looks correct."
        )
        session = _canonical_session_string(ip)
        _append_session_message(session, "user", text)
        _append_session_message(session, "assistant", spec)
        _append_session_message(session, "assistant", msg)
        _append_workflow_history("ssot-gen", "user", text)
        _append_workflow_history("ssot-gen", "assistant", spec)
        _append_workflow_history("ssot-gen", "assistant", msg)
        _append_active_history("user", text)
        _append_active_history("assistant", "```\n" + msg + "\n```")
        _emit_workflow_result(msg, "approve")
        _emit_ssot_approval_ready(ip, state, [])
        return True

    def _handle_refresh_wiki_command(text: str, client_session: Any | None = None) -> bool:
        """/refresh-wiki [ip] — regenerate <ip>/wiki/_generated/ for the ACTIVE IP.

        Handled here (not the generic slash registry) so the IP resolves from the
        per-session namespace via _command_ip — the registry's _cmd_refresh_wiki
        reads the process-global ATLAS_ACTIVE_IP env, which in the web server is
        "default" and produced a bogus <root>/default/wiki tree instead of the
        IP the user is actually on.
        """
        cmd, args = _split_slash(text)
        if cmd not in ("refresh-wiki", "refresh_wiki"):
            return False
        ip = _command_ip(args, client_session=client_session)
        if not _valid_ip_name(ip) or ip == "default":
            _emit_workflow_result(
                "[refresh-wiki] no active IP found\n"
                "Open/select an IP (or run /new-ip <ip_name>), or pass /refresh-wiki <ip>.",
                "refresh-wiki",
            )
            return True
        try:
            from core.tools import refresh_ip_wiki as _refresh_ip_wiki_pages
        except Exception:
            try:
                from tools import refresh_ip_wiki as _refresh_ip_wiki_pages  # type: ignore
            except Exception as exc:
                _emit_workflow_result(f"[refresh-wiki] unavailable: {exc}", "refresh-wiki")
                return True
        try:
            result = _refresh_ip_wiki_pages(ip, str(PROJECT_ROOT))
        except Exception as exc:
            _emit_workflow_result(f"[refresh-wiki] failed for {ip}: {exc}", "refresh-wiki")
            return True
        _emit_workflow_result(str(result), "refresh-wiki")
        return True

    def _handle_to_ssot_gate(text: str, client_session: Any | None = None) -> bool:
        cmd, args = _split_slash(text)
        if cmd not in ("to-ssot", "ssot", "ts"):
            return False
        ip = _command_ip(args, client_session=client_session)
        if not _valid_ip_name(ip):
            _emit_workflow_result(
                "[SSOT GATE] no active IP found\n"
                "Open/select an IP or run /new-ip <ip_name> first.",
                "to-ssot",
            )
            return True
        _set_active_ssot_ip(ip)
        if _ip_root_for_session is not None:
            ip_dir = _ip_root_for_session(ip, client_session)
        else:
            ip_dir = _ip_root(ip)
        state = _load_ssot_state(ip) or {}
        session = _canonical_session_string(ip)
        manifest_path = ip_dir / "req" / "import_manifest.json"
        extracted_path = ip_dir / "req" / "extracted_decisions.json"
        evidence_path = ip_dir / "wiki" / "import-evidence.md"
        imports_dir = ip_dir / "req" / "imports"

        def _emit_to_ssot_blocked(msg: str) -> bool:
            _append_session_message(session, "user", text)
            _append_session_message(session, "assistant", msg)
            _append_workflow_history("ssot-gen", "user", text)
            _append_workflow_history("ssot-gen", "assistant", msg)
            _append_active_history("user", text)
            _append_active_history("assistant", "```\n" + msg + "\n```")
            _emit_workflow_result(msg, "to-ssot")
            _emit_ssot_approval_ready(ip, state)
            return True

        locked_manifest_path = ip_dir / "req" / "approval_manifest.json"
        locked_req_paths = [
            ip_dir / "req" / "requirements_index.json",
            ip_dir / "req" / "obligations.json",
            ip_dir / "req" / "contract_refs.json",
            ip_dir / "req" / "evidence_plan.json",
            ip_dir / "req" / "locked_truth.md",
        ]
        locked_truth_active = False
        locked_truth_sources: list[str] = []
        if locked_manifest_path.is_file():
            try:
                locked_manifest = json.loads(locked_manifest_path.read_text(encoding="utf-8"))
            except Exception as exc:
                return _emit_to_ssot_blocked(
                    f"[SSOT GATE] blocked: locked truth manifest is unreadable for {ip}\n"
                    f"manifest: `{_relative_project_path(locked_manifest_path)}`\n"
                    f"error: {exc}"
                )
            locked_status = str(locked_manifest.get("status") or locked_manifest.get("locked_truth_status") or "").strip()
            if locked_status == "requirements_locked":
                missing_locked_files = [p for p in locked_req_paths if not p.is_file()]
                if missing_locked_files:
                    listed = "\n".join(f"- `{_relative_project_path(path)}`" for path in missing_locked_files)
                    return _emit_to_ssot_blocked(
                        f"[SSOT GATE] blocked: locked truth bundle is incomplete for {ip}\n"
                        f"manifest: `{_relative_project_path(locked_manifest_path)}`\n"
                        f"missing locked-truth files:\n{listed}"
                    )
                locked_truth_active = True
                locked_truth_sources = [
                    _relative_project_path(locked_manifest_path),
                    *[_relative_project_path(path) for path in locked_req_paths],
                ]
        import_files: list[Path] = []
        if imports_dir.is_dir():
            for path in sorted(imports_dir.rglob("*"), key=lambda p: p.as_posix()):
                if path.is_file() and path.suffix.lower() in _SSOT_IMPORT_EXTENSIONS:
                    import_files.append(path)
                    if len(import_files) >= 12:
                        break

        if import_files and (not manifest_path.is_file() or not extracted_path.is_file() or not evidence_path.is_file()):
            listed = "\n".join(f"- `{_relative_project_path(path)}`" for path in import_files[:8])
            return _emit_to_ssot_blocked(
                f"[SSOT GATE] blocked: import evidence index is incomplete for {ip}\n"
                f"required: `{_relative_project_path(manifest_path)}`, "
                f"`{_relative_project_path(extracted_path)}`, "
                f"`{_relative_project_path(evidence_path)}`\n"
                "found import files:\n"
                f"{listed or '- (none)'}\n"
                f"run: /import --ip {ip} " + " ".join(f"@{_relative_project_path(path)}" for path in import_files[:8])
            )

        missing = _missing_ssot_decisions(ip, state)
        if missing and not locked_truth_active:
            return _emit_to_ssot_blocked(
                f"[SSOT GATE] blocked: {ip} still has missing SSOT decisions\n"
                f"missing: {', '.join(missing)}\n"
                f"next: run `/import --ip {ip} @<evidence>` if docs exist, or `/grill-me {ip}` for only the gaps.\n"
                "The LLM SSOT write is not queued until these decision slots are evidence-backed."
            )

        # /to-ssot queues a Normal-mode LLM turn only after the deterministic
        # import/decision preflight is complete. When locked truth exists,
        # req/ is the authority and missing legacy decision slots must be
        # projected into SSOT fields instead of blocking on grill-me.
        spec = _render_approved_ssot_spec(ip, state) if (state or locked_truth_active) else f"[to-ssot] {ip}: no SSOT state yet."
        _append_session_message(session, "user", text)
        _append_session_message(session, "assistant", spec)
        _append_workflow_history("ssot-gen", "user", text)
        _append_workflow_history("ssot-gen", "assistant", spec)
        _append_active_history("user", text)
        if _ssot_yaml_path_for_session is not None:
            ssot_path = _ssot_yaml_path_for_session(ip, client_session)
        else:
            ssot_path = _ssot_yaml_path(ip)
        source_summary = (
            "Sources: locked truth bundle "
            + ", ".join(f"`{src}`" for src in locked_truth_sources)
            + "."
            if locked_truth_active
            else f"Sources: `{ip}/req/import_manifest.json`, `{ip}/req/extracted_decisions.json`, `{ip}/wiki/import-evidence.md`, Web Q&A."
        )
        ready_msg = (
            f"[to-ssot] {ip} — queueing LLM SSOT write.\n"
            f"Target: {ssot_path}\n"
            f"{source_summary}"
        )
        _append_session_message(session, "assistant", ready_msg)
        _append_workflow_history("ssot-gen", "assistant", ready_msg)
        _append_active_history("assistant", "```\n" + ready_msg + "\n```")
        _emit_workflow_result(ready_msg, "to-ssot")
        # Queue the actual LLM write turn. Normal mode + ssot-gen
        # workspace + cleared chat so the agent starts from a clean
        # slate with the import/wiki context inline.
        _queue_prompt_for_session(client_session, "/mode normal")
        _queue_prompt_for_session(client_session, "/wf ssot-gen")
        _queue_prompt_for_session(client_session, "/clear")
        if _script_project_root_for_session is not None:
            script_root = _script_project_root_for_session(ip, client_session)
        else:
            script_root = _script_project_root(ip)
        repair_script = WORKFLOW_ROOT / "ssot-gen" / "scripts" / "repair_ssot_schema.py"
        verify_script = WORKFLOW_ROOT / "ssot-gen" / "scripts" / "verify_ssot.py"
        _queue_prompt_for_session(client_session,
            f"Write the canonical SSOT YAML for IP `{ip}` at the path\n"
            f"  `{ssot_path}`\n\n"
            "Workspace boundary (do not search or read outside these roots):\n"
            f"  - PROJECT_ROOT: `{script_root}`\n"
            f"  - IP_ROOT:      `{ip_dir}`\n"
            f"  - WORKFLOW_ROOT: `{WORKFLOW_ROOT}`\n"
            f"  - COMMON_AI_AGENT_HOME (read-only): `{SOURCE_ROOT}`\n\n"
            "Environment aliases for commands: `$ATLAS_PROJECT_ROOT` is the IP/project artifact root, "
            "`$ATLAS_WORKFLOW_ROOT` is the workflow script root, and `$ATLAS_IP_ROOT` may pin this IP root.\n\n"
            "Source-of-truth inputs (READ these first):\n"
            + (
                f"  1. `{ip}/req/approval_manifest.json`  — locked-truth approval, approver, and bundle hash.\n"
                f"  2. `{ip}/req/requirements_index.json` — canonical locked requirements.\n"
                f"  3. `{ip}/req/obligations.json`        — atomic testable obligations split from requirements.\n"
                f"  4. `{ip}/req/contract_refs.json`      — machine-checkable central/stage contract references.\n"
                f"  5. `{ip}/req/evidence_plan.json`      — planned artifacts, validators, and pass conditions.\n"
                f"  6. `{ip}/req/locked_truth.md`         — deterministic human-readable projection of the locked bundle.\n"
                f"  7. Existing `{ip}/yaml/{ip}.ssot.yaml` is only a prior Design Spec projection; if it is a TBD skeleton, replace/repair it from req/.\n"
                f"  8. Import/wiki evidence may be read if present, but locked req/ wins on conflicts.\n\n"
                if locked_truth_active else
                f"  1. `{ip}/req/import_manifest.json`     — authoritative import inventory, candidate facts, source excerpts, conflicts, next action.\n"
                f"  2. `{ip}/req/extracted_decisions.json` — per-decision evidence extracted by /import.\n"
                f"  3. `{ip}/wiki/import-evidence.md`, `{ip}/wiki/index.md`, `_graph.json`, `log.md`, `notes.md` — accumulated wiki evidence.\n"
                f"  4. `{ip}/req/imports/`                 — uploaded/converted requirement evidence referenced by the manifest.\n"
                "  5. Web Q&A snapshot (already inline above in the [SSOT SPEC] block).\n\n"
            )
            +
            "Canonical YAML shape required by SSOT Preview and gates:\n"
            "  - Top level must be one YAML mapping. Do NOT wrap the document in `ssot:`, `sections:`, `spec:`, or markdown fences.\n"
            "  - Use these exact top-level keys, in this order:\n"
            "    top_module, sub_modules, decomposition, rtl_contract, parameters, io_list, features, dataflow, function_model, cycle_model, clock_reset_domains, cdc_requirements, rdc_requirements, registers, memory, interrupts, fsm, timing, power, security, error_handling, debug_observability, integration, dft, synthesis, pnr, coding_rules, reuse_modules, custom, dir_structure, filelist, test_requirements, quality_gates, traceability, workflow_todos, generation_flow.\n"
            "  - Do NOT use legacy aliases such as `interface`, `bus_interface`, `register_map`, `clock_reset`, `errors`, `debug`, `dv_plan`, or `verification_plan` as top-level sections.\n"
            "  - Engineering/signoff SSOT must include the fields SSOT Preview parses: `top_module.description`, `io_list.interfaces[].ports[]`, `function_model.transactions[]`, `cycle_model.pipeline[]`, `cycle_model.scenarios[]` or `function_model.scenarios[]` or `test_requirements.scenarios[]`, `registers.register_list[]` or an explicit no-register policy, `fsm.states/transitions` or an explicit no-FSM policy, and `test_requirements.scenarios[]`.\n\n"
            "Workflow TODO contract:\n"
            "  - Preserve and enrich `workflow_todos.<stage>[]` as the executable handoff list.\n"
            "  - Every workflow_todos item you add or keep must include: `id`, `content`, `detail`, `command`, `script`, `instructions`, `criteria`, `source_refs`, `priority`, and `required`.\n"
            f"  - `command` is the ATLAS slash command (for example `/to-ssot {ip}`, `/ssot-rtl {ip}`, `/ssot-tb {ip}`).\n"
            "  - `script` is the deterministic workflow script that validates or expands that handoff (for example `$ATLAS_WORKFLOW_ROOT/ssot-gen/scripts/verify_ssot.py`).\n"
            "  - `instructions` must be IP-specific and source-backed; do not leave generic template language when imported evidence is available.\n\n"
            "Rules for the write:\n"
            "  - Derive missing SSOT Preview fields from locked requirements, obligations, contract_refs, and evidence_plan before asking the user.\n"
            "  - Map req/obligation/contract facts into canonical Design Spec sections: purpose -> top_module.description; interface obligations -> io_list.interfaces[].ports[]; register obligations -> registers.register_list[]; reset obligations -> clock_reset_domains; interrupt obligations -> interrupts; evidence_plan -> test_requirements.scenarios[] and quality_gates.\n"
            "  - If locked truth does not specify memory blocks, FSMs, child submodules, DFT, power, or security behavior, add an explicit no-memory/no-FSM/external-owner/non-goal policy with source_refs instead of leaving TBD.\n"
            "  - Do NOT stamp a 33-section template; do NOT invent behavior beyond req/. Do NOT use placeholder strings like '(TBD)' as a shortcut. If a fact is truly absent from locked truth and affects RTL behavior, record a focused blocker/assumption in `custom.assumptions` or `[SSOT QUESTION]`.\n"
            f"  - Do not copy DMA/AXI example content from `{WORKFLOW_ROOT / 'ssot-gen' / 'rules' / 'ssot-template.yaml'}`. The template is a schema/order reference only; imported evidence and Q&A are the behavior source.\n"
            "  - Quote register addresses, signal names, encodings, and "
            "interface widths verbatim from the imports.\n"
            "  - Cite the source path inline (e.g. "
            f"`# source: {ip}/req/imports/<file>.md L<lineno>`) whenever "
            "you transcribe a number, table row, or normative requirement.\n\n"
            "Execution requirement: this is a single Normal-mode write turn. "
            "Use write_file (or replace_in_file on an existing draft) to "
            "produce the yaml; do not call todo_write (Plan Mode only). "
            f"After the write, run `python3 {repair_script} {ip} --root {script_root} --mode engineering` "
            f"and `python3 {verify_script} {ip} --root {script_root} --mode engineering`; fix any format failures before handoff. "
            "Emit `[SSOT HANDOFF]` once the yaml is on disk."
        )
        client_session.emit("agent_state", running=True)
        return True

    def _handle_repair_ssot_command(text: str, client_session: Any | None = None) -> bool:
        cmd, args = _split_slash(text)
        if cmd not in ("repair-ssot", "rs"):
            return False
        ip = _command_ip(args, client_session=client_session)
        if not _valid_ip_name(ip):
            _emit_workflow_result(
                "[repair-ssot] no active IP found\nOpen/select an IP or run /new-ip <ip_name> first.",
                "repair-ssot",
            )
            return True

        script = WORKFLOW_ROOT / "ssot-gen" / "scripts" / "repair_ssot_schema.py"
        validator = WORKFLOW_ROOT / "ssot-gen" / "scripts" / "verify_ssot.py"
        ssot_path = _ssot_yaml_path(ip)
        session = _canonical_session_string(ip)
        _append_session_message(session, "user", text)
        _append_workflow_history("ssot-gen", "user", text)
        _append_active_history("user", text)
        client_session.emit("agent_state", running=True)

        if not ssot_path.is_file():
            msg = (
                f"[repair-ssot] blocked: SSOT not found at {ssot_path}\n"
                "Run /new-ip if needed, then /to-ssot for the active IP."
            )
            _append_session_message(session, "assistant", msg)
            _append_workflow_history("ssot-gen", "assistant", msg)
            _append_active_history("assistant", "```\n" + msg + "\n```")
            _emit_workflow_result(msg, "repair-ssot")
            return True

        try:
            import subprocess

            repair = subprocess.run(
                [_python_cmd(), str(script), ip, "--root", str(PROJECT_ROOT)],
                cwd=str(PROJECT_ROOT),
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                timeout=60,
            )
            validate = subprocess.run(
                [_python_cmd(), str(validator), ip, "--root", str(PROJECT_ROOT), "--mode", "engineering"],
                cwd=str(PROJECT_ROOT),
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                timeout=60,
            )
        except Exception as exc:
            msg = f"[repair-ssot] failed: {exc}"
            _append_session_message(session, "assistant", msg)
            _append_workflow_history("ssot-gen", "assistant", msg)
            _append_active_history("assistant", "```\n" + msg + "\n```")
            _emit_workflow_result(msg, "repair-ssot")
            return True

        parts = [
            f"[repair-ssot] {ip}",
            f"source: {ssot_path}",
            f"repair exit: {repair.returncode}",
        ]
        if repair.stdout.strip():
            parts += ["", "repair stdout:", repair.stdout.strip()]
        if repair.stderr.strip():
            parts += ["", "repair stderr:", repair.stderr.strip()]
        parts += ["", f"validator exit: {validate.returncode}"]
        if validate.stdout.strip():
            parts += ["", "validator stdout:", validate.stdout.strip()]
        if validate.stderr.strip():
            parts += ["", "validator stderr:", validate.stderr.strip()]
        msg = "\n".join(parts)
        _append_session_message(session, "assistant", msg)
        _append_workflow_history("ssot-gen", "assistant", msg)
        _append_active_history("assistant", "```\n" + msg + "\n```")
        _emit_workflow_result(msg, "repair-ssot")
        return True

    def _handle_verify_ssot_command(text: str, client_session: Any | None = None) -> bool:
        cmd, args = _split_slash(text)
        if cmd not in ("verify-ssot", "verify_ssot", "vs", "verity-ssot", "verity_ssot"):
            return False
        try:
            tokens = shlex.split(args or "")
        except ValueError as exc:
            _emit_workflow_result(f"[verify-ssot] invalid arguments: {exc}", "verify-ssot")
            return True

        ip = ""
        mode = "engineering"
        preview = "strict"
        i = 0
        while i < len(tokens):
            tok = tokens[i]
            if tok in ("--mode", "--run-mode") and i + 1 < len(tokens):
                mode = tokens[i + 1]
                i += 2
                continue
            if tok.startswith("--mode="):
                mode = tok.split("=", 1)[1]
                i += 1
                continue
            if tok in ("--preview", "--preview-contract") and i + 1 < len(tokens):
                preview = tokens[i + 1]
                i += 2
                continue
            if tok.startswith("--preview="):
                preview = tok.split("=", 1)[1]
                i += 1
                continue
            if not tok.startswith("-") and not ip:
                ip = tok
            i += 1

        ip = ip if _valid_ip_name(ip) else _active_ssot_ip()
        if not _valid_ip_name(ip):
            _emit_workflow_result(
                "[verify-ssot] no active IP found\n"
                "Open/select an IP or run /new-ip <ip_name> first.",
                "verify-ssot",
            )
            return True

        _set_active_ssot_ip(ip)
        ssot_path = _ssot_yaml_path(ip)
        script = WORKFLOW_ROOT / "ssot-gen" / "scripts" / "verify_ssot.py"
        session = _canonical_session_string(ip)
        _append_session_message(session, "user", text)
        _append_workflow_history("ssot-gen", "user", text)
        _append_active_history("user", text)
        client_session.emit("agent_state", running=True)

        if not script.is_file():
            msg = f"[verify-ssot] verifier script not found: {script}"
            _append_session_message(session, "assistant", msg)
            _append_workflow_history("ssot-gen", "assistant", msg)
            _append_active_history("assistant", "```\n" + msg + "\n```")
            _emit_workflow_result(msg, "verify-ssot")
            return True

        try:
            verify = subprocess.run(
                [
                    _python_cmd(),
                    str(script),
                    ip,
                    "--root",
                    str(PROJECT_ROOT),
                    "--mode",
                    mode,
                    "--preview",
                    preview,
                ],
                cwd=str(PROJECT_ROOT),
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                timeout=120,
            )
        except Exception as exc:
            msg = f"[verify-ssot] failed: {exc}"
            _append_session_message(session, "assistant", msg)
            _append_workflow_history("ssot-gen", "assistant", msg)
            _append_active_history("assistant", "```\n" + msg + "\n```")
            _emit_workflow_result(msg, "verify-ssot")
            return True

        parts = [
            f"[verify-ssot] {ip}",
            f"source: {ssot_path}",
            f"mode: {mode}",
            f"exit: {verify.returncode}",
        ]
        if verify.stdout.strip():
            parts += ["", verify.stdout.strip()]
        if verify.stderr.strip():
            parts += ["", "stderr:", verify.stderr.strip()]
        msg = "\n".join(parts)
        _append_session_message(session, "assistant", msg)
        _append_workflow_history("ssot-gen", "assistant", msg)
        _append_active_history("assistant", "```\n" + msg + "\n```")
        _emit_workflow_result(msg, "verify-ssot")
        return True

    def _handle_repair_rtl_command(text: str, client_session: Any | None = None) -> bool:
        cmd, args = _split_slash(text)
        if cmd not in ("repair-rtl", "rrtl"):
            return False
        ip = _command_ip(args, client_session=client_session)
        if not _valid_ip_name(ip):
            _emit_workflow_result(
                "[repair-rtl] no active IP found\nOpen/select an IP or run /new-ip <ip_name> first.",
                "repair-rtl",
            )
            return True
        ip_dir = _ip_root(ip)
        ssot_path = _ssot_yaml_path(ip)
        if not ssot_path.is_file():
            _emit_workflow_result(
                f"[repair-rtl] blocked: SSOT not found at {ip}/yaml/{ip}.ssot.yaml\n"
                "Run /new-ip if needed, then /to-ssot for the active IP.",
                "repair-rtl",
            )
            return True
        session = f"{ip}/rtl-gen"
        compile_report = ip_dir / "rtl" / "rtl_compile.json"
        lint_report = ip_dir / "lint" / "dut_lint.json"
        py_cmd = _python_cmd()
        queued = (
            f"[repair-rtl] queued through rtl-gen\n"
            f"module: {ip}\n"
            f"ssot: {ip}/yaml/{ip}.ssot.yaml\n"
            f"compile report: {ip}/rtl/rtl_compile.json\n"
            f"lint report: {ip}/lint/dut_lint.json"
        )
        _append_session_message(session, "user", text)
        _append_session_message(session, "assistant", "```\n" + queued + "\n```")
        _append_active_history("user", text)
        _append_active_history("assistant", "```\n" + queued + "\n```")
        _queue_prompt_for_session(client_session, "/mode normal")
        _queue_prompt_for_session(client_session, "/wf rtl-gen")
        _queue_prompt_for_session(client_session, "/clear")
        _queue_prompt_for_session(client_session, f"/todo template ssot-rtl {ip}")
        _queue_prompt_for_session(client_session,
            f"Repair RTL for {ip} using only SSOT-driven rtl-gen ownership.\n\n"
            f"Read these evidence files first:\n"
            f"- SSOT: `{ssot_path}`\n"
            f"- compile report: `{compile_report}`\n"
            f"- compile log: `{ip_dir / 'rtl' / 'rtl_compile.log'}`\n"
            f"- lint report: `{lint_report}`\n"
            f"- filelist: `{ip_dir / 'list' / f'{ip}.f'}`\n\n"
            "Repair only files under `<ip>/rtl/` and `<ip>/list/` unless the evidence "
            "proves the SSOT manifest itself is wrong. If SSOT/filelist/top-module "
            "naming is inconsistent, emit `[SSOT QUESTION] -> ssot-gen` with the exact "
            "YAML fields to repair instead of silently changing the YAML. Do not edit TB, "
            "sim, cov, or unrelated IPs.\n\n"
            "Current required repair classes:\n"
            "- Eliminate all `rtl_compile.json.style_violation_details`; especially no "
            "parameterized part-selects inside `always`, `always_comb`, `always_ff`, or "
            "`always_latch`. Use helper wires and continuous assigns.\n"
            "- Eliminate all Icarus `sorry:` diagnostics and any compile warnings/errors.\n"
            "- Preserve DUT-only lint pass with zero suppressions; on Windows use Icarus "
            "Verilog (`iverilog`) rather than Verilator.\n"
            "- Reconcile filelist and top wrapper naming with SSOT, or escalate to ssot-gen "
            "if the SSOT source of truth must change.\n\n"
            "After the final RTL edit, run exactly:\n"
            f"`{py_cmd} {WORKFLOW_ROOT / 'rtl-gen' / 'scripts' / 'rtl_compile_report.py'} {ip} --top {ip}`\n"
            f"`{py_cmd} {WORKFLOW_ROOT / 'lint' / 'scripts' / 'dut_lint_report.py'} {ip} --top {ip}`\n\n"
            "DONE requires compile pass E0/D0/S0, lint pass E0/W0/S0, and no hidden "
            "waivers/suppressions. If any part cannot be fixed from RTL alone, stop with "
            "a precise `[SSOT QUESTION]` or `[RTL BLOCKED]` rather than claiming DONE."
        )
        client_session.emit("agent_state", running=True)
        _emit_workflow_result(queued, "repair-rtl")
        client_session.emit("agent_state", running=True)
        return True

    def _handle_repair_equiv_command(text: str, client_session: Any | None = None) -> bool:
        cmd, args = _split_slash(text)
        if cmd not in ("repair-equiv", "repair-equivalence", "reqv"):
            return False
        ip = _command_ip(args, client_session=client_session)
        if not _valid_ip_name(ip):
            _emit_workflow_result(
                "[repair-equiv] no active IP found\nOpen/select an IP or run /new-ip <ip_name> first.",
                "repair-equiv",
            )
            return True
        classify_path = _ip_root(ip) / "sim" / "mismatch_classification.json"
        if not classify_path.is_file():
            _emit_workflow_result(
                f"[repair-equiv] blocked: missing {ip}/sim/mismatch_classification.json\n"
                f"Run /sim-debug {ip} first.",
                "repair-equiv",
            )
            return True
        try:
            classify_doc = json.loads(classify_path.read_text(encoding="utf-8"))
            if not isinstance(classify_doc, dict):
                classify_doc = {}
        except Exception as exc:
            _emit_workflow_result(
                f"[repair-equiv] blocked: cannot parse {ip}/sim/mismatch_classification.json: {exc}",
                "repair-equiv",
            )
            return True
        classifications = classify_doc.get("classifications")
        if not isinstance(classifications, list):
            classifications = []

        loopable = [
            item for item in classifications
            if isinstance(item, dict)
            and item.get("llm_loop_allowed") is True
            and str(item.get("owner") or "").strip()
            and str(item.get("repair_prompt") or "").strip()
        ]
        human_only = [
            item for item in classifications
            if isinstance(item, dict) and item.get("llm_loop_allowed") is False
        ]
        if not loopable:
            lines = [
                "[repair-equiv] no loopable classifications found",
                f"module: {ip}",
                f"classification status: {classify_doc.get('status') or 'unknown'}",
                f"human-gated: {len(human_only)}",
                f"source: {ip}/sim/mismatch_classification.json",
            ]
            if human_only:
                lines.append("next: answer ATLAS human-gate questions from /sim-debug before repair")
            else:
                lines.append("next: rerun /sim-debug after a failing sim to create repair classifications")
            _emit_workflow_result("\n".join(lines), "repair-equiv")
            return True

        route = {
            "rtl-gen": ("rtl-gen", "ssot-rtl"),
            "rtl": ("rtl-gen", "ssot-rtl"),
            "fl-model-gen": ("fl-model-gen", "ssot-fl-model"),
            "fl_model": ("fl-model-gen", "ssot-fl-model"),
            "tb-gen": ("tb-gen", "ssot-tb-cocotb"),
            "tb": ("tb-gen", "ssot-tb-cocotb"),
            "coverage": ("coverage", "coverage_iter"),
            "sim_debug": ("sim_debug", "sim-debug"),
            "sim-debug": ("sim_debug", "sim-debug"),
        }
        grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
        unrouted: list[dict[str, Any]] = []
        for item in loopable:
            owner = str(item.get("owner") or "").strip()
            key = route.get(owner)
            if key is None:
                unrouted.append(item)
                continue
            grouped.setdefault(key, []).append(item)

        session = f"{ip}/sim_debug"
        _append_session_message(session, "user", text)
        _append_active_history("user", text)
        queued_lines = [
            "[repair-equiv] queued loopable equivalence repairs",
            f"module: {ip}",
            f"source: {ip}/sim/mismatch_classification.json",
            f"loopable: {len(loopable)}",
            f"human-gated: {len(human_only)}",
        ]
        for (workflow, template), items in grouped.items():
            queued_lines.append(f"- {workflow}: {len(items)} classification(s)")
            _queue_prompt_for_session(client_session, "/mode normal")
            _queue_prompt_for_session(client_session, f"/wf {workflow}")
            _queue_prompt_for_session(client_session, "/clear")
            _queue_prompt_for_session(client_session, f"/todo template {template} {ip}")
            payload = json.dumps(items, indent=2, ensure_ascii=False)[:12000]
            _queue_prompt_for_session(client_session,
                f"Execute classified FL-vs-RTL repair for {ip}.\n\n"
                "Hard rules:\n"
                "- Use SSOT YAML, FunctionalModel, equivalence_goals.json, scoreboard_events.jsonl, "
                "fl_rtl_compare.json, and mismatch_classification.json as evidence.\n"
                "- Repair only this workflow owner's artifacts. Do not change SSOT semantics unless "
                "the classification explicitly routes to ssot-gen and a human answer exists.\n"
                "- Do not copy wrong RTL observed behavior into expected values.\n"
                "- After repair, rerun the smallest owning validator, then tell the user to rerun "
                f"/sim {ip}, /sim-debug {ip}, and /goal-audit {ip}.\n\n"
                f"Classifications for this owner:\n```json\n{payload}\n```"
            )
        if unrouted:
            queued_lines.append(f"unrouted owners: {', '.join(str(i.get('owner')) for i in unrouted[:8] if isinstance(i, dict))}")
        if human_only:
            queued_lines.append("human gate remains required for non-loopable classifications")
        msg = "\n".join(queued_lines)
        _append_session_message(session, "assistant", "```\n" + msg + "\n```")
        _append_workflow_history("sim_debug", "assistant", msg)
        _append_active_history("assistant", "```\n" + msg + "\n```")
        _emit_workflow_result(msg, "repair-equiv")
        client_session.emit("agent_state", running=True)
        return True

    def _run_stage_command(text: str, client_session: Any | None = None) -> bool:
        cmd, args = _split_slash(text)
        alias = {
            "sr": "ssot-rtl",
            "sfm": "ssot-fl-model",
            "seg": "ssot-equiv-goals",
            "equiv-goals": "ssot-equiv-goals",
            "tb": "ssot-tb-cocotb",
            "stb": "ssot-tb",
            "stb-cocotb": "ssot-tb-cocotb",
            "stb-uvm": "ssot-tb-uvm",
            "stb-verilog": "ssot-tb-verilog",
            "ssot-tb-sv": "ssot-tb-verilog",
            "stb-sv": "ssot-tb-verilog",
            "s": "sim",
            "sd": "sim-debug",
            "cov": "coverage",
            "l": "lint",
            "contract": "contract-check",
            "audit": "goal-audit",
            "ga": "goal-audit",
        }.get(cmd, cmd)
        spec = _STAGE_RUNNERS.get(alias)
        if not spec:
            return False
        ip = _command_ip(args, client_session=client_session)
        if not _valid_ip_name(ip):
            _emit_workflow_result(
                f"[{alias}] no active IP found\nOpen/select an IP or run /new-ip <ip_name> first.",
                alias,
            )
            return True
        ip_dir = _ip_root(ip)
        ssot_path = _ssot_yaml_path(ip)
        if not ssot_path.is_file():
            _emit_workflow_result(
                f"[{alias}] blocked: SSOT not found at {ip}/yaml/{ip}.ssot.yaml\n"
                "Run /new-ip if needed, then /to-ssot for the active IP.",
                alias,
            )
            return True
        if alias == "signoff":
            session = f"{ip}/signoff"
            _append_session_message(session, "user", text)
            _append_active_history("user", text)
            client_session.emit("agent_state", running=True)

            async def _emit_signoff_snapshot() -> None:
                try:
                    resp = await api_progress(scope=ip)
                    data = json.loads(resp.body.decode("utf-8"))
                    selected = data.get("selected") if isinstance(data, dict) else {}
                    signoff = selected.get("signoff") if isinstance(selected, dict) else {}
                    status = signoff.get("status") if isinstance(signoff, dict) else {}
                    blockers = signoff.get("blockers") if isinstance(signoff, dict) else []
                    progress = selected.get("progress") if isinstance(selected, dict) else {}
                    equivalence = progress.get("equivalence_goals") if isinstance(progress, dict) else {}
                    goal_audit = progress.get("goal_audit") if isinstance(progress, dict) else {}
                    lines = [
                        "[signoff] strict SSOT progress gate",
                        f"module: {ip}",
                        f"status: {status.get('signoff', 'unknown') if isinstance(status, dict) else 'unknown'}",
                        f"equivalence: {status.get('equivalence_goals', 'unknown') if isinstance(status, dict) else 'unknown'}",
                        f"goal_audit: {status.get('goal_audit', 'unknown') if isinstance(status, dict) else 'unknown'}",
                        f"coverage: {status.get('coverage', 'unknown') if isinstance(status, dict) else 'unknown'}",
                        f"evidence: /api/progress?scope={ip}",
                    ]
                    if isinstance(equivalence, dict):
                        lines.append(
                            "equivalence_counts: "
                            f"{equivalence.get('passed', 0)}/{equivalence.get('total', 0)} pass, "
                            f"failed={equivalence.get('failed', 0)}, "
                            f"blocked={equivalence.get('blocked', 0)}, "
                            f"untested={equivalence.get('untested', 0)}"
                        )
                    if isinstance(goal_audit, dict):
                        lines.append(
                            "goal_audit_checks: "
                            f"{goal_audit.get('passed_checks', 0)}/{goal_audit.get('total_checks', 0)} pass, "
                            f"failed={goal_audit.get('failed_checks', 0)}"
                        )
                    if blockers:
                        lines.append("")
                        lines.append("blockers:")
                        for blocker in blockers[:12]:
                            lines.append(f"- {blocker}")
                    msg = "\n".join(lines)
                except Exception as exc:
                    msg = f"[signoff] failed to read ATLAS progress gate for {ip}: {exc}"
                _append_session_message(session, "assistant", msg)
                _append_workflow_history("sim_debug", "assistant", msg)
                _append_active_history("assistant", "```\n" + msg + "\n```")
                _emit_workflow_result(msg, alias)

            asyncio.create_task(_emit_signoff_snapshot())
            return True

        try:
            from src.workflow_stage_surface import is_common_stage, run_common_stage_surface
        except ModuleNotFoundError:  # pragma: no cover - direct script execution fallback
            from workflow_stage_surface import is_common_stage, run_common_stage_surface

        if is_common_stage(alias):
            template = str(spec.get("template") or alias)
            surface = run_common_stage_surface(
                project_root=_script_project_root(ip),
                source_root=SOURCE_ROOT,
                alias=alias,
                ip=ip,
                template=template,
                run_mode=os.environ.get("ATLAS_RUN_MODE", ""),
            )
            if not surface.handled:
                return False
            session = surface.session
            workflow = surface.workflow
            msg = surface.message
            engine_alias = surface.alias
            _append_session_message(session, "user", text)
            _append_active_history("user", text)
            client_session.emit("agent_state", running=True)
            _append_session_message(session, "assistant", msg)
            _append_workflow_history(workflow, "assistant", msg)
            _append_active_history("assistant", "```\n" + msg + "\n```")
            _emit_workflow_result(msg, engine_alias)

            if surface.rtl_blocked:
                # surface.message already contains the [SSOT QUESTION] /
                # rtl_blocked.json explanation in the chat; skip the
                # separate structured RTL Blocker Q&A panel so /ssot-rtl
                # stops short with a single readable message.
                return True
            for prompt in surface.queue_prompts:
                _queue_prompt_for_session(client_session, prompt)
            if surface.queue_prompts:
                client_session.emit("agent_state", running=True)
                return True
            if surface.sim_human_gate_doc is not None:
                opened_human_gate = _start_sim_human_gate_qna(
                    ip,
                    surface.sim_human_gate_doc,
                    reason="automatic /sim-debug",
                    client_session=client_session,
                )
                if opened_human_gate:
                    note = f"[sim-debug] opened ATLAS human-gate question(s) from {ip}/sim/mismatch_classification.json"
                    _append_session_message(session, "assistant", note)
                    _append_workflow_history(workflow, "assistant", note)
                    _append_active_history("assistant", "```\n" + note + "\n```")
                    client_session.emit("tool_result", text="```\n" + note + "\n```", tool=engine_alias, truncated=False)
                    client_session.emit("slash_output", text="```\n" + note + "\n```")
                    client_session.emit("flush")
                    return True
            client_session.emit("agent_state", running=False)
            return True
        if alias == "sim":
            session = f"{ip}/sim"
            script = WORKFLOW_ROOT / "tb-gen" / "scripts" / "sim.sh"
            validator = WORKFLOW_ROOT / "tb-gen" / "scripts" / "check_tb_sim_evidence.sh"
            coverage_script = WORKFLOW_ROOT / "coverage" / "scripts" / "ssot_coverage_summary.py"
            runner_candidates = [
                ip_dir / "tb" / "cocotb" / "test_runner.py",
                ip_dir / "tb" / "cocotb" / "run_tests.py",
                ip_dir / "tb" / "test_runner.py",
                ip_dir / "tb" / "run_tests.py",
                ip_dir / "sim" / f"test_{ip}.py",
            ]
            runner = next((p for p in runner_candidates if p.is_file()), None)
            _append_session_message(session, "user", text)
            _append_active_history("user", text)
            client_session.emit("agent_state", running=True)
            if runner is None:
                msg = (
                    f"[sim] blocked: no executable TB runner found for {ip}\n"
                    "expected one of:\n"
                    f"- {ip}/tb/cocotb/test_runner.py\n"
                    f"- {ip}/tb/cocotb/run_tests.py\n"
                    f"- {ip}/tb/test_runner.py\n"
                    f"- {ip}/tb/run_tests.py\n"
                    "Run /tb <ip> first."
                )
                _append_session_message(session, "assistant", msg)
                _append_workflow_history("sim", "assistant", msg)
                _append_active_history("assistant", "```\n" + msg + "\n```")
                _emit_workflow_result(msg, alias)
                return True
            try:
                import subprocess
                stage_root = _script_project_root(ip)
                try:
                    runner_rel = runner.relative_to(stage_root).as_posix()
                except ValueError:
                    runner_rel = runner.relative_to(PROJECT_ROOT).as_posix()

                sim_run = subprocess.run(
                    ["bash", str(script), runner_rel],
                    cwd=str(stage_root),
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    capture_output=True,
                    timeout=180,
                )
                validate_run = subprocess.run(
                    ["bash", str(validator), ip],
                    cwd=str(stage_root),
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    capture_output=True,
                    timeout=180,
                )
                coverage_run = subprocess.CompletedProcess(
                    args=[_python_cmd(), str(coverage_script), str(ip_dir)],
                    returncode=0,
                    stdout="",
                    stderr="",
                )
                if sim_run.returncode == 0 and validate_run.returncode == 0:
                    coverage_run = subprocess.run(
                        [_python_cmd(), str(coverage_script), str(ip_dir)],
                        cwd=str(stage_root),
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                        capture_output=True,
                        timeout=90,
                    )
            except Exception as exc:
                msg = f"[sim] failed: {exc}"
                _append_session_message(session, "assistant", msg)
                _append_workflow_history("sim", "assistant", msg)
                _append_active_history("assistant", "```\n" + msg + "\n```")
                _emit_workflow_result(msg, alias)
                return True

            status_word = "PASS" if sim_run.returncode == 0 and validate_run.returncode == 0 and coverage_run.returncode == 0 else "FAIL"
            parts = [
                f"[sim] {status_word}",
                f"script: {script}",
                f"validator: {validator}",
                f"coverage: {coverage_script}",
                f"module: {ip}",
                f"runner: {runner_rel}",
                f"sim exit: {sim_run.returncode}",
            ]
            if sim_run.stdout.strip():
                parts += ["", "sim stdout:", sim_run.stdout.strip()]
            if sim_run.stderr.strip():
                parts += ["", "sim stderr:", sim_run.stderr.strip()]
            parts += ["", f"validator exit: {validate_run.returncode}"]
            if validate_run.stdout.strip():
                parts += ["", "validator stdout:", validate_run.stdout.strip()]
            if validate_run.stderr.strip():
                parts += ["", "validator stderr:", validate_run.stderr.strip()]
            parts += ["", f"coverage exit: {coverage_run.returncode}"]
            if coverage_run.stdout.strip():
                parts += ["", "coverage stdout:", coverage_run.stdout.strip()]
            if coverage_run.stderr.strip():
                parts += ["", "coverage stderr:", coverage_run.stderr.strip()]
            parts += [
                "",
                "expected artifacts:",
                f"- {ip}/sim/results.xml or {ip}/tb/cocotb/results.xml",
                f"- {ip}/sim/scoreboard_events.jsonl",
                f"- {ip}/cov/coverage.json",
                f"- {ip}/sim/sim_report.txt",
            ]
            msg = "\n".join(parts)
            _append_session_message(session, "assistant", msg)
            _append_workflow_history("sim", "assistant", msg)
            _append_active_history("assistant", "```\n" + msg + "\n```")
            _emit_workflow_result(msg, alias)
            return True
        if alias == "ssot-rtl":
            session = f"{ip}/rtl-gen"
            script = WORKFLOW_ROOT / "rtl-gen" / "scripts" / "ssot_to_rtl.py"
            top = ip
            try:
                import yaml as _yaml  # type: ignore
                ssot_doc = _yaml.safe_load(ssot_path.read_text(encoding="utf-8", errors="replace")) or {}
                top_doc = ssot_doc.get("top_module") if isinstance(ssot_doc, dict) else {}
                if isinstance(top_doc, dict) and top_doc.get("name"):
                    top = str(top_doc.get("name"))
                elif isinstance(top_doc, str) and top_doc.strip():
                    top = top_doc.strip()
            except Exception:
                top = ip

            _append_session_message(session, "user", text)
            _append_active_history("user", text)
            client_session.emit("agent_state", running=True)
            runs: list[dict[str, Any]] = []
            stage_root = _script_project_root(ip)

            def _clip(s: str, limit: int = 12000) -> str:
                if len(s) <= limit:
                    return s
                return s[:limit] + f"\n... <truncated {len(s) - limit} chars>"

            def _run_tool(label: str, command: list[str], timeout_s: int = 180) -> int:
                try:
                    import subprocess

                    proc = subprocess.run(
                        command,
                        cwd=str(stage_root),
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                        capture_output=True,
                        timeout=timeout_s,
                    )
                    runs.append({
                        "label": label,
                        "command": " ".join(command),
                        "returncode": proc.returncode,
                        "stdout": _clip((proc.stdout or "").strip()),
                        "stderr": _clip((proc.stderr or "").strip()),
                    })
                    return int(proc.returncode)
                except Exception as exc:
                    runs.append({
                        "label": label,
                        "command": " ".join(command),
                        "returncode": 999,
                        "stdout": "",
                        "stderr": str(exc),
                    })
                    return 999

            gen_rc = _run_tool("rtl_generate", [_python_cmd(), str(script), ip, "--root", str(stage_root)])
            compile_rc: int | None = None
            lint_rc: int | None = None
            if gen_rc == 0:
                compile_script = WORKFLOW_ROOT / "rtl-gen" / "scripts" / "rtl_compile_report.py"
                lint_script = WORKFLOW_ROOT / "lint" / "scripts" / "dut_lint_report.py"
                compile_rc = _run_tool(
                    "dut_compile",
                    [
                        _python_cmd(),
                        str(compile_script),
                        ip,
                        "--top",
                        top,
                        "--project-root",
                        str(stage_root),
                    ],
                )
                lint_rc = _run_tool("dut_lint", [_python_cmd(), str(lint_script), ip, "--top", top])

            blocked_path = ip_dir / "rtl" / "rtl_blocked.json"
            blocked_doc: dict[str, Any] = {}
            if blocked_path.is_file():
                try:
                    blocked_doc = json.loads(blocked_path.read_text(encoding="utf-8"))
                except Exception as exc:
                    blocked_doc = {"reason": f"rtl_blocked.json parse failed: {exc}", "questions": []}

            if blocked_doc:
                headline = "[SSOT QUESTION] rtl-gen BLOCKED"
            elif gen_rc == 0 and compile_rc == 0 and lint_rc == 0:
                headline = "[RTL RESULT] PASS - generated RTL and DUT-only compile/lint evidence"
            elif gen_rc == 0:
                headline = "[RTL RESULT] FAIL - generated RTL needs rtl-gen repair"
            else:
                headline = "[RTL BLOCKED] rtl-gen failed before producing approved evidence"

            parts = [
                headline,
                f"module: {ip}",
                f"top: {top}",
                f"source: {ip}/yaml/{ip}.ssot.yaml",
                f"generator: {script}",
            ]
            if blocked_doc:
                parts += [
                    f"blocker: {blocked_doc.get('reason') or 'SSOT decision required'}",
                    f"evidence: {ip}/rtl/rtl_blocked.json",
                    f"next: {blocked_doc.get('next_action') or 'answer SSOT questions and rerun /ssot-rtl'}",
                ]
                questions = blocked_doc.get("questions") if isinstance(blocked_doc.get("questions"), list) else []
                if questions:
                    parts.append("")
                    parts.append("questions:")
                    for q in questions:
                        if not isinstance(q, dict):
                            continue
                        parts.append(f"- {q.get('id')}: {q.get('decision_needed')}")
                        if q.get("recommended_default"):
                            parts.append(f"  recommended: {q.get('recommended_default')}")
            parts.append("")
            parts.append("runs:")
            for run in runs:
                parts.append(f"- {run['label']}: exit {run['returncode']}")
                parts.append(f"  cmd: {run['command']}")
                if run.get("stdout"):
                    parts.append("  stdout:")
                    parts.append(str(run["stdout"]))
                if run.get("stderr"):
                    parts.append("  stderr:")
                    parts.append(str(run["stderr"]))
            parts += [
                "",
                "artifacts:",
                f"- {ip}/yaml/{ip}.ssot.yaml",
                f"- {ip}/list/{ip}.f",
                f"- {ip}/rtl/rtl_compile.json",
                f"- {ip}/lint/dut_lint.json",
                f"- {ip}/rtl/rtl_blocked.json (only when SSOT decision is required)",
            ]
            if blocked_doc:
                parts.append("")
                parts.append("next: ATLAS opened an SSOT decision Q&A card for the RTL blocker.")
            elif gen_rc == 0 and compile_rc == 0 and lint_rc == 0:
                parts += [
                    "",
                    "next: run /tb, /sim, /sim-debug, and /goal-audit to prove FL-vs-RTL behavior.",
                ]
            elif gen_rc == 0:
                parts += [
                    "",
                    "next: queued rtl-gen repair with compile/lint diagnostics as evidence.",
                ]
            msg = "\n".join(parts)
            _append_session_message(session, "assistant", msg)
            _append_workflow_history("rtl-gen", "assistant", msg)
            _append_active_history("assistant", "```\n" + msg + "\n```")
            _emit_workflow_result(msg, alias)
            if blocked_doc:
                # rtl_blocked.json present → the SSOT message above already
                # surfaces the question. Stop here instead of opening a
                # parallel Q&A panel or auto-queuing a repair (the repair
                # path needs a clean SSOT to make sense).
                pass
            elif gen_rc == 0 and (compile_rc != 0 or lint_rc != 0):
                workflow = str(spec["workflow"])
                template = str(spec.get("template") or alias)
                _queue_prompt_for_session(client_session, "/mode normal")
                _queue_prompt_for_session(client_session, f"/wf {workflow}")
                _queue_prompt_for_session(client_session, "/clear")
                _queue_prompt_for_session(client_session, f"/todo template {template} {ip}")
                _queue_prompt_for_session(client_session,
                    f"Execute {alias} for {ip} from {ip}/yaml/{ip}.ssot.yaml. "
                    "The SSOT-driven RTL generator produced artifacts but compile/lint did not approve them. "
                    "Repair only the generated RTL against function_model, cycle_model, interfaces, "
                    "error_handling, and test_requirements. Then run the canonical DUT-only compile and "
                    "lint commands, repair diagnostics, and report exact artifact evidence. If new behavior "
                    "is still ambiguous, emit a precise "
                    "[SSOT QUESTION] and stop."
                )
            client_session.emit("agent_state", running=False)
            return True
        if alias == "ssot-equiv-goals":
            session = f"{ip}/fl-model-gen"
            fl_script = WORKFLOW_ROOT / "fl-model-gen" / "scripts" / "emit_fl_model.py"
            script = WORKFLOW_ROOT / "fl-model-gen" / "scripts" / "emit_equivalence_goals.py"
            _append_session_message(session, "user", text)
            _append_active_history("user", text)
            client_session.emit("agent_state", running=True)
            runs: list[dict[str, Any]] = []
            stage_root = _script_project_root(ip)

            def _run_local(label: str, cmdline: list[str], timeout_s: int = 60) -> int:
                try:
                    import subprocess

                    proc = subprocess.run(
                        cmdline,
                        cwd=str(stage_root),
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                        capture_output=True,
                        timeout=timeout_s,
                    )
                    runs.append({
                        "label": label,
                        "cmd": " ".join(cmdline),
                        "returncode": proc.returncode,
                        "stdout": (proc.stdout or "").strip()[:12000],
                        "stderr": (proc.stderr or "").strip()[:12000],
                    })
                    return int(proc.returncode)
                except Exception as exc:
                    runs.append({
                        "label": label,
                        "cmd": " ".join(cmdline),
                        "returncode": 999,
                        "stdout": "",
                        "stderr": str(exc),
                    })
                    return 999

            fl_rc = _run_local("emit_fl_model", [_python_cmd(), str(fl_script), ip, "--root", str(stage_root)])
            eq_rc = _run_local("emit_equivalence_goals", [_python_cmd(), str(script), ip, "--root", str(stage_root)]) if fl_rc == 0 else 999
            goals_path = ip_dir / "verify" / "equivalence_goals.json"
            goal_summary = ""
            if goals_path.is_file():
                try:
                    gdoc = json.loads(goals_path.read_text(encoding="utf-8"))
                    summary = gdoc.get("summary") if isinstance(gdoc, dict) else {}
                    if isinstance(summary, dict):
                        goal_summary = (
                            f"total={summary.get('total', 0)} "
                            f"required={summary.get('required', 0)} "
                            f"blocked={summary.get('blocked', 0)}"
                        )
                except Exception:
                    goal_summary = "unparseable equivalence_goals.json"
            headline = (
                "[ssot-equiv-goals] PASS"
                if eq_rc == 0 else
                "[ssot-equiv-goals] BLOCKED"
            )
            parts = [
                headline,
                f"script: {script}",
                f"module: {ip}",
                f"source: {ip}/yaml/{ip}.ssot.yaml",
                f"goals: {goal_summary or '(not generated)'}",
                "",
                "runs:",
            ]
            for run in runs:
                parts.append(f"- {run['label']}: exit {run['returncode']}")
                parts.append(f"  cmd: {run['cmd']}")
                if run["stdout"]:
                    parts.append("  stdout:")
                    parts.append(run["stdout"])
                if run["stderr"]:
                    parts.append("  stderr:")
                    parts.append(run["stderr"])
            parts += [
                "",
                "expected artifacts:",
                f"- {ip}/verify/equivalence_goals.json",
                f"- {ip}/model/functional_model.py",
                f"- {ip}/model/decomposition.json",
                f"- {ip}/cov/fcov_plan.json",
            ]
            if eq_rc != 0:
                parts.append("")
                parts.append("next: inspect blocked goals and answer/repair SSOT behavior before TB signoff")
            msg = "\n".join(parts)
            _append_session_message(session, "assistant", msg)
            _append_workflow_history("fl-model-gen", "assistant", msg)
            _append_active_history("assistant", "```\n" + msg + "\n```")
            _emit_workflow_result(msg, alias)
            client_session.emit("agent_state", running=False)
            return True
        if alias in {"ssot-tb", "ssot-tb-cocotb"}:
            canonical_alias = "ssot-tb-cocotb"
            session = f"{ip}/tb-gen"
            script = WORKFLOW_ROOT / "tb-gen" / "scripts" / "emit_goal_scoreboard_cocotb.py"
            validator = WORKFLOW_ROOT / "tb-gen" / "scripts" / "check_pyuvm_structure.sh"
            scoreboard = WORKFLOW_ROOT / "tb-gen" / "runtime" / "equivalence_scoreboard.py"
            _append_session_message(session, "user", text)
            _append_active_history("user", text)
            client_session.emit("agent_state", running=True)
            runs: list[dict[str, Any]] = []
            stage_root = _script_project_root(ip)

            def _run_tb_tool(label: str, command: list[str], timeout_s: int = 180) -> int:
                try:
                    import subprocess

                    proc = subprocess.run(
                        command,
                        cwd=str(stage_root),
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                        capture_output=True,
                        timeout=timeout_s,
                    )
                    runs.append({
                        "label": label,
                        "cmd": " ".join(command),
                        "returncode": proc.returncode,
                        "stdout": (proc.stdout or "").strip()[:12000],
                        "stderr": (proc.stderr or "").strip()[:12000],
                    })
                    return int(proc.returncode)
                except Exception as exc:
                    runs.append({
                        "label": label,
                        "cmd": " ".join(command),
                        "returncode": 999,
                        "stdout": "",
                        "stderr": str(exc),
                    })
                    return 999

            gen_rc = _run_tb_tool("emit_goal_scoreboard_cocotb", [_python_cmd(), str(script), ip, "--root", str(stage_root)])
            structure_rc: int | None = None
            self_check_rc: int | None = None
            if gen_rc == 0:
                structure_rc = _run_tb_tool("check_pyuvm_structure", ["bash", str(validator), ip])
                self_check_rc = _run_tb_tool(
                    "equivalence_scoreboard_self_check",
                    [_python_cmd(), str(scoreboard), ip, "--root", str(stage_root), "--self-check"],
                )

            blocked_path = ip_dir / "tb" / "cocotb" / "tb_blocked.json"
            blocked_doc: dict[str, Any] = {}
            if blocked_path.is_file():
                try:
                    loaded = json.loads(blocked_path.read_text(encoding="utf-8"))
                    blocked_doc = loaded if isinstance(loaded, dict) else {}
                except Exception as exc:
                    blocked_doc = {"reason": f"tb_blocked.json parse failed: {exc}", "questions": []}

            if blocked_doc or gen_rc == 2:
                headline = "[ssot-tb-cocotb] BLOCKED - SSOT/RTL contract needs repair"
            elif gen_rc == 0 and structure_rc == 0 and self_check_rc == 0:
                headline = "[ssot-tb-cocotb] PASS - generated goal-driven pyuvm/cocotb scoreboard"
            elif gen_rc == 0:
                headline = "[ssot-tb-cocotb] FAIL - generated TB needs tb-gen repair"
            else:
                headline = "[ssot-tb-cocotb] FAIL - generator did not produce approved TB artifacts"

            parts = [
                headline,
                f"module: {ip}",
                f"source: {ip}/yaml/{ip}.ssot.yaml",
                f"generator: {script}",
                f"validator: {validator}",
            ]
            if blocked_doc:
                parts += [
                    f"blocker: {blocked_doc.get('reason') or 'SSOT/RTL decision required'}",
                    f"evidence: {ip}/tb/cocotb/tb_blocked.json",
                    f"next: {blocked_doc.get('next_action') or 'repair SSOT/RTL contract and rerun /tb'}",
                ]
                questions = blocked_doc.get("questions") if isinstance(blocked_doc.get("questions"), list) else []
                if questions:
                    parts.append("")
                    parts.append("questions:")
                    for q in questions:
                        if not isinstance(q, dict):
                            continue
                        parts.append(f"- {q.get('id')}: {q.get('decision_needed')}")
                        if q.get("recommended_default"):
                            parts.append(f"  recommended: {q.get('recommended_default')}")
            parts += ["", "runs:"]
            for run in runs:
                parts.append(f"- {run['label']}: exit {run['returncode']}")
                parts.append(f"  cmd: {run['cmd']}")
                if run["stdout"]:
                    parts.append("  stdout:")
                    parts.append(run["stdout"])
                if run["stderr"]:
                    parts.append("  stderr:")
                    parts.append(run["stderr"])
            parts += [
                "",
                "expected artifacts:",
                f"- {ip}/tb/cocotb/test_{ip}.py",
                f"- {ip}/tb/cocotb/test_runner.py",
                f"- {ip}/tb/cocotb/tb_manifest.json",
                f"- {ip}/tb/cocotb/tb_generation.json",
                f"- {ip}/sim/scoreboard_events.jsonl after /sim",
                f"- {ip}/cov/coverage.json after /sim",
            ]
            if gen_rc == 0 and structure_rc == 0 and self_check_rc == 0:
                parts += [
                    "",
                    "next: run /sim, /sim-debug, and /goal-audit to collect FL-vs-RTL evidence.",
                ]
            elif gen_rc == 0:
                parts += [
                    "",
                    "next: queued tb-gen repair with structure/self-check diagnostics as evidence.",
                ]
            msg = "\n".join(parts)
            _append_session_message(session, "assistant", msg)
            _append_workflow_history("tb-gen", "assistant", msg)
            _append_active_history("assistant", "```\n" + msg + "\n```")
            _emit_workflow_result(msg, canonical_alias)
            if gen_rc == 0 and not (structure_rc == 0 and self_check_rc == 0):
                workflow = str(spec["workflow"])
                template = str(spec.get("template") or canonical_alias)
                _queue_prompt_for_session(client_session, "/mode normal")
                _queue_prompt_for_session(client_session, f"/wf {workflow}")
                _queue_prompt_for_session(client_session, "/clear")
                _queue_prompt_for_session(client_session, f"/todo template {template} {ip}")
                _queue_prompt_for_session(client_session,
                    f"Repair generated pyuvm/cocotb TB for {ip} using SSOT, FunctionalModel, "
                    "equivalence_goals.json, rtl_contract.json, and the validator output below. "
                    "Do not use fixed IP templates. Keep the TB goal-driven, instantiate "
                    "EquivalenceScoreboard, preserve all required scoreboard row fields, and rerun "
                    f"`bash {validator} {ip}` plus the scoreboard self-check before reporting DONE.\n\n"
                    "ATLAS direct-generation evidence:\n```text\n"
                    f"{msg}\n"
                    "```"
                )
                client_session.emit("agent_state", running=True)
            else:
                client_session.emit("agent_state", running=False)
            return True
        if alias == "sim-debug":
            session = f"{ip}/sim_debug"
            script = WORKFLOW_ROOT / "sim_debug" / "scripts" / "compare_fl_rtl_results.py"
            _append_session_message(session, "user", text)
            _append_active_history("user", text)
            client_session.emit("agent_state", running=True)
            try:
                import subprocess

                run = subprocess.run(
                    [_python_cmd(), str(script), ip, "--root", str(_script_project_root(ip))],
                    cwd=str(_script_project_root(ip)),
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    capture_output=True,
                    timeout=60,
                )
            except Exception as exc:
                msg = f"[sim-debug] failed: {exc}"
                _append_session_message(session, "assistant", msg)
                _append_active_history("assistant", "```\n" + msg + "\n```")
                _emit_workflow_result(msg, alias)
                client_session.emit("agent_state", running=False)
                return True

            compare_path = ip_dir / "sim" / "fl_rtl_compare.json"
            classify_path = ip_dir / "sim" / "mismatch_classification.json"
            summary_line = ""
            if compare_path.is_file():
                try:
                    cdoc = json.loads(compare_path.read_text(encoding="utf-8"))
                    summary = cdoc.get("summary") if isinstance(cdoc, dict) else {}
                    if isinstance(summary, dict):
                        summary_line = (
                            f"status={cdoc.get('status')} total={summary.get('total', 0)} "
                            f"checked={summary.get('goals_checked', 0)} passed={summary.get('goals_passed', 0)} "
                            f"failed={summary.get('goals_failed', 0)} blocked={summary.get('goals_blocked', 0)} "
                            f"untested={summary.get('goals_untested', 0)}"
                        )
                except Exception:
                    summary_line = "unparseable fl_rtl_compare.json"
            parts = [
                "[sim-debug] FL-vs-RTL compare",
                f"script: {script}",
                f"module: {ip}",
                f"exit: {run.returncode}",
                f"summary: {summary_line or '(not generated)'}",
            ]
            if run.stdout.strip():
                parts += ["", "stdout:", run.stdout.strip()]
            if run.stderr.strip():
                parts += ["", "stderr:", run.stderr.strip()]
            parts += [
                "",
                "expected artifacts:",
                f"- {ip}/sim/fl_rtl_compare.json",
                f"- {ip}/sim/mismatch_classification.json",
                f"- {ip}/sim/scoreboard_events.jsonl",
                f"- {ip}/verify/equivalence_goals.json",
            ]
            if run.returncode != 0 and classify_path.is_file():
                parts.append("")
                parts.append("next: repair classified owner or answer human-gate questions from mismatch_classification.json")
            msg = "\n".join(parts)
            _append_session_message(session, "assistant", msg)
            _append_workflow_history("sim_debug", "assistant", msg)
            _append_active_history("assistant", "```\n" + msg + "\n```")
            _emit_workflow_result(msg, alias)
            opened_human_gate = False
            if classify_path.is_file():
                try:
                    loaded = json.loads(classify_path.read_text(encoding="utf-8"))
                    classify_doc = loaded if isinstance(loaded, dict) else {}
                except Exception:
                    classify_doc = {}
                opened_human_gate = _start_sim_human_gate_qna(ip, classify_doc, reason="automatic /sim-debug", client_session=client_session)
                if opened_human_gate:
                    note = f"[sim-debug] opened ATLAS human-gate question(s) from {ip}/sim/mismatch_classification.json"
                    _append_session_message(session, "assistant", note)
                    _append_workflow_history("sim_debug", "assistant", note)
                    _append_active_history("assistant", "```\n" + note + "\n```")
                    client_session.emit("tool_result", text="```\n" + note + "\n```", tool=alias, truncated=False)
                    client_session.emit("slash_output", text="```\n" + note + "\n```")
                    client_session.emit("flush")
            if not opened_human_gate:
                client_session.emit("agent_state", running=False)
            return True
        if alias == "goal-audit":
            session = f"{ip}/goal-audit"
            script = WORKFLOW_ROOT / "sim_debug" / "scripts" / "audit_fl_rtl_equivalence_goal.py"
            _append_session_message(session, "user", text)
            _append_active_history("user", text)
            client_session.emit("agent_state", running=True)
            try:
                import subprocess

                run = subprocess.run(
                    [_python_cmd(), str(script), ip, "--root", str(_script_project_root(ip))],
                    cwd=str(_script_project_root(ip)),
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    capture_output=True,
                    timeout=60,
                )
            except Exception as exc:
                msg = f"[goal-audit] failed: {exc}"
                _append_session_message(session, "assistant", msg)
                _append_active_history("assistant", "```\n" + msg + "\n```")
                _emit_workflow_result(msg, alias)
                client_session.emit("agent_state", running=False)
                return True

            audit_path = ip_dir / "sim" / "fl_rtl_goal_audit.json"
            summary_line = ""
            blockers: list[str] = []
            if audit_path.is_file():
                try:
                    audit_doc = json.loads(audit_path.read_text(encoding="utf-8"))
                    summary = audit_doc.get("summary") if isinstance(audit_doc, dict) else {}
                    if isinstance(summary, dict):
                        blockers = [str(x) for x in summary.get("blockers") or []]
                        summary_line = (
                            f"status={audit_doc.get('status')} "
                            f"passed={summary.get('passed_checks', 0)}/{summary.get('total_checks', 0)} "
                            f"blockers={', '.join(blockers) if blockers else 'none'}"
                        )
                except Exception:
                    summary_line = "unparseable fl_rtl_goal_audit.json"
            headline = "[goal-audit] PASS" if run.returncode == 0 else "[goal-audit] FAIL"
            parts = [
                headline,
                f"script: {script}",
                f"module: {ip}",
                f"exit: {run.returncode}",
                f"summary: {summary_line or '(not generated)'}",
            ]
            if run.stdout.strip():
                parts += ["", "stdout:", run.stdout.strip()]
            if run.stderr.strip():
                parts += ["", "stderr:", run.stderr.strip()]
            parts += [
                "",
                "expected artifact:",
                f"- {ip}/sim/fl_rtl_goal_audit.json",
            ]
            if blockers:
                parts += ["", "blockers:"]
                parts += [f"- {blocker}" for blocker in blockers[:12]]
            if run.returncode != 0:
                parts += [
                    "",
                    "next: inspect fl_rtl_goal_audit.json and rerun the owning ATLAS stage; do not bypass with a fixed IP template.",
                ]
            msg = "\n".join(parts)
            _append_session_message(session, "assistant", msg)
            _append_workflow_history("sim_debug", "assistant", msg)
            _append_active_history("assistant", "```\n" + msg + "\n```")
            _emit_workflow_result(msg, alias)
            client_session.emit("agent_state", running=False)
            return True
        if alias == "ssot-fl-model":
            session = f"{ip}/fl-model-gen"
            script = WORKFLOW_ROOT / "fl-model-gen" / "scripts" / "emit_fl_model.py"
            _append_session_message(session, "user", text)
            _append_active_history("user", text)
            client_session.emit("agent_state", running=True)
            try:
                import subprocess

                run = subprocess.run(
                    [_python_cmd(), str(script), ip, "--root", str(_script_project_root(ip))],
                    cwd=str(_script_project_root(ip)),
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    capture_output=True,
                    timeout=60,
                )
            except Exception as exc:
                msg = f"[ssot-fl-model] failed: {exc}"
                _append_session_message(session, "assistant", msg)
                _append_active_history("assistant", "```\n" + msg + "\n```")
                _emit_workflow_result(msg, alias)
                client_session.emit("agent_state", running=False)
                return True

            parts = [
                "[ssot-fl-model] generic SSOT-driven FL model stage",
                f"script: {script}",
                f"module: {ip}",
                f"source: {ip}/yaml/{ip}.ssot.yaml",
                f"exit: {run.returncode}",
            ]
            if run.stdout.strip():
                parts += ["", "stdout:", run.stdout.strip()]
            if run.stderr.strip():
                parts += ["", "stderr:", run.stderr.strip()]
            parts += [
                "",
                "expected artifacts:",
                f"- {ip}/model/functional_model.py",
                f"- {ip}/model/decomposition.json",
                f"- {ip}/model/fl_model_check.json",
                f"- {ip}/cov/fcov_plan.json",
            ]
            msg = "\n".join(parts)
            _append_session_message(session, "assistant", msg)
            _append_workflow_history("fl-model-gen", "assistant", msg)
            _append_active_history("assistant", "```\n" + msg + "\n```")
            _emit_workflow_result(msg, alias)
            client_session.emit("agent_state", running=False)
            return True
        workflow = str(spec["workflow"])
        template = str(spec.get("template") or alias)
        session = f"{ip}/{workflow}"
        _append_session_message(session, "user", text)
        queued = (
            f"[{alias}] queued through workflow agent\n"
            f"workflow: {workflow}\n"
            f"template: {template}\n"
            f"module: {ip}\n"
            f"source: {ip}/yaml/{ip}.ssot.yaml\n"
            f"expected artifacts: {ip}/{spec['artifact_hint']}"
        )
        _append_session_message(session, "assistant", "```\n" + queued + "\n```")
        _append_active_history("user", text)
        _append_active_history("assistant", "```\n" + queued + "\n```")
        _queue_prompt_for_session(client_session, "/mode normal")
        _queue_prompt_for_session(client_session, f"/wf {workflow}")
        # Per-IP stage runs must not inherit stale workflow-level chat/todo
        # context from a previous IP. The concrete SSOT path and rerun prompt
        # below re-establish the only context the worker should use.
        _queue_prompt_for_session(client_session, "/clear")
        _queue_prompt_for_session(client_session, f"/todo template {template} {ip}")
        _queue_prompt_for_session(client_session,
            f"Execute {alias} for {ip} from {ip}/yaml/{ip}.ssot.yaml. "
            "Use the workflow todo detail/criteria. Do not use fixed IP templates; "
            "derive implementation from SSOT and verify with real commands. "
            "After reading the SSOT, keep the ledger bounded and move to "
            "write_file/replace_in_file/run_command; do not loop on architecture "
            "debate before producing artifacts. Do not publish the ledger as a long "
            "chat answer; if work remains, the next response must start with an "
            "Action line. Use small action chunks: one file or one validation command "
            "per response, prefer dependency/leaf files before the top wrapper, and "
            "split any file that would exceed about 180 lines into replace_in_file "
            "or replace_lines follow-up actions."
        )
        client_session.emit("agent_state", running=True)
        _emit_workflow_result(queued, alias)
        client_session.emit("agent_state", running=True)
        return True
    return {
        "_handle_bang_shell_command": _handle_bang_shell_command,
        "_handle_import_command": _handle_import_command,
        "_handle_grill_me_command": _handle_grill_me_command,
        "_handle_new_ip_command": _handle_new_ip_command,
        "_handle_ip_command": _handle_ip_command,
        "_handle_session_command": _handle_session_command,
        "_handle_approval_command": _handle_approval_command,
        "_handle_refresh_wiki_command": _handle_refresh_wiki_command,
        "_handle_to_ssot_gate": _handle_to_ssot_gate,
        "_handle_repair_ssot_command": _handle_repair_ssot_command,
        "_handle_verify_ssot_command": _handle_verify_ssot_command,
        "_handle_repair_rtl_command": _handle_repair_rtl_command,
        "_handle_repair_equiv_command": _handle_repair_equiv_command,
        "_run_stage_command": _run_stage_command,
    }
