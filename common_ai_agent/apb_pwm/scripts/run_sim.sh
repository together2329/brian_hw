#!/bin/sh
set -eu
cd "$(dirname "$0")/../tb/cocotb"
make SIM=${SIM:-icarus}
