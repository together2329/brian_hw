import os
import sys
from pathlib import Path


def _apply_workspace_env_early():
    """
    Parse -w/--workspace from sys.argv BEFORE load_env_file() runs,
    so workspace.json [env] overrides have priority over .env/.config files.
    Only sets env vars that are not already set in the shell environment.
    """
    workspace_name = None
    argv = sys.argv[1:]
    for i, arg in enumerate(argv):
        if arg in ('-w', '--workspace') and i + 1 < len(argv):
            workspace_name = argv[i + 1]
            break
        if arg.startswith('--workspace='):
            workspace_name = arg.split('=', 1)[1]
            break
    if not workspace_name:
        return

    # Locate workflow directory relative to this file (src/ → .. → workflow/)
    workflow_root = Path(__file__).parent.parent.parent / "new_feature" / "workflow"
    ws_json = workflow_root / workspace_name / "workspace.json"
    if not ws_json.exists():
        # Fallback: look for workflow/ next to common_ai_agent
        workflow_root2 = Path(__file__).parent.parent / "workflow"
        ws_json = workflow_root2 / workspace_name / "workspace.json"
    if not ws_json.exists():
        return

    try:
        import json
        data = json.loads(ws_json.read_text(encoding="utf-8"))
        env_overrides = data.get("env", {})
        for key, value in env_overrides.items():
            if key and value is not None and key not in os.environ:
                os.environ[key] = str(value)
        # Signal which workspace is active
        if "ACTIVE_WORKSPACE" not in os.environ:
            os.environ["ACTIVE_WORKSPACE"] = workspace_name
    except Exception:
        pass


_apply_workspace_env_early()

# Load .env file if it exists
def load_env_file():
    # Load config files in order of priority (first loaded takes precedence)
    # .config has highest priority, then .env files
    search_paths = [
        Path.home() / '.config' / 'common_ai_agent' / 'config',  # ~/.config/common_ai_agent/config (highest priority)
        Path(__file__).parent.parent / '.config',  # common_ai_agent/.config
        Path(__file__).parent.parent / '.env',  # common_ai_agent/.env
        Path(__file__).parent / '.env',  # src/.env
    ]

    for env_path in search_paths:
        if env_path.exists():
            with open(env_path, encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Skip comments and empty lines
                    if not line or line.startswith('#'):
                        continue
                    # Parse KEY=VALUE
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()

                        # Remove inline comments (e.g., "value    # comment")
                        if '#' in value:
                            value = value.split('#')[0].strip()

                        # Only set if not already in environment
                        if key and value and key not in os.environ:
                            os.environ[key] = value
            # Continue loading other files (no break)

load_env_file()

# Configuration for the Internal LLM
# Users can override these via environment variables

# ============================================================
# OpenAI ChatGPT API Configuration (기본 설정)
# ============================================================
BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
API_KEY = os.getenv("LLM_API_KEY", "your-openai-api-key-here")
MODEL_NAME = os.getenv("LLM_MODEL_NAME", "gpt-4o-mini")
SSL_VERIFY = os.getenv("SSL_VERIFY", "true").lower() != "false"  # set false for corporate proxy
CUSTOM_PRICE = os.getenv("CUSTOM_PRICE", "false").lower() == "true"  # GLM flat $1/$0/$1 per 1M when true
PRIMARY_MODEL = os.getenv("PRIMARY_MODEL", MODEL_NAME)

# ============================================================
# Azure OpenAI Configuration
# ============================================================
# Set LLM_PROVIDER=azure to enable Azure OpenAI mode.
# Required env vars when using Azure:
#   AZURE_OPENAI_ENDPOINT  — e.g. https://my-resource.openai.azure.com
#   AZURE_OPENAI_API_KEY   — your Azure API key
#   AZURE_OPENAI_DEPLOYMENT — deployment name (e.g. gpt-4o-mini-deploy)
#   AZURE_OPENAI_API_VERSION — API version (default: 2024-06-01)
# ============================================================
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()  # openai | azure | anthropic | openrouter | zai
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2025-04-01-preview")

# Responses API mode: uses /responses endpoint instead of /chat/completions.
# Required for Azure gpt-5-codex models and OpenAI codex models.
# When enabled, transforms messages→input, system→instructions, max_tokens→max_output_tokens.
USE_RESPONSES_API = os.getenv("USE_RESPONSES_API", "false").lower() in ("true", "1", "yes")

# Force Chat Completions API for gpt-5* models (opt-out of Responses API).
# When true, models matching *gpt*5* use /chat/completions even if they would
# otherwise be routed to /responses (e.g. gpt-5-codex, gpt-5.1-codex).
FORCE_CHAT_COMPLETIONS_GPT5 = os.getenv("FORCE_CHAT_COMPLETIONS_GPT5", "false").lower() in ("true", "1", "yes")

# Azure auto-detection: if LLM_PROVIDER=azure, override BASE_URL/API_KEY/MODEL_NAME
if LLM_PROVIDER == "azure" and AZURE_OPENAI_ENDPOINT:
    if not AZURE_OPENAI_API_KEY:
        AZURE_OPENAI_API_KEY = API_KEY  # fallback to LLM_API_KEY
    if not AZURE_OPENAI_DEPLOYMENT:
        AZURE_OPENAI_DEPLOYMENT = MODEL_NAME  # fallback to LLM_MODEL_NAME
    # Azure uses a different URL pattern — llm_client.py builds the full path
    BASE_URL = AZURE_OPENAI_ENDPOINT.rstrip("/")
    API_KEY = AZURE_OPENAI_API_KEY
    MODEL_NAME = AZURE_OPENAI_DEPLOYMENT

# ============================================================
# cursor-agent Backend Configuration
# ============================================================
CURSOR_AGENT_ENABLE = os.getenv("CURSOR_AGENT_ENABLE", "false").lower() == "true"
CURSOR_AGENT_MODEL = os.getenv("CURSOR_AGENT_MODEL", "auto")
CURSOR_AGENT_YOLO = os.getenv("CURSOR_AGENT_YOLO", "false").lower() == "true"
CURSOR_AGENT_MODE = os.getenv("CURSOR_AGENT_MODE", "")       # "ask" | "plan" | "" (full agent)
CURSOR_AGENT_WORKSPACE = os.getenv("CURSOR_AGENT_WORKSPACE", "")  # path; empty = cwd
# Active mode: instructs the primary LLM to delegate most execution to cursor_agent tool
CURSOR_AGENT_ACTIVE_MODE = os.getenv("CURSOR_AGENT_ACTIVE_MODE", "false").lower() == "true"

# When cursor-agent is the backend, force ReAct text mode so the system prompt
# includes Action:/Observation: instructions that cursor-agent can follow.
# cursor-agent does not support receiving an OpenAI-style tools JSON schema.
if CURSOR_AGENT_ENABLE:
    os.environ["ENABLE_NATIVE_TOOL_CALLS"] = "false"

# ============================================================
# OpenRouter Configuration (주석 처리됨)
# ============================================================
# BASE_URL = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")
# API_KEY = os.getenv("LLM_API_KEY", "sk-or-v1-...")
# MODEL_NAME = os.getenv("LLM_MODEL_NAME", "meta-llama/llama-3.3-70b-instruct:free")

# Rate limiting
# ──────────────────────────────────────────────────────────────────────────────
# TPM (Tokens Per Minute): max tokens allowed in a 60s sliding window.
#   Set to 0 to disable. Typical values:
#     Free tier:  20,000   |   Pro tier:  200,000   |   Enterprise: 2,000,000
# RPM (Requests Per Minute): max API calls in a 60s sliding window.
#   Set to 0 to disable. Typical values:
#     Free tier:  10       |   Pro tier:  60         |   Enterprise: 500
#
# These replace the old RATE_LIMIT_DELAY (fixed delay between calls).
# If both TPM/RPM are 0, falls back to RATE_LIMIT_DELAY behavior.
# ──────────────────────────────────────────────────────────────────────────────
TPM_LIMIT = int(os.getenv("TPM_LIMIT", "0"))
RPM_LIMIT = int(os.getenv("RPM_LIMIT", "0"))

# Legacy: fixed delay (seconds) between API calls. Ignored when TPM/RPM > 0.
# Set to 0 to disable.
RATE_LIMIT_DELAY = float(os.getenv("RATE_LIMIT_DELAY", "5"))

# MCP (Model Context Protocol) integration
# Set ENABLE_MCP=true and configure servers in .mcp.json
ENABLE_MCP      = os.getenv("ENABLE_MCP", "false").lower() in ("true", "1", "yes")
MCP_CONFIG_PATH = os.getenv("MCP_CONFIG_PATH", ".mcp.json")
# Secrets for MCP servers — referenced as ${VAR} in .mcp.json env blocks
MCP_Z_AI_API_KEY = os.getenv("MCP_Z_AI_API_KEY", "")

# Maximum number of ReAct loop iterations
# Increased to allow for error recovery attempts (3 retries per error)
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "100"))

# API timeout in seconds (how long to wait for API response)
# Set to 0 to disable timeout (not recommended)
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "600"))

# Streaming timeout: per-read socket timeout for streaming requests.
# Must be higher than API_TIMEOUT — reasoning models (GLM, DeepSeek) can think
# silently for minutes before emitting the first token, causing socket.timeout.
STREAM_API_TIMEOUT = int(os.getenv("STREAM_API_TIMEOUT", "1800"))

# Timeout for non-streaming requests (full response must arrive within this time)
NONSTREAM_API_TIMEOUT = int(os.getenv("NONSTREAM_API_TIMEOUT", "1800"))

