---
name: pcie-expert
description: >
  PCIe 7.0 스펙 관련 모든 질문 시 호출. TLP/DLLP 패킷 구조, LTSSM 상태머신, Flow Control,
  Lane Equalization, Power Management, AER, ACS, TDISP, IDE, ATS, IOV, Physical/Data Link/Transaction Layer,
  Flit Mode, Link Training, Virtual Channel, Root Complex, Endpoint 등.
  spec_navigate 도구로 TOC를 계층적으로 탐색하여 정확한 스펙 섹션을 찾는다.
  Trigger on: pcie, pci express, tlp, dllp, ltssm, tdisp, ide, ats, aer, acs, flit, equalization,
  power management, link training, physical layer, data link, transaction layer.
priority: 85
activation:
  keywords: [pcie, "pci express", tlp, dllp, ltssm, "state machine", "flow control",
             equalization, aer, acs, ide, tdisp, "root complex", endpoint, completion,
             "power management", "physical layer", "data link layer", "transaction layer",
             "address translation", ats, iov, "virtual channel", flit, "lane equalization",
             "link training", register, config, specification, spec,
             "상태머신", "프로토콜", "스펙", "레인", "링크"]
  file_patterns: ["*.md", "*.pdf", "*.txt", "*.rst"]
  auto_detect: true
requires_tools: [spec_search, spec_navigate, read_lines]
related_skills: [verilog-expert, protocol-spec-expert]
---

# ⚠️ MANDATORY: spec_ask 도구를 사용할 것

**PCIe 스펙 질문은 반드시 `spec_ask` 도구를 사용한다.**

```
Action: spec_ask(spec="pcie", query="<사용자 질문 그대로>")
```

- **`spec_ask`는 질문당 단 한 번만 호출한다** — 여러 번 또는 병렬로 호출하지 말 것
- query는 사용자 질문을 그대로 전달 — 여러 sub-query로 나누지 말 것
- **acronym/용어를 임의로 추측하거나 해석하지 말 것** — spec_ask 결과를 보기 전까지 어떤 가정도 하지 말 것
- `find_files`, `grep_file`, `read_file` 등으로 직접 탐색하지 말 것
- `spec_ask` 하나로 검색, 탐색, 답변 생성이 모두 처리된다
- 결과가 반환되면 그 내용을 바탕으로 사용자에게 답변한다
