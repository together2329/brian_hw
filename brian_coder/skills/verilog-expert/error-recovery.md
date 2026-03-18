# Verilog Compilation Error Recovery

컴파일 에러 발생 시: 에러 위치 읽기 → 수정 → 재컴파일. 최대 3회.

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| syntax error at line N | Missing semicolon, bracket, keyword | read_lines ±2줄 → replace_in_file |
| signal_x is not declared | Typo or missing declaration | Check spelling, add declaration |
| port count mismatch | Wrong instantiation | Compare module def vs instance |
| always requires sensitivity list | Missing @(...) | Add `@(posedge clk)` or `@*` |

## Rules
- read_lines BEFORE fixing — 절대 추측으로 수정하지 말 것
- replace_in_file 사용 (write_file 금지)
- 3회 실패 → 유저에게 물어보기