# Maximum output tokens per LLM response (0 = no limit)
MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", "32000"))

# Maximum reasoning/thinking tokens (GLM, DeepSeek etc.).
# For reasoning models, this EXPANDS the max_tokens budget so reasoning
# tokens don't eat into the visible content budget:
#   effective max_tokens = MAX_OUTPUT_TOKENS + MAX_REASONING_TOKENS
# Set to 0 to disable the expansion.
# Recommended: 8000-16000 to give the model room to think AND produce content.
MAX_REASONING_TOKENS = int(os.getenv("MAX_REASONING_TOKENS", "0"))

# Reasoning effort for Responses API models (GPT-5.1, o1, o3, o4).
# Controls how much compute the model spends "thinking" before responding.
# Options: low | medium | high
# Default: medium (good balance of quality and speed/cost)
# - low:    fastest, cheapest, good for simple tasks
# - medium: balanced (recommended for coding agents)
# - high:   deepest reasoning, slowest, most expensive (for complex problems)
REASONING_EFFORT = os.getenv("REASONING_EFFORT", "medium").lower()

# Save conversation history to file
SAVE_HISTORY = os.getenv("SAVE_HISTORY", "true").lower() in ("true", "1", "yes")
HISTORY_FILE = os.getenv("HISTORY_FILE", "conversation_history.json")
TODO_FILE = os.getenv("TODO_FILE", "current_todos.json")
TODO_ERROR_FILE = os.getenv("TODO_ERROR_FILE", "current_todos_error.json")
COST_FILE      = os.getenv("COST_FILE", "")                   # .session/<project>/cost.json

# Session directory layout (set by _setup_session at runtime)
SESSION_DIR = os.getenv("SESSION_DIR", "")            # .session/<project_name>
ACTIVE_PROJECT = os.getenv("ACTIVE_PROJECT", "default")  # current active project name

# Step-by-step execution mode
STEP_BY_STEP_MODE = os.getenv("STEP_BY_STEP_MODE", "false").lower() in ("true", "1", "yes")

# Execution mode: agent (default loop), chat (limited iterations), step (pause after each action)
EXECUTION_MODE = os.getenv("EXECUTION_MODE", "agent")  # agent | chat | step
# Chat mode iteration limit: 0=respond only (no tools), N=run N ReAct iterations with tools
CHAT_MAX_ITERATIONS = int(os.getenv("CHAT_MAX_ITERATIONS", "1"))

# Debug mode - show detailed parsing and execution info
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() in ("true", "1", "yes")

# Performance tracking - print timing for each phase of the ReAct loop
PERF_TRACKING = os.getenv("PERF_TRACKING", "false").lower() in ("true", "1", "yes")

# Show token usage stats after each LLM response (✽ in X · out Y · sum Z tokens)
SHOW_TOKEN_STATS = os.getenv("SHOW_TOKEN_STATS", "true").lower() in ("true", "1", "yes")
# Show token stats in sidebar (TUI only); hides them from main log when true
SHOW_TOKEN_STATS_SIDEBAR = os.getenv("SHOW_TOKEN_STATS_SIDEBAR", "true").lower() in ("true", "1", "yes")

# Include LLM reasoning in message context (stored in history for next turn)
REASONING_IN_CONTEXT = os.getenv("REASONING_IN_CONTEXT", "false").lower() in ("true", "1", "yes")

# Display LLM reasoning tokens in terminal (dim text before content)
REASONING_DISPLAY = os.getenv("REASONING_DISPLAY", "true").lower() in ("true", "1", "yes")

# Enable streaming mode (token-by-token). false = wait for full response then display.
# Non-streaming cleanly separates reasoning/content but shows nothing until complete.
ENABLE_STREAMING = os.getenv("ENABLE_STREAMING", "true").lower() in ("true", "1", "yes")

# Enable rich Markdown rendering for LLM textual output (Textual UI).
# Disable to stream raw text line-by-line for maximum performance.
# Default: true
ENABLE_MARKDOWN_RENDER = os.getenv("ENABLE_MARKDOWN_RENDER", "true").lower() in ("true", "1", "yes")

# Streaming token delay (milliseconds). 0 = disabled. Use for debugging display issues.
STREAM_TOKEN_DELAY_MS = float(os.getenv("STREAM_TOKEN_DELAY_MS", "0"))

# RAG Debug mode - show detailed RAG search/indexing info
DEBUG_RAG = os.getenv("DEBUG_RAG", "false").lower() in ("true", "1", "yes")

# SubAgent Debug mode - show detailed SubAgent execution info
# Shows: parsing details, error checks, stall detection, tool calls (color-coded)
DEBUG_SUBAGENT = os.getenv("DEBUG_SUBAGENT", "false").lower() in ("true", "1", "yes")

# Context Flow Debug mode - monitor agent context sharing
# Shows: SharedContext updates, agent interactions, efficiency metrics
DEBUG_CONTEXT_FLOW = os.getenv("DEBUG_CONTEXT_FLOW", "false").lower() in ("true", "1", "yes")

# Full Prompt Debug - show complete input messages to LLM
FULL_PROMPT_DEBUG = os.getenv("FULL_PROMPT_DEBUG", "false").lower() in ("true", "1", "yes")

# Limit the number of messages shown in Full Prompt Debug
# If True, only shows the last N messages
FULL_PROMPT_DEBUG_LIMIT_ENABLED = os.getenv("FULL_PROMPT_DEBUG_LIMIT_ENABLED", "true").lower() in ("true", "1", "yes")

# Number of recent messages to show when limiting is enabled
FULL_PROMPT_DEBUG_LIMIT_COUNT = int(os.getenv("FULL_PROMPT_DEBUG_LIMIT_COUNT", "5"))

# Limit the number of lines shown per message in Full Prompt Debug
FULL_PROMPT_DEBUG_LINE_LIMIT_ENABLED = os.getenv("FULL_PROMPT_DEBUG_LINE_LIMIT_ENABLED", "true").lower() in ("true", "1", "yes")

# Number of lines to show per message when limiting is enabled
FULL_PROMPT_DEBUG_LINE_LIMIT_COUNT = int(os.getenv("FULL_PROMPT_DEBUG_LINE_LIMIT_COUNT", "20"))

# Tool Description System (OpenCode Integration)
# When enabled, loads detailed tool descriptions from .txt files
ENABLE_TOOL_DESCRIPTIONS = os.getenv("ENABLE_TOOL_DESCRIPTIONS", "true").lower() in ("true", "1", "yes")

# ============================================================
# Native Tool Call Support (Function Calling)
# ============================================================
# When true: uses structured JSON tool_calls API instead of ReAct text parsing.
ENABLE_NATIVE_TOOL_CALLS = os.getenv("ENABLE_NATIVE_TOOL_CALLS", "false").lower() in ("true", "1", "yes")

# ============================================================
# Type Validation & Linting (Zero-Dependency Features)
# ============================================================
# Enable parameter type validation (always available - uses standard library only)
# Validates tool parameters before execution using type hints
ENABLE_TYPE_VALIDATION = os.getenv("ENABLE_TYPE_VALIDATION", "true").lower() in ("true", "1", "yes")

# Enable automatic linting after file writes (optional - uses external tools if available)
# Checks Python files with compile() + pyflakes, Verilog files with configured simulator
# Falls back gracefully if external tools not installed
ENABLE_LINTING = os.getenv("ENABLE_LINTING", "true").lower() in ("true", "1", "yes")

# pyslang: IEEE 1800-2017 SV parser/linter (pip install pyslang, no binary needed)
# When true AND pyslang is importable, used as primary Verilog linter + AST tools.
# Falls back to VERILOG_SIMULATOR if pyslang not installed or ENABLE_PYSLANG=false.
ENABLE_PYSLANG = os.getenv("ENABLE_PYSLANG", "true").lower() in ("true", "1", "yes")

# Verilog simulator fallback (used when pyslang unavailable or ENABLE_PYSLANG=false)
# Options: "vcs" (default, Synopsys commercial), "iverilog" (open-source), "verilator"
VERILOG_SIMULATOR = os.getenv("VERILOG_SIMULATOR", "vcs")

# Enable automatic git version control (git init + add + commit on write/replace)
GIT_VERSION_CONTROL_ENABLE = os.getenv("GIT_VERSION_CONTROL_ENABLE", "true").lower() in ("true", "1", "yes")
# Commit message verbosity: "simple" | "summary"
GIT_COMMIT_MSG_MODE = os.getenv("GIT_COMMIT_MSG_MODE", "simple")
GIT_COMMIT_SUMMARY_TEMPERATURE = float(os.getenv("GIT_COMMIT_SUMMARY_TEMPERATURE", "0.3"))

# Secondary model: lightweight tasks (git commit summary, spec summarization, etc.)
# Uses same LLM_BASE_URL / LLM_API_KEY — no separate auth needed.
SECONDARY_MODEL = os.getenv("SECONDARY_MODEL", MODEL_NAME)

# Enable LSP integration (optional - requires LSP server installed)
# Uses pylsp, pyright, or jedi-language-server for advanced diagnostics
# Gracefully disabled if no LSP server found
ENABLE_LSP = os.getenv("ENABLE_LSP", "false").lower() in ("true", "1", "yes")

# ============================================================
# Skill System Configuration (Claude Code Style)
# ============================================================
# Enable/Disable skill system (plugin-based domain expertise)
# When enabled, loads domain-specific prompts dynamically based on task context
ENABLE_SKILL_SYSTEM = os.getenv("ENABLE_SKILL_SYSTEM", "true").lower() in ("true", "1", "yes")

