---
name: testbench-expert
description: >
  Verilog 테스트벤치 작성, 시뮬레이션 실행, 디버깅 시 호출.
  Trigger on: 'testbench', 'tb', 'simulation', 'iverilog', 'vvp',
  'assert', 'stimulus', 'waveform', '시뮬레이션', '검증'.
priority: 80
activation:
  keywords: [testbench, tb, simulation, test, iverilog, vvp, assert, check, verify, stimulus, clock, reset, waveform, dump]
  file_patterns: ["*_tb.v", "*_test.v", "tb_*.v"]
  auto_detect: true
requires_tools: [generate_module_testbench, write_file, run_command, read_lines]
related_skills: [verilog-expert]
---

## Gotchas
- 모듈을 먼저 read_file/analyze 한 후 테스트벤치 작성 — 포트를 추측하지 말 것
- 모든 reg 초기화 필수 (clk=0, reset=1) — 미초기화 시 X 전파
- race condition 방지: stimulus는 `@(negedge clk)` 또는 `#1` 지연 후 변경
- 무한 대기 방지: fork/join_any + timeout 패턴 사용
- compile: VCS → `vcs -full64 -sverilog -o sim tb.sv dut.sv` then `./sim`; iverilog fallback → `iverilog -g2012 -Wall -o sim tb.v dut.v` then `vvp sim`
- self-checking testbench 권장: expected vs actual 비교

## Workflow
1. read_file(module) → 포트/신호 파악
2. generate_module_testbench(path, tb_type) 또는 직접 작성
3. 시뮬레이터 컴파일 → 실행 (VCS 기본, iverilog fallback — simulation.md 참조)
4. 에러 시 read_lines → replace_in_file → 재컴파일

## References (read when needed)
| Situation | File |
|-----------|------|
| TB patterns (basic, AXI, self-checking) | patterns.md |
| Compilation & simulation commands | simulation.md |
