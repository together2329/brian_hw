"""
Simple Linter (Zero-Dependency with Optional External Tools)

Provides basic linting functionality using:
1. Python built-in compile() for syntax checking
2. pyslang (pip install pyslang) — preferred Verilog/SV linter, no binary needed
3. Optional external tools (pyflakes, pylint, iverilog/vcs) as fallback
4. Graceful degradation when tools not installed
"""

import subprocess
import shutil
import os
import sys
from pathlib import Path
from typing import Optional, List

# Read simulator config without importing full config (avoid circular imports)
# Default: vcs (Synopsys). Override with VERILOG_SIMULATOR=iverilog
_VERILOG_SIMULATOR = os.getenv("VERILOG_SIMULATOR", "vcs")

# pyslang: IEEE 1800-2017 SystemVerilog parser — preferred over external binaries
# Controlled by ENABLE_PYSLANG env var (default: true). Falls back if not installed.
_ENABLE_PYSLANG = os.getenv("ENABLE_PYSLANG", "true").lower() in ("true", "1", "yes")
try:
    if _ENABLE_PYSLANG:
        import pyslang as _pyslang
        HAS_PYSLANG = True
    else:
        HAS_PYSLANG = False
except ImportError:
    HAS_PYSLANG = False


class LintError:
    """Represents a single lint error"""

    def __init__(self, file: str, line: int, message: str, severity: str = "error"):
        self.file = file
        self.line = line
        self.message = message
        self.severity = severity  # "error" | "warning" | "info"

    def __str__(self):
        icon = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}.get(self.severity, "•")
        return f"{icon} Line {self.line}: {self.message}"

    def __repr__(self):
        return f"LintError(file={self.file!r}, line={self.line}, message={self.message!r}, severity={self.severity!r})"


