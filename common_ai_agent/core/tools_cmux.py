"""
core/tools_cmux.py — cmux integration tools for common_ai_agent

common_ai_agent가 cmux CLI를 통해 modifiable_ai_agent surface를
읽고 조작하는 도구 모음.

실제 cmux 명령어 (cmux --help 기준):
  cmux read-screen [--surface <ref>] [--lines <n>]      화면 텍스트 캡처
  cmux send [--surface <ref>] <text>                    텍스트 입력 전송
  cmux send-key [--surface <ref>] <key>                 키 전송 (ctrl+c 등)
  cmux notify --title <t> [--body <b>]                  알림 전송
  cmux respawn-pane [--surface <ref>] [--command <cmd>] pane 재시작
  cmux list-panes [--workspace <ref>]                   pane 목록
  cmux tree [--all]                                     전체 구조 출력
  cmux new-split <left|right|up|down>                   현재 pane 분할
  cmux new-workspace [--name] [--cwd] [--command]       새 workspace 생성
  cmux new-pane [--direction <dir>]                     현재 workspace에 탭형 pane 추가
  cmux focus-pane --pane <ref>                          pane 포커스 이동
  cmux resize-pane --pane <ref> (-L|-R|-U|-D) [--amount <n>]  pane 크기 조절
  cmux drag-surface-to-split --surface <ref> <dir>      surface를 split으로 이동
  cmux move-surface --surface <ref> [--pane <ref>]      surface를 다른 pane으로 이동
  cmux select-workspace --workspace <ref>               workspace 포커스
  cmux close-surface [--surface <ref>]                  surface 닫기
  cmux break-pane [--pane <ref>]                        pane을 독립 workspace로 분리
  cmux swap-pane --pane <ref> --target-pane <ref>       두 pane 위치 교환

환경변수 (cmux 터미널 내에서 자동 설정):
  CMUX_WORKSPACE_ID  현재 workspace ID
  CMUX_SURFACE_ID    현재 surface ID
  → --surface/--workspace 생략 시 현재 pane이 기본값
"""

import json
import os
import shlex
import subprocess
import time
from pathlib import Path

# modifiable_ai_agent surface 참조 — setup_cmux.sh가 저장하는 설정 파일
_CONFIG_PATH = Path.home() / ".config" / "agentic_test" / "surfaces.json"
_MOD_SURFACE_DEFAULT = "surface:1"   # fallback (setup 전)

# 프로젝트 .config 파일 (MODIFIABLE_DIR 등 읽기)
_PROJECT_CONFIG = Path(__file__).parent.parent / ".config"


def _read_project_config() -> dict:
    """프로젝트 .config 파일에서 KEY=VALUE 파싱."""
    result = {}
    if not _PROJECT_CONFIG.exists():
        return result
    for line in _PROJECT_CONFIG.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, _, v = line.partition("=")
            result[k.strip()] = v.strip()
    return result


