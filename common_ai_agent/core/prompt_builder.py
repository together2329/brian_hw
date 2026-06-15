"""
System prompt construction for the ReAct agent.

Extracted from src/main.py. All global state (memory_system, graph_lite, etc.)
is passed via PromptContext for testability and clean dependency injection.

Public API:
  PromptContext          — dataclass bundling all optional subsystem references
  build_system_prompt()  — main builder
  _build_system_prompt_str()  — always-string wrapper
"""
import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Union


# ---------------------------------------------------------------------------
# PromptContext — bundles all optional global state
# ---------------------------------------------------------------------------

@dataclass
class PromptContext:
    """Container for optional subsystem references passed to build_system_prompt."""
    memory_system: Any = None
    graph_lite: Any = None
    procedural_memory: Any = None
    hybrid_rag: Any = None
    todo_tracker: Any = None


MEMORY_OVERRIDE_START = "=== MEMORY RULES ==="
MEMORY_OVERRIDE_END = "=== END MEMORY RULES ==="
LEGACY_MEMORY_OVERRIDE_START = "=== MEMORY OVERRIDES (HIGHEST PRIORITY) ==="
LEGACY_MEMORY_OVERRIDE_END = "=== END MEMORY OVERRIDES ==="

MEMORY_INSERT_MARKERS = (
    "\n=== PROJECT RULES",
    "\n## PROJECT RULES",
    "\n## ABSOLUTE RULES",
    "\n## RULES",
    "\n# RULES",
    "\nRULES:",
    "\nRULES (",
    "\nRules:",
)

PROJECT_WIKI_CONTEXT_START = "=== PROJECT WIKI (read before acting) ==="
PROJECT_WIKI_CONTEXT_END = "=== END PROJECT WIKI ==="
PROJECT_WIKI_STAGE_TAGS: Dict[str, List[str]] = {
    "req-gen": ["requirements", "req", "locked-truth"],
    "ssot-gen": ["ssot-gen", "ssot", "new-ip", "ssot-flags", "requirements"],
    "fl-model-gen": ["fl-model-gen", "functional-model", "model-fidelity", "ssot"],
    "cl-model-gen": ["cl-model-gen", "cycle-model", "model-fidelity", "ssot"],
    "equiv-goals": ["equiv-goals", "equivalence", "coverage"],
    "rtl-gen": ["rtl-gen", "rtl-ownership", "rtl", "ssot"],
    "lint": ["lint", "rtl-gen", "rtl"],
    "tb-gen": ["tb-gen", "tb", "stimulus-contract", "scoreboard"],
    "sim": ["sim", "sim-debug", "scoreboard"],
    "sim-debug": ["sim-debug", "sim", "scoreboard", "rtl-gen", "tb-gen"],
    "coverage": ["coverage", "sim", "scoreboard"],
    "goal-audit": ["goal-audit", "equivalence", "coverage"],
}
PROJECT_WIKI_TERM_RE = re.compile(r"[^a-z0-9]+")
PROJECT_WIKI_STOPWORDS = {
    "the", "and", "for", "you", "are", "how", "what", "why", "when", "where",
    "with", "this", "that", "from", "into", "onto", "then", "than", "can",
    "could", "would", "should", "please", "about", "your", "have", "has",
    "had", "not", "but", "all", "any", "use", "using", "fix",
}

TRUE_STRINGS = {"1", "true", "yes", "on", "enable", "enabled"}
FALSE_STRINGS = {"0", "false", "no", "off", "disable", "disabled"}