# User skills directory (for custom skills)
# Users can add SKILL.md files here for project-specific expertise
SKILLS_DIR = os.getenv("SKILLS_DIR", "~/.common_ai_agent/skills")

# Auto-detect skills based on keywords and file patterns
# If false, skills must be manually activated
SKILL_AUTO_DETECT = os.getenv("SKILL_AUTO_DETECT", "true").lower() in ("true", "1", "yes")

# Activation threshold for skill auto-detection (0.0-1.0)
# Lower = more skills activated, Higher = only highly relevant skills
# Default: 0.15 (sensitive - activates skills with 1-2 keyword matches)
SKILL_ACTIVATION_THRESHOLD = float(os.getenv("SKILL_ACTIVATION_THRESHOLD", "0.15"))

# Tool result preview settings
TOOL_RESULT_PREVIEW_LINES = int(os.getenv("TOOL_RESULT_PREVIEW_LINES", "3"))  # For read_file/read_lines
TOOL_RESULT_PREVIEW_CHARS = int(os.getenv("TOOL_RESULT_PREVIEW_CHARS", "300"))  # For other tools

# Large File Handling
MAX_OBSERVATION_CHARS = int(os.getenv("MAX_OBSERVATION_CHARS", "20000"))  # ~5000 tokens
LARGE_FILE_PREVIEW_LINES = int(os.getenv("LARGE_FILE_PREVIEW_LINES", "100"))  # Number of lines to show in preview

# Context Management
# Token limit for the model context window (0 = no limit, use estimated from chars)
# Set to your model's actual context window size for best results.
MAX_CONTEXT_TOKENS = int(os.getenv("MAX_CONTEXT_TOKENS", "128000"))  # Default: 128K tokens
# Threshold to trigger compression (0.0 to 1.0)
# Default: 0.9 (90% of 128K = ~115K tokens)
# Old value 0.8 was too conservative, causing compression every iteration
COMPRESSION_THRESHOLD = float(os.getenv("COMPRESSION_THRESHOLD", "0.9"))
# Enable/Disable compression
# Default: True
ENABLE_COMPRESSION = os.getenv("ENABLE_COMPRESSION", "true").lower() in ("true", "1", "yes")

# Compression mode: 'single' or 'chunked'
# single: Summarize all old messages in one go (faster, cheaper)
# chunked: Summarize in chunks (better for very long histories)
COMPRESSION_MODE = os.getenv("COMPRESSION_MODE", "single")

# Chunk size for chunked compression (number of messages per chunk)
# Only used when COMPRESSION_MODE=chunked
COMPRESSION_CHUNK_SIZE = int(os.getenv("COMPRESSION_CHUNK_SIZE", "10"))

# Number of recent messages to keep unchanged during compression
# Recommended: 4-15 messages
COMPRESSION_KEEP_RECENT = int(os.getenv("COMPRESSION_KEEP_RECENT", "4"))

# Number of LLM retry attempts on empty/failed response (0 = no retry)
LLM_RETRY_COUNT = int(os.getenv("LLM_RETRY_COUNT", "1"))

# Enable Smart Compression (selective preservation based on importance)
# NOTE: Default changed to "false" - using Traditional Compression for simplicity
# When enabled, preserves critical messages (user preferences, error solutions)
# and only summarizes less important messages
ENABLE_SMART_COMPRESSION = os.getenv("ENABLE_SMART_COMPRESSION", "false").lower() in ("true", "1", "yes")

# ============================================================
# Dynamic Context Pruning Configuration
# ============================================================
# Preemptive compression threshold (0.0 to 1.0)
# Triggers compression earlier to prevent emergency situations
# Default: 0.85 (85% of context limit)
PREEMPTIVE_COMPRESSION_THRESHOLD = float(os.getenv("PREEMPTIVE_COMPRESSION_THRESHOLD", "0.85"))

# Enable turn-based message protection during compression
# When enabled, protects recent N turns instead of N messages
# Default: true (recommended for better conversation continuity)
ENABLE_TURN_PROTECTION = os.getenv("ENABLE_TURN_PROTECTION", "true").lower() in ("true", "1", "yes")

# Number of recent turns to protect from compression
# Only used when ENABLE_TURN_PROTECTION=true
# Default: 3 (protects last 3 user-assistant exchanges)
TURN_PROTECTION_COUNT = int(os.getenv("TURN_PROTECTION_COUNT", "3"))

# ============================================================
# Prompt Caching Configuration
# ============================================================
# Enable prompt caching — works with Anthropic (explicit) and Z.AI/OpenAI (implicit)
# Default: true. Set ENABLE_PROMPT_CACHING=false in .config to disable.
ENABLE_PROMPT_CACHING = os.getenv("ENABLE_PROMPT_CACHING", "true").lower() in ("true", "1", "yes")

# Prompt Caching Optimization Mode
# Options:
#   - "legacy": Single-string system message (current behavior, safe fallback)
#   - "optimized": Multi-block system message (40-50% cost reduction)
# Default: "legacy" (backward compatible)
# NOTE: Only effective when ENABLE_PROMPT_CACHING=true and using Anthropic models
CACHE_OPTIMIZATION_MODE = os.getenv("CACHE_OPTIMIZATION_MODE", "legacy").lower()

# Token Cost Configuration (per 1M tokens, USD)
# Set these in .config to enable cost tracking in the sidebar.
# Example for GLM-5.1: LLM_COST_INPUT_PER_M=0.14 LLM_COST_CACHE_PER_M=0.07 LLM_COST_OUTPUT_PER_M=0.28
LLM_COST_INPUT_PER_M  = float(os.getenv("LLM_COST_INPUT_PER_M",  "0"))
LLM_COST_CACHE_PER_M  = float(os.getenv("LLM_COST_CACHE_PER_M",  "0"))
LLM_COST_OUTPUT_PER_M = float(os.getenv("LLM_COST_OUTPUT_PER_M", "0"))

# Feature Flags
ENABLE_VERILOG_TOOLS = os.getenv("ENABLE_VERILOG_TOOLS", "false").lower() in ("true", "1", "yes")
ENABLE_CMUX_TOOLS = os.getenv("CMUX_ENABLE", "false").lower() in ("true", "1", "yes")
ENABLE_TMUX_TOOLS = os.getenv("TMUX_ENABLE", "false").lower() in ("true", "1", "yes")
ENABLE_WEB_TOOLS = os.getenv("ENABLE_WEB_TOOLS", "false").lower() in ("true", "1", "yes")
FIRECRAWL_API_URL = os.getenv("FIRECRAWL_API_URL", "http://localhost:3002")
FIRECRAWL_TIMEOUT = int(os.getenv("FIRECRAWL_TIMEOUT", "30"))

# Maximum cache breakpoints (1-4, Anthropic allows up to 4)
# Default: 3 (System message + 2 dynamic points in history)
MAX_CACHE_BREAKPOINTS = int(os.getenv("MAX_CACHE_BREAKPOINTS", "3"))

# Cache interval - how often to place breakpoints in message history
# If 0 or not set: use dynamic calculation based on history length
# If set to N: place breakpoint every N messages
# Default: 0 (dynamic calculation)
CACHE_INTERVAL = int(os.getenv("CACHE_INTERVAL", "0"))

# Minimum tokens required for caching
# Claude Sonnet/Opus: 1024, Claude Haiku: 2048
# Default: 1024
MIN_CACHE_TOKENS = int(os.getenv("MIN_CACHE_TOKENS", "1024"))

# ============================================================
# Session Recovery Configuration
# ============================================================
# Enable/Disable session recovery system
# When enabled, creates automatic recovery points and allows rollback on errors
# Default: true (recommended for stability)
ENABLE_SESSION_RECOVERY = os.getenv("ENABLE_SESSION_RECOVERY", "true").lower() in ("true", "1", "yes")

# Maximum number of recovery attempts after consecutive errors
# System will try to rollback and retry up to this many times
# Default: 3
MAX_RECOVERY_ATTEMPTS = int(os.getenv("MAX_RECOVERY_ATTEMPTS", "3"))

# Automatically create recovery points
# When enabled, creates a recovery point after each user message
# Default: true (recommended)
AUTO_RECOVERY_POINT = os.getenv("AUTO_RECOVERY_POINT", "true").lower() in ("true", "1", "yes")

# ============================================================
# Embedding Configuration (for Memory System)
# ============================================================
# Embedding API URL (OpenAI compatible)
EMBEDDING_BASE_URL = os.getenv("EMBEDDING_BASE_URL", "https://api.openai.com/v1")

# Embedding API Key (fallback to LLM_API_KEY if not set)
EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY", API_KEY)

# Embedding model name
# OpenAI: text-embedding-3-small (1536 dim, $0.00002/1K tokens)
#         text-embedding-3-large (3072 dim, $0.00013/1K tokens)
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

# Embedding dimension (auto-detected, optional override)
# Optional: Auto-detect if not set
_emb_dim_env = os.getenv("EMBEDDING_DIMENSION")
EMBEDDING_DIMENSION = int(_emb_dim_env) if _emb_dim_env else None

# ============================================================
# Memory System Configuration
# ============================================================
# Enable/Disable memory system
ENABLE_MEMORY = os.getenv("ENABLE_MEMORY", "false").lower() in ("true", "1", "yes")

# Memory directory (relative to home directory)
MEMORY_DIR = os.getenv("MEMORY_DIR", ".memory")

