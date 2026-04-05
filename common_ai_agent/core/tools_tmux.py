"""
core/tools_tmux.py — tmux integration tools for common_ai_agent

Allows common_ai_agent to observe and control modifiable_ai_agent
running in a separate tmux pane.

실제 tmux 명령어 (tmux list-commands 기준):
  capture-pane  -t <pane> -p [-e]               화면 텍스트 캡처
  send-keys     -t <pane> <keys> Enter           키 입력 전송
  split-window  [-h|-v] -t <pane> [command]      pane 분할
  select-pane   -t <pane>                        pane 포커스
  kill-pane     -t <pane>                        pane 종료
  list-panes    [-a] [-t <session>]              pane 목록
  list-sessions                                  세션 목록
  new-session   [-s <name>] [-c <dir>] [cmd]     새 세션 생성
  new-window    [-n <name>] [-t <session>] [cmd] 새 window 생성
  rename-window -t <window> <name>               window 이름 변경
  kill-session  -t <session>                     세션 종료
  resize-pane   -t <pane> [-D|-U|-L|-R] [n]      pane 크기 조절
  respawn-pane  -t <pane> [command]              pane 재시작
  swap-pane     -s <src> -t <dst>                pane 위치 교환
  move-pane     -s <src> -t <dst> [-h|-v]        pane 이동
  break-pane    -t <pane>                        pane을 독립 window로 분리
"""

import shlex
import subprocess
import time
from pathlib import Path

TMUX_SESSION = "agentic"
MOD_PANE     = f"{TMUX_SESSION}:0.0"   # modifiable_ai_agent (기본 fallback)

_PROJECT_CONFIG = Path(__file__).parent.parent / ".config"


def _read_project_config() -> dict:
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
    cfg = _read_project_config()
    if cfg.get("MODIFIABLE_DIR"):
        p = Path(cfg["MODIFIABLE_DIR"])
        if p.exists():
            return str(p)
    base = Path(__file__).parent.parent.parent
    for c in [
        base / "AGENTIC_TEST" / "modifiable_ai_agent",
        base / "brian_hw_modifiable",
        base / "modifiable_ai_agent",
    ]:
        if c.exists():
            return str(c)
    return ""


def _mod_script(mod_dir: str) -> str:
    for sub in ["src/textual_main.py", "textual_main.py"]:
        if (Path(mod_dir) / sub).exists():
            return sub
    return "src/textual_main.py"


def _run(cmd: str, timeout: int = 10) -> str:
    result = subprocess.run(
        cmd, shell=True, capture_output=True, text=True, timeout=timeout
    )
    out = (result.stdout or "").strip()
    err = (result.stderr or "").strip()
    if result.returncode != 0 and err:
        return f"Error (rc={result.returncode}): {err}"
    return out or "(no output)"


# ── Tools ─────────────────────────────────────────────────────────────────────

def tmux_capture(pane: str = MOD_PANE, lines: int = 200) -> str:
    """
    tmux pane의 현재 화면 텍스트를 캡처한다.

    Args:
        pane:  tmux pane 주소 (기본: agentic:0.0)
        lines: 캡처할 최대 라인 수 (기본: 200)

    Returns:
        pane 화면 텍스트
    """
    # -e: ANSI escape sequences 포함, -p: stdout 출력
    raw = _run(f"tmux capture-pane -t {shlex.quote(pane)} -p -e")
    if raw.startswith("Error"):
        raw = _run(f"tmux capture-pane -t {shlex.quote(pane)} -p")
    tail = "\n".join(raw.splitlines()[-lines:])
    return tail or f"(pane {pane} is empty or not found)"


def tmux_send_keys(keys: str, pane: str = MOD_PANE) -> str:
    """
    tmux pane에 키 입력을 전송한다 (Enter 자동 추가).

    Args:
        keys: 전송할 텍스트 또는 키 (예: 'hello', 'C-c', 'C-q')
        pane: tmux pane 주소 (기본: agentic:0.0)

    Returns:
        성공/실패 메시지
    """
    result = _run(f"tmux send-keys -t {shlex.quote(pane)} {shlex.quote(keys)} Enter")
    return f"Sent to {pane}: {keys!r}" + (f"\n{result}" if result and result != "(no output)" else "")


