#!/usr/bin/env bash
# gen_tc.sh — Generate tc_*.sv skeleton from DUT source
MODULE="${HOOK_CMD_ARGS:-$1}"
[ -z "${MODULE}" ] && MODULE=$(find . -maxdepth 1 -name "*.sv" | grep -v "tb_\|tc_" | head -1 | sed 's|./||;s|\.sv||')
SRC="${MODULE}.sv"
OUT="tc_${MODULE}.sv"

[ ! -f "${SRC}" ] && { echo "DUT not found: ${SRC}"; exit 1; }
[ -f "${OUT}" ] && { echo "${OUT} already exists — edit it directly."; exit 0; }

# Extract ports
INPUTS=$(grep -oP 'input\s+logic\s+(\[\d+:\d+\]\s+)?\K\w+' "${SRC}")
OUTPUTS=$(grep -oP 'output\s+logic\s+(\[\d+:\d+\]\s+)?\K\w+' "${SRC}")

cat > "${OUT}" << EOF
// tc_${MODULE}.sv — Test cases for ${MODULE}
// Generated skeleton — fill in stimulus and assertions

task automatic tc_reset(
    ref logic clk, rst_n,
    ref integer pass_cnt, fail_cnt
);
    // Reset assertion
    rst_n = 0;
    repeat(3) @(posedge clk);
    rst_n = 1;
    @(posedge clk);
    // TODO: assert reset values
    \$display("[PASS] tc_reset"); pass_cnt++;
endtask

task automatic tc_normal_op(
    ref logic clk, rst_n,
    // TODO: add port refs
    ref integer pass_cnt, fail_cnt
);
    // TODO: apply normal stimulus
    // TODO: check expected output
    \$display("[PASS] tc_normal_op"); pass_cnt++;
endtask

task automatic tc_boundary(
    ref logic clk, rst_n,
    // TODO: add port refs
    ref integer pass_cnt, fail_cnt
);
    // TODO: min/max parameter values
    \$display("[PASS] tc_boundary"); pass_cnt++;
endtask

task automatic tc_edge_case(
    ref logic clk, rst_n,
    // TODO: add port refs
    ref integer pass_cnt, fail_cnt
);
    // TODO: edge case from spec
    \$display("[PASS] tc_edge_case"); pass_cnt++;
endtask
EOF

echo "Generated: ${OUT}"
echo "Ports found in DUT:"
echo "  Inputs : ${INPUTS}"
echo "  Outputs: ${OUTPUTS}"
echo ""
echo "Fill in stimulus and assertions in each task."
