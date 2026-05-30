"""
Verilog Analysis Tools Plugin for Common AI Agent.
Provides specialized tools for analyzing, debugging, and verifying Verilog code.
Core: Python re module (zero-dependency). Enhanced: pyslang (pip install pyslang).
"""
import os
import re
import glob
from typing import Dict, List, Optional, Any

from core.pyslang_compat import (
    can_compile_probe,
    compile_files as compile_pyslang_files,
    diagnostic_is_error,
    diagnostic_line,
    diagnostic_message,
    top_instances,
)

# pyslang: IEEE 1800-2017 SV parser — enables AST-level analysis without external binaries
# Controlled by ENABLE_PYSLANG env var (default: true). Falls back to regex if unavailable.
import os as _os
_ENABLE_PYSLANG = _os.getenv("ENABLE_PYSLANG", "true").lower() in ("true", "1", "yes")
HAS_PYSLANG, _PYSLANG_UNAVAILABLE_REASON = can_compile_probe() if _ENABLE_PYSLANG else (
    False,
    "disabled by ENABLE_PYSLANG",
)

_IP_SUBDIRS = frozenset({
    "rtl", "yaml", "tb", "tc", "sim", "sdc", "lint", "doc", "wiki",
    "req", "list", "model", "syn", "sta", "pnr", "cov", "verify",
    "todo", "sta-post",
})


def _resolve_sv_path(path: str) -> str:
    """Resolve ATLAS IP-relative Verilog paths for standalone HDL tools."""
    if not path:
        return path
    norm = os.path.expanduser(str(path).strip()).replace("\\", "/")
    if os.path.isabs(norm) or re.match(r"^[A-Za-z]:/", norm) or norm.startswith("//"):
        return norm
    while norm.startswith("./"):
        norm = norm[2:]
    parts = [part for part in norm.split("/") if part and part != "."]
    if not parts or any(part == ".." for part in parts):
        return norm

    project_root = (
        os.environ.get("ATLAS_PROJECT_ROOT", "")
        or os.environ.get("PROJECT_ROOT", "")
    ).strip()
    active_ip = (os.environ.get("ATLAS_ACTIVE_IP", "") or "").strip()
    ip_root = (os.environ.get("ATLAS_IP_ROOT", "") or "").strip()
    candidates = []
    first = parts[0]

    if active_ip and active_ip != "default":
        if project_root:
            if first == active_ip:
                candidates.append(os.path.join(project_root, *parts))
            elif first in _IP_SUBDIRS:
                candidates.append(os.path.join(project_root, active_ip, *parts))
        if ip_root and first in _IP_SUBDIRS:
            candidates.append(os.path.join(ip_root, *parts))
    if project_root:
        candidates.append(os.path.join(project_root, norm))
    candidates.append(norm)

    seen = set()
    for candidate in candidates:
        resolved = os.path.abspath(os.path.expanduser(candidate))
        if resolved in seen:
            continue
        seen.add(resolved)
        if os.path.exists(resolved):
            return resolved
    return norm

# --- Phase 1: Foundation Tools ---

