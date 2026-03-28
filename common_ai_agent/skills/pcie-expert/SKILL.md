---
name: pcie-expert
description: >
  PCIe 7.0 스펙 관련 모든 질문 시 호출. TLP/DLLP 패킷 구조, LTSSM 상태머신, Flow Control,
  Lane Equalization, Power Management, AER, ACS, TDISP, IDE, ATS, IOV, Physical/Data Link/Transaction Layer,
  Flit Mode, Link Training, Virtual Channel, Root Complex, Endpoint 등.
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
requires_tools: [spec_navigate, grep_file, read_lines]
related_skills: [verilog-expert, protocol-spec-expert]
---

# ⚠️ MANDATORY: spec_navigate → grep 방식으로 탐색

**PCIe 스펙 질문은 반드시 아래 순서로 처리한다.**

## Step 1: TOC 확인
```
Action: spec_navigate(spec="pcie", node_id="root")
```

## Step 2: 키워드 검색
```
Action: grep_file(pattern="<핵심 키워드>", path="skills/pcie-expert/data/markdown")
```

## Step 3: 관련 파일 읽기
```
Action: read_lines(path="skills/pcie-expert/data/markdown/<파일명>", start_line=1, end_line=100)
```

## 규칙
- **acronym/용어를 임의로 추측하거나 해석하지 말 것** — 탐색 결과를 보기 전까지 어떤 가정도 하지 말 것
- `spec_search`는 사용하지 말 것
- 탐색 범위는 `skills/pcie-expert/data/markdown/` 내로 한정
- 필요하면 `spec_navigate(spec="pcie", node_id="<섹션ID>")` 로 특정 섹션 드릴다운
