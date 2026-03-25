---
name: code-analysis-expert
description: >
  코드베이스 탐색, 정의 찾기, 함수/신호 추적, 코드 구조 분석.
  특정 함수/클래스/심볼 위치 파악, 사용처 추적, call hierarchy 파악.
  Trigger on: 'find usage', 'trace', '어디에 있어', '코드 구조', 'call hierarchy',
  'definition', '함수 찾아', '클래스 찾아'.
  NOTE: 파일 전체 내용/구조 파악(함수 목록 등)은 large-file-analyst를 사용할 것.
priority: 90
activation:
  keywords: ["find usage", "trace signal", "어디에 있어", "코드 구조", "call hierarchy", "definition", "함수 찾아", "클래스 찾아"]
  auto_detect: true
requires_tools: [find_files, grep_file, read_file, read_lines]
related_skills: [verilog-expert]
---

# SKILL: Code Analysis Expert — MANDATORY PROTOCOL

## Step 1: 위치 파악

경로를 모르면 반드시 find_files부터.

```
Action: find_files(pattern="*.py", directory="src")
```

## Step 2: 심볼 검색

```
Action: grep_file(pattern="def target_function", path="src/", recursive=True)
```

- 추측하지 말 것. 결과 확인 후 진행.

## Step 3: 코드 확인

**1000줄 이상 파일**: `grep_file`로 줄 번호 파악 후 해당 범위만 `read_lines` 사용.
**절대 `read_file` 단독으로 대용량 파일 읽지 말 것.**

```
Action: read_lines(path="src/main.py", start_line=<N-20>, end_line=<N+50>)
```

## Step 4: 답변

항상 `파일경로:줄번호` 형식으로 인용.

## Gotchas

- `#include`/`import` 발견 시 해당 파일도 확인
- 파일 전체 구조/함수 목록이 필요하면 large-file-analyst skill을 사용할 것
- grep 결과가 너무 많으면 패턴을 좁힐 것