def tmux_send_key_noenter(key: str, pane: str = MOD_PANE) -> str:
    """
    tmux pane에 특수 키를 전송한다 (Enter 없음).

    Args:
        key:  전송할 키 (예: 'C-c', 'C-q', 'Escape', 'q')
        pane: tmux pane 주소 (기본: agentic:0.0)

    Returns:
        성공/실패 메시지
    """
    result = _run(f"tmux send-keys -t {shlex.quote(pane)} {shlex.quote(key)}")
    return f"Key '{key}' sent to {pane}" + (f"\n{result}" if result and result != "(no output)" else "")


def tmux_restart_modifiable(mod_dir: str = "", pane: str = MOD_PANE) -> str:
    """
    modifiable_ai_agent를 종료하고 재시작한다.
    코드 수정 후 변경사항을 반영할 때 사용.

    Args:
        mod_dir: modifiable_ai_agent 디렉터리 경로 (생략 시 자동 탐색)
        pane:    tmux pane 주소 (기본: agentic:0.0)

    Returns:
        재시작 후 화면 텍스트
    """
    if not mod_dir:
        mod_dir = _mod_dir()
    if not mod_dir:
        return "Error: modifiable_ai_agent directory not found. Set MODIFIABLE_DIR in .config."

    # 1) Ctrl+Q로 Textual 앱 정상 종료
    _run(f"tmux send-keys -t {shlex.quote(pane)} C-q")
    time.sleep(0.8)

    # 2) 혹시 살아있으면 Ctrl+C
    _run(f"tmux send-keys -t {shlex.quote(pane)} C-c")
    time.sleep(1.0)

    script = _mod_script(mod_dir)
    # 3) 재시작
    cmd = f"cd {shlex.quote(mod_dir)} && python3 {script}"
    _run(f"tmux send-keys -t {shlex.quote(pane)} {shlex.quote(cmd)} Enter")
    time.sleep(2.5)

    # 4) 재시작 후 화면 확인
    screen = tmux_capture(pane=pane)
    return f"modifiable_ai_agent restarted.\n\nCurrent screen:\n{screen}"


def tmux_split(direction: str = "h", command: str = "", pane: str = f"{TMUX_SESSION}:0") -> str:
    """
    tmux pane을 분할하고 선택적으로 명령어를 실행한다.

    Args:
        direction: 'h' (좌우 분할) 또는 'v' (위아래 분할)
        command:   새 pane에서 실행할 명령어 (생략 시 shell)
        pane:      분할할 대상 pane (기본: agentic:0)

    Returns:
        새 pane ID
    """
    flag = "-h" if direction == "h" else "-v"
    cmd_part = f" {shlex.quote(command)}" if command else ""
    result = _run(
        f"tmux split-window {flag} -t {shlex.quote(pane)} -P -F '#{{pane_id}}'{cmd_part}"
    )
    return f"New pane: {result}"


def tmux_list_panes(session: str = TMUX_SESSION) -> str:
    """
    tmux 세션의 모든 pane 목록과 실행 중인 명령어를 반환한다.

    Args:
        session: tmux 세션 이름 (기본: agentic)

    Returns:
        pane 목록 텍스트
    """
    fmt = "#{pane_index}: #{pane_id} [#{pane_width}x#{pane_height}] #{pane_current_command} (#{pane_title})"
    return _run(f"tmux list-panes -t {shlex.quote(session)} -F {shlex.quote(fmt)}")


def tmux_list_sessions() -> str:
    """
    현재 tmux 서버의 모든 세션 목록을 반환한다.

    Returns:
        세션 목록 텍스트
    """
    fmt = "#{session_name}: #{session_windows} windows (created #{session_created_string})"
    return _run(f"tmux list-sessions -F {shlex.quote(fmt)}")


def tmux_focus(pane: str) -> str:
    """
    특정 pane으로 포커스를 이동한다.

    Args:
        pane: 포커스할 pane 주소 (예: 'agentic:0.1', '%3')

    Returns:
        성공/실패 메시지
    """
    result = _run(f"tmux select-pane -t {shlex.quote(pane)}")
    return f"Focused: {pane}" + (f"\n{result}" if result and result != "(no output)" else "")


def tmux_new_window(name: str = "", command: str = "", session: str = TMUX_SESSION) -> str:
    """
    tmux 세션에 새 window를 만든다.

    Args:
        name:    window 이름 (선택)
        command: window에서 실행할 명령어 (선택)
        session: tmux 세션 이름 (기본: agentic)

    Returns:
        새 window 인덱스
    """
    name_part = f" -n {shlex.quote(name)}" if name else ""
    cmd_part  = f" {shlex.quote(command)}" if command else ""
    result = _run(
        f"tmux new-window -t {shlex.quote(session)}{name_part} -P -F '#{{window_index}}'{cmd_part}"
    )
    return f"New window: {result}"


