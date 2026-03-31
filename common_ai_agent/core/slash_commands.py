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
                 aliases: Optional[List[str]] = None,
                 hidden: bool = False):
        """
        Register a slash command.

        Args:
            name: Command name (without /)
            handler: Function to handle the command
            description: Help text for the command
            aliases: Alternative names for the command
            hidden: If True, only shown with /help -v
        """
        self.commands[name] = {
            'handler': handler,
            'description': description,
            'aliases': aliases or [],
            'hidden': hidden,
        }

    def _register_builtin_commands(self):
        """Register built-in commands"""
        # --- Core commands (visible in /help) ---
        self.register('skills', self._cmd_skills,
                     '스킬 목록 및 상태 관리')

        self.register('plan', self._cmd_plan,
                     'Plan Mode — 계획 후 실행: /plan <task>')

        self.register('todo', self._cmd_todo,
                     'Todo 목록 보기/관리: /todo, /todo clear')

        self.register('context', self._cmd_context,
                     'Context 사용량 시각화: /context [-v|debug]')

        self.register('clear', self._cmd_clear,
                     '대화 기록 초기화: /clear, /clear <N>개 유지')

        self.register('compact', self._cmd_compact,
                     '요약 유지하며 기록 압축: /compact [--keep N]')

        self.register('git', self._cmd_git,
                     'Git 작업: /git diff, /git clear')

        self.register('model', self._cmd_model,
                     '모델 전환: /model 1|2|<name>, /model (현재)')

        self.register('help', self._cmd_help,
                     '커맨드 목록: /help, /help -v (전체)',
                     aliases=['h', '?'])

        self.register('man', self._cmd_man,
                     '상세 매뉴얼: /man plan, /man todo, /man guide ...')

        # --- Hidden commands (visible only in /help -v) ---
        self.register('compression', self._cmd_compression,
                     'Auto-compress when message count exceeds N: /compression 30, /compression 0 to disable',
                     hidden=True)

        self.register('window', self._cmd_window,
                     'Rolling context window: /window 10 (keep last N pairs), /window 0 to disable',
                     hidden=True)

        self.register('snapshot', self._cmd_snapshot,
                     'Save/restore conversation snapshots',
                     hidden=True)

        self.register('status', self._cmd_status,
                     'Show Common AI Agent status including version, model, and tools',
                     hidden=True)

        self.register('list', self._cmd_list,
                     'Quick list of all commands (TAB alternative)',
                     aliases=['ls'],
                     hidden=True)

        self.register('tools', self._cmd_tools,
                     'Show available tools and their status',
                     hidden=True)

        self.register('config', self._cmd_config,
                     'Show current configuration',
                     hidden=True)

        self.register('step', self._cmd_step,
                     'Toggle Step-by-Step execution mode (pause after each task)',
                     hidden=True)

        self.register('mode', self._cmd_mode,
                     'Switch agent mode: /mode normal to exit plan mode',
                     hidden=True)

    def _cmd_plan(self, args: str) -> str:
        """Enter plan mode."""
        return "AGENT_MODE:plan"

    def _cmd_git(self, args: str) -> str:
        """Git operations. /git clear or /git diff."""
        arg = args.strip().lower()
        if arg == 'clear':
            return "GIT_CLEAR"
        if arg == 'diff':
            return "GIT_DIFF"
        return "Usage: /git clear (to delete .git) or /git diff (to see changes)\n"

    def _cmd_todo(self, args: str) -> str:
        """Show/manage current todo list status."""
        try:
            import config
            from pathlib import Path
            import json
            todo_file = Path(config.TODO_FILE)

            # Handle /todo clear
            if args.strip().lower() == 'clear':
                if todo_file.exists():
                    todo_file.unlink()
                    return "✅ Todo list cleared.\n"
                return "No active todo list to clear.\n"

            parts = args.strip().split(maxsplit=2)
            subcmd = parts[0].lower() if parts else ''

            if subcmd == 'set':
                return self._todo_force_set(parts[1:], todo_file)
            if subcmd == 'remove':
                return self._todo_remove(parts[1:], todo_file)
            if subcmd == 'add':
                text = args.strip()[len('add'):].strip()
                return self._todo_add(text, todo_file)
            if subcmd == 'move':
                return self._todo_move(parts[1:], todo_file)
            if subcmd == 'goal':
                # /todo goal <N> <new text>
                rest = args.strip()[len('goal'):].strip().split(maxsplit=1)
                return self._todo_goal(rest, todo_file)

            if not todo_file.exists():
                # Check if there's a recent write failure to surface
                try:
                    import time as _time
                    error_file = Path(getattr(config, "TODO_ERROR_FILE", "current_todos_error.json"))
                    if error_file.exists():
                        err_data = json.loads(error_file.read_text(encoding="utf-8"))
                        err_msg = err_data.get("error", "")
                        ts = err_data.get("timestamp")
                        n = err_data.get("attempted_count", 0)
                        if err_msg:
                            age = int(_time.time() - ts) if ts else 0
                            age_str = f"{age}s ago" if age < 3600 else f"{age//3600}h ago"
                            return (
                                f"No active todo list.\n\n"
                                f"⚠️  Last todo_write failed ({age_str}, {n} task(s) attempted):\n"
                                f"   {err_msg}\n"
                            )
                except Exception:
                    pass
                return "No active todo list.\n"
            # Use TodoTracker's own premium formatting if possible
            try:
                from lib.todo_tracker import TodoTracker
                tracker = TodoTracker.load(todo_file)
                if tracker:
                    return tracker.format_progress()
            except ImportError:
                pass

            # Fallback if library not available
            data = json.loads(todo_file.read_text(encoding="utf-8"))
            todos = data.get("todos", [])
            if not todos:
                return "No active todo list.\n"
            icons = {"completed": "✅", "in_progress": "▶️", "pending": "⏸️"}
            lines = []
            for i, t in enumerate(todos):
                icon = icons.get(t.get("status", "pending"), "⏸️")
                lines.append(f"{icon} {i+1}. {t.get('content', '')}")
            return "\n".join(lines) + "\n"
        except Exception as e:
            return f"Error reading/managing todos: {e}\n"

    def _todo_force_set(self, parts: list, todo_file) -> str:
        """
        Force-set todo status, bypassing state machine validation.
        Usage: /todo set <N|all> <status>
        Valid statuses: pending, in_progress, completed, approved, rejected
        """
        VALID_STATUSES = {"pending", "in_progress", "completed", "approved", "rejected"}
        STATUS_ICONS = {
            "pending": "⏸️",
            "in_progress": "▶️",
            "completed": "✅",
            "approved": "✅✅",
            "rejected": "❌",
        }

        if len(parts) < 2:
            return (
                "Usage: /todo set <N|all> <status>\n"
                f"Valid statuses: {', '.join(sorted(VALID_STATUSES))}\n"
                "Examples:\n"
                "  /todo set 1 approved     — force approve task 1\n"
                "  /todo set 2 pending      — reset task 2 to pending\n"
                "  /todo set all pending    — reset all tasks to pending\n"
                "  /todo set all approved   — mark all tasks approved\n"
            )

        target = parts[0].lower()
        new_status = parts[1].lower()

        if new_status not in VALID_STATUSES:
            return f"❌ Invalid status: '{new_status}'\nValid: {', '.join(sorted(VALID_STATUSES))}\n"

        if not todo_file.exists():
            return "No active todo list.\n"

        try:
            from lib.todo_tracker import TodoTracker
            tracker = TodoTracker.load(todo_file)
            if not tracker or not tracker.todos:
                return "No todos found.\n"

            if target == 'all':
                changed = []
                for i, todo in enumerate(tracker.todos):
                    old = todo.status
                    todo.status = new_status
                    if new_status == 'approved':
                        import time as _time
                        if not todo.completed_at:
                            todo.completed_at = _time.time()
                        todo.rejection_reason = ""
                    elif new_status == 'pending':
                        todo.rejection_reason = ""
                    changed.append(f"  {STATUS_ICONS.get(new_status, '?')} {i+1}. {todo.content}  ({old} → {new_status})")
                tracker.current_index = -1
                tracker.stagnation_count = 0
                tracker.save()
                return f"Force-set ALL {len(tracker.todos)} tasks to '{new_status}':\n" + "\n".join(changed) + "\n"

            elif target.isdigit():
                idx = int(target) - 1  # 1-based → 0-based
                if not (0 <= idx < len(tracker.todos)):
                    return f"❌ Task {target} not found (total: {len(tracker.todos)})\n"

                old_status = tracker.todos[idx].status
                tracker.todos[idx].status = new_status

                if new_status == 'approved':
                    import time as _time
                    if not tracker.todos[idx].completed_at:
                        tracker.todos[idx].completed_at = _time.time()
                    tracker.todos[idx].rejection_reason = ""
                    # Auto-advance current_index to next pending
                    next_pending = None
                    for j, t in enumerate(tracker.todos):
                        if t.status == 'pending':
                            next_pending = j
                            break
                    tracker.current_index = next_pending if next_pending is not None else -1
                elif new_status == 'in_progress':
                    # Only one in_progress at a time
                    for j, t in enumerate(tracker.todos):
                        if j != idx and t.status == 'in_progress':
                            t.status = 'pending'
                    tracker.current_index = idx
                elif new_status == 'pending':
                    tracker.todos[idx].rejection_reason = ""
                    if tracker.current_index == idx:
                        tracker.current_index = -1

                tracker.save()
                icon = STATUS_ICONS.get(new_status, '?')
                return (
                    f"{icon} Task {int(target)} force-set: {old_status} → {new_status}\n"
                    f"   {tracker.todos[idx].content}\n\n"
                    + tracker.format_progress()
                )
            else:
                return f"❌ Invalid target: '{target}' — use a task number or 'all'\n"

        except Exception as e:
            return f"❌ Error: {e}\n"

    def _todo_remove(self, parts: list, todo_file) -> str:
        """Remove a todo item by index. /todo remove <N>"""
        if not parts or not parts[0].isdigit():
            return "Usage: /todo remove <N>\nExample: /todo remove 2\n"
        if not todo_file.exists():
            return "No active todo list.\n"
        try:
            from lib.todo_tracker import TodoTracker
            tracker = TodoTracker.load(todo_file)
            if not tracker or not tracker.todos:
                return "No todos found.\n"
            idx = int(parts[0]) - 1
            if not (0 <= idx < len(tracker.todos)):
                return f"❌ Task {parts[0]} not found (total: {len(tracker.todos)})\n"
            removed = tracker.todos.pop(idx)
            # Fix current_index
            if tracker.current_index == idx:
                tracker.current_index = -1
                # Find next in_progress or pending
                for i, t in enumerate(tracker.todos):
                    if t.status == 'in_progress':
                        tracker.current_index = i
                        break
            elif tracker.current_index > idx:
                tracker.current_index -= 1
            tracker.save()
            return f"🗑️  Removed task {int(parts[0])}: {removed.content}\n\n" + tracker.format_progress()
        except Exception as e:
            return f"❌ Error: {e}\n"

    def _todo_add(self, text: str, todo_file) -> str:
        """Add a new todo item. /todo add <text>"""
        if not text.strip():
            return "Usage: /todo add <task description>\nExample: /todo add Write unit tests\n"
        try:
            from lib.todo_tracker import TodoTracker, TodoItem
            import time as _time
            if todo_file.exists():
                tracker = TodoTracker.load(todo_file)
            else:
                tracker = TodoTracker(persist_path=todo_file)
            if tracker is None:
                tracker = TodoTracker(persist_path=todo_file)
            tracker.todos.append(TodoItem(
                content=text.strip(),
                active_form=text.strip(),
                status="pending",
                priority="medium",
            ))
            tracker.save()
            n = len(tracker.todos)
            return f"➕ Added task {n}: {text.strip()}\n\n" + tracker.format_progress()
        except Exception as e:
            return f"❌ Error: {e}\n"

    def _todo_move(self, parts: list, todo_file) -> str:
        """Move todo from position N to position M. /todo move <N> <M>"""
        if len(parts) < 2 or not parts[0].isdigit() or not parts[1].isdigit():
            return (
                "Usage: /todo move <N> <M>\n"
                "Example: /todo move 3 1  (move task 3 to position 1)\n"
            )
        if not todo_file.exists():
            return "No active todo list.\n"
        try:
            from lib.todo_tracker import TodoTracker
            tracker = TodoTracker.load(todo_file)
            if not tracker or not tracker.todos:
                return "No todos found.\n"
            src = int(parts[0]) - 1
            dst = int(parts[1]) - 1
            n = len(tracker.todos)
            if not (0 <= src < n):
                return f"❌ Task {parts[0]} not found (total: {n})\n"
            dst = max(0, min(dst, n - 1))
            item = tracker.todos.pop(src)
            tracker.todos.insert(dst, item)
            # Fix current_index after reorder
            tracker.current_index = -1
            for i, t in enumerate(tracker.todos):
                if t.status == 'in_progress':
                    tracker.current_index = i
                    break
            tracker.save()
            return (
                f"↕️  Moved task '{item.content}': position {int(parts[0])} → {dst + 1}\n\n"
                + tracker.format_progress()
            )
        except Exception as e:
            return f"❌ Error: {e}\n"

    def _todo_goal(self, parts: list, todo_file) -> str:
        """Change the content/goal of a todo item. /todo goal <N> <new text>"""
        if len(parts) < 2 or not parts[0].isdigit():
            return (
                "Usage: /todo goal <N> <new description>\n"
                "Example: /todo goal 2 Refactor auth module using JWT\n"
            )
        if not todo_file.exists():
            return "No active todo list.\n"
        try:
            from lib.todo_tracker import TodoTracker
            tracker = TodoTracker.load(todo_file)
            if not tracker or not tracker.todos:
                return "No todos found.\n"
            idx = int(parts[0]) - 1
            if not (0 <= idx < len(tracker.todos)):
                return f"❌ Task {parts[0]} not found (total: {len(tracker.todos)})\n"
            old_content = tracker.todos[idx].content
            tracker.todos[idx].content = parts[1].strip()
            tracker.todos[idx].active_form = parts[1].strip()
            tracker.save()
            return (
                f"✏️  Task {int(parts[0])} goal updated:\n"
                f"   Before: {old_content}\n"
                f"   After:  {parts[1].strip()}\n\n"
                + tracker.format_progress()
            )
        except Exception as e:
            return f"❌ Error: {e}\n"

    def _cmd_mode(self, args: str) -> str:
        """Switch agent mode. /mode normal to exit."""
        mode = args.strip().lower()
        if mode in ('plan', 'normal'):
            return f"AGENT_MODE:{mode}"
        return f"AGENT_MODE:normal"

    def _cmd_step(self, args: str) -> str:
        """Toggle Step-by-Step execution mode."""
        import config
        config.STEP_BY_STEP_MODE = not getattr(config, 'STEP_BY_STEP_MODE', False)
        status = "ON" if config.STEP_BY_STEP_MODE else "OFF"
        return f"STEP_MODE:{status}"

    def _cmd_skills(self, args: str) -> str:
        """Show available skills"""
        section = self._fmt_skills_section()
        if not section.strip():
            return "No skills loaded.\n"
        return section + "\n"

    def _format_full_context(self, tracker) -> str:
        """Format the full conversation history for verbose display."""
        if not hasattr(tracker, 'messages') or not tracker.messages:
            return "\n\033[33m[System] No message history available in context.\033[0m\n"

        from lib.display import Color
        
        lines = []
        lines.append("\n" + "=" * 60)
        lines.append(" 📄 Full Conversation Context")
        lines.append("=" * 60)

        for i, msg in enumerate(tracker.messages):
            role = msg.get("role", "unknown").upper()
            raw_content = msg.get("content", "")
            
            # Handle structured content (list of blocks, common in Anthropic caching)
            if isinstance(raw_content, list):
                content = []
                for block in raw_content:
                    if isinstance(block, dict):
                        if block.get("type") == "text":
                            content.append(block.get("text", ""))
                        elif block.get("type") == "tool_use":
                            content.append(f"[Tool Use: {block.get('name')}]")
                    else:
                        content.append(str(block))
                content = "\n".join(content).strip()
            elif isinstance(raw_content, dict):
                content = []
                if "static" in raw_content:
                    content.append(raw_content["static"])
                if "dynamic" in raw_content:
                    content.append(raw_content["dynamic"])
                content = "\n".join(content).strip()
            else:
                content = str(raw_content).strip()
            
            # Formatting based on role
            if role == "SYSTEM":
                role_fmt = f"\033[1;35m[{role}]\033[0m" # Magenta bold
            elif role == "USER":
                role_fmt = f"\033[1;32m[{role}]\033[0m" # Green bold
            elif role == "ASSISTANT":
                role_fmt = f"\033[1;36m[{role}]\033[0m" # Cyan bold
            else:
                role_fmt = f"[{role}]"

            # Optional turn ID and tokens
            turn_str = f" (turn {msg['turn_id']})" if "turn_id" in msg else ""
            token_str = ""
            if "_tokens" in msg:
                t = msg["_tokens"]
                count = t.get("completion_tokens", t.get("output_tokens", 0))
                if count > 0:
                    token_str = f" [{count} tokens]"

            lines.append(f"\n{role_fmt}{turn_str}{token_str}")
            
            # Print content with subtle indentation
            for line in content.splitlines():
                lines.append(f"  {line}")
            
            lines.append("\033[2m" + "-" * 40 + "\033[0m") # Dim separator

        lines.append("\n" + "=" * 60)
        return "\n".join(lines) + "\n"

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

            # --- VERBOSE MODE: Show full context ---
            if 'verbose' in args or '-v' in args:
                output += self._format_full_context(tracker)

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

    def _cmd_model(self, args: str) -> str:
        """Switch model. /model 1 (primary), /model 2 (secondary), /model <name>"""
        import sys
        _config = sys.modules.get('config') or sys.modules.get('src.config')
        if _config is None:
            import src.config as _config
        name = args.strip()
        if not name:
            marker1 = " ◀ active" if _config.MODEL_NAME == _config.PRIMARY_MODEL else ""
            marker2 = " ◀ active" if _config.MODEL_NAME == _config.SECONDARY_MODEL else ""
            return (
                f"Current model: {_config.MODEL_NAME}\n"
                f"  1: {_config.PRIMARY_MODEL}{marker1}\n"
                f"  2: {_config.SECONDARY_MODEL}{marker2}"
            )
        if name == "1":
            return "MODEL_SWITCH:1"
        if name == "2":
            return "MODEL_SWITCH:2"
        return f"MODEL_SWITCH:{name}"

    def _cmd_window(self, args: str) -> str:
        """Rolling context window. /window N — only last N message pairs sent to LLM each turn."""
        n = args.strip()
        if n.isdigit():
            return f"WINDOW_MODE:{n}"
        return "WINDOW_MODE:0"  # disable

    def _cmd_compression(self, args: str) -> str:
        """Auto-compress when non-system message count exceeds N. /compression 0 to disable."""
        n = args.strip()
        if n.isdigit():
            return f"COMPRESSION_MODE:{n}"
        return "COMPRESSION_MODE:0"  # disable

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
        """Show help. /help for core commands, /help -v for all."""
        verbose = args.strip() in ('-v', '--verbose', 'v')
        SEP = "=" * 60
        output = []

        if not verbose:
            # --- Core (brief) view ---
            output.append("\n" + SEP)
            output.append(" Common AI Agent")
            output.append(SEP)
            output.append("")
            for name, cmd in self.commands.items():
                if not cmd.get('hidden', False):
                    output.append(f"  /{name:<8} {cmd['description']}")
            output.append("")
            output.append(SEP)
            output.append("💡 /help -v 전체 커맨드  |  TAB 자동완성  |  /man guide 시작 가이드")
            output.append(SEP)
        else:
            # --- Verbose view: grouped ---
            output.append("\n" + SEP)
            output.append(" Common AI Agent — Full Command Reference")
            output.append(SEP)

            groups = [
                ("Context & History", ["context", "clear", "compact", "compression", "window", "snapshot"]),
                ("Agent & Mode",      ["plan", "mode", "step"]),
                ("Tools & Config",    ["model", "tools", "skills", "config", "status"]),
                ("Task Management",   ["todo", "git"]),
                ("Help",              ["help", "list", "man"]),
            ]
            listed = set()
            for group_name, names in groups:
                output.append(f"\n[{group_name}]")
                for name in names:
                    if name in self.commands:
                        cmd = self.commands[name]
                        aliases = f"  ({', '.join('/' + a for a in cmd['aliases'])})" if cmd['aliases'] else ""
                        output.append(f"  /{name:<14} {cmd['description']}{aliases}")
                        listed.add(name)
            # Any commands not in groups
            extras = [n for n in self.commands if n not in listed]
            if extras:
                output.append("\n[Other]")
                for name in sorted(extras):
                    cmd = self.commands[name]
                    output.append(f"  /{name:<14} {cmd['description']}")

            output.append("\n" + SEP)
            output.append("💡 /man <topic> 상세 매뉴얼  |  TAB 자동완성")
            output.append(SEP)

        return "\n".join(output)

    def _cmd_man(self, args: str) -> str:
        """Show detailed manual page for a topic."""
        from core.help_manual import get_man_page
        return get_man_page((args or "").strip().lower())

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
                "Sub-Agents": ["spawn_explore"]
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