def _coerce_bool(value: Any, *, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    text = str(value).strip().lower()
    if text in TRUE_STRINGS:
        return True
    if text in FALSE_STRINGS:
        return False
    return default


def prompt_injection_enabled(cfg: Any = None) -> bool:
    """Return whether optional prompt-injection layers should be applied.

    The base system prompt and tool schemas are not controlled by this flag.
    It gates workspace/default system prompt overlays, memory/project-wiki/RAG
    context, skills, graph/procedural guidance, and live orchestrator context.
    """
    for attr in ("ENABLE_PROMPT_INJECTION", "ATLAS_PROMPT_INJECTION"):
        if cfg is not None and hasattr(cfg, attr):
            return _coerce_bool(getattr(cfg, attr), default=False)
    for env_name in ("ATLAS_PROMPT_INJECTION", "ENABLE_PROMPT_INJECTION"):
        if env_name in os.environ:
            return _coerce_bool(os.environ.get(env_name), default=False)
    return False


OAG_CONTEXT_START = "=== OAG / AGENTS.md (project agent rules — read and follow before acting) ==="
OAG_CONTEXT_END = "=== END OAG / AGENTS.md ==="
_OAG_CONTEXT_MAX = 24000  # cap so a big AGENTS.md/rules set can't blow the prompt


def oag_mode_enabled(cfg: Any = None) -> bool:
    """Whether OAG mode is on — tightly fuse a project's `.codex` OAG pack into
    the default agent (inject AGENTS.md + expose the native `oag` tool). Default
    OFF; toggle with OAG_MODE=1 (cfg.OAG_MODE wins when present)."""
    if cfg is not None and hasattr(cfg, "OAG_MODE"):
        return _coerce_bool(getattr(cfg, "OAG_MODE"), default=False)
    return _coerce_bool(os.environ.get("OAG_MODE", ""), default=False)


def oag_root(cfg: Any = None) -> Optional[Path]:
    """Resolve the OAG project root — the directory holding `.codex/` (and
    usually AGENTS.md). Order: OAG_ROOT (env/cfg) -> ATLAS_PROJECT_ROOT -> cwd;
    first candidate that actually has `.codex/` or `AGENTS.md` wins."""
    candidates = [
        os.environ.get("OAG_ROOT", "").strip(),
        str(getattr(cfg, "OAG_ROOT", "") or "") if cfg is not None else "",
        os.environ.get("ATLAS_PROJECT_ROOT", "").strip(),
        os.getcwd(),
        # platform root — the vendored .codex ships inside common_ai_agent, so OAG
        # mode is self-contained even when the workspace/cwd has no .codex.
        str(Path(__file__).resolve().parents[1]),
    ]
    for raw in candidates:
        if not raw:
            continue
        try:
            p = Path(os.path.expandvars(str(raw))).expanduser()
        except (OSError, ValueError):
            continue
        if (p / ".codex").is_dir() or (p / "AGENTS.md").is_file():
            return p
    return None


def _build_oag_agents_context(cfg: Any = None) -> str:
    """Build the OAG context block: the project's AGENTS.md (+ `.codex/AGENTS.md`
    and `.codex/rules/*.md`), so OAG mode 'always reads' the project agent rules.
    Returns '' if no OAG project is resolvable."""
    root = oag_root(cfg)
    if root is None:
        return ""
    parts: List[str] = []
    for rel in ("AGENTS.md", ".codex/AGENTS.md"):
        f = root / rel
        if f.is_file():
            try:
                txt = f.read_text(encoding="utf-8", errors="replace").strip()
            except OSError:
                continue
            if txt:
                parts.append(f"# {rel}\n{txt}")
    rules_dir = root / ".codex" / "rules"
    if rules_dir.is_dir():
        for rf in sorted(rules_dir.glob("*.md")):
            try:
                txt = rf.read_text(encoding="utf-8", errors="replace").strip()
            except OSError:
                continue
            if txt:
                parts.append(f"# .codex/rules/{rf.name}\n{txt}")
    if not parts:
        return ""
    body = "\n\n".join(parts)
    if len(body) > _OAG_CONTEXT_MAX:
        body = body[:_OAG_CONTEXT_MAX] + "\n…(truncated)"
    header = (
        f"(OAG_MODE active — project root: {root})\n"
        "Drive this project's .codex OAG pack with the `oag` tool (no MCP needed): "
        "oag(tool=\"oag.inspect|oag.compile|oag.context|oag.run.start|oag.run.next|"
        "oag.record|oag.decide|oag.review|oag.scaffold|oag.graph|...\", ip=..., stage=..., "
        "intent=...). Run a .codex script with oag(script=\"<file>.py\"). Follow the rules below."
    )
    return f"{OAG_CONTEXT_START}\n{header}\n\n{body}\n{OAG_CONTEXT_END}"


OAG_RUN_CONTEXT_START = "=== OAG ACTIVE RUN (keep driving this — do not stop until it is closed) ==="
OAG_RUN_CONTEXT_END = "=== END OAG ACTIVE RUN ==="
_OAG_RUN_DONE_STATUSES = {"complete", "completed", "closed", "done", "signoff", "promoted", "passed"}


def _build_oag_run_context(cfg: Any = None) -> str:
    """L3 (hook lifecycle, native): surface each incomplete OAG run's persisted
    next-action prompt block every turn. This is the read-only equivalent of the
    .codex UserPromptSubmit context-inject + Stop gate: the agent always sees the
    active run + the single next action, so it keeps driving instead of stopping
    after scaffold. DYNAMIC (run state changes each step) — never mutates state.
    Returns '' when there is no incomplete active run."""
    import json as _json
    root = oag_root(cfg)
    if root is None:
        return ""
    # Scope to the ACTIVE IP only when known — never dump every IP's open run
    # (that bloats the prompt with irrelevant runs and slows every turn). Fall
    # back to globbing all only when no active IP is resolvable (e.g. some
    # headless runs that do not set ATLAS_ACTIVE_IP).
    active_ip = (active_ip_name() or "").strip()
    if active_ip:
        cand = Path(root) / active_ip / "ontology" / "runs" / "active_run.json"
        actives = [cand] if cand.is_file() else []
    else:
        try:
            actives = sorted(Path(root).glob("*/ontology/runs/active_run.json"))
        except OSError:
            return ""
    blocks: List[str] = []
    for active in actives:
        try:
            meta = _json.loads(active.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        run_id = str((meta or {}).get("run_id") or "").strip()
        if not run_id:
            continue
        try:
            ip = active.parents[2].name
        except IndexError:
            ip = ""
        state_path = active.parent / run_id / "run_state.json"
        try:
            state = _json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if str((state or {}).get("status") or "").lower() in _OAG_RUN_DONE_STATUSES:
            continue
        prompt_block = str(((state or {}).get("next_action") or {}).get("prompt_block") or "").strip()
        if prompt_block:
            blocks.append(f"[ip={ip}]\n{prompt_block}")
    if not blocks:
        return ""
    body = "\n\n".join(blocks)
    if len(body) > _OAG_CONTEXT_MAX:
        body = body[:_OAG_CONTEXT_MAX] + "\n…(truncated)"
    return f"{OAG_RUN_CONTEXT_START}\n{body}\n{OAG_RUN_CONTEXT_END}"


def active_workflow_name() -> Optional[str]:
    """Resolve the active workflow name from Atlas/workspace environment."""
    session = (os.environ.get("ATLAS_ACTIVE_SESSION") or "").strip("/")
    parts = [part for part in session.split("/") if part]
    if len(parts) >= 3:
        return parts[-1]
    workspace = (os.environ.get("ACTIVE_WORKSPACE") or "").strip()
    return workspace or None


def active_ip_name() -> Optional[str]:
    """Resolve the active IP name from Atlas/workspace environment."""
    ip = (os.environ.get("ATLAS_ACTIVE_IP") or "").strip()
    if ip:
        return ip
    ip_root = (os.environ.get("ATLAS_IP_ROOT") or "").strip()
    if ip_root:
        return Path(ip_root).expanduser().name or None
    session = (os.environ.get("ATLAS_ACTIVE_SESSION") or "").strip("/")
    parts = [part for part in session.split("/") if part]
    if len(parts) >= 2:
        return parts[-2]
    return None


def build_memory_override(memory_system: Any, workflow: Optional[str] = None) -> str:
    """Build the durable memory rule block injected into the system prompt."""
    if memory_system is None:
        return ""
    effective_memory = memory_system
    try:
        if hasattr(memory_system, "for_active_user"):
            effective_memory = memory_system.for_active_user()
    except Exception:
        effective_memory = memory_system
    workflow_name = workflow if workflow is not None else active_workflow_name()
    try:
        memory_context = effective_memory.format_all_for_prompt(workflow=workflow_name)
    except TypeError:
        memory_context = effective_memory.format_all_for_prompt()
    if not memory_context:
        return ""

    scope = workflow_name or "global"
    user_scope = getattr(effective_memory, "user", "") or "global"
    return "\n".join([
        MEMORY_OVERRIDE_START,
        "Treat these durable memory entries as user/workflow rules for the active session.",
        "Conflict rule: newer explicit user messages in the active conversation override stored memory.",
        f"User memory scope: {user_scope}",
        f"Active workflow scope: {scope}",
        "",
        memory_context,
        MEMORY_OVERRIDE_END,
    ])


def _strip_memory_block(prompt: str, start_marker: str, end_marker: str) -> str:
    text = prompt or ""
    while True:
        start = text.find(start_marker)
        if start < 0:
            return text.strip()
        end = text.find(end_marker, start)
        if end < 0:
            return text.strip()
        end += len(end_marker)
        text = (text[:start] + text[end:]).strip()


def strip_memory_override(prompt: str) -> str:
    """Remove previously injected memory blocks so rebuilt prompts do not duplicate them."""
    text = _strip_memory_block(prompt, MEMORY_OVERRIDE_START, MEMORY_OVERRIDE_END)
    return _strip_memory_block(
        text,
        LEGACY_MEMORY_OVERRIDE_START,
        LEGACY_MEMORY_OVERRIDE_END,
    )


def _memory_insert_index(prompt: str) -> int:
    """Find the first rule-section boundary so memory follows the system prompt."""
    candidates: List[int] = []
    for marker in MEMORY_INSERT_MARKERS:
        marker_at_start = marker.lstrip("\n")
        if prompt.startswith(marker_at_start):
            candidates.append(0)
        found = prompt.find(marker)
        if found >= 0:
            candidates.append(found)
    return min(candidates) if candidates else -1


def apply_memory_override(prompt: str, memory_system: Any, workflow: Optional[str] = None) -> str:
    """Insert a fresh memory rule block after the system prompt and before rules."""
    base = strip_memory_override(prompt)
    override = build_memory_override(memory_system, workflow=workflow)
    if not override:
        return base
    if not base:
        return override
    insert_at = _memory_insert_index(base)
    if insert_at < 0:
        return base.rstrip() + "\n\n" + override
    if insert_at == 0:
        return override + "\n\n" + base.lstrip()
    return base[:insert_at].rstrip() + "\n\n" + override + "\n\n" + base[insert_at:].lstrip()


# ---------------------------------------------------------------------------
# _build_system_prompt_str
# ---------------------------------------------------------------------------

def _build_system_prompt_str(**kwargs) -> str:
    """Wrapper around build_system_prompt that always returns a string."""
    sp = build_system_prompt(**kwargs)
    if isinstance(sp, dict):
        return (sp.get("static", "") + "\n\n" + sp.get("dynamic", "")).strip()
    return sp


# ---------------------------------------------------------------------------
# build_system_prompt
# ---------------------------------------------------------------------------

def build_system_prompt(
    messages: Optional[List[Dict[str, Any]]] = None,
    allowed_tools: Optional[Set[str]] = None,
    agent_mode: Optional[str] = None,
    context: Optional[PromptContext] = None,
    cfg=None,
    build_base_fn: Optional[Callable] = None,
    load_skills_fn: Optional[Callable] = None,
    llm_call_fn: Optional[Callable] = None,
) -> Union[str, Dict[str, str]]:
    """Build system prompt with memory, graph, and procedural guidance.

    Args:
        messages:       Optional message history for semantic search context.
        allowed_tools:  Optional set of allowed tool names (for sub-agents).
        agent_mode:     Optional mode string ("plan", "plan_q", or None).
        context:        PromptContext with optional subsystem references.
        cfg:            Config namespace. Defaults to importing config module.
        build_base_fn:  Callable(allowed_tools, plan_mode, todo_active) -> str.
                        Defaults to cfg.build_base_system_prompt.
        load_skills_fn: Callable(messages, allowed_tools) -> List[str].
                        Defaults to None (skills disabled).
        llm_call_fn:    LLM call function for SmartRAG judge. Defaults to None.

    Returns:
        String prompt (legacy mode) or {"static": ..., "dynamic": ...} (optimized mode).
    """
    if cfg is None:
        import config as cfg  # type: ignore

    if context is None:
        context = PromptContext()

    if build_base_fn is None:
        build_base_fn = cfg.build_base_system_prompt

    # ── Tool filtering ──
    if allowed_tools is None:
        try:
            from core import tools  # type: ignore
            _at: Set[str] = set(tools.AVAILABLE_TOOLS.keys())
        except ImportError:
            _at = set()
    else:
        _at = set(allowed_tools)

    if agent_mode in ('plan', 'plan_q'):
        blocked = getattr(cfg, 'PLAN_MODE_BLOCKED_TOOLS', set())
        _at = {t for t in _at if t not in blocked}
    else:
        # Normal/execution mode: block plan-only tools (todo_write, todo_remove)
        normal_blocked = getattr(cfg, 'NORMAL_MODE_BLOCKED_TOOLS', set())
        _at = {t for t in _at if t not in normal_blocked}

    is_plan = agent_mode in ('plan', 'plan_q')
    todo_active = (
        context.todo_tracker is not None
        and bool(context.todo_tracker.todos)
    )

    base_prompt: str = build_base_fn(
        allowed_tools=_at,
        plan_mode=is_plan,
        todo_active=todo_active,
    )
    injection_enabled = prompt_injection_enabled(cfg)

    # ── cursor-agent Active Mode injection ──
    if getattr(cfg, 'CURSOR_AGENT_ACTIVE_MODE', False):
        _yolo_default = "true" if getattr(cfg, 'CURSOR_AGENT_YOLO', False) else "false"
        _cursor_block = f"""
## CURSOR AGENT ACTIVE MODE

You are operating in **Cursor Agent Active Mode**. Delegate most execution tasks to the `cursor_agent` tool, which has full access to files, shell, and code editing.

**Delegation rules:**
- ANY task involving reading multiple files, code analysis, refactoring, writing/editing files, running tests/commands → use `cursor_agent`
- Keep for yourself: todo tracking (`todo_write`, `todo_update`), orchestration, planning, summarizing results
- Set `yolo="true"` when the task modifies files or runs shell commands
- Set `yolo="false"` for read-only analysis

**Workflow pattern:**
1. `todo_write` to plan the tasks
2. `cursor_agent(task="...", yolo="{_yolo_default}")` to execute each task
3. `todo_update` to mark tasks complete based on cursor-agent's result
4. Summarize the outcome for the user

**cursor_agent usage:**
```
Action: cursor_agent(task="<detailed task description with file paths and goals>", yolo="{_yolo_default}")
```

Write detailed tasks — include file paths, what to change, and expected outcome. cursor-agent reads context from the workspace automatically.
"""
        base_prompt = base_prompt + "\n" + _cursor_block.strip()

    if getattr(cfg, 'DEBUG_MODE', False) and messages:
        try:
            from lib.display import Color  # type: ignore
            print(Color.system("[PROMPT] Building system prompt with context..."))
            print(Color.system(f"[PROMPT]   Messages in history: {len(messages)}"))
        except ImportError:
            pass

    # ── Dynamic context ──
    dynamic_context = ""
    ctx = context

    has_optional = (
        injection_enabled
        and (
            ctx.memory_system is not None
            or ctx.graph_lite is not None
            or ctx.procedural_memory is not None
            or getattr(cfg, 'ENABLE_SKILL_SYSTEM', False)
            or getattr(cfg, 'ENABLE_PROJECT_WIKI_CONTEXT', True)
        )
    )

    if has_optional:
        context_parts: List[str] = []

        # Memory is injected into the static system prompt below, not as a
        # normal dynamic section. Keep the debug signal here.
        if ctx.memory_system is not None:
            memory_context = build_memory_override(ctx.memory_system)
            if memory_context and getattr(cfg, 'DEBUG_MODE', False):
                _debug_memory(cfg, ctx.memory_system)

        # Procedural guidance
        if (
            ctx.procedural_memory is not None
            and getattr(cfg, 'PROCEDURAL_INJECT_GUIDANCE', False)
            and messages
        ):
            guidance = _build_procedural_guidance(cfg, ctx.procedural_memory, messages)
            if guidance:
                context_parts.append(guidance)

        # Graph knowledge
        if ctx.graph_lite is not None and messages:
            graph_ctx = _build_graph_context(cfg, ctx.graph_lite, messages)
            if graph_ctx:
                context_parts.append(graph_ctx)

        # Project wiki push context
        if getattr(cfg, 'ENABLE_PROJECT_WIKI_CONTEXT', True):
            wiki_ctx = _build_project_wiki_context(cfg, messages)
            if wiki_ctx:
                context_parts.append(wiki_ctx)

        # Smart RAG
        if getattr(cfg, 'ENABLE_SMART_RAG', False) and messages:
            rag_ctx = _build_rag_context(cfg, ctx.hybrid_rag, messages, llm_call_fn)
            if rag_ctx:
                context_parts.append(rag_ctx)

        # Active skills
        if getattr(cfg, 'ENABLE_SKILL_SYSTEM', False) and messages and load_skills_fn is not None:
            skill_ctx = _build_skill_context(cfg, load_skills_fn, messages, allowed_tools)
            if skill_ctx:
                context_parts.append(skill_ctx)

        if context_parts:
            dynamic_context = "\n\n".join(context_parts)
            if getattr(cfg, 'DEBUG_MODE', False) and messages:
                _debug_summary(cfg, base_prompt, dynamic_context, context_parts)

    # ── Return format ──
    if injection_enabled and ctx.memory_system is not None:
        base_prompt = apply_memory_override(base_prompt, ctx.memory_system)

    # ── OAG mode: append the project's AGENTS.md (+ .codex/rules) to the STATIC
    # system prompt as a one-time rule block — NOT the per-turn dynamic context.
    # These are static project rules, so they belong in the cached system prompt
    # (sent/cached once), not re-sent every turn. Independent of prompt-injection:
    # OAG mode = follow this project's agent rules and drive its .codex pack.
    if oag_mode_enabled(cfg):
        oag_ctx = _build_oag_agents_context(cfg)
        if oag_ctx:
            base_prompt = base_prompt + "\n\n" + oag_ctx
        # L2: the normal skill block (above) is gated behind prompt-injection; in
        # OAG mode (injection is usually off) activate the OAG workflow skill here
        # too, on demand, so its per-stage flow rides along when relevant.
        if (not injection_enabled and getattr(cfg, 'ENABLE_SKILL_SYSTEM', False)
                and messages and load_skills_fn is not None):
            oag_skill = _build_skill_context(cfg, load_skills_fn, messages, allowed_tools)
            if oag_skill:
                dynamic_context = (dynamic_context + "\n\n" + oag_skill) if dynamic_context else oag_skill
        # L3: active-run next-action is DYNAMIC (changes each step) → goes in the
        # per-turn dynamic context, not the cached static prompt. Drives the agent
        # to keep following the OAG run (context-inject + soft stop-gate).
        oag_run = _build_oag_run_context(cfg)
        if oag_run:
            dynamic_context = (dynamic_context + "\n\n" + oag_run) if dynamic_context else oag_run

    if getattr(cfg, 'CACHE_OPTIMIZATION_MODE', 'legacy') == "optimized":
        return {"static": base_prompt, "dynamic": dynamic_context}
    else:
        if dynamic_context:
            return base_prompt + "\n\n" + dynamic_context
        return base_prompt


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _debug_memory(cfg, memory_system) -> None:
    try:
        from lib.display import Color  # type: ignore
        prefs = memory_system.list_preferences()
        project_ctx = memory_system.list_project_context()
        print(Color.system("[PROMPT] ✅ Memory loaded:"))
        if prefs:
            print(Color.system(f"[PROMPT]     📋 Preferences ({len(prefs)} items):"))
            for k, v in prefs.items():
                vs = str(v)[:50] + "..." if len(str(v)) > 50 else str(v)
                print(Color.system(f"[PROMPT]        {k}: {vs}"))
        if project_ctx:
            print(Color.system(f"[PROMPT]     🗂️ Project Context ({len(project_ctx)} items):"))
            for k, v in project_ctx.items():
                vs = str(v)[:50] + "..." if len(str(v)) > 50 else str(v)
                print(Color.system(f"[PROMPT]        {k}: {vs}"))
    except ImportError:
        pass


def _build_procedural_guidance(cfg, procedural_memory, messages) -> str:
    user_msgs = [m for m in messages if m.get("role") == "user"]
    if not user_msgs:
        return ""
    current_task = user_msgs[-1].get("content", "")[:200]
    try:
        similar = procedural_memory.retrieve(
            current_task,
            limit=getattr(cfg, 'PROCEDURAL_RETRIEVE_LIMIT', 3),
        )
        threshold = getattr(cfg, 'PROCEDURAL_SIMILARITY_THRESHOLD', 0.5)
        similar = [(s, t) for s, t in similar if s >= threshold]
        if not similar:
            return ""

        guidance = "=== PAST EXPERIENCE ===\n\nYou have similar past experiences that may help:\n\n"
        for i, (score, traj) in enumerate(similar, 1):
            guidance += f"{i}. Task: {traj.task_description}\n"
            guidance += f"   Outcome: {traj.outcome.upper()} ({traj.iterations} iterations)\n"
            if traj.outcome == "success":
                guidance += "   Successful approach:\n"
                for action in traj.actions[:3]:
                    guidance += f"     - {action.tool}({action.args[:50]}...)\n"
            elif traj.errors_encountered:
                guidance += f"   Errors encountered: {', '.join(traj.errors_encountered[:2])}\n"
            guidance += "\n"
        guidance += "Use this experience to avoid past mistakes and follow proven approaches.\n"
        guidance += "=====================\n"

        for _, traj in similar:
            procedural_memory.increment_usage(traj.id)

        return guidance
    except Exception:
        return ""


def _project_wiki_graph_path(cfg) -> Optional[Path]:
    explicit = (
        getattr(cfg, "PROJECT_WIKI_GRAPH_PATH", "")
        or os.environ.get("ATLAS_PROJECT_WIKI_GRAPH", "")
    )
    if explicit:
        return Path(os.path.expandvars(explicit)).expanduser()

    root_override = (
        getattr(cfg, "PROJECT_WIKI_ROOT", "")
        or os.environ.get("ATLAS_PROJECT_WIKI_ROOT", "")
    )
    if root_override:
        root = Path(os.path.expandvars(root_override)).expanduser()
        return root / "_graph.json" if root.name == "wiki" else root / "doc" / "wiki" / "_graph.json"

    candidates = [
        os.environ.get("COMMON_AI_AGENT_HOME", ""),
        os.environ.get("ATLAS_WORKFLOW_ROOT", ""),
        os.environ.get("ATLAS_PROJECT_ROOT", ""),
        os.getcwd(),
        str(Path(__file__).resolve().parents[1]),
    ]
    for raw in candidates:
        if not raw:
            continue
        root = Path(os.path.expandvars(raw)).expanduser()
        graph_path = root / "doc" / "wiki" / "_graph.json"
        if graph_path.is_file():
            return graph_path
    return Path(__file__).resolve().parents[1] / "doc" / "wiki" / "_graph.json"


def _load_project_wiki_graph(cfg) -> Optional[Dict[str, Any]]:
    graph_path = _project_wiki_graph_path(cfg)
    if graph_path is None or not graph_path.is_file():
        return None
    try:
        graph = json.loads(graph_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return graph if isinstance(graph, dict) else None


def _split_project_wiki_terms(text: str) -> List[str]:
    terms: List[str] = []
    for term in PROJECT_WIKI_TERM_RE.split((text or "").lower().replace("_", "-")):
        if len(term) >= 2 and term not in PROJECT_WIKI_STOPWORDS and term not in terms:
            terms.append(term)
    return terms


def _stage_key(workflow: Optional[str]) -> str:
    return (workflow or "").strip().lower().replace("_", "-")


def _node_text(node: Dict[str, Any], *fields: str) -> str:
    values: List[str] = []
    for field_name in fields:
        value = node.get(field_name)
        if isinstance(value, list):
            values.extend(str(item) for item in value)
        elif value is not None:
            values.append(str(value))
    return " ".join(values).replace("_", "-").lower()


def _score_project_wiki_node(
    node: Dict[str, Any],
    *,
    stage_tags: List[str],
    query_terms: List[str],
    active_ip: str,
) -> int:
    tags = [str(tag).lower().replace("_", "-") for tag in node.get("tags") or []]
    identifiers = _node_text(node, "id", "title", "path", "type")
    summary = _node_text(node, "summary")
    score = 0

    for tag in stage_tags:
        tag_l = tag.lower().replace("_", "-")
        if tag_l in tags:
            score += 30
        if tag_l and tag_l in identifiers:
            score += 14
        if tag_l and tag_l in summary:
            score += 4

    for term in query_terms:
        if term in identifiers:
            score += 6
        if term in " ".join(tags):
            score += 5
        if term in summary:
            score += 2

    if active_ip:
        ip_l = active_ip.lower().replace("_", "-")
        if ip_l in identifiers:
            score += 10
        if ip_l in summary:
            score += 4

    if node.get("type") in {"rule", "runbook", "process"} and score:
        score += 2
    return score


def _build_project_wiki_context(cfg, messages) -> str:
    workflow = active_workflow_name()
    stage = _stage_key(workflow)
    active_ip = active_ip_name() or ""
    user_msgs = [m for m in (messages or []) if m.get("role") == "user"]
    recent_topic = str(user_msgs[-1].get("content", ""))[:500] if user_msgs else ""
    stage_tags = list(PROJECT_WIKI_STAGE_TAGS.get(stage, []))
    if stage and stage not in stage_tags:
        stage_tags.insert(0, stage)
    query_terms = _split_project_wiki_terms(" ".join([active_ip, stage, recent_topic]))
    if not stage_tags and not query_terms:
        return ""

    graph = _load_project_wiki_graph(cfg)
    if not graph:
        return ""
    nodes = [node for node in graph.get("nodes") or [] if isinstance(node, dict)]
    if not nodes:
        return ""

    scored: List[tuple[int, Dict[str, Any]]] = []
    for node in nodes:
        score = _score_project_wiki_node(
            node,
            stage_tags=stage_tags,
            query_terms=query_terms,
            active_ip=active_ip,
        )
        if score > 0:
            scored.append((score, node))
    if not scored:
        return ""

    try:
        limit = int(getattr(cfg, "PROJECT_WIKI_CONTEXT_LIMIT", 5))
    except Exception:
        limit = 5
    limit = max(1, min(8, limit))
    scored.sort(
        key=lambda item: (
            item[0],
            str(item[1].get("updated") or ""),
            str(item[1].get("id") or ""),
        ),
        reverse=True,
    )
    included = scored[:limit]

    scope_bits = []
    if stage:
        scope_bits.append(f"workflow={stage}")
    if active_ip:
        scope_bits.append(f"ip={active_ip}")
    scope = " · ".join(scope_bits) if scope_bits else "message query"
    lines = [
        PROJECT_WIKI_CONTEXT_START,
        f"Relevant project wiki pages surfaced from doc/wiki/_graph.json ({scope}).",
    ]
    for score, node in included:
        node_id = str(node.get("id") or "?")
        path = str(node.get("path") or "")
        summary = " ".join(str(node.get("summary") or "").split())
        if len(summary) > 220:
            summary = summary[:219].rsplit(" ", 1)[0] + "..."
        line = f"- [[{node_id}]]"
        if path:
            line += f" ({path})"
        if summary:
            line += f" - {summary}"
        line += f" [score={score}]"
        lines.append(line)
    lines.append("Open full pages with wiki_query or direct file reads before acting on matching workflow details.")
    lines.append(PROJECT_WIKI_CONTEXT_END)
    return "\n".join(lines)


def _build_graph_context(cfg, graph_lite, messages) -> str:
    user_msgs = [m for m in messages if m.get("role") == "user"]
    if not user_msgs:
        return ""
    recent_topic = user_msgs[-1].get("content", "")[:200]
    try:
        results = graph_lite.graph_rag_search(
            recent_topic,
            limit=getattr(cfg, 'GRAPH_SEARCH_LIMIT', 5),
            hop=1,
        )
        if not results:
            return ""

        threshold = getattr(cfg, 'GRAPH_SIMILARITY_THRESHOLD', 0.5)
        graph_context = "=== RELEVANT KNOWLEDGE ===\n\n"
        included = []
        for score, node in results:
            if score > threshold:
                desc = (
                    node.data.get("content")
                    or node.data.get("description")
                    or node.data.get("name", "")
                )
                if desc:
                    if len(desc) > 200:
                        desc = desc[:200] + "..."
                    graph_context += f"- {node.type}: {desc}\n"
                    included.append((score, node))

        graph_context += "\n=====================\n"
        return graph_context if included else ""
    except Exception:
        return ""


def _build_rag_context(cfg, hybrid_rag, messages, llm_call_fn) -> str:
    user_msgs = [m for m in messages if m.get("role") == "user"]
    if not user_msgs:
        return ""
    recent_query = user_msgs[-1].get("content", "")[:200]
    try:
        from core.smart_rag import SmartRAGDecision  # type: ignore
        from core.rag_db import get_rag_db  # type: ignore

        smart_rag = SmartRAGDecision(
            high_threshold=getattr(cfg, 'SMART_RAG_HIGH_THRESHOLD', 0.8),
            low_threshold=getattr(cfg, 'SMART_RAG_LOW_THRESHOLD', 0.4),
            top_k=getattr(cfg, 'SMART_RAG_TOP_K', 3),
            debug=getattr(cfg, 'DEBUG_MODE', False),
        )

        def rag_search_func(query, limit=3):
            if hybrid_rag:
                return hybrid_rag.search(query, limit=limit)
            return get_rag_db().search(query, limit=limit)

        llm_judge = llm_call_fn if getattr(cfg, 'SMART_RAG_LLM_JUDGE', False) else None
        should_use, rag_results = smart_rag.decide(recent_query, rag_search_func, llm_judge)

        if should_use and rag_results:
            return smart_rag.format_context(rag_results, max_chars=2000)
    except (ImportError, Exception):
        pass
    return ""


def _build_skill_context(cfg, load_skills_fn, messages, allowed_tools) -> str:
    try:
        skill_prompts = load_skills_fn(messages, allowed_tools)
        if skill_prompts:
            section = "=== ACTIVE SKILLS ===\n\nThe following domain expertise is active:\n\n"
            section += "\n\n".join(skill_prompts)
            section += "\n\n====================="
            return section
    except Exception as e:
        try:
            from lib.display import Color  # type: ignore
            print(Color.warning(f"[PROMPT] ⚠️ Error injecting skills: {e}"))
        except ImportError:
            pass
    return ""


def _debug_summary(cfg, base_prompt, dynamic_context, context_parts) -> None:
    try:
        from lib.display import Color  # type: ignore
        total_chars = len(base_prompt) + len(dynamic_context)
        estimated_tokens = total_chars // 4
        print(Color.system(f"[PROMPT] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"))
        print(Color.system(f"[PROMPT] Build complete: {len(context_parts)} sections, ~{estimated_tokens:,} tokens"))
    except ImportError:
        pass
