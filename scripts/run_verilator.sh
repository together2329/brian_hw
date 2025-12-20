#!/bin/bash
# Build and run the Caliptra SS top‑level simulation with Verilator

# 1. Run Verilator to generate C++ model
verilator --trace -Wall --top-module caliptra_ss_top -I src -I src/caliptra_ss_top \
    src/caliptra_ss_top.sv \
    src/caliptra_top/caliptra_top.sv \
    src/mcu_top/mcu_top.sv \
    src/lc_ctrl/lc_ctrl.sv \
    src/mci_top/mci_top.sv \
    src/i3c_wrapper/i3c_wrapper.sv \
    src/otp_ctrl/otp_ctrl.sv \
    src/axi_mem/axi_mem.sv \
    testbench/caliptra_ss_top_tb.sv

# 2. Build the C++ model
make -C obj_dir -j -f Vcaliptra_ss_top.mk Vcaliptra_ss_top

# 3. Run the simulation (produces VCD waveform)
./obj_dir/Vcaliptra_ss_top +trace
