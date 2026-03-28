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

# ⚠️ MANDATORY: spec_navigate로 탐색

**PCIe 스펙 질문은 반드시 `spec_navigate`로 처리한다.**

## 탐색 방법

```
# 1. TOC 확인
Action: spec_navigate(spec="pcie", node_id="root")

# 2. 관련 챕터 드릴다운 → leaf의 content에 내용 포함
Action: spec_navigate(spec="pcie", node_id="<섹션ID>")

# 3. 더 깊이 탐색 필요 시 — navigate path로 grep → 라인 번호 확인 → read_lines
Action: grep_file(pattern="<키워드>", path="<navigate path의 상위 디렉토리>")
Action: read_lines(path="<파일경로>", start_line=<N>, end_line=<N+80>)
```

## 규칙
- **acronym/용어를 임의로 추측하지 말 것** — navigate 결과를 보기 전까지 어떤 가정도 하지 말 것
- leaf `content`로 충분하면 추가 read 불필요
- grep 경로는 반드시 `spec_navigate`의 `path`에서 유도할 것 — 임의 경로 금지
- `spec_search`는 사용하지 말 것
