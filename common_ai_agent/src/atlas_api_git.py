"""ATLAS git API — extracted from atlas_ui.py.

First step of the gradual atlas_ui.py decomposition: pull the
self-contained `/api/git/*` routes (status, log, show, diff, commit,
push) and the `_git` / `_git_cwd_for_ip` helpers into their own
module. The host (atlas_ui.py) wires routes via `register_git_routes`
and injects callables for runtime values (PROJECT_ROOT, active IP,
IP-name validator) so this module never reaches into the host's
mutable globals.
"""
from __future__ import annotations

import asyncio
import re
import subprocess as _sp_git
from pathlib import Path
from typing import Any, Callable, Optional

from fastapi import FastAPI
from fastapi.responses import JSONResponse


def register_git_routes(
    app: FastAPI,
    *,
    project_root: Callable[[], Path],
    active_ip_value: Callable[[], str],
    valid_ip_name: Callable[[str], bool],
) -> None:
    """Mount the git API onto *app*.

    project_root, active_ip_value, valid_ip_name are passed as callables
    rather than values so the routes always read the live state — the
    --root flag in atlas_ui main() rebinds PROJECT_ROOT after this
    module is imported.
    """

    async def _git(*args: str, cwd: str | None = None):
        # `cwd` lets callers target the per-IP repo (PROJECT_ROOT/<ip>)
        # instead of the outer project repo. Defaults to PROJECT_ROOT
        # for backwards compatibility with existing /api/git/* paths.
        # Async via asyncio.to_thread so /api/git/* polling never
        # blocks the event loop while git runs (10-100 ms).
        def _run_git():
            try:
                r = _sp_git.run(
                    ["git", *args], cwd=cwd or str(project_root()),
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=30,
                )
                return r.returncode, r.stdout, r.stderr
            except _sp_git.TimeoutExpired:
                return 124, "", "git command timed out"
            except FileNotFoundError:
                return 127, "", "git executable not found"
        return await asyncio.to_thread(_run_git)

    def _git_cwd_for_ip(ip: str) -> tuple[str | None, JSONResponse | None, str]:
        """Resolve the cwd for a per-IP git repo.

        Empty IP keeps the legacy project-root git view. A non-empty IP is
        explicit user intent, so never fall back to PROJECT_ROOT: returning the
        outer repo for a missing per-IP repo makes commit/push hit the wrong
        repository.
        """
        clean = str(ip or "").strip()
        if not clean:
            return str(project_root()), None, ""
        if not valid_ip_name(clean):
            return None, JSONResponse({"error": "invalid ip", "ip": clean}, status_code=400), clean
        candidate = (project_root() / clean).resolve()
        try:
            candidate.relative_to(project_root().resolve())
        except ValueError:
            return None, JSONResponse({"error": "ip path escapes project root", "ip": clean}, status_code=400), clean
        if not candidate.is_dir():
            return None, JSONResponse({"error": "ip not found", "ip": clean}, status_code=404), clean
        if not (candidate / ".git").is_dir():
            return None, JSONResponse({"error": "ip has no .git", "ip": clean}, status_code=409), clean
        return str(candidate), None, clean

    def _route_cwd(ip: str) -> tuple[str | None, JSONResponse | None, str]:
        return _git_cwd_for_ip(ip or active_ip_value())

    @app.get("/api/git/status")
    async def api_git_status(ip: str = ""):
        cwd, error, resolved_ip = _route_cwd(ip)
        if error is not None:
            return error
        rc, branch, _ = await _git("rev-parse", "--abbrev-ref", "HEAD", cwd=cwd)
        branch = branch.strip() if rc == 0 else ""
        rc, head, _ = await _git("rev-parse", "--short", "HEAD", cwd=cwd)
        head = head.strip() if rc == 0 else ""
        rc, head_full, _ = await _git("rev-parse", "HEAD", cwd=cwd)
        head_full = head_full.strip() if rc == 0 else ""
        rc, out, err = await _git("status", "--porcelain=v1", "--branch", cwd=cwd)
        if rc != 0:
            return JSONResponse({"error": err.strip() or "git status failed",
                                 "branch": branch, "head": head,
                                 "head_full": head_full, "files": []}, status_code=200)
        files = []
        ahead = behind = 0
        for line in out.splitlines():
            if not line:
                continue
            if line.startswith("##"):
                m = re.search(r"ahead (\d+)", line)
                if m: ahead = int(m.group(1))
                m = re.search(r"behind (\d+)", line)
                if m: behind = int(m.group(1))
                continue
            xy = line[:2]; path = line[3:]
            if " -> " in path:
                path = path.split(" -> ", 1)[1]
            files.append({
                "path": path, "status": xy,
                "staged":   xy[0] not in (" ", "?"),
                "unstaged": xy[1] != " ",
            })
        rc, ns_out, _ = await _git("diff", "--numstat", "HEAD", cwd=cwd)
        numstat = {}
        if rc == 0:
            for line in ns_out.splitlines():
                parts = line.split("\t")
                if len(parts) >= 3:
                    a, d, p = parts[0], parts[1], parts[2]
                    try:
                        numstat[p] = {"added": int(a) if a != "-" else 0,
                                       "removed": int(d) if d != "-" else 0}
                    except ValueError:
                        pass
        for f in files:
            ns = numstat.get(f["path"])
            if ns: f.update(ns)
        return JSONResponse({"branch": branch, "head": head,
                              "head_full": head_full, "ahead": ahead,
                              "behind": behind, "dirty": bool(files), "files": files,
                              "ip": resolved_ip, "cwd": cwd})

    @app.get("/api/git/log")
    async def api_git_log(ip: str = "", limit: int = 60):
        cwd, error, resolved_ip = _route_cwd(ip)
        if error is not None:
            return error
        rc, branch, _ = await _git("rev-parse", "--abbrev-ref", "HEAD", cwd=cwd)
        branch = branch.strip() if rc == 0 else ""
        fmt = "%H%x1f%h%x1f%an%x1f%ae%x1f%aI%x1f%s%x1e"
        rc, out, err = await _git(
            "log",
            f"-n{max(1, min(limit, 500))}",
            f"--pretty=format:{fmt}",
            cwd=cwd,
        )
        if rc != 0:
            return JSONResponse({
                "error": err.strip() or "git log failed",
                "commits": [], "branch": branch, "ip": resolved_ip,
            }, status_code=200)
        commits = []
        for record in out.split("\x1e"):
            record = record.strip("\n")
            if not record:
                continue
            parts = record.split("\x1f")
            if len(parts) < 6:
                continue
            sha, short, author, email, iso_date, subject = parts[:6]
            commits.append({
                "sha": sha, "short": short,
                "author": author, "email": email,
                "date": iso_date, "subject": subject,
            })
        if commits:
            rc, ns, _ = await _git(
                "log",
                f"-n{len(commits)}",
                "--no-renames", "--numstat", "--format=__SHA__%H__",
                cwd=cwd,
            )
            if rc == 0:
                cur_sha = None
                added_total = removed_total = 0
                files_changed = 0
                by_sha: dict[str, dict[str, int]] = {}
                for line in ns.splitlines():
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
                            a, d, _p = line.split("\t", 2)
                            added_total += 0 if a == "-" else int(a)
                            removed_total += 0 if d == "-" else int(d)
                            files_changed += 1
                        except ValueError:
                            pass
                if cur_sha is not None:
                    by_sha[cur_sha] = {
                        "added": added_total,
                        "removed": removed_total,
                        "files": files_changed,
                    }
                for c in commits:
                    s = by_sha.get(c["sha"], {})
                    c["added"] = s.get("added", 0)
                    c["removed"] = s.get("removed", 0)
                    c["files"] = s.get("files", 0)
        return JSONResponse({
            "commits": commits, "branch": branch,
            "ip": resolved_ip, "cwd": cwd,
        })

    @app.get("/api/git/show")
    async def api_git_show(sha: str, ip: str = ""):
        if not sha or not re.match(r"^[0-9a-f]{4,40}$", sha):
            return JSONResponse({"error": "invalid sha"}, status_code=400)
        cwd, error, resolved_ip = _route_cwd(ip)
        if error is not None:
            return error
        rc, out, err = await _git("show", sha, "--no-color", "--unified=3", cwd=cwd)
        if rc != 0:
            return JSONResponse({
                "error": err.strip() or f"git show {sha} failed",
                "diff": "",
            }, status_code=200)
        return JSONResponse({"sha": sha, "diff": out, "ip": resolved_ip})

    @app.get("/api/git/diff")
    async def api_git_diff(path: str = "", staged: int = 0, ip: str = ""):
        cwd, error, resolved_ip = _route_cwd(ip)
        if error is not None:
            return error
        if not path:
            rc, out, err = await _git(
                "diff" if not staged else "diff",
                "--cached" if staged else "HEAD",
                cwd=cwd,
            )
        else:
            args = ["diff"]
            if staged: args.append("--cached")
            args.append("--")
            args.append(path)
            rc, out, err = await _git(*args, cwd=cwd)
        if rc != 0 and not out:
            return JSONResponse({"error": err.strip() or "diff failed",
                                  "diff": ""}, status_code=200)
        return JSONResponse({"diff": out, "path": path, "ip": resolved_ip})

    @app.post("/api/git/commit")
    async def api_git_commit(payload: dict[str, Any]):
        body = payload or {}
        message = str(body.get("message", "")).strip()
        add_all = bool((payload or {}).get("add_all", True))
        if not message:
            return JSONResponse({"error": "commit message required"},
                                 status_code=400)
        cwd, error, resolved_ip = _route_cwd(str(body.get("ip") or ""))
        if error is not None:
            return error
        if add_all:
            rc, _, err = await _git("add", "-A", cwd=cwd)
            if rc != 0:
                return JSONResponse({"error": "git add -A failed: " + err.strip()},
                                     status_code=200)
        rc, out, err = await _git("commit", "-m", message, cwd=cwd)
        return JSONResponse({"ok": rc == 0, "stdout": out, "stderr": err,
                              "returncode": rc, "ip": resolved_ip})

    @app.post("/api/git/push")
    async def api_git_push(payload: Optional[dict[str, Any]] = None):
        body = payload or {}
        cwd, error, resolved_ip = _route_cwd(str(body.get("ip") or ""))
        if error is not None:
            return error
        rc, branch, _ = await _git("rev-parse", "--abbrev-ref", "HEAD", cwd=cwd)
        branch = branch.strip()
        if not branch or branch == "HEAD":
            return JSONResponse({"error": "no current branch (detached HEAD?)"},
                                 status_code=400)
        rc, out, err = await _git("push", "origin", branch, cwd=cwd)
        return JSONResponse({"ok": rc == 0, "stdout": out, "stderr": err,
                              "branch": branch, "returncode": rc,
                              "ip": resolved_ip})