def analyze_verilog_module(path: str, deep: bool = False) -> Dict[str, Any]:
    """
    Parses a Verilog module and extracts structure and metrics.
    
    Args:
        path: Path to the Verilog file
        deep: If True, performs deeper analysis (complexity, logic depth)
        
    Returns:
        Dictionary containing module info (name, ports, signals, etc.)
    """
    path = _resolve_sv_path(path)
    if not os.path.exists(path):
        return {"error": f"File not found: {path}"}
        
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Remove comments for easier parsing
        content_no_comments = re.sub(r'//.*', '', content)
        content_no_comments = re.sub(r'/\*.*?\*/', '', content_no_comments, flags=re.DOTALL)
        
        result = {
            "file_path": path,
            "module_name": None,
            "parameters": [],
            "ports": {"input": [], "output": [], "inout": []},
            "signals": {"reg": [], "wire": []},
            "instances": [],
            "metrics": {}
        }
        
        # 1. Module Name
        module_match = re.search(r'module\s+(\w+)', content_no_comments)
        if module_match:
            result["module_name"] = module_match.group(1)
            
        # 2. Parameters
        # parameter WIDTH = 64;
        # module m #(parameter WIDTH = 64)
        param_matches = re.finditer(r'parameter\s+(?:\[.*?\]\s*)?(\w+)\s*=\s*([^;,)]+)', content_no_comments)
        for m in param_matches:
            result["parameters"].append(f"{m.group(1)}={m.group(2).strip()}")
            
        # 3. Ports
        # Robust parsing: Extract content inside module (...)
        # Then parse individual declarations
        header_match = re.search(r'module\s+\w+\s*(?:#\(.*?\)\s*)?\((.*?)\);', content_no_comments, re.DOTALL)
        if header_match:
            ports_content = header_match.group(1)
            # Split by comma, but respect brackets
            # Simple split might fail on [WIDTH-1:0], so we use a simple iterator
            
            # Normalize whitespace
            ports_content = " ".join(ports_content.split())
            
            # Split by comma (assuming no commas in widths for now, or simple ones)
            # A better way is to iterate and track brackets, but for Phase 1 we try splitting
            # If we have [1,2], this split fails. But Verilog widths usually use :
            raw_ports = ports_content.split(',')
            
            for raw_port in raw_ports:
                raw_port = raw_port.strip()
                if not raw_port:
                    continue
                    
                # Parse direction: input, output, inout
                # Regex: (dir) (type)? (width)? name
                port_match = re.match(
                    r'(input|output|inout)\s+'
                    r'(?:(?:reg|wire|logic)\s+)?'
                    r'(?:(?:signed|unsigned)\s+)?'
                    r'(?:\[.*?\]\s*)?'
                    r'(\w+)',
                    raw_port,
                )
                if port_match:
                    p_dir = port_match.group(1)
                    p_name = port_match.group(2)
                    result["ports"][p_dir].append(p_name)
                else:
                    # Maybe it's a list: input a, b (handled by split, but direction is missing on b)
                    # ANSI style requires direction on each port usually, or inherits?
                    # In ANSI: input a, input b.
                    # In Non-ANSI: input a, b;
                    pass
        else:
            # Fallback for Non-ANSI style (ports declared inside body)
            port_dirs = ["input", "output", "inout"]
            for p_dir in port_dirs:
                pattern = (
                    rf'{p_dir}\s+(?:(?:reg|wire|logic)\s+)?'
                    rf'(?:(?:signed|unsigned)\s+)?'
                    rf'(?:\[.*?\]\s*)?([^;]+);'
                )
                matches = re.finditer(pattern, content_no_comments)
                for m in matches:
                    raw_names = m.group(1)
                    names = [n.strip().split('=')[0].strip() for n in raw_names.split(',')]
                    result["ports"][p_dir].extend([n for n in names if n])

        # 4. Signals (Internal)
        # reg [63:0] count;
        # wire overflow;
        for sig_type in ["reg", "wire"]:
            pattern = rf'{sig_type}\s+(?:\[.*?\])?\s*([^;]+);'
            matches = re.finditer(pattern, content_no_comments)
            for m in matches:
                raw_names = m.group(1)
                names = [n.strip().split('=')[0].strip() for n in raw_names.split(',')]
                # Filter out ports if they are redeclared (e.g. output reg)
                # This is a simple heuristic
                result["signals"][sig_type].extend([n for n in names if n])

        # 5. Instances
        # mod_name inst_name ( ... );
        # Exclude 'module' keyword itself
        # This regex looks for: word word ( ... );
        # It's tricky to distinguish from function calls, but in Verilog usually instances are top-level
        instance_pattern = r'^\s*(\w+)\s+(?:#\(.*?\)\s*)?(\w+)\s*\('
        inst_matches = re.finditer(instance_pattern, content_no_comments, re.MULTILINE)
        for m in inst_matches:
            mod_type = m.group(1)
            inst_name = m.group(2)
            if mod_type not in ["module", "always", "initial", "assign", "function", "task", "if", "else", "case", "endcase", "begin", "end"]:
                result["instances"].append({"type": mod_type, "name": inst_name})

        # Deep Analysis
        if deep:
            # Complexity: Count always blocks
            always_count = len(re.findall(r'always\s*@', content_no_comments))
            assign_count = len(re.findall(r'assign\s+', content_no_comments))
            
            # Logic Depth (Heuristic: count non-blocking assignments in one block? Hard with regex)
            # For now, just return counts
            result["metrics"] = {
                "always_blocks": always_count,
                "assign_statements": assign_count,
                "lines": len(content.splitlines())
            }
            
        return result
        
    except Exception as e:
        return {"error": f"Failed to parse: {e}"}

def find_signal_usage(directory: str, signal_name: str) -> str:
    """
    Finds all usages of a signal in Verilog files within a directory.
    
    Args:
        directory: Directory to search in
        signal_name: Name of the signal to find
        
    Returns:
        Formatted string with search results
    """
    results = []
    files = glob.glob(os.path.join(directory, "**/*.v"), recursive=True)
    
    # Regex patterns for classification
    # Driver: signal <= ... or signal = ... or .port(signal) (output port?)
    # Reader: ... = signal ... or if (signal)
    
    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            for i, line in enumerate(lines):
                if signal_name in line:
                    line_clean = line.strip()
                    # Skip comments
                    if line_clean.startswith("//"):
                        continue
                        
                    # Classify usage
                    usage_type = "[REF]" # Default
                    
                    # Check for Declaration
                    if re.search(rf'(?:input|output|inout|reg|wire).*?\b{signal_name}\b', line_clean):
                        usage_type = "[DEF]"
                    # Check for Driver (LHS)
                    elif re.search(rf'\b{signal_name}\b\s*(?:<=|=)', line_clean):
                        usage_type = "[DRV]"
                    # Check for Port connection .port(signal)
                    elif re.search(rf'\.\w+\s*\(\s*{signal_name}\s*\)', line_clean):
                        usage_type = "[PORT]"
                    # Check for Reader (RHS) - heuristic
                    elif re.search(rf'(?:<=|=).*?\b{signal_name}\b', line_clean) or "if" in line_clean or "case" in line_clean:
                        usage_type = "[READ]"
                        
                    results.append(f"{usage_type} {os.path.basename(file_path)}:{i+1} - {line_clean}")
                    
        except Exception:
            continue
            
    if not results:
        return f"Signal '{signal_name}' not found in {directory}"
        
    return "\n".join(results)