def _mod_dir() -> str:
    """modifiable_ai_agent 디렉터리 경로를 반환한다."""
    # 1) 프로젝트 .config 우선
    cfg = _read_project_config()
    if cfg.get("MODIFIABLE_DIR"):
        p = Path(cfg["MODIFIABLE_DIR"])
        if p.exists():
            return str(p)

    # 2) 상위 디렉터리 후보 탐색
    base = Path(__file__).parent.parent.parent
    candidates = [
        base / "AGENTIC_TEST" / "modifiable_ai_agent",
        base / "brian_hw_modifiable",
        base / "modifiable_ai_agent",
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    return ""


def _mod_script(mod_dir: str) -> str:
    """modifiable_ai_agent 실행 스크립트 경로를 반환한다."""
    for sub in ["src/textual_main.py", "textual_main.py"]:
        p = Path(mod_dir) / sub
        if p.exists():
            return sub
    return "src/textual_main.py"  # fallback


def _run(cmd: str, timeout: int = 10) -> str:
    result = subprocess.run(
        cmd, shell=True, capture_output=True, text=True, timeout=timeout
    )
    out = (result.stdout or "").strip()
    err = (result.stderr or "").strip()
    if result.returncode != 0 and err:
        return f"Error (rc={result.returncode}): {err}"
    return out or "(no output)"


def _mod_surface() -> str:
    """설정 파일에서 modifiable surface ref 읽기."""
    if _CONFIG_PATH.exists():
        try:
            data = json.loads(_CONFIG_PATH.read_text())
            return data.get("modifiable_surface", _MOD_SURFACE_DEFAULT)
        except Exception:
            pass
    return _MOD_SURFACE_DEFAULT


# ── Tools ─────────────────────────────────────────────────────────────────────

def cmux_capture(lines: int = 200) -> str:
    """
    modifiable_ai_agent 화면 텍스트를 캡처한다.

    Args:
        lines: 캡처할 최대 라인 수 (기본: 200)

    Returns:
        화면 텍스트
    """
    surface = _mod_surface()
    return _run(f"cmux read-screen --surface {surface} --lines {lines}")


def cmux_send(text: str, capture_delay: float = 1.5, capture_lines: int = 80) -> str:
    """
    modifiable_ai_agent에 텍스트를 입력하고 Enter를 전송한 뒤, 화면을 캡처해 반환한다.

    Args:
        text:          전송할 텍스트
        capture_delay: 캡처 전 대기 시간 초 (기본: 1.5s — 명령 실행 완료 대기)
        capture_lines: 캡처할 라인 수 (기본: 80)

    Returns:
        화면 캡처 결과 (명령 실행 결과 확인 가능)
    """
    surface = _mod_surface()
    # 텍스트 전송 (cmux send는 Enter를 자동으로 붙이지 않음 → send-key enter 별도 전송)
    _run(f"cmux send --surface {surface} {shlex.quote(text)}")
    _run(f"cmux send-key --surface {surface} enter")
    time.sleep(capture_delay)
    screen = _run(f"cmux read-screen --surface {surface} --lines {capture_lines}")
    return f"Sent: {text!r}\n\n--- screen after ---\n{screen}"


def cmux_send_key(key: str) -> str:
    """
    modifiable_ai_agent에 특수 키를 전송한다.

    Args:
        key: 전송할 키 (예: 'ctrl+c', 'ctrl+q', 'enter', 'escape')

    Returns:
        성공/실패 메시지
    """
    surface = _mod_surface()
    safe = shlex.quote(key)
    result = _run(f"cmux send-key --surface {surface} {safe}")
    return f"Key '{key}' sent to modifiable ({surface})\n{result}"


def cmux_restart_modifiable() -> str:
    """
    modifiable_ai_agent를 종료하고 재시작한다.
    코드 수정 후 변경사항을 반영할 때 사용.

    Returns:
        재시작 후 화면 텍스트
    """
    surface = _mod_surface()
    mod_dir = _mod_dir()

    if not mod_dir:
        return (
            "Error: modifiable_ai_agent directory not found.\n"
            "Set MODIFIABLE_DIR in common_ai_agent/.config and retry."
        )

    script = _mod_script(mod_dir)

    # 1) Ctrl+Q 로 Textual 앱 종료 시도
    _run(f"cmux send-key --surface {surface} ctrl+q")
    time.sleep(0.8)

    # 2) 혹시 살아있으면 Ctrl+C
    _run(f"cmux send-key --surface {surface} ctrl+c")
    time.sleep(1.0)

    # 3) 재시작
    cmd = f"cd {shlex.quote(mod_dir)} && python3 {script}"
    _run(f"cmux send --surface {surface} {shlex.quote(cmd)}")
    time.sleep(2.5)

    # 4) 재시작 후 화면 확인
    screen = cmux_capture()
    return f"modifiable_ai_agent restarted ({mod_dir}).\n\nCurrent screen:\n{screen}"


def cmux_notify(title: str, body: str = "") -> str:
    """
    macOS 알림을 전송한다.

    Args:
        title: 알림 제목
        body:  알림 내용 (선택)

    Returns:
        성공/실패 메시지
    """
    cmd = f"cmux notify --title {shlex.quote(title)}"
    if body:
        cmd += f" --body {shlex.quote(body)}"
    return _run(cmd)


def cmux_tree() -> str:
    """
    현재 cmux workspace 전체 구조(pane/surface 목록)를 출력한다.
    surface ref 확인에 사용.

    Returns:
        workspace tree 텍스트
    """
    return _run("cmux tree")


def cmux_set_surface(surface_ref: str) -> str:
    """
    modifiable_ai_agent의 surface ref를 설정 파일에 저장한다.

    Args:
        surface_ref: cmux surface 참조 (예: 'surface:1', UUID)

    Returns:
        저장 완료 메시지
    """
    _CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = {}
    if _CONFIG_PATH.exists():
        try:
            data = json.loads(_CONFIG_PATH.read_text())
        except Exception:
            pass
    data["modifiable_surface"] = surface_ref
    _CONFIG_PATH.write_text(json.dumps(data, indent=2))
    return f"modifiable surface set to: {surface_ref}"


def cmux_new_split(direction: str = "right", command: str = "") -> str:
    """
    현재 pane을 분할하여 새 split pane을 만든다 (new-split).

    Args:
        direction: 분할 방향 — 'left', 'right', 'up', 'down' (기본: 'right')
        command:   새 pane에서 실행할 명령어 (선택)

    Returns:
        성공/실패 메시지 (새 surface ref 포함)
    """
    result = _run(f"cmux new-split {shlex.quote(direction)}")
    if command and "Error" not in result:
        time.sleep(0.5)
        _run(f"cmux send {shlex.quote(command)}")
    return f"Split {direction} created.\n{result}"


# backward-compat alias
def cmux_new_pane(direction: str = "right", command: str = "") -> str:
    """cmux_new_split의 별칭 (하위 호환)."""
    return cmux_new_split(direction=direction, command=command)


def cmux_new_workspace(name: str = "", command: str = "", cwd: str = "") -> str:
    """
    새 cmux workspace를 만든다.

    Args:
        name:    workspace 이름 (선택)
        command: 생성 후 실행할 명령어 (선택)
        cwd:     작업 디렉터리 (선택)

    Returns:
        성공/실패 메시지
    """
    cmd = "cmux new-workspace"
    if name:
        cmd += f" --name {shlex.quote(name)}"
    if cwd:
        cmd += f" --cwd {shlex.quote(cwd)}"
    if command:
        cmd += f" --command {shlex.quote(command)}"
    return _run(cmd)


def cmux_list_panes(workspace: str = "") -> str:
    """현재 workspace의 pane 목록을 반환한다."""
    cmd = "cmux list-panes"
    if workspace:
        cmd += f" --workspace {shlex.quote(workspace)}"
    return _run(cmd)


def cmux_focus_pane(pane: str) -> str:
    """
    특정 pane으로 포커스를 이동한다.

    Args:
        pane: pane ref (예: 'pane:1', 'pane:2')
    """
    return _run(f"cmux focus-pane --pane {shlex.quote(pane)}")


def cmux_resize_pane(pane: str, direction: str, amount: int = 5) -> str:
    """
    pane 크기를 조절한다.

    Args:
        pane:      pane ref (예: 'pane:1')
        direction: 'L' (왼쪽 확장) | 'R' (오른쪽 확장) | 'U' (위 확장) | 'D' (아래 확장)
        amount:    조절 크기 (기본: 5)
    """
    dir_flag = f"-{direction.upper()}"
    return _run(f"cmux resize-pane --pane {shlex.quote(pane)} {dir_flag} --amount {amount}")


def cmux_move_surface(surface: str, direction: str) -> str:
    """
    surface를 드래그해서 새 split pane으로 분리한다.

    Args:
        surface:   surface ref (예: 'surface:14')
        direction: 분리 방향 — 'left' | 'right' | 'up' | 'down'

    Returns:
        성공/실패 메시지
    """
    return _run(
        f"cmux drag-surface-to-split --surface {shlex.quote(surface)} {shlex.quote(direction)}"
    )


def cmux_select_workspace(workspace: str) -> str:
    """
    특정 workspace로 포커스를 이동한다.

    Args:
        workspace: workspace ref (예: 'workspace:1', 'workspace:2')

    Returns:
        성공/실패 메시지
    """
    return _run(f"cmux select-workspace --workspace {shlex.quote(workspace)}")


def cmux_close_surface(surface: str = "") -> str:
    """
    surface를 닫는다.

    Args:
        surface: surface ref (생략 시 현재 surface)

    Returns:
        성공/실패 메시지
    """
    cmd = "cmux close-surface"
    if surface:
        cmd += f" --surface {shlex.quote(surface)}"
    return _run(cmd)


def cmux_break_pane(pane: str = "") -> str:
    """
    pane을 독립적인 새 workspace로 분리한다 (break-pane).

    Args:
        pane: pane ref (생략 시 현재 pane)

    Returns:
        성공/실패 메시지
    """
    cmd = "cmux break-pane"
    if pane:
        cmd += f" --pane {shlex.quote(pane)}"
    return _run(cmd)


def cmux_swap_pane(pane: str, target_pane: str) -> str:
    """
    두 pane의 위치를 교환한다.

    Args:
        pane:        교환할 pane ref
        target_pane: 교환 대상 pane ref

    Returns:
        성공/실패 메시지
    """
    return _run(
        f"cmux swap-pane --pane {shlex.quote(pane)} --target-pane {shlex.quote(target_pane)}"
    )


def cmux_rename_workspace(name: str, workspace: str = "") -> str:
    """
    workspace 이름을 변경한다.

    Args:
        name:      새 이름
        workspace: workspace ref (생략 시 현재 workspace)

    Returns:
        성공/실패 메시지
    """
    # rename-workspace [--workspace <ref>] <title>
    cmd = "cmux rename-workspace"
    if workspace:
        cmd += f" --workspace {shlex.quote(workspace)}"
    cmd += f" {shlex.quote(name)}"
    return _run(cmd)


CMUX_TOOLS = {
    "cmux_capture":            cmux_capture,
    "cmux_send":               cmux_send,
    "cmux_send_key":           cmux_send_key,
    "cmux_restart_modifiable": cmux_restart_modifiable,
    "cmux_notify":             cmux_notify,
    "cmux_tree":               cmux_tree,
    "cmux_set_surface":        cmux_set_surface,
    "cmux_new_split":          cmux_new_split,
    "cmux_new_pane":           cmux_new_pane,          # alias → cmux_new_split
    "cmux_new_workspace":      cmux_new_workspace,
    "cmux_list_panes":         cmux_list_panes,
    "cmux_focus_pane":         cmux_focus_pane,
    "cmux_resize_pane":        cmux_resize_pane,
    "cmux_move_surface":       cmux_move_surface,
    "cmux_select_workspace":   cmux_select_workspace,
    "cmux_close_surface":      cmux_close_surface,
    "cmux_break_pane":         cmux_break_pane,
    "cmux_swap_pane":          cmux_swap_pane,
    "cmux_rename_workspace":   cmux_rename_workspace,
}
