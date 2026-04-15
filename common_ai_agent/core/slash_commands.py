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


# ── Session tree helpers ─────────────────────────────────────────────────────

def _fmt_size(n: int) -> str:
    """Human-readable file size."""
    if n < 1024:
        return f"{n}B"
    if n < 1024 * 1024:
        return f"{n/1024:.1f}KB"
    return f"{n/(1024*1024):.1f}MB"


# Map well-known filenames to brief descriptions
_FILE_DESCRIPTIONS = {
    "conversation.json":      "← main agent 대화",
    "full_conversation.json":  "← append-only 원본",
    "input_history.txt":       "← ↑↓ history",
    "todo.json":               "← main agent todo",
    "todo_error.json":         "← todo error backup",
    "result.json":             "← {status, output, iterations, …}",
    "status.json":             "← job status",
    "output.txt":              "← job output",
    "error.txt":               "← job error",
    "project.json":            "← job recipe (fixed flow)",
}


def _file_description(name: str) -> str:
    """Return a short description for well-known session files."""
    return _FILE_DESCRIPTIONS.get(name, "")

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
                 hidden: bool = False,
                 usage: Optional[str] = None):
        """
        Register a slash command.

        Args:
            name: Command name (without /)
            handler: Function to handle the command
            description: Help text for the command
            aliases: Alternative names for the command
            hidden: If True, only shown with /help -v
            usage: Usage string shown in /help (defaults to /<name>)
        """
        self.commands[name] = {
            'handler': handler,
            'description': description,
            'aliases': aliases or [],
            'hidden': hidden,
            'usage': usage or f"/{name}",
        }

    def unregister(self, name: str):
        """Remove a slash command by name (safe no-op if not registered)."""
        self.commands.pop(name, None)

    def unregister_many(self, names: list):
        """Remove multiple slash commands by name."""
        for n in names:
            self.commands.pop(n, None)

    def _register_builtin_commands(self):
        """Register built-in commands"""
        # --- Core commands (visible in /help) ---
        self.register('skills', self._cmd_skills,
                     '스킬 목록 및 상태 관리')

        self.register('plan', self._cmd_plan,
                     'Plan Mode — 계획 후 실행: /plan <task>')

        self.register('make', self._cmd_make,
                     '대화 기반 자동 생성: /make todo')

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

        self.register('guide', lambda _: self._cmd_man('guide'),
                     '시작 가이드 (= /man guide)',
                     hidden=True)

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

        self.register('workflow', self._cmd_workspace,
                     '워크플로우 전환: /workflow <name> | /workflow (현재)',
                     aliases=['wf'])

        self.register('project', self._cmd_project,
                     'Project management: /project | /project <name> | /project create <name> | /project delete <name>')

        self.register('job', self._cmd_job,
                     'Job management: /job | /job <id> | /job output <id> | /job context <id> | /job cancel <id>')

        self.register('session', self._cmd_session,
                     'Session layout: /session | /session tree | /session tree <project>',
                     aliases=['ss'])

        self.register('converge', self._cmd_converge,
                     'Converge loop: /converge start <module> | /converge status | /converge history | /converge report',
                     aliases=['cv'])

    def _cmd_session(self, args: str) -> str:
        """Show .session/ hierarchy tree or project layout summary.

        /session          → show active project summary (path, files, size)
        /session tree     → full .session/ directory tree across all projects
        /session tree X   → tree for specific project X
        """
        from pathlib import Path
        import config as _cfg

        parts = args.strip().split()
        session_root = Path.cwd() / '.session'

        # Sub-command: tree
        if parts and parts[0].lower() == 'tree':
            project_name = parts[1] if len(parts) > 1 else None
            return self._render_tree(session_root, project_name, _cfg)

        # Default: show active project layout summary
        active = getattr(_cfg, 'ACTIVE_PROJECT', 'default')
        session_dir = session_root / active
        if not session_dir.is_dir():
            return f"Session directory not found: {session_dir}"

        lines = [f"📂 Project: {active}", f"   Path: {session_dir}", ""]

        # Root files
        root_files = sorted([f for f in session_dir.iterdir()
                             if f.is_file() and not f.name.startswith('.')])
        hidden_files = sorted([f for f in session_dir.iterdir()
                               if f.is_file() and f.name.startswith('.')])
        total_size = 0

        for f in root_files:
            sz = f.stat().st_size
            total_size += sz
            sz_str = _fmt_size(sz)
            desc = _file_description(f.name)
            lines.append(f"   {f.name:30s} {sz_str:>8s}  {desc}")

        if hidden_files:
            lines.append(f"   {'(hidden):':30s}")
            for f in hidden_files:
                sz = f.stat().st_size
                total_size += sz
                lines.append(f"     {f.name:28s} {_fmt_size(sz):>8s}")

        # Jobs
        jobs_dir = session_dir / 'jobs'
        if jobs_dir.is_dir():
            job_dirs = sorted([d for d in jobs_dir.iterdir()
                               if d.is_dir() and d.name.startswith('job')])
            counter_file = jobs_dir / '.counter'
            counter_str = ""
            if counter_file.exists():
                counter_str = f' ← "{counter_file.read_text().strip()}"'
            lines.append(f"")
            lines.append(f"   jobs/")
            if counter_file.exists():
                lines.append(f"   ├── .counter{counter_str}")
            for i, jd in enumerate(job_dirs):
                connector = "└──" if i == len(job_dirs) - 1 else "├──"
                jfiles = sorted([f for f in jd.iterdir() if f.is_file()])
                jsize = sum(f.stat().st_size for f in jfiles)
                lines.append(f"   {connector} {jd.name}/ ({len(jfiles)} files, {_fmt_size(jsize)})")
                # Show result.json status if present
                result_file = jd / 'result.json'
                if result_file.exists():
                    try:
                        import json
                        rdata = json.loads(result_file.read_text(encoding='utf-8'))
                        status = rdata.get('status', '?')
                        agent = rdata.get('agent_name', '')
                        icon = {"completed": "✅", "failed": "❌", "cancelled": "⛔"}.get(status, "📋")
                        lines.append(f"   │   {icon} status={status}  agent={agent}")
                    except Exception:
                        pass

        size_str = _fmt_size(total_size)
        lines.append(f"\n   Total: {size_str}")
        return "\n".join(lines)

    def _render_tree(self, session_root: 'Path', project_name: Optional[str], _cfg) -> str:
        """Render an ASCII tree of .session/ directory structure."""
        if not session_root.is_dir():
            return f"No .session/ directory found at {session_root}"

        lines = [f".session/"]

        project_dirs = sorted([d for d in session_root.iterdir() if d.is_dir()])
        active = getattr(_cfg, 'ACTIVE_PROJECT', 'default')

        if project_name:
            # Specific project
            target = session_root / project_name
            if not target.is_dir():
                return f"Project '{project_name}' not found."
            project_dirs = [target]

        for pi, pd in enumerate(project_dirs):
            p_connector = "└──" if pi == len(project_dirs) - 1 else "├──"
            p_prefix    = "    " if pi == len(project_dirs) - 1 else "│   "
            marker = " ◀ active" if pd.name == active else ""
            lines.append(f"{p_connector} {pd.name}/{marker}")

            # Collect items: root files + jobs dir
            root_files = sorted([f for f in pd.iterdir()
                                 if f.is_file() and not f.name.startswith('.')])
            hidden_files = sorted([f for f in pd.iterdir()
                                   if f.is_file() and f.name.startswith('.')])
            jobs_dir = pd / 'jobs'
            items = []  # (name, type, extra_info)

            for f in root_files:
                sz = f.stat().st_size
                desc = _file_description(f.name)
                items.append((f.name, 'file', f"{_fmt_size(sz):>7s}  {desc}"))

            if hidden_files:
                for f in hidden_files:
                    sz = f.stat().st_size
                    items.append((f.name, 'hidden', f"{_fmt_size(sz):>7s}"))

            jobs = []
            if jobs_dir.is_dir():
                counter_file = jobs_dir / '.counter'
                if counter_file.exists():
                    val = counter_file.read_text().strip()
                    items.append(('.counter', 'file', f'← "{val}"'))
                job_dirs = sorted([d for d in jobs_dir.iterdir()
                                   if d.is_dir() and d.name.startswith('job')])
                for jd in job_dirs:
                    jfiles = sorted([f for f in jd.iterdir() if f.is_file()])
                    jsize = sum(f.stat().st_size for f in jfiles)
                    # Get result status
                    result_info = ""
                    result_file = jd / 'result.json'
                    if result_file.exists():
                        try:
                            import json
                            rdata = json.loads(result_file.read_text(encoding='utf-8'))
                            st = rdata.get('status', '?')
                            icon = {"completed": "✅", "failed": "❌", "cancelled": "⛔"}.get(st, "📋")
                            result_info = f"  {icon} {st}"
                        except Exception:
                            pass
                    jobs.append((jd.name, jfiles, _fmt_size(jsize), result_info))

            all_items = items + [('jobs/', 'dir', '')] if jobs else items + ([] if not jobs_dir.is_dir() else [])
            # Build: files first, then jobs dir
            n_items = len(items)
            has_jobs = len(jobs) > 0
            total_visual = n_items + (1 if has_jobs else 0)  # +1 for "jobs/" header

            idx = 0
            for name, typ, info in items:
                idx += 1
                is_last_root = (idx == n_items) and not has_jobs
                c = "└──" if is_last_root else "├──"
                pad = "    " if is_last_root else "│   "
                lines.append(f"{p_prefix}{c} {name}  {info}")

            if has_jobs:
                # jobs/ header
                c = "└──" if True else "├──"  # always last at project level
                lines.append(f"{p_prefix}└── jobs/")
                j_prefix = f"{p_prefix}    "
                for ji, (jname, jfiles, jsize, jstatus) in enumerate(jobs):
                    is_last_job = ji == len(jobs) - 1
                    jc = "└──" if is_last_job else "├──"
                    jpad = "    " if is_last_job else "│   "
                    lines.append(f"{j_prefix}{jc} {jname}/ ({len(jfiles)} files, {jsize}){jstatus}")
                    # Show files inside job
                    for fi, jf in enumerate(jfiles):
                        is_last_file = fi == len(jfiles) - 1
                        fc = "└──" if is_last_file else "├──"
                        fsz = _fmt_size(jf.stat().st_size)
                        fdesc = _file_description(jf.name)
                        lines.append(f"{j_prefix}{jpad}{fc} {jf.name}  {fsz:>7s}  {fdesc}")

        return "\n".join(lines)

    def _cmd_project(self, args: str) -> str:
        """Manage session projects: list, switch, create, delete."""
        import sys, os
        from pathlib import Path
        import config as _cfg

        parts = args.strip().split()

        # No args → list projects
        if not parts:
            try:
                session_root = Path.cwd() / '.session'
                if not session_root.is_dir():
                    return "No .session/ directory found."
                active = getattr(_cfg, 'ACTIVE_PROJECT', 'default')
                lines = []
                for d in sorted(session_root.iterdir()):
                    if not d.is_dir():
                        continue
                    files = [f for f in d.rglob('*') if f.is_file()]
                    total_size = sum(f.stat().st_size for f in files)
                    marker = " ◀ active" if d.name == active else ""
                    size_str = f"{total_size/1024:.0f}KB" if total_size > 1024 else f"{total_size}B"
                    lines.append(f"  {d.name}/ ({len(files)} files, {size_str}){marker}")
                if not lines:
                    return "No projects found."
                return "Projects:\n" + "\n".join(lines)
            except Exception as e:
                return f"Error: {e}"

        subcmd = parts[0].lower()

        if subcmd == 'create':
            name = parts[1] if len(parts) > 1 else ''
            if not name:
                return "Usage: /project create <name>"
            if '/' in name or '\\' in name or '..' in name:
                return "Error: invalid project name"
            session_dir = Path.cwd() / '.session' / name
            if session_dir.exists():
                return f"Project '{name}' already exists."
            session_dir.mkdir(parents=True, exist_ok=True)
            return f"✅ Created project '{name}'"

        if subcmd == 'delete':
            name = parts[1] if len(parts) > 1 else ''
            if not name:
                return "Usage: /project delete <name>"
            if name == 'default':
                return "Error: Cannot delete the 'default' project."
            active = getattr(_cfg, 'ACTIVE_PROJECT', 'default')
            if name == active:
                return f"Error: Cannot delete active project '{name}'. Switch first."
            import shutil
            session_dir = Path.cwd() / '.session' / name
            if not session_dir.exists():
                return f"Project '{name}' not found."
            files = [f for f in session_dir.rglob('*') if f.is_file()]
            shutil.rmtree(str(session_dir))
            return f"✅ Deleted project '{name}' ({len(files)} files)"

        # Default: switch to project
        name = parts[0]
        if '/' in name or '\\' in name or '..' in name:
            return "Error: invalid project name"
        try:
            import main as _main
            _setup_fn = getattr(_main, '_setup_session', None)
        except ImportError:
            _setup_fn = None

        if _setup_fn is None:
            for mod_name in list(sys.modules.keys()):
                if 'main' in mod_name.lower():
                    _setup_fn = getattr(sys.modules[mod_name], '_setup_session', None)
                    if _setup_fn:
                        break

        if _setup_fn is None:
            return "Error: Cannot find _setup_session. Start agent normally first."

        old = getattr(_cfg, 'ACTIVE_PROJECT', 'default')
        _setup_fn(name)
        new = getattr(_cfg, 'ACTIVE_PROJECT', name)
        return f"✅ Switched project: {old} → {new}"

    def _cmd_job(self, args: str) -> str:
        """Manage jobs in current project: list, status, output, context, cancel.

        /job              → list all jobs
        /job <id>         → show job status + result summary
        /job output <id>  → show full output
        /job context <id> → show conversation messages (the agent's context)
        /job cancel <id>  → cancel a running job
        """
        from pathlib import Path
        import json
        import config as _cfg

        parts = args.strip().split()
        session_dir = getattr(_cfg, 'SESSION_DIR', '')
        if not session_dir:
            return "No active session."
        jobs_dir = Path(session_dir) / 'jobs'

        def _read_result(job_dir: Path) -> dict:
            """Read result.json from a job directory."""
            result_file = job_dir / 'result.json'
            if result_file.exists():
                try:
                    return json.loads(result_file.read_text(encoding='utf-8'))
                except Exception:
                    pass
            return {}

        # ── No args → list jobs ───────────────────────────────────────────
        if not parts:
            if not jobs_dir.is_dir():
                return "No jobs directory for current project."
            jobs = sorted([d for d in jobs_dir.iterdir()
                           if d.is_dir() and d.name.startswith('job')])
            if not jobs:
                return "No jobs in current project."
            lines = []
            for job_dir in jobs:
                rdata = _read_result(job_dir)
                status = rdata.get('status', 'unknown')
                agent = rdata.get('agent_name', '')
                iterations = rdata.get('iterations', '')
                exec_ms = rdata.get('execution_time_ms', '')
                output_preview = rdata.get('output_preview', rdata.get('output', ''))[:80]

                # Legacy fallback
                if not rdata:
                    status_file = job_dir / 'status.json'
                    if status_file.exists():
                        try:
                            data = json.loads(status_file.read_text(encoding='utf-8'))
                            status = data.get('status', 'unknown')
                            agent = data.get('agent', '')
                        except Exception:
                            pass
                    elif (job_dir / 'output.txt').exists():
                        status = "completed"
                    elif (job_dir / 'error.txt').exists():
                        status = "failed"

                file_count = sum(1 for f in job_dir.iterdir() if f.is_file())
                icon = {"running": "🔄", "completed": "✅", "failed": "❌",
                        "cancelled": "⛔", "pending": "⏳"}.get(status, "📋")

                time_str = ""
                if exec_ms:
                    time_str = f", {exec_ms/1000:.1f}s" if exec_ms > 1000 else f", {exec_ms}ms"

                lines.append(f"  {icon} {job_dir.name}  {agent or '?'}  {status}  ({iterations} iter{time_str})")
                if output_preview:
                    lines.append(f"     {output_preview}")
            return "Jobs:\n" + "\n".join(lines)

        subcmd = parts[0].lower()

        # ── /job output <id> ──────────────────────────────────────────────
        if subcmd == 'output':
            job_id = parts[1] if len(parts) > 1 else ''
            if not job_id:
                return "Usage: /job output <id>"
            if job_id.isdigit():
                job_id = f"job{job_id}"
            job_dir = jobs_dir / job_id
            if not job_dir.is_dir():
                return f"Job '{job_id}' not found."

            # Try result.json output_preview first
            rdata = _read_result(job_dir)
            if rdata:
                lines = [f"=== {job_id} output ==="]
                for key in ('agent_name', 'status', 'iterations', 'execution_time_ms'):
                    if key in rdata:
                        lines.append(f"{key}: {rdata[key]}")
                if rdata.get('files_examined'):
                    lines.append(f"files_examined: {rdata['files_examined']}")
                if rdata.get('files_modified'):
                    lines.append(f"files_modified: {rdata['files_modified']}")
                if rdata.get('tool_calls'):
                    lines.append(f"tool_calls: {rdata['tool_calls']}")
                output = rdata.get('output_preview', rdata.get('output', ''))
                if output:
                    lines.append(f"\n{output}")
                return "\n".join(lines)

            # Legacy: output.txt
            output_file = job_dir / 'output.txt'
            if output_file.exists():
                content = output_file.read_text(encoding='utf-8', errors='replace')
                if len(content) > 4000:
                    return f"[Output truncated]\n\n{content[:4000]}\n..."
                return content
            return f"No output in job '{job_id}'."

        # ── /job context <id> ─────────────────────────────────────────────
        if subcmd == 'context':
            job_id = parts[1] if len(parts) > 1 else ''
            if not job_id:
                return "Usage: /job context <id>"
            if job_id.isdigit():
                job_id = f"job{job_id}"
            job_dir = jobs_dir / job_id
            if not job_dir.is_dir():
                return f"Job '{job_id}' not found."

            conv_file = job_dir / 'conversation.json'
            if not conv_file.exists():
                return f"No conversation.json in job '{job_id}'."

            try:
                messages = json.loads(conv_file.read_text(encoding='utf-8'))
            except Exception as e:
                return f"Error reading conversation: {e}"

            if not messages:
                return f"Empty conversation in job '{job_id}'."

            lines = [f"=== {job_id} conversation ({len(messages)} messages) ===", ""]
            for i, msg in enumerate(messages):
                role = msg.get('role', '?')
                content = msg.get('content', '')
                if isinstance(content, list):
                    # Handle structured content (text blocks)
                    parts_text = []
                    for part in content:
                        if isinstance(part, dict) and part.get('type') == 'text':
                            parts_text.append(part.get('text', ''))
                        elif isinstance(part, str):
                            parts_text.append(part)
                    content = '\n'.join(parts_text)

                # Truncate long messages
                if len(content) > 500:
                    content = content[:500] + f"\n... [{len(content)} chars total]"

                role_icon = {"user": "👤", "assistant": "🤖", "system": "⚙️"}.get(role, "📋")
                lines.append(f"{role_icon} [{role}]")
                lines.append(f"   {content}")
                lines.append("")

            return "\n".join(lines)

        # ── /job cancel <id> ──────────────────────────────────────────────
        if subcmd == 'cancel':
            job_id = parts[1] if len(parts) > 1 else ''
            if not job_id:
                return "Usage: /job cancel <id>"
            if job_id.isdigit():
                job_id = f"job{job_id}"
            job_dir = jobs_dir / job_id
            if not job_dir.is_dir():
                return f"Job '{job_id}' not found."
            import time
            (job_dir / 'cancel').write_text(str(int(time.time())), encoding='utf-8')
            rdata = _read_result(job_dir)
            if rdata:
                if rdata.get('status') in ('completed', 'failed'):
                    return f"Job '{job_id}' is already {rdata['status']}. Cannot cancel."
            return f"✅ Cancel signal sent to '{job_id}'."

        # ── Default: /job <id> → status summary ──────────────────────────
        job_id = parts[0]
        if job_id.isdigit():
            job_id = f"job{job_id}"
        job_dir = jobs_dir / job_id
        if not job_dir.is_dir():
            return f"Job '{job_id}' not found."

        lines = [f"Job: {job_id}", f"Path: {job_dir}"]

        # Read result.json (new format)
        rdata = _read_result(job_dir)
        if rdata:
            for key in ('agent_name', 'status', 'iterations', 'execution_time_ms',
                        'tool_calls', 'files_examined', 'files_modified', 'error'):
                val = rdata.get(key)
                if val is not None and val != '' and val != []:
                    lines.append(f"{key}: {val}")
            output = rdata.get('output_preview', rdata.get('output', ''))
            if output:
                if len(output) > 300:
                    lines.append(f"\nOutput (preview):\n{output[:300]}...")
                else:
                    lines.append(f"\nOutput:\n{output}")
        else:
            # Legacy: status.json
            status_file = job_dir / 'status.json'
            if status_file.exists():
                try:
                    data = json.loads(status_file.read_text(encoding='utf-8'))
                    for key in ('status', 'description', 'prompt', 'agent', 'started_at', 'completed_at', 'error'):
                        if key in data:
                            lines.append(f"{key}: {str(data[key])[:200]}")
                except Exception:
                    pass

        files = sorted(job_dir.iterdir())
        lines.append(f"\nFiles ({len(files)}):")
        for f in files:
            if f.is_file():
                size = f.stat().st_size
                lines.append(f"  {f.name}  {_fmt_size(size):>8s}  {_file_description(f.name)}")

        return "\n".join(lines)

    # ============================================================
    # /converge — Self-converging EDA loop commands
    # ============================================================

    def _cmd_converge(self, args: str) -> str:
        """Manage converge loop: start, status, next, auto, override, inject, level, history, report.

        /converge                        → show usage
        /converge start <module> [-p Y]  → create project, load config, start loop
        /converge status                 → show loop_state.json (stage, score, iteration, criteria)
        /converge next                   → manual single-step (advance one stage)
        /converge auto                   → resume auto-loop from current state
        /converge override <S> <C>       → force classifier decision next iteration
        /converge inject <message>       → send message to running sub-agent inbox
        /converge level [1-3]            → set verbosity (1=summary, 2=per-stage, 3=full)
        /converge history                → score trajectory table
        /converge report                 → final convergence report
        """
        import json
        from pathlib import Path

        parts = args.strip().split()
        if not parts:
            return (
                "Converge Loop Commands:\n"
                "  /converge start <module> [-p converge.yaml]  — start new loop\n"
                "  /converge status                              — show current state\n"
                "  /converge next                                — single step\n"
                "  /converge auto                                — resume auto-loop\n"
                "  /converge override <stage> <classifier>       — force classifier\n"
                "  /converge inject <message>                    — send to sub-agent inbox\n"
                "  /converge level [1-3]                         — set verbosity\n"
                "  /converge history                             — score trajectory\n"
                "  /converge report                              — final report\n"
            )

        subcmd = parts[0].lower()

        # ── /converge start <module> [-p converge.yaml] ─────────────────────
        if subcmd == 'start':
            return self._converge_start(parts[1:])

        # ── /converge status ────────────────────────────────────────────────
        if subcmd == 'status':
            return self._converge_status()

        # ── /converge next ──────────────────────────────────────────────────
        if subcmd == 'next':
            return self._converge_next()

        # ── /converge auto ──────────────────────────────────────────────────
        if subcmd == 'auto':
            return self._converge_auto()

        # ── /converge override <stage> <classifier> ─────────────────────────
        if subcmd == 'override':
            return self._converge_override(parts[1:])

        # ── /converge inject <message> ──────────────────────────────────────
        if subcmd == 'inject':
            return self._converge_inject(' '.join(parts[1:]))

        # ── /converge level [1-3] ───────────────────────────────────────────
        if subcmd == 'level':
            return self._converge_level(parts[1:])

        # ── /converge history ───────────────────────────────────────────────
        if subcmd == 'history':
            return self._converge_history()

        # ── /converge report ────────────────────────────────────────────────
        if subcmd == 'report':
            return self._converge_report()

        return (
            f"Unknown converge subcommand: {subcmd}\n"
            f"Usage: /converge start|status|next|auto|override|inject|level|history|report"
        )

    # ── Converge session tracker (module-level) ─────────────────────────────
    # Stored on the registry instance so it persists across calls.

    def _cv_get_session(self):
        """Get the active converge session dict (or None)."""
        return getattr(self, '_cv_session', None)

    def _cv_set_session(self, project, controller, verbose_level=1):
        """Store active converge session."""
        self._cv_session = {
            'project': project,
            'controller': controller,
            'verbose_level': verbose_level,  # 1=summary, 2=per-stage, 3=full
        }

    def _cv_clear_session(self):
        """Clear the active converge session."""
        if hasattr(self, '_cv_session'):
            del self._cv_session

    def _cv_get_verbose(self) -> int:
        """Get current verbosity level."""
        sess = self._cv_get_session()
        return sess['verbose_level'] if sess else 1

    def _converge_start(self, parts: list) -> str:
        """Handle /converge start <module> [-p converge.yaml]"""
        import config as _cfg
        from core.project import create_project
        from core.converge import LoopController

        if not parts:
            return "Usage: /converge start <module> [-p converge.yaml]"

        module = parts[0]
        converge_yaml = None

        # Parse -p flag
        i = 1
        while i < len(parts):
            if parts[i] in ('-p', '--path') and i + 1 < len(parts):
                converge_yaml = Path(parts[i + 1])
                i += 2
            else:
                i += 1

        try:
            # Determine project root
            project_root = Path(_cfg.SESSION_DIR).parent if hasattr(_cfg, 'SESSION_DIR') and _cfg.SESSION_DIR else Path.cwd()

            # Create project with converge config
            project = create_project(
                module=module,
                project_root=project_root,
                converge_yaml=converge_yaml,
            )

            # Set up the session directory
            if not project.session_dir:
                project.session_dir = project_root / ".session" / module
            project.save_state()

            # Create controller
            verbose = True  # always capture logs
            controller = LoopController(project, verbose=verbose)

            # Store session
            self._cv_set_session(project, controller, verbose_level=2)

            config = project.converge_config
            stage_ids = [s.id for s in config.stages] if config else []

            return (
                f"✅ Converge loop initialized\n"
                f"  Module: {module}\n"
                f"  Config: {project.converge_yaml_path}\n"
                f"  Stages: {' → '.join(stage_ids)}\n"
                f"  Criteria: {len(config.criteria_hard_stop)} hard-stop(s)\n"
                f"  Score threshold: {config.criteria_score_threshold}\n"
                f"  Max iterations: {config.criteria_max_total_iterations}\n"
                f"\n"
                f"Use /converge auto to run, /converge next to single-step."
            )

        except FileNotFoundError as e:
            return f"❌ Config not found: {e}"
        except Exception as e:
            return f"❌ Failed to start converge loop: {e}"

    def _converge_status(self) -> str:
        """Handle /converge status — display current loop state."""
        from core.project import restore_project
        import config as _cfg

        # Try active session first
        sess = self._cv_get_session()
        if sess:
            project = sess['project']
            return project.format_status()

        # Try restoring from session dir
        session_dir = getattr(_cfg, 'SESSION_DIR', '')
        if session_dir:
            sdir = Path(session_dir)
            project = restore_project(sdir)
            if project:
                return project.format_status()

        return (
            "No active converge loop.\n"
            "Use /converge start <module> to begin."
        )

    def _converge_next(self) -> str:
        """Handle /converge next — manual single step."""
        sess = self._cv_get_session()
        if not sess:
            return "No active converge loop. Use /converge start <module> first."

        project = sess['project']
        controller = sess['controller']

        if project.status in ('converged', 'failed', 'stalled', 'timeout'):
            return (
                f"Loop already finished: {project.status}\n"
                f"Reason: {project.convergence_reason}\n"
                f"Use /converge start to begin a new loop."
            )

        if project.phase == 'done':
            return (
                f"Loop phase is 'done'. Status: {project.status}\n"
                f"Reason: {project.convergence_reason}"
            )

        try:
            # Execute one iteration via the controller's run method
            # For single-step, we run a truncated loop (max 1 stage advance)
            config = project.converge_config
            if not config or not config.stages:
                return "No stages configured."

            # Find current stage index
            stage_ids = [s.id for s in config.stages]
            current_idx = 0
            if project.current_stage in stage_ids:
                current_idx = stage_ids.index(project.current_stage)

            # Execute just the current stage
            if current_idx < len(stage_ids):
                stage_cfg = controller._stage_map[stage_ids[current_idx]]
                action_label, raw_output = controller._execute_stage(stage_cfg)

                if raw_output:
                    # Parse output → metrics
                    stage_parser = config.parsers.get(stage_cfg.id)
                    parsed = controller.parser.parse(raw_output, stage_parser)

                    # Flatten into project metrics
                    for k, v in parsed.items():
                        project.metrics[f"{stage_cfg.id}.{k}"] = v

                    # Compute score
                    score = controller.score_calc.compute(project.metrics)

                    # Record iteration
                    project.current_stage = stage_cfg.id
                    project.record_iteration(action_label, dict(project.metrics), score)
                    project.save_state()

                    # Format result based on verbosity
                    vl = sess['verbose_level']
                    lines = [
                        f"Step complete: {stage_cfg.id}",
                        f"  Score: {score:.1f} (best: {project.best_score:.1f})",
                    ]

                    if vl >= 2:
                        for k, v in sorted(parsed.items()):
                            lines.append(f"  {stage_cfg.id}.{k}: {v}")

                    # Check convergence
                    if project.is_converged():
                        project.status = "converged"
                        project.convergence_reason = "All hard_stop criteria met"
                        project.phase = "done"
                        project.save_state()
                        lines.append("\n✅ CONVERGED — all criteria met!")
                    elif project.is_exhausted():
                        project.status = "failed"
                        project.convergence_reason = f"Max iterations reached"
                        project.phase = "done"
                        project.save_state()
                        lines.append(f"\n❌ EXHAUSTED — max iterations reached")

                    return "\n".join(lines)
                else:
                    project.save_state()
                    return f"Stage {stage_cfg.id} produced no output."

            return f"All stages completed. Status: {project.status}"

        except Exception as e:
            return f"❌ Step failed: {e}"

    def _converge_auto(self) -> str:
        """Handle /converge auto — resume auto-loop."""
        sess = self._cv_get_session()
        if not sess:
            return "No active converge loop. Use /converge start <module> first."

        project = sess['project']
        controller = sess['controller']

        if project.status in ('converged', 'failed', 'stalled', 'timeout') and project.phase == 'done':
            return (
                f"Loop already finished: {project.status}\n"
                f"Reason: {project.convergence_reason}\n"
                f"Use /converge start to begin a new loop."
            )

        try:
            project.phase = "running"
            project.status = "running"
            result_project = controller.run()

            # Update session
            self._cv_set_session(result_project, controller, sess['verbose_level'])

            # Format result
            criteria = result_project.check_hard_stop_criteria()
            criteria_lines = []
            for desc, passed in criteria.items():
                icon = "✅" if passed else "❌"
                criteria_lines.append(f"  {icon} {desc}")

            return (
                f"{'='*50}\n"
                f"Converge Loop Complete\n"
                f"{'='*50}\n"
                f"Status: {result_project.status}\n"
                f"Score: {result_project.score:.1f} (best: {result_project.best_score:.1f})\n"
                f"Iterations: {result_project.iteration}\n"
                f"Reason: {result_project.convergence_reason}\n"
                f"\nCriteria:\n" + "\n".join(criteria_lines) +
                f"\n\nUse /converge history for trajectory, /converge report for details."
            )

        except Exception as e:
            return f"❌ Auto-loop failed: {e}"

    def _converge_override(self, parts: list) -> str:
        """Handle /converge override <stage> <classifier> — force classifier decision."""
        sess = self._cv_get_session()
        if not sess:
            return "No active converge loop. Use /converge start <module> first."

        if len(parts) < 2:
            return "Usage: /converge override <stage_id> <classifier_label>"

        stage_id = parts[0]
        classifier_label = parts[1]

        project = sess['project']

        # Store override in project inbox for the controller to pick up
        project.send_to_inbox(
            "override",
            f"Forcing classifier={classifier_label} for stage={stage_id}",
            stage=stage_id,
            classifier=classifier_label,
        )
        project.save_state()

        return (
            f"✅ Override queued\n"
            f"  Stage: {stage_id}\n"
            f"  Classifier: {classifier_label}\n"
            f"  Will apply on next iteration of stage '{stage_id}'."
        )

    def _converge_inject(self, message: str) -> str:
        """Handle /converge inject <message> — send message to sub-agent inbox."""
        sess = self._cv_get_session()
        if not sess:
            return "No active converge loop. Use /converge start <module> first."

        if not message.strip():
            return "Usage: /converge inject <message>"

        project = sess['project']
        project.send_to_inbox("user_inject", message.strip())
        project.save_state()

        return (
            f"✅ Message injected into converge loop inbox\n"
            f"  Current stage: {project.current_stage}\n"
            f"  Iteration: {project.iteration}\n"
            f"  Pending inbox: {len(project.inbox)} message(s)"
        )

    def _converge_level(self, parts: list) -> str:
        """Handle /converge level [1-3] — set verbosity."""
        sess = self._cv_get_session()

        if not parts:
            current = sess['verbose_level'] if sess else 1
            return (
                f"Verbosity level: {current}\n"
                f"  1 = summary (status only)\n"
                f"  2 = per-stage (metrics per stage)\n"
                f"  3 = full (raw output included)"
            )

        try:
            level = int(parts[0])
            if level not in (1, 2, 3):
                return "Level must be 1, 2, or 3."
        except ValueError:
            return "Level must be 1, 2, or 3."

        if sess:
            sess['verbose_level'] = level

        return (
            f"✅ Verbosity set to {level}\n"
            f"  {'summary' if level == 1 else 'per-stage' if level == 2 else 'full output'}"
        )

    def _converge_history(self) -> str:
        """Handle /converge history — score trajectory table."""
        sess = self._cv_get_session()
        if sess:
            project = sess['project']
            if project.history:
                return project.format_history()

        # Try loading from disk
        from core.project import restore_project
        import config as _cfg

        session_dir = getattr(_cfg, 'SESSION_DIR', '')
        if session_dir:
            project = restore_project(Path(session_dir))
            if project and project.history:
                return project.format_history()

        return (
            "No converge history available.\n"
            "Use /converge start <module> and run some iterations first."
        )

    def _converge_report(self) -> str:
        """Handle /converge report — final convergence report."""
        sess = self._cv_get_session()
        project = None

        if sess:
            project = sess['project']
        else:
            # Try loading from disk
            from core.project import restore_project
            import config as _cfg
            session_dir = getattr(_cfg, 'SESSION_DIR', '')
            if session_dir:
                project = restore_project(Path(session_dir))

        if not project:
            return (
                "No converge data available.\n"
                "Use /converge start <module> and run the loop first."
            )

        # Build report
        criteria = project.check_hard_stop_criteria()
        criteria_lines = []
        for desc, passed in criteria.items():
            icon = "✅" if passed else "❌"
            criteria_lines.append(f"  {icon} {desc}")

        # Score trajectory summary
        scores = [h['score'] for h in project.history] if project.history else []
        score_summary = ""
        if scores:
            score_summary = (
                f"  Min: {min(scores):.1f} | Max: {max(scores):.1f} | "
                f"Final: {scores[-1]:.1f} | Best: {project.best_score:.1f}"
            )

        # Stage breakdown
        stage_stats = {}
        for h in project.history:
            stage = h.get('stage', '?')
            if stage not in stage_stats:
                stage_stats[stage] = {'count': 0, 'scores': []}
            stage_stats[stage]['count'] += 1
            stage_stats[stage]['scores'].append(h['score'])

        stage_lines = []
        for stage, stats in stage_stats.items():
            avg = sum(stats['scores']) / len(stats['scores']) if stats['scores'] else 0
            stage_lines.append(
                f"  {stage:<15} iterations: {stats['count']:>3}  avg_score: {avg:>6.1f}"
            )

        # Variables
        var_lines = []
        for k, v in sorted(project.variables.items()):
            var_lines.append(f"  {k}: {v}")

        # Metrics
        metric_lines = []
        for k, v in sorted(project.metrics.items()):
            metric_lines.append(f"  {k}: {v}")

        # Jobs
        job_lines = []
        for jid in project.jobs:
            job_lines.append(f"  {jid}")

        lines = [
            f"{'='*60}",
            f"  CONVERGE REPORT: {project.module}",
            f"{'='*60}",
            f"",
            f"Status: {project.status}",
            f"Phase: {project.phase}",
            f"Reason: {project.convergence_reason or 'N/A'}",
            f"",
            f"Score: {project.score:.1f} | Best: {project.best_score:.1f}",
            f"Total iterations: {project.iteration}",
            f"No-improve count: {project.no_improve_count}",
            f"",
        ]

        if score_summary:
            lines.append("Score Trajectory:")
            lines.append(score_summary)
            lines.append("")

        if criteria_lines:
            lines.append("Criteria:")
            lines.extend(criteria_lines)
            lines.append("")

        if stage_lines:
            lines.append("Stage Breakdown:")
            lines.extend(stage_lines)
            lines.append("")

        if metric_lines:
            lines.append("Final Metrics:")
            lines.extend(metric_lines)
            lines.append("")

        if var_lines:
            lines.append("Variables:")
            lines.extend(var_lines)
            lines.append("")

        if job_lines:
            lines.append(f"Jobs ({len(job_lines)}):")
            lines.extend(job_lines)
            lines.append("")

        return "\n".join(lines)

    def _cmd_workspace(self, args: str) -> str:
        """Switch workspace/workflow. /workspace <name> or /workspace to show current."""
        import sys, os
        name = args.strip()
        if not name:
            # Show current workspace and available ones
            current = os.environ.get("ACTIVE_WORKSPACE", "default")
            # Discover available workspaces
            _script_dir = os.path.dirname(os.path.abspath(__file__))
            _project_root = os.path.dirname(_script_dir)
            workflow_root = os.path.join(_project_root, "workflow")
            available = []
            if os.path.isdir(workflow_root):
                for d in sorted(os.listdir(workflow_root)):
                    p = os.path.join(workflow_root, d)
                    if os.path.isdir(p) and os.path.exists(os.path.join(p, "workspace.json")):
                        marker = " ◀ active" if d == current else ""
                        available.append(f"  {d}{marker}")
            lines = [f"Current workflow: {current}"]
            if available:
                lines.append("Available:")
                lines.extend(available)
            lines.append("Usage: /workflow <name>")
            return "\n".join(lines)
        return f"WORKSPACE_SWITCH:{name}"

    def _cmd_plan(self, args: str) -> str:
        """Enter plan mode. If task given, enter plan mode and run immediately."""
        task = args.strip()
        if task:
            return f"PLAN_AND_RUN:{task}"
        return "AGENT_MODE:plan"

    def _cmd_make(self, args: str) -> str:
        """Generate artifacts from conversation context. /make todo"""
        sub = args.strip().lower()
        if sub == 'todo':
            prompt = (
                "지금까지의 대화 전체를 면밀히 분석하여 Todo List를 즉시 생성하라.\n\n"
                "## 필수 규칙\n"
                "1. 대화에서 언급된 모든 미완료 작업·요청·버그·개선사항을 빠짐없이 추출하라.\n"
                "2. 이미 완료된 항목은 제외하고 **남은 작업만** 포함하라.\n"
                "3. 각 항목은 '동사+목적어' 형태의 구체적 행동으로 작성하라 (예: '로그인 API 401 오류 수정').\n"
                "4. 우선순위(높음→낮음) 순으로 정렬하라.\n"
                "5. 각 항목에 반드시 다음을 포함하라:\n"
                "   - **detail**: 구체적 구현 방법 또는 접근 방식\n"
                "   - **criteria**: 완료 판단 기준 체크리스트 (줄바꿈으로 구분, 2~4개)\n"
                "     예) '테스트 통과\n동작 확인\n코드 리뷰 완료'\n"
                "6. **반드시 TodoWrite 도구를 호출**하여 todo list를 저장하라 — 텍스트 출력만으로는 부족하다.\n\n"
                "지금 바로 TodoWrite를 호출하라."
            )
            return f"INJECT_PROMPT:{prompt}"
        return f"Usage: /make todo\nUnknown subcommand: {sub}\n"

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

            # Subcommand aliases
            SUBCMD_ALIASES = {
                'rm': 'remove',
                'mv': 'move',
                'g':  'goal',
                's':  'set',
                'e':  'edit',
                'rv': 'revert',
            }
            subcmd = SUBCMD_ALIASES.get(subcmd, subcmd)

            if subcmd == 'set':
                return self._todo_force_set(parts[1:], todo_file)
            if subcmd == 'remove':
                return self._todo_remove(parts[1:], todo_file)
            if subcmd == 'add':
                text = args.strip().split(maxsplit=1)
                return self._todo_add(text[1] if len(text) > 1 else '', todo_file)
            if subcmd == 'move':
                return self._todo_move(parts[1:], todo_file)
            if subcmd == 'goal':
                rest = args.strip().split(maxsplit=2)
                return self._todo_goal(rest[1:], todo_file)
            if subcmd == 'edit':
                rest = args.strip().split(maxsplit=3)
                return self._todo_edit(rest[1:], todo_file)
            if subcmd in ('rule', 'rules'):
                return self._todo_rule()
            if subcmd == 'revert':
                rest = args.strip().split()
                return self._todo_revert(rest[1:], todo_file)
            if subcmd == 'templates':
                return self._todo_list_templates()
            if subcmd == 'template':
                tname = parts[1] if len(parts) > 1 else ''
                return self._todo_load_template(tname, todo_file)
            if subcmd == 'delegate':
                return self._todo_delegate(parts[1:], todo_file)
            if subcmd == 'workflow':
                return self._todo_workflow(parts[1:], todo_file)
            if subcmd == 'pipeline':
                return self._todo_pipeline(parts[1:], todo_file)
            if subcmd == 'workflow-delegate':
                return self._todo_workflow_delegate(parts[1:])

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
            # -v flag: full detail (criteria, detail, times)
            verbose = '-v' in args.split()

            try:
                from lib.todo_tracker import TodoTracker
                tracker = TodoTracker.load(todo_file)
                if tracker:
                    return tracker.format_progress() if verbose else tracker.format_simple()
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
        STATUS_ABBR = {
            "p": "pending",
            "i": "in_progress", "ip": "in_progress",
            "c": "completed",
            "a": "approved",
            "r": "rejected",
        }
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
        new_status = STATUS_ABBR.get(parts[1].lower(), parts[1].lower())

        if new_status not in VALID_STATUSES:
            return (
                f"❌ Invalid status: '{parts[1]}'\n"
                f"Valid: {', '.join(sorted(VALID_STATUSES))}\n"
                f"Abbr:  p=pending  i=in_progress  c=completed  a=approved  r=rejected\n"
            )

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

    def _todo_delegate(self, parts: list, todo_file) -> str:
        """Set delegate backend for a task. /todo delegate <N> <backend>"""
        if len(parts) < 2:
            return (
                "Usage: /todo delegate <index> <backend>\n"
                "Backends: sub-agent, cursor-agent, codex, gemini, api\n"
                "Example: /todo delegate 1 sub-agent"
            )
        try:
            idx = int(parts[0]) - 1
            backend = parts[1].lower()
            valid = ["sub-agent", "cursor-agent", "codex", "gemini", "api"]
            if backend not in valid:
                return f"❌ Unknown backend '{backend}'. Valid: {', '.join(valid)}"
            from lib.todo_tracker import TodoTracker
            tracker = TodoTracker.load(todo_file)
            if not tracker or idx < 0 or idx >= len(tracker.todos):
                return f"❌ Task {parts[0]} not found."
            tracker.todos[idx].delegate = backend
            tracker.save()
            return f"✅ Task {parts[0]} delegate set to '{backend}'"
        except Exception as e:
            return f"❌ Error: {e}"

    def _todo_workflow(self, parts: list, todo_file) -> str:
        """Set workflow for a task. /todo workflow <N> <workflow-name>"""
        if len(parts) < 2:
            try:
                from core.workflow_orchestrator import WorkflowOrchestrator
                from pathlib import Path
                orch = WorkflowOrchestrator(project_root=Path.cwd())
                wf_list = orch.list_workflows()
            except Exception:
                wf_list = "(error loading workflows)"
            return (
                "Usage: /todo workflow <index> <workflow-name>\n\n"
                f"{wf_list}"
            )
        try:
            idx = int(parts[0]) - 1
            wf_name = parts[1]
            from core.workflow_orchestrator import WorkflowOrchestrator
            from pathlib import Path
            orch = WorkflowOrchestrator(project_root=Path.cwd())
            if not orch.workflow_exists(wf_name):
                available = list(orch.discover_workflows().keys())
                return f"❌ Workflow '{wf_name}' not found. Available: {available}"
            from lib.todo_tracker import TodoTracker
            tracker = TodoTracker.load(todo_file)
            if not tracker or idx < 0 or idx >= len(tracker.todos):
                return f"❌ Task {parts[0]} not found."
            tracker.todos[idx].workflow = wf_name
            tracker.save()
            return f"✅ Task {parts[0]} workflow set to '{wf_name}'"
        except Exception as e:
            return f"❌ Error: {e}"

    def _todo_pipeline(self, parts: list, todo_file) -> str:
        """Execute pipeline. /todo pipeline sequential|parallel|auto"""
        mode = parts[0] if parts else "auto"
        if mode not in ("sequential", "parallel", "auto"):
            return "Usage: /todo pipeline [sequential|parallel|auto]"
        try:
            from core.tools import pipeline_execute
            return pipeline_execute(mode=mode)
        except Exception as e:
            return f"❌ Pipeline error: {e}"

    def _todo_workflow_delegate(self, parts: list) -> str:
        """Set default delegate for current workspace. /todo workflow-delegate <backend>"""
        if not parts:
            return "Usage: /todo workflow-delegate <backend>\nBackends: sub-agent, cursor-agent, codex, gemini, api"
        backend = parts[0].lower()
        valid = ["sub-agent", "cursor-agent", "codex", "gemini", "api"]
        if backend not in valid:
            return f"❌ Unknown backend '{backend}'. Valid: {', '.join(valid)}"
        # Store in workspace.json default_delegate
        try:
            import os
            ws_name = os.environ.get("ACTIVE_WORKSPACE", "default")
            ws_json = Path("workflow") / ws_name / "workspace.json"
            if ws_json.exists():
                data = json.loads(ws_json.read_text(encoding="utf-8"))
            else:
                data = {}
            data["default_delegate"] = backend
            ws_json.parent.mkdir(parents=True, exist_ok=True)
            ws_json.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            return f"✅ Workspace '{ws_name}' default delegate set to '{backend}'"
        except Exception as e:
            return f"❌ Error: {e}"

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

    def _todo_edit(self, parts: list, todo_file) -> str:
        """
        Edit any field of a todo item.
        Usage: /todo edit <N> <field>[+] <value>
        field+  = append (add to existing), field = replace

        Fields:
          content / c          task description (also updates active_form)
          detail  / d          implementation details
          criteria / cr        completion criteria
          priority / pr        high/medium/low  (h/m/l)
          active_form / af     in-progress display text
          rejection_reason / rr  rejection reason
          approved_reason / ar   approval note
        """
        FIELD_ALIASES = {
            'c':       'content',
            'd':       'detail',
            'cr':      'criteria',
            'pr':      'priority',
            'af':      'active_form',
            'rr':      'rejection_reason',
            'ar':      'approved_reason',
        }
        PRIORITY_ABBR = {'h': 'high', 'm': 'medium', 'l': 'low'}
        VALID_FIELDS = set(FIELD_ALIASES.values())

        if len(parts) < 3 or not parts[0].isdigit():
            fields_str = "  content/c, detail/d, criteria/cr, priority/pr, active_form/af, rejection_reason/rr, approved_reason/ar"
            return (
                "Usage: /todo edit <N> <field>[+] <value>\n"
                "  field+  = append to existing value\n\n"
                "Fields:\n" + fields_str + "\n\n"
                "Examples:\n"
                "  /todo e 1 d \"JWT 라이브러리 사용\"    set detail\n"
                "  /todo e 1 d+ \"\\n- RS256 알고리즘\"   append to detail\n"
                "  /todo e 2 cr \"테스트 통과\"           set criteria\n"
                "  /todo e 1 pr h                      set priority=high\n"
                "  /todo e 1 ar \"모든 테스트 통과\"      set approved reason\n"
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

            raw_field = parts[1]
            append = raw_field.endswith('+')
            field_key = raw_field.rstrip('+').lower()
            field_name = FIELD_ALIASES.get(field_key, field_key)

            if field_name not in VALID_FIELDS:
                return f"❌ Unknown field: '{field_key}'\nValid: {', '.join(sorted(VALID_FIELDS))}\n"

            value = parts[2].strip()

            # Priority special handling
            if field_name == 'priority':
                value = PRIORITY_ABBR.get(value.lower(), value.lower())
                if value not in ('high', 'medium', 'low'):
                    return f"❌ Invalid priority: '{value}' — use high/medium/low (h/m/l)\n"
                append = False  # priority never appends

            todo = tracker.todos[idx]
            old_value = getattr(todo, field_name, "")

            if append and old_value:
                new_value = old_value + value
            else:
                new_value = value

            setattr(todo, field_name, new_value)

            # content change also syncs active_form (unless af was explicitly set)
            if field_name == 'content' and not append:
                todo.active_form = new_value

            tracker.save()

            mode = "appended" if append else "set"
            return (
                f"✏️  Task {int(parts[0])} [{field_name}] {mode}:\n"
                f"   {repr(new_value[:120])}\n\n"
                + tracker.format_progress()
            )
        except Exception as e:
            return f"❌ Error: {e}\n"

    def _todo_rule(self) -> str:
        """Show current rules/ folder contents."""
        from pathlib import Path
        import os
        rules_dir = Path(os.getcwd()) / "rules"
        SEP = "=" * 60
        lines = [f"\n{SEP}", f" TODO RULES  {rules_dir}", SEP]
        if rules_dir.is_dir():
            files = sorted(rules_dir.glob("*.md"))
            if files:
                for f in files:
                    content = f.read_text(encoding="utf-8").strip()
                    lines.append(f"\n  ├ {f.name}")
                    for ln in content.splitlines()[:6]:
                        lines.append(f"  │  {ln}")
                    if len(content.splitlines()) > 6:
                        lines.append(f"  │  ... ({len(content.splitlines())} lines total)")
            else:
                lines.append("\n  (파일 없음 — rules/*.md 파일을 추가하세요)")
        else:
            lines.append(f"\n  rules/ 폴더 없음")
            lines.append(f"  mkdir rules && vi rules/todo.md 로 생성하세요")
        lines.append(f"\n{SEP}")
        lines.append("💡 태스크 실행 중 매 continuation prompt에 자동 첨부됩니다.")
        lines.append(f"{SEP}")
        return "\n".join(lines) + "\n"

    def _todo_list_templates(self) -> str:
        """List available todo templates from the active workspace and default."""
        try:
            import builtins as _b
            registry = getattr(_b, "_TODO_TEMPLATE_REGISTRY", None)
            if registry is None:
                # Try importing from workflow.loader
                try:
                    from workflow.loader import get_todo_template_registry
                    registry = get_todo_template_registry()
                except ImportError:
                    pass
            if registry:
                names = registry.list_templates()
                if names:
                    lines = ["\nAvailable todo templates:"]
                    for name in names:
                        tmpl = registry.get_template(name)
                        desc = tmpl.get("description", "") if tmpl else ""
                        task_count = len(tmpl.get("tasks", [])) if tmpl else 0
                        lines.append(f"  {name:<20} {task_count} tasks  {desc}")
                    lines.append("\nUsage: /todo template <name>")
                    return "\n".join(lines) + "\n"
            return "No todo templates available. Load a workspace with -w <name> to get templates.\n"
        except Exception as e:
            return f"Error listing templates: {e}\n"

    def _todo_load_template(self, template_name: str, todo_file) -> str:
        """Load a todo template and write it to the todo file. /todo template <name>"""
        if not template_name:
            return "Usage: /todo template <name>\nSee /todo templates for available templates.\n"
        try:
            import builtins as _b
            import json
            from pathlib import Path
            registry = getattr(_b, "_TODO_TEMPLATE_REGISTRY", None)
            if registry is None:
                try:
                    from workflow.loader import get_todo_template_registry
                    registry = get_todo_template_registry()
                except ImportError:
                    pass
            if not registry:
                return "No todo template registry available. Load a workspace with -w <name>.\n"
            tmpl = registry.get_template(template_name)
            if not tmpl:
                available = ", ".join(registry.list_templates()) or "(none)"
                return f"Template '{template_name}' not found.\nAvailable: {available}\n"

            tasks = tmpl.get("tasks", [])
            if not tasks:
                return f"Template '{template_name}' has no tasks.\n"

            # Write tasks to todo file using TodoTracker
            try:
                from lib.todo_tracker import TodoTracker
                tracker = TodoTracker(persist_path=Path(todo_file))
                tracker.add_todos(tasks)
                tracker.save()
                desc = tmpl.get("description", "")
                return (
                    f"Loaded template '{template_name}': {len(tasks)} tasks added.\n"
                    + (f"Description: {desc}\n" if desc else "")
                    + "Run /todo to see the list.\n"
                )
            except Exception as e:
                return f"Error writing todo file: {e}\n"
        except Exception as e:
            return f"Error loading template: {e}\n"

    def _todo_revert(self, args: list, todo_file) -> str:
        """Return revert signal: /todo revert <N> [--hard] [--reset-conv] [reason]"""
        if not args:
            return (
                "Usage: /todo revert <N> [--hard] [--reset-conv] [reason]\n"
                "  --hard        git reset --hard (destructive, removes commits)\n"
                "  --reset-conv  restore conversation to approval snapshot\n"
            )
        try:
            n = int(args[0])
        except ValueError:
            return "Error: N must be an integer.\n"
        rest = args[1:]
        hard = '--hard' in rest
        reset_conv = '--reset-conv' in rest
        reason_parts = [a for a in rest if a not in ('--hard', '--reset-conv')]
        reason = " ".join(reason_parts)
        return f"TODO_REVERT:{n}:hard={hard}:reset_conv={reset_conv}:{reason}"

    def _cmd_mode(self, args: str) -> str:
        """Switch execution or agent mode."""
        parts = args.strip().lower().split()
        if not parts:
            import config as _cfg
            em = getattr(_cfg, 'EXECUTION_MODE', 'agent')
            ci = getattr(_cfg, 'CHAT_MAX_ITERATIONS', 1)
            sbsm = getattr(_cfg, 'STEP_BY_STEP_MODE', False)
            chat_desc = f"chat (max {ci} iter{'s' if ci != 1 else ''}, {'no tools' if ci == 0 else 'tools allowed'})"
            cur = chat_desc if em == 'chat' else em
            return (f"\nExecution mode: {cur}  |  Step-by-step: {'ON' if sbsm else 'OFF'}\n"
                    f"Usage: /mode agent | chat [N] | step | plan | normal\n"
                    f"  chat 0   respond only, no tools\n"
                    f"  chat 1   1 ReAct iteration with tools (default)\n"
                    f"  chat N   N iterations with tools\n")
        mode = parts[0]
        if mode == 'chat':
            n = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 1
            return f"EXECUTION_MODE:chat:{n}"
        if mode in ('agent', 'step'):
            return f"EXECUTION_MODE:{mode}:0"
        if mode in ('plan', 'normal'):
            return f"AGENT_MODE:{mode}"
        return f"\nUnknown mode: {mode}\nUsage: /mode agent|chat [N]|step|plan|normal\n"

    def _cmd_step(self, args: str) -> str:
        """Toggle Step-by-Step execution mode."""
        import config
        config.STEP_BY_STEP_MODE = not getattr(config, 'STEP_BY_STEP_MODE', False)
        status = "ON" if config.STEP_BY_STEP_MODE else "OFF"
        return f"STEP_MODE:{status}"

    def _cmd_skills(self, args: str) -> str:
        """Skill list and control — handled by main loop; fallback display here."""
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
        lines.append("\n\033[2m" + "=" * 60 + "\033[0m")
        lines.append("\033[1m 📄 Full Conversation Context\033[0m")
        lines.append("\033[2m" + "=" * 60 + "\033[0m")

        # Show active skill as a separate [SKILL] block before messages
        try:
            import sys as _sys
            _main = _sys.modules.get('__main__') or _sys.modules.get('main')
            _load_fn = getattr(_main, 'load_active_skills', None)
            _active = getattr(_load_fn, 'active_skills', []) if _load_fn else []
            if _active:
                from core.skill_system import get_skill_registry
                _reg = get_skill_registry()
                for _sname in _active:
                    _skill = _reg.get_skill(_sname)
                    if _skill and _skill.content:
                        lines.append(f"\n\033[1;33m[SKILL: {_sname}]\033[0m")
                        for _sl in _skill.content.splitlines()[:30]:
                            lines.append(f"  {_sl}")
                        if len(_skill.content.splitlines()) > 30:
                            lines.append(f"  \033[2m... ({len(_skill.content.splitlines())} lines total)\033[0m")
        except Exception:
            pass

        for i, msg in enumerate(tracker.messages):
            role = msg.get("role", "unknown").upper()
            raw_content = msg.get("content", "")

            # Handle structured content — for SYSTEM, strip dynamic skill block
            # (shown separately above as [SKILL]) and show only static base
            if isinstance(raw_content, list):
                content_parts = []
                for block in raw_content:
                    if isinstance(block, dict):
                        if block.get("type") == "text":
                            text = block.get("text", "")
                            # Skip the injected ACTIVE SKILLS section (shown as [SKILL] above)
                            if role == "SYSTEM" and "=== ACTIVE SKILLS ===" in text:
                                continue
                            content_parts.append(text)
                        elif block.get("type") == "tool_use":
                            content_parts.append(f"[Tool Use: {block.get('name')}]")
                    else:
                        content_parts.append(str(block))
                content = "\n".join(content_parts).strip()
            elif isinstance(raw_content, dict):
                content = (raw_content.get("static", "") + "\n" + raw_content.get("dynamic", "")).strip()
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

        lines.append("\n\033[2m" + "=" * 60 + "\033[0m")
        return "\n".join(lines) + "\n"

    def _cmd_context(self, args: str) -> str:
        """Visualize context usage"""
        try:
            # Get actual token counts from context tracker
            import config
            import sys
            # Import llm_client (should already be in sys.modules from main.py)
            import llm_client

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

                debug_lines.append(f"  config.MAX_CONTEXT_TOKENS: {config.MAX_CONTEXT_TOKENS:,}")
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
        """Load and format available skills with active status."""
        try:
            import sys
            from core.skill_system import get_skill_registry
            registry = get_skill_registry()
            skills = registry.get_skills_by_priority()
            if not skills:
                return ""

            # Get active state from main.py's load_active_skills if available
            main_mod = sys.modules.get('__main__') or sys.modules.get('main')
            load_fn = getattr(main_mod, 'load_active_skills', None)
            forced = getattr(load_fn, 'forced_skills', set()) if load_fn else set()
            disabled = getattr(load_fn, 'disabled_skills', set()) if load_fn else set()
            auto_active = getattr(load_fn, 'active_skills', []) if load_fn else []

            # active_skills = final merged list actually injected this turn
            _ORANGE = "\033[38;5;208m"
            _RESET  = "\033[0m"
            _DIM    = "\033[2m"
            _BOLD   = "\033[1m"

            lines = ["\n Skills  (/skills a <name|#> · /skills d <name|#> · /skills all · /skills clear)"]
            for i, skill in enumerate(skills, 1):
                n = skill.name
                injected = n in auto_active or n in forced
                if injected:
                    # Orange [SKILL] — actually loaded into system prompt
                    status = f"{_ORANGE}[SKILL]{_RESET} "
                elif n in disabled:
                    status = "\033[31m[off]\033[0m   "
                else:
                    status = f"{_DIM}[off]{_RESET}   "
                desc = (skill.description or "")[:55]
                name_fmt = f"{_ORANGE}{_BOLD}{n:<26}{_RESET}" if injected else f"{_DIM}{n:<26}{_RESET}"
                lines.append(f"  {i:2}  {name_fmt} {status}  {_DIM}{desc}{_RESET}")
            return "\n".join(lines) + "\n"
        except Exception:
            return ""

    def _cmd_clear(self, args: str) -> str:
        """Clear conversation history. /clear [N|all]"""
        arg = args.strip()
        if arg == 'all':
            return "CLEAR_ALL"
        if arg.isdigit():
            return f"CLEAR_HISTORY:{arg}"
        return "CLEAR_HISTORY"  # Special signal for main loop

    def _cmd_model(self, args: str) -> str:
        """Switch model. /model 1 (primary), /model 2 (secondary), /model <name>"""
        import sys
        _config = sys.modules.get('config') or sys.modules.get('src.config')
        if _config is None:
            import src.config as _config
        name = args.strip()
        if not name:
            try:
                from src.llm_client import get_active_model as _get_active_model
                _current_display = _get_active_model()
            except Exception:
                _current_display = _config.MODEL_NAME

            # When cursor-agent is active, show backend info and skip 1/2 markers
            if getattr(_config, "CURSOR_AGENT_ENABLE", False):
                lines = [
                    f"Current model: {_current_display}",
                    f"  Backend: cursor-agent (CURSOR_AGENT_ENABLE=true)",
                    f"  Model:   {getattr(_config, 'CURSOR_AGENT_MODEL', 'auto')}",
                    f"",
                    f"  API models (inactive while cursor-agent is enabled):",
                    f"  1: {_config.PRIMARY_MODEL}",
                    f"  2: {_config.SECONDARY_MODEL}",
                    f"  usage: /model 1|2|<model-name>  (sets CURSOR_AGENT_MODEL when backend active)",
                ]
                return "\n".join(lines)

            marker1 = " ◀ active" if _config.MODEL_NAME == _config.PRIMARY_MODEL and _config.MODEL_NAME != _config.SECONDARY_MODEL else (
                      " ◀ active" if _config.MODEL_NAME == _config.PRIMARY_MODEL and _config.PRIMARY_MODEL != _config.SECONDARY_MODEL else "")
            marker2 = " ◀ active" if _config.MODEL_NAME == _config.SECONDARY_MODEL and _config.MODEL_NAME != _config.PRIMARY_MODEL else ""
            # If primary == secondary == current, mark only primary as active
            if _config.PRIMARY_MODEL == _config.SECONDARY_MODEL == _config.MODEL_NAME:
                marker1 = " ◀ active"
                marker2 = ""
            lines = [
                f"Current model: {_current_display}",
                f"  1: {_config.PRIMARY_MODEL}{marker1}",
                f"  2: {_config.SECONDARY_MODEL}{marker2}",
            ]
            if _config.PRIMARY_MODEL == _config.SECONDARY_MODEL:
                lines.append("  (tip: set PRIMARY_MODEL / SECONDARY_MODEL in .config to use different models)")
            lines.append("  usage: /model 1|2|<model-name>")
            return "\n".join(lines)
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
        W = 64
        SEP  = "─" * W
        SEP2 = "═" * W
        output = []

        if not verbose:
            # --- Core (brief) view ---
            output.append("\n" + SEP2)
            output.append("  Common AI Agent  |  /help -v 전체 목록")
            output.append(SEP2)
            groups_brief = [
                ("컨텍스트",  ["context", "clear", "compact", "compression", "window", "snapshot"]),
                ("모드",      ["plan", "mode", "step"]),
                ("도구/설정", ["model", "tools", "skills", "config", "status"]),
                ("태스크",    ["todo", "git"]),
                ("도움말",    ["help", "list", "man"]),
            ]
            for grp, names in groups_brief:
                cmds_in_grp = [(n, self.commands[n]) for n in names if n in self.commands]
                if not cmds_in_grp:
                    continue
                output.append(f"\n  {grp}")
                for name, cmd in cmds_in_grp:
                    if cmd.get('hidden', False):
                        continue
                    aliases = ""
                    if cmd['aliases']:
                        aliases = f"  (={', '.join('/' + a for a in cmd['aliases'])})"
                    output.append(f"    /{name:<12}{cmd['description']}{aliases}")
            # --- Workspace commands (dynamic, not in the hardcoded list above) ---
            _builtin_names = {n for grp, names in groups_brief for n in names}
            _ws_cmds = [(n, cmd) for n, cmd in sorted(self.commands.items())
                        if n not in _builtin_names and not cmd.get('hidden', False)]
            if _ws_cmds:
                output.append(f"\n  워크스페이스")
                for name, cmd in _ws_cmds:
                    aliases = ""
                    if cmd['aliases']:
                        aliases = f"  (={', '.join('/' + a for a in cmd['aliases'])})"
                    output.append(f"    /{name:<12}{cmd['description']}{aliases}")
            output.append("\n" + SEP)
            output.append("  TAB 자동완성  |  ↑↓ 히스토리  |  /man <topic> 상세 도움말")
            output.append(SEP2)
        else:
            # --- Verbose view: grouped with full detail ---
            output.append("\n" + SEP2)
            output.append("  Common AI Agent — 전체 커맨드 레퍼런스")
            output.append(SEP2)

            groups = [
                ("컨텍스트 & 히스토리", [
                    ("context",     "context [-v|debug]",  "컨텍스트 토큰 사용량 시각화. -v: 전체 대화 표시"),
                    ("clear",       "clear [N]",           "대화 기록 초기화. N 지정 시 최근 N쌍 유지"),
                    ("compact",     "compact [--keep N]",  "AI 요약 압축. 맥락 유지하며 컨텍스트 절약"),
                    ("compression", "compression [N]",     "N 메시지 초과 시 자동 압축. 0=비활성화"),
                    ("window",      "window [N]",          "LLM에 최근 N쌍만 전송. 0=비활성화"),
                    ("snapshot",    "snapshot <subcmd>",   "save|load|list|delete — 대화 스냅샷 관리"),
                ]),
                ("에이전트 & 모드", [
                    ("plan", "plan [task]",  "계획 수립 모드. 탐색→계획→승인→실행"),
                    ("mode", "mode normal",  "Plan Mode 종료, 일반 모드 복귀"),
                    ("step", "step",         "태스크 단위 일시정지 토글 (각 액션 후 멈춤)"),
                ]),
                ("도구 & 설정", [
                    ("model",  "model [1|2|name]",          "모델 전환. 인자 없으면 현재 모델 표시"),
                    ("tools",  "tools",                     "사용 가능한 도구 목록"),
                    ("skills", "skills [a|d <name|#>|all]", "스킬 목록·활성화·비활성화"),
                    ("config", "config",                    "현재 설정 (.config) 주요 값 표시"),
                    ("status", "status",                    "에이전트 상태: 모델, API, 기능 활성화 여부"),
                ]),
                ("태스크 관리", [
                    ("todo", "todo [subcmd]",   "Todo 관리. /man todo 서브커맨드 전체 확인"),
                    ("git",  "git diff|clear",  "Git 변경사항 확인 / .git 디렉토리 삭제"),
                ]),
                ("도움말", [
                    ("help", "help [-v]",    "기본: 핵심 커맨드. -v: 이 전체 목록"),
                    ("list", "list",         "슬래시 커맨드 이름만 간단히 나열"),
                    ("man",  "man <topic>",  "상세 매뉴얼 (plan|todo|compact|context|skills|git|model|clear|guide)"),
                ]),
            ]
            CMD_W = 26
            for group_name, items in groups:
                output.append(f"\n  ┌─ {group_name} {'─' * max(0, W - len(group_name) - 5)}")
                for name, usage, desc in items:
                    if name not in self.commands:
                        continue
                    cmd = self.commands[name]
                    aliases = ""
                    if cmd['aliases']:
                        aliases = f"  (={', '.join('/' + a for a in cmd['aliases'])})"
                    cmd_str = f"/{usage}"
                    output.append(f"  │  {cmd_str:<{CMD_W}} {desc}{aliases}")

            # --- Workspace commands (dynamic) ---
            _verbose_builtin = {name for _, items in groups for name, _, _ in items}
            _ws_cmds_v = [(n, cmd) for n, cmd in sorted(self.commands.items())
                          if n not in _verbose_builtin and not cmd.get('hidden', False)]
            if _ws_cmds_v:
                output.append(f"\n  ┌─ 워크스페이스 커맨드 {'─' * max(0, W - 13)}")
                for name, cmd in _ws_cmds_v:
                    aliases = ""
                    if cmd['aliases']:
                        aliases = f"  (={', '.join('/' + a for a in cmd['aliases'])})"
                    usage = cmd.get('usage', f"/{name}") or f"/{name}"
                    output.append(f"  │  {usage:<{CMD_W}} {cmd['description']}{aliases}")
            output.append("\n" + SEP)
            output.append("  TAB 자동완성  |  ↑↓ 히스토리  |  /man <topic> 상세 도움말")
            output.append(SEP2)

        return "\n".join(output)

    def _cmd_man(self, args: str) -> str:
        """Show detailed manual page for a topic."""
        from core.help_manual import get_man_page
        return get_man_page((args or "").strip().lower())

    def _cmd_list(self, args: str) -> str:
        """Quick command list (alternative to TAB)"""
        commands = sorted(self.get_completions())
        # Display in columns: 4 per row
        col_w = max(len(c) for c in commands) + 2
        rows = []
        for i in range(0, len(commands), 4):
            rows.append("  " + "".join(c.ljust(col_w) for c in commands[i:i+4]))
        return "Commands:\n" + "\n".join(rows)

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