def find_module_definition(module_name: str, directory: str = ".") -> str:
    """
    Finds the file defining a specific Verilog module.
    
    Args:
        module_name: Name of the module
        directory: Directory to search
        
    Returns:
        Path to the file and line number, or message if not found
    """
    files = glob.glob(os.path.join(directory, "**/*.v"), recursive=True)
    
    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            match = re.search(rf'module\s+{module_name}\b', content)
            if match:
                # Find line number
                line_num = content[:match.start()].count('\n') + 1
                
                # Get quick stats
                lines = content.splitlines()
                port_count = len(re.findall(r'(?:input|output|inout)', content))
                
                return (f"Found '{module_name}' in {file_path}:{line_num}\n"
                        f"  - Lines: {len(lines)}\n"
                        f"  - Approx Ports: {port_count}")
                        
        except Exception:
            continue
            
    return f"Module '{module_name}' definition not found in {directory}"

# --- Phase 2: Smart Analysis Tools ---

def extract_module_hierarchy(top_module: str, directory: str = ".") -> str:
    """
    Builds and visualizes the instantiation hierarchy tree starting from top_module.
    
    Args:
        top_module: Name of the top-level module
        directory: Directory to search for modules
        
    Returns:
        String representation of the hierarchy tree
    """
    hierarchy = []
    visited = set()
    
    def _build_tree(module_name, prefix="", is_last=True):
        if module_name in visited:
            hierarchy.append(f"{prefix}{'└── ' if is_last else '├── '}{module_name} (Recursive/Cycle)")
            return
        
        # Find module definition
        def_info = find_module_definition(module_name, directory)
        if "not found" in def_info:
            hierarchy.append(f"{prefix}{'└── ' if is_last else '├── '}{module_name} [Module Not Found]")
            return
            
        # Extract file path from def_info (simple parsing)
        file_path = def_info.split(" in ")[1].split(":")[0]
        
        # Analyze module to find instances
        info = analyze_verilog_module(file_path)
        instances = info.get("instances", [])
        
        # Add current node
        connector = "└── " if is_last else "├── "
        hierarchy.append(f"{prefix}{connector}{module_name} ({os.path.basename(file_path)})")
        
        # Recurse
        visited.add(module_name)
        child_prefix = prefix + ("    " if is_last else "│   ")
        
        for i, inst in enumerate(instances):
            sub_mod = inst["type"]
            inst_name = inst["name"]
            is_last_child = (i == len(instances) - 1)
            
            # Display instance name alongside module type
            display_name = f"{inst_name} ({sub_mod})"
            _build_tree(sub_mod, child_prefix, is_last_child)
            
        visited.remove(module_name)

    _build_tree(top_module)
    return "\n".join(hierarchy)

def generate_module_testbench(path: str, tb_type: str = "basic") -> str:
    """
    Generates a Verilog testbench for a given module.
    
    Args:
        path: Path to the Verilog module file
        tb_type: Type of testbench ('basic', 'random')
        
    Returns:
        Generated testbench code
    """
    info = analyze_verilog_module(path)
    if "error" in info:
        return f"Error: {info['error']}"
        
    mod_name = info.get("module_name", "unknown")
    ports = info.get("ports", {})
    params = info.get("parameters", [])
    
    # Prepare signals
    inputs = ports.get("input", [])
    outputs = ports.get("output", [])
    inouts = ports.get("inout", [])
    
    # Generate TB code
    lines = []
    lines.append(f"`timescale 1ns/1ps")
    lines.append(f"module tb_{mod_name};")
    
    # Parameters
    if params:
        lines.append("\n    // Parameters")
        for p in params:
            name, val = p.split('=')
            lines.append(f"    parameter {name} = {val};")
            
    # Signals
    lines.append("\n    // Signals")
    for p in inputs:
        lines.append(f"    reg {p};") # Inputs become regs
    for p in outputs:
        lines.append(f"    wire {p};") # Outputs become wires
    for p in inouts:
        lines.append(f"    wire {p};")
        
    # DUT Instantiation
    lines.append(f"\n    // DUT Instantiation")
    lines.append(f"    {mod_name} #(")
    # Parameter mapping
    if params:
        param_map = [f".{p.split('=')[0]}({p.split('=')[0]})" for p in params]
        lines.append("        " + ",\n        ".join(param_map))
    lines.append("    ) u_dut (")
    
    # Port mapping
    port_map = []
    all_ports = inputs + outputs + inouts
    for p in all_ports:
        # Handle array names: count[63:0] -> .count(count)
        # Regex to strip width: name[...] -> name
        clean_name = re.sub(r'\[.*?\]', '', p).strip()
        port_map.append(f".{clean_name}({clean_name})")
        
    lines.append("        " + ",\n        ".join(port_map))
    lines.append("    );")
    
    # Clock Generation
    has_clk = any("clk" in p for p in inputs)
    if has_clk:
        lines.append("\n    // Clock Generation")
        lines.append("    initial begin")
        lines.append("        clk = 0;")
        lines.append("        forever #5 clk = ~clk;")
        lines.append("    end")
        
    # Stimulus
    lines.append("\n    // Stimulus")
    lines.append("    initial begin")
    lines.append("        // Initialize Inputs")
    for p in inputs:
        clean_name = re.sub(r'\[.*?\]', '', p).strip()
        if "clk" not in clean_name:
            lines.append(f"        {clean_name} = 0;")
            
    # Reset sequence - handle ALL reset signals (not just first one)
    rst_names = [p for p in inputs if "rst" in p.lower() or "reset" in p.lower()]
    if rst_names:
        lines.append(f"\n        // Reset Sequence (handling {len(rst_names)} reset signal(s))")
        # First, assert all resets
        for rst_name in rst_names:
            clean_rst = re.sub(r'\[.*?\]', '', rst_name).strip()
            is_active_low = "_n" in clean_rst.lower() or "_b" in clean_rst.lower()
            if is_active_low:
                lines.append(f"        {clean_rst} = 0;  // Assert active-low reset")
            else:
                lines.append(f"        {clean_rst} = 1;  // Assert active-high reset")
        lines.append(f"        #20;")
        # Then, de-assert all resets
        for rst_name in rst_names:
            clean_rst = re.sub(r'\[.*?\]', '', rst_name).strip()
            is_active_low = "_n" in clean_rst.lower() or "_b" in clean_rst.lower()
            if is_active_low:
                lines.append(f"        {clean_rst} = 1;  // De-assert active-low reset")
            else:
                lines.append(f"        {clean_rst} = 0;  // De-assert active-high reset")
            
    lines.append("\n        // Add test cases here")
    lines.append("        #100;")
    
    if tb_type == "random":
        lines.append("\n        // Random Stimulus")
        lines.append("        repeat(10) begin")
        lines.append("            #10;")
        for p in inputs:
            clean_name = re.sub(r'\[.*?\]', '', p).strip()
            if "clk" not in clean_name and "rst" not in clean_name and "reset" not in clean_name:
                lines.append(f"            {clean_name} = $random;")
        lines.append("        end")
        
    lines.append("\n        $display(\"Test completed\");")
    lines.append("        $finish;")
    lines.append("    end")
    
    # Waveform dump (optional but useful)
    lines.append("\n    initial begin")
    lines.append(f"        $dumpfile(\"tb_{mod_name}.vcd\");")
    lines.append("        $dumpvars(0, tb_" + mod_name + ");")
    lines.append("    end")
    
    lines.append("endmodule")
    
    return "\n".join(lines)

