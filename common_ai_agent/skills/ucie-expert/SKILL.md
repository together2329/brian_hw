---
name: ucie-expert
description: >
  UCIe (Universal Chiplet Interconnect Express) 스펙 관련 모든 질문 시 호출.
  Die-to-Die interface, Physical Layer, Die Adapter, Protocol Layer, FDI/RDI interface,
  Streaming Protocol, CXL over UCIe, PCIe over UCIe, Link Training, Parameter Exchange,
  Advanced/Standard Package 등.
priority: 85
activation:
  keywords: [ucie, "universal chiplet", "die-to-die", "d2d", chiplet, "die adapter",
             fdi, rdi, "protocol layer", "die interface", "link training",
             "parameter exchange", "streaming protocol", "advanced package",
             "standard package", "chiplet interconnect"]
  file_patterns: ["*.md", "*.pdf", "*.txt"]
  auto_detect: true
requires_tools: [spec_navigate, grep_file, read_lines]
related_skills: [pcie-expert]
---

# ⚠️ MANDATORY: spec_navigate → grep 방식으로 탐색

**UCIe 스펙 질문은 반드시 아래 순서로 처리한다.**

## Step 1: TOC 확인
```
Action: spec_navigate(spec="ucie", node_id="root")
```

## Step 2: 키워드 검색
```
Action: grep_file(pattern="<핵심 키워드>", path="skills/ucie-expert/data/markdown")
```

## Step 3: 관련 파일 읽기
```
Action: read_lines(path="skills/ucie-expert/data/markdown/<파일명>", start_line=1, end_line=100)
```

## 규칙
- **acronym/용어를 임의로 추측하거나 해석하지 말 것** — 탐색 결과를 보기 전까지 어떤 가정도 하지 말 것
- `spec_search`는 사용하지 말 것
- 탐색 범위는 `skills/ucie-expert/data/markdown/` 내로 한정
- 필요하면 `spec_navigate(spec="ucie", node_id="<섹션ID>")` 로 특정 섹션 드릴다운
