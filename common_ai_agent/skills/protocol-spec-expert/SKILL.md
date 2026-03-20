---
name: protocol-spec-expert
description: >
  PCIe, AMBA, TDISP 등 프로토콜 스펙 질문, 상태머신, 레지스터 정의 검색 시 호출.
  Trigger on: 'pcie', 'axi', 'tlp', 'protocol', 'spec', 'register',
  'state machine', 'tdisp', '프로토콜', '스펙', '상태머신'.
priority: 85
activation:
  keywords: [pcie, amba, axi, tlp, protocol, specification, spec, transaction, header, packet, "state machine", transition, config, register, dllp, tdisp, "상태머신", "프로토콜", "스펙"]
  file_patterns: ["*.md", "*.pdf", "*.txt", "*.rst"]
  auto_detect: true
requires_tools: [rag_search, rag_explore, read_lines]
related_skills: [verilog-expert]
---

## Gotchas
- 반드시 `categories="spec"` 사용 — "verilog" 카테고리는 코드가 섞임
- RAG 결과만으로 답하지 말 것 — read_lines로 실제 스펙 텍스트 확인
- acronym 질문: "X stands for" 패턴의 정의 chunk 우선 (사용 chunk 아님)
- 정의 못 찾으면 "indexed documents에서 정의를 찾지 못했습니다" 솔직히 답변
- cross-reference 있으면 rag_explore로 따라가기

## Tools
| Tool | When to use |
|------|-------------|
| rag_search(query, categories="spec") | 스펙 문서 검색 (최우선) |
| rag_explore(start_node, max_depth) | cross-reference 따라가기 |
| read_lines(path, start, end) | 실제 스펙 텍스트 확인 |

## References (read when needed)
| Situation | File |
|-----------|------|
| Protocol-specific search strategies | search-strategies.md |