# --- Phase 3: Automated Verification Tools ---

def find_potential_issues(path: str) -> List[str]:
    """
    Performs static analysis to find potential issues (Linting).
    
    Args:
        path: Path to Verilog file
        
    Returns:
        List of warning messages
    """
    issues = []
    info = analyze_verilog_module(path)
    if "error" in info:
        return [f"Error parsing file: {info['error']}"]
        
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Remove comments
    content_clean = re.sub(r'//.*', '', content)
    content_clean = re.sub(r'/\*.*?\*/', '', content_clean, flags=re.DOTALL)
    
    # 1. Undriven Signals
    # Signals declared but never on LHS of assignment or input port
    declared_signals = set()
    declared_signals.update(info["ports"]["input"])
    declared_signals.update(info["ports"]["output"])
    declared_signals.update(info["ports"]["inout"])
    declared_signals.update(info["signals"]["reg"])
    declared_signals.update(info["signals"]["wire"])
    
    driven_signals = set(info["ports"]["input"]) # Inputs are driven externally
    
    # Find assignments (LHS)
    # assign x = ...
    assign_matches = re.finditer(r'assign\s+(\w+)\s*=', content_clean)
    for m in assign_matches:
        driven_signals.add(m.group(1))
        
    # always assignments (LHS of <= or =)
    # This is rough, assumes signal is first word on line or after begin/whitespace
    # Matches: "  x <= y" or "  x = y"
    always_assign_matches = re.finditer(r'(?:\s|^)(\w+)\s*(?:<=|=)', content_clean)
    for m in assign_matches:
        driven_signals.add(m.group(1))
    for m in always_assign_matches:
        driven_signals.add(m.group(1))
        
    # Check for instance outputs (rough heuristic)
    # .port(signal) - hard to know if port is output without checking submodule
    # So we skip this check if signal is connected to instance
    instance_connected = set()
    inst_matches = re.finditer(r'\.\w+\s*\(\s*(\w+)\s*\)', content_clean)
    for m in inst_matches:
        instance_connected.add(m.group(1))
        
    for sig in declared_signals:
        if sig not in driven_signals and sig not in instance_connected:
            issues.append(f"⚠️ Undriven signal: '{sig}' (declared but not assigned)")
            
    # 2. Multiple Drivers
    # Check if a signal is assigned in multiple always blocks
    # Split content into always blocks
    always_blocks = re.split(r'always\s*@', content_clean)[1:] # Skip preamble
    
    driver_counts = {}
    for block in always_blocks:
        # Extract LHS signals in this block
        lhs_sigs = set(re.findall(r'(\w+)\s*<=', block))
        lhs_sigs.update(re.findall(r'(\w+)\s*=', block))
        
        for sig in lhs_sigs:
            driver_counts[sig] = driver_counts.get(sig, 0) + 1
            
    for sig, count in driver_counts.items():
        if count > 1:
            issues.append(f"⚠️ Multiple drivers: '{sig}' assigned in {count} always blocks (Race Condition Risk)")
            
    # 3. Combinational Loops (Simple self-assignment)
    # assign a = ... a ...
    assign_lines = re.findall(r'assign\s+(\w+)\s*=\s*(.*?);', content_clean)
    for lhs, rhs in assign_lines:
        if re.search(rf'\b{lhs}\b', rhs):
             issues.append(f"🚫 Combinational Loop detected: 'assign {lhs} = ... {lhs} ...'")
             
    if not issues:
        issues.append("✅ No obvious issues found.")
        
    return issues