# Enable automatic preference extraction from user messages (Mem0-style)
# When enabled, Common AI Agent will detect preferences in user messages
# and automatically learn them without explicit instruction
# Default: true
ENABLE_AUTO_EXTRACT = os.getenv("ENABLE_AUTO_EXTRACT", "true").lower() in ("true", "1", "yes")

# ============================================================
# Graph Lite Configuration (Knowledge Graph)
# ============================================================
# Enable/Disable graph system
ENABLE_GRAPH = os.getenv("ENABLE_GRAPH", "false").lower() in ("true", "1", "yes")

# Auto-extract knowledge from conversations (end of session)
GRAPH_AUTO_EXTRACT = os.getenv("GRAPH_AUTO_EXTRACT", "true").lower() in ("true", "1", "yes")

# Number of relevant nodes to inject into context (semantic search)
GRAPH_SEARCH_LIMIT = int(os.getenv("GRAPH_SEARCH_LIMIT", "5"))

# Similarity threshold for graph search results (0.0-1.0)
# Only nodes with similarity >= this value will be included in context
GRAPH_SIMILARITY_THRESHOLD = float(os.getenv("GRAPH_SIMILARITY_THRESHOLD", "0.5"))

# Number of recent messages to use for knowledge extraction
GRAPH_EXTRACTION_MESSAGES = int(os.getenv("GRAPH_EXTRACTION_MESSAGES", "10"))

# ============================================================
# A-MEM Configuration (Auto-Linking)
# ============================================================
# Similarity threshold for finding candidate notes to link (0.0-1.0)
AMEM_SIMILARITY_THRESHOLD = float(os.getenv("AMEM_SIMILARITY_THRESHOLD", "0.5"))

# Maximum number of candidate notes to send to LLM for linking decision
AMEM_MAX_CANDIDATES = int(os.getenv("AMEM_MAX_CANDIDATES", "10"))

# LLM temperature for linking decisions (lower = more logical/deterministic)
AMEM_LINK_TEMPERATURE = float(os.getenv("AMEM_LINK_TEMPERATURE", "0.3"))

# ============================================================
# ACE Credit Assignment Configuration
# ============================================================
# Enable credit tracking for graph nodes (ACE-style feedback)
# When enabled, tracks which knowledge nodes helped or harmed task completion
ENABLE_CREDIT_TRACKING = os.getenv("ENABLE_CREDIT_TRACKING", "true").lower() in ("true", "1", "yes")

# Minimum quality score to include a node in search results (-1.0 to 1.0)
# Nodes with quality below this will be excluded/deprioritized
# Quality = (helpful - harmful) / (helpful + harmful + 1)
NODE_QUALITY_THRESHOLD = float(os.getenv("NODE_QUALITY_THRESHOLD", "-0.3"))

# ============================================================
# Knowledge Curator Configuration (ACE-style)
# ============================================================
# Enable/Disable knowledge curator (automatic node cleanup)
ENABLE_CURATOR = os.getenv("ENABLE_CURATOR", "true").lower() in ("true", "1", "yes")

# Run curation every N conversations
CURATOR_INTERVAL = int(os.getenv("CURATOR_INTERVAL", "10"))

# Days of inactivity before pruning unused nodes
CURATOR_PRUNE_DAYS = int(os.getenv("CURATOR_PRUNE_DAYS", "30"))

# Minimum harmful count before considering deletion
# Node deleted if: harmful > helpful AND harmful >= this threshold
CURATOR_HARMFUL_THRESHOLD = int(os.getenv("CURATOR_HARMFUL_THRESHOLD", "2"))

# ============================================================
# Hybrid Search Configuration (BM25 + Embedding)
# ============================================================
# Search method: "embedding", "bm25", or "hybrid"
# hybrid uses RRF (Reciprocal Rank Fusion) to combine both
SEARCH_METHOD = os.getenv("SEARCH_METHOD", "hybrid")

# Alpha weight for hybrid search (0.0-1.0)
# Higher = more weight on embedding similarity
# Lower = more weight on BM25 keyword matching
HYBRID_ALPHA = float(os.getenv("HYBRID_ALPHA", "0.8"))

# ============================================================
# RAG Auto-Indexing Configuration
# ============================================================
# Enable/Disable automatic RAG indexing on startup
# When enabled, automatically indexes files based on ~/.rag/.ragconfig
# Uses hash-based comparison to skip unchanged files (very fast on re-runs)
ENABLE_RAG_AUTO_INDEX = os.getenv("ENABLE_RAG_AUTO_INDEX", "false").lower() in ("true", "1", "yes")

# Fine-grained chunking for Verilog files
# When enabled, creates detailed chunks for individual signals, case statements, if-else blocks
# More precise search but ~10x more chunks (and embeddings)
RAG_FINE_GRAINED = os.getenv("RAG_FINE_GRAINED", "false").lower() in ("true", "1", "yes")

# RAG API rate limiting delay (milliseconds)
# Prevents "Too Many Requests" (429) errors when indexing
# Default: 100ms (10 API calls/sec)
RAG_RATE_LIMIT_DELAY_MS = int(os.getenv("RAG_RATE_LIMIT_DELAY_MS", "100"))

# RAG storage directory (absolute or ~-prefixed path)
# Default: "~/.rag" (stored in home directory, not project dir)
RAG_DIR = os.getenv("RAG_DIR", "~/.rag")

# RAG config file path (.ragconfig location)
# Default: None (uses RAG_DIR/.ragconfig)
# Set to project .ragconfig path for project-specific indexing patterns
RAG_CONFIG_PATH = os.getenv("RAG_CONFIG_PATH", None)

# RAG Optimization Settings
# Chunk size for splitting documents (characters)
# Reduced to 1200 for better semantic precision (matches embedding limits)
RAG_CHUNK_SIZE = int(os.getenv("RAG_CHUNK_SIZE", "1200"))

# Check overlap size
RAG_CHUNK_OVERLAP = int(os.getenv("RAG_CHUNK_OVERLAP", "200"))

# Batch size for embedding API calls
RAG_EMBEDDING_BATCH_SIZE = int(os.getenv("RAG_EMBEDDING_BATCH_SIZE", "50"))

# Enable persistent caching (SQLite)
RAG_ENABLE_PERSISTENT_CACHE = os.getenv("RAG_ENABLE_PERSISTENT_CACHE", "true").lower() in ("true", "1", "yes")

# Search Algorithm: 'vector', 'hybrid_simple', 'hybrid_rrf'
RAG_SEARCH_ALGORITHM = os.getenv("RAG_SEARCH_ALGORITHM", "hybrid_simple")

# Enable/Disable Node Merge (Phase 4)
# When enabled, Curator will merge similar nodes to reduce redundancy
ENABLE_NODE_MERGE = os.getenv("ENABLE_NODE_MERGE", "false").lower() in ("true", "1", "yes")

# Similarity threshold for node merging (0.0-1.0)
# Only nodes with similarity >= this value will be merged
MERGE_SIMILARITY_THRESHOLD = float(os.getenv("MERGE_SIMILARITY_THRESHOLD", "0.85"))

# ============================================================
# Smart RAG Decision Configuration
# ============================================================
# Enable/Disable automatic RAG context injection
# When enabled, automatically searches RAG and injects relevant context
ENABLE_SMART_RAG = os.getenv("ENABLE_SMART_RAG", "false").lower() in ("true", "1", "yes")

# High threshold: score >= this -> use RAG context directly
SMART_RAG_HIGH_THRESHOLD = float(os.getenv("SMART_RAG_HIGH_THRESHOLD", "0.75"))

# Low threshold: score < this -> ignore RAG results
SMART_RAG_LOW_THRESHOLD = float(os.getenv("SMART_RAG_LOW_THRESHOLD", "0.0"))

# Number of top results to consider
SMART_RAG_TOP_K = int(os.getenv("SMART_RAG_TOP_K", "3"))

# Enable LLM judgment for mid-score results (between low and high threshold)
# When enabled, asks LLM to judge relevance for ambiguous cases
SMART_RAG_LLM_JUDGE = os.getenv("SMART_RAG_LLM_JUDGE", "true").lower() in ("true", "1", "yes")

# ============================================================
# Procedural Memory Configuration (Memp)
# ============================================================
# Enable/Disable procedural memory system (learning from past experiences)
ENABLE_PROCEDURAL_MEMORY = os.getenv("ENABLE_PROCEDURAL_MEMORY", "false").lower() in ("true", "1", "yes")

# Maximum number of similar trajectories to retrieve for guidance
PROCEDURAL_RETRIEVE_LIMIT = int(os.getenv("PROCEDURAL_RETRIEVE_LIMIT", "3"))

# Minimum similarity score to use a trajectory (0.0-1.0)
PROCEDURAL_SIMILARITY_THRESHOLD = float(os.getenv("PROCEDURAL_SIMILARITY_THRESHOLD", "0.5"))

# Enable trajectory guidance injection into prompts
PROCEDURAL_INJECT_GUIDANCE = os.getenv("PROCEDURAL_INJECT_GUIDANCE", "true").lower() in ("true", "1", "yes")

# ============================================================
# Deep Think Configuration (Hypothesis Branching)
# ============================================================
# Enable/Disable Deep Think system (parallel hypothesis reasoning)
ENABLE_DEEP_THINK = os.getenv("ENABLE_DEEP_THINK", "true").lower() in ("true", "1", "yes")

# Number of hypotheses to generate per task
DEEP_THINK_NUM_HYPOTHESES = int(os.getenv("DEEP_THINK_NUM_HYPOTHESES", "3"))

