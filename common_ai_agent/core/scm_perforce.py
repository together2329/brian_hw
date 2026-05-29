"""Deployment-specific Perforce (Helix Core) SCM adapter for Atlas.

This is the real p4 implementation that the built-in ``core.scm.PerforceSCMAdapter``
stub intentionally leaves out. It is wired in via the documented override hook
(``ATLAS_SCM_ADAPTER_PERFORCE=core.scm_perforce:PerforceP4Adapter``) so the core
contract test that asserts the stub stays unimplemented keeps passing.

Connection/workspace are resolved by p4 itself (P4CONFIG/.p4config or env), set up
by ``scripts/perforce_setup.sh``. The adapter is constructed per-IP with
``root = PROJECT_ROOT/<ip>`` (see atlas_api_git._scm_call), so every operation is
scoped to that IP subtree of the stream ``//GOOD_SOC/GOOD_IP``.
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from core.scm import (
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


class PerforceP4Adapter(SCMAdapter):
    provider = "perforce"

    def __init__(self, root: str | Path, executable: str = "p4") -> None:
        super().__init__(root, executable=executable)
        # Local filespec covering this IP subtree, in p4 syntax.
        self._scope = f"{self.root.as_posix()}/..."
        self._info_cache: dict[str, str] | None = None

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
        command = (self.executable, "-d", str(self.root), *args)
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

    def _is_client_root(self) -> bool:
        cr = self._client_root()
        return cr is not None and cr == self.root

    def _branch(self) -> str:
        info = self._info()
        return info.get("clientStream") or info.get("clientName") or ""

    def _latest_change(self) -> str:
        recs, _ = self._records("changes", "-m", "1", "-s", "submitted", self._scope)
        return recs[0].get("change", "") if recs else ""

    def _rel(self, p: str) -> str:
        if not p:
            return p
        try:
            return str(Path(p).resolve().relative_to(self.root))
        except Exception:
            return p

    def _safe_filespecs(self, paths: Any) -> list[str]:
        """Resolve UI-supplied paths to absolute local filespecs inside root."""
        out: list[str] = []
        if not paths:
            return out
        if isinstance(paths, str):
            paths = [paths]
        for raw in paths:
            text = str(raw or "").strip()
            if not text:
                continue
            cand = Path(text)
            if not cand.is_absolute():
                cand = self.root / text
            try:
                resolved = cand.resolve()
                resolved.relative_to(self.root)  # reject escapes
            except Exception:
                continue
            out.append(resolved.as_posix())
        return out

    # --------------------------------------------------------------- contract
    def detect(self) -> SCMCommandResult:
        return self._run_p4("info", timeout=5)

    def status(self) -> dict[str, Any]:
        info = self._info()
        if not info:
            res = self._run_p4("info", timeout=5)
            return {
                "ok": False, "provider": self.provider, "root": str(self.root),
                "branch": "", "head": "", "head_full": "", "ahead": 0, "behind": 0,
                "dirty": False, "files": [],
                "error": res.error or "cannot reach perforce server",
            }
        files: list[dict[str, Any]] = []
        seen: set[str] = set()
        opened, _ = self._records("opened", self._scope)
        for rec in opened:
            path = self._rel(rec.get("clientFile", "") or rec.get("depotFile", ""))
            action = rec.get("action", "")
            seen.add(path)
            files.append(SCMFileStatus(
                path=path, status=action, action=action, staged=True, unstaged=False,
            ).to_dict())
        recon, _ = self._records("reconcile", "-n", "-a", "-e", "-d", self._scope)
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

    def diff(self, path: str = "", staged: bool = False) -> SCMCommandResult:
        _ = staged  # Perforce has no staging area; opened files are the working set.
        target = self._safe_filespecs([path])
        return self._soften(self._run_p4("diff", "-du", *(target or [self._scope])))

    def log(self, limit: int = 60) -> dict[str, Any]:
        limit = max(1, min(int(limit or 60), 500))
        recs, result = self._records("changes", "-m", str(limit), "-t", "-s", "submitted", self._scope)
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

    def submit(self, message: str, *, add_all: bool = True, allow_empty: bool = False) -> SCMCommandResult:
        if self._is_client_root():
            return self._result(
                ok=False, returncode=78,
                error="refusing to submit at the client root; target a specific IP subpath",
            )
        if add_all:
            self._run_p4("reconcile", self._scope)  # benign if nothing to reconcile
        opened, _ = self._records("opened", self._scope)
        if not opened and not allow_empty:
            return self._result(ok=False, returncode=0, stdout="no files opened", error="no changes to submit")
        return self._run_p4("submit", "-d", message or "atlas: submit", self._scope)

    def push(self, branch: str = "", remote: str = "origin") -> SCMCommandResult:
        _ = branch, remote
        return self._result(
            ok=True, returncode=0,
            stdout="Perforce: submit publishes directly to the shared server; no separate push step.",
        )

    def sync(self, revision: str = "") -> SCMCommandResult:
        scope = self._scope
        rev = str(revision or "").strip()
        if rev:
            scope = f"{scope}{rev if rev[0] in '@#' else '@' + rev}"
        # -f forces re-fetch and (with the client's clobber option) overwrites
        # writable local files: "없으면 받고 있으면 overwrite".
        return self._soften(self._run_p4("sync", "-f", scope))

    def hard_reset(self, revision: str) -> SCMCommandResult:
        if self._is_client_root():
            return self._result(ok=False, returncode=78, error="refusing to reset at the client root")
        self._run_p4("revert", self._scope)
        cl = str(revision or "").lstrip("@#").strip()
        scope = f"{self._scope}@{cl}" if cl else self._scope
        return self._soften(self._run_p4("sync", "-f", scope))

    # ------------------------------------------------------- two-pane UI API
    def sync_state(self) -> dict[str, Any]:
        """Left (local) / right (depot) / pending data for the Perforce Sync UI."""
        info = self._info()
        if not info:
            return {
                "ok": False, "provider": self.provider, "root": str(self.root),
                "error": "cannot reach perforce server",
            }
        recon, _ = self._records("reconcile", "-n", "-a", "-e", "-d", self._scope)
        recon_action: dict[str, str] = {}
        for rec in recon:
            cf = rec.get("clientFile", "")
            if cf:
                recon_action[str(Path(cf).resolve())] = rec.get("action", "")

        fstat, _ = self._records(
            "fstat", "-T", "depotFile,clientFile,headRev,headAction,haveRev", self._scope,
        )
        depot: list[dict[str, Any]] = []
        local: list[dict[str, Any]] = []
        for rec in fstat:
            cf = rec.get("clientFile", "")
            key = str(Path(cf).resolve()) if cf else ""
            rel = self._rel(cf) if cf else rec.get("depotFile", "")
            head_rev = rec.get("headRev", "")
            head_action = rec.get("headAction", "")
            have_rev = rec.get("haveRev", "")
            if head_rev and head_action != "delete":
                depot.append({"path": rel, "rev": head_rev})
            if have_rev:
                act = recon_action.get(key, "")
                if act == "edit":
                    state = "modified"
                elif act in ("delete", "move/delete"):
                    state = "missing"
                else:
                    state = "same"
                local.append({"path": rel, "state": state})
        for key, act in recon_action.items():
            if act in ("add", "move/add"):
                local.append({"path": self._rel(key), "state": "new"})

        pending: list[dict[str, Any]] = []
        opened, _ = self._records("opened", self._scope)
        for rec in opened:
            pending.append({
                "path": self._rel(rec.get("clientFile", "") or rec.get("depotFile", "")),
                "action": rec.get("action", ""),
            })

        local.sort(key=lambda r: r["path"])
        depot.sort(key=lambda r: r["path"])
        return {
            "ok": True, "provider": self.provider, "root": str(self.root),
            "client": info.get("clientName", ""), "stream": self._branch(),
            "head": self._latest_change(),
            "local": local, "depot": depot, "pending": pending,
        }

    def open_paths(self, paths: Any) -> SCMCommandResult:
        specs = self._safe_filespecs(paths)
        if not specs:
            return self._result(ok=False, returncode=2, error="no valid paths to open")
        return self._soften(self._run_p4("reconcile", *specs))

    def revert_paths(self, paths: Any) -> SCMCommandResult:
        specs = self._safe_filespecs(paths)
        if not specs:
            return self._result(ok=False, returncode=2, error="no valid paths to revert")
        return self._soften(self._run_p4("revert", *specs))

    def sync_paths(self, paths: Any, revision: str = "") -> SCMCommandResult:
        specs = self._safe_filespecs(paths)
        if not specs:
            return self.sync(revision)
        rev = str(revision or "").strip()
        if rev:
            tag = rev if rev[0] in "@#" else "@" + rev
            specs = [s + tag for s in specs]
        return self._soften(self._run_p4("sync", "-f", *specs))
