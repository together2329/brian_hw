#!/usr/bin/env bash
# descriptor + header-snapshot deep-dive: §9.3/§9.5 across sim + formal
set -u
export PATH="$HOME/.local/bin:$PATH"
cd "$(cd "$(dirname "$0")" && pwd)"
RTL=rtl/mctp_rx_descriptor.sv
TB=tb/tb_desc.sv
BUGS="NOEARLY FIRST LAST CONTENT FULL"
VFLAGS="-Wno-fatal --assert --timing --binary"

echo "### anti-vacuity: assert / cover cells"
yosys -p "read_verilog -sv -formal -DFORMAL $RTL; prep -top mctp_rx_descriptor; select -count t:\$assert; select -count t:\$cover" 2>&1 | grep -iE "found and reported" | tail -1
echo

vsim() { local d="ds_$1"; rm -rf "$d"
  if ! verilator $VFLAGS $2 --top-module tb_desc --Mdir "$d" "$RTL" "$TB" >"$d.blog" 2>&1; then echo BUILDFAIL; return; fi
  ./"$d"/Vtb_desc >"$d.rlog" 2>&1; local rc=$?
  if grep -q DESC_SIM_DONE "$d.rlog" && [ $rc -eq 0 ]; then echo PASS; else echo FAIL; fi
}
fsby() { local t=$1 m=$2 d=$3
  cat > "fc_$t.sby" <<EOF
[options]
mode $m
depth 14
[engines]
smtbmc z3
[script]
read_verilog -sv -formal -DFORMAL $d mctp_rx_descriptor.sv
prep -top mctp_rx_descriptor
[files]
$RTL
EOF
  sby -f "fc_$t.sby" >/dev/null 2>&1
  grep -oE "DONE \([A-Z]+" "fc_$t/logfile.txt" 2>/dev/null | tail -1 | sed 's/DONE (//'
}

echo "### CORRECT  (expect verilator=PASS  formal=PASS)"
echo "verilator=$(vsim correct '')   formal=$(fsby correct prove '')"
echo
echo "### MUTANTS  (killed if verilator=FAIL or formal=FAIL)"
printf "%-9s | %-10s | %-7s | %s\n" CONTRACT verilator formal KILLED
printf -- "----------+------------+---------+--------\n"
for B in $BUGS; do
  D="-DINJECT_${B}_BUG"; vs=$(vsim "$B" "$D"); fs=$(fsby "$B" bmc "$D")
  if [ "$vs" = "FAIL" ] || [ "$fs" = "FAIL" ]; then k=YES; else k="** NO **"; fi
  printf "%-9s | %-10s | %-7s | %s\n" "$B" "$vs" "$fs" "$k"
done
find . -maxdepth 1 \( -name 'ds_*' -o -name 'fc_*' \) -exec rm -rf {} + 2>/dev/null
