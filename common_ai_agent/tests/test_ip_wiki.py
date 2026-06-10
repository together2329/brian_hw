"""ip_wiki 헬퍼 검증 — 라운드트립 + check kill-proof.

evidence for: OBL_IP_WIKI_HELPER, OBL_IP_WIKI_CHECK_KILLPROOF
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("ip_wiki", REPO / "scripts" / "ip_wiki.py")
ipw = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ipw)


def test_init_log_check_roundtrip(tmp_path, capsys):
    ip = tmp_path / "uart_v1"
    ip.mkdir()
    assert ipw.main(["init", str(ip)]) == 0
    assert (ip / "wiki" / "index.md").is_file()
    assert (ip / "wiki" / "log.md").is_file()

    assert ipw.main(["log", str(ip), "--title", "rtl 게이트 통과", "--stage", "rtl",
                     "--body", "lint PASS\ncompile PASS"]) == 0
    assert ipw.main(["log", str(ip), "--title", "sim 28/28", "--stage", "sim"]) == 0
    text = (ip / "wiki" / "log.md").read_text(encoding="utf-8")
    assert "rtl 게이트 통과" in text and "sim 28/28" in text
    assert "`[rtl]`" in text and "  lint PASS" in text
    # 같은 날짜 섹션은 하나, 최신 항목이 위
    assert text.count("## ") == 1
    assert text.index("sim 28/28") < text.index("rtl 게이트 통과")

    assert ipw.main(["check", str(ip)]) == 0
    assert "PASS" in capsys.readouterr().out


def test_init_is_idempotent(tmp_path):
    ip = tmp_path / "ip"
    ip.mkdir()
    ipw.main(["init", str(ip)])
    ipw.main(["log", str(ip), "--title", "내용 보존 확인"])
    ipw.main(["init", str(ip)])  # 재실행이 로그를 덮으면 안 됨
    assert "내용 보존 확인" in (ip / "wiki" / "log.md").read_text(encoding="utf-8")


def test_page_creation_and_link_resolution(tmp_path):
    ip = tmp_path / "ip"
    ip.mkdir()
    ipw.main(["init", str(ip)])
    assert ipw.main(["page", str(ip), "fsm-design", "--title", "FSM 설계 결정"]) == 0
    fm = ipw._frontmatter((ip / "wiki" / "fsm-design.md").read_text(encoding="utf-8"))
    assert fm["title"] == "FSM 설계 결정" and fm["category"] == "ip-wiki"
    assert ipw.main(["check", str(ip)]) == 0  # 새 page의 [[log]] 링크가 해소됨


def test_check_killproof_broken_frontmatter(tmp_path, capsys):
    """KILL-PROOF: frontmatter 없는 페이지는 잡혀야 한다."""
    ip = tmp_path / "ip"
    ip.mkdir()
    ipw.main(["init", str(ip)])
    (ip / "wiki" / "rogue.md").write_text("# frontmatter 없음\n", encoding="utf-8")
    assert ipw.main(["check", str(ip)]) == 1
    assert "missing frontmatter" in capsys.readouterr().out


def test_check_killproof_ghost_link(tmp_path, capsys):
    """KILL-PROOF: 존재하지 않는 [[link]] 는 잡혀야 한다."""
    ip = tmp_path / "ip"
    ip.mkdir()
    ipw.main(["init", str(ip)])
    idx = ip / "wiki" / "index.md"
    idx.write_text(idx.read_text(encoding="utf-8") + "\n[[ghost-page]]\n", encoding="utf-8")
    assert ipw.main(["check", str(ip)]) == 1
    assert "broken link" in capsys.readouterr().out


def test_check_killproof_missing_wiki(tmp_path):
    ip = tmp_path / "no_wiki_ip"
    ip.mkdir()
    assert ipw.main(["check", str(ip)]) == 1
