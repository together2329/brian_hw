#!/usr/bin/env python3
"""IP-local development memory helper.

This helper keeps the durable part of an IP development session inside the IP
folder itself:

- `<ip>/wiki/` keeps LLM-readable notes and decisions.
- `<ip>/.git/` keeps local snapshots for that IP.

It is intentionally conservative. Hooks call `hook-session` or
`hook-file-edit`; those commands only initialize an existing IP directory when
the IP can be detected from the hook payload, prompt, path, or cwd.
"""

import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
from contextlib import redirect_stdout
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

IP_HINT_RE = re.compile(r"\b[A-Za-z][A-Za-z0-9_.-]*(?:_cx1|_v[0-9]+)\b")
IP_MARKER_DIRS = ("req", "rtl", "tb", "sim", "lint", "cov", "verify", "signoff")
IP_MARKER_FILES = ("requirements.md", "locked_truth.md")
HOOK_TEXT_KEYS = (
    "prompt",
    "userPrompt",
    "user_prompt",
    "message",
    "last_assistant_message",
    "command",
    "cmd",
    "path",
    "file_path",
    "filePath",
    "cwd",
)


def tool_root() -> Path:
    return Path(__file__).resolve().parents[1]


def project_root(start: Optional[Path] = None) -> Path:
    override = os.environ.get("COMMON_AI_AGENT_ROOT")
    if override:
        candidate = Path(override).expanduser().resolve()
        if (candidate / "scripts" / "ip_wiki.py").is_file():
            return candidate

    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / "scripts" / "ip_dev_memory.py").is_file():
            return candidate
    return tool_root()


def workspace_root() -> Path:
    override = os.environ.get("IP_DEV_MEMORY_WORKSPACE_ROOT") or os.environ.get("COMMON_AI_AGENT_ROOT")
    if override:
        return Path(override).expanduser().resolve()
    return project_root()