def analyze_timing_paths(path: str) -> str:
    """
    Estimates logic depth of combinational paths.
    Builds a simple dependency graph from 'assign' statements.
    """
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    content = re.sub(r'//.*', '', content)
    
    # Build Graph: Driven -> [Drivers]
    # Only considers 'assign' statements for now (Combinational logic)
    graph = {}
    
    assign_matches = re.finditer(r'assign\s+(\w+)\s*=\s*(.*?);', content)
    for m in assign_matches:
        lhs = m.group(1)
        rhs = m.group(2)
        # Find all words in RHS that are potential signals
        drivers = re.findall(r'[a-zA-Z_]\w*', rhs)
        graph[lhs] = [d for d in drivers if d != lhs] # Avoid self-loop in graph
        
    # Calculate depth
    # Roots are signals not driven by other assigns (Inputs or Regs)
    memo = {}
    
    def get_depth(sig, path_stack):
        if sig in path_stack: return 0 # Cycle detected
        if sig in memo: return memo[sig]
        if sig not in graph: return 0 # Input or Reg
        
        path_stack.append(sig)
        max_d = 0
        for driver in graph[sig]:
            max_d = max(max_d, get_depth(driver, path_stack))
        path_stack.pop()
        
        memo[sig] = 1 + max_d
        return 1 + max_d
        
    # Analyze all driven signals
    results = []
    for sig in graph:
        depth = get_depth(sig, [])
        if depth > 0:
            results.append((sig, depth))
            
    results.sort(key=lambda x: x[1], reverse=True)
    
    output = ["Logic Depth Estimation (Combinational Levels):"]
    for sig, depth in results[:5]: # Top 5
        output.append(f"- {sig}: {depth} levels")
        if depth > 5:
            output.append(f"  ⚠️  High logic depth! Consider pipelining.")
            
    if not results:
        output.append("No combinational paths found (or only simple assignments).")
        
    return "\n".join(output)

def generate_waveform_dict(path: str) -> str:
    """
    Generates a GTKWave TCL script to add all signals.
    """
    info = analyze_verilog_module(path)
    if "error" in info:
        return "Error parsing file."
        
    mod_name = info.get("module_name", "top")
    
    lines = []
    lines.append(f"# GTKWave Script for {mod_name}")
    lines.append(f"set nfac [gtkwave::getNumFacs]")
    lines.append(f"gtkwave::addSignalsFromList {{")
    
    # Add Clock and Reset first
    for p in info["ports"]["input"]:
        if "clk" in p or "rst" in p or "reset" in p:
             lines.append(f"    tb_{mod_name}.u_dut.{p}")
             
    # Add Inputs
    for p in info["ports"]["input"]:
        if "clk" not in p and "rst" not in p and "reset" not in p:
            lines.append(f"    tb_{mod_name}.u_dut.{p}")
            
    # Add Outputs
    for p in info["ports"]["output"]:
        lines.append(f"    tb_{mod_name}.u_dut.{p}")
        
    # Add Registers (Internal state)
    for p in info["signals"]["reg"]:
        lines.append(f"    tb_{mod_name}.u_dut.{p}")
        
    lines.append("}")
    lines.append(f"gtkwave::/Edit/Insert_Comment \"Internal Signals\"")
    
    return "\n".join(lines)

# --- Phase 4: Documentation & Optimization Tools ---

def generate_module_docs(path: str) -> str:
    """
    Generates Markdown documentation for a Verilog module.
    
    Args:
        path: Path to Verilog file
        
    Returns:
        Markdown string
    """
    info = analyze_verilog_module(path)
    if "error" in info:
        return f"Error: {info['error']}"
        
    mod_name = info.get("module_name", "unknown")
    
    docs = []
    docs.append(f"# Module: `{mod_name}`")
    docs.append(f"\n**File**: `{os.path.basename(path)}`")
    
    # Overview (Extract comments before module declaration)
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Simple heuristic for description: Comments right before module
    match = re.search(r'(//.*?\n)+module', content)
    if match:
        desc = match.group(0).replace('module', '').replace('//', '').strip()
        docs.append(f"\n## Description\n{desc}")
        
    # Ports Table
    docs.append("\n## Interface")
    docs.append("| Name | Direction | Type | Description |")
    docs.append("|------|-----------|------|-------------|")
    
    all_ports = []
    for p in info["ports"]["input"]: all_ports.append((p, "input"))
    for p in info["ports"]["output"]: all_ports.append((p, "output"))
    for p in info["ports"]["inout"]: all_ports.append((p, "inout"))
    
    for name, direction in all_ports:
        # Try to find width and type from raw content if possible, 
        # but analyze_verilog_module simplified it. 
        # For now, we list what we have.
        # TODO: Enhance analyze_verilog_module to return full port info objects
        docs.append(f"| `{name}` | {direction} | Wire/Reg | - |")
        
    # Parameters
    if info["parameters"]:
        docs.append("\n## Parameters")
        docs.append("| Name | Value | Description |")
        docs.append("|------|-------|-------------|")
        for p in info["parameters"]:
            name, val = p.split('=')
            docs.append(f"| `{name}` | `{val}` | - |")
            
    # Metrics
    if "metrics" in info:
        docs.append("\n## Metrics")
        docs.append(f"- **Lines**: {info['metrics'].get('lines', '?')}")
        docs.append(f"- **Always Blocks**: {info['metrics'].get('always_blocks', '?')}")
        
    return "\n".join(docs)

