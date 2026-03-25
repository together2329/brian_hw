import os
from pathlib import Path

# Load .env file if it exists
def load_env_file():
    # Load config files in order of priority (first loaded takes precedence)
    # .config has highest priority, then .env files
    search_paths = [
        Path(__file__).parent.parent / '.config',  # common_ai_agent/.config (highest priority)
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

# ============================================================
# OpenRouter Configuration (주석 처리됨)
# ============================================================
# BASE_URL = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")
# API_KEY = os.getenv("LLM_API_KEY", "sk-or-v1-...")
# MODEL_NAME = os.getenv("LLM_MODEL_NAME", "meta-llama/llama-3.3-70b-instruct:free")

# Rate limiting (seconds to wait between API calls)
# Set to 0 to disable rate limiting
RATE_LIMIT_DELAY = float(os.getenv("RATE_LIMIT_DELAY", "5"))

# Maximum number of ReAct loop iterations
# Increased to allow for error recovery attempts (3 retries per error)
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "100"))

# API timeout in seconds (how long to wait for API response)
# Set to 0 to disable timeout (not recommended)
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "600"))

# Save conversation history to file
SAVE_HISTORY = os.getenv("SAVE_HISTORY", "true").lower() in ("true", "1", "yes")
HISTORY_FILE = os.getenv("HISTORY_FILE", "conversation_history.json")

# Debug mode - show detailed parsing and execution info
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() in ("true", "1", "yes")

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
# Type Validation & Linting (Zero-Dependency Features)
# ============================================================
# Enable parameter type validation (always available - uses standard library only)
# Validates tool parameters before execution using type hints
ENABLE_TYPE_VALIDATION = os.getenv("ENABLE_TYPE_VALIDATION", "true").lower() in ("true", "1", "yes")

# Enable automatic linting after file writes (optional - uses external tools if available)
# Checks Python files with compile() + pyflakes, Verilog files with iverilog
# Falls back gracefully if external tools not installed
ENABLE_LINTING = os.getenv("ENABLE_LINTING", "true").lower() in ("true", "1", "yes")

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
# Approximate token limit (1 token ~= 4 chars)
# Default: 262144 chars (~65K tokens) - matches Claude's 200K context
MAX_CONTEXT_CHARS = int(os.getenv("MAX_CONTEXT_CHARS", "512000"))  # Gemini Flash 3: 128K tokens * 4 chars/token
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
# Enable Anthropic Prompt Caching (manual control only)
# Set to true only when using Anthropic Claude models
# Cost savings: 90% for cached tokens
ENABLE_PROMPT_CACHING = os.getenv("ENABLE_PROMPT_CACHING", "false").lower() in ("true", "1", "yes")

# Prompt Caching Optimization Mode
# Options:
#   - "legacy": Single-string system message (current behavior, safe fallback)
#   - "optimized": Multi-block system message (40-50% cost reduction)
# Default: "legacy" (backward compatible)
# NOTE: Only effective when ENABLE_PROMPT_CACHING=true and using Anthropic models
CACHE_OPTIMIZATION_MODE = os.getenv("CACHE_OPTIMIZATION_MODE", "legacy").lower()

# Feature Flags
ENABLE_VERILOG_TOOLS = os.getenv("ENABLE_VERILOG_TOOLS", "false").lower() in ("true", "1", "yes")

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
ENABLE_MEMORY = os.getenv("ENABLE_MEMORY", "true").lower() in ("true", "1", "yes")

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
ENABLE_GRAPH = os.getenv("ENABLE_GRAPH", "true").lower() in ("true", "1", "yes")

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
ENABLE_PROCEDURAL_MEMORY = os.getenv("ENABLE_PROCEDURAL_MEMORY", "true").lower() in ("true", "1", "yes")

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

# Timeout for a parallel action batch (seconds)
REACT_ACTION_TIMEOUT = int(os.getenv("REACT_ACTION_TIMEOUT", "30"))

