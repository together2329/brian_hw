# Brian Coder `/context` Command - Implementation Summary

## 개요
Claude Code 스타일의 실시간 토큰 사용량 시각화 기능을 brian_coder에 구현했습니다.

## 구현된 기능

### 1. Context Tracker (`core/context_tracker.py`)
- 실시간 토큰 사용량 추적
- Claude Code 스타일 시각화 (⛁ ⛀ ⛶ 문자 사용)
- API 실제 토큰 vs 추정치 지원

### 2. Slash Command (`/context`)
- **일반 모드**: `/context`
  - 실제 API 토큰 수 표시 (API 호출 후)
  - 추정치 표시 (API 호출 전)

- **디버그 모드**: `/context debug`
  - 상세 내부 정보 표시
  - 토큰 카운팅 검증용

### 3. Main.py 통합
- `chat_loop()` 시작 시 tracker 초기화
- `/context` 실행 시 자동으로 최신 상태 업데이트
- `llm_client.last_input_tokens` 활용

## 사용 예시

### API 호출 전 (추정치)
```
 Context Usage
 ⛁ ⛀ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶   openai/gpt-oss-120b · 13.0k/65.5k tokens (19.8%) [estimated]
 ⛁ ⛀ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶   ⛁ System (includes tools, memory, graph): 13.0k tokens (19.8%)
 ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶   ⛶ Free space: 52.6k (80.2%)
```

### API 호출 후 (실제 값)
```
 Context Usage
 ⛁ ⛀ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶   openai/gpt-oss-120b · 55.3k/65.5k tokens (84.4%) [API actual]
 ⛁ ⛀ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶   ⛁ System (includes tools, memory, graph): 13.0k tokens (19.8%)
 ⛁ ⛁ ⛁ ⛁ ⛁ ⛁ ⛶ ⛶ ⛶ ⛶   ⛁ Messages (user/assistant): 42.4k tokens (64.6%)
 ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶ ⛶   ⛶ Free space: 10.2k (15.6%)

💡 Tip: Use /clear to free up context
💡 Tip: Use /compact to summarize old messages
💡 Tip: Use /context debug for detailed info
```

### 디버그 모드
```
=== DEBUG INFO ===
  llm_client.last_input_tokens: 55,324
  actual_total: 55,324
  tracker.system_prompt_tokens: 12,966
  tracker.messages_tokens: 33
  config.MAX_CONTEXT_CHARS: 262,144
  tracker.max_tokens: 65,536
==================
```

## 검증

### 테스트 결과
- ✅ API reported: 55,324 tokens
- ✅ Displayed total: 55,324 tokens
- ✅ System: 13.0k tokens (19.8%)
- ✅ Messages: 42.4k tokens (64.6%)
- ✅ **완벽히 일치!**

### 테스트 파일
- `test_context_command.py` - 기본 기능 테스트
- `test_context_api.py` - API 토큰 통합 테스트
- `test_context_live.py` - 실시간 시뮬레이션
- `test_main_direct.py` - main.py 통합 테스트

## 수정된 파일

1. **새 파일**
   - `brian_coder/core/context_tracker.py` - Context tracking 모듈

2. **수정 파일**
   - `brian_coder/core/slash_commands.py` - `/context` 명령어 개선
   - `brian_coder/src/main.py` - tracker 초기화 및 업데이트

## 주요 개선 사항

### 1. 정확한 토큰 카운팅
- API의 실제 토큰 수(`last_input_tokens`) 사용
- 추정치와 실제 값을 명확히 구분 표시
- System prompt와 Messages 중복 계산 방지

### 2. Claude Code 스타일 UI
- Progress bar 시각화 (⛁ ⛀ ⛶)
- 퍼센티지 및 절대값 표시
- `[API actual]` vs `[estimated]` 구분

### 3. 디버깅 편의성
- `/context debug` 모드
- 내부 상태 확인 가능
- 토큰 카운팅 검증 용이

## 사용 방법

1. **Brian Coder 실행**
   ```bash
   cd brian_coder
   python3 src/main.py
   ```

2. **일반 사용**
   ```
   You: /context
   ```

3. **디버그 모드**
   ```
   You: /context debug
   ```

## 결론

Brian Coder에 Claude Code 수준의 context tracking 기능이 성공적으로 구현되었습니다.
실제 API 토큰 수를 정확하게 표시하며, 디버그 모드로 내부 상태 확인도 가능합니다.
