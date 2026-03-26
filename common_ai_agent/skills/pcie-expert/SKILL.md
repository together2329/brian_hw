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

# ⚠️ MANDATORY: spec-navigator agent에 위임할 것

**PCIe 스펙 질문은 반드시 spec-navigator agent에 위임한다.**

```
Action: background_task(agent="spec-navigator", prompt="spec=pcie query=<질문>")
```

- `spec_search` / `spec_navigate`를 직접 호출하지 말 것
- spec-navigator가 검색, 탐색, 답변 생성을 모두 처리한다
- 결과가 반환되면 그 내용을 바탕으로 사용자에게 답변한다
