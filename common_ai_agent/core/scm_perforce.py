"""Deployment-specific Perforce (Helix Core) SCM adapter for Atlas.

This is the real p4 implementation that the built-in ``core.scm.PerforceSCMAdapter``
stub intentionally leaves out. It is wired in via the documented override hook
(``ATLAS_SCM_ADAPTER_PERFORCE=core.scm_perforce:PerforceP4Adapter``) so the core
contract test that asserts the stub stays unimplemented keeps passing.

Connection/workspace are resolved by p4 itself (P4CONFIG/.p4config or env), set up
by ``scripts/perforce_setup.sh``. The adapter root is the Perforce workspace
root; UI calls may pass a separate local IP root for the left pane.
"""
from __future__ import annotations

import filecmp
import json
import os
import re
import shutil
import subprocess
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Final

from .scm import (
    DEFAULT_TIMEOUT_SEC,
    SCMAdapter,
    SCMCommandResult,
    SCMCommit,
    SCMFileStatus,
)
from .scm_perforce_browse import (
    DEPOT_BROWSE_LIMIT,
    depot_file_entries,
    depot_folder_entries,
    local_entries,
    merge_depot_entries,
    pane_browse_scope,
)

# Non-zero p4 exits that just mean "nothing here", not a real failure.
_BENIGN = (
    "up-to-date",
    "no such file",
    "not opened",
    "no file(s) to reconcile",
    "not in client view",
    "file(s) not on client",
    "no file(s) to resolve",
    "empty, assuming text",
)
_LOCAL_SCAN_SKIP_DIRS: Final[frozenset[str]] = frozenset({
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "node_modules",
})
_LOCAL_SCAN_SKIP_FILES: Final[frozenset[str]] = frozenset({".DS_Store"})
_ATLAS_SOURCE_MAP: Final[str] = ".atlas/p4_source_map.json"
_RECONCILE_LOCAL_STATES: Final[Mapping[str, str]] = {
    "add": "new",
    "edit": "modified",
    "delete": "missing",
    "move/add": "new",
    "move/delete": "missing",
}
_STREAM_NAME_RE: Final[re.Pattern[str]] = re.compile(r"^//[A-Za-z0-9_.-]+/[A-Za-z0-9_./-]+$")
# A failed `p4 submit -d … <filespec>` first moves the default-changelist files
# into a fresh numbered changelist; these patterns recover its number so the
# adapter can move the files back instead of stranding the changelist.
_SUBMIT_FAILED_CHANGE_RES: Final[tuple[re.Pattern[str], ...]] = (
    re.compile(r"Submitting change (\d+)"),
    re.compile(r"p4 submit -c (\d+)"),
)
_CLIENT_ENV_VARS: Final[tuple[str, ...]] = (
    "ATLAS_SCM_CLIENT_PERFORCE",
    "ATLAS_PERFORCE_CLIENT",
    "ATLAS_P4CLIENT",
    "P4CLIENT",
)
_PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[1]


