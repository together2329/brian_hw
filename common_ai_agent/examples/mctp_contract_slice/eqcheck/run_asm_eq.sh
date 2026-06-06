#!/usr/bin/env bash
# SpecLoop EQ-check on the REAL mctp_rx_assembler (open-source sequential equivalence).
# Regenerates two variants from the reference RTL, then SEC-checks each:
#   asm_rf  = refactored-but-EQUIVALENT  ( == rewritten as xor-reduce )   -> expect EQUIVALENT
#   asm_bug = spec-MISSING regeneration  ( OOS-drop forgotten )           -> expect NOT EQUIVALENT
# Note: the assembler uses async reset ($adff) -> 'async2sync' is required before SEC.
set -u
export PATH="$HOME/.local/bin:$PATH"
cd "$(cd "$(dirname "$0")" && pwd)"
SRC=../rtl/mctp_rx_assembler.sv

python3 - "$SRC" <<'PY'
import re, sys
src = open(sys.argv[1]).read()
src = re.sub(r"`ifdef INJECT_STATUS_BUG.*?`endif\n", "", src, flags=re.S, count=1)  # drop macro def
src = src.replace("`DROP_INC", "drop_count <= drop_count + 8'd1")                     # inline it
v = lambda n, x=(lambda s: s): x(src.replace("module mctp_rx_assembler ", "module %s " % n))
open("asm_gold.sv","w").write(v("mctp_rx_assembler_gold"))
open("asm_rf.sv","w").write(v("mctp_rx_assembler_rf", lambda s: s
  .replace("wire seq_ok_eff = (pkt_seq == expected_seq);", "wire seq_ok_eff = ~(|(pkt_seq ^ expected_seq));")
  .replace("wire key_ok_eff = (pkt_tag == ctx_tag);",     "wire key_ok_eff = ~(|(pkt_tag ^ ctx_tag));")))
open("asm_bug.sv","w").write(v("mctp_rx_assembler_bug", lambda s: s
  .replace("wire seq_ok_eff = (pkt_seq == expected_seq);", "wire seq_ok_eff = 1'b1;  // SPEC MISS: OOS drop forgotten")))
PY

chk() { # $1 gate file  $2 gate module
  yosys -q -p "read_verilog -sv asm_gold.sv $1; proc; async2sync; equiv_make mctp_rx_assembler_gold $2 m; hierarchy -top m; equiv_simple; equiv_induct; equiv_status -assert" >/dev/null 2>&1
}
echo "SpecLoop EQ-check (yosys equiv_make+equiv_induct) on mctp_rx_assembler:"
chk asm_rf.sv  mctp_rx_assembler_rf  && echo "  gold vs refactored   => EQUIVALENT (proven)"        || echo "  gold vs refactored   => NOT EQUIVALENT"
chk asm_bug.sv mctp_rx_assembler_bug && echo "  gold vs spec-missing => EQUIVALENT"                  || echo "  gold vs spec-missing => NOT EQUIVALENT (counterexample)"
