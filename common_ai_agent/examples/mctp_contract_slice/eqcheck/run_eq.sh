#!/usr/bin/env bash
# SpecLoop EQ-check demo: open-source sequential equivalence checking with yosys.
# gold = reference RTL; eq = a differently-written but EQUIVALENT regeneration;
# ne  = a regeneration that missed the spec (NOT equivalent).
set -u
export PATH="$HOME/.local/bin:$PATH"
cd "$(cd "$(dirname "$0")" && pwd)"
chk() { # $1 label  $2 gateFile  $3 gateModule
  yosys -q -p "read_verilog gold.sv $2; proc; equiv_make dut_gold $3 m; hierarchy -top m; equiv_simple; equiv_induct; equiv_status -assert" >/dev/null 2>&1
  if [ $? -eq 0 ]; then echo "  $1 => EQUIVALENT (proven)"; else echo "  $1 => NOT EQUIVALENT (unproven equiv cells / counterexample)"; fi
}
echo "open-source sequential equivalence check (yosys equiv_make + equiv_induct):"
chk "gold vs eq (refactored)        " eq.sv dut_eq
chk "gold vs ne (spec missed)       " ne.sv dut_ne
