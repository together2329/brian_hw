---
name: large-file-analyst
description: >
  1000줄 이상 대용량 파일 분석 시 호출. 병렬 explore 에이전트로 1000줄씩
  분할 스캔하여 빠르게 필요한 정보를 추출.
  Trigger on: '대용량 파일', 'large file', '전체 파일 분석', '파일 구조 파악',
  '함수 목록', '클래스 목록', '전체 내용', '파일 전체'.
priority: 85
activation:
  keywords: [
    "large file", "대용량", "전체 파일", "파일 전체", "전체 분석",
    "함수 목록", "클래스 목록", "파일 구조", "모든 함수", "전체 내용",
    "전체 로직", "전체 구조", "코드 분석", "소스 분석", "구조 파악"
  ]
  file_patterns: ["*.py", "*.js", "*.ts", "*.go", "*.java", "*.cpp", "*.c"]
  auto_detect: true
requires_tools: [run_command, read_lines, background_task]
---

# SKILL: Large File Analyst — MANDATORY PROTOCOL

**⚠️ OVERRIDE: 이 skill이 활성화된 경우, 기존 "grep_file first" 지시보다 아래 프로토콜이 우선합니다.**
**DO NOT use read_file or grep_file alone for large file analysis.**
**MUST use background_task parallel agents as described below.**

---

## MANDATORY Step 1: 파일 줄 수 확인

```
Action: run_command(command="wc -l <파일경로>")
```

→ 줄 수 파악 후 chunk_size 결정:
- 1K~3K줄: chunk_size=1000
- 3K~10K줄: chunk_size=1000
- 10K줄 이상: chunk_size=2000

---

## MANDATORY Step 2: 병렬 background_task 에이전트 실행

**반드시** 아래 형식으로 background_task를 동시 다발로 실행:

```
Action: background_task(agent="explore", prompt="<파일경로> 파일의 <start>~<end>줄을 read_lines(path='<파일경로>', start_line=<start>, end_line=<end>)로 읽고, <추출목표>를 찾아 [줄번호] 내용 형식으로 보고하라. 없으면 '해당 없음' 출력.")
Action: background_task(agent="explore", prompt="<파일경로> 파일의 <start2>~<end2>줄을 read_lines(path='<파일경로>', start_line=<start2>, end_line=<end2>)로 읽고, <추출목표>를 찾아 [줄번호] 내용 형식으로 보고하라. 없으면 '해당 없음' 출력.")
Action: background_task(agent="explore", prompt="<파일경로> 파일의 <start3>~<end3>줄을 read_lines(path='<파일경로>', start_line=<start3>, end_line=<end3>)로 읽고, <추출목표>를 찾아 [줄번호] 내용 형식으로 보고하라. 없으면 '해당 없음' 출력.")
```

- **한 배치에 최대 3개** (BACKGROUND_MAX_WORKERS=3 제한)
- 3개 완료 후 다음 배치 실행
- 마지막 청크는 실제 줄 수까지 (예: 4001~4425)

---

## MANDATORY Step 3: 결과 취합 후 최종 답변

모든 배치 완료 → background_output으로 결과 수집 → 통합하여 최종 답변 제공.

---

## 예시: src/main.py (4425줄), 함수 목록 추출

```
Action: run_command(command="wc -l src/main.py")
```

→ 4425줄 → chunk_size=1000 → 5개 청크 → 배치 2회

**배치 1** (동시 실행):
```
Action: background_task(agent="explore", prompt="src/main.py 파일의 1~1000줄을 read_lines(path='src/main.py', start_line=1, end_line=1000)로 읽고, def/class 정의를 [줄번호] 함수명/클래스명 형식으로 모두 추출하라.")
Action: background_task(agent="explore", prompt="src/main.py 파일의 1001~2000줄을 read_lines(path='src/main.py', start_line=1001, end_line=2000)로 읽고, def/class 정의를 [줄번호] 함수명/클래스명 형식으로 모두 추출하라.")
Action: background_task(agent="explore", prompt="src/main.py 파일의 2001~3000줄을 read_lines(path='src/main.py', start_line=2001, end_line=3000)로 읽고, def/class 정의를 [줄번호] 함수명/클래스명 형식으로 모두 추출하라.")
```

**배치 2** (배치 1 완료 후):
```
Action: background_task(agent="explore", prompt="src/main.py 파일의 3001~4000줄을 read_lines(path='src/main.py', start_line=3001, end_line=4000)로 읽고, def/class 정의를 [줄번호] 함수명/클래스명 형식으로 모두 추출하라.")
Action: background_task(agent="explore", prompt="src/main.py 파일의 4001~4425줄을 read_lines(path='src/main.py', start_line=4001, end_line=4425)로 읽고, def/class 정의를 [줄번호] 함수명/클래스명 형식으로 모두 추출하라.")
```

---

## Gotchas
- explore 에이전트는 저비용 모델 사용 — 비용 효율적
- 각 background_task prompt에 반드시 **정확한 파일 경로 + 줄 범위 + read_lines 호출** 명시
- `background_task` 없이 `read_file` 단독 사용 금지
- `grep_file` 단독으로 전체 분석 시도 금지 (부분 결과만 반환됨)
