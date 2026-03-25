"""
Slash Command System (Zero-Dependency)

Claude Code style slash commands with readline autocomplete.
Uses Python standard library only.

Available commands:
- /context  : Visualize token usage
- /clear    : Clear conversation history
- /compact  : Clear history but keep summary
- /status   : Show system status
- /help     : Show available commands
"""

import sys
import os
from pathlib import Path
from typing import Callable, Optional, Any, List

# Emoji support: disabled on Linux unless explicitly enabled
_USE_EMOJI = sys.platform != 'linux' and os.environ.get('NO_EMOJI', '').lower() not in ('1', 'true', 'yes')

def _icon(emoji: str, fallback: str) -> str:
    return emoji if _USE_EMOJI else fallback

try:
    import readline
except ImportError:
    try:
        import pyreadline3 as readline  # Windows fallback
    except ImportError:
        readline = None  # No autocomplete, but still works


class SlashCommandRegistry:
    """
    Slash command registry with autocomplete support.

    Zero-dependency implementation using only Python standard library.
    """

    def __init__(self):
        self.commands = {}
        self._history_file = os.path.expanduser("~/.common_ai_agent_history")
        self._register_builtin_commands()
        self._setup_readline()

    def _setup_readline(self):
        """Setup readline for autocomplete and history"""
        if not readline:
            return

        # Load command history
        if os.path.exists(self._history_file):
            try:
                readline.read_history_file(self._history_file)
            except:
                pass

        # Set history size
        readline.set_history_length(1000)

        # Setup autocomplete
        readline.set_completer(self._completer)

        # Try both GNU readline and libedit (macOS) syntax
        try:
            # GNU readline
            readline.parse_and_bind("tab: complete")
        except:
            try:
                # libedit (macOS default)
                readline.parse_and_bind("bind ^I rl_complete")
            except:
                # Fallback: just set the completer without binding
                pass

        # Use delimiters that don't include '/'
        readline.set_completer_delims(' \t\n')

    def save_history(self):
        """Save command history to file"""
        if not readline:
            return
        try:
            readline.write_history_file(self._history_file)
        except:
            pass

    def _completer(self, text: str, state: int) -> Optional[str]:
        """
        Readline completer function.

        Args:
            text: Current text being completed
            state: Completion index (0, 1, 2, ...)

        Returns:
            Completion option or None
        """
        if text.startswith('/'):
            # Slash command completion
            options = [cmd for cmd in self.get_completions()
                      if cmd.startswith(text)]
        else:
            # No completion for regular text
            options = []

        if state < len(options):
            return options[state]
        return None

    def register(self,
                 name: str,
                 handler: Callable[[str], Any],
                 description: str,
                 aliases: Optional[List[str]] = None):
        """
        Register a slash command.

        Args:
            name: Command name (without /)
            handler: Function to handle the command
            description: Help text for the command
            aliases: Alternative names for the command
        """
        self.commands[name] = {
            'handler': handler,
            'description': description,
            'aliases': aliases or []
        }

    def _register_builtin_commands(self):
        """Register built-in commands"""
        self.register('context', self._cmd_context,
                     'Visualize current context usage as a colored grid')

        self.register('clear', self._cmd_clear,
                     'Clear conversation history and free up context')

        self.register('compact', self._cmd_compact,
                     'Clear conversation history but keep a summary in context')

        self.register('plan', self._cmd_plan,
                     'Enter interactive plan mode (/plan <task>)')

        self.register('status', self._cmd_status,
                     'Show Common AI Agent status including version, model, and tools')

        self.register('help', self._cmd_help,
                     'Show available commands',
                     aliases=['h', '?'])

        self.register('list', self._cmd_list,
                     'Quick list of all commands (TAB alternative)',
                     aliases=['ls'])

        self.register('tools', self._cmd_tools,
                     'Show available tools and their status')

        self.register('config', self._cmd_config,
                     'Show current configuration')

        self.register('snapshot', self._cmd_snapshot,
                     'Save/restore conversation snapshots')

        self.register('skills', self._cmd_skills,
                     'Show available skills and their activation status')

    def _cmd_skills(self, args: str) -> str:
        """Show available skills"""
        section = self._fmt_skills_section()
        if not section.strip():
            return "No skills loaded.\n"
        return section + "\n"

    def _cmd_plan(self, args: str) -> str:
        """Enter interactive Plan Mode"""
        task = args.strip()
        if not task:
            return "❌ Error: /plan requires a task description\nUsage: /plan <task>"
        return f"PLAN_MODE_REQUEST:{task}"

    def _cmd_context(self, args: str) -> str:
        """Visualize context usage"""
        try:
            # Get actual token counts from context tracker
            import config
            import sys
            # Import llm_client from the right location
            if 'llm_client' in sys.modules:
                llm_client = sys.modules['llm_client']
            else:
                from src import llm_client

            from core.context_tracker import get_tracker

            tracker = get_tracker()
            model_name = config.MODEL_NAME

            # Get actual token count from last API call
            actual_total = llm_client.last_input_tokens if llm_client.last_input_tokens > 0 else None

            # Debug output
            debug_lines = []
            if args.strip() == "debug":
                debug_lines.append("\n=== DEBUG INFO ===")
                debug_lines.append(f"  llm_client.last_input_tokens: {llm_client.last_input_tokens:,}")
                debug_lines.append(f"  actual_total: {actual_total:,}" if actual_total else f"  actual_total: None")
                debug_lines.append(f"  tracker.system_prompt_tokens: {tracker.system_prompt_tokens:,}")
                debug_lines.append(f"  tracker.messages_tokens: {tracker.messages_tokens:,}")

                # Message stats
                if hasattr(tracker, '_message_stats'):
                    stats = tracker._message_stats
                    debug_lines.append(f"  message_stats:")
                    debug_lines.append(f"    total_messages: {stats.get('total_messages', 0)}")
                    debug_lines.append(f"    with_actual_tokens: {stats.get('with_actual_tokens', 0)}")
                    debug_lines.append(f"    with_estimated_tokens: {stats.get('with_estimated_tokens', 0)}")
                    debug_lines.append(f"    assistant_messages: {stats.get('assistant_messages', 0)}")
                    debug_lines.append(f"    assistant_with_actual: {stats.get('assistant_with_actual', 0)}")

                # Actual percentage (based on assistant messages only)
                actual_pct = getattr(tracker, 'actual_percentage', 0)
                debug_lines.append(f"  actual_percentage (assistant only): {actual_pct:.1f}%")
                debug_lines.append(f"  will_use_saved_tokens: {actual_pct >= 50.0}")

                debug_lines.append(f"  config.MAX_CONTEXT_CHARS: {config.MAX_CONTEXT_CHARS:,}")
                debug_lines.append(f"  tracker.max_tokens: {tracker.max_tokens:,}")
                debug_lines.append("==================\n")

            # Generate Claude Code style visualization
            output = tracker.visualize(model_name, actual_total=actual_total)

            # Add debug info if requested
            if debug_lines:
                output = "".join(debug_lines) + output

            # Add Rules section (.UPD_RULE.md)
            output += self._fmt_rules_section()

            # Add Skills section
            output += self._fmt_skills_section()

            # Tips (emoji-safe)
            tip = _icon("💡", "[i]")
            output += f"\n{tip} Tip: Use /clear to free up context"
            output += f"\n{tip} Tip: Use /compact to summarize old messages"
            output += f"\n{tip} Tip: Use /context debug for detailed info\n"

            return output
        except Exception as e:
            import traceback
            return f"Error getting context info: {e}\n{traceback.format_exc()}"

    def _fmt_rules_section(self) -> str:
        """Load and format .UPD_RULE.md files (global + project)."""
        rule_paths = [
            Path.home() / ".common_ai_agent" / ".UPD_RULE.md",   # global
            Path(__file__).parent.parent / ".UPD_RULE.md",         # project (core/../)
            Path.cwd() / ".UPD_RULE.md",                           # cwd fallback
        ]
        found = [(p, p.read_text(encoding="utf-8").strip()) for p in rule_paths if p.exists()]
        if not found:
            return ""

        lines = ["\n Rules · .UPD_RULE.md"]
        for path, content in found:
            scope = "global" if path.parent != Path.cwd() else "project"
            lines.append(f" \033[2m[{scope}]\033[0m")
            for line in content.splitlines():
                line = line.strip()
                if line and not line.startswith("#") and not line.startswith("<!--"):
                    lines.append(f" \033[2m└ {line[:80]}\033[0m")
        return "\n".join(lines) + "\n"

    def _fmt_skills_section(self) -> str:
        """Load and format available skills."""
        try:
            from core.skill_system import get_skill_registry
            registry = get_skill_registry()
            skills = registry.get_skills_by_priority()
            if not skills:
                return ""

            lines = ["\n Skills · /skills"]
            for skill in skills:
                spoke = f"  +{len(skill.spoke_files)} refs" if skill.spoke_files else ""
                lines.append(f" \033[2m└ {skill.name} (priority: {skill.priority}){spoke}\033[0m")
            return "\n".join(lines) + "\n"
        except Exception:
            return ""

    def _cmd_clear(self, args: str) -> str:
        """Clear conversation history. /clear [N] keeps last N user/assistant message pairs."""
        keep = args.strip()
        if keep.isdigit():
            return f"CLEAR_HISTORY:{keep}"
        return "CLEAR_HISTORY"  # Special signal for main loop

    def _cmd_compact(self, args: str) -> str:
        """
        Compact conversation with optional instructions

        Usage:
            /compact                    # Default (keep 4 recent)
            /compact --keep 10          # Keep 10 recent messages
            /compact --dry-run          # Preview without saving
            /compact custom instruction # Custom summarization prompt
        """
        if not args.strip():
            return "COMPACT_HISTORY"

        # Parse options
        import re

        # --keep N option
        keep_match = re.search(r'--keep\s+(\d+)', args)
        if keep_match:
            keep_count = int(keep_match.group(1))
            return f"COMPACT_HISTORY:keep={keep_count}"

        # --dry-run option
        if "--dry-run" in args:
            return "COMPACT_HISTORY:dry_run=true"

        # Otherwise: custom instruction
        return f"COMPACT_HISTORY:{args.strip()}"

    def _cmd_status(self, args: str) -> str:
        """Show system status"""
        try:
            import config
            from core.simple_linter import SimpleLinter

            output = []
            output.append("\n" + "=" * 60)
            output.append("🤖 Common AI Agent Status")
            output.append("=" * 60)

            # Model info
            output.append("\n📡 LLM Configuration:")
            output.append(f"  • Model: {config.MODEL_NAME}")
            output.append(f"  • API: {config.BASE_URL}")
            output.append(f"  • Timeout: {config.API_TIMEOUT}s")

            # Features
            output.append("\n⚡ Features:")
            output.append(f"  • Type Validation: {'✅' if config.ENABLE_TYPE_VALIDATION else '❌'}")
            output.append(f"  • Linting: {'✅' if config.ENABLE_LINTING else '❌'}")
            output.append(f"  • Smart RAG: {'✅' if config.ENABLE_SMART_RAG else '❌'}")
            output.append(f"  • Memory System: {'✅' if config.ENABLE_MEMORY else '❌'}")
            output.append(f"  • Skill System: {'✅' if config.ENABLE_SKILL_SYSTEM else '❌'}")
            output.append(f"  • Sub-Agents: {'✅' if config.ENABLE_SUB_AGENTS else '❌'}")

            # Linter tools
            output.append("\n🔧 Linting Tools:")
            linter = SimpleLinter()
            for line in linter.get_available_tools_info().split('\n'):
                if line.strip():
                    output.append(f"  {line}")

            # Working directory
            output.append(f"\n📁 Working Directory:")
            output.append(f"  • {os.getcwd()}")

            output.append("=" * 60)

            return "\n".join(output)
        except Exception as e:
            return f"Error getting status: {e}"

    def _cmd_help(self, args: str) -> str:
        """Show help for all commands"""
        output = []
        output.append("\n" + "=" * 60)
        output.append("Available Slash Commands")
        output.append("=" * 60)

        # Sort commands
        for name in sorted(self.commands.keys()):
            cmd = self.commands[name]
            aliases = f" ({', '.join('/' + a for a in cmd['aliases'])})" if cmd['aliases'] else ""
            output.append(f"\n  /{name:<12} {cmd['description']}{aliases}")

        output.append("\n" + "=" * 60)
        output.append("💡 Tip: Press TAB to autocomplete commands")
        output.append("💡 TAB이 안 되면: /? 로 이 목록 다시 보기")
        output.append("=" * 60)

        return "\n".join(output)

    def _cmd_list(self, args: str) -> str:
        """Quick command list (alternative to TAB)"""
        commands = sorted(self.get_completions())
        return "Available: " + " ".join(commands)

    def _cmd_tools(self, args: str) -> str:
        """Show available tools"""
        try:
            from core.tools import AVAILABLE_TOOLS

            output = []
            output.append("\n" + "=" * 60)
            output.append("Available Tools")
            output.append("=" * 60)

            # Group tools by category
            categories = {
                "File Operations": ["read_file", "write_file", "list_dir"],
                "Search & Navigation": ["grep_file", "read_lines", "find_files"],
                "File Editing": ["replace_in_file", "replace_lines"],
                "Git": ["git_status", "git_diff"],
                "RAG": ["rag_search", "rag_index", "rag_status", "rag_explore", "rag_clear"],
                "Verilog": [
                    "analyze_verilog_module", "find_signal_usage",
                    "find_module_definition", "extract_module_hierarchy"
                ],
                "Commands": ["run_command"],
                "Sub-Agents": ["spawn_explore", "spawn_plan"]
            }

            for category, tools in categories.items():
                available = [t for t in tools if t in AVAILABLE_TOOLS]
                if available:
                    output.append(f"\n📦 {category}:")
                    for tool in available:
                        output.append(f"  • {tool}")

            output.append(f"\n✅ Total: {len(AVAILABLE_TOOLS)} tools")
            output.append("=" * 60)

            return "\n".join(output)
        except Exception as e:
            return f"Error listing tools: {e}"

    def _cmd_config(self, args: str) -> str:
        """Show current configuration"""
        try:
            import config

            output = []
            output.append("\n" + "=" * 60)
            output.append("⚙️  Configuration")
            output.append("=" * 60)

            # Key settings
            settings = {
                "LLM": {
                    "MODEL_NAME": config.MODEL_NAME,
                    "BASE_URL": config.BASE_URL,
                    "API_TIMEOUT": config.API_TIMEOUT,
                    "MAX_ITERATIONS": config.MAX_ITERATIONS,
                },
                "Features": {
                    "ENABLE_TYPE_VALIDATION": config.ENABLE_TYPE_VALIDATION,
                    "ENABLE_LINTING": config.ENABLE_LINTING,
                    "ENABLE_SMART_RAG": config.ENABLE_SMART_RAG,
                    "ENABLE_MEMORY": config.ENABLE_MEMORY,
                    "ENABLE_SKILL_SYSTEM": config.ENABLE_SKILL_SYSTEM,
                },
                "Performance": {
                    "RATE_LIMIT_DELAY": config.RATE_LIMIT_DELAY,
                    "REACT_MAX_WORKERS": config.REACT_MAX_WORKERS,
                    "ENABLE_REACT_PARALLEL": config.ENABLE_REACT_PARALLEL,
                }
            }

            for section, items in settings.items():
                output.append(f"\n{section}:")
                for key, value in items.items():
                    output.append(f"  • {key}: {value}")

            output.append("\n" + "=" * 60)
            output.append("💡 Edit ~/.common_ai_agent/.config to change settings")
            output.append("=" * 60)

            return "\n".join(output)
        except Exception as e:
            return f"Error loading config: {e}"

    def _cmd_snapshot(self, args: str) -> str:
        """
        Save/restore conversation snapshots

        Usage:
            /snapshot save [name]    # Save current conversation
            /snapshot load <name>    # Restore from snapshot
            /snapshot list           # List all snapshots
            /snapshot delete <name>  # Delete a snapshot
        """
        from core.session_snapshot import save_snapshot, load_snapshot, list_snapshots, delete_snapshot

        parts = args.strip().split(maxsplit=1)
        action = parts[0] if parts else "list"

        if action == "save":
            name = parts[1] if len(parts) > 1 else None
            return f"SNAPSHOT_SAVE:{name or ''}"

        elif action == "load":
            if len(parts) < 2:
                return "❌ Error: /snapshot load <name>"
            return f"SNAPSHOT_LOAD:{parts[1]}"

        elif action == "delete":
            if len(parts) < 2:
                return "❌ Error: /snapshot delete <name>"
            return f"SNAPSHOT_DELETE:{parts[1]}"

        elif action == "list":
            snapshots = list_snapshots()
            if snapshots:
                output = "\n📸 Available Snapshots:\n"
                for s in snapshots:
                    output += f"  • {s}\n"
                output += "\n💡 Use '/snapshot load <name>' to restore"
                return output
            else:
                return "📸 No snapshots found.\n💡 Use '/snapshot save <name>' to create one."

        else:
            return f"❌ Unknown action: {action}\nUsage: /snapshot [save|load|list|delete]"

    def execute(self, command_line: str) -> Optional[str]:
        """
        Execute a slash command.

        Args:
            command_line: Full command line (e.g., "/help" or "/compact summary")

        Returns:
            Command output or None if not a command
        """
        if not command_line.startswith('/'):
            return None

        # Parse command
        parts = command_line[1:].split(maxsplit=1)
        if not parts:
            return "Empty command. Type /help for available commands."

        cmd_name = parts[0]
        args = parts[1] if len(parts) > 1 else ""

        # Find command (including aliases)
        handler = None
        for name, cmd in self.commands.items():
            if cmd_name == name or cmd_name in cmd.get('aliases', []):
                handler = cmd['handler']
                break

        if not handler:
            return f"❌ Unknown command: /{cmd_name}\n💡 Type /help for available commands"

        try:
            return handler(args)
        except Exception as e:
            return f"❌ Error executing /{cmd_name}: {e}"

    def get_completions(self) -> List[str]:
        """Get list of all command completions"""
        completions = []
        for name, cmd in self.commands.items():
            completions.append(f"/{name}")
            for alias in cmd.get('aliases', []):
                completions.append(f"/{alias}")
        return sorted(completions)

    def is_command(self, text: str) -> bool:
        """Check if text is a slash command"""
        return text.startswith('/')


# Global registry instance
_registry = None

def get_registry() -> SlashCommandRegistry:
    """Get global slash command registry"""
    global _registry
    if _registry is None:
        _registry = SlashCommandRegistry()
    return _registry


# ============================================================
# Example Usage
# ============================================================

if __name__ == "__main__":
    # Test commands
    registry = get_registry()

    print("=" * 60)
    print("Slash Command System Test")
    print("=" * 60)

    # Test each command
    commands = [
        "/help",
        "/status",
        "/context",
        "/tools",
        "/config",
        "/unknown",  # Should show error
    ]

    for cmd in commands:
        print(f"\n>>> {cmd}")
        result = registry.execute(cmd)
        if result:
            print(result)

    # Test autocomplete
    print("\n" + "=" * 60)
    print("Autocomplete Test")
    print("=" * 60)
    print("Available completions:", registry.get_completions())