# Enable simulation step (run first_action for each hypothesis)
DEEP_THINK_ENABLE_SIMULATION = os.getenv("DEEP_THINK_ENABLE_SIMULATION", "true").lower() in ("true", "1", "yes")

# Scoring weights (must sum to 1.0)
DEEP_THINK_WEIGHT_EXPERIENCE = float(os.getenv("DEEP_THINK_WEIGHT_EXPERIENCE", "0.30"))
DEEP_THINK_WEIGHT_KNOWLEDGE = float(os.getenv("DEEP_THINK_WEIGHT_KNOWLEDGE", "0.20"))
DEEP_THINK_WEIGHT_COHERENCE = float(os.getenv("DEEP_THINK_WEIGHT_COHERENCE", "0.25"))
DEEP_THINK_WEIGHT_SIMULATION = float(os.getenv("DEEP_THINK_WEIGHT_SIMULATION", "0.15"))
DEEP_THINK_WEIGHT_CONFIDENCE = float(os.getenv("DEEP_THINK_WEIGHT_CONFIDENCE", "0.10"))

# LLM temperature for hypothesis generation (higher = more diverse)
DEEP_THINK_TEMPERATURE = float(os.getenv("DEEP_THINK_TEMPERATURE", "0.7"))

# Timeout for parallel tool execution (seconds)
DEEP_THINK_TOOL_TIMEOUT = int(os.getenv("DEEP_THINK_TOOL_TIMEOUT", "10"))

# ============================================================
# Sub-Agent Configuration (Claude Code Style)
# ============================================================
# Enable/Disable Sub-Agent system (replaces Deep Think when enabled)
# When enabled, Orchestrator analyzes tasks and spawns specialized agents
ENABLE_SUB_AGENTS = os.getenv("ENABLE_SUB_AGENTS", "false").lower() in ("true", "1", "yes")

# Enable parallel execution of sub-agents
# Default: false (sequential execution for stability)
SUB_AGENT_PARALLEL_ENABLED = os.getenv("SUB_AGENT_PARALLEL_ENABLED", "false").lower() in ("true", "1", "yes")

# Maximum iterations per sub-agent
SUB_AGENT_MAX_ITERATIONS = int(os.getenv("SUB_AGENT_MAX_ITERATIONS", "10"))

# Maximum parallel workers when parallel execution is enabled
SUB_AGENT_MAX_WORKERS = int(os.getenv("SUB_AGENT_MAX_WORKERS", "3"))

# Timeout for each sub-agent (seconds)
SUB_AGENT_TIMEOUT = int(os.getenv("SUB_AGENT_TIMEOUT", "60"))

# ============================================================
# ReAct Parallel Execution Configuration
# ============================================================
# Enable parallel execution of multiple Actions in the ReAct loop.
# When LLM outputs multiple Actions, eligible read-only tools can run concurrently.
ENABLE_REACT_PARALLEL = os.getenv("ENABLE_REACT_PARALLEL", "true").lower() in ("true", "1", "yes")

# Enhanced parallel execution using ActionDependencyAnalyzer (Claude Code style)
# - Automatic dependency analysis
# - Intelligent batching (read-only → parallel, write → barrier)
# - File conflict detection
# Set to False to use legacy simple allowlist-based parallelism
ENABLE_ENHANCED_PARALLEL = os.getenv("ENABLE_ENHANCED_PARALLEL", "true").lower() in ("true", "1", "yes")

# Maximum parallel workers for ReAct actions
REACT_MAX_WORKERS = int(os.getenv("REACT_MAX_WORKERS", "5"))

# Lines to preview when write_file runs (parallel or sequential). 0 = disable (show brief)
WRITE_PREVIEW_LINES = int(os.getenv("WRITE_PREVIEW_LINES", "15"))

# Max lines to show for edit/replace tool results. 0 = disable (show brief)
EDIT_PREVIEW_MAX_LINES = int(os.getenv("EDIT_PREVIEW_MAX_LINES", "50"))

# Timeout for a parallel action batch (seconds)
REACT_ACTION_TIMEOUT = int(os.getenv("REACT_ACTION_TIMEOUT", "30"))

# Global timeout for ANY single tool execution (seconds).
# This is the last-resort safety net — if a tool hangs beyond this, it is force-killed.
# Applies to both serial and parallel tool execution paths.
REACT_TOOL_GLOBAL_TIMEOUT = int(os.getenv("REACT_TOOL_GLOBAL_TIMEOUT", "300"))

# ============================================================
# Todo Tracking System (Phase 2 - Claude Code Style)
# ============================================================
# Enable todo tracking for multi-step tasks
# Displays real-time progress with ✅ ▶️ ⏸️ icons
ENABLE_TODO_TRACKING = os.getenv("ENABLE_TODO_TRACKING", "true").lower() in ("true", "1", "yes")
ACTION_REMINDER = os.getenv("ACTION_REMINDER", "true").lower() in ("true", "1", "yes")
ACTION_REMINDER_TEXT = os.getenv(
    "ACTION_REMINDER_TEXT",
    "If further action is needed, output it now: Action: tool_name(param=value)",
)
TODO_STAGNATION_LIMIT = int(os.getenv("TODO_STAGNATION_LIMIT", "50"))
TODO_AUTO_ADVANCE_THRESHOLD = int(os.getenv("TODO_AUTO_ADVANCE_THRESHOLD", "5"))
TODO_TEXT_ONLY_LIMIT = int(os.getenv("TODO_TEXT_ONLY_LIMIT", "50"))
PLAN_TODO_WRITE_MAX = int(os.getenv("PLAN_TODO_WRITE_MAX", "10"))
MAX_REJECTION_LIMIT = int(os.getenv("MAX_REJECTION_LIMIT", "50"))

# Inject .UPD_RULE.md before default RULES in system prompt so it takes precedence.
# true  = PROJECT RULES appear before default RULES (recommended)
# false = PROJECT RULES appear after (old behavior — may be overridden by defaults)
UPD_RULE_PRIORITY_INJECT = os.getenv("UPD_RULE_PRIORITY_INJECT", "false").lower() in ("true", "1", "yes")

# Periodically re-inject .UPD_RULE.md into continuation_prompt every turn.
# true  = remind the model of PROJECT RULES alongside each task reminder
# false = PROJECT RULES only in system prompt (may be forgotten in long sessions)
UPD_RULE_PERIODIC_INJECT = os.getenv("UPD_RULE_PERIODIC_INJECT", "false").lower() in ("true", "1", "yes")

# Auto-advance to next todo when current step completes
# If False, todos stay in_progress until manually completed
TODO_AUTO_ADVANCE = os.getenv("TODO_AUTO_ADVANCE", "true").lower() in ("true", "1", "yes")

# ============================================================
# Proactive Mode Configuration
# ============================================================
# When enabled, the agent will show a proactive message after idle timeout
PROACTIVE_ENABLED = os.getenv("PROACTIVE_ENABLED", "false").lower() in ("true", "1", "yes")
PROACTIVE_IDLE_SECONDS = int(os.getenv("PROACTIVE_IDLE_SECONDS", "30"))
PROACTIVE_MESSAGE = os.getenv("PROACTIVE_MESSAGE", "🤔 Still here? Need help with anything?")
PROACTIVE_MAX_CYCLES = int(os.getenv("PROACTIVE_MAX_CYCLES", "10"))  # Max proactive injections before stopping (0 = unlimited)

# ============================================================
# TodoWrite Tool (Claude Code Integration)
# ============================================================
# Enable TodoWrite as an explicit tool (in addition to auto-parsing)
# When enabled, LLM can explicitly call todo_write() tool
# When disabled, only auto-parsing from text works (legacy behavior)
ENABLE_TODO_WRITE_TOOL = os.getenv("ENABLE_TODO_WRITE_TOOL", "true").lower() in ("true", "1", "yes")

# Enhanced tool descriptions with Claude Code patterns
# Adds "parallel execution", "when NOT to use", and detailed parameter constraints
# When disabled, uses legacy simple descriptions
ENABLE_ENHANCED_TOOL_DESCRIPTIONS = os.getenv("ENABLE_ENHANCED_TOOL_DESCRIPTIONS", "true").lower() in ("true", "1", "yes")

# ============================================================
# Multiline Input (prompt_toolkit)
# ============================================================
# Enable multiline input mode using prompt_toolkit
# When enabled: Enter = newline, Meta+Enter (ESC then Enter) or Ctrl+D = submit
# When disabled: standard single-line input() (default)
ENABLE_MULTILINE_INPUT = os.getenv("ENABLE_MULTILINE_INPUT", "true").lower() in ("true", "1", "yes")

# ============================================================
# Phase 4: Autonomous Decision-Making
# ============================================================

# LLM 기반 복잡도 분석 활성화
# When enabled, uses LLM to analyze task complexity instead of simple heuristics
AUTONOMOUS_COMPLEXITY_ANALYSIS = os.getenv("AUTONOMOUS_COMPLEXITY_ANALYSIS", "false").lower() in ("true", "1", "yes")

# LLM 복잡도 분석 시 사용할 temperature (0.0-1.0)
# Lower = more consistent, Higher = more creative
AUTONOMOUS_TEMPERATURE = float(os.getenv("AUTONOMOUS_TEMPERATURE", "0.3"))

