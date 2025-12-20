import os
import re
from pathlib import Path

# Configuration
SEARCH_ROOT = Path("../caliptra-ss")
REPORT_FILE = Path("caliptra_signal_report.md")

# Regex Patterns (Basic)
PATTERNS = {
    "module": re.compile(r"^\s*module\s+(\w+)", re.MULTILINE),
    "port": re.compile(r"^\s*(input|output|inout)\s+(?:logic|wire|reg)?\s*(?:\[[^\]]+\])?\s*(\w+)", re.MULTILINE),
    "signal": re.compile(r"^\s*(logic|wire|reg)\s+(?:\[[^\]]+\])?\s*(\w+)", re.MULTILINE),
    "parameter": re.compile(r"^\s*parameter\s+(\w+)", re.MULTILINE)
}

def analyze_file(file_path):
    """Analyzes a single Verilog file."""
    try:
        content = file_path.read_text(errors='ignore')
    except Exception as e:
        return f"Error reading file: {e}"

    analysis = {
        "module": "N/A",
        "ports": [],
        "signals": [],
        "parameters": [],
        "lines": len(content.splitlines())
    }

    # Extract info
    m_match = PATTERNS["module"].search(content)
    if m_match:
        analysis["module"] = m_match.group(1)

    analysis["ports"] = PATTERNS["port"].findall(content)
    analysis["signals"] = PATTERNS["signal"].findall(content)
    analysis["parameters"] = PATTERNS["parameter"].findall(content)
    
    return analysis

def generate_report():
    print(f"Searching for .sv and .v files in {SEARCH_ROOT.resolve()}...")
    
    verilog_files = sorted(list(SEARCH_ROOT.rglob("*.sv")) + list(SEARCH_ROOT.rglob("*.v")))
    
    if not verilog_files:
        print("No Verilog files found!")
        return

    with open(REPORT_FILE, "w") as f:
        f.write("# Caliptra Verilog Signal Analysis Report\n\n")
        f.write(f"**Root Directory:** `{SEARCH_ROOT}`\n")
        f.write(f"**Total Files Scanned:** {len(verilog_files)}\n\n")
        f.write("## File Summaries\n\n")
        f.write("| File | Module | Lines | Ports | Signals | Params |\n")
        f.write("|---|---|---|---|---|---|\n")

        total_ports = 0
        total_signals = 0

        details_section = []

        for v_file in verilog_files:
            # Relative path for readability
            try:
                rel_path = v_file.relative_to(SEARCH_ROOT)
            except ValueError:
                rel_path = v_file.name

            data = analyze_file(v_file)
            
            if isinstance(data, str): # Error
                print(f"Skipping {v_file}: {data}")
                continue

            num_ports = len(data["ports"])
            num_sig = len(data["signals"])
            num_param = len(data["parameters"])
            
            total_ports += num_ports
            total_signals += num_sig

            f.write(f"| `{rel_path}` | `{data['module']}` | {data['lines']} | {num_ports} | {num_sig} | {num_param} |\n")

            # Prepare details
            details_section.append(f"### {rel_path}\n")
            details_section.append(f"- **Module**: `{data['module']}`\n")
            if data["ports"]:
                details_section.append(f"- **Ports ({num_ports})**: {', '.join([p[1] for p in data['ports'][:10]])}{'...' if num_ports > 10 else ''}\n")
            if data["signals"]:
                details_section.append(f"- **Signals ({num_sig})**: {', '.join([s[1] for s in data['signals'][:10]])}{'...' if num_sig > 10 else ''}\n")
            details_section.append("\n")

        f.write("\n\n## Detailed Listings\n\n")
        f.writelines(details_section)
        
        f.write(f"\n\n---\n**Grand Totals:**\n- Ports: {total_ports}\n- Signals: {total_signals}\n")

    print(f"Report generated: {REPORT_FILE.resolve()}")

if __name__ == "__main__":
    generate_report()
