# Keepalive ("keep going") 버그 진단 및 수정

## 문제 요약

`KEEPALIVE_INTERVAL` 설정 시 자동으로 "keep going" 메시지를 주입하는 기능이 **동작하지 않았음**.

## 근본 원인

기존 코드의 두 가지 injection 경로 모두 실패:

### 1. `app.exit(result=msg)` — 백그라운드 스레드에서 직접 호출
- `prompt_toolkit`의 `Application.exit()`은 이벤트 루프 안에서만 동작
- `self.future is None`인 경우 `Exception("Application is not running")` 발생
- `except: pass`로 묶여 있어 **조용히 무시됨**

### 2. `os.write(sys.stdin.fileno(), msg)` — stdin에 직접 write
- `prompt_toolkit`은 `/dev/tty`에서 읽지 `sys.stdin`에서 읽지 않음
- 따라서 stdin에 write해도 **입력으로 인식되지 않음**

### 3. `_keepalive_waiting` 상태 관리 불필요
- 입력 대기 상태를 수동으로 `True/False` 토글 → 타이밍 버그 가능
- LLM 작업 중에도 타이머가 계속 돌아서 잘못된 시점에 발동 가능

## 수정 내용 (근본 해결)

### 핵심 변경사항

| 항목 | 기존 (❌) | 수정 (✅) |
|------|-----------|-----------|
| 주입 방식 | `app.exit()` 직접 호출 | `loop.call_soon_threadsafe(app.exit)` |
| 대체 경로 | `sys.stdin` write | `/dev/tty` write |
| 타이머 관리 | `_keepalive_waiting` 수동 토글 | `_keepalive_last_activity` 리셋만 |
| 폴링 간격 | 60초 | 5초 (더 빠른 반응) |
| pre_run hook | 없음 | `_keepalive_arm()` 등록 |

### 상세 설명

#### 1. `call_soon_threadsafe` + `app.exit()` (Path A)
```python
_loop = _app.loop
_loop.call_soon_threadsafe(lambda: _app.exit(result=_full_msg))
```
- 백그라운드 스레드에서 **이벤트 루프 스레드로 안전하게** `app.exit()` 예약
- `prompt_toolkit` 공식 패턴 (`progress_bar/base.py` 245라인에서 동일 방식 사용)
- `self.future`가 유효한 상태에서 실행되므로 정상 종료

#### 2. `/dev/tty` write (Path B — fallback)
```python
_tty_fd = os.open('/dev/tty', os.O_RDWR | os.O_NOCTTY)
os.write(_tty_fd, (msg + "\n").encode())
```
- `prompt_toolkit`이 없거나 이벤트 루프를 얻을 수 없는 경우
- 터미널이 실제로 읽는 `/dev/tty`에 write

#### 3. 타이머 설계
- **LLM 작업 중**: 타이머 리셋 안 함 → 마지막 사용자 입력 시점부터 카운트
- **프롬프트 표시 시**: `pre_run_callables` + 루프 시작점에서 리셋
- **사용자 입력 완료 시**: 리셋 (활동 감지)
- 타이머가 interval을 넘으면 → keepalive 발동 → 리셋

#### 4. `_keepalive_waiting` 제거
- 더 이상 "입력 대기 중" 플래그가 필요 없음
- 타이머는 항상 마지막 활동 시점 기준으로만 동작
- LLM이 길게 돌면 → idle이 길어짐 → BUT 프롬프트가 표시되는 순간 리셋됨
- 실제로는 프롬프트 표시 후 interval초 동안 사용자가 아무 입력 안 할 때만 발동

## 파일 변경

- `src/main.py` lines 1296-1399: keepalive 섹션 전면 재작성
- `src/main.py` lines 1406-1409: `_keepalive_waiting` → timer reset
- `src/main.py` line 1461: `_keepalive_waiting = False` → timer reset

## 테스트 방법

```bash
KEEPALIVE_INTERVAL=30 KEEPALIVE_MESSAGE="keep going" python src/main.py
```

1. 프롬프트가 표시된 후 30초 대기
2. `[Keepalive] No activity for 30s — injecting keepalive` 출력
3. 자동으로 "keep going"이 입력되어 LLM이 계속 진행
