---
name: nvme-expert
description: >
  NVMe (Non-Volatile Memory Express) Base Spec 2.3 관련 모든 질문 시 호출.
  Command Set, Admin Commands, I/O Commands, Queue Model, Submission/Completion Queue,
  Namespace, Controller, PCIe Transport, Fabrics, NVM Command Set, Zoned Namespace,
  Key Value, Power Management, Error Handling, Sanitize, Security (TCG), Telemetry 등.
  spec_navigate 도구로 TOC를 계층적으로 탐색하여 정확한 스펙 섹션을 찾는다.
priority: 85
activation:
  keywords: [nvme, "nvm express", "non-volatile memory", "submission queue", "completion queue",
             "admin command", "i/o command", namespace, controller, "queue model",
             "nvme over fabrics", "zoned namespace", "key value", sanitize, telemetry,
             "nvm command set", "identify command", doorbell, "prp", "sgl",
             "스토리지", "큐", "컨트롤러", "네임스페이스"]
  file_patterns: ["*.md", "*.pdf", "*.txt"]
  auto_detect: true
requires_tools: [spec_search, spec_navigate, read_lines]
related_skills: [pcie-expert, protocol-spec-expert]
---

# ⚠️ MANDATORY: spec-navigator agent에 위임할 것

**NVMe 스펙 질문은 반드시 spec-navigator agent에 위임한다.**

```
Action: background_task(agent="spec-navigator", prompt="spec=nvme query=<질문>")
```

- `spec_search` / `spec_navigate`를 직접 호출하지 말 것
- spec-navigator가 검색, 탐색, 답변 생성을 모두 처리한다
- 결과가 반환되면 그 내용을 바탕으로 사용자에게 답변한다
