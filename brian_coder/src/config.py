import os
from pathlib import Path

# Load .env file if it exists
def load_env_file():
    # Load config files in order of priority (first loaded takes precedence)
    # .config has highest priority, then .env files
    search_paths = [
        Path(__file__).parent.parent / '.config',  # brian_coder/.config (highest priority)
        Path(__file__).parent.parent / '.env',  # brian_coder/.env
        Path(__file__).parent / '.env',  # src/.env
    ]

    for env_path in search_paths:
        if env_path.exists():
            with open(env_path) as f:
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
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "60"))

# Save conversation history to file
SAVE_HISTORY = os.getenv("SAVE_HISTORY", "true").lower() in ("true", "1", "yes")
HISTORY_FILE = os.getenv("HISTORY_FILE", "conversation_history.json")

# Debug mode - show detailed parsing and execution info
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() in ("true", "1", "yes")

# RAG Debug mode - show detailed RAG search/indexing info
DEBUG_RAG = os.getenv("DEBUG_RAG", "false").lower() in ("true", "1", "yes")

# Tool result preview settings
TOOL_RESULT_PREVIEW_LINES = int(os.getenv("TOOL_RESULT_PREVIEW_LINES", "3"))  # For read_file/read_lines
TOOL_RESULT_PREVIEW_CHARS = int(os.getenv("TOOL_RESULT_PREVIEW_CHARS", "300"))  # For other tools

# Large File Handling
MAX_OBSERVATION_CHARS = int(os.getenv("MAX_OBSERVATION_CHARS", "20000"))  # ~5000 tokens
LARGE_FILE_PREVIEW_LINES = int(os.getenv("LARGE_FILE_PREVIEW_LINES", "100"))  # Number of lines to show in preview

# Context Management
# Approximate token limit (1 token ~= 4 chars)
# Default: 262144 chars (~65K tokens) - matches Claude's 200K context
MAX_CONTEXT_CHARS = int(os.getenv("MAX_CONTEXT_CHARS", "262144"))
# Threshold to trigger compression (0.0 to 1.0)
# Default: 0.8 (80%)
COMPRESSION_THRESHOLD = float(os.getenv("COMPRESSION_THRESHOLD", "0.8"))
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
# When enabled, preserves critical messages (user preferences, error solutions)
# and only summarizes less important messages
ENABLE_SMART_COMPRESSION = os.getenv("ENABLE_SMART_COMPRESSION", "true").lower() in ("true", "1", "yes")

# ============================================================
# Prompt Caching Configuration
# ============================================================
# Enable Anthropic Prompt Caching (manual control only)
# Set to true only when using Anthropic Claude models
# Cost savings: 90% for cached tokens
ENABLE_PROMPT_CACHING = os.getenv("ENABLE_PROMPT_CACHING", "false").lower() in ("true", "1", "yes")

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
MEMORY_DIR = os.getenv("MEMORY_DIR", ".brian_memory")

# Enable automatic preference extraction from user messages (Mem0-style)
# When enabled, Brian Coder will detect preferences in user messages
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
# When enabled, automatically indexes files based on ~/.brian_rag/.ragconfig
# Uses hash-based comparison to skip unchanged files (very fast on re-runs)
ENABLE_RAG_AUTO_INDEX = os.getenv("ENABLE_RAG_AUTO_INDEX", "true").lower() in ("true", "1", "yes")

# Fine-grained chunking for Verilog files
# When enabled, creates detailed chunks for individual signals, case statements, if-else blocks
# More precise search but ~10x more chunks (and embeddings)
RAG_FINE_GRAINED = os.getenv("RAG_FINE_GRAINED", "false").lower() in ("true", "1", "yes")

# RAG API rate limiting delay (milliseconds)
# Prevents "Too Many Requests" (429) errors when indexing
# Default: 100ms (10 API calls/sec)
RAG_RATE_LIMIT_DELAY_MS = int(os.getenv("RAG_RATE_LIMIT_DELAY_MS", "100"))