# System Prompt with ReAct instructions
SYSTEM_PROMPT = """You are an intelligent coding agent named Common AI Agent.
You can read files, write code, and run terminal commands to help the user.
Always use surgical edits (replace_in_file or multi_replace) to modify only the necessary parts and save tokens.

TOOLS:
You have access to the following tools:

Basic File Tools:
1. read_file(path="path/to/file") - Read entire file content
2. write_file(path="path/to/file", content="file content") - Write/overwrite file
3. run_command(command="ls -la") - Execute shell commands
4. list_dir(path=".") - List directory contents

File Search & Navigation:
5. grep_file(pattern="regex_pattern", path="path/to/file", context_lines=2) - Search for pattern in file with context
6. read_lines(path="path/to/file", start_line=10, end_line=20) - Read specific line range
7. find_files(pattern="*.py", directory=".", max_depth=None) - Find files matching pattern

File Editing:
8. replace_in_file(path="path/to/file", old_text="old", new_text="new", count=-1, start_line=None, end_line=None) - Replace text occurrences (optionally within specific lines)
9. replace_lines(path="path/to/file", start_line=10, end_line=20, new_content="new code") - Replace line range

Git Tools:
10. git_status() - Show current git status
11. git_diff(path=None) - Show git diff (optionally for specific file)
12. git_revert(path="path/to/file") - Revert uncommitted changes to a file

Sub-Agent Tools:
30. background_task(agent="workflow", prompt="implement the change") - Delegate to sub-agent (explore/workflow)
31. background_output(task_id="bg_xxxx") - Get background task result
32. todo_update(index=1, status="completed") - Update todo item status (index is REQUIRED and MUST be 1-based. 1=first task, 2=second, etc.)

RELIABILITY RULES:
1. Always update your todo status immediately after completing the associated work in the SAME TURN.
2. Use the exact 1-based index provided in the "[Todo X/Y] Next Task N: ..." status footer.

FORMAT:
To use a tool, you must use the following format exactly:

Thought: [Your reasoning about what to do next]
Action: [ToolName]([Arguments])

CRITICAL: NEVER use "tool_call" or any other block format. ALWAYS use "Action:".

The user will then respond with:
Observation: [Output of the tool]

You can then continue with more Thought/Action/Observation steps.
When you have finished the task or need to ask the user a question, respond normally (without Action:).

CRITICAL - DO NOT GENERATE OBSERVATIONS:
You must NEVER generate lines starting with "Observation:".
The system will provide the Observation to you after you execute an Action.
If you generate "Observation:", the system will think you are done and stop.
ALWAYS wait for the system to provide the Observation.

CRITICAL - Triple-Quoted Strings:
When writing files with multi-line content, you MUST use actual triple quotes.

DO NOT USE PLACEHOLDERS OR PSEUDO-CODE:
❌ WRONG: content=TRIPLE_QUOTE_START...TRIPLE_QUOTE_END
❌ WRONG: content="[your code here]"
❌ WRONG: content="..." (placeholder)

CORRECT FORMAT - Use actual triple quotes (three double-quotes or three single-quotes):
✅ CORRECT: content=\"\"\"actual code here\"\"\"
✅ CORRECT: content='''actual code here'''

This is MANDATORY for:
- Source code files (.py, .v, .c, .js, etc.)
- Configuration files (.yaml, .json, .toml, etc.)
- Scripts (.sh, .bash, etc.)
- Any content with multiple lines

EXAMPLES:

Example 1 - Single line content:
User: Create a hello world python file.
Thought: I need to create a file named hello.py.
Action: write_file(path="hello.py", content="print('Hello World')")
Observation: Successfully wrote to 'hello.py'.

Example 2 - Multi-line content (USE ACTUAL TRIPLE QUOTES):
User: Create a Python hello world script.
Thought: I need to create hello.py with proper Python syntax. I will use triple quotes.
Action: write_file(path="hello.py", content=\"\"\"#!/usr/bin/env python3

def main():
    print("Hello World")

if __name__ == "__main__":
    main()
\"\"\")
Observation: Successfully wrote to 'hello.py'.

ERROR RECOVERY - NEVER GIVE UP:
You are a persistent agent. When you encounter errors, you MUST analyze and fix them.
NEVER output phrases like "I give up" or "I cannot proceed".

When a command or action fails:
1. Read the error message carefully
2. Identify the root cause
3. Use diagnostic tools (read_lines, grep_file) to examine the problem
4. Fix the issue (replace_in_file, replace_lines, or write_file)
5. Retry the failed command
6. Repeat up to 3 times before asking user for help

Example Error Recovery Workflow:
User: Run the tests
Action: run_command(command="pytest test_utils.py")
Observation: Error: test_utils.py:15: SyntaxError: invalid syntax

Thought: There's a syntax error at line 15. Let me examine the code around that line.
Action: read_lines(path="test_utils.py", start_line=13, end_line=17)
Observation: 13: def test_calculation():
14: result = calculate(10, 20  <- missing closing parenthesis
15: assert result == 30

Thought: I see the problem - missing closing parenthesis on line 14. Let me fix it.
Action: replace_in_file(path="test_utils.py", old_text="result = calculate(10, 20", new_text="result = calculate(10, 20)", start_line=14, end_line=14)
Observation: Replaced 1 occurrence in test_utils.py

Thought: Now let me retry the tests.
Action: run_command(command="pytest test_utils.py")
Observation: Success! All tests passed.

ANOTHER ERROR RECOVERY EXAMPLE - Import Issues:
Action: run_command(command="python main.py")
Observation: Error: ModuleNotFoundError: No module named 'utils'

Thought: Let me check the import statements and file structure.
Action: read_lines(path="main.py", start_line=1, end_line=5)
Observation: Shows import structure

Thought: The import path is incorrect. Let me check if utils.py exists.
Action: list_dir(path=".")
Observation: [File list showing utils.py in src/ subdirectory]

Thought: I need to fix the import path to include the src directory.
Action: replace_in_file(path="main.py", old_text="import utils", new_text="from src import utils")
Observation: Replaced 1 occurrence in main.py

Thought: Now let me retry execution.
Action: run_command(command="python main.py")
Observation: Success!

PERSISTENCE RULES:
- Try fixing at least 3 times before asking for help
- Always examine the actual code when errors occur
- Use read_lines to see context around error locations
- Use replace_in_file for small targeted fixes
- Use write_file for major restructuring
- After fixing, ALWAYS retry the failed command
- Keep trying until success or 3 failed fix attempts
IMPORTANT: You can execute MULTIPLE actions in a single turn.
If you need to run multiple commands or read multiple files, list them one after another.

Example of Multi-Action:
Thought: I need to check two files.
Action: read_file(path="file1.py")
Action: read_file(path="file2.py")

The system will execute them sequentially and provide all observations.

TASK TRACKING (for complex multi-step tasks):
**IMPORTANT: Only use TodoWrite when the user explicitly asks you to create a todo list or track tasks. Do NOT proactively create todos without being instructed.**
When working on complex tasks with multiple steps, use TodoWrite to track progress:

TodoWrite:
- [ ] Step 1: Explore existing implementations
- [ ] Step 2: Design interface specification
- [ ] Step 3: Implement RTL
- [ ] Step 4: Create testbench
- [ ] Step 5: Run simulation

The system will automatically:
1. Mark current step as "in progress" (▶️)
2. Mark completed steps as "done" (✅)
3. Show progress visualization

Only ONE step can be in_progress at a time.
Mark steps complete IMMEDIATELY after finishing them.

Example with TodoWrite:
Thought: This task requires multiple steps. Let me create a todo list.
TodoWrite:
- [ ] Explore codebase for similar modules
- [ ] Design the interface
- [ ] Write the implementation
- [ ] Test the module

Thought: Now let me start with the first step.
Action: grep_file(pattern="module.*fifo", path="*.v")

# ============================================================
# AUTONOMOUS DECISION-MAKING (Phase 4)
# ============================================================

When deciding how to approach a task, consider:

1. **Task Complexity**:
   - Simple (1-2 actions): Direct execution
   - Medium (3-5 steps): Direct execution (do NOT auto-create todos)
   - Complex (6+ steps): Direct execution unless user explicitly asks for todo tracking

2. **Tool Selection**:
   - **Parallel execution**: Use multiple read-only tools simultaneously
   - **Sequential execution**: Write tools create barriers
   - **Sub-agents**: Use background_task for delegation
   - **Todo tracking**: Use todo_update/todo_add for task progress during execution

Focus on using the right tools for the task at hand.

"""

# ============================================================
# Tool Description System (OpenCode Integration)
# ============================================================

# Backup of original SYSTEM_PROMPT for legacy mode
LEGACY_SYSTEM_PROMPT = SYSTEM_PROMPT


def _load_prompt_fragment(filename: str):
    """
    Load workflow/prompts/<filename>. Returns None if not found (→ hardcoded fallback).
    Priority:
      1. Active workspace prompts/<filename>   (workspace-specific override)
      2. workflow/prompts/<filename>            (shared fragment)
    """
    import builtins as _b
    candidates = []
    ws_msgs = getattr(_b, "_WORKSPACE_HOOK_MESSAGES", {})
    ws_dir = ws_msgs.get("_workspace_dir")
    if ws_dir:
        candidates.append(Path(ws_dir) / "prompts" / filename)
    candidates.append(Path(__file__).parent.parent / "workflow" / "prompts" / filename)
    for p in candidates:
        try:
            if p.exists():
                return p.read_text(encoding="utf-8").strip()
        except Exception:
            pass
    return None