# ============================================================
# Todo Tracking System (Phase 2 - Claude Code Style)
# ============================================================
# Enable todo tracking for multi-step tasks
# Displays real-time progress with ✅ ▶️ ⏸️ icons
ENABLE_TODO_TRACKING = os.getenv("ENABLE_TODO_TRACKING", "true").lower() in ("true", "1", "yes")

# Auto-advance to next todo when current step completes
# If False, todos stay in_progress until manually completed
TODO_AUTO_ADVANCE = os.getenv("TODO_AUTO_ADVANCE", "true").lower() in ("true", "1", "yes")

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
# Claude Code Flow (Plan → Approve → Execute)
# ============================================================
# Flow modes:
# - "off": 기존 ReAct 동작
# - "auto": 복잡한 요청만 자동으로 Plan 모드 진입 (기본)
# - "always": 모든 요청에서 Plan 모드 진입
CLAUDE_FLOW_MODE = os.getenv("CLAUDE_FLOW_MODE", "auto").strip().lower()
if CLAUDE_FLOW_MODE not in ("off", "auto", "always"):
    CLAUDE_FLOW_MODE = "auto"

# Plan 승인 전에는 실행(파일쓰기/명령)을 하지 않도록 가드
CLAUDE_FLOW_REQUIRE_APPROVAL = os.getenv("CLAUDE_FLOW_REQUIRE_APPROVAL", "true").lower() in ("true", "1", "yes")

# 사용자가 "execute plan"/"계획 실행"을 입력하면 남은 step을 자동 진행
CLAUDE_FLOW_AUTO_EXECUTE = os.getenv("CLAUDE_FLOW_AUTO_EXECUTE", "true").lower() in ("true", "1", "yes")

# 복잡도 판정(자동 Plan 진입) 임계값
CLAUDE_FLOW_COMPLEX_TASK_CHAR_THRESHOLD = int(os.getenv("CLAUDE_FLOW_COMPLEX_TASK_CHAR_THRESHOLD", "120"))

# Plan step 실행 시 step별 최대 반복 횟수 (무한 루프 방지)
CLAUDE_FLOW_STEP_MAX_ITERATIONS = int(os.getenv("CLAUDE_FLOW_STEP_MAX_ITERATIONS", "25"))

# Interactive Plan Mode output directory
PLAN_DIR = os.getenv("PLAN_DIR", "~/.common_ai_agent/plans")

# Interactive Plan Mode debug (message flow)
PLAN_MODE_DEBUG = os.getenv("PLAN_MODE_DEBUG", "false").lower() in ("true", "1", "yes")
PLAN_MODE_DEBUG_FULL = os.getenv("PLAN_MODE_DEBUG_FULL", "false").lower() in ("true", "1", "yes")
PLAN_MODE_STREAM = os.getenv("PLAN_MODE_STREAM", "false").lower() in ("true", "1", "yes")

# Interactive Plan Mode context options
PLAN_MODE_CONTEXT_MODE = os.getenv("PLAN_MODE_CONTEXT_MODE", "full").strip().lower()
if PLAN_MODE_CONTEXT_MODE not in ("full", "summary", "recent"):
    PLAN_MODE_CONTEXT_MODE = "full"
PLAN_MODE_CONTEXT_RECENT_N = int(os.getenv("PLAN_MODE_CONTEXT_RECENT_N", "12"))
PLAN_MODE_CONTEXT_INCLUDE_SYSTEM = os.getenv("PLAN_MODE_CONTEXT_INCLUDE_SYSTEM", "false").lower() in ("true", "1", "yes")
PLAN_MODE_CONTEXT_MAX_CHARS = int(os.getenv("PLAN_MODE_CONTEXT_MAX_CHARS", "0"))

# ============================================================
# Phase 3: Claude Flow Complete Implementation
# ============================================================

# Explore agent 개수 (Plan Mode에서 병렬 탐색)
PLAN_MODE_EXPLORE_COUNT = int(os.getenv("PLAN_MODE_EXPLORE_COUNT", "3"))

# Explore agents를 병렬로 실행할지 여부
PLAN_MODE_PARALLEL_EXPLORE = os.getenv("PLAN_MODE_PARALLEL_EXPLORE", "true").lower() in ("true", "1", "yes")

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

