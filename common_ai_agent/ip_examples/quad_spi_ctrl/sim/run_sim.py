#!/usr/bin/env python3
"""Standalone simulation runner for quad_spi_ctrl using iverilog + cocotb VPI.

Bypasses cocotb's Makefile system which has environment issues
on this machine. Compiles and runs directly."""

import os, sys, subprocess, shutil, json, glob

SIM_DIR = os.path.dirname(__file__)
PROJ_DIR = os.path.dirname(SIM_DIR)
RTL_DIR = os.path.join(PROJ_DIR, 'rtl')
TB_DIR = os.path.join(PROJ_DIR, 'tb')
SIM_BUILD = os.path.join(PROJ_DIR, 'sim_build')

COCOTB_LIBS = '/Users/brian/Library/Python/3.9/lib/python/site-packages/cocotb/libs'
COCOTB_SHARE = '/Users/brian/Library/Python/3.9/lib/python/site-packages/cocotb/share'

# Clean build
if os.path.exists(SIM_BUILD):
    shutil.rmtree(SIM_BUILD)
os.makedirs(SIM_BUILD, exist_ok=True)

# RTL files
rtl_files = sorted(glob.glob(os.path.join(RTL_DIR, '*.sv')))
print(f"RTL files: {len(rtl_files)}")

# Compile with iverilog
ivl_cmd = [
    '/opt/homebrew/bin/iverilog',
    '-g2012',
    '-o', os.path.join(SIM_BUILD, 'sim.vvp'),
    '-D', 'COCOTB_SIM=1',
    '-s', 'quad_spi_ctrl_top',
] + rtl_files

print(f"Compiling: {' '.join(ivl_cmd)}")
result = subprocess.run(ivl_cmd, capture_output=True, text=True)
if result.returncode != 0:
    print(f"COMPILE ERROR:\n{result.stderr}")
    summary = {"rc": 1, "errors": 1, "compile_output": result.stderr}
    with open(os.path.join(SIM_DIR, 'sim_report.json'), 'w') as f:
        json.dump(summary, f, indent=2)
    sys.exit(1)

print("Compile OK")

# Run tests
tests = [
    'test_reset',
    'test_sc_apb_config',
    'test_sc_basic_transfer',
    'test_sc_lane_mode_sweep',
    'test_sc_cpol_cpha_sweep',
    'test_sc_fifo_limits',
]

all_passed = True
results_xml_path = os.path.join(SIM_BUILD, 'results.xml')
# Accumulate results
results_blocks = []

for test in tests:
    vvp_cmd = [
        '/opt/homebrew/bin/vvp',
        '-M', COCOTB_LIBS,
        '-m', 'libcocotbvpi_icarus',
        os.path.join(SIM_BUILD, 'sim.vvp'),
    ]
    env = os.environ.copy()
    env['COCOTB_TESTCASE'] = test
    env['MODULE'] = 'cocotb.test_quad_spi_ctrl'
    env['TOPLEVEL'] = 'quad_spi_ctrl_top'
    env['COCOTB_RESULTS_FILE'] = results_xml_path
    env['PYTHONPATH'] = f"{TB_DIR}:{PROJ_DIR}:{os.path.join(PROJ_DIR, 'model')}:" + env.get('PYTHONPATH', '')
    env['PYTHONHOME'] = env.get('PYTHONHOME', '')
    
    print(f"\nRunning {test}...")
    result = subprocess.run(vvp_cmd, capture_output=True, text=True, env=env, timeout=120)
    
    # Parse results.xml if it was written
    if os.path.exists(results_xml_path):
        with open(results_xml_path) as f:
            xml = f.read()
        if '<failure' in xml or '<error' in xml:
            print(f"  FAILED: {test}")
            all_passed = False
        else:
            print(f"  PASSED: {test}")
        results_blocks.append(xml)
        os.remove(results_xml_path)
    else:
        print(f"  NO RESULT: {test}")
        print(result.stdout[-500:])
        all_passed = False

# Write combined results
combined_xml = '<?xml version="1.0"?>\n<testsuite name="quad_spi_ctrl">\n'
for block in results_blocks:
    # Extract testcase elements
    for line in block.split('\n'):
        if 'testcase' in line or 'failure' in line or 'error' in line or '</testsuite' in line or '<?xml' in line:
            if '<?xml' not in line and '</testsuite' not in line:
                combined_xml += line + '\n'
combined_xml += '</testsuite>\n'

with open(os.path.join(SIM_BUILD, 'results.xml'), 'w') as f:
    f.write(combined_xml)

failures = combined_xml.count('<failure')
errors = combined_xml.count('<error')
test_count = combined_xml.count('testcase ')

summary = {
    "rc": 0 if all_passed else 1,
    "testsuite": "quad_spi_ctrl",
    "tests": test_count,
    "failures": failures,
    "errors": errors,
    "tool": "iverilog + cocotb VPI",
    "all_passed": all_passed,
}

with open(os.path.join(SIM_DIR, 'sim_report.json'), 'w') as f:
    json.dump(summary, f, indent=2)

print(f"\nTests: {test_count}, Failures: {failures}, Errors: {errors}")
print("All passed!" if all_passed else "SOME FAILED!")