class SimpleLinter:
    """
    Simple linter with zero dependencies.

    Features:
    - Python: compile() (built-in) + pyflakes (optional)
    - Verilog: iverilog or vcs (configured via VERILOG_SIMULATOR env var)
    - Graceful fallback when external tools not available
    """

    def __init__(self):
        self.simulator = _VERILOG_SIMULATOR
        self._check_available_tools()

    def _check_available_tools(self):
        """Check which external tools are available"""
        self.tools = {
            'pyslang': HAS_PYSLANG,
            'pyflakes': shutil.which('pyflakes') is not None,
            'pylint': shutil.which('pylint') is not None,
            'iverilog': shutil.which('iverilog') is not None,
            'vcs': shutil.which('vcs') is not None,
            'verilator': shutil.which('verilator') is not None,
        }

    def is_available(self, language: str) -> bool:
        """Check if linting is available for a language"""
        if language == 'python':
            return True  # Always available (built-in compile())
        elif language == 'verilog':
            # pyslang preferred (no binary); fallback vcs → iverilog → verilator
            return (self.tools['pyslang'] or self.tools['vcs']
                    or self.tools['iverilog'] or self.tools['verilator'])
        return False

    def _effective_verilog_tool(self) -> str:
        """Return the tool that will actually be used for Verilog linting."""
        if self.tools['pyslang']:
            return 'pyslang'
        if self.simulator == 'vcs' and self.tools['vcs']:
            return 'vcs'
        if self.tools['iverilog']:
            return 'iverilog'
        if self.tools['verilator']:
            return 'verilator'
        return ''

    def get_available_tools_info(self) -> str:
        """Get human-readable info about available tools"""
        effective = self._effective_verilog_tool()
        lines = [f"Available linting tools (Verilog: using {effective or 'none'}):"]
        lines.append(f"  ✅ Python (built-in compile())")

        for tool, available in self.tools.items():
            status = "✅" if available else "❌"
            active = " [active]" if tool == effective else ""
            lines.append(f"  {status} {tool}{active}")

        return "\n".join(lines)

    def check_file(self, filepath: str) -> List[LintError]:
        """
        Check file and return list of errors.

        Args:
            filepath: Path to file to check

        Returns:
            List of LintError objects (empty if no errors)
        """
        filepath = Path(filepath)

        if not filepath.exists():
            return [LintError(
                file=str(filepath),
                line=0,
                message=f"File not found: {filepath}",
                severity="error"
            )]

        # Detect language
        ext = filepath.suffix.lower()

        if ext == '.py':
            return self.check_python(filepath)
        elif ext in ['.v', '.sv', '.vh']:
            return self.check_verilog(filepath)
        else:
            # Unknown file type
            return []

    def check_python(self, filepath: Path) -> List[LintError]:
        """Check Python file using built-in compile() + optional pyflakes"""
        errors = []

        # 1. Syntax check (always available)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                source = f.read()

            compile(source, str(filepath), 'exec')
        except SyntaxError as e:
            errors.append(LintError(
                file=str(filepath),
                line=e.lineno or 0,
                message=e.msg,
                severity="error"
            ))
        except Exception as e:
            errors.append(LintError(
                file=str(filepath),
                line=0,
                message=f"Compilation error: {e}",
                severity="error"
            ))

        # 2. Additional checks with pyflakes (optional)
        if self.tools['pyflakes']:
            try:
                result = subprocess.run(
                    ['pyflakes', str(filepath)],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                if result.stdout:
                    # Parse pyflakes output
                    # Format: "file.py:10: undefined name 'foo'"
                    for line in result.stdout.strip().split('\n'):
                        if ':' in line:
                            parts = line.split(':', 2)
                            if len(parts) >= 3:
                                try:
                                    line_num = int(parts[1])
                                    msg = parts[2].strip()
                                    errors.append(LintError(
                                        file=str(filepath),
                                        line=line_num,
                                        message=msg,
                                        severity="warning"
                                    ))
                                except ValueError:
                                    pass
            except (subprocess.TimeoutExpired, Exception):
                # Ignore pyflakes errors
                pass

        return errors

    def _check_verilog_pyslang(self, filepath: Path) -> List[LintError]:
        """Lint using pyslang — IEEE 1800-2017 compliant, no binary required."""
        errors = []
        try:
            tree = _pyslang.SyntaxTree.fromFile(str(filepath))
            comp = _pyslang.Compilation()
            comp.addSyntaxTree(tree)

            sm = tree.sourceManager
            engine = _pyslang.DiagnosticEngine(sm)

            for diag in comp.getAllDiagnostics():
                severity = "error" if diag.isError() else "warning"
                loc = diag.location
                line = sm.getLineNumber(loc) if loc else 0
                message = engine.formatMessage(diag)
                errors.append(LintError(
                    file=str(filepath),
                    line=line,
                    message=message,
                    severity=severity,
                ))
        except Exception as e:
            errors.append(LintError(
                file=str(filepath),
                line=0,
                message=f"pyslang error: {e}",
                severity="error",
            ))
        return errors

    def check_verilog(self, filepath: Path) -> List[LintError]:
        """Check Verilog/SV file. Uses pyslang (preferred) → vcs → iverilog → verilator."""
        errors = []
        tool = self._effective_verilog_tool()

        # pyslang path (preferred — no binary required)
        if tool == 'pyslang':
            return self._check_verilog_pyslang(filepath)

        # VCS path (Synopsys commercial simulator)
        if tool == 'vcs':
            try:
                # Use -parse for syntax/lint-only analysis — skips elaboration and
                # linking so single-file checks don't produce spurious link errors
                # (Error-[LNK], unresolved references, etc.) from missing top-level.
                result = subprocess.run(
                    ['vcs', '-full64', '-sverilog', '-q', '+lint=all', '-parse', str(filepath)],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=filepath.parent
                )
                output = result.stderr + result.stdout
                import re
                for line in output.strip().split('\n'):
                    if not line.strip():
                        continue
                    # Skip link-phase errors — irrelevant for single-file lint
                    if re.search(r'Error-\[LNK\]|unresolved reference|cannot find|not found in|link error', line, re.IGNORECASE):
                        continue
                    # VCS error format: "filename", line N: error|warning: message
                    # or: Error-[XXX] Description
                    severity = "error"
                    if 'warning' in line.lower():
                        severity = "warning"
                    elif 'error' not in line.lower():
                        continue  # skip informational

                    line_num = 0
                    m = re.search(r'line\s+(\d+)', line)
                    if m:
                        line_num = int(m.group(1))

                    errors.append(LintError(
                        file=str(filepath),
                        line=line_num,
                        message=line.strip(),
                        severity=severity
                    ))
            except (subprocess.TimeoutExpired, Exception) as e:
                errors.append(LintError(
                    file=str(filepath),
                    line=0,
                    message=f"VCS linter error: {e}",
                    severity="error"
                ))
            return errors

        # iverilog fallback
        if tool == 'iverilog':
            try:
                result = subprocess.run(
                    ['iverilog', '-t', 'null', str(filepath)],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    cwd=filepath.parent  # Run in same directory for includes
                )

                if result.stderr:
                    # Parse iverilog errors
                    # Format: "file.v:10: error: syntax error"
                    # Format: "file.v:10: warning: something"
                    for line in result.stderr.strip().split('\n'):
                        if not line.strip():
                            continue

                        # Try to parse line number
                        if ':' in line:
                            parts = line.split(':', 3)
                            if len(parts) >= 3:
                                try:
                                    line_num = int(parts[1].strip())
                                    rest = ':'.join(parts[2:]).strip()

                                    # Determine severity
                                    severity = "error"
                                    if 'warning' in rest.lower():
                                        severity = "warning"
                                    elif 'sorry' in rest.lower():
                                        severity = "info"

                                    # Extract message
                                    msg = rest
                                    if 'error:' in msg.lower():
                                        msg = msg.split('error:', 1)[1].strip()
                                    elif 'warning:' in msg.lower():
                                        msg = msg.split('warning:', 1)[1].strip()

                                    errors.append(LintError(
                                        file=str(filepath),
                                        line=line_num,
                                        message=msg,
                                        severity=severity
                                    ))
                                except (ValueError, IndexError):
                                    # Couldn't parse, skip
                                    pass
            except (subprocess.TimeoutExpired, Exception) as e:
                errors.append(LintError(
                    file=str(filepath),
                    line=0,
                    message=f"Linter error: {e}",
                    severity="error"
                ))

        # verilator last resort
        elif tool == 'verilator':
            try:
                result = subprocess.run(
                    ['verilator', '--lint-only', str(filepath)],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if result.stderr or result.stdout:
                    output = result.stderr + result.stdout
                    # Parse verilator output (similar to iverilog)
                    for line in output.strip().split('\n'):
                        if 'Error:' in line or 'Warning:' in line:
                            errors.append(LintError(
                                file=str(filepath),
                                line=0,
                                message=line.strip(),
                                severity="error" if "Error:" in line else "warning"
                            ))
            except (subprocess.TimeoutExpired, Exception):
                pass

        return errors

    def check_syntax_only(self, filepath: str) -> bool:
        """
        Quick syntax-only check (no external tools).

        Returns:
            True if syntax is valid, False otherwise
        """
        filepath = Path(filepath)
        ext = filepath.suffix.lower()

        if ext == '.py':
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    compile(f.read(), str(filepath), 'exec')
                return True
            except SyntaxError:
                return False

        # For other languages, no built-in syntax check
        return True

    def format_errors(self, errors: List[LintError], max_errors: int = 10) -> str:
        """
        Format errors as human-readable string.

        Args:
            errors: List of LintError objects
            max_errors: Maximum number of errors to show

        Returns:
            Formatted error string
        """
        if not errors:
            return "✅ No errors found"

        # Group by severity
        by_severity = {"error": [], "warning": [], "info": []}
        for err in errors:
            by_severity[err.severity].append(err)

        lines = []

        # Show errors first
        if by_severity["error"]:
            limited = by_severity["error"][:max_errors]
            lines.append(f"❌ {len(by_severity['error'])} error(s):")
            for err in limited:
                lines.append(f"  {err}")

            if len(by_severity["error"]) > max_errors:
                remaining = len(by_severity["error"]) - max_errors
                lines.append(f"  ... and {remaining} more error(s)")

        # Then warnings
        if by_severity["warning"]:
            if lines:
                lines.append("")

            limited = by_severity["warning"][:max_errors]
            lines.append(f"⚠️  {len(by_severity['warning'])} warning(s):")
            for err in limited:
                lines.append(f"  {err}")

            if len(by_severity["warning"]) > max_errors:
                remaining = len(by_severity["warning"]) - max_errors
                lines.append(f"  ... and {remaining} more warning(s)")

        return "\n".join(lines)


# ============================================================
# Example Usage
# ============================================================

if __name__ == "__main__":
    linter = SimpleLinter()

    print(linter.get_available_tools_info())
    print()

    # Test Python file
    test_py = Path("test_lint.py")
    test_py.write_text("""
# Test Python file
def hello():
    print("Hello")
    x = undefined_var  # Error: undefined

def unused_function():  # Warning: unused
    pass
""")

    print(f"Checking {test_py}:")
    errors = linter.check_file(str(test_py))
    print(linter.format_errors(errors))
    print()

    # Test Verilog file (if iverilog available)
    if linter.is_available('verilog'):
        test_v = Path("test_lint.v")
        test_v.write_text("""
module test(
    input clk,
    output reg [7:0] count
);
    always @(posedge clk) begin
        count <= count + 1
    end  // Missing semicolon
endmodule
""")

        print(f"Checking {test_v}:")
        errors = linter.check_file(str(test_v))
        print(linter.format_errors(errors))
    else:
        print("⚠️  Verilog linting not available (iverilog not installed)")

    # Cleanup
    test_py.unlink(missing_ok=True)
    if linter.is_available('verilog'):
        Path("test_lint.v").unlink(missing_ok=True)
