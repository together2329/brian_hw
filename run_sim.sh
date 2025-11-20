#!/bin/bash

# PCIe System Simulation Run Script
# 시뮬레이션을 컴파일하고 실행하는 스크립트

set -e  # 에러 발생 시 스크립트 중단

PROJECT_DIR="/Users/brian/Desktop/Project/brian_hw"
cd "$PROJECT_DIR"

echo "=========================================="
echo "[INFO] PCIe System Simulation"
echo "=========================================="
echo ""

# 기존 바이너리 제거
echo "[1/3] Cleaning old binaries..."
rm -f sim/pcie_system
mkdir -p sim

# Verilog 컴파일
echo "[2/3] Compiling Verilog files..."
if iverilog -g2009 -o sim/pcie_system *.v; then
    echo "✓ Compilation successful"
else
    echo "✗ Compilation failed"
    exit 1
fi

echo ""

# 시뮬레이션 실행
echo "[3/3] Running simulation..."
echo "=========================================="
echo ""

vvp sim/pcie_system 2>&1

echo ""
echo "=========================================="
echo "[INFO] Simulation completed"
echo "=========================================="
echo ""
echo "Output files:"
echo "  - sim/pcie_system (compiled binary)"
echo "  - pcie_system.vcd (waveform file for GTKWave)"