def suggest_optimizations(path: str) -> List[str]:
    """
    Suggests code optimizations for Verilog modules.
    
    Args:
        path: Path to Verilog file
        
    Returns:
        List of suggestion strings
    """
    suggestions = []
    
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # 1. Resource Sharing (Multipliers)
    # Count multipliers
    mult_count = content.count('*')
    if mult_count > 2:
        suggestions.append(f"💡 Resource Sharing: Found {mult_count} multipliers. Consider sharing resources using MUXes if they are not active simultaneously.")
        
    # 2. FSM Encoding
    # Detect state parameters
    state_params = re.findall(r'parameter\s+\w+\s*=\s*\d+\'b[01]+', content)
    if len(state_params) > 8:
        suggestions.append(f"💡 FSM Encoding: Found {len(state_params)} states. For large FSMs (>8 states), consider One-Hot encoding for speed, or Gray code for glitch reduction.")
        
    # 3. Register Duplication (High Fanout)
    # Rough heuristic: check if a signal is used many times
    # This requires deep analysis, so we use a placeholder for now
    
    # 4. Arithmetic Operator Replacement
    if "/" in content or "%" in content:
        suggestions.append("💡 Expensive Operation: Found division/modulo operator. Ensure the divisor is a power of 2 for optimization, otherwise this will synthesize to a large circuit.")
        
    if not suggestions:
        suggestions.append("✅ No obvious optimizations found.")
        
    return suggestions

# ─────────────────────────────────────────────────────────────────────────────
# pyslang-powered tools (require: pip install pyslang)
# ─────────────────────────────────────────────────────────────────────────────

def _normalise_sv_direction(raw: Any) -> str:
    value = str(raw).replace("ArgumentDirection.", "").lower()
    return {
        "in": "input",
        "input": "input",
        "out": "output",
        "output": "output",
        "inout": "inout",
        "ref": "ref",
    }.get(value, value or "unknown")


def _split_sv_commas(text: str) -> List[str]:
    parts = []
    start = 0
    depth = 0
    pairs = {"(": ")", "[": "]", "{": "}"}
    closers = set(pairs.values())
    for idx, ch in enumerate(text):
        if ch in pairs:
            depth += 1
        elif ch in closers and depth > 0:
            depth -= 1
        elif ch == "," and depth == 0:
            parts.append(text[start:idx].strip())
            start = idx + 1
    tail = text[start:].strip()
    if tail:
        parts.append(tail)
    return parts


def _sv_width_from_range(width_expr: str) -> int:
    m = re.search(r'\[(\d+)\s*:\s*(\d+)\]', width_expr or "")
    if not m:
        return 1
    return abs(int(m.group(1)) - int(m.group(2))) + 1


def _regex_module_summaries(path: str) -> List[Dict[str, Any]]:
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    content_no_comments = re.sub(r'//.*', '', content)
    content_no_comments = re.sub(r'/\*.*?\*/', '', content_no_comments, flags=re.DOTALL)

    modules: List[Dict[str, Any]] = []
    for match in re.finditer(r'\bmodule\s+(\w+)\b.*?\bendmodule\b', content_no_comments, re.DOTALL):
        block = match.group(0)
        name = match.group(1)
        header_match = re.search(
            rf'\bmodule\s+{re.escape(name)}\s*(?:#\s*\(.*?\)\s*)?\((.*?)\)\s*;',
            block,
            re.DOTALL,
        )
        header = header_match.group(1) if header_match else ""
        body = block[header_match.end():] if header_match else block
        ports: Dict[str, List[Dict[str, Any]]] = {"input": [], "output": [], "inout": []}

        last_direction = ""
        last_type = "logic"
        last_width_expr = ""
        for raw_port in _split_sv_commas(" ".join(header.split())):
            port_match = re.match(
                r'(?:(input|output|inout)\s+)?'
                r'(?:(reg|wire|logic)\s+)?'
                r'(?:(?:signed|unsigned)\s+)?'
                r'(\[[^\]]+\]\s*)?'
                r'(\w+)\b',
                raw_port,
            )
            if not port_match:
                continue
            direction = port_match.group(1) or last_direction
            if not direction:
                continue
            port_type = port_match.group(2) or last_type
            width_expr = port_match.group(3) or last_width_expr
            last_direction = direction
            last_type = port_type
            last_width_expr = width_expr
            ports.setdefault(direction, []).append({
                "name": port_match.group(4),
                "direction": direction,
                "type": port_type,
                "width": _sv_width_from_range(width_expr),
                "type_full": f"{port_type}{width_expr.strip()}".strip(),
            })

        for p_dir in ("input", "output", "inout"):
            pattern = (
                rf'{p_dir}\s+(?:(?:reg|wire|logic)\s+)?'
                rf'(?:(?:signed|unsigned)\s+)?'
                rf'(\[[^\]]+\]\s*)?([^;]+);'
            )
            for decl in re.finditer(pattern, body):
                width_expr = decl.group(1) or ""
                for name_part in _split_sv_commas(decl.group(2)):
                    name_match = re.match(r'(\w+)', name_part.strip())
                    if not name_match:
                        continue
                    pname = name_match.group(1)
                    if any(p["name"] == pname for p in ports.get(p_dir, [])):
                        continue
                    ports.setdefault(p_dir, []).append({
                        "name": pname,
                        "direction": p_dir,
                        "type": "logic",
                        "width": _sv_width_from_range(width_expr),
                        "type_full": f"logic{width_expr.strip()}".strip(),
                    })

        instance_pattern = r'^\s*(\w+)\s+(?:#\(.*?\)\s*)?(\w+)\s*\('
        instances = []
        for inst in re.finditer(instance_pattern, body, re.MULTILINE):
            mod_type, inst_name = inst.group(1), inst.group(2)
            if mod_type not in ["module", "always", "initial", "assign", "function", "task", "if", "else", "case", "endcase", "begin", "end"]:
                instances.append({"module": mod_type, "instance": inst_name})

        params = [
            f"{m.group(1)}={m.group(2).strip()}"
            for m in re.finditer(r'parameter\s+(?:\[.*?\]\s*)?(\w+)\s*=\s*([^;,)]+)', block)
        ]
        modules.append({"name": name, "ports": ports, "parameters": params, "instances": instances})
    return modules


