---
name: code-analysis-expert
description: >
  대규모 코드베이스 탐색, 정의 찾기, 신호/함수 추적, 코드 구조 분석 시 호출.
  Trigger on: 'analyze', '분석', 'find usage', 'trace', '어디에 있어',
  '코드 구조', 'call hierarchy', 'definition'.
priority: 90
activation:
  keywords: ["analyze", "분석해줘", "find usage", "trace signal", "어디에 있어", "코드 구조", "call hierarchy", "definition"]
  auto_detect: true
requires_tools: [find_files, grep_file, read_file, read_lines]
related_skills: [verilog-expert]
---

## Gotchas
- 경로를 모르면 find_files부터 — 추측하지 말 것
- 1000줄 이상 파일은 grep_file/read_lines로 범위 좁힌 후 읽기
- 결과 보고 시 항상 파일 경로 + 줄 번호 인용
- `#include` 발견 시 해당 파일도 확인

## Approach
1. **find_files(pattern)** — 위치 파악 (broad → narrow)
2. **grep_file(pattern, recursive=True)** — 사용처/정의 검색
3. **read_lines(path, start, end)** — 실제 코드 확인 (±20줄 컨텍스트)
4. 분석 후 파일 경로:줄번호와 함께 답변
