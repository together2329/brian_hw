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
_RECONCILE_LOCAL_STATES: Final[Mapping[str, str]] = {
    "add": "new",
    "edit": "modified",
    "delete": "missing",
    "move/add": "new",
    "move/delete": "missing",
}
_STREAM_NAME_RE: Final[re.Pattern[str]] = re.compile(r"^//[A-Za-z0-9_.-]+/[A-Za-z0-9_./-]+$")


class PerforceP4Adapter(SCMAdapter):
    provider = "perforce"

    def __init__(self, root: str | Path, executable: str = "p4") -> None:
        super().__init__(root, executable=executable)
        self._info_cache: dict[str, str] | None = None
        self._selected_stream = ""
        self._selected_client = ""

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
    def _run_p4(self, *args: str, timeout: int = DEFAULT_TIMEOUT_SEC) -> SCMCommandResult:
        client_args = ("-c", self._selected_client) if self._selected_client else ()
        command = (self.executable, *client_args, "-d", str(self.root), *args)
        try:
            completed = subprocess.run(
                list(command),
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

    def _output_path_from_target(self, target: str, local_root: str | Path | None = None) -> Path | None:
        text = str(target or "").strip()
        if not text:
            return None
        base = self._local_root_path(local_root)
        if text.startswith("//"):
            rel = self._depot_output_rel(text, base)
            cand = base / rel
        else:
            cand = Path(text)
            if not cand.is_absolute():
                cand = base / text
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

    def _copy_depot_to_local(
        self,
        depot_spec: str,
        output_from: str,
        local_root: str | Path | None = None,
        target_path: str = "",
    ) -> SCMCommandResult:
        output = self._output_path_from_target(target_path, local_root) if target_path else self._depot_output_path(output_from, local_root)
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

    def _client_path_for_depot(self, depot_file: str) -> Path | None:
        base = self._workspace_root_path()
        recs, result = self._records("fstat", "-T", "clientFile", depot_file, timeout=10)
        if self._soften(result).ok and recs and recs[0].get("clientFile"):
            filespec = self._workspace_filespec(Path(recs[0]["clientFile"]))
            if filespec is None:
                return None
            return Path(filespec)
        rel = self._depot_output_rel(depot_file)
        if not rel:
            return None
        filespec = self._workspace_filespec(base / rel)
        if filespec is None:
            return None
        return Path(filespec)

    def _workspace_targets_for_sources(
        self,
        sources: list[Path],
        original_paths: Any,
        target_paths: Any,
    ) -> list[Path]:
        base = self._workspace_root_path()
        targets = self._target_values(target_paths)
        originals = [original_paths] if isinstance(original_paths, str) else list(original_paths or [])
        out: list[Path] = []
        for idx, source in enumerate(sources):
            target_text = targets[idx] if idx < len(targets) else targets[0] if len(targets) == 1 else ""
            if target_text.startswith("//"):
                if target_text.endswith("/"):
                    rel = self._depot_output_rel(target_text)
                    target = (base / rel / source.name) if rel else None
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
        if failures:
            first = failures[0]
            return self._result(
                ok=False, stdout=stdout, stderr=stderr,
                returncode=first.returncode, error=first.error or first.stderr.strip(),
            )
        return self._result(ok=True, stdout=stdout, stderr=stderr)

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

    def diff(self, path: str = "", staged: bool = False, local_root: str | Path | None = None) -> SCMCommandResult:
        _ = staged  # Perforce has no staging area; opened files are the working set.
        _ = local_root
        target = self._safe_filespecs([path])
        return self._soften(self._run_p4("diff", "-du", *(target or [self._workspace_scope()])))

    def log(self, limit: int = 60) -> dict[str, Any]:
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

    def show(self, revision: str) -> SCMCommandResult:
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
            return self._run_p4("submit", "-c", target_change)
        if add_all:
            self._run_p4("reconcile", self._workspace_scope())  # benign if nothing to reconcile
        scope = self._workspace_scope() if add_all else self._perforce_scope()
        opened, _ = self._records("opened", scope)
        if not opened and not allow_empty:
            return self._result(ok=False, returncode=0, stdout="no files opened", error="no changes to submit")
        return self._run_p4("submit", "-d", message or "atlas: submit", scope)

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
    def sync_state(self, stream: str = "", local_root: str | Path | None = None) -> dict[str, Any]:
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

        recon_action: dict[str, str] = {}
        if local_base == self.root:
            recon, recon_result = self._records("reconcile", "-n", "-a", "-e", "-d", self._workspace_scope())
            remember_error(recon_result)
            for rec in recon:
                cf = rec.get("clientFile", "")
                if cf:
                    recon_action[str(Path(cf).resolve())] = rec.get("action", "")

        fstat, fstat_result = self._records(
            "fstat", "-T", "depotFile,clientFile,headRev,headAction,haveRev", self._perforce_scope(),
        )
        remember_error(fstat_result)
        depot: list[dict[str, Any]] = []
        local: list[dict[str, Any]] = []
        known_local_paths: set[str] = set()
        for rec in fstat:
            cf = rec.get("clientFile", "")
            key = self._local_key(cf)
            depot_path = rec.get("depotFile", "") or self._rel(cf)
            rel = self._rel(cf) if key else ""
            mapped_key = key if local_base == self.root else self._mapped_local_key(rel, local_base)
            head_rev = rec.get("headRev", "")
            head_action = rec.get("headAction", "")
            have_rev = rec.get("haveRev", "")
            if head_rev and head_action != "delete":
                depot.append({"path": depot_path, "rev": head_rev})
            if have_rev and key and (local_base == self.root or (mapped_key and Path(mapped_key).exists())):
                act = recon_action.get(key, "")
                if act == "edit":
                    state = "modified"
                elif act in ("delete", "move/delete"):
                    state = "missing"
                else:
                    state = "same"
                local.append({"path": rel, "state": state})
                if mapped_key:
                    known_local_paths.add(mapped_key)
        for key, act in recon_action.items():
            if key in known_local_paths:
                continue
            local.append({"path": self._rel(key, local_base), "state": _RECONCILE_LOCAL_STATES.get(act, act or "new")})
            known_local_paths.add(key)
        local.extend(self._local_disk_rows(known_local_paths, local_base))

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

        local.sort(key=lambda r: r["path"])
        depot.sort(key=lambda r: r["path"])
        payload = {
            "ok": not p4_errors, "provider": self.provider, "root": str(self.root),
            "client": info.get("clientName", ""), "stream": self._branch(),
            "streams": self._streams(),
            "head": self._latest_change(),
            "local": local, "depot": depot, "pending": pending,
            "pendingChanges": pending_changes,
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
    ) -> SCMCommandResult:
        sources = self._safe_local_paths(paths, local_root)
        if not sources:
            return self._result(ok=False, returncode=2, error="no valid local paths to open")
        targets = self._workspace_targets_for_sources(sources, paths, target_paths)
        if len(targets) != len(sources):
            return self._result(ok=False, returncode=2, error="cannot map local paths to Perforce target paths")
        specs: list[str] = []
        for source, target in zip(sources, targets):
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                if target.exists():
                    opened = self._soften(self._run_p4("edit", target.as_posix()))
                    if not opened.ok:
                        return opened
                if source.resolve() != target.resolve():
                    shutil.copy2(source, target)
            except OSError as exc:
                return self._result(ok=False, returncode=1, error=str(exc))
            specs.append(target.as_posix())
        result = self._soften(self._run_p4("reconcile", *specs))
        if not result.ok:
            return result
        return self._combine_results([result, self._move_to_changelist(changelist, specs)])

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
            return self._stage_local_sources(paths, local_root, target_paths, changelist)
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
            return self._stage_local_sources(paths, local_root, target_paths, changelist)
        specs = self._filespecs_for_perforce_selection(paths)
        if not specs:
            return self._result(ok=False, returncode=2, error="no valid paths to edit/open")
        result = self._soften(self._run_p4("edit", *specs))
        if not result.ok:
            return result
        return self._combine_results([result, self._move_to_changelist(changelist, specs)])

    def revert_paths(self, paths: Any, stream: str = "") -> SCMCommandResult:
        self._select_stream(stream)
        specs = self._filespecs_for_perforce_selection(paths)
        if not specs:
            return self._result(ok=False, returncode=2, error="no valid paths to revert")
        return self._soften(self._run_p4("revert", *specs))

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
            target = targets[idx] if idx < len(targets) else targets[0] if len(targets) == 1 else ""
            results.append(self._copy_depot_to_local(spec + tag, spec, local_root, target))
        return self._combine_results(results)
