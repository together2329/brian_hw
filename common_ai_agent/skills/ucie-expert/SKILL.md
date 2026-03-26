---
name: ucie-expert
description: >
  UCIe (Universal Chiplet Interconnect Express) 스펙 관련 모든 질문 시 호출.
  Die-to-Die interface, Physical Layer, Die Adapter, Protocol Layer, FDI/RDI interface,
  Streaming Protocol, CXL over UCIe, PCIe over UCIe, Link Training, Parameter Exchange,
  Advanced/Standard Package 등.
  spec_navigate 도구로 TOC를 계층적으로 탐색하여 정확한 스펙 섹션을 찾는다.
priority: 85
activation:
  keywords: [ucie, "universal chiplet", "die-to-die", "d2d", chiplet, "die adapter",
             fdi, rdi, "protocol layer", "die interface", "link training",
             "parameter exchange", "streaming protocol", "advanced package",
             "standard package", "chiplet interconnect"]
  file_patterns: ["*.md", "*.pdf", "*.txt"]
  auto_detect: true
requires_tools: [spec_search, spec_navigate, read_lines]
related_skills: [pcie-expert]
---

# ⚠️ MANDATORY: spec-navigator agent에 위임할 것

**UCIe 스펙 질문은 반드시 spec-navigator agent에 위임한다.**

```
Action: background_task(agent="spec-navigator", prompt="spec=ucie query=<질문>")
```

- `spec_search` / `spec_navigate`를 직접 호출하지 말 것
- spec-navigator가 검색, 탐색, 답변 생성을 모두 처리한다
- 결과가 반환되면 그 내용을 바탕으로 사용자에게 답변한다
