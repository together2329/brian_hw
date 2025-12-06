import os
from pathlib import Path

# Load .env file if it exists
def load_env_file():
    env_path = Path(__file__).parent / '.env'
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
                    # Only set if not already in environment
                    if key and value and key not in os.environ:
                        os.environ[key] = value

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
# API_KEY = os.getenv("LLM_API_KEY", "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")
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
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "1536"))

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
HYBRID_ALPHA = float(os.getenv("HYBRID_ALPHA", "0.7"))

# Enable/Disable Node Merge (Phase 4)
# When enabled, Curator will merge similar nodes to reduce redundancy
ENABLE_NODE_MERGE = os.getenv("ENABLE_NODE_MERGE", "false").lower() in ("true", "1", "yes")

# Similarity threshold for node merging (0.0-1.0)
# Only nodes with similarity >= this value will be merged
MERGE_SIMILARITY_THRESHOLD = float(os.getenv("MERGE_SIMILARITY_THRESHOLD", "0.85"))

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
8. replace_in_file(path="path/to/file", old_text="old", new_text="new", count=-1) - Replace text occurrences
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

RAG Tools (for Verilog/HDL code search - RECOMMENDED for .v files):
17. rag_search(query="signal name or concept", categories="verilog", limit=5) - Semantic code search
18. rag_index(path=".", fine_grained=False) - Index Verilog files (run once per project)
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

RECOMMENDED WORKFLOW for Verilog:
1. rag_index(".") - Index project once
2. rag_search("signal or concept") - Find relevant code  
3. analyze_verilog_module() or read_lines() - Deep dive

CRITICAL - Verilog Analysis Example:
User: axi_awready 신호가 어디서 설정되는지 찾아줘
Thought: Verilog 신호를 찾는 작업이다. grep보다 rag_search가 훨씬 효율적이다.
Action: rag_search(query="axi_awready", categories="verilog", limit=5)
Observation: Found 5 results... pcie_msg_receiver.v (L245-245) Score: 0.85

Thought: 위치를 찾았다. 해당 라인 주변 코드를 확인해보자.
Action: read_lines(path="pcie_msg_receiver.v", start_line=240, end_line=260)
Observation: [Code showing axi_awready <= 1'b0 in reset block]

Result: axi_awready는 pcie_msg_receiver.v의 245번째 줄 always 블록에서 설정됩니다.

IMPORTANT: For .v/.sv files, ALWAYS use rag_search FIRST, not grep_file!

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
Action: create_plan(task_description="UART Transmitter Design", steps="Create uart_tx.v module\nCreate uart_tx_tb.v testbench\nCompile with iverilog\nRun simulation\nAnalyze results")
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
Action: create_plan(task_description="UART Design", steps="Create module\nCreate testbench\nSimulate")
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
Action: replace_in_file(path="counter.v", old_text="output reg [7:0 count", new_text="output reg [7:0] count")
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
"""