def build_base_system_prompt(allowed_tools: set = None, plan_mode: bool = False, todo_active: bool = False) -> str:
    """
    Build compact system prompt (~5K tokens).
    Tool descriptions are minimal (name + signature + when-to-use).
    Detailed examples removed — LLM infers usage from signatures.
    """
    # cursor-agent backend: use dedicated minimal prompt so cursor-agent
    # outputs Action: lines for todo tracking instead of using internal tools
    if CURSOR_AGENT_ENABLE:
        import os as _os
        _prompt_path = _os.path.join(
            _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
            "workflow", "prompts", "cursor_agent.md"
        )
        try:
            with open(_prompt_path, "r") as _f:
                return _f.read()
        except Exception:
            pass  # fall through to normal prompt

    if not ENABLE_TOOL_DESCRIPTIONS:
        # Legacy fallback
        return LEGACY_SYSTEM_PROMPT

    try:
        from core import tools
    except ImportError:
        return LEGACY_SYSTEM_PROMPT

    # Determine tool list
    if allowed_tools is None:
        tool_list = set(tools.AVAILABLE_TOOLS.keys())
    else:
        tool_list = set(t for t in tools.AVAILABLE_TOOLS if t in allowed_tools)

    # Filter out blocked tools based on mode
    if plan_mode:
        tool_list = tool_list - PLAN_MODE_BLOCKED_TOOLS
    else:
        tool_list = tool_list - NORMAL_MODE_BLOCKED_TOOLS

    def _tool_line(name, sig, desc):
        """Format one tool line, only if available."""
        if name in tool_list:
            return f"- {name}({sig}) — {desc}"
        return None

    # ── COMPACT TOOL TABLE ──
    tool_lines = {
        "File I/O": [
            _tool_line("read_file", 'path', "Read entire file. For large files (>500 lines), use grep_file first."),
            _tool_line("read_lines", 'path, start_line, end_line', "Read line range. Use after grep to target sections."),
            _tool_line("write_file", 'path, content', "Create NEW files ONLY. NEVER use on existing files."),
            _tool_line("replace_in_file", 'path, old_text, new_text', "Edit existing files. ALWAYS read first to get exact text."),
            _tool_line("replace_lines", 'path, start_line, end_line, new_content', "Replace line range in existing files."),
            _tool_line("run_command", 'command', "Execute shell command."),
            _tool_line("list_dir", 'path', "List directory contents."),
        ],
        "Search": [
            _tool_line("grep_file", 'pattern, path', "Regex search in file(s). Use BEFORE read_file on large files."),
            _tool_line("find_files", 'pattern, path', "Glob search for files. Prefer over repeated list_dir."),
        ],
        "Git": [
            _tool_line("git_status", '', "Show working tree status."),
            _tool_line("git_diff", 'path', "Show unstaged changes."),
            _tool_line("git_revert", 'path', "Revert uncommitted changes to a file."),
        ]
    }

    # Task Management (conditional)
    # todo_write is ALWAYS visible in Plan Mode (used to start a list)
    # Others only if todo_active is True
    task_tools = []
    if plan_mode:
        task_tools.append(_tool_line("todo_write", 'tasks', "Create task list (Plan Mode only). Format: [{content, activeForm, status}]."))
        task_tools.append(_tool_line("todo_remove", 'index', "Remove a task (index REQUIRED, 1-based)."))
    
    if todo_active:
        task_tools.append(_tool_line("todo_update", 'index, status, content, detail', "Update task status (index REQUIRED, 1-based)."))
        task_tools.append(_tool_line("todo_add", 'content, priority, index', "Add task (index is target position, 1-based)."))
        task_tools.append(_tool_line("todo_status", '', "Show current task progress."))
    
    task_tools = [t for t in task_tools if t]
    if task_tools:
        tool_lines["Task Management"] = task_tools

    tool_lines["Sub-Agents"] = [
        _tool_line("background_task", 'agent, prompt', "Delegate to sub-agent (explore/workflow)."),
        _tool_line("background_output", 'task_id', "Get sub-agent result."),
        _tool_line("background_cancel", 'task_id', "Cancel sub-agent."),
        _tool_line("background_list", '', "List active sub-agents."),
    ]

    # Spec navigation tools
    if "spec_navigate" in tool_list:
        tool_lines["Spec Navigation"] = [
            _tool_line("spec_navigate", 'spec, node_id="root"',
                       "Navigate PCIe/UCIe/NVMe spec by section ID. "
                       "Start with node_id='root' for TOC, drill into sections. "
                       "Leaf nodes contain full spec text. Use for ALL spec questions."),
        ]

    # cmux tools (conditional)
    if ENABLE_CMUX_TOOLS and "cmux_capture" in tool_list:
        tool_lines["cmux (modifiable_ai_agent)"] = [
            _tool_line("cmux_tree",               '',                      "List all cmux surfaces. Run first to find surface refs."),
            _tool_line("cmux_capture",            'lines=200',             "Capture modifiable_ai_agent screen text."),
            _tool_line("cmux_send",               'text',                  "Send text to modifiable_ai_agent (Enter auto-appended)."),
            _tool_line("cmux_send_key",           'key',                   "Send special key (ctrl+c, ctrl+q, escape, enter)."),
            _tool_line("cmux_restart_modifiable", '',                      "Quit and restart modifiable_ai_agent."),
            _tool_line("cmux_set_surface",        'surface_ref',           "Save surface ref to config for other cmux tools."),
            _tool_line("cmux_notify",             'title, body=""',        "Send macOS notification."),
            _tool_line("cmux_new_pane",           'direction="right", command=""',       "Split current workspace: create new pane (left/right/up/down)."),
            _tool_line("cmux_new_workspace",      'name="", command="", cwd=""',         "Create a new cmux workspace, optionally running a command."),
            _tool_line("cmux_list_panes",         'workspace=""',                        "List panes in current (or given) workspace."),
            _tool_line("cmux_focus_pane",         'pane',                                "Move focus to a pane by ref (e.g. 'pane:1')."),
            _tool_line("cmux_resize_pane",        'pane, direction, amount=5',           "Resize a pane: direction L/R/U/D, amount in cells."),
            _tool_line("cmux_move_surface",       'surface, direction',                  "Drag a surface into a new split pane (left/right/up/down)."),
        ]

    # tmux tools (conditional)
    if ENABLE_TMUX_TOOLS and "tmux_capture" in tool_list:
        tool_lines["tmux"] = [
            _tool_line("tmux_list_panes",         '',                      "List all panes in the agentic tmux session."),
            _tool_line("tmux_capture",            'pane="agentic:0.0", lines=200', "Capture pane screen text."),
            _tool_line("tmux_send_keys",          'keys, pane="agentic:0.0"',      "Send keys to a pane (Enter auto-appended)."),
            _tool_line("tmux_new_window",         'name="", command=""',   "Create a new tmux window."),
            _tool_line("tmux_kill_pane",          'pane',                  "Kill a tmux pane."),
        ]

    # Verilog tools (conditional)
    if ENABLE_VERILOG_TOOLS and "analyze_verilog_module" in tool_list:
        tool_lines["Verilog Analysis"] = [
            _tool_line("analyze_verilog_module", 'path', "Parse module ports, parameters, FSM."),
            _tool_line("find_signal_usage", 'signal, path', "Find signal assignments/references."),
            _tool_line("find_module_definition", 'module_name, directory', "Locate module source file."),
            _tool_line("extract_module_hierarchy", 'path', "Get instantiation tree."),
            _tool_line("generate_module_testbench", 'path', "Auto-generate testbench."),
            _tool_line("find_potential_issues", 'path', "Lint-like checks."),
            _tool_line("analyze_timing_paths", 'path', "Timing analysis hints."),
            _tool_line("generate_module_docs", 'path', "Auto-generate documentation."),
            _tool_line("suggest_optimizations", 'path', "Optimization suggestions."),
        ]

    # Web tools (conditional — requires Firecrawl)
    if ENABLE_WEB_TOOLS and "web_search" in tool_list:
        tool_lines["Web"] = [
            _tool_line("web_search", 'query, limit=5, lang="en", tbs=""', "Search the web via Firecrawl. Returns titles, URLs, content."),
            _tool_line("web_fetch", 'url, formats="markdown"', "Scrape a URL and return markdown/html content."),
            _tool_line("web_extract", 'urls, prompt="", schema=""', "Extract structured data from URLs using AI."),
        ]

    # ── BUILD PROMPT ──
    parts = []

    # Identity
    # Skip base identity when a workspace is active — the workspace system_prompt.md
    # defines the agent role. Injecting a second "coding agent" label here causes
    # the LLM to answer "who are you" with the base identity instead of the workspace role.
    _active_ws = os.environ.get("ACTIVE_WORKSPACE", "").strip()
    if not _active_ws:
        _identity = _load_prompt_fragment("identity.md")
        parts.append(
            (_identity + "\n") if _identity else "You are Common AI Agent, an intelligent coding agent.\n"
        )

    # Format
    _native_mode = os.getenv("ENABLE_NATIVE_TOOL_CALLS", "false").lower() in ("true", "1", "yes")
    # Codex/Responses API models tend to echo ReAct templates literally — use simpler format
    _codex_mode = False
    try:
        from src.llm_client import is_responses_api_model
        _codex_mode = is_responses_api_model()
    except ImportError:
        pass

    if _native_mode or _codex_mode:
        parts.append(
            "Use the provided function tools to complete tasks. "
            "Call tools when you need information or to take actions. "
            "You may call multiple tools in one turn for parallel execution.\n"
        )
    else:
        _fmt = _load_prompt_fragment("format.md")
        parts.append(
            (_fmt + "\n") if _fmt else (
                "FORMAT (strict ReAct loop):\n"
                "Thought: [reasoning]\n"
                "Action: tool_name(arg=\"value\")\n"
                "- Multiple Actions per turn = parallel execution.\n"
                "- Use triple quotes for multi-line: content=\"\"\"...\"\"\".\n"
                "- NEVER generate \"Observation:\" — the system provides it.\n"
                "- NEVER say 'Let me check...' or 'I will...' without an Action in the same turn.\n"
                "- If you need information, call the tool NOW — do not narrate first.\n"
            )
        )

    # Tool table (skip in native mode — LLM sees schemas via API tools param)
    if _native_mode:
        parts.append("TOOLS: (use function tools provided by the API)\n")
    else:
        parts.append("TOOLS:\n")
        for category, lines in tool_lines.items():
            available = [l for l in lines if l is not None]
            if available:
                parts.append(f"{category}:")
                parts.extend(available)
                parts.append("")

    # .UPD_RULE.md — load early so PROJECT RULES can override defaults below
    _upd_rule_paths = [
        Path.home() / ".common_ai_agent" / ".UPD_RULE.md",   # global
        Path(__file__).parent.parent / ".UPD_RULE.md",        # project
    ]
    _upd_rule_parts = []
    for _p in _upd_rule_paths:
        if _p.exists():
            try:
                _text = _p.read_text(encoding="utf-8").strip()
                if _text:
                    _upd_rule_parts.append(_text)
            except Exception:
                pass
    _upd_rule_text = "\n\n".join(_upd_rule_parts) if _upd_rule_parts else ""

    # PROJECT RULES injected BEFORE default rules so they take precedence
    if _upd_rule_text and UPD_RULE_PRIORITY_INJECT:
        parts.append(
            "\n=== PROJECT RULES (override defaults below) ===\n"
            + _upd_rule_text
            + "\n=== END PROJECT RULES ===\n"
        )
    elif _upd_rule_text:
        # Legacy: append after rules (lower priority)
        parts.append("\n=== PROJECT RULES ===\n" + _upd_rule_text + "\n=====================")

    # Core rules — try loading from file first, fall back to hardcoded
    _rules_file = _load_prompt_fragment("rules_normal.md") if not plan_mode else None
    if _rules_file:
        parts.append(_rules_file + "\n")
        # Append Plan Mode instructions if active
        if plan_mode:
            _plan_rules = _load_prompt_fragment("rules_plan.md")
            if _plan_rules:
                parts.append(_plan_rules + "\n")
            parts.append(PLAN_MODE_PROMPT)
        return "\n".join(parts)

    # Core rules (compressed) — PROJECT RULES above override these if they conflict
    rules_parts = [
        "RULES (defaults — PROJECT RULES above take precedence):\n",
        "\n1. PARALLEL EXECUTION:\n",
        "   - Read-only tools are parallel-safe: read_file, read_lines, grep_file, list_dir, find_files, git_status, git_diff.\n"
    ]
    if not plan_mode:
        rules_parts.append("   - Write tools create sequential barriers: write_file, replace_in_file, run_command.\n")

    rules_parts.append("\n2. FILE OPERATIONS:\n")
    if plan_mode:
        rules_parts.append("   - You are in PLAN MODE. File modifications are BLOCKED until the plan is confirmed.\n")
    else:
        rules_parts.append("   - New file → write_file(). Existing file → replace_in_file(). NEVER write_file() on existing.\n")
        rules_parts.append("   - ALWAYS read_file/read_lines BEFORE replace_in_file. Copy exact text including indentation.\n")
        rules_parts.append("   - Include 5+ lines of context in old_text for unique matching.\n")

    if not plan_mode:
        rules_parts.append(
            "\n3. TODO TOOLS:\n"
            "   - In normal/execution mode, do NOT call todo_write. It is reserved for Plan Mode.\n"
            "   - Use todo_update to mark tasks in_progress/completed, todo_add to add a task.\n"
            "   - If you feel the need to rewrite the entire task list, switch to Plan Mode instead.\n"
        )

    rules_parts.append(
        "\n4. LARGE FILE STRATEGY:\n"
        "   - Files >500 lines: grep_file first → read_lines on found sections. Never blind-read.\n"
        "\n"
        "5. SEARCH PRIORITY: grep_file > find_files > list_dir.\n"
        "   - Search in current directory (.) first. NEVER expand to parent dirs unless explicitly told.\n"
        "   - If not found in ., report it — do not guess other locations.\n"
        "\n"
        "6. SURGICAL EDITING:\n"
        "   - Replace ONLY the specific changed block. Never replace entire classes/functions for small changes.\n"
        "   - Always include 5+ lines of surrounding context in old_text for unique matching.\n"
        "\n"
        "7. ANTI-HALLUCINATION:\n"
        "   - Never analyze a file you haven't read. Never invent tool results.\n"
        "   - If tool fails, adapt search — don't pretend results exist.\n"
    )
    if not ENABLE_MARKDOWN_RENDER:
        rules_parts.append(
            "\n8. TEXT FORMATTING:\n"
            "   - Markdown rendering is DISABLED. Do NOT use markdown syntax "
            "(like ``` , **, _, ##) in your thoughts or responses. Provide plain text only.\n"
        )
    parts.append("".join(rules_parts))

    # Append Plan Mode instructions if active
    if plan_mode:
        _plan_rules = _load_prompt_fragment("rules_plan.md")
        if _plan_rules:
            parts.append(_plan_rules + "\n")
        parts.append(PLAN_MODE_PROMPT)

    return "\n".join(parts)