Planning Tools (for complex multi-step tasks):
12. create_plan(task_description="description", steps="step1\\nstep2\\nstep3")
13. get_plan() - View current plan
14. mark_step_done(step_number=1) - Mark step as completed
15. wait_for_plan_approval() - Pause and wait for user to review/edit plan
16. check_plan_status() - Check if plan was approved by user

Sub-Agent Tools:
30. background_task(agent="explore", prompt="find FIFO implementations") - Delegate to sub-agent
31. background_output(task_id="bg_xxxx") - Get background task result
32. todo_update(index=1, status="completed") - Update todo item status (1-based index)

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

Example 3 - Complex Task with Planning:
User: Design a complete REST API with authentication and testing.
Thought: This is a complex multi-step task. I should create a plan first.
Action: create_plan(task_description="REST API with Auth", steps="Create API routes\\nImplement authentication\\nWrite unit tests\\nRun tests\\nAnalyze results")
Observation: Plan created successfully in 'current_plan.md' with 5 steps.

Thought: Now I'll start with step 1. Let me check the plan.
Action: get_plan()
Observation: [Plan content showing all 5 steps]

Thought: I'll create the API routes module for step 1.
Action: write_file(path="api_routes.py", content=\"\"\"[full API code here]\"\"\")
Observation: Successfully wrote to 'api_routes.py'.

Thought: Step 1 is complete. Let me mark it done.
Action: mark_step_done(step_number=1)
Observation: Step 1 marked as done.

[Continue with remaining steps...]

WHEN TO USE PLAN MODE:
- Complex tasks with 3+ distinct steps
- Tasks requiring multiple file creation
- Tasks with dependencies between steps
- Design + testbench + simulation workflows
- Multi-module projects

HOW TO USE PLAN MODE:

Option A - Automatic Execution (AI-driven):
1. Create plan with create_plan()
2. Execute each step in order
3. Mark completed steps with mark_step_done()

Option B - Interactive Planning (User-approved, RECOMMENDED):
1. Create initial plan with create_plan()
2. Call wait_for_plan_approval() - This pauses execution
3. User reviews and edits current_plan.md
4. User adds 'APPROVED' to the file when ready
5. Call check_plan_status() to verify approval
6. If approved, execute steps one by one
7. Mark each step done with mark_step_done()

Example Interactive Workflow:
Thought: This is complex. I should get user approval first.
Action: create_plan(task_description="API Development", steps="Create routes\\nAdd authentication\\nWrite tests")
Observation: Plan created.
Action: wait_for_plan_approval()
Observation: Plan saved. Waiting for user approval...
[User edits plan and approves]
Action: check_plan_status()
Observation: Plan is APPROVED!
[Now proceed with execution]

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
   - Medium (3-5 steps): Consider TodoWrite for tracking
   - Complex (6+ steps): Automatically enters Plan Mode

2. **Tool Selection**:
   - **Parallel execution**: Use multiple read-only tools simultaneously
   - **Sequential execution**: Write tools create barriers
   - **Sub-agents**: Use background_task for delegation
   - **Todo tracking**: Use todo_write/todo_update for multi-step tasks

3. **Plan Mode** (automatic when complex):
   - System analyzes complexity automatically
   - Spawns Explore agents in parallel
   - Creates structured plan with approval
   - Executes with TodoTracker

You don't need to worry about complexity analysis - the system handles it automatically.
Focus on using the right tools for the task at hand.

"""

# ============================================================
# Tool Description System (OpenCode Integration)
# ============================================================

# Backup of original SYSTEM_PROMPT for legacy mode
LEGACY_SYSTEM_PROMPT = SYSTEM_PROMPT


def build_base_system_prompt(allowed_tools: set = None) -> str:
    """
    Build compact system prompt (~5K tokens).
    Tool descriptions are minimal (name + signature + when-to-use).
    Detailed examples removed — LLM infers usage from signatures.
    """
    if not ENABLE_TOOL_DESCRIPTIONS:
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
            # RAG tools disabled by default (set ENABLE_SMART_RAG=true to re-enable)
        ],
        "Git": [
            _tool_line("git_status", '', "Show working tree status."),
            _tool_line("git_diff", 'path', "Show unstaged changes."),
        ],
        "Task Management": [
            _tool_line("todo_write", 'tasks', "Track multi-step tasks (3+ steps). Format: [{content, activeForm, status}]."),
            _tool_line("todo_update", 'index, status', "Update task status (pending/in_progress/completed)."),
            _tool_line("create_plan", 'title, steps', "Create execution plan for complex tasks."),
            _tool_line("get_plan", '', "Get current plan."),
            _tool_line("mark_step_done", 'step_index', "Mark plan step as done."),
            _tool_line("wait_for_plan_approval", '', "Wait for user plan approval."),
            _tool_line("check_plan_status", '', "Check plan status."),
        ],
        "Sub-Agents": [
            _tool_line("background_task", 'agent, prompt', "Delegate to sub-agent (explore/plan/execute/review)."),
            _tool_line("background_output", 'task_id', "Get sub-agent result."),
            _tool_line("background_cancel", 'task_id', "Cancel sub-agent."),
            _tool_line("background_list", '', "List active sub-agents."),
        ],
    }

    # Spec navigation tool (pcie/ucie/nvme 등)
    if "spec_navigate" in tool_list:
        tool_lines["Spec Navigation"] = [
            _tool_line("spec_navigate", 'spec, node_id="root"',
                       "Navigate spec TOC hierarchy. spec='pcie'/'ucie'/'nvme'. "
                       "Start with node_id='root', drill down with returned ids. "
                       "Leaf node returns path → use read_lines to read content."),
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

    # ── BUILD PROMPT ──
    parts = []

    # Identity
    parts.append(
        "You are Common AI Agent, an intelligent coding agent.\n"
    )

    # Format
    parts.append(
        "FORMAT (strict ReAct loop):\n"
        "Thought: [reasoning]\n"
        "Action: tool_name(arg=\"value\")\n"
        "- Multiple Actions per turn = parallel execution.\n"
        "- Use triple quotes for multi-line: content=\"\"\"...\"\"\".\n"
        "- NEVER generate \"Observation:\" — the system provides it.\n"
    )

    # Tool table
    parts.append("TOOLS:\n")
    for category, lines in tool_lines.items():
        available = [l for l in lines if l is not None]
        if available:
            parts.append(f"{category}:")
            parts.extend(available)
            parts.append("")

    # Core rules (compressed)
    parts.append(
        "RULES:\n"
        "\n"
        "1. PARALLEL EXECUTION (MANDATORY):\n"
        "   - Output 3+ Actions per response when exploring/reading.\n"
        "   - Read-only tools are parallel-safe: read_file, read_lines, grep_file, list_dir, find_files, git_status, git_diff.\n"
        "   - Write tools create sequential barriers: write_file, replace_in_file, run_command.\n"
        "\n"
        "2. FILE OPERATIONS:\n"
        "   - New file → write_file(). Existing file → replace_in_file(). NEVER write_file() on existing.\n"
        "   - ALWAYS read_file/read_lines BEFORE replace_in_file. Copy exact text including indentation.\n"
        "   - Include 5+ lines of context in old_text for unique matching.\n"
        "\n"
        "3. LARGE FILE STRATEGY:\n"
        "   - Files >500 lines: grep_file first → read_lines on found sections. Never blind-read.\n"
        "\n"
        "4. SEARCH PRIORITY: grep_file > find_files > list_dir.\n"
        "\n"
        "5. ANTI-HALLUCINATION:\n"
        "   - Never analyze a file you haven't read. Never invent tool results.\n"
        "   - If tool fails, adapt search — don't pretend results exist.\n"
    )

    # .UPD_RULE.md — global then project (like CLAUDE.md hierarchy)
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
    if _upd_rule_parts:
        parts.append("\n=== PROJECT RULES ===\n" + "\n\n".join(_upd_rule_parts) + "\n=====================")

    return "\n".join(parts)


# Update SYSTEM_PROMPT to use new tool description system
# This will be overridden by build_system_prompt() in main.py when needed
SYSTEM_PROMPT = build_base_system_prompt()
