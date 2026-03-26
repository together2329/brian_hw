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

# ⚠️ MANDATORY: spec_ask 도구를 사용할 것

**UCIe 스펙 질문은 반드시 `spec_ask` 도구를 사용한다.**

```
Action: spec_ask(spec="ucie", query="<사용자 질문 그대로>")
```

- query는 **사용자 질문을 그대로** 전달 — 확장하거나 수정하지 말 것
- `find_files`, `grep_file`, `read_file` 등으로 직접 탐색하지 말 것
- `spec_ask` 하나로 검색, 탐색, 답변 생성이 모두 처리된다
- 결과가 반환되면 그 내용을 바탕으로 사용자에게 답변한다
