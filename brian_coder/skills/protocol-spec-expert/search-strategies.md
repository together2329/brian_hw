# Protocol Search Strategies

## Shallow → Deep Pattern
1. `rag_search(query, categories="spec", depth=2)` — 빠른 개요
2. 결과에서 관련 섹션 식별
3. `rag_search(query, categories="spec", depth=4, follow_references=true)` — 심층

## Exploration
관련 섹션 발견 시: `rag_explore(start_node, max_depth=3, explore_type="related")`

explore_type: "related" (전체), "hierarchy" (부모/자식), "references" (cross-ref)

## Protocol Quick Reference

### PCIe
- TLP header format, DLLP, link training, config space, AER
- Keywords: "PCIe TLP header", "PCIe link training"

### AXI (AMBA)
- 5 channels (AW, W, B, AR, R), handshake (VALID/READY), burst types
- Keywords: "AXI handshake", "AXI burst"

### TDISP
- State machine (CONFIG_LOCKED, RUN), lock/unlock, reports
- Keywords: "TDISP state", "TDISP transition"
