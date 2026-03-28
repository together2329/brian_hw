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

# ⚠️ MANDATORY: spec_navigate → grep 방식으로 탐색

**NVMe 스펙 질문은 반드시 아래 순서로 처리한다.**

## Step 1: TOC 확인
```
Action: spec_navigate(spec="nvme", node_id="root")
```

## Step 2: 키워드 검색
```
Action: grep_file(pattern="<핵심 키워드>", path="skills/nvme-expert/data/markdown")
```

## Step 3: 관련 파일 읽기
```
Action: read_lines(path="skills/nvme-expert/data/markdown/<파일명>", start_line=1, end_line=100)
```

## 규칙
- **acronym/용어를 임의로 추측하거나 해석하지 말 것** — 탐색 결과를 보기 전까지 어떤 가정도 하지 말 것
- `spec_search`는 사용하지 말 것
- 탐색 범위는 `skills/nvme-expert/data/markdown/` 내로 한정
- 필요하면 `spec_navigate(spec="nvme", node_id="<섹션ID>")` 로 특정 섹션 드릴다운