def tmux_new_session(name: str, command: str = "", cwd: str = "") -> str:
    """
    새 tmux 세션을 생성한다.

    Args:
        name:    세션 이름
        command: 세션에서 실행할 명령어 (선택)
        cwd:     작업 디렉터리 (선택)

    Returns:
        성공/실패 메시지
    """
    cmd = f"tmux new-session -d -s {shlex.quote(name)}"
    if cwd:
        cmd += f" -c {shlex.quote(cwd)}"
    if command:
        cmd += f" {shlex.quote(command)}"
    result = _run(cmd)
    return f"Session '{name}' created." + (f"\n{result}" if result and result != "(no output)" else "")


def tmux_kill_pane(pane: str) -> str:
    """
    특정 pane을 종료한다.

    Args:
        pane: 종료할 pane 주소 (예: 'agentic:0.2', '%3')

    Returns:
        성공/실패 메시지
    """
    result = _run(f"tmux kill-pane -t {shlex.quote(pane)}")
    return f"Killed: {pane}" + (f"\n{result}" if result and result != "(no output)" else "")


def tmux_kill_session(session: str) -> str:
    """
    tmux 세션을 종료한다.

    Args:
        session: 종료할 세션 이름

    Returns:
        성공/실패 메시지
    """
    result = _run(f"tmux kill-session -t {shlex.quote(session)}")
    return f"Session '{session}' killed." + (f"\n{result}" if result and result != "(no output)" else "")


def tmux_resize_pane(pane: str, direction: str, amount: int = 5) -> str:
    """
    tmux pane 크기를 조절한다.

    Args:
        pane:      pane 주소 (예: 'agentic:0.0', '%3')
        direction: 'D' (아래) | 'U' (위) | 'L' (왼쪽) | 'R' (오른쪽)
        amount:    조절 크기 (기본: 5)

    Returns:
        성공/실패 메시지
    """
    flag = f"-{direction.upper()}"
    result = _run(f"tmux resize-pane -t {shlex.quote(pane)} {flag} {amount}")
    return f"Resized {pane} {direction} by {amount}." + (f"\n{result}" if result and result != "(no output)" else "")


def tmux_rename_window(name: str, window: str = f"{TMUX_SESSION}:0") -> str:
    """
    tmux window 이름을 변경한다.

    Args:
        name:   새 window 이름
        window: 대상 window 주소 (기본: agentic:0)

    Returns:
        성공/실패 메시지
    """
    result = _run(f"tmux rename-window -t {shlex.quote(window)} {shlex.quote(name)}")
    return f"Window '{window}' renamed to '{name}'." + (f"\n{result}" if result and result != "(no output)" else "")


def tmux_swap_pane(src: str, dst: str) -> str:
    """
    두 tmux pane의 위치를 교환한다.

    Args:
        src: 교환할 pane 주소
        dst: 교환 대상 pane 주소

    Returns:
        성공/실패 메시지
    """
    result = _run(f"tmux swap-pane -s {shlex.quote(src)} -t {shlex.quote(dst)}")
    return f"Swapped {src} ↔ {dst}." + (f"\n{result}" if result and result != "(no output)" else "")


def tmux_break_pane(pane: str) -> str:
    """
    tmux pane을 독립적인 새 window로 분리한다 (break-pane).

    Args:
        pane: 분리할 pane 주소

    Returns:
        성공/실패 메시지
    """
    result = _run(f"tmux break-pane -t {shlex.quote(pane)}")
    return f"Pane {pane} broken out." + (f"\n{result}" if result and result != "(no output)" else "")


TMUX_TOOLS = {
    "tmux_capture":            tmux_capture,
    "tmux_send_keys":          tmux_send_keys,
    "tmux_send_key_noenter":   tmux_send_key_noenter,
    "tmux_restart_modifiable": tmux_restart_modifiable,
    "tmux_split":              tmux_split,
    "tmux_list_panes":         tmux_list_panes,
    "tmux_list_sessions":      tmux_list_sessions,
    "tmux_focus":              tmux_focus,
    "tmux_new_window":         tmux_new_window,
    "tmux_new_session":        tmux_new_session,
    "tmux_kill_pane":          tmux_kill_pane,
    "tmux_kill_session":       tmux_kill_session,
    "tmux_resize_pane":        tmux_resize_pane,
    "tmux_rename_window":      tmux_rename_window,
    "tmux_swap_pane":          tmux_swap_pane,
    "tmux_break_pane":         tmux_break_pane,
}
