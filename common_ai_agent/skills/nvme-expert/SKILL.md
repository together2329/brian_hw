---
name: nvme-expert
description: >
  NVMe (Non-Volatile Memory Express) Base Spec 2.3 관련 모든 질문 시 호출.
  Command Set, Admin Commands, I/O Commands, Queue Model, Submission/Completion Queue,
  Namespace, Controller, PCIe Transport, Fabrics, NVM Command Set, Zoned Namespace,
  Key Value, Power Management, Error Handling, Sanitize, Security (TCG), Telemetry 등.
priority: 85
activation:
  keywords: [nvme, "nvm express", "non-volatile memory", "submission queue", "completion queue",
             "admin command", "i/o command", namespace, controller, "queue model",
             "nvme over fabrics", "zoned namespace", "key value", sanitize, telemetry,
             "nvm command set", "identify command", doorbell, "prp", "sgl",
             "스토리지", "큐", "컨트롤러", "네임스페이스"]
  file_patterns: ["*.md", "*.pdf", "*.txt"]
  auto_detect: true
requires_tools: [spec_navigate, grep_file, read_lines]
related_skills: [pcie-expert, protocol-spec-expert]
---

# ⚠️ MANDATORY: spec_navigate로 탐색

**NVMe 스펙 질문은 반드시 `spec_navigate`로 처리한다.**

## 탐색 방법

```
# 1. TOC 확인
Action: spec_navigate(spec="nvme", node_id="root")

# 2. 관련 챕터 드릴다운 → leaf의 content에 내용 포함
Action: spec_navigate(spec="nvme", node_id="<섹션ID>")

# 3. 더 깊이 탐색 필요 시 — navigate path로 grep → 라인 번호 확인 → read_lines
Action: grep_file(pattern="<키워드>", path="<navigate path의 상위 디렉토리>")
Action: read_lines(path="<파일경로>", start_line=<N>, end_line=<N+80>)
```

## 규칙
- **acronym/용어를 임의로 추측하지 말 것** — navigate 결과를 보기 전까지 어떤 가정도 하지 말 것
- leaf `content`로 충분하면 추가 read 불필요
- grep 경로는 반드시 `spec_navigate`의 `path`에서 유도할 것 — 임의 경로 금지
- `spec_search`는 사용하지 말 것
