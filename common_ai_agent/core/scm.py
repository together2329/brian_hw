"""Source-control adapter contract used by Atlas.

Git is the built-in implementation today. Perforce is intentionally exposed as
an adapter surface so a site-specific implementation can be plugged in without
rewriting Atlas routes or workflow code.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from importlib import import_module
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any


DEFAULT_TIMEOUT_SEC = 30


@dataclass(frozen=True)
class SCMCommandResult:
    ok: bool
    provider: str
    root: str
    stdout: str = ""
    stderr: str = ""
    returncode: int = 0
    error: str = ""
    command: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "ok": self.ok,
            "provider": self.provider,
            "root": self.root,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "returncode": self.returncode,
        }
        if self.error:
            payload["error"] = self.error
        if self.command:
            payload["command"] = list(self.command)
        return payload


@dataclass(frozen=True)
class SCMFileStatus:
    path: str
    status: str
    staged: bool = False
    unstaged: bool = False
    added: int = 0
    removed: int = 0
    action: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "path": self.path,
            "status": self.status,
            "staged": self.staged,
            "unstaged": self.unstaged,
        }
        if self.added:
            payload["added"] = self.added
        if self.removed:
            payload["removed"] = self.removed
        if self.action:
            payload["action"] = self.action
        return payload


@dataclass(frozen=True)
class SCMCommit:
    sha: str
    short: str
    author: str
    email: str = ""
    date: str = ""
    time: float = 0
    subject: str = ""
    parents: tuple[str, ...] = field(default_factory=tuple)
    added: int = 0
    removed: int = 0
    files: int = 0

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "sha": self.sha,
            "short": self.short,
            "author": self.author,
            "email": self.email,
            "date": self.date,
            "subject": self.subject,
        }
        if self.time:
            payload["time"] = self.time
        if self.parents:
            payload["parents"] = list(self.parents)
        if self.added:
            payload["added"] = self.added
        if self.removed:
            payload["removed"] = self.removed
        if self.files:
            payload["files"] = self.files
        return payload

    def to_graph_dict(self) -> dict[str, Any]:
        return {
            "hash": self.sha,
            "short": self.short,
            "author": self.author,
            "time": self.time,
            "subject": self.subject,
            "parents": list(self.parents),
        }


def normalize_scm_provider(provider: str | None) -> str:
    value = (provider or "").strip().lower()
    if value in ("", "auto", "default"):
        return "auto"
    if value in ("git", "git-cli"):
        return "git"
    if value in ("p4", "perforce"):
        return "perforce"
    return value


def configured_scm_provider(env: dict[str, str] | None = None) -> str:
    source = env if env is not None else os.environ
    return normalize_scm_provider(source.get("ATLAS_SCM_PROVIDER", "auto"))


def scm_provider_allows_missing_git_dir(provider: str | None = None) -> bool:
    return normalize_scm_provider(provider or configured_scm_provider()) == "perforce"


def resolve_scm_adapter(
    root: str | Path,
    provider: str | None = None,
) -> "SCMAdapter":
    selected = normalize_scm_provider(provider or configured_scm_provider())
    if selected == "git":
        return _configured_adapter("git", root)
    if selected == "perforce":
        return _configured_adapter("perforce", root)

    git = _configured_adapter("git", root)
    detected = git.detect()
    if detected.ok:
        return git

    p4 = _configured_adapter("perforce", root)
    detected = p4.detect()
    if detected.ok:
        return p4

    return git


class SCMAdapter:
    provider = "scm"

    def __init__(self, root: str | Path, executable: str = "") -> None:
        self.root = Path(root).resolve()
        self.executable = executable or self.provider

    def capabilities(self) -> dict[str, bool]:
        return {
            "status": False,
            "diff": False,
            "log": False,
            "show": False,
            "submit": False,
            "push": False,
            "graph": False,
            "hard_reset": False,
            "sync": False,
        }

    def _result(
        self,
        *,
        ok: bool,
        stdout: str = "",
        stderr: str = "",
        returncode: int = 0,
        error: str = "",
        command: tuple[str, ...] = (),
    ) -> SCMCommandResult:
        return SCMCommandResult(
            ok=ok,
            provider=self.provider,
            root=str(self.root),
            stdout=stdout,
            stderr=stderr,
            returncode=returncode,
            error=error,
            command=command,
        )

    def _unsupported(self, operation: str) -> SCMCommandResult:
        return self._result(
            ok=False,
            returncode=78,
            error=f"{self.provider} operation is not implemented: {operation}",
        )

    def detect(self) -> SCMCommandResult:
        return self._unsupported("detect")

    def status(self) -> dict[str, Any]:
        result = self._unsupported("status")
        return {
            "ok": False,
            "provider": self.provider,
            "root": str(self.root),
            "branch": "",
            "head": "",
            "head_full": "",
            "ahead": 0,
            "behind": 0,
            "dirty": False,
            "files": [],
            "error": result.error,
        }

    def diff(self, path: str = "", staged: bool = False) -> SCMCommandResult:
        _ = path, staged
        return self._unsupported("diff")

    def log(self, limit: int = 60) -> dict[str, Any]:
        _ = limit
        result = self._unsupported("log")
        return {
            "ok": False,
            "provider": self.provider,
            "root": str(self.root),
            "branch": "",
            "commits": [],
            "error": result.error,
        }

    def show(self, revision: str) -> SCMCommandResult:
        _ = revision
        return self._unsupported("show")

    def submit(
        self,
        message: str,
        *,
        add_all: bool = True,
        allow_empty: bool = False,
    ) -> SCMCommandResult:
        _ = message, add_all, allow_empty
        return self._unsupported("submit")

    def push(self, branch: str = "", remote: str = "origin") -> SCMCommandResult:
        _ = branch, remote
        return self._unsupported("push")

    def graph(self, limit: int = 80) -> dict[str, Any]:
        _ = limit
        result = self._unsupported("graph")
        return {
            "ok": False,
            "provider": self.provider,
            "root": str(self.root),
            "graph": "",
            "commits": [],
            "error": result.error,
        }

    def hard_reset(self, revision: str) -> SCMCommandResult:
        _ = revision
        return self._unsupported("hard_reset")

    def sync(self, revision: str = "") -> SCMCommandResult:
        _ = revision
        return self._unsupported("sync")


class SCMConfigurationErrorAdapter(SCMAdapter):
    def __init__(self, root: str | Path, provider: str, error: str) -> None:
        super().__init__(root, executable=provider)
        self.provider = provider
        self._configuration_error = error

    def _unsupported(self, operation: str) -> SCMCommandResult:
        return self._result(
            ok=False,
            returncode=78,
            error=f"{self.provider} adapter configuration error during {operation}: {self._configuration_error}",
        )

    def detect(self) -> SCMCommandResult:
        return self._unsupported("detect")


class GitSCMAdapter(SCMAdapter):
    provider = "git"

    def __init__(self, root: str | Path, executable: str = "git") -> None:
        super().__init__(root, executable=executable)

    def capabilities(self) -> dict[str, bool]:
        caps = super().capabilities()
        caps.update({
            "status": True,
            "diff": True,
            "log": True,
            "show": True,
            "submit": True,
            "push": True,
            "graph": True,
            "hard_reset": True,
            "sync": True,
        })
        return caps

    def _run(self, *args: str, timeout: int = DEFAULT_TIMEOUT_SEC) -> SCMCommandResult:
        command = (self.executable, *args)
        try:
            completed = subprocess.run(
                list(command),
                cwd=str(self.root),
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
            return self._result(
                ok=False,
                returncode=124,
                error=f"git command timed out after {timeout}s",
                command=command,
            )
        except FileNotFoundError:
            return self._result(
                ok=False,
                returncode=127,
                error="git executable not found",
                command=command,
            )

    def detect(self) -> SCMCommandResult:
        return self._run("rev-parse", "--show-toplevel", timeout=5)

    def _short_head(self) -> str:
        result = self._run("rev-parse", "--short", "HEAD", timeout=5)
        return result.stdout.strip() if result.ok else ""

    def _full_head(self) -> str:
        result = self._run("rev-parse", "HEAD", timeout=5)
        return result.stdout.strip() if result.ok else ""

    def current_branch(self) -> str:
        result = self._run("rev-parse", "--abbrev-ref", "HEAD", timeout=5)
        return result.stdout.strip() if result.ok else ""

    def status(self) -> dict[str, Any]:
        branch = self.current_branch()
        head = self._short_head()
        head_full = self._full_head()
        result = self._run("status", "--porcelain=v1", "--branch")
        if not result.ok:
            return {
                "ok": False,
                "provider": self.provider,
                "root": str(self.root),
                "branch": branch,
                "head": head,
                "head_full": head_full,
                "ahead": 0,
                "behind": 0,
                "dirty": False,
                "files": [],
                "error": result.error or "git status failed",
            }

        files: list[SCMFileStatus] = []
        ahead = behind = 0
        for line in result.stdout.splitlines():
            if not line:
                continue
            if line.startswith("##"):
                match = re.search(r"ahead (\d+)", line)
                if match:
                    ahead = int(match.group(1))
                match = re.search(r"behind (\d+)", line)
                if match:
                    behind = int(match.group(1))
                continue
            status = line[:2]
            path = line[3:]
            if " -> " in path:
                path = path.split(" -> ", 1)[1]
            files.append(SCMFileStatus(
                path=path,
                status=status,
                staged=status[0] not in (" ", "?"),
                unstaged=status[1] != " ",
            ))

        numstat = self._numstat()
        merged = []
        for item in files:
            stats = numstat.get(item.path, {})
            merged.append(SCMFileStatus(
                path=item.path,
                status=item.status,
                staged=item.staged,
                unstaged=item.unstaged,
                added=stats.get("added", 0),
                removed=stats.get("removed", 0),
                action=item.action,
            ).to_dict())

        return {
            "ok": True,
            "provider": self.provider,
            "root": str(self.root),
            "branch": branch,
            "head": head,
            "head_full": head_full,
            "ahead": ahead,
            "behind": behind,
            "dirty": bool(merged),
            "files": merged,
            "raw": result.stdout,
        }

    def _numstat(self) -> dict[str, dict[str, int]]:
        result = self._run("diff", "--numstat", "HEAD")
        stats: dict[str, dict[str, int]] = {}
        if not result.ok:
            return stats
        for line in result.stdout.splitlines():
            parts = line.split("\t")
            if len(parts) < 3:
                continue
            added, removed, path = parts[0], parts[1], parts[2]
            try:
                stats[path] = {
                    "added": int(added) if added != "-" else 0,
                    "removed": int(removed) if removed != "-" else 0,
                }
            except ValueError:
                continue
        return stats

    def diff(self, path: str = "", staged: bool = False) -> SCMCommandResult:
        if path:
            args = ["diff"]
            if staged:
                args.append("--cached")
            args.extend(["--", path])
            return self._run(*args)
        if staged:
            return self._run("diff", "--cached")
        return self._run("diff", "HEAD")

    def log(self, limit: int = 60) -> dict[str, Any]:
        limit = max(1, min(int(limit or 60), 500))
        branch = self.current_branch()
        fmt = "%H%x1f%h%x1f%an%x1f%ae%x1f%aI%x1f%at%x1f%s%x1e"
        result = self._run("log", f"-n{limit}", f"--pretty=format:{fmt}")
        if not result.ok:
            return {
                "ok": False,
                "provider": self.provider,
                "root": str(self.root),
                "branch": branch,
                "commits": [],
                "error": result.error or "git log failed",
            }

        commits: list[SCMCommit] = []
        for record in result.stdout.split("\x1e"):
            record = record.strip("\n")
            if not record:
                continue
            parts = record.split("\x1f")
            if len(parts) < 7:
                continue
            sha, short, author, email, iso_date, unix_time, subject = parts[:7]
            commits.append(SCMCommit(
                sha=sha,
                short=short,
                author=author,
                email=email,
                date=iso_date,
                time=float(unix_time) if unix_time.isdigit() else 0,
                subject=subject,
            ))

        by_sha = self._commit_numstats(len(commits)) if commits else {}
        return {
            "ok": True,
            "provider": self.provider,
            "root": str(self.root),
            "branch": branch,
            "commits": [
                SCMCommit(
                    sha=commit.sha,
                    short=commit.short,
                    author=commit.author,
                    email=commit.email,
                    date=commit.date,
                    time=commit.time,
                    subject=commit.subject,
                    added=by_sha.get(commit.sha, {}).get("added", 0),
                    removed=by_sha.get(commit.sha, {}).get("removed", 0),
                    files=by_sha.get(commit.sha, {}).get("files", 0),
                ).to_dict()
                for commit in commits
            ],
        }

    def _commit_numstats(self, limit: int) -> dict[str, dict[str, int]]:
        result = self._run(
            "log",
            f"-n{max(1, limit)}",
            "--no-renames",
            "--numstat",
            "--format=__SHA__%H__",
        )
        if not result.ok:
            return {}
        cur_sha = None
        added_total = removed_total = files_changed = 0
        by_sha: dict[str, dict[str, int]] = {}
        for line in result.stdout.splitlines():
            if line.startswith("__SHA__"):
                if cur_sha is not None:
                    by_sha[cur_sha] = {
                        "added": added_total,
                        "removed": removed_total,
                        "files": files_changed,
                    }
                cur_sha = line[len("__SHA__"):].rstrip("_")
                added_total = removed_total = files_changed = 0
            elif line.strip():
                try:
                    added, removed, _path = line.split("\t", 2)
                    added_total += 0 if added == "-" else int(added)
                    removed_total += 0 if removed == "-" else int(removed)
                    files_changed += 1
                except ValueError:
                    continue
        if cur_sha is not None:
            by_sha[cur_sha] = {
                "added": added_total,
                "removed": removed_total,
                "files": files_changed,
            }
        return by_sha

    def show(self, revision: str) -> SCMCommandResult:
        return self._run("show", revision, "--no-color", "--unified=3")

    def submit(
        self,
        message: str,
        *,
        add_all: bool = True,
        allow_empty: bool = False,
    ) -> SCMCommandResult:
        if add_all:
            add = self._run("add", "-A")
            if not add.ok:
                return self._result(
                    ok=False,
                    stdout=add.stdout,
                    stderr=add.stderr,
                    returncode=add.returncode,
                    error="git add -A failed: " + (add.error or add.stderr.strip()),
                    command=add.command,
                )
        args = ["commit"]
        if allow_empty:
            args.append("--allow-empty")
        args.extend(["-m", message])
        return self._run(*args)

    def push(self, branch: str = "", remote: str = "origin") -> SCMCommandResult:
        selected_branch = branch or self.current_branch()
        if not selected_branch or selected_branch == "HEAD":
            return self._result(
                ok=False,
                returncode=2,
                error="no current branch (detached HEAD?)",
            )
        return self._run("push", remote, selected_branch)

    def graph(self, limit: int = 80) -> dict[str, Any]:
        limit = max(1, min(int(limit or 80), 1000))
        graph = self._run(
            "log",
            "--graph",
            "--oneline",
            "--decorate",
            "--all",
            "--date=relative",
            f"-n{limit}",
            "--pretty=format:%h %s%d (%cr)",
            timeout=10,
        )
        structured = self._run(
            "log",
            f"-n{limit}",
            "--pretty=format:%H\x1f%h\x1f%an\x1f%at\x1f%s\x1f%P",
            timeout=10,
        )
        if not graph.ok and not structured.ok:
            return {
                "ok": False,
                "provider": self.provider,
                "root": str(self.root),
                "graph": "",
                "commits": [],
                "error": graph.error or structured.error or "git graph failed",
            }
        commits: list[dict[str, Any]] = []
        for line in structured.stdout.splitlines():
            parts = line.split("\x1f")
            if len(parts) < 5:
                continue
            commits.append(SCMCommit(
                sha=parts[0],
                short=parts[1],
                author=parts[2],
                time=float(parts[3]) if parts[3].isdigit() else 0,
                subject=parts[4],
                parents=tuple(parts[5].split()) if len(parts) >= 6 else (),
            ).to_graph_dict())
        return {
            "ok": True,
            "provider": self.provider,
            "root": str(self.root),
            "graph": graph.stdout,
            "commits": commits,
        }

    def hard_reset(self, revision: str) -> SCMCommandResult:
        verify = self._run("cat-file", "-e", revision, timeout=5)
        if not verify.ok:
            return self._result(
                ok=False,
                returncode=404,
                error="revision not in this repository history",
                command=verify.command,
            )
        return self._run("reset", "--hard", revision, timeout=15)

    def sync(self, revision: str = "") -> SCMCommandResult:
        if revision:
            fetch = self._run("fetch", "--all", "--prune")
            if not fetch.ok:
                return fetch
            return self._run("checkout", revision)
        return self._run("pull", "--ff-only")


class PerforceSCMAdapter(SCMAdapter):
    provider = "perforce"

    def __init__(self, root: str | Path, executable: str = "p4") -> None:
        super().__init__(root, executable=executable)

    def capabilities(self) -> dict[str, bool]:
        # The interface exists here; the actual p4 behavior should be supplied
        # by the deployment-specific Perforce implementation.
        return super().capabilities()

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
            return self._result(
                ok=False,
                returncode=124,
                error=f"p4 command timed out after {timeout}s",
                command=command,
            )
        except FileNotFoundError:
            return self._result(
                ok=False,
                returncode=127,
                error="p4 executable not found",
                command=command,
            )

    def detect(self) -> SCMCommandResult:
        return self._run_p4("info", timeout=5)


def _configured_adapter(provider: str, root: str | Path) -> SCMAdapter:
    adapter_ref = _adapter_override_ref(provider)
    if adapter_ref:
        try:
            adapter_class = _load_adapter_class(adapter_ref, provider)
            return adapter_class(root)
        except Exception as exc:
            return SCMConfigurationErrorAdapter(
                root,
                provider,
                f"failed to load {adapter_ref}: {exc}",
            )
    if provider == "git":
        return GitSCMAdapter(root)
    if provider == "perforce":
        return PerforceSCMAdapter(root)
    return SCMConfigurationErrorAdapter(root, provider, "unknown provider")


def _adapter_override_ref(provider: str, env: dict[str, str] | None = None) -> str:
    source = env if env is not None else os.environ
    normalized = normalize_scm_provider(provider)
    suffix = normalized.upper()
    specific = (
        source.get(f"ATLAS_SCM_ADAPTER_{suffix}", "").strip()
        or source.get(f"ATLAS_{suffix}_SCM_ADAPTER", "").strip()
    )
    if specific:
        return specific
    if configured_scm_provider(source) == normalized:
        return source.get("ATLAS_SCM_ADAPTER", "").strip()
    return ""


def _load_adapter_class(ref: str, provider: str) -> type[SCMAdapter]:
    module_ref, sep, class_name = ref.partition(":")
    if not sep or not module_ref.strip() or not class_name.strip():
        raise ValueError("adapter reference must be 'module:Class' or '/path/file.py:Class'")

    _extend_plugin_path()
    module = _load_adapter_module(module_ref.strip(), provider)
    adapter_class = getattr(module, class_name.strip())
    if not isinstance(adapter_class, type) or not issubclass(adapter_class, SCMAdapter):
        raise TypeError(f"{class_name.strip()} must subclass core.scm.SCMAdapter")
    return adapter_class


def _extend_plugin_path(env: dict[str, str] | None = None) -> None:
    source = env if env is not None else os.environ
    raw = source.get("ATLAS_SCM_PLUGIN_PATH", "")
    for item in raw.split(os.pathsep):
        path = item.strip()
        if path and path not in sys.path:
            sys.path.insert(0, path)


def _load_adapter_module(module_ref: str, provider: str):
    looks_like_file = (
        module_ref.endswith(".py")
        or "/" in module_ref
        or "\\" in module_ref
    )
    if not looks_like_file:
        return import_module(module_ref)

    path = Path(module_ref).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(str(path))
    module_name = f"_atlas_scm_{provider}_{abs(hash(str(path)))}"
    spec = spec_from_file_location(module_name, str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load adapter module from {path}")
    module = module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module
