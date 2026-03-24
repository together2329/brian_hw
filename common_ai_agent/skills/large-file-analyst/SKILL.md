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
    "함수 목록", "클래스 목록", "파일 구조", "모든 함수", "전체 내용"
  ]
  auto_detect: false
requires_tools: [run_command, read_lines, background_task]
---

## 핵심 원칙
- **전체 read_file 금지** — 대용량 파일을 한번에 읽지 말 것
- **병렬 분할 스캔** — explore 에이전트가 1000줄씩 동시 처리
- **BACKGROUND_MAX_WORKERS=3** — 한 번에 최대 3개 에이전트만 실행 가능

## Approach

### Step 1: 파일 크기 확인
```
run_command("wc -l <파일경로>")
```
→ 총 줄 수 파악 후 청크 수 계산 (chunk_size=1000)

### Step 2: 병렬 에이전트 spawn (3개씩 배치)
청크가 3개 이하면 한 번에, 4개 이상이면 3개씩 나눠서 실행.

각 에이전트 prompt 템플릿:
```
파일 <path>의 <start>~<end>줄을 read_lines로 읽고 다음을 추출하라:
<사용자 질문에 맞는 추출 목표>

출력 형식:
- 발견한 항목: [줄번호] 내용
- 없으면: "해당 없음"
```

### Step 3: 결과 취합
3개 배치가 끝날 때마다 결과를 수집하고, 다음 배치 실행.
모든 배치 완료 후 전체 결과를 종합하여 답변.

## 예시: 10000줄 파일, 함수 목록 추출

**배치 1** (동시 실행):
- `background_task(agent="explore", prompt="파일 foo.py 1~1000줄 읽고 함수/클래스 정의 줄번호와 이름 추출")`
- `background_task(agent="explore", prompt="파일 foo.py 1001~2000줄 읽고 함수/클래스 정의 줄번호와 이름 추출")`
- `background_task(agent="explore", prompt="파일 foo.py 2001~3000줄 읽고 함수/클래스 정의 줄번호와 이름 추출")`

→ 3개 완료 후 **배치 2** 실행...

## Chunk Size 가이드
| 파일 크기 | chunk_size | 이유 |
|-----------|-----------|------|
| 1K ~ 3K줄 | 1000 | 에이전트 3개로 커버 |
| 3K ~ 10K줄 | 1000 | 배치 3~4회 |
| 10K줄 이상 | 2000 | 배치 수 줄이기 |

## Gotchas
- explore 에이전트는 저비용 모델(SUBAGENT_LOW_MODEL) 사용 — 비용 효율적
- 각 에이전트 prompt에 반드시 **파일 경로 + 줄 범위** 명시
- 에이전트 결과가 "해당 없음"이면 그 청크는 관련 없음으로 처리
- 마지막 청크는 실제 줄 수까지만 (예: 9001~9843)
