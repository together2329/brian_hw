---
name: verilog-expert
description: >
  .v/.sv 파일 수정, RTL 신호 추적, FSM 분석, 합성 에러 수정 시 호출.
  Trigger on: 'verilog', 'module', 'signal', 'fsm', 'synthesis', 'rtl',
  'always', 'wire', 'reg', 'posedge', '합성', '신호', '상태머신'.
priority: 90
activation:
  keywords: [
    verilog, systemverilog, rtl, hdl, synthesize, synthesis, timing, signal,
    module, always, reg, wire, posedge, negedge, fsm, state, clocking,
    iverilog, verilator, yosys, quartus, vivado, modelsim,
    axi, ahb, apb, pcie, wishbone, avalon, amba,
    fifo, counter, uart, spi, i2c, timer, pwm,
    clock, reset, async, synchronous, asynchronous, combinational, sequential,
    blocking, nonblocking, "state machine", pipeline, handshake,
    "신호", "모듈", "설계", "검증", "상태머신", "클럭", "리셋",
    "동기", "비동기", "조합", "순차", "블로킹", "넌블로킹"
  ]
  file_patterns: ["*.v", "*.sv"]
  auto_detect: true
requires_tools: [analyze_verilog_module, find_signal_usage, rag_search, read_lines]
related_skills: [testbench-expert]
---

## Gotchas
- rag_search 결과만으로 답하지 말 것 — 반드시 read_lines로 실제 코드 확인 후 답변
- replace_in_file로 수정. write_file은 기존 모듈을 통째로 덮어씀
- always @(posedge) 안에서 blocking(=) 쓰면 합성 결과가 시뮬레이션과 달라짐
- grep보다 rag_search(categories="verilog") 우선 — 10-100x 빠르고 semantic
- analyze_verilog_module(deep=true)은 느림. 간단한 질문엔 rag_search + read_lines
- 에러 수정 시 최대 3회 시도 후 유저에게 물어볼 것

## Tools
| Tool | When to use |
|------|-------------|
| rag_search(query, categories="verilog") | 신호/모듈 위치 찾기 (최우선) |
| read_lines(path, start, end) | RAG 결과 확인 — 반드시 실제 코드 읽기 |
| analyze_verilog_module(path, deep) | 모듈 전체 구조 분석 |
| find_signal_usage(signal, dir) | 신호 할당/사용처 추적 |
| grep_file(pattern, path) | 정확한 패턴 매칭 (fallback) |
| replace_in_file(path, old, new) | 코드 수정 (write_file 금지) |

## References (read when needed)
| Situation | File |
|-----------|------|
| Signal tracing workflow | signal-tracing.md |
| Compilation error patterns | error-recovery.md |
| Detailed tool selection guide | tool-selection.md |