PLAN_MODE_BLOCKED_TOOLS = frozenset({
    'write_file', 'replace_in_file', 'replace_lines',
    'replace_file_content', 'multi_replace_file_content',
    'apply_diffs', 'run_command', 'git_revert',
    'background_task', 'background_output', 'spawn_explore',
    'todo_update',  # Plan mode: use todo_write/todo_add/todo_remove; todo_update is for execution
})

# Tools only available in Plan Mode (blocked in Normal/Execution mode)
NORMAL_MODE_BLOCKED_TOOLS = frozenset({
    'todo_write',   # Use todo_update/todo_add during execution
    'todo_remove',  # Task removal only during planning
})


# Update SYSTEM_PROMPT to use new tool description system
# This will be overridden by build_system_prompt() in main.py when needed
SYSTEM_PROMPT = build_base_system_prompt()

# ============================================================
# Mode Prompts
# ============================================================

PLAN_MODE_PROMPT = """

🚨 === PLAN MODE === 🚨
You are in PLAN MODE. Your job is to research and build a concrete task list — NOT to execute.

════════════════════════════════════════
WORKFLOW
════════════════════════════════════════
1. RESEARCH   → Use read_file, grep_file, list_dir to understand the codebase.
2. TODO_WRITE → Call todo_write() to create a complete, step-by-step task list.
3. REFINE     → Adjust with todo_add / todo_remove based on user feedback.
4. CONFIRM    → Wait for user approval ('y' / 'confirm' / 'go') before execution.

════════════════════════════════════════
ALLOWED TODO TOOLS
════════════════════════════════════════
todo_write(todos=[...])
  Create or fully replace the task list. Use this first to establish the plan.
  Each task:
    {
      "content":    "Short past-tense label (shown when completed)",
      "activeForm": "Present-progressive label (shown while running)",
      "status":     "pending",   # always pending in plan mode
      "priority":   "high",      # high | medium | low
      "detail":     "Acceptance criteria, constraints, implementation notes"
    }
  Strings also accepted:
    todo_write(["Step 1", "Step 2", "Step 3"])

  Example:
    todo_write(todos=[
      {"content": "Analyzed counter module", "activeForm": "Analyzing counter module",
       "status": "pending", "detail": "Read counter.v, identify ports and FSM states"},
      {"content": "Wrote testbench", "activeForm": "Writing testbench", "status": "pending"},
      {"content": "Added reset tests", "activeForm": "Adding reset tests",
       "status": "pending", "priority": "high"}
    ])

todo_add(content, activeForm="", priority="medium", detail="", index=None)
  Append or insert one task. index= is 1-based; omit to append at end.
  Example:
    todo_add(content="Verified timing constraints", activeForm="Verifying timing constraints",
             priority="high", index=2)

todo_remove(index)
  Remove a task by 1-based index.
  Example:
    todo_remove(index=3)

════════════════════════════════════════
BLOCKED IN PLAN MODE
════════════════════════════════════════
🚫 todo_update  — DO NOT call todo_update in plan mode. It is blocked.
                  Use todo_add to add tasks, todo_remove to delete, todo_write to replace.
                  todo_update is for execution mode only (marking tasks in_progress / completed).
🚫 write_file, replace_in_file, replace_lines — file writing is blocked.
🚫 run_command, background_task — execution is blocked.

════════════════════════════════════════
RULES
════════════════════════════════════════
- Read freely: read_file, grep_file, list_dir, read_lines are all available.
- Always call todo_write before asking the user to confirm.
- Keep tasks atomic — one clear deliverable per task.
- Use detail= for acceptance criteria or implementation notes.
- Refine the list as research reveals more — do not rush to confirm.
- Do not begin execution until user explicitly approves.

════════════════════════════════════════
/todo REFERENCE  (user slash commands)
════════════════════════════════════════
  /todo                     show current list
  /todo add <text>          add a task
  /todo rm <N>              remove task N
  /todo mv <N> <M>          move task N to position M
  /todo g <N> <text>        change task N content
  /todo s <N> <status>      force status (p/i/c/a/r)
  /todo s all <status>      force all tasks to a status
  /todo e <N> <field> <val> edit a field

Edit fields: c=content  d=detail  cr=criteria  pr=priority  af=active_form
AI status flow: pending → in_progress → completed → approved
=================="""