def _select_regex_top(modules: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not modules:
        return None
    instantiated = {
        inst.get("module")
        for module in modules
        for inst in module.get("instances", [])
        if inst.get("module")
    }
    candidates = [module for module in modules if module.get("name") not in instantiated]
    with_instances = [module for module in candidates if module.get("instances")]
    if with_instances:
        return with_instances[-1]
    if candidates:
        return candidates[-1]
    return modules[-1]


def _regex_ports_fallback(path: str, reason: str) -> List[Dict[str, Any]]:
    try:
        top = _select_regex_top(_regex_module_summaries(path))
    except Exception:
        top = None
    if top is not None:
        ports = []
        for port_list in (top.get("ports") or {}).values():
            for port in port_list:
                ports.append({
                    **port,
                    "backend": "regex-fallback",
                    "warning": reason,
                })
        if ports:
            return ports

    parsed = analyze_verilog_module(path)
    if parsed.get("error"):
        return [{"error": f"{reason}; regex fallback failed: {parsed['error']}"}]

    ports: List[Dict[str, Any]] = []
    for direction, names in (parsed.get("ports") or {}).items():
        for name in names:
            ports.append({
                "name": name,
                "direction": direction,
                "type": "logic",
                "width": 1,
                "type_full": "logic",
                "backend": "regex-fallback",
                "warning": reason,
            })
    if ports:
        return ports
    return [{"error": f"{reason}; regex fallback found no ports"}]


def _regex_hierarchy_fallback(path: str, reason: str) -> Dict[str, Any]:
    try:
        top = _select_regex_top(_regex_module_summaries(path))
    except Exception:
        top = None
    if top is not None:
        return {
            "top": top.get("name"),
            "parameters": top.get("parameters", []),
            "instances": top.get("instances", []),
            "backend": "regex-fallback",
            "warning": reason,
        }

    parsed = analyze_verilog_module(path)
    if parsed.get("error"):
        return {"error": f"{reason}; regex fallback failed: {parsed['error']}"}
    return {
        "top": parsed.get("module_name"),
        "parameters": parsed.get("parameters", []),
        "instances": [
            {"instance": inst.get("name"), "module": inst.get("type")}
            for inst in parsed.get("instances", [])
        ],
        "backend": "regex-fallback",
        "warning": reason,
    }


def sv_get_ports(path: str) -> List[Dict[str, Any]]:
    """
    Extract port list from a Verilog/SV file using pyslang AST.
    Returns accurate direction, type, and width — no regex parsing ambiguity.

    Args:
        path: Path to .v / .sv file

    Returns:
        List of dicts: [{"name": "clk", "direction": "input", "type": "logic", "width": 1}, ...]
        On error or pyslang unavailable, returns {"error": "..."} in a list.
    """
    path = _resolve_sv_path(path)
    if not os.path.exists(path):
        return [{"error": f"File not found: {path}"}]
    if not HAS_PYSLANG:
        return _regex_ports_fallback(path, f"pyslang unavailable: {_PYSLANG_UNAVAILABLE_REASON}")

    try:
        compiled = compile_pyslang_files([path])
        if compiled.error:
            return _regex_ports_fallback(path, f"pyslang compile setup failed: {compiled.error}")
        comp = compiled.compilation

        ports = []
        for inst in top_instances(comp):
            body = getattr(inst, "body", None)
            port_list = getattr(body, "portList", None) or getattr(inst, "ports", None) or []
            for port in port_list:
                t = port.type
                type_str = str(t)
                # Extract width from type string e.g. "logic[7:0]" → 8
                width = 1
                m = re.search(r'\[(\d+):(\d+)\]', type_str)
                if m:
                    width = abs(int(m.group(1)) - int(m.group(2))) + 1
                base_type = re.sub(r'\[.*?\]', '', type_str).strip() or 'logic'
                direction = _normalise_sv_direction(getattr(port, "direction", ""))
                ports.append({
                    "name": getattr(port, "name", ""),
                    "direction": direction,
                    "type": base_type,
                    "width": width,
                    "type_full": type_str,
                    "backend": "pyslang",
                })
        return ports or _regex_ports_fallback(path, "pyslang returned no ports")
    except Exception as e:
        return _regex_ports_fallback(path, f"pyslang port extraction failed: {e}")


def sv_get_hierarchy(path: str) -> Dict[str, Any]:
    """
    Extract module instantiation hierarchy from a single SV/Verilog file using pyslang.
    Does NOT require full compilation — works with a single file even if submodules are missing.

    Args:
        path: Path to .v / .sv file

    Returns:
        Dict with top module name and list of instances:
        {
          "top": "counter",
          "instances": [{"instance": "u_sub", "module": "sub_module"}, ...]
          "parameters": ["WIDTH=8"]
        }
    """
    path = _resolve_sv_path(path)
    if not os.path.exists(path):
        return {"error": f"File not found: {path}"}
    if not HAS_PYSLANG:
        return _regex_hierarchy_fallback(path, f"pyslang unavailable: {_PYSLANG_UNAVAILABLE_REASON}")

    try:
        compiled = compile_pyslang_files([path])
        if compiled.error:
            return _regex_hierarchy_fallback(path, f"pyslang compile setup failed: {compiled.error}")
        comp = compiled.compilation

        tops = top_instances(comp)
        if not tops:
            return _regex_hierarchy_fallback(path, "pyslang found no top-level module")

        top_inst = tops[0]
        top_name = getattr(getattr(top_inst, "definition", None), "name", None) or getattr(top_inst, "name", "")

        # Parameters
        params = []
        body = getattr(top_inst, "body", None)
        for p in getattr(body, "parameters", []) or []:
            params.append(f"{getattr(p, 'name', '')}={getattr(p, 'value', '')}")

        # Sub-instances via visitor
        sub_instances = []
        def visitor(node):
            if "Instance" in str(getattr(node, "kind", "")) and "Body" not in str(getattr(node, "kind", "")):
                sub_instances.append({
                    "instance": getattr(node, "name", ""),
                    "module": getattr(getattr(node, "definition", None), "name", ""),
                })
            action = getattr(compiled.pyslang, "VisitAction", None)
            return getattr(action, "Advance", None) if action is not None else None

        visit = getattr(body, "visit", None)
        if visit is not None:
            visit(visitor)
        elif body is not None:
            for member in body:
                if "Instance" in str(getattr(member, "kind", "")) and "Body" not in str(getattr(member, "kind", "")):
                    sub_instances.append({
                        "instance": getattr(member, "name", ""),
                        "module": getattr(getattr(member, "definition", None), "name", ""),
                    })

        return {
            "top": top_name,
            "parameters": params,
            "instances": sub_instances,
            "backend": "pyslang",
        }
    except Exception as e:
        return _regex_hierarchy_fallback(path, f"pyslang hierarchy extraction failed: {e}")


def sv_compile(files: List[str]) -> str:
    """
    Compile multiple SV/Verilog files together using pyslang and report all diagnostics.
    Useful for cross-reference checking (unresolved ports, type mismatches, etc.)
    across a multi-file design. Does not require VCS/iverilog.

    Args:
        files: List of .v / .sv file paths

    Returns:
        Formatted string with all errors and warnings, or "No issues found."
    """
    if not HAS_PYSLANG:
        return f"pyslang unavailable: {_PYSLANG_UNAVAILABLE_REASON}"

    files = [_resolve_sv_path(f) for f in files]
    missing = [f for f in files if not os.path.exists(f)]
    if missing:
        return f"Files not found: {', '.join(missing)}"

    try:
        compiled = compile_pyslang_files(files)
        if compiled.error:
            return f"Compilation setup error: {compiled.error}"

        diags = compiled.diagnostics
        if not diags:
            return f"✅ No issues found across {len(files)} file(s)."

        sm = compiled.source_manager
        lines = []
        errors = warnings = 0
        for d in diags:
            line_num = diagnostic_line(d, sm)
            msg = diagnostic_message(compiled.pyslang, d, sm)
            if diagnostic_is_error(d):
                lines.append(f"❌ Line {line_num}: {msg}")
                errors += 1
            else:
                lines.append(f"⚠️  Line {line_num}: {msg}")
                warnings += 1

        summary = f"{errors} error(s), {warnings} warning(s) across {len(files)} file(s):"
        return summary + "\n" + "\n".join(lines)
    except Exception as e:
        return f"Compilation error: {e}"


# Export tools registry
VERILOG_TOOLS = {
    "analyze_verilog_module": analyze_verilog_module,
    "find_signal_usage": find_signal_usage,
    "find_module_definition": find_module_definition,
    "extract_module_hierarchy": extract_module_hierarchy,
    "generate_module_testbench": generate_module_testbench,
    "find_potential_issues": find_potential_issues,
    "analyze_timing_paths": analyze_timing_paths,
    "generate_waveform_dict": generate_waveform_dict,
    "generate_module_docs": generate_module_docs,
    "suggest_optimizations": suggest_optimizations,
    # pyslang-powered (AST-level)
    "sv_get_ports": sv_get_ports,
    "sv_get_hierarchy": sv_get_hierarchy,
    "sv_compile": sv_compile,
}