def load_ip_wiki(root: Path):
    script = root / "scripts" / "ip_wiki.py"
    spec = importlib.util.spec_from_file_location("ip_wiki", script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {script}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def call_ip_wiki(func, *args):
    with redirect_stdout(sys.stderr):
        return func(*args)


def run_git(ip_dir: Path, *args: str, check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ip_dir,
        text=True,
        capture_output=True,
        check=check,
    )


def has_git_config(ip_dir: Path, key: str) -> bool:
    result = run_git(ip_dir, "config", "--local", "--get", key)
    return result.returncode == 0 and bool(result.stdout.strip())


def ensure_git(ip_dir: Path) -> bool:
    created = False
    git_dir = ip_dir / ".git"
    if not git_dir.exists():
        run_git(ip_dir, "init", "-q", check=True)
        created = True

    if not has_git_config(ip_dir, "user.name"):
        run_git(ip_dir, "config", "--local", "user.name", "IP Memory Bot", check=True)
    if not has_git_config(ip_dir, "user.email"):
        run_git(ip_dir, "config", "--local", "user.email", "ip-memory@local", check=True)
    return created


def is_ip_dir(path: Path) -> bool:
    if not path.is_dir():
        return False
    if (path / "wiki").is_dir() or (path / ".git").is_dir():
        return True
    if any((path / name).exists() for name in IP_MARKER_DIRS):
        return True
    if any((path / "req" / name).exists() for name in IP_MARKER_FILES):
        return True
    return bool(IP_HINT_RE.fullmatch(path.name))


def known_ip_dirs(root: Path) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for child in sorted(root.iterdir() if root.is_dir() else []):
        if child.name.startswith(".") or not child.is_dir():
            continue
        if is_ip_dir(child):
            result[child.name] = child
    return result


def add_index_row(index: Path, page: str, description: str) -> None:
    text = index.read_text(encoding="utf-8")
    row = f"| [[{page}]] | {description} |"
    if row in text or f"[[{page}]]" in text:
        return
    if "| [[log]] |" in text:
        text = text.replace("| [[log]] | 개발 히스토리 (append-only) |", "| [[log]] | 개발 히스토리 (append-only) |\n" + row)
    else:
        text = text.rstrip() + "\n\n" + row + "\n"
    index.write_text(text, encoding="utf-8")


def ensure_memory_pages(ip_dir: Path) -> None:
    ip = ip_dir.name
    wiki = ip_dir / "wiki"
    wiki.mkdir(parents=True, exist_ok=True)

    llm_memory = wiki / "llm_memory.md"
    if not llm_memory.is_file():
        llm_memory.write_text(
            f"---\ntitle: {ip} LLM Memory\nip: {ip}\ncategory: ip-wiki\nstatus: live\n---\n\n"
            f"# {ip} LLM Memory\n\n"
            "이 파일은 채팅창 밖에 남기는 장기 메모리다. 다음 세션은 여기서 이어간다.\n\n"
            "## Current Context\n\n"
            "- Requirement/obligation source: `req/`\n"
            "- Evidence source: `rtl/`, `lint/`, `sim/`, `cov/`, `verify/`, `signoff/`\n"
            "- Development history: [[log]]\n"
            "- Local version snapshots: [[git]]\n\n"
            "## Session Entries\n",
            encoding="utf-8",
        )

    git_page = wiki / "git.md"
    if not git_page.is_file():
        git_page.write_text(
            f"---\ntitle: {ip} Git Memory\nip: {ip}\ncategory: ip-wiki\nstatus: live\n---\n\n"
            f"# {ip} Git Memory\n\n"
            "이 IP 폴더는 독립적인 git repository로 snapshot을 남긴다.\n\n"
            "## Commands\n\n"
            "```bash\n"
            "python3 scripts/ip_dev_memory.py init <ip>\n"
            "python3 scripts/ip_dev_memory.py log <ip> --stage sim --title \"...\"\n"
            "python3 scripts/ip_dev_memory.py snapshot <ip> --message \"sim: ...\"\n"
            "python3 scripts/ip_dev_memory.py check <ip> --require-git\n"
            "```\n",
            encoding="utf-8",
        )

    index = wiki / "index.md"
    if index.is_file():
        add_index_row(index, "llm_memory", "LLM 장기 메모리와 다음 세션 시작점")
        add_index_row(index, "git", "IP-local git snapshot 사용법")


def init_ip(ip_dir: Path, *, stage: str = "session", title: str = "IP memory session start") -> dict[str, Any]:
    if not ip_dir.is_dir():
        raise FileNotFoundError(f"IP directory does not exist: {ip_dir}")

    root = project_root(ip_dir)
    ip_wiki = load_ip_wiki(root)
    call_ip_wiki(ip_wiki.cmd_init, str(ip_dir))
    ensure_memory_pages(ip_dir)
    git_created = ensure_git(ip_dir)

    if git_created:
        append_memory_entry(
            ip_dir,
            stage=stage,
            title=title,
            body="Initialized IP-local git repository and wiki memory.",
            evidence=[],
            snapshot=False,
        )

    return {
        "ip": ip_dir.name,
        "path": str(ip_dir),
        "wiki": str(ip_dir / "wiki"),
        "git_created": git_created,
    }


def append_memory_entry(
    ip_dir: Path,
    *,
    stage: str,
    title: str,
    body: str,
    evidence: list[str],
    snapshot: bool,
) -> None:
    root = project_root(ip_dir)
    ip_wiki = load_ip_wiki(root)
    evidence_lines = [f"- Evidence: `{item}`" for item in evidence]
    full_body = body.strip()
    if evidence_lines:
        full_body = (full_body + "\n" if full_body else "") + "\n".join(evidence_lines)
    call_ip_wiki(ip_wiki.cmd_log, str(ip_dir), title, full_body, stage)

    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    llm_memory = ip_dir / "wiki" / "llm_memory.md"
    text = llm_memory.read_text(encoding="utf-8")
    entry = [f"### {stamp} - {title}", "", f"- Stage: `{stage or 'general'}`"]
    if body.strip():
        entry.extend(["", body.strip()])
    if evidence:
        entry.append("")
        entry.extend(evidence_lines)
    if snapshot:
        entry.extend(["", "- Snapshot: committed to IP-local git."])
    text = text.rstrip() + "\n\n" + "\n".join(entry) + "\n"
    llm_memory.write_text(text, encoding="utf-8")


def git_snapshot(ip_dir: Path, message: str) -> dict[str, Any]:
    init_ip(ip_dir, stage="git", title="IP memory snapshot prepared")
    run_git(ip_dir, "add", "-A", check=True)
    staged = run_git(ip_dir, "diff", "--cached", "--quiet")
    if staged.returncode == 0:
        return {"ip": ip_dir.name, "committed": False, "reason": "no changes"}

    run_git(ip_dir, "commit", "-q", "-m", message, check=True)
    head = run_git(ip_dir, "rev-parse", "--short", "HEAD", check=True).stdout.strip()
    append_memory_entry(
        ip_dir,
        stage="git",
        title=f"Snapshot {head}",
        body=message,
        evidence=[],
        snapshot=True,
    )
    run_git(ip_dir, "add", "wiki/llm_memory.md", "wiki/log.md", check=True)
    if run_git(ip_dir, "diff", "--cached", "--quiet").returncode != 0:
        run_git(ip_dir, "commit", "-q", "-m", f"memory: record snapshot {head}", check=True)
    return {"ip": ip_dir.name, "committed": True, "head": head}


def check_ip(ip_dir: Path, *, require_git: bool) -> tuple[bool, list[str]]:
    issues: list[str] = []
    root = project_root(ip_dir)
    ip_wiki = load_ip_wiki(root)
    if call_ip_wiki(ip_wiki.cmd_check, str(ip_dir)) != 0:
        issues.append("wiki check failed")
    if require_git and not (ip_dir / ".git").is_dir():
        issues.append("missing IP-local .git")
    if (ip_dir / ".git").is_dir():
        status = run_git(ip_dir, "status", "--short", "--", ".")
        if status.returncode == 0 and status.stdout.strip():
            issues.append("IP-local git has uncommitted changes")
    return not issues, issues


def read_payload() -> dict[str, Any]:
    try:
        value = json.load(sys.stdin)
    except Exception:
        return {}
    return value if isinstance(value, dict) else {}


def collect_strings(value: Any, out: list[str]) -> None:
    if isinstance(value, str):
        out.append(value)
    elif isinstance(value, dict):
        for key, item in value.items():
            if key in HOOK_TEXT_KEYS or isinstance(item, (dict, list)):
                collect_strings(item, out)
    elif isinstance(value, list):
        for item in value:
            collect_strings(item, out)


def detect_ips(root: Path, payload: dict[str, Any], explicit_ip: Optional[str]) -> list[Path]:
    known = known_ip_dirs(root)
    selected: dict[str, Path] = {}

    values = []
    if explicit_ip:
        values.append(explicit_ip)
    env_ip = os.environ.get("IP_DEV_MEMORY_IP")
    if env_ip:
        values.extend(part.strip() for part in env_ip.split(",") if part.strip())
    collect_strings(payload, values)

    cwd_value = payload.get("cwd") or payload.get("currentWorkingDirectory") or os.getcwd()
    cwd = Path(str(cwd_value)).expanduser()
    if cwd.exists():
        resolved = cwd.resolve()
        root_resolved = root.resolve()
        cwd_in_workspace = False
        try:
            resolved.relative_to(root_resolved)
        except ValueError:
            cwd_in_workspace = False
        else:
            cwd_in_workspace = True
        if cwd_in_workspace and resolved != root_resolved and is_ip_dir(resolved):
            selected[resolved.name] = resolved
        for name, path in known.items():
            try:
                resolved.relative_to(path.resolve())
            except ValueError:
                pass
            else:
                selected[name] = path

    combined = "\n".join(values)
    for name, path in known.items():
        if name in combined:
            selected[name] = path
    for match in IP_HINT_RE.findall(combined):
        if match in known:
            selected[match] = known[match]

    for text in values:
        for name, path in known.items():
            if f"{name}/" in text or f"{name}\\" in text:
                selected[name] = path

    return sorted(selected.values(), key=lambda item: item.name)


def emit_hook(surface: str, message: str, *, block: bool = False) -> None:
    if not message:
        print("{}")
        return
    if surface == "codex":
        if block:
            print(json.dumps({"decision": "block", "reason": message}, ensure_ascii=False))
        else:
            print(
                json.dumps(
                    {
                        "hookSpecificOutput": {
                            "hookEventName": "SessionStart",
                            "additionalContext": message,
                        }
                    },
                    ensure_ascii=False,
                )
            )
    else:
        key = "followup_message" if block else "agent_message"
        print(json.dumps({key: message}, ensure_ascii=False))


def cmd_hook_session(args: argparse.Namespace) -> int:
    payload = read_payload()
    root = workspace_root()
    ips = detect_ips(root, payload, args.ip)
    initialized = [init_ip(ip, stage="session", title="IP memory session start") for ip in ips]
    if initialized:
        names = ", ".join(item["ip"] for item in initialized)
        emit_hook(args.surface, f"IP dev memory initialized for: {names}. Read <ip>/wiki/llm_memory.md before continuing.")
    else:
        emit_hook(args.surface, "")
    return 0


def cmd_hook_stop(args: argparse.Namespace) -> int:
    payload = read_payload()
    root = workspace_root()
    ips = detect_ips(root, payload, args.ip)
    if not ips:
        emit_hook(args.surface, "")
        return 0

    issues: list[str] = []
    for ip in ips:
        ok, ip_issues = check_ip(ip, require_git=True)
        if not ok:
            issues.append(f"{ip.name}: {', '.join(ip_issues)}")
    if not issues:
        emit_hook(args.surface, "")
        return 0

    message = (
        "IP dev memory is not closed. Run `python3 scripts/ip_dev_memory.py init <ip>`, "
        "`log`, and `snapshot` before claiming the IP work is complete. "
        + " | ".join(issues)
    )
    emit_hook(args.surface, message, block=True)
    return 0


def cmd_init(args: argparse.Namespace) -> int:
    root = workspace_root()
    ip_dir = (root / args.ip_dir).resolve() if not Path(args.ip_dir).is_absolute() else Path(args.ip_dir).resolve()
    result = init_ip(ip_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_log(args: argparse.Namespace) -> int:
    root = workspace_root()
    ip_dir = (root / args.ip_dir).resolve() if not Path(args.ip_dir).is_absolute() else Path(args.ip_dir).resolve()
    init_ip(ip_dir, stage=args.stage, title="IP memory log prepared")
    append_memory_entry(
        ip_dir,
        stage=args.stage,
        title=args.title,
        body=args.body,
        evidence=args.evidence,
        snapshot=False,
    )
    print(f"[ip_dev_memory] logged: {ip_dir.name} {args.title}")
    return 0


def cmd_snapshot(args: argparse.Namespace) -> int:
    root = workspace_root()
    ip_dir = (root / args.ip_dir).resolve() if not Path(args.ip_dir).is_absolute() else Path(args.ip_dir).resolve()
    result = git_snapshot(ip_dir, args.message)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    root = workspace_root()
    ip_dir = (root / args.ip_dir).resolve() if not Path(args.ip_dir).is_absolute() else Path(args.ip_dir).resolve()
    ok, issues = check_ip(ip_dir, require_git=args.require_git)
    if ok:
        print(f"[ip_dev_memory] PASS: {ip_dir.name}")
        return 0
    for issue in issues:
        print(f"[ip_dev_memory] FAIL: {issue}")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    init = sub.add_parser("init")
    init.add_argument("ip_dir")
    init.set_defaults(func=cmd_init)

    log = sub.add_parser("log")
    log.add_argument("ip_dir")
    log.add_argument("--stage", default="general")
    log.add_argument("--title", required=True)
    log.add_argument("--body", default="")
    log.add_argument("--evidence", action="append", default=[])
    log.set_defaults(func=cmd_log)

    snapshot = sub.add_parser("snapshot")
    snapshot.add_argument("ip_dir")
    snapshot.add_argument("--message", required=True)
    snapshot.set_defaults(func=cmd_snapshot)

    check = sub.add_parser("check")
    check.add_argument("ip_dir")
    check.add_argument("--require-git", action="store_true")
    check.set_defaults(func=cmd_check)

    for name, func in (
        ("hook-session", cmd_hook_session),
        ("hook-file-edit", cmd_hook_session),
        ("hook-stop", cmd_hook_stop),
    ):
        hook = sub.add_parser(name)
        hook.add_argument("--surface", choices=("codex", "cursor"), default="codex")
        hook.add_argument("--ip")
        hook.set_defaults(func=func)

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
