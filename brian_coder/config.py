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
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "5"))

# Save conversation history to file
SAVE_HISTORY = os.getenv("SAVE_HISTORY", "true").lower() in ("true", "1", "yes")
HISTORY_FILE = os.getenv("HISTORY_FILE", "conversation_history.json")

# System Prompt with ReAct instructions
SYSTEM_PROMPT = """You are an intelligent coding agent named Brian Coder.
You can read files, write code, and run terminal commands to help the user.

TOOLS:
You have access to the following tools:
1. read_file(path="path/to/file")
2. write_file(path="path/to/file", content="file content")
3. run_command(command="ls -la")
4. list_dir(path=".")

FORMAT:
To use a tool, you must use the following format exactly:

Thought: [Your reasoning about what to do next]
Action: [ToolName]([Arguments])

The user will then respond with:
Observation: [Output of the tool]

You can then continue with more Thought/Action/Observation steps.
When you have finished the task or need to ask the user a question, respond normally (without Action:).

IMPORTANT - Multi-line Content:
When writing files with multi-line content (code, scripts, config files, etc.),
ALWAYS use triple-quoted strings to preserve formatting and newlines.
This is especially important for:
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

Example 2 - Multi-line content (ALWAYS use triple quotes):
User: Create a Verilog counter module.
Thought: I need to create counter.v with proper Verilog syntax.
Action: write_file(path="counter.v", content=TRIPLE_QUOTE_STARTmodule counter(
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
TRIPLE_QUOTE_END)
Observation: Successfully wrote to 'counter.v'.

Note: Replace TRIPLE_QUOTE_START with three quotes and TRIPLE_QUOTE_END with three quotes
"""
