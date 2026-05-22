#!/usr/bin/env python3
"""Test runner for quad_spi_ctrl cocotb suite."""
import os, sys, subprocess, json

tb_dir = os.path.join(os.path.dirname(__file__), 'tb')
sim_build = os.path.join(os.path.dirname(__file__), 'sim_build')
results_xml = os.path.join(sim_build, 'results.xml')

# Clean build
if os.path.exists(sim_build):
    import shutil
    shutil.rmtree(sim_build)

print("Running cocotb simulation...")
result = subprocess.run(
    ['make', '-C', tb_dir, 'SIM=icarus'],
    capture_output=True, text=True, timeout=300
)

print(result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout)
if result.stderr:
    print("STDERR:", result.stderr[-1000:])

# Check results
if os.path.exists(results_xml):
    with open(results_xml) as f:
        xml_content = f.read()
    failures = xml_content.count('<failure')
    errors = xml_content.count('<error')
    tests = xml_content.count('testcase ')
    summary = {
        "rc": result.returncode,
        "testsuite": "quad_spi_ctrl",
        "tests": tests,
        "failures": failures,
        "errors": errors,
        "tool": "cocotb + iverilog",
        "results_xml": results_xml
    }
else:
    summary = {
        "rc": result.returncode,
        "testsuite": "quad_spi_ctrl",
        "tests": 0,
        "failures": 0,
        "errors": 1,
        "tool": "cocotb + iverilog",
        "note": "results.xml not found — build failed",
        "stdout_tail": result.stdout[-500:]
    }

with open(os.path.join(os.path.dirname(__file__), 'sim', 'sim_report.json'), 'w') as f:
    json.dump(summary, f, indent=2)

print(f"Tests: {summary['tests']}, Failures: {summary['failures']}, Errors: {summary['errors']}")