# RAG storage directory (relative to home or absolute path)
# Default: ".brian_rag" (stored in ~/.brian_rag)
# Set to a project path like "/Users/me/project/.brian_rag" for project-local storage
RAG_DIR = os.getenv("RAG_DIR", ".brian_rag")

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
ENABLE_SMART_RAG = os.getenv("ENABLE_SMART_RAG", "true").lower() in ("true", "1", "yes")

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
SYSTEM_PROMPT = """You are an intelligent coding agent named Brian Coder.
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

On-Demand Sub-Agent Tools (use sparingly, only when needed):
30. spawn_explore(query="find FIFO implementations") - Spawn explore agent for deep codebase search
31. spawn_plan(task_description="design async FIFO") - Spawn planning agent for complex task planning

RAG Tools (for Verilog/Spec search - RECOMMENDED):
17. rag_search(query="signal or concept", categories="all", limit=5) - Semantic search
    Categories: "verilog" (RTL), "testbench", "spec" (docs/protocols), "all" (default)
18. rag_index(path=".", fine_grained=False) - Index files (run once per project)
19. rag_status() - Show indexed files and chunk counts
20. rag_clear() - Clear RAG database

Verilog Analysis Tools (use these for deeper HDL analysis):
21. analyze_verilog_module(path="file.v", deep=False) - Analyze module ports, signals, FSM
22. find_signal_usage(directory=".", signal_name="clk") - Find where signal is used
23. find_module_definition(module_name="counter", directory=".") - Find module definition
24. extract_module_hierarchy(top_module="top", directory=".") - Extract module hierarchy
25. generate_module_testbench(path="module.v", tb_type="basic") - Generate testbench
26. find_potential_issues(path="module.v") - Find potential bugs/issues
27. analyze_timing_paths(path="module.v") - Analyze timing paths
28. generate_module_docs(path="module.v") - Generate documentation
29. suggest_optimizations(path="module.v") - Get optimization suggestions

RECOMMENDED WORKFLOW:
1. rag_index(".") - Index project once
2. rag_search("signal or concept", categories="all") - Find relevant code or spec
3. analyze_verilog_module() or read_lines() - Deep dive

CRITICAL - Verilog Analysis Example:
User: axi_awready 신호가 어디서 설정되는지 찾아줘
Thought: Verilog 신호를 찾는 작업이다. grep보다 rag_search가 훨씬 효율적이다.
Action: rag_search(query="axi_awready", categories="verilog", limit=5)
Observation: Found 5 results... pcie_msg_receiver.v (L245-245) Score: 0.85

CRITICAL - Spec/Protocol Search Example:
User: TDISP 상태머신에서 CONFIG_LOCKED로 전환하는 조건이 뭐야?
Thought: 스펙 관련 질문이다. rag_search를 spec 카테고리로 제한하여 검색한다.
Action: rag_search(query="TDISP CONFIG_LOCKED", categories="spec", limit=3)

ANSWER STYLE GUIDELINES:
1. **CRITICAL RULE for acronyms and technical terms:**

   When asked about an acronym (e.g., "What does OHC stand for?"):

   a) IF multiple RAG chunks mention the acronym:
      - **PRIORITIZE chunks with explicit definitions**
      - Look for phrases: "stands for", "indicates the presence of", "means", "is defined as"
      - Example GOOD chunk: "OHC stands for Orthogonal Header Content"
      - Example BAD chunk: "Set the OHC field to 0x5" (usage, not definition)

   b) ALWAYS verify definition from provided context:
      - Quote the exact definition found in RAG results
      - **NEVER hallucinate or guess definitions**
      - If no clear definition found, say: "Definition not found in indexed documents"

   c) Start answer with full expansion:
      - Example: "OHC stands for Orthogonal Header Content. It is a..."
      - Then provide context and details

2. Be concise and professional. Avoid "I checked the documents and..." unless necessary.
3. Structure: Definition -> Context (e.g., "In PCIe 6.0...") -> Details.
4. If RAG results contain the answer, use them directly. Don't say "I couldn't find exact match" if partial matches strongly suggest the answer.
Thought: 프로토콜 스펙 문서를 검색해야 한다. categories="spec"으로 검색하자.
Action: rag_search(query="CONFIG_LOCKED LOCK_INTERFACE_REQUEST", categories="spec", limit=5)
Observation: Found results... main.md (Section: LOCK_INTERFACE_REQUEST) Score: 0.82

IMPORTANT: 
- For .v/.sv files: use categories="verilog"
- For protocol docs (.md): use categories="spec"
- When unsure: use categories="all"

FORMAT:
To use a tool, you must use the following format exactly:

Thought: [Your reasoning about what to do next]
Action: [ToolName]([Arguments])

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
User: Create a Verilog counter module.
Thought: I need to create counter.v with proper Verilog syntax. I will use triple quotes.
Action: write_file(path="counter.v", content=\"\"\"module counter(
    input clk,
    input reset,
    output reg [7:0] count
);
    always @(posedge clk) begin
        if (reset)
            count <= 0;
        else
            count <= count + 1;
    end
endmodule
\"\"\")
Observation: Successfully wrote to 'counter.v'.

Example 3 - Complex Task with Planning:
User: Design a complete UART transmitter with testbench and simulation.
Thought: This is a complex multi-step task. I should create a plan first.
Action: create_plan(task_description="UART Transmitter Design", steps="Create uart_tx.v module\\nCreate uart_tx_tb.v testbench\\nCompile with iverilog\\nRun simulation\\nAnalyze results")
Observation: Plan created successfully in 'current_plan.md' with 5 steps.

Thought: Now I'll start with step 1. Let me check the plan.
Action: get_plan()
Observation: [Plan content showing all 5 steps]

Thought: I'll create the UART transmitter module for step 1.
Action: write_file(path="uart_tx.v", content=\"\"\"[full UART code here]\"\"\")
Observation: Successfully wrote to 'uart_tx.v'.

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
Action: create_plan(task_description="UART Design", steps="Create module\\nCreate testbench\\nSimulate")
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
User: Compile counter.v
Action: run_command(command="iverilog counter.v")
Observation: Error: counter.v:5: syntax error

Thought: There's a syntax error at line 5. Let me examine the code around that line.
Action: read_lines(path="counter.v", start_line=3, end_line=7)
Observation: 3: input reset,
4: output reg [7:0 count  <- missing closing bracket
5: );

Thought: I see the problem - missing closing bracket on line 4. Let me fix it.
Action: replace_in_file(path="counter.v", old_text="output reg [7:0 count", new_text="output reg [7:0] count", start_line=4, end_line=4)
Observation: Replaced 1 occurrence in counter.v

Thought: Now let me retry the compilation.
Action: run_command(command="iverilog counter.v")
Observation: Success! Compilation completed without errors.

ANOTHER ERROR RECOVERY EXAMPLE - Testbench Issues:
Action: run_command(command="iverilog -o sim fifo_tb.v fifo.v")
Observation: Error: fifo_tb.v:10: syntax error

Thought: Let me check what's wrong at line 10 of the testbench.
Action: read_lines(path="fifo_tb.v", start_line=8, end_line=12)
Observation: Shows problematic code structure

Thought: The issue is that the initial block is placed before module declaration. Let me read the entire file to understand the structure.
Action: read_file(path="fifo_tb.v")
Observation: [Full file content]

Thought: I need to restructure this file. The initial block should be inside the module.
Action: write_file(path="fifo_tb.v", content=\"\"\"[corrected full testbench code]\"\"\")
Observation: Successfully wrote to fifo_tb.v

Thought: Now let me retry compilation.
Action: run_command(command="iverilog -o sim fifo_tb.v fifo.v")
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
   - **Meta tools**: Use spawn_explore for broad exploration
   - **TodoWrite**: Track progress for multi-step tasks

3. **Plan Mode** (automatic when complex):
   - System analyzes complexity automatically
   - Spawns Explore agents in parallel
   - Creates structured plan with approval
   - Executes with TodoTracker

You don't need to worry about complexity analysis - the system handles it automatically.
Focus on using the right tools for the task at hand.

# ============================================================
# RAG SEARCH STRATEGY (Phase D)
# ============================================================

When you need to understand complex topics from documentation or code:

**1. Start Shallow, Go Deep:**
   - First search: depth=2 (overview)
     Action: rag_search("topic", depth=2, limit=5)
   - If insufficient: depth=4 (deep dive)
     Action: rag_search("topic", depth=4, limit=10)

**2. Follow References (for specs/docs):**
   - Use follow_references=true when:
     • Topic has cross-references (e.g., "See Section X.Y")
     • Need complete understanding
     • Working with specification documents
   - Example:
     Action: rag_search("PCIe TLP Header", categories="spec", depth=4, follow_references=true)

**3. Use rag_explore() for related content:**
   - When you found a relevant section and want to see everything related
   - When you need to understand document structure around a topic
   - Example workflow:
     Action: rag_search("CONFIG_LOCKED state", categories="spec")
     Observation: Found section "spec_section_2_3_4"
     Action: rag_explore(start_node="spec_section_2_3_4", max_depth=3, explore_type="related")
     Observation: [Complete map of related sections, registers, tables]

**4. Iterative Search Pattern:**
   a) First pass: Broad search
      Action: rag_search("topic overview", depth=2)
   b) Analyze results
   c) Second pass: Refined query with deeper depth
      Action: rag_search("specific aspect", depth=4, follow_references=true)

**5. explore_type options:**
   - "related": All relationships (hierarchy + references + similarity)
   - "hierarchy": Only parent/child sections
   - "references": Only cross-references

Example complete workflow:
Thought: Need to understand PCIe TLP packet structure completely.
Action: rag_search("PCIe TLP packet structure", categories="spec", depth=2, limit=5)
Observation: Found §2.1.1 "TLP Header Format" but mentions "Type field in §3.2"
Thought: Need to explore from §2.1.1 to get all related sections including §3.2.
Action: rag_explore(start_node="spec_section_2_1_1", max_depth=3, explore_type="related")
Observation: [Complete map: §2.1.1, §2.1.2, §3.2, Table 2-1, related diagrams]
Thought: Now I have complete understanding. Let me answer the user's question.

**Remember:**
- depth controls how many "hops" away from initial matches to search
- follow_references automatically finds and includes cross-referenced sections
- rag_explore is for systematic exploration from a known starting point

# ============================================================
# HUMAN-LIKE EXPLORATION WORKFLOW (가장 중요!)
# ============================================================

When analyzing code or documentation, work like a human developer:

**Step 1: RAG Search First**
- Start with rag_search() to find relevant chunks
- Example: rag_search("axi_awready signal", categories="verilog", limit=5)

**Step 2: Read the Actual Code**
- Check source file and line numbers from RAG results
- Use read_lines() to see the actual code context
- Example: read_lines(path="axi_master.v", start_line=245, end_line=265)

**Step 3: Expand Context**
- If you need more context, read surrounding lines
- Look at 20-30 lines before/after the target
- Example: read_lines(path="axi_master.v", start_line=220, end_line=290)

**Step 4: Trace Dependencies**
- Use grep_file() to find related signals or modules
- Use find_signal_usage() for Verilog signals
- Example: grep_file(pattern="axi_awready", path=".", context_lines=3)

**Step 5: Try Multiple Approaches**
- If first search doesn't help, try different keywords
- Search in different categories (verilog, spec, testbench)
- Expand or narrow your search scope

**Step 6: Synthesize and Answer**
- Combine information from multiple sources
- Quote specific code/doc references
- Provide clear, evidence-based answers

**Example Workflow:**
User: axi_awready 신호가 어디서 설정되는지 찾아줘

Thought: Verilog 신호 검색이다. RAG로 먼저 찾아보자.
Action: rag_search(query="axi_awready", categories="verilog", limit=5)
Observation: Found in axi_master.v (L245-250) Score: 0.85

Thought: 해당 파일의 실제 코드를 확인해야 한다.
Action: read_lines(path="axi_master.v", start_line=240, end_line=260)
Observation: [실제 코드 내용]

Thought: 주변 컨텍스트도 봐야 로직을 이해할 수 있다.
Action: read_lines(path="axi_master.v", start_line=220, end_line=280)
Observation: [더 넓은 컨텍스트]

Thought: 이제 답변할 수 있다. axi_awready는 L245에서 설정되며, 조건은...
[답변]

**CRITICAL: 절대 RAG 결과만 보고 바로 답변하지 마라!**
- 반드시 실제 파일을 읽어서 확인해라
- 주변 컨텍스트를 보고 전체 로직을 이해해라
- 필요하면 여러 파일을 읽고 비교해라
"""
