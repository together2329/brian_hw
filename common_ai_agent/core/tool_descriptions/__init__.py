"""
Tool Description Loader for Brian Coder

OpenCode-style tool descriptions with:
- Good/Bad examples
- Verilog-specific use cases
- Error recovery procedures
- Tool precedence guidelines
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from pathlib import Path
import os

@dataclass
class ToolDescription:
    """Tool description parsed from .txt file"""
    name: str
    description: str
    signature: str
    examples_good: List[str]
    examples_bad: List[str]
    when_to_use: List[str]
    when_not_to_use: List[str]
    error_recovery: List[str]
    see_also: List[str]
    verilog_specific: str  # Detailed section
    tool_precedence: str   # Always/Never guidelines

    def format_for_prompt(self, include_examples: bool = True) -> str:
        """Format as LLM-friendly prompt section"""
        parts = [
            f"## {self.name}",
            "",
            self.description,
            "",
            f"**Signature**: `{self.signature}`",
            ""
        ]

        if include_examples:
            if self.examples_good:
                parts.append("**Good Examples**:")
                for ex in self.examples_good:
                    parts.append(f"  ✅ {ex}")
                parts.append("")

            if self.examples_bad:
                parts.append("**Bad Examples**:")
                for ex in self.examples_bad:
                    parts.append(f"  ❌ {ex}")
                parts.append("")

        if self.tool_precedence:
            parts.append("**Tool Precedence**:")
            parts.append(self.tool_precedence)
            parts.append("")

        if self.verilog_specific:
            parts.append("**Verilog Use Cases**:")
            parts.append(self.verilog_specific)
            parts.append("")

        if self.error_recovery:
            parts.append("**Error Recovery**:")
            for err in self.error_recovery:
                parts.append(f"  - {err}")
            parts.append("")

        if self.see_also:
            parts.append("**See Also**: " + ", ".join(self.see_also))
            parts.append("")

        return "\n".join(parts)


class DescriptionLoader:
    """Singleton loader for tool descriptions"""

    _instance = None
    _cache: Dict[str, ToolDescription] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # Find tool_descriptions directory
        current_file = Path(__file__)
        self.base_dir = current_file.parent
        self.tools_dir = self.base_dir / "tools"

        self._initialized = True

    def load_tool_description(self, tool_name: str) -> Optional[ToolDescription]:
        """Load tool description from .txt file"""
        if tool_name in self._cache:
            return self._cache[tool_name]

        txt_path = self.tools_dir / f"{tool_name}.txt"

        if not txt_path.exists():
            return None

        # Parse .txt file
        desc = self._parse_txt_file(txt_path, tool_name)
        self._cache[tool_name] = desc
        return desc

        return self._cache[tool_name]

    def load_agent_guide(self, guide_name: str) -> str:
        """Load agent guide text from agents directory"""
        guide_path = self.base_dir / "agents" / f"{guide_name}.txt"
        
        if not guide_path.exists():
            return ""
            
        return guide_path.read_text(encoding='utf-8')

    def _parse_txt_file(self, path: Path, tool_name: str) -> ToolDescription:
        """Parse tool description .txt file"""
        content = path.read_text(encoding='utf-8')

        # Parse sections using simple marker-based parsing
        sections = {
            'description': '',
            'signature': '',
            'examples_good': [],
            'examples_bad': [],
            'when_to_use': [],
            'when_not_to_use': [],
            'error_recovery': [],
            'see_also': [],
            'verilog_specific': '',
            'tool_precedence': ''
        }

        current_section = None
        lines = content.split('\n')

        for line in lines:
            line_lower = line.lower().strip()

            # Section markers
            if line_lower.startswith('## signature'):
                current_section = 'signature'
                continue
            elif line_lower.startswith('## description'):
                current_section = 'description'
                continue
            elif line_lower.startswith('## good examples'):
                current_section = 'examples_good'
                continue
            elif line_lower.startswith('## bad examples'):
                current_section = 'examples_bad'
                continue
            elif line_lower.startswith('## when to use'):
                current_section = 'when_to_use'
                continue
            elif line_lower.startswith('## when not to use'):
                current_section = 'when_not_to_use'
                continue
            elif line_lower.startswith('## error recovery'):
                current_section = 'error_recovery'
                continue
            elif line_lower.startswith('## see also'):
                current_section = 'see_also'
                continue
            elif line_lower.startswith('## verilog'):
                current_section = 'verilog_specific'
                continue
            elif line_lower.startswith('## tool precedence'):
                current_section = 'tool_precedence'
                continue
            elif line.startswith('# Tool:'):
                # Skip header
                continue

            # Content parsing
            if current_section:
                if current_section in ['examples_good', 'examples_bad', 'when_to_use',
                                       'when_not_to_use', 'error_recovery', 'see_also']:
                    # List items
                    if line.strip().startswith(('✅', '❌', '-', '*')):
                        cleaned = line.strip().lstrip('✅❌-*').strip()
                        if cleaned:
                            sections[current_section].append(cleaned)
                else:
                    # Text sections
                    if line.strip():
                        if sections[current_section]:
                            sections[current_section] += '\n' + line
                        else:
                            sections[current_section] = line

        return ToolDescription(
            name=tool_name,
            description=sections['description'].strip(),
            signature=sections['signature'].strip(),
            examples_good=sections['examples_good'],
            examples_bad=sections['examples_bad'],
            when_to_use=sections['when_to_use'],
            when_not_to_use=sections['when_not_to_use'],
            error_recovery=sections['error_recovery'],
            see_also=sections['see_also'],
            verilog_specific=sections['verilog_specific'].strip(),
            tool_precedence=sections['tool_precedence'].strip()
        )

    def get_all_tool_names(self) -> List[str]:
        """Get list of all tools with descriptions"""
        if not self.tools_dir.exists():
            return []

        return [f.stem for f in self.tools_dir.glob("*.txt")]


# Singleton accessor
_loader_instance = None

def get_loader() -> DescriptionLoader:
    """Get singleton DescriptionLoader instance"""
    global _loader_instance
    if _loader_instance is None:
        _loader_instance = DescriptionLoader()
    return _loader_instance


def format_tool_for_prompt(tool_name: str, include_examples: bool = True) -> str:
    """
    Format tool description for LLM prompt

    Args:
        tool_name: Name of the tool
        include_examples: Include good/bad examples

    Returns:
        Formatted string ready for system prompt
    """
    loader = get_loader()
    desc = loader.load_tool_description(tool_name)

    if desc is None:
        return f"## {tool_name}\n(No detailed description available)\n"

    return desc.format_for_prompt(include_examples=include_examples)
