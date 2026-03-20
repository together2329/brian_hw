# Signal Tracing

신호 위치를 찾고, 실제 코드를 확인하고, 필요하면 주변 컨텍스트를 확장하는 워크플로우.

## Approach
1. `rag_search(query="signal_name", categories="verilog")` — 위치 파악
2. `read_lines(path, start-10, end+10)` — 실제 코드 확인 (±10줄)
3. 로직 이해에 컨텍스트 부족하면 범위 확장 (±30줄)
4. RAG에서 못 찾으면 `find_signal_usage(signal, dir)` 사용

## RAG Categories
- `categories="verilog"` — RTL 소스 (.v, .sv)
- `categories="testbench"` — 테스트벤치 (*_tb.v)
- `categories="spec"` — 프로토콜 문서 (.md, .pdf)
- `categories="all"` — 카테고리 불확실할 때
