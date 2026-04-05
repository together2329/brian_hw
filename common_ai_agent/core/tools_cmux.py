"""
core/tools_cmux.py — cmux integration tools for action_ai_agent

action_ai_agent가 cmux CLI를 통해 modifiable_ai_agent surface를
읽고 조작하는 도구 모음.

cmux 명령어:
  cmux read-screen --surface <ref>         화면 텍스트 캡처
  cmux send --surface <ref> <text>         텍스트 입력 전송
  cmux send-key --surface <ref> <key>      키 전송 (ctrl+c 등)
  cmux notify --title <t> --body <b>       알림 전송
  cmux respawn-pane --surface <ref>        pane 재시작
  cmux list-panes --workspace <ref>        pane 목록
  cmux tree                                전체 구조 출력
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


def cmux_send(text: str) -> str:
    """
    modifiable_ai_agent에 텍스트를 입력한다 (Enter 자동 추가).

    Args:
        text: 전송할 텍스트

    Returns:
        성공/실패 메시지
    """
    surface = _mod_surface()
    safe = shlex.quote(text)
    result = _run(f"cmux send --surface {surface} {safe}")
    return f"Sent to modifiable ({surface}): {text!r}\n{result}"


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
    mod_dir = str(Path(__file__).parent.parent.parent / "modifiable_ai_agent")

    # 1) Ctrl+Q 로 Textual 앱 종료 시도
    _run(f"cmux send-key --surface {surface} ctrl+q")
    time.sleep(0.8)

    # 2) 혹시 살아있으면 Ctrl+C
    _run(f"cmux send-key --surface {surface} ctrl+c")
    time.sleep(1.0)

    # 3) 재시작
    cmd = f"cd {shlex.quote(mod_dir)} && python3 src/textual_main.py"
    _run(f"cmux send --surface {surface} {shlex.quote(cmd)}")
    time.sleep(2.5)

    # 4) 재시작 후 화면 확인
    screen = cmux_capture()
    return f"modifiable_ai_agent restarted.\n\nCurrent screen:\n{screen}"


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


def cmux_new_pane(direction: str = "right", command: str = "") -> str:
    """
    현재 workspace에 새 pane을 만든다 (split).

    Args:
        direction: 분할 방향 — 'left', 'right', 'up', 'down' (기본: 'right')
        command:   새 pane에서 실행할 명령어 (선택)

    Returns:
        성공/실패 메시지
    """
    cmd = f"cmux new-pane --direction {shlex.quote(direction)}"
    result = _run(cmd)
    if command:
        import time
        time.sleep(0.5)
        safe = shlex.quote(command)
        _run(f"cmux send {safe}")
    return f"New pane ({direction}) created.\n{result}"


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


CMUX_TOOLS = {
    "cmux_capture":            cmux_capture,
    "cmux_send":               cmux_send,
    "cmux_send_key":           cmux_send_key,
    "cmux_restart_modifiable": cmux_restart_modifiable,
    "cmux_notify":             cmux_notify,
    "cmux_tree":               cmux_tree,
    "cmux_set_surface":        cmux_set_surface,
    "cmux_new_pane":           cmux_new_pane,
    "cmux_new_workspace":      cmux_new_workspace,
}
