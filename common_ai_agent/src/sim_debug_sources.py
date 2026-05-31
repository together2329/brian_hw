"""src/sim_debug_sources.py — RTL source-set resolution for sim_debug elab.

Extracted verbatim (logic-identical) from the `_elab_resolve_sources` closure
that lived inside `register_sim_debug_routes` in src/atlas_api_sim_debug.py, so
both the /api/hierarchy|/api/trace|/api/module/signals routes AND the agent
`sim_debug` tool (core/sim_debug_analyze.py) can resolve the same source set.

`PROJECT_ROOT` is now an explicit first argument instead of a closed-over
binding; everything else is unchanged.
"""
from __future__ import annotations

import os
import shlex
from pathlib import Path
from typing import List, Optional


def resolve_elab_sources(project_root: Path, sources_glob: str, ip: str = "") -> List[Path]:
    """Resolve a comma-separated glob list (or a single ip-tree default).
    Each pattern is interpreted relative to `project_root` and clipped to
    files under it. Default source discovery prefers the IP filelist
    (`<ip>/list/*.f` or nested `*/<ip>/list/*.f`) before falling back to RTL
    directory scans.
    """
    PROJECT_ROOT = project_root
    skip_parts = {
        ".git", ".session", "__pycache__", "node_modules", "vendor",
        ".venv", "venv", "dist", "build",
    }
    rtl_suffixes = (".sv", ".v", ".svh", ".vh")
    filelist_suffixes = (".f", ".vf", ".flist", ".list")
    out: list = []
    seen: set[str] = set()
    seen_filelists: set[str] = set()

    def _add(f):
        try:
            resolved = f.resolve()
            rel = resolved.relative_to(PROJECT_ROOT)
        except (OSError, ValueError):
            return
        if any(part in skip_parts for part in rel.parts):
            return
        if not f.is_file() or f.suffix.lower() not in rtl_suffixes:
            return
        key = rel.as_posix()
        if key in seen:
            return
        seen.add(key)
        out.append(resolved)

    def _project_relative_file(p: Path, suffixes: tuple) -> Optional[Path]:
        try:
            resolved = p.resolve()
            rel = resolved.relative_to(PROJECT_ROOT)
        except (OSError, ValueError):
            return None
        if any(part in skip_parts for part in rel.parts):
            return None
        if not resolved.is_file() or resolved.suffix.lower() not in suffixes:
            return None
        return resolved

    def _resolve_filelist_token(token: str, bases: list) -> list:
        raw = os.path.expanduser(os.path.expandvars(str(token or "").strip()))
        if not raw:
            return []
        p = Path(raw)
        if p.is_absolute():
            return [p]
        candidates: list = []
        for base in bases:
            candidates.append(base / p)
        candidates.append(PROJECT_ROOT / p)
        return candidates

    def _read_filelist(filelist: Path) -> None:
        resolved = _project_relative_file(filelist, filelist_suffixes)
        if resolved is None:
            return
        key = resolved.relative_to(PROJECT_ROOT).as_posix()
        if key in seen_filelists:
            return
        seen_filelists.add(key)
        bases = [resolved.parent, resolved.parent.parent, PROJECT_ROOT]
        try:
            lines = resolved.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            return
        for raw in lines:
            line = raw.split("//", 1)[0].split("#", 1)[0].strip()
            if not line:
                continue
            try:
                tokens = shlex.split(line, comments=False, posix=True)
            except ValueError:
                tokens = line.split()
            i = 0
            while i < len(tokens):
                token = tokens[i].strip()
                if token in ("-f", "-F") and i + 1 < len(tokens):
                    for candidate in _resolve_filelist_token(tokens[i + 1], bases):
                        _read_filelist(candidate)
                    i += 2
                    continue
                if (token.startswith("-f") or token.startswith("-F")) and len(token) > 2:
                    for candidate in _resolve_filelist_token(token[2:], bases):
                        _read_filelist(candidate)
                    i += 1
                    continue
                if token.startswith("+incdir+") or token.startswith("+define+") or token.startswith("-I"):
                    i += 1
                    continue
                if token.startswith("-") or token.startswith("+"):
                    i += 1
                    continue
                if Path(token).suffix.lower() in rtl_suffixes:
                    for candidate in _resolve_filelist_token(token, bases):
                        _add(candidate)
                i += 1

    def _add_default_filelists(clean_ip: str) -> None:
        ip_leaf = Path(clean_ip).name
        patterns = [
            f"{clean_ip}/list/{ip_leaf}.f",
            f"{clean_ip}/list/*.f",
            f"common_ai_agent/{clean_ip}/list/{ip_leaf}.f",
            f"common_ai_agent/{clean_ip}/list/*.f",
            f"common_ai_agent/*/{clean_ip}/list/{ip_leaf}.f",
            f"common_ai_agent/*/{clean_ip}/list/*.f",
            f"*/{clean_ip}/list/{ip_leaf}.f",
            f"*/{clean_ip}/list/*.f",
            f"*/*/{clean_ip}/list/{ip_leaf}.f",
            f"*/*/{clean_ip}/list/*.f",
        ]
        for pat in patterns:
            for f in PROJECT_ROOT.glob(pat):
                _read_filelist(f)

    if not sources_glob and ip:
        clean_ip = str(ip).strip().strip("/")
        _add_default_filelists(clean_ip)
        if out:
            return out
        default_patterns = [
            f"{clean_ip}/rtl/*",
            f"common_ai_agent/{clean_ip}/rtl/*",
            f"common_ai_agent/*/{clean_ip}/rtl/*",
            f"*/{clean_ip}/rtl/*",
            f"*/*/{clean_ip}/rtl/*",
        ]
        for pat in default_patterns:
            for f in PROJECT_ROOT.glob(pat):
                _add(f)
        if not out:
            for rtl_dir in PROJECT_ROOT.rglob("rtl"):
                try:
                    rel = rtl_dir.resolve().relative_to(PROJECT_ROOT)
                except (OSError, ValueError):
                    continue
                if any(part in skip_parts for part in rel.parts):
                    continue
                parent = rtl_dir.parent.name
                if parent == clean_ip or clean_ip in rel.parts:
                    for f in rtl_dir.glob("*"):
                        _add(f)
        return out
    for pat in (sources_glob or "").split(","):
        pat = pat.strip().lstrip("/")
        if not pat:
            continue
        for f in PROJECT_ROOT.glob(pat):
            _add(f)
    return out
