#!/usr/bin/env bash
# 12-contract closure across 3 lanes: iverilog (compile) + verilator --assert (sim) + sby/z3 (formal)
set -u
export PATH="$HOME/.local/bin:$PATH"
cd "$(cd "$(dirname "$0")" && pwd)"
RTL=rtl/mctp_rx_assembler.sv
TB=tb/tb_random.sv
BUGS="GATE KEY START SINGLE SEQ PAYLOAD END DROP OUT RESET STATUS"
VFLAGS="-Wno-fatal --assert --timing --binary"

echo "### anti-vacuity guard: assert / cover cells in the model"
yosys -p "read_verilog -sv -formal -DFORMAL $RTL; prep -top mctp_rx_assembler; stat" 2>&1 | grep -E '\$(assert|cover)' | sed 's/^/   /'
echo

ivl() {  # $@ = defines ; returns exit code (0=compiles)
  iverilog -g2012 "$@" -o /tmp/ivl.out "$RTL" "$TB" >/tmp/ivl.err 2>&1; echo $?
}
vsim() {  # $1=tag $2=define ; PASS|ASSERT_FAIL|BUILDFAIL|RUNFAIL
  local d="vbuild_$1"; rm -rf "$d"
  if ! verilator $VFLAGS -DFORMAL $2 --top-module tb_random --Mdir "$d" "$RTL" "$TB" >"$d.blog" 2>&1; then echo BUILDFAIL; return; fi
  ./"$d"/Vtb_random >"$d.rlog" 2>&1; local rc=$?
  if grep -qiE "Assertion failed|%Error" "$d.rlog"; then echo ASSERT_FAIL
  elif [ $rc -eq 0 ] && grep -q RANDOM_SIM_DONE "$d.rlog"; then echo PASS
  else echo "RUNFAIL($rc)"; fi
}
fsby() {  # $1=tag $2=mode $3=define ; PASS|FAIL|ERROR
  cat > "f_$1.sby" <<EOF
[options]
mode $2
depth 22
[engines]
smtbmc z3
[script]
read_verilog -sv -formal -DFORMAL $3 mctp_rx_assembler.sv
prep -top mctp_rx_assembler
[files]
$RTL
EOF
  sby -f "f_$1.sby" >/dev/null 2>&1
  grep -oE "DONE \([A-Z]+" "f_$1/logfile.txt" 2>/dev/null | tail -1 | sed 's/DONE (//'
}

echo "### CORRECT design  (expect: iverilog=0  verilator=PASS  formal=PASS)"
echo "iverilog=$(ivl -DFORMAL_OFF)   verilator=$(vsim correct '')   formal=$(fsby correct prove '')"
echo

echo "### MUTANTS  (a contract is KILLED if verilator=ASSERT_FAIL or formal=FAIL)"
printf "%-9s | %-9s | %-12s | %-7s | %s\n" CONTRACT iverilog verilator formal KILLED
printf -- "----------+-----------+--------------+---------+--------\n"
for B in $BUGS; do
  D="-DINJECT_${B}_BUG"
  ic=$(ivl "$D")
  vs=$(vsim "$B" "$D")
  fs=$(fsby "$B" bmc "$D")
  if [ "$vs" = "ASSERT_FAIL" ] || [ "$fs" = "FAIL" ]; then k="YES"; else k="** NO **"; fi
  printf "%-9s | %-9s | %-12s | %-7s | %s\n" "$B" "$ic" "$vs" "$fs" "$k"
done
