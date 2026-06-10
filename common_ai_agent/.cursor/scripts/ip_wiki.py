#!/usr/bin/env python3
"""ip_wiki.py — IP 폴더 내장 wiki (<ip>/wiki) 헬퍼.

doc/wiki 와 같은 형태(frontmatter + [[link]])를 IP 단위로 축소 이식한다.
IP 를 개발하는 동안 스테이지가 끝날 때마다 `log` 로 히스토리를 쌓고,
`check` 가 frontmatter/링크 무결성을 게이트한다 (silent-PASS 금지).

Usage:
  python3 scripts/ip_wiki.py init  <ip_dir>                  # wiki/ 골격 생성 (멱등)
  python3 scripts/ip_wiki.py log   <ip_dir> --title T [--body B] [--stage S]
  python3 scripts/ip_wiki.py page  <ip_dir> <name> --title T [--tags a,b]
  python3 scripts/ip_wiki.py check <ip_dir>                  # rc 0/1 게이트
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)
LINK_RE = re.compile(r"\[\[([A-Za-z0-9._/-]+)\]\]")


def _wiki_dir(ip_dir: str) -> Path:
    return Path(ip_dir) / "wiki"


def _frontmatter(text: str):
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.startswith((" ", "\t")):
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    return fm


def cmd_init(ip_dir: str) -> int:
    wiki = _wiki_dir(ip_dir)
    ip = Path(ip_dir).resolve().name
    wiki.mkdir(parents=True, exist_ok=True)
    index = wiki / "index.md"
    log = wiki / "log.md"
    if not index.is_file():
        index.write_text(
            f"---\ntitle: {ip} Wiki Index\nip: {ip}\ncategory: ip-wiki\n"
            f"status: live\n---\n\n# {ip} Wiki\n\n"
            "이 IP 의 설계 결정·시행착오·스테이지 히스토리. 히스토리는 [[log]] 에 쌓인다.\n\n"
            "| Page | 내용 |\n|---|---|\n| [[log]] | 개발 히스토리 (append-only) |\n",
            encoding="utf-8")
    if not log.is_file():
        log.write_text(
            f"---\ntitle: {ip} Development Log\nip: {ip}\ncategory: ip-wiki\n"
            f"status: live\n---\n\n# {ip} Log\n",
            encoding="utf-8")
    print(f"[ip_wiki] init OK: {wiki}")
    return 0


def cmd_log(ip_dir: str, title: str, body: str, stage: str) -> int:
    wiki = _wiki_dir(ip_dir)
    log = wiki / "log.md"
    if not log.is_file():
        rc = cmd_init(ip_dir)
        if rc:
            return rc
    today = datetime.now().strftime("%Y-%m-%d")
    stamp = datetime.now().strftime("%H:%M")
    tag = f" `[{stage}]`" if stage else ""
    entry = f"- **{title}**{tag} ({stamp})"
    if body:
        entry += "\n" + "\n".join(f"  {line}" for line in body.splitlines())
    text = log.read_text(encoding="utf-8")
    heading = f"## {today}"
    if heading in text:
        # 오늘 날짜 섹션의 첫 줄 바로 아래에 prepend (최신이 위)
        text = text.replace(heading, f"{heading}\n\n{entry}", 1)
        # 원래 섹션 첫 항목과의 사이 빈줄 정리
        text = re.sub(rf"({re.escape(heading)}\n\n{re.escape(entry)})\n\n\n", r"\1\n\n", text)
    else:
        # 로그 제목(# ...) 바로 아래 새 날짜 섹션
        m = re.search(r"^# .*$", text, re.M)
        pos = m.end() if m else len(text)
        text = text[:pos] + f"\n\n{heading}\n\n{entry}" + text[pos:]
    log.write_text(text, encoding="utf-8")
    print(f"[ip_wiki] logged: {today} {title}")
    return 0


def cmd_page(ip_dir: str, name: str, title: str, tags: str) -> int:
    wiki = _wiki_dir(ip_dir)
    wiki.mkdir(parents=True, exist_ok=True)
    page = wiki / f"{name}.md"
    if page.is_file():
        print(f"[ip_wiki] page exists: {page}")
        return 0
    ip = Path(ip_dir).resolve().name
    tag_line = f"tags: [{tags}]\n" if tags else ""
    page.write_text(
        f"---\ntitle: {title}\nip: {ip}\ncategory: ip-wiki\n{tag_line}status: draft\n---\n\n"
        f"# {title}\n\n(작성 — 관련 히스토리는 [[log]] 참조)\n",
        encoding="utf-8")
    print(f"[ip_wiki] page created: {page}")
    return 0


def cmd_check(ip_dir: str) -> int:
    wiki = _wiki_dir(ip_dir)
    if not wiki.is_dir():
        print(f"[ip_wiki] FAIL: no wiki/ under {ip_dir} (run init)")
        return 1
    pages = sorted(wiki.glob("*.md"))
    if not pages:
        print("[ip_wiki] FAIL: wiki/ has no pages")
        return 1
    names = {p.stem for p in pages}
    issues = []
    for page in pages:
        text = page.read_text(encoding="utf-8", errors="replace")
        fm = _frontmatter(text)
        if fm is None:
            issues.append(f"{page.name}: missing frontmatter")
            continue
        for field in ("title", "ip", "category"):
            if not fm.get(field):
                issues.append(f"{page.name}: frontmatter missing '{field}'")
        for link in LINK_RE.findall(text):
            target = link.split("/")[-1]
            if target not in names:
                issues.append(f"{page.name}: broken link [[{link}]]")
    for required in ("index", "log"):
        if required not in names:
            issues.append(f"missing required page: {required}.md")
    if issues:
        for issue in issues:
            print(f"[ip_wiki] FAIL: {issue}")
        return 1
    print(f"[ip_wiki] PASS: {len(pages)} pages, frontmatter/links OK")
    return 0


def main(argv) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_init = sub.add_parser("init"); p_init.add_argument("ip_dir")
    p_log = sub.add_parser("log"); p_log.add_argument("ip_dir")
    p_log.add_argument("--title", required=True)
    p_log.add_argument("--body", default="")
    p_log.add_argument("--stage", default="")
    p_page = sub.add_parser("page"); p_page.add_argument("ip_dir"); p_page.add_argument("name")
    p_page.add_argument("--title", required=True)
    p_page.add_argument("--tags", default="")
    p_check = sub.add_parser("check"); p_check.add_argument("ip_dir")
    args = ap.parse_args(argv)
    if args.cmd == "init":
        return cmd_init(args.ip_dir)
    if args.cmd == "log":
        return cmd_log(args.ip_dir, args.title, args.body, args.stage)
    if args.cmd == "page":
        return cmd_page(args.ip_dir, args.name, args.title, args.tags)
    if args.cmd == "check":
        return cmd_check(args.ip_dir)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
