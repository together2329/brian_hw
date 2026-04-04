"""
System prompt construction for the ReAct agent.

Extracted from src/main.py. All global state (memory_system, graph_lite, etc.)
is passed via PromptContext for testability and clean dependency injection.

Public API:
  PromptContext          — dataclass bundling all optional subsystem references
  build_system_prompt()  — main builder
  _build_system_prompt_str()  — always-string wrapper
"""
import os
from dataclasses import dataclass, field
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
        ctx.memory_system is not None
        or ctx.graph_lite is not None
        or ctx.procedural_memory is not None
        or getattr(cfg, 'ENABLE_SKILL_SYSTEM', False)
    )

    if has_optional:
        context_parts: List[str] = []

        # Memory preferences
        if ctx.memory_system is not None:
            memory_context = ctx.memory_system.format_all_for_prompt()
            if memory_context:
                context_parts.append(memory_context)
                if getattr(cfg, 'DEBUG_MODE', False):
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
