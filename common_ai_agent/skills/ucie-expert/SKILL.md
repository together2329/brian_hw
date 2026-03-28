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

# ⚠️ MANDATORY: spec_search 도구를 사용할 것

**UCIe 스펙 질문은 반드시 `spec_search` 도구를 사용한다.**

```
Action: spec_search(spec="ucie", query="<사용자 질문 그대로>")
```

- **`spec_search`는 질문당 단 한 번만 호출한다** — 여러 번 또는 병렬로 호출하지 말 것
- query는 **사용자 질문을 그대로** 전달 — 여러 sub-query로 나누거나 확장하지 말 것
- **acronym/용어를 임의로 추측하거나 해석하지 말 것** — spec_search 결과를 보기 전까지 어떤 가정도 하지 말 것
- `find_files`, `grep_file`, `read_file` 등으로 직접 탐색하지 말 것
- 결과가 반환되면 그 내용을 바탕으로 사용자에게 답변한다

## Fallback: spec_search 결과가 부족할 때
```
Action: spec_navigate(spec="ucie", node_id="<섹션 ID>")
```
→ spec_search가 관련 내용을 못 찾은 경우에만 사용. node_id="root"로 시작해 드릴다운.
