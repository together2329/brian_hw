#!/usr/bin/env bash
# multi-context deep-dive: interleaving isolation across 3 lanes
set -u
export PATH="$HOME/.local/bin:$PATH"
cd "$(cd "$(dirname "$0")" && pwd)"
RTL=rtl/mctp_rx_mc.sv
TB=tb/tb_mc.sv
BUGS="ISO ALLOC DUP SEQ"
VFLAGS="-Wno-fatal --assert --timing --binary"

echo "### anti-vacuity: assert / cover cells"
yosys -p "read_verilog -sv -formal -DFORMAL $RTL; prep -top mctp_rx_mc; select -count t:\$assert; select -count t:\$cover" 2>&1 | grep -iE "found and reported|^[0-9]+\." | tail -3
echo

echo "### INTERLEAVING reachable?  (cover: two contexts live with different keys)"
cat > f_mccov.sby <<'EOF'
[options]
mode cover
depth 20
[engines]
smtbmc z3
[script]
read_verilog -sv -formal -DFORMAL mctp_rx_mc.sv
prep -top mctp_rx_mc
[files]
rtl/mctp_rx_mc.sv
EOF
sby -f f_mccov.sby 2>&1 | grep -iE "Reached cover.*c0_v|two contexts|c0_key != c1_key|Reached cover statement.*mctp_rx_mc.sv:1[0-9][0-9]" | head -3
sby -f f_mccov.sby >/dev/null 2>&1
echo "   cover summary: $(grep -c 'Reached cover' f_mccov/logfile.txt) cover statements reached"
echo

vsim() { local d="mc_$1"; rm -rf "$d"
  if ! verilator $VFLAGS -DFORMAL $2 --top-module tb_mc --Mdir "$d" "$RTL" "$TB" >"$d.blog" 2>&1; then echo BUILDFAIL; return; fi
  ./"$d"/Vtb_mc >"$d.rlog" 2>&1; local rc=$?
  if grep -qiE "Assertion failed|%Error" "$d.rlog"; then echo ASSERT_FAIL
  elif [ $rc -eq 0 ] && grep -q MC_SIM_DONE "$d.rlog"; then echo PASS; else echo "RUNFAIL($rc)"; fi
}
fsby() { local t=$1 m=$2 d=$3
  cat > "fm_$t.sby" <<EOF
[options]
mode $m
depth 22
[engines]
smtbmc z3
[script]
read_verilog -sv -formal -DFORMAL $d mctp_rx_mc.sv
prep -top mctp_rx_mc
[files]
$RTL
EOF
  sby -f "fm_$t.sby" >/dev/null 2>&1
  grep -oE "DONE \([A-Z]+" "fm_$t/logfile.txt" 2>/dev/null | tail -1 | sed 's/DONE (//'
}

echo "### CORRECT  (expect verilator=PASS  formal=PASS)"
echo "verilator=$(vsim correct '')   formal=$(fsby correct prove '')"
echo

echo "### MUTANTS  (killed if verilator=ASSERT_FAIL or formal=FAIL)"
printf "%-7s | %-12s | %-7s | %s\n" CONTRACT verilator formal KILLED
printf -- "--------+--------------+---------+--------\n"
for B in $BUGS; do
  D="-DINJECT_${B}_BUG"; vs=$(vsim "$B" "$D"); fs=$(fsby "$B" bmc "$D")
  if [ "$vs" = "ASSERT_FAIL" ] || [ "$fs" = "FAIL" ]; then k=YES; else k="** NO **"; fi
  printf "%-7s | %-12s | %-7s | %s\n" "$B" "$vs" "$fs" "$k"
done
