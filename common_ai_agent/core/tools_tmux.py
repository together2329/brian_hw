"""
core/tools_tmux.py — tmux integration tools for action_ai_agent

Allows action_ai_agent to observe and control modifiable_ai_agent
running in a separate tmux pane.

Session layout:
    agentic:0.0 (left)  — modifiable_ai_agent (textual_main.py)
    agentic:0.1 (right) — action_ai_agent     (textual_main.py)
"""

import subprocess
import time

TMUX_SESSION = "agentic"
MOD_PANE     = f"{TMUX_SESSION}:0.0"   # modifiable_ai_agent
MOD_DIR      = "modifiable_ai_agent"


def _run(cmd: str, timeout: int = 10) -> str:
    result = subprocess.run(
        cmd, shell=True, capture_output=True, text=True, timeout=timeout
    )
    out = result.stdout or ""
    err = result.stderr or ""
    return (out + err).strip()


def tmux_capture(pane: str = MOD_PANE, lines: int = 200) -> str:
    """
    modifiable_ai_agent pane의 현재 화면 텍스트를 캡처한다.

    Args:
        pane:  tmux pane 주소 (기본: agentic:0.0)
        lines: 캡처할 최대 라인 수 (기본: 200)

    Returns:
        pane 화면 텍스트 (ANSI 코드 제거)
    """
    # -e: escape sequences 포함, -p: stdout 출력
    raw = _run(f"tmux capture-pane -t {pane} -p -e")
    if not raw:
        raw = _run(f"tmux capture-pane -t {pane} -p")
    # 마지막 N줄만 반환 (너무 길면 컨텍스트 낭비)
    tail = "\n".join(raw.splitlines()[-lines:])
    return tail or f"(pane {pane} is empty or not found)"


def tmux_send_keys(keys: str, pane: str = MOD_PANE) -> str:
    """
    modifiable_ai_agent pane에 키 입력을 전송한다.

    Args:
        keys: 전송할 텍스트 (Enter 자동 추가)
        pane: tmux pane 주소 (기본: agentic:0.0)

    Returns:
        성공/실패 메시지
    """
    safe = keys.replace("'", "'\\''")
    result = _run(f"tmux send-keys -t {pane} '{safe}' Enter")
    return f"Sent to {pane}: {keys!r}" + (f"\n{result}" if result else "")


def tmux_restart_modifiable() -> str:
    """
    modifiable_ai_agent를 종료하고 재시작한다.
    코드 수정 후 변경사항을 반영할 때 사용.

    Returns:
        재시작 완료 메시지
    """
    # 1) Ctrl-Q로 Textual 앱 정상 종료 시도
    _run(f"tmux send-keys -t {MOD_PANE} 'q' ''")
    time.sleep(0.5)
    # 2) 혹시 살아있으면 Ctrl-C
    _run(f"tmux send-keys -t {MOD_PANE} C-c ''")
    time.sleep(1.0)
    # 3) 재시작
    _run(
        f"tmux send-keys -t {MOD_PANE} "
        f"'cd /Users/brian/Desktop/Project/AGENTIC_TEST/{MOD_DIR} && "
        f"python3 src/textual_main.py' Enter"
    )
    time.sleep(2.0)
    # 4) 재시작 후 화면 확인
    screen = tmux_capture()
    return f"modifiable_ai_agent restarted.\n\nCurrent screen:\n{screen}"


def tmux_split(direction: str = "h", command: str = "", pane: str = f"{TMUX_SESSION}:0") -> str:
    """
    tmux pane을 분할하고 선택적으로 명령어를 실행한다.

    Args:
        direction: 'h' (좌우) 또는 'v' (위아래)
        command:   새 pane에서 실행할 명령어 (빈 문자열이면 shell만 열림)
        pane:      분할할 대상 pane (기본: agentic:0)

    Returns:
        새 pane 주소
    """
    flag = "-h" if direction == "h" else "-v"
    cmd_part = f" '{command}'" if command else ""
    result = _run(f"tmux split-window {flag} -t {pane} -P -F '#{{pane_id}}'{cmd_part}")
    return f"New pane: {result}"


def tmux_list_panes() -> str:
    """
    현재 tmux 세션의 모든 pane 목록과 실행 중인 명령어를 반환한다.

    Returns:
        pane 목록 텍스트
    """
    fmt = "'#{pane_index}: #{pane_id} [#{pane_width}x#{pane_height}] #{pane_current_command}'"
    return _run(f"tmux list-panes -t {TMUX_SESSION} -F {fmt}")


def tmux_focus(pane: str) -> str:
    """
    특정 pane으로 포커스를 이동한다.

    Args:
        pane: 포커스할 pane 주소 (예: 'agentic:0.1')

    Returns:
        성공/실패 메시지
    """
    result = _run(f"tmux select-pane -t {pane}")
    return f"Focused: {pane}" + (f"\n{result}" if result else "")


def tmux_new_window(name: str = "", command: str = "") -> str:
    """
    tmux 세션에 새 window를 만든다.

    Args:
        name:    window 이름 (선택)
        command: window에서 실행할 명령어 (선택)

    Returns:
        새 window 정보
    """
    name_part = f" -n '{name}'" if name else ""
    cmd_part  = f" '{command}'" if command else ""
    result = _run(f"tmux new-window -t {TMUX_SESSION}{name_part} -P -F '#{{window_index}}'{cmd_part}")
    return f"New window: {result}"


def tmux_kill_pane(pane: str) -> str:
    """
    특정 pane을 종료한다.

    Args:
        pane: 종료할 pane 주소 (예: 'agentic:0.2')

    Returns:
        성공/실패 메시지
    """
    result = _run(f"tmux kill-pane -t {pane}")
    return f"Killed: {pane}" + (f"\n{result}" if result else "")


TMUX_TOOLS = {
    "tmux_capture":            tmux_capture,
    "tmux_send_keys":          tmux_send_keys,
    "tmux_restart_modifiable": tmux_restart_modifiable,
    "tmux_split":              tmux_split,
    "tmux_list_panes":         tmux_list_panes,
    "tmux_focus":              tmux_focus,
    "tmux_new_window":         tmux_new_window,
    "tmux_kill_pane":          tmux_kill_pane,
}
