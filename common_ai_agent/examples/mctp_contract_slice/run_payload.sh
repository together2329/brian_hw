#!/usr/bin/env bash
# payload byte-exact deep-dive: SRAM write contract across sim + symbolic-byte formal
set -u
export PATH="$HOME/.local/bin:$PATH"
cd "$(cd "$(dirname "$0")" && pwd)"
RTL=rtl/mctp_rx_payload.sv
TB=tb/tb_payload.sv
BUGS="OFFSET GAP OVERWRITE LOSS"
VFLAGS="-Wno-fatal --assert --timing --binary"

echo "### anti-vacuity: assert / cover cells"
yosys -p "read_verilog -sv -formal -DFORMAL $RTL; prep -top mctp_rx_payload; select -count t:\$assert; select -count t:\$cover" 2>&1 | grep -iE "found and reported" | tail -1
echo

vsim() { local d="pv_$1"; rm -rf "$d"
  if ! verilator $VFLAGS $2 --top-module tb_payload --Mdir "$d" "$RTL" "$TB" >"$d.blog" 2>&1; then echo BUILDFAIL; return; fi
  ./"$d"/Vtb_payload >"$d.rlog" 2>&1; local rc=$?
  if grep -q PAYLOAD_SIM_DONE "$d.rlog" && [ $rc -eq 0 ]; then echo PASS; else echo FAIL; fi
}
fsby() { local t=$1 m=$2 d=$3
  cat > "fp_$t.sby" <<EOF
[options]
mode $m
depth 16
[engines]
smtbmc z3
[script]
read_verilog -sv -formal -DFORMAL $d mctp_rx_payload.sv
prep -top mctp_rx_payload
[files]
$RTL
EOF
  sby -f "fp_$t.sby" >/dev/null 2>&1
  grep -oE "DONE \([A-Z]+" "fp_$t/logfile.txt" 2>/dev/null | tail -1 | sed 's/DONE (//'
}

echo "### CORRECT  (expect verilator=PASS  formal=PASS)"
echo "verilator=$(vsim correct '')   formal=$(fsby correct prove '')"
echo
echo "### MUTANTS  (killed if verilator=FAIL or formal=FAIL)"
printf "%-10s | %-10s | %-7s | %s\n" CONTRACT verilator formal KILLED
printf -- "-----------+------------+---------+--------\n"
for B in $BUGS; do
  D="-DINJECT_${B}_BUG"; vs=$(vsim "$B" "$D"); fs=$(fsby "$B" bmc "$D")
  if [ "$vs" = "FAIL" ] || [ "$fs" = "FAIL" ]; then k=YES; else k="** NO **"; fi
  printf "%-10s | %-10s | %-7s | %s\n" "$B" "$vs" "$fs" "$k"
done