class PerforceP4Adapter(SCMAdapter):
    provider: str = "perforce"

    def __init__(self, root: str | Path, executable: str = "p4") -> None:
        super().__init__(root, executable=executable)
        self._info_cache: dict[str, str] | None = None
        self._selected_stream: str = ""
        self._selected_client: str = ""

    # ------------------------------------------------------------------ caps
    def capabilities(self) -> dict[str, bool]:
        caps = super().capabilities()
        caps.update({
            "status": True,
            "diff": True,
            "log": True,
            "show": True,
            "submit": True,
            "push": True,
            "graph": False,
            "hard_reset": True,
            "sync": True,
        })
        return caps

    # --------------------------------------------------------------- runners
    def _run_p4(
        self,
        *args: str,
        timeout: int = DEFAULT_TIMEOUT_SEC,
        input_text: str = "",
    ) -> SCMCommandResult:
        selected_client = self._configured_client()
        client_args = ("-c", selected_client) if selected_client else ()
        command = (self.executable, *client_args, "-d", str(self.root), *args)
        try:
            completed = subprocess.run(
                list(command),
                input=input_text if input_text else None,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                check=False,
            )
            return self._result(
                ok=completed.returncode == 0,
                stdout=completed.stdout,
                stderr=completed.stderr,
                returncode=completed.returncode,
                error="" if completed.returncode == 0 else completed.stderr.strip(),
                command=command,
            )
        except subprocess.TimeoutExpired:
            return self._result(ok=False, returncode=124, error=f"p4 command timed out after {timeout}s", command=command)
        except FileNotFoundError:
            return self._result(ok=False, returncode=127, error="p4 executable not found", command=command)

    def _records(self, *args: str, timeout: int = DEFAULT_TIMEOUT_SEC) -> tuple[list[dict[str, str]], SCMCommandResult]:
        """Run ``p4 -ztag <args>`` and parse the tagged output into dicts."""
        result = self._run_p4("-ztag", *args, timeout=timeout)
        records: list[dict[str, str]] = []
        cur: dict[str, str] = {}
        last_key = ""
        for line in result.stdout.split("\n"):
            if line == "":
                if cur:
                    records.append(cur)
                    cur = {}
                    last_key = ""
                continue
            if line.startswith("... "):
                rest = line[4:]
                sp = rest.find(" ")
                if sp == -1:
                    key, val = rest, ""
                else:
                    key, val = rest[:sp], rest[sp + 1:]
                cur[key] = val
                last_key = key
            elif cur and last_key:  # continuation of a multi-line value
                cur[last_key] += "\n" + line
        if cur:
            records.append(cur)
        return records, result

    @staticmethod
    def _soften(result: SCMCommandResult) -> SCMCommandResult:
        if result.ok:
            return result
        low = f"{result.stderr} {result.error}".lower()
        if any(b in low for b in _BENIGN):
            return SCMCommandResult(
                ok=True,
                provider=result.provider,
                root=result.root,
                stdout=result.stdout or result.stderr.strip(),
                stderr=result.stderr,
                returncode=0,
                command=result.command,
            )
        return result

    # --------------------------------------------------------------- helpers
    def _info(self) -> dict[str, str]:
        if self._info_cache is None:
            recs, _ = self._records("info", timeout=5)
            self._info_cache = recs[0] if recs else {}
        return self._info_cache

    def _client_root(self) -> Path | None:
        root = self._info().get("clientRoot", "")
        if not root:
            return None
        try:
            return Path(root).resolve()
        except Exception:
            return None

    def _workspace_root_path(self) -> Path:
        root = self._info().get("clientRoot", "")
        if root:
            return Path(root)
        return self.root

    def _workspace_filespec(self, path: Path) -> str | None:
        base = self._workspace_root_path()
        try:
            rel = path.resolve().relative_to(base.resolve())
        except (OSError, RuntimeError, ValueError):
            return None
        # Perforce compares local files against the literal client Root. On
        # macOS, resolving /tmp to /private/tmp makes p4 reject valid files.
        return (base / rel).as_posix()

    def _workspace_scope(self) -> str:
        return f"{self._workspace_root_path().as_posix()}/..."

    def _is_client_root(self) -> bool:
        cr = self._client_root()
        return cr is not None and cr == self.root

    def _branch(self) -> str:
        info = self._info()
        return info.get("clientStream") or info.get("clientName") or ""

    @staticmethod
    def _client_for_stream(stream: str) -> str:
        body = stream.strip().rstrip("/").rsplit("/", 1)[-1]
        body = re.sub(r"[^A-Za-z0-9_.-]+", "_", body).strip("_")
        return f"atlas_{body}" if body else "atlas_GOOD_IP"

    @staticmethod
    def _client_override_from_mapping(values: Mapping[str, str]) -> str:
        for name in _CLIENT_ENV_VARS:
            value = values.get(name, "").strip()
            if value:
                return value
        return ""

    @staticmethod
    def _env_client_override() -> str:
        return PerforceP4Adapter._client_override_from_mapping(os.environ)

    @staticmethod
    def _dotenv_assignment(line: str) -> tuple[str, str] | None:
        raw = line.strip()
        if not raw or raw.startswith("#") or "=" not in raw:
            return None
        if raw.startswith("export "):
            raw = raw[7:].strip()
        key, value = raw.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] in ("'", '"') and value[-1] == value[0]:
            value = value[1:-1]
        elif "#" in value:
            value = value.split("#", 1)[0].strip()
        if not key:
            return None
        return key, value

    def _dotenv_paths(self) -> tuple[Path, ...]:
        return (
            Path.cwd() / ".env",
            _PROJECT_ROOT / ".env",
            self.root / ".env",
        )

    def _dotenv_client_override(self) -> str:
        seen: set[Path] = set()
        for env_path in self._dotenv_paths():
            path = env_path.resolve(strict=False)
            if path in seen:
                continue
            seen.add(path)
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except OSError:
                continue
            values: dict[str, str] = {}
            for line in lines:
                parsed = self._dotenv_assignment(line)
                if parsed is None:
                    continue
                key, value = parsed
                values[key] = value
            client = self._client_override_from_mapping(values)
            if client:
                return client
        return ""

    def _configured_client(self) -> str:
        return self._env_client_override() or self._dotenv_client_override() or self._selected_client

    def _select_stream(self, stream: str = "") -> None:
        clean = str(stream or "").strip()
        if not clean:
            return
        if not _STREAM_NAME_RE.fullmatch(clean):
            return
        if clean == self._selected_stream:
            return
        self._selected_stream = clean
        self._selected_client = self._client_for_stream(clean)
        self._info_cache = None

    def _streams(self) -> list[str]:
        branch = self._selected_stream or self._branch()
        parts = branch.split("/")
        pattern = f"//{parts[2]}/..." if len(parts) > 3 and parts[2] else "//..."
        recs, result = self._records("streams", pattern, timeout=10)
        if not self._soften(result).ok:
            return [branch] if branch else []
        streams = sorted({rec.get("Stream", "") for rec in recs if rec.get("Stream", "")})
        if branch and branch not in streams:
            streams.insert(0, branch)
        return streams

    def _latest_change(self) -> str:
        recs, _ = self._records("changes", "-m", "1", "-s", "submitted", self._perforce_scope())
        return recs[0].get("change", "") if recs else ""

    def _perforce_scope(self) -> str:
        branch = self._selected_stream or self._branch()
        if branch.startswith("//"):
            return f"{branch.rstrip('/')}/..."
        return self._workspace_scope()

    def _local_root_path(self, local_root: str | Path | None = None) -> Path:
        if local_root is None or str(local_root or "").strip() == "":
            return self.root
        return Path(local_root).resolve()

    def _rel(self, p: str, local_root: str | Path | None = None) -> str:
        if not p:
            return p
        base = self._local_root_path(local_root)
        if p.startswith("//"):
            parts = p.strip("/").split("/")
            try:
                idx = parts.index(base.name)
            except ValueError:
                return p
            return "/".join(parts[idx + 1:])
        try:
            return str(Path(p).resolve().relative_to(base))
        except Exception:
            try:
                return str(Path(p).resolve().relative_to(self.root))
            except Exception:
                return p

    def _safe_filespecs(self, paths: Any) -> list[str]:
        """Resolve UI-supplied paths to absolute local filespecs inside root."""
        out: list[str] = []
        base = self._workspace_root_path()
        if not paths:
            return out
        if isinstance(paths, str):
            paths = [paths]
        for raw in paths:
            text = str(raw or "").strip()
            if not text:
                continue
            if text.startswith("//"):
                text = self._rel(text)
            cand = Path(text)
            if not cand.is_absolute():
                cand = base / text
            filespec = self._workspace_filespec(cand)
            if filespec is None:
                continue
            out.append(filespec)
        return out

    def _filespecs_for_perforce_selection(self, paths: Any) -> list[str]:
        out: list[str] = []
        if not paths:
            return out
        values = [paths] if isinstance(paths, str) else paths
        for raw in values:
            text = str(raw or "").strip()
            if not text:
                continue
            if text.startswith("//"):
                out.append(text)
                continue
            out.extend(self._safe_filespecs([text]))
        return out

    def _safe_local_paths(self, paths: Any, local_root: str | Path | None = None) -> list[Path]:
        out: list[Path] = []
        base = self._local_root_path(local_root)
        if not paths:
            return out
        values = [paths] if isinstance(paths, str) else paths
        for raw in values:
            text = str(raw or "").strip()
            if not text or text.startswith("//"):
                continue
            cand = Path(text)
            if not cand.is_absolute():
                cand = base / text
            try:
                resolved = cand.resolve()
                resolved.relative_to(base)
            except (OSError, RuntimeError, ValueError):
                continue
            out.append(resolved)
        return out

    def _depot_output_rel(self, depot_file: str, local_root: str | Path | None = None) -> str:
        clean = str(depot_file or "").strip()
        base = self._local_root_path(local_root)
        for marker in ("#", "@"):
            pos = clean.find(marker)
            if pos >= 0:
                clean = clean[:pos]
                break
        parts = [part for part in clean.strip("/").split("/") if part]
        if not parts:
            return ""
        try:
            root_idx = parts.index(base.name)
            rest = parts[root_idx + 1:]
            if rest:
                return "/".join(rest)
        except ValueError:
            pass
        stream_parts = [part for part in self._selected_stream.strip("/").split("/") if part]
        if stream_parts and parts[:len(stream_parts)] == stream_parts:
            return "/".join(parts[len(stream_parts):])
        if len(parts) > 2:
            return "/".join(parts[2:])
        return parts[-1]

    def _output_path_from_target(
        self,
        target: str,
        local_root: str | Path | None = None,
        source_name: str = "",
    ) -> Path | None:
        text = str(target or "").strip()
        if not text:
            return None
        base = self._local_root_path(local_root)
        is_folder_target = text.endswith("/")
        if text.startswith("//"):
            rel = self._depot_output_rel(text, base)
            cand = base / rel
        else:
            cand = Path(text)
            if not cand.is_absolute():
                cand = base / text
        if is_folder_target and source_name:
            cand = cand / source_name
        try:
            resolved = cand.resolve()
            resolved.relative_to(base)
        except (OSError, RuntimeError, ValueError):
            return None
        return resolved

    def _depot_output_path(self, depot_file: str, local_root: str | Path | None = None) -> Path | None:
        base = self._local_root_path(local_root)
        rel = self._depot_output_rel(depot_file, base)
        if not rel:
            return None
        try:
            resolved = (base / rel).resolve()
            resolved.relative_to(base)
        except (OSError, RuntimeError, ValueError):
            return None
        return resolved

    def _client_file_rel(self, client_file: str) -> Path | None:
        text = str(client_file or "").strip()
        if not text:
            return None
        if text.startswith("//"):
            parts = [part for part in text.strip("/").split("/") if part]
            if len(parts) < 2:
                return None
            configured = self._configured_client() or self._info().get("clientName", "")
            if configured and parts[0] != configured:
                return None
            return Path(*parts[1:])
        try:
            return Path(text).resolve().relative_to(self._workspace_root_path().resolve())
        except (OSError, RuntimeError, ValueError):
            return None

    def _workspace_path_from_client_file(self, client_file: str) -> Path | None:
        rel = self._client_file_rel(client_file)
        if rel is None:
            return None
        filespec = self._workspace_filespec(self._workspace_root_path() / rel)
        return Path(filespec) if filespec is not None else None

    def _copy_depot_to_local(
        self,
        depot_spec: str,
        output_from: str,
        local_root: str | Path | None = None,
        target_path: str = "",
    ) -> SCMCommandResult:
        rel = self._depot_output_rel(output_from, local_root)
        source_name = Path(rel).name if rel else ""
        output = (
            self._output_path_from_target(target_path, local_root, source_name)
            if target_path
            else self._depot_output_path(output_from, local_root)
        )
        if output is None:
            return self._result(ok=False, returncode=2, error=f"cannot map depot path to local root: {output_from}")
        try:
            output.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            return self._result(ok=False, returncode=1, error=str(exc))
        return self._soften(self._run_p4("print", "-q", "-o", output.as_posix(), depot_spec))

    def _target_values(self, target_paths: Any) -> list[str]:
        if not target_paths:
            return []
        values = [target_paths] if isinstance(target_paths, str) else target_paths
        return [str(value or "").strip() for value in values if str(value or "").strip()]

    def _source_map_path(self) -> Path:
        return self._workspace_root_path() / _ATLAS_SOURCE_MAP

    def _load_source_map(self) -> dict[str, Any]:
        path = self._source_map_path()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"sources": {}}
        if not isinstance(data, dict):
            return {"sources": {}}
        sources = data.get("sources")
        if not isinstance(sources, dict):
            data["sources"] = {}
        return data

    def _save_source_map(self, data: dict[str, Any]) -> None:
        path = self._source_map_path()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        except OSError:
            pass

    def _depot_file_for_target(self, target_value: str, target: Path, source: Path) -> str:
        text = str(target_value or "").strip()
        if text.startswith("//"):
            if not text.endswith("/"):
                return self._clean_depot_key(text)
            return self._clean_depot_key(f"{text.rstrip('/')}/{source.name}")
        recs, result = self._records("fstat", "-T", "depotFile", target.as_posix(), timeout=10)
        if self._soften(result).ok and recs:
            return self._clean_depot_key(recs[0].get("depotFile", ""))
        return ""

    def _remember_local_source_mapping(
        self,
        depot_file: str,
        source: Path,
        local_root: str | Path | None,
    ) -> None:
        if local_root is None or not depot_file:
            return
        base = self._local_root_path(local_root)
        try:
            rel = source.resolve().relative_to(base)
        except (OSError, RuntimeError, ValueError):
            return
        data = self._load_source_map()
        sources = data.setdefault("sources", {})
        if isinstance(sources, dict):
            sources[self._clean_depot_key(depot_file)] = {
                "localRoot": base.as_posix(),
                "relativePath": rel.as_posix(),
            }
        self._save_source_map(data)

    def _mapped_local_source(self, depot_file: str, local_root: str | Path | None) -> Path | None:
        if local_root is None or not depot_file:
            return None
        data = self._load_source_map()
        sources = data.get("sources")
        if not isinstance(sources, dict):
            return None
        entry = sources.get(self._clean_depot_key(depot_file))
        if not isinstance(entry, dict):
            return None
        rel = str(entry.get("relativePath") or "").strip()
        if not rel:
            return None
        base = self._local_root_path(local_root)
        try:
            source = (base / rel).resolve()
            source.relative_to(base)
        except (OSError, RuntimeError, ValueError):
            return None
        return source

    def _drop_local_source_mappings(self, depot_files: list[str]) -> None:
        clean = {self._clean_depot_key(item) for item in depot_files if item}
        if not clean:
            return
        data = self._load_source_map()
        sources = data.get("sources")
        if not isinstance(sources, dict):
            return
        for depot_file in clean:
            sources.pop(depot_file, None)
        self._save_source_map(data)

    def _client_path_for_depot(self, depot_file: str) -> Path | None:
        base = self._workspace_root_path()
        recs, result = self._records("fstat", "-T", "clientFile", depot_file, timeout=10)
        if self._soften(result).ok and recs and recs[0].get("clientFile"):
            mapped = self._workspace_path_from_client_file(recs[0]["clientFile"])
            if mapped is not None:
                return mapped
        rel = self._depot_output_rel(depot_file)
        if not rel:
            return None
        filespec = self._workspace_filespec(base / rel)
        if filespec is None:
            return None
        return Path(filespec)

    def _ip_mirror_target(
        self,
        base: Path,
        source: Path,
        originals: list[Any],
        idx: int,
        local_root: str | Path | None,
    ) -> Path:
        """1:1 mirror of a local IP file under the workspace root:
        <workspace>/<ip>/<relative path> (the documented depot mapping)."""
        raw = str(originals[idx]) if idx < len(originals) else source.name
        rel = Path(raw)
        if raw.startswith("//") or rel.is_absolute():
            try:
                rel = source.resolve().relative_to(self._local_root_path(local_root))
            except (OSError, RuntimeError, ValueError):
                rel = Path(source.name)
        ip_name = Path(local_root).resolve().name if local_root is not None else ""
        return (base / ip_name / rel) if ip_name else (base / rel)

    def _workspace_targets_for_sources(
        self,
        sources: list[Path],
        original_paths: Any,
        target_paths: Any,
        local_root: str | Path | None = None,
    ) -> list[Path]:
        base = self._workspace_root_path()
        targets = self._target_values(target_paths)
        originals = [original_paths] if isinstance(original_paths, str) else list(original_paths or [])
        stream_root = (self._selected_stream or self._branch()).rstrip("/")
        out: list[Path] = []
        for idx, source in enumerate(sources):
            if idx < len(targets):
                target_text = targets[idx]
            elif len(targets) == 1 and targets[0].endswith("/"):
                target_text = targets[0]
            else:
                target_text = ""
            if target_text.startswith("//"):
                if target_text.endswith("/"):
                    # The UI's default target is the depot pane's current folder,
                    # which starts at the stream root. That folder IS the
                    # workspace root (rel would be empty/garbage), so mirror the
                    # IP 1:1 instead of dropping basenames at the root.
                    if stream_root and target_text.rstrip("/") == stream_root:
                        target = self._ip_mirror_target(base, source, originals, idx, local_root)
                    else:
                        rel = self._depot_output_rel(target_text)
                        if rel:
                            target = base / rel / source.name
                        else:
                            target = self._ip_mirror_target(base, source, originals, idx, local_root)
                else:
                    target = self._client_path_for_depot(target_text)
            elif target_text:
                cand = Path(target_text)
                target = cand if cand.is_absolute() else base / target_text
            else:
                raw = str(originals[idx] if idx < len(originals) else source.name)
                cand = Path(raw)
                target = cand if cand.is_absolute() else base / raw
            if target is None:
                continue
            filespec = self._workspace_filespec(target)
            if filespec is None:
                continue
            out.append(Path(filespec))
        return out

    def _combine_results(self, results: list[SCMCommandResult]) -> SCMCommandResult:
        if not results:
            return self._result(ok=True)
        if len(results) == 1:
            return results[0]
        failures = [result for result in results if not result.ok]
        stdout = "\n".join(result.stdout.strip() for result in results if result.stdout.strip())
        stderr = "\n".join(result.stderr.strip() for result in results if result.stderr.strip())
        command = next((result.command for result in failures if result.command), ())
        if not command:
            command = next((result.command for result in reversed(results) if result.command), ())
        if failures:
            first = failures[0]
            return self._result(
                ok=False, stdout=stdout, stderr=stderr,
                returncode=first.returncode, error=first.error or first.stderr.strip(), command=command,
            )
        return self._result(ok=True, stdout=stdout, stderr=stderr, command=command)

    @staticmethod
    def _pending_changelist_id(changelist: str = "") -> str:
        clean = str(changelist or "").strip()
        if not clean or clean.lower() == "default":
            return ""
        return clean if clean.isdigit() else ""

    def _move_to_changelist(self, changelist: str, specs: list[str]) -> SCMCommandResult:
        target = self._pending_changelist_id(changelist)
        if not target or not specs:
            return self._result(ok=True)
        return self._soften(self._run_p4("reopen", "-c", target, *specs))

    def _depot_file_state(self, spec: str) -> tuple[bool, int]:
        """(file exists at depot head and is not deleted, client have revision)."""
        recs, _ = self._records("fstat", "-T", "depotFile,headAction,haveRev", spec, timeout=10)
        if not recs:
            return False, 0
        rec = recs[0]
        head_action = rec.get("headAction", "")
        exists = bool(head_action) and not head_action.endswith("delete")
        try:
            have = int(rec.get("haveRev", "") or 0)
        except ValueError:
            have = 0
        return exists, have

    def _open_for_edit(self, *specs: str) -> SCMCommandResult:
        """p4 edit with write intent: never softened — a checkout that opens
        nothing must fail loudly. A 'not on client' (have=0) failure is
        recovered by force-syncing the specs and retrying once."""
        result = self._run_p4("edit", *specs)
        # p4 may exit 0 while only warning "file(s) not on client." on stderr —
        # the file is then NOT opened, so gate the retry on the message, not rc.
        low = f"{result.stderr} {result.error}".lower()
        if "not on client" in low:
            synced = self._soften(self._run_p4("sync", "-f", *specs))
            if not synced.ok:
                return synced
            return self._run_p4("edit", *specs)
        return result

    @staticmethod
    def _stranded_submit_change(result: SCMCommandResult) -> str:
        text = f"{result.stdout}\n{result.stderr}\n{result.error}"
        for pattern in _SUBMIT_FAILED_CHANGE_RES:
            match = pattern.search(text)
            if match:
                return match.group(1)
        return ""

    def _restore_failed_submit_to_default(self, change: str) -> None:
        """Move files a failed default-changelist submit stranded in the
        auto-created numbered changelist back to default, then drop the empty
        shell so the pending changelist list does not accumulate junk."""
        opened, _ = self._records("opened", "-c", change)
        files = [rec.get("clientFile") or rec.get("depotFile", "") for rec in opened]
        files = [item for item in files if item]
        if files:
            self._soften(self._run_p4("reopen", "-c", "default", *files))
        self._soften(self._run_p4("change", "-d", change))

    @staticmethod
    def _clean_depot_key(value: str) -> str:
        clean = str(value or "").strip()
        for marker in ("#", "@"):
            idx = clean.find(marker)
            if idx >= 0:
                clean = clean[:idx]
                break
        return clean.rstrip("/")

    def _restage_local_submit_paths(
        self,
        opened: list[dict[str, str]],
        local_root: str | Path | None = None,
        paths: Any = None,
    ) -> SCMCommandResult:
        if local_root is None:
            return self._result(ok=True)
        requested = {
            self._clean_depot_key(str(path))
            for path in ([paths] if isinstance(paths, str) else list(paths or []))
            if str(path or "").strip()
        }
        matched: set[str] = set()
        copied: list[str] = []
        diagnostics: list[str] = []
        for rec in opened:
            action = rec.get("action", "")
            depot_file = self._clean_depot_key(rec.get("depotFile", ""))
            if requested and depot_file not in requested:
                continue
            if depot_file:
                matched.add(depot_file)
            if action.endswith("delete"):
                continue
            source = self._mapped_local_source(depot_file, local_root)
            client_file = rec.get("clientFile", "")
            client_rel = self._client_file_rel(client_file)
            if source is None and client_rel is not None:
                try:
                    source = (self._local_root_path(local_root) / client_rel).resolve()
                except (OSError, RuntimeError, ValueError):
                    source = None
            if source is None:
                source = self._depot_output_path(depot_file, local_root)
            if source is None or not source.is_file():
                diagnostics.append(
                    f"restage skipped: local source not found for {depot_file or client_file} "
                    f"under {self._local_root_path(local_root)}"
                )
                continue
            target = self._workspace_path_from_client_file(client_file) if client_file else None
            if target is None:
                target = self._client_path_for_depot(depot_file)
            if target is None:
                return self._result(ok=False, returncode=2, error=f"cannot map opened file to workspace path: {depot_file}")
            try:
                if source.resolve() == target.resolve():
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                if target.exists() and filecmp.cmp(source, target, shallow=False):
                    continue
                shutil.copy2(source, target)
                copied.append(depot_file or target.as_posix())
            except OSError as exc:
                return self._result(ok=False, returncode=1, error=str(exc))
        if requested:
            missing = sorted(path for path in requested - matched if path)
            if missing:
                stdout = "\n".join(diagnostics)
                return self._result(
                    ok=False,
                    stdout=stdout,
                    returncode=2,
                    error="selected submit path is not opened in this changelist: " + ", ".join(missing),
                )
        stdout = "\n".join([*(f"restaged local edit: {path}" for path in copied), *diagnostics])
        return self._result(ok=True, stdout=stdout)

    @staticmethod
    def _opened_depot_specs(opened: list[dict[str, str]]) -> list[str]:
        specs: list[str] = []
        for rec in opened:
            depot_file = PerforceP4Adapter._clean_depot_key(rec.get("depotFile", ""))
            if depot_file:
                specs.append(depot_file)
        return specs

    def _pending_resolve(self, specs: list[str]) -> tuple[bool, SCMCommandResult]:
        preview = self._run_p4("resolve", "-n", *(specs or [self._perforce_scope()]))
        checked = self._soften(preview)
        text = f"{preview.stdout}\n{preview.stderr}\n{preview.error}".strip()
        low = text.lower()
        pending = checked.ok and bool(text) and "no file(s) to resolve" not in low
        return pending, preview

    def _resolve_required_result(self, preview: SCMCommandResult, action: str) -> SCMCommandResult:
        text = "\n".join(part.strip() for part in (preview.stdout, preview.stderr, preview.error) if part.strip())
        return self._result(
            ok=False,
            stdout=text,
            stderr=preview.stderr,
            returncode=3,
            command=preview.command,
            error=(
                f"Perforce resolve required before {action}. "
                "Resolve the file in P4, or use Revert to discard the pending workspace edit."
            ),
        )

    def _out_of_date_opened(self, opened: list[dict[str, str]]) -> SCMCommandResult:
        specs = self._opened_depot_specs(opened)
        if not specs:
            return self._result(ok=True)
        recs, result = self._records("fstat", "-T", "depotFile,haveRev,headRev,headAction", *specs, timeout=10)
        checked = self._soften(result)
        if not checked.ok:
            return checked
        stale: list[str] = []
        for rec in recs:
            head_action = rec.get("headAction", "")
            if head_action.endswith("delete"):
                continue
            try:
                have = int(rec.get("haveRev", "") or 0)
                head = int(rec.get("headRev", "") or 0)
            except ValueError:
                continue
            if have > 0 and head > have:
                stale.append(f"{rec.get('depotFile', '')} haveRev={have} headRev={head}")
        if not stale:
            return self._result(ok=True)
        return self._result(
            ok=False,
            stdout="\n".join(stale),
            returncode=3,
            command=result.command,
            error=(
                "Perforce resolve required before submit. "
                "Opened file is out of date; sync/resolve it in P4, or use Revert to discard the pending workspace edit."
            ),
        )

    def _submit_resolve_preflight(self, opened: list[dict[str, str]]) -> SCMCommandResult:
        out_of_date = self._out_of_date_opened(opened)
        if not out_of_date.ok:
            return out_of_date
        resolve_pending, resolve_preview = self._pending_resolve(self._opened_depot_specs(opened))
        if resolve_pending:
            return self._resolve_required_result(resolve_preview, "submit")
        return self._result(ok=True)

    def _delete_emptied_changelists(self, changes: set[str]) -> None:
        for change in sorted(changes):
            remaining, _ = self._records("opened", "-c", change)
            if not remaining:
                self._soften(self._run_p4("change", "-d", change))

    @staticmethod
    def _change_form_with_description(form: str, message: str) -> str:
        clean = (message or "atlas: submit").strip() or "atlas: submit"
        description = ["Description:", *[f"\t{line}" for line in clean.splitlines()], ""]
        lines = form.splitlines()
        start = -1
        for idx, line in enumerate(lines):
            if line == "Description:":
                start = idx
                break
        if start < 0:
            insert_at = len(lines)
            for idx, line in enumerate(lines):
                if line == "Files:":
                    insert_at = idx
                    break
            return "\n".join([*lines[:insert_at], *description, *lines[insert_at:]]).rstrip() + "\n"
        end = start + 1
        while end < len(lines):
            line = lines[end]
            if line and not line.startswith((" ", "\t")) and line.endswith(":"):
                break
            end += 1
        return "\n".join([*lines[:start], *description, *lines[end:]]).rstrip() + "\n"

    def _update_pending_changelist_description(self, changelist: str, message: str) -> SCMCommandResult:
        form = self._run_p4("change", "-o", changelist)
        if not form.ok:
            return form
        updated = self._change_form_with_description(form.stdout, message)
        return self._run_p4("change", "-i", input_text=updated)

    def _pending_changes(self) -> tuple[list[dict[str, str]], SCMCommandResult]:
        args = ["changes", "-s", "pending"]
        client = self._info().get("clientName", "")
        if client:
            args.extend(["-c", client])
        recs, result = self._records(*args, timeout=10)
        changes = [{"id": "default", "label": "default", "description": ""}]
        if not self._soften(result).ok:
            return changes, result
        for rec in recs:
            change = rec.get("change", "")
            if not change:
                continue
            desc = (rec.get("desc", "") or "").strip()
            label = f"{change} {desc.splitlines()[0]}" if desc else change
            changes.append({"id": change, "label": label, "description": desc})
        return changes, result

    def _local_key(self, client_file: str) -> str:
        if not client_file:
            return ""
        try:
            resolved = Path(client_file).resolve()
            resolved.relative_to(self.root)
        except Exception:
            return ""
        return resolved.as_posix()

    def _mapped_local_key(self, rel: str, local_root: str | Path | None = None) -> str:
        if not rel:
            return ""
        try:
            return (self._local_root_path(local_root) / rel).resolve().as_posix()
        except (OSError, RuntimeError, ValueError):
            return ""

    def _split_local_state(self, rel: str, client_file: str, local_root: str | Path | None = None) -> tuple[str, str]:
        mapped_key = self._mapped_local_key(rel, local_root)
        if not mapped_key:
            return "", ""
        local_path = Path(mapped_key)
        if not local_path.exists():
            return mapped_key, "missing"
        client_path = Path(client_file) if client_file else None
        if client_path is None:
            return mapped_key, "same"
        if not client_path.exists():
            return mapped_key, "modified"
        if local_path.is_file() and client_path.is_file():
            try:
                if not filecmp.cmp(local_path, client_path, shallow=False):
                    return mapped_key, "modified"
            except OSError:
                return mapped_key, "modified"
        return mapped_key, "same"

    def _local_disk_rows(self, known_paths: set[str], local_root: str | Path | None = None) -> list[dict[str, str]]:
        rows: list[dict[str, str]] = []
        base = self._local_root_path(local_root)
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [
                name for name in dirnames
                if name not in _LOCAL_SCAN_SKIP_DIRS and not name.startswith(".")
            ]
            for filename in filenames:
                if filename in _LOCAL_SCAN_SKIP_FILES:
                    continue
                local_path = Path(dirpath) / filename
                try:
                    resolved = local_path.resolve()
                    resolved.relative_to(base)
                except (OSError, RuntimeError, ValueError):
                    continue
                key = resolved.as_posix()
                if key in known_paths:
                    continue
                known_paths.add(key)
                rows.append({"path": self._rel(key, base), "state": "new"})
        return rows

    # --------------------------------------------------------------- contract
    def detect(self) -> SCMCommandResult:
        return self._run_p4("info", timeout=5)

    def status(self, local_root: str | Path | None = None, stream: str = "") -> dict[str, Any]:
        self._select_stream(stream)
        info = self._info()
        if not info:
            res = self._run_p4("info", timeout=5)
            return {
                "ok": False, "provider": self.provider, "root": str(self.root),
                "branch": "", "head": "", "head_full": "", "ahead": 0, "behind": 0,
                "dirty": False, "files": [],
                "error": res.error or "cannot reach perforce server",
            }
        local_base = self._local_root_path(local_root)
        if local_base != self.root:
            rows = self._local_disk_rows(set(), local_base)
            files = [
                SCMFileStatus(
                    path=row["path"], status=row["state"], action="add",
                    staged=False, unstaged=True,
                ).to_dict()
                for row in rows
            ]
            return {
                "ok": True, "provider": self.provider, "root": str(self.root),
                "branch": self._branch(), "head": self._latest_change(),
                "head_full": self._latest_change(), "ahead": 0, "behind": 0,
                "dirty": bool(files), "files": files,
            }
        files: list[dict[str, Any]] = []
        seen: set[str] = set()
        opened, _ = self._records("opened", self._workspace_scope())
        for rec in opened:
            path = self._rel(rec.get("clientFile", "") or rec.get("depotFile", ""))
            action = rec.get("action", "")
            seen.add(path)
            files.append(SCMFileStatus(
                path=path, status=action, action=action, staged=True, unstaged=False,
            ).to_dict())
        recon, _ = self._records("reconcile", "-n", "-a", "-e", "-d", self._workspace_scope())
        for rec in recon:
            path = self._rel(rec.get("clientFile", "") or rec.get("depotFile", ""))
            if not path or path in seen:
                continue
            action = rec.get("action", "")
            seen.add(path)
            files.append(SCMFileStatus(
                path=path, status=action, action=action, staged=False, unstaged=True,
            ).to_dict())
        return {
            "ok": True, "provider": self.provider, "root": str(self.root),
            "branch": self._branch(), "head": self._latest_change(),
            "head_full": self._latest_change(), "ahead": 0, "behind": 0,
            "dirty": bool(files), "files": files,
        }

    def diff(
        self,
        path: str = "",
        staged: bool = False,
        local_root: str | Path | None = None,
        stream: str = "",
    ) -> SCMCommandResult:
        _ = staged  # Perforce has no staging area; opened files are the working set.
        _ = local_root
        self._select_stream(stream)
        target = self._filespecs_for_perforce_selection([path])
        return self._soften(self._run_p4("diff", "-du", *(target or [self._workspace_scope()])))

    def log(self, limit: int = 60, stream: str = "") -> dict[str, Any]:
        self._select_stream(stream)
        limit = max(1, min(int(limit or 60), 500))
        recs, result = self._records("changes", "-m", str(limit), "-t", "-s", "submitted", self._perforce_scope())
        if not recs and not self._soften(result).ok:
            return {
                "ok": False, "provider": self.provider, "root": str(self.root),
                "branch": self._branch(), "commits": [],
                "error": result.error or "p4 changes failed",
            }
        commits: list[dict[str, Any]] = []
        for rec in recs:
            cl = rec.get("change", "")
            desc = (rec.get("desc", "") or "").strip()
            subject = desc.splitlines()[0] if desc else ""
            t = rec.get("time", "")
            commits.append(SCMCommit(
                sha=cl, short=cl, author=rec.get("user", ""),
                date=t, time=float(t) if t.isdigit() else 0, subject=subject,
            ).to_dict())
        return {
            "ok": True, "provider": self.provider, "root": str(self.root),
            "branch": self._branch(), "commits": commits,
        }

    def show(self, revision: str, stream: str = "") -> SCMCommandResult:
        self._select_stream(stream)
        cl = str(revision or "").lstrip("@#").strip()
        if not cl:
            return self._result(ok=False, returncode=2, error="empty revision")
        return self._run_p4("describe", "-du", cl)

    def submit(
        self,
        message: str,
        *,
        add_all: bool = True,
        allow_empty: bool = False,
        stream: str = "",
        changelist: str = "",
        local_root: str | Path | None = None,
        paths: Any = None,
    ) -> SCMCommandResult:
        self._select_stream(stream)
        if self._is_client_root() and add_all:
            return self._result(
                ok=False, returncode=78,
                error="refusing to submit at the client root; target a specific IP subpath",
            )
        target_change = self._pending_changelist_id(changelist)
        if target_change:
            opened, _ = self._records("opened", "-c", target_change, self._perforce_scope())
            if not opened and not allow_empty:
                return self._result(ok=False, returncode=0, stdout="no files opened", error="no changes to submit")
            restaged = self._restage_local_submit_paths(opened, local_root, paths)
            if not restaged.ok:
                return restaged
            preflight = self._submit_resolve_preflight(opened)
            if not preflight.ok:
                return self._combine_results([restaged, preflight])
            updated = self._update_pending_changelist_description(target_change, message)
            if not updated.ok:
                return updated
            result = self._run_p4("submit", "-c", target_change)
            if result.ok:
                self._drop_local_source_mappings(self._opened_depot_specs(opened))
            return self._combine_results([restaged, updated, result])
        if add_all:
            self._run_p4("reconcile", self._workspace_scope())  # benign if nothing to reconcile
        scope = self._workspace_scope() if add_all else self._perforce_scope()
        opened, _ = self._records("opened", scope)
        if not opened and not allow_empty:
            return self._result(ok=False, returncode=0, stdout="no files opened", error="no changes to submit")
        restaged = self._restage_local_submit_paths(opened, local_root, paths)
        if not restaged.ok:
            return restaged
        preflight = self._submit_resolve_preflight(opened)
        if not preflight.ok:
            return self._combine_results([restaged, preflight])
        result = self._run_p4("submit", "-d", message or "atlas: submit", scope)
        if result.ok:
            self._drop_local_source_mappings(self._opened_depot_specs(opened))
        if not result.ok:
            stranded = self._stranded_submit_change(result)
            if stranded:
                self._restore_failed_submit_to_default(stranded)
        return self._combine_results([restaged, result])

    def push(self, branch: str = "", remote: str = "origin") -> SCMCommandResult:
        _ = branch, remote
        return self._result(
            ok=True, returncode=0,
            stdout="Perforce: submit publishes directly to the shared server; no separate push step.",
        )

    def sync(self, revision: str = "", stream: str = "") -> SCMCommandResult:
        self._select_stream(stream)
        scope = self._perforce_scope()
        rev = str(revision or "").strip()
        if rev:
            scope = f"{scope}{rev if rev[0] in '@#' else '@' + rev}"
        # -f forces re-fetch and (with the client's clobber option) overwrites
        # writable local files: "없으면 받고 있으면 overwrite".
        return self._soften(self._run_p4("sync", "-f", scope))

    def hard_reset(self, revision: str) -> SCMCommandResult:
        if self._is_client_root():
            return self._result(ok=False, returncode=78, error="refusing to reset at the client root")
        self._run_p4("revert", self._workspace_scope())
        cl = str(revision or "").lstrip("@#").strip()
        scope = f"{self._workspace_scope()}@{cl}" if cl else self._workspace_scope()
        return self._soften(self._run_p4("sync", "-f", scope))

    # ------------------------------------------------------- two-pane UI API
    def sync_state(
        self,
        stream: str = "",
        local_root: str | Path | None = None,
        local_dir: str = "",
        depot_dir: str = "",
    ) -> dict[str, Any]:
        """Left (local) / right (depot) / pending data for the Perforce Sync UI."""
        self._select_stream(stream)
        local_base = self._local_root_path(local_root)
        info = self._info()
        if not info:
            return {
                "ok": False, "provider": self.provider, "root": str(self.root),
                "error": "cannot reach perforce server",
            }
        p4_errors: list[str] = []

        def remember_error(result: SCMCommandResult) -> None:
            checked = self._soften(result)
            if checked.ok:
                return
            message = checked.error or checked.stderr.strip() or "p4 command failed"
            if message not in p4_errors:
                p4_errors.append(message)

        scope = pane_browse_scope(local_base, local_dir, depot_dir, self._branch())
        local = local_entries(local_base, scope.local_dir, _LOCAL_SCAN_SKIP_DIRS, _LOCAL_SCAN_SKIP_FILES)
        depot: list[Any] = []
        fstat: list[dict[str, str]] = []
        if scope.depot_pattern:
            dirs_result = self._run_p4("dirs", scope.depot_pattern, timeout=10)
            remember_error(dirs_result)
            fstat, fstat_result = self._records(
                "fstat",
                "-m", str(DEPOT_BROWSE_LIMIT),
                "-T", "depotFile,clientFile,headRev,headAction,haveRev",
                scope.depot_pattern,
                timeout=10,
            )
            remember_error(fstat_result)
            depot = merge_depot_entries(depot_folder_entries(dirs_result.stdout), depot_file_entries(fstat))

        pending: list[dict[str, Any]] = []
        opened, opened_result = self._records("opened", self._perforce_scope())
        remember_error(opened_result)
        for rec in opened:
            pending.append({
                "path": rec.get("depotFile", "") or self._rel(rec.get("clientFile", "")),
                "action": rec.get("action", ""),
                "change": rec.get("change", "default") or "default",
            })
        pending_changes, changes_result = self._pending_changes()
        remember_error(changes_result)

        payload = {
            "ok": not p4_errors, "provider": self.provider, "root": str(self.root),
            "client": info.get("clientName", ""), "stream": self._branch(),
            "streams": self._streams(),
            "head": self._latest_change(),
            "local": local, "depot": depot, "pending": pending,
            "pendingChanges": pending_changes,
            "localDir": scope.local_dir,
            "depotDir": scope.depot_dir,
            "truncated": len(fstat) >= DEPOT_BROWSE_LIMIT,
        }
        if p4_errors:
            payload["error"] = "; ".join(p4_errors)
        return payload

    def _stage_local_sources(
        self,
        paths: Any,
        local_root: str | Path | None = None,
        target_paths: Any = None,
        changelist: str = "",
        checkout_existing: bool = False,
    ) -> SCMCommandResult:
        sources = self._safe_local_paths(paths, local_root)
        if not sources:
            return self._result(ok=False, returncode=2, error="no valid local paths to open")
        targets = self._workspace_targets_for_sources(sources, paths, target_paths, local_root)
        if len(targets) != len(sources):
            return self._result(ok=False, returncode=2, error="cannot map local paths to Perforce target paths")
        specs: list[str] = []
        reconcile_specs: list[str] = []
        results: list[SCMCommandResult] = []
        target_values = self._target_values(target_paths)
        for source, target in zip(sources, targets):
            idx = len(specs)
            target_value = target_values[idx] if idx < len(target_values) else ""
            depot_file_target = target_value.startswith("//") and not target_value.endswith("/")
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                # Whether the depot already has this file decides edit-vs-add —
                # NOT the shape of the UI target (folder targets used to fall
                # into reconcile and open existing depot files for add).
                depot_exists, have_rev = (False, 0)
                if checkout_existing:
                    p4_spec = target_value if depot_file_target else target.as_posix()
                    depot_exists, have_rev = self._depot_file_state(p4_spec)
                if checkout_existing and depot_exists:
                    if have_rev <= 0 or not target.exists():
                        synced = self._soften(self._run_p4("sync", "-f", p4_spec))
                        if not synced.ok:
                            return synced
                        results.append(synced)
                    opened = self._open_for_edit(target.as_posix())
                    if not opened.ok:
                        return opened
                    results.append(opened)
                else:
                    reconcile_specs.append(target.as_posix())
                if source.resolve() != target.resolve():
                    shutil.copy2(source, target)
                if target_value:
                    depot_file = self._depot_file_for_target(target_value, target, source)
                    self._remember_local_source_mapping(depot_file, source, local_root)
            except OSError as exc:
                return self._result(ok=False, returncode=1, error=str(exc))
            specs.append(target.as_posix())
        if reconcile_specs:
            result = self._soften(self._run_p4("reconcile", *reconcile_specs))
            if not result.ok:
                return result
            results.append(result)
        return self._combine_results([*results, self._move_to_changelist(changelist, specs)])

    def open_paths(
        self,
        paths: Any,
        stream: str = "",
        local_root: str | Path | None = None,
        target_paths: Any = None,
        changelist: str = "",
    ) -> SCMCommandResult:
        self._select_stream(stream)
        if local_root is not None or target_paths:
            return self._stage_local_sources(paths, local_root, target_paths, changelist, checkout_existing=False)
        specs = self._safe_filespecs(paths)
        if not specs:
            return self._result(ok=False, returncode=2, error="no valid paths to open")
        result = self._soften(self._run_p4("reconcile", *specs))
        if not result.ok:
            return result
        return self._combine_results([result, self._move_to_changelist(changelist, specs)])

    def edit_paths(
        self,
        paths: Any,
        stream: str = "",
        local_root: str | Path | None = None,
        target_paths: Any = None,
        changelist: str = "",
    ) -> SCMCommandResult:
        self._select_stream(stream)
        if local_root is not None or target_paths:
            return self._stage_local_sources(paths, local_root, target_paths, changelist, checkout_existing=True)
        specs = self._filespecs_for_perforce_selection(paths)
        if not specs:
            return self._result(ok=False, returncode=2, error="no valid paths to edit/open")
        result = self._open_for_edit(*specs)
        if not result.ok:
            return result
        return self._combine_results([result, self._move_to_changelist(changelist, specs)])

    def revert_paths(self, paths: Any, stream: str = "", changelist: str = "") -> SCMCommandResult:
        self._select_stream(stream)
        specs = self._filespecs_for_perforce_selection(paths)
        if not specs:
            return self._result(ok=False, returncode=2, error="no valid paths to revert")
        change = self._pending_changelist_id(changelist)
        opened_args = ["opened", *specs] if not change else ["opened", "-c", change, *specs]
        opened, _ = self._records(*opened_args)
        touched = {rec.get("change", "") for rec in opened}
        if change:
            touched.add(change)
        revert_args = ["revert", *specs] if not change else ["revert", "-c", change, *specs]
        result = self._soften(self._run_p4(*revert_args))
        results = [result]
        if result.ok:
            resolve_pending, resolve_preview = self._pending_resolve(specs)
            if resolve_pending:
                fallback_args = ["revert", "-k", *specs] if not change else ["revert", "-k", "-c", change, *specs]
                fallback = self._soften(self._run_p4(*fallback_args))
                results.append(fallback)
                still_pending, still_preview = self._pending_resolve(specs)
                if still_pending:
                    diagnostics = "\n".join(
                        part.strip()
                        for part in (
                            resolve_preview.stdout,
                            resolve_preview.stderr,
                            fallback.stdout,
                            fallback.stderr,
                            still_preview.stdout,
                            still_preview.stderr,
                        )
                        if part.strip()
                    )
                    return self._combine_results([
                        *results,
                        self._result(
                            ok=False,
                            stdout=diagnostics,
                            returncode=3,
                            command=still_preview.command,
                            error="revert did not clear Perforce resolve state",
                        ),
                    ])
            self._delete_emptied_changelists({c for c in touched if c.isdigit()})
            self._drop_local_source_mappings(self._opened_depot_specs(opened) or specs)
        return self._combine_results(results)

    def delete_pending_changelist(self, changelist: str, stream: str = "") -> SCMCommandResult:
        """Drop a numbered pending changelist. Opened files are reverted with
        -k (workspace content kept) so deleting a junk changelist never
        destroys local edits; shelved changelists still refuse deletion."""
        self._select_stream(stream)
        change = self._pending_changelist_id(changelist)
        if not change:
            return self._result(ok=False, returncode=2, error="a numbered pending changelist is required")
        opened, _ = self._records("opened", "-c", change)
        results: list[SCMCommandResult] = []
        if opened:
            reverted = self._soften(self._run_p4("revert", "-k", "-c", change, "//..."))
            if not reverted.ok:
                return reverted
            results.append(reverted)
        results.append(self._run_p4("change", "-d", change))
        combined = self._combine_results(results)
        if combined.ok:
            self._drop_local_source_mappings(self._opened_depot_specs(opened))
        return combined

    def sync_paths(
        self,
        paths: Any,
        revision: str = "",
        stream: str = "",
        local_root: str | Path | None = None,
        target_paths: Any = None,
    ) -> SCMCommandResult:
        self._select_stream(stream)
        specs = self._filespecs_for_perforce_selection(paths)
        if not specs:
            return self.sync(revision)
        rev = str(revision or "").strip()
        tag = ""
        if rev:
            tag = rev if rev[0] in "@#" else "@" + rev
        depot_specs = [spec for spec in specs if spec.startswith("//")]
        local_specs = [spec + tag for spec in specs if not spec.startswith("//")]
        results: list[SCMCommandResult] = []
        if local_specs:
            results.append(self._soften(self._run_p4("sync", "-f", *local_specs)))
        targets = self._target_values(target_paths)
        for idx, spec in enumerate(depot_specs):
            if idx < len(targets):
                target = targets[idx]
            elif len(targets) == 1 and targets[0].endswith("/"):
                target = targets[0]
            else:
                target = ""
            results.append(self._copy_depot_to_local(spec + tag, spec, local_root, target))
        return self._combine_results(results)
