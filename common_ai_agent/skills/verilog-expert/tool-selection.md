# Verilog Tool Selection Guide

## Priority Order
1. **rag_search()** — Semantic, fast, ranked. 신호/모듈 찾기의 첫 선택
2. **analyze_verilog_module(deep=true)** — 모듈 구조 완전 분석 (ports, FSM, clocks)
3. **find_signal_usage()** — 특정 신호의 모든 할당/사용처
4. **grep_file()** — 정확한 regex 패턴 (e.g., `always @(posedge`)

## When to Use What

| Task | Tool |
|------|------|
| "Where is signal X?" | rag_search → read_lines |
| "Analyze this module" | analyze_verilog_module(deep=true) |
| "Find all uses of Y" | find_signal_usage |
| "Find all always blocks" | grep_file(pattern="always @") |
| "Explain protocol spec" | rag_search(categories="spec") |

## Combination Patterns

**Signal Investigation**: rag_search → read_lines → find_signal_usage
**Module Deep-Dive**: analyze_verilog_module → find_potential_issues → analyze_timing_paths
**Design Pattern Search**: rag_search → read_file → extract_module_hierarchy
