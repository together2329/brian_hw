import sys
import os
import json
import urllib.request
import urllib.error
import re
import copy
import config
import tools

# --- 1. No Vendor Path Needed ---
# We are using standard libraries only.

# --- 2. API Client (urllib) ---

import time

# --- Global Token Tracking ---
# Stores actual token counts from API responses
# Structure: {"message_index": actual_token_count}
actual_token_cache = {}
last_input_tokens = 0  # Last reported input tokens from API

# --- Color Utilities (ANSI Escape Codes) ---

class Color:
    """ANSI color codes for terminal output"""
    # Basic colors
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    
    # Styles
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RESET = '\033[0m'
    
    @staticmethod
    def system(text):
        """System messages - Cyan"""
        return f"{Color.CYAN}{text}{Color.RESET}"
    
    @staticmethod
    def user(text):
        """User messages - Green"""
        return f"{Color.GREEN}{text}{Color.RESET}"
    
    @staticmethod
    def agent(text):
        """Agent messages - Blue"""
        return f"{Color.BLUE}{text}{Color.RESET}"
    
    @staticmethod
    def tool(text):
        """Tool names - Magenta"""
        return f"{Color.MAGENTA}{text}{Color.RESET}"
    
    @staticmethod
    def success(text):
        """Success messages - Green + Bold"""
        return f"{Color.BOLD}{Color.GREEN}{text}{Color.RESET}"
    
    @staticmethod
    def warning(text):
        """Warning messages - Yellow"""
        return f"{Color.YELLOW}{text}{Color.RESET}"
    
    @staticmethod
    def error(text):
        """Error messages - Red + Bold"""
        return f"{Color.BOLD}{Color.RED}{text}{Color.RESET}"
    
    @staticmethod
    def info(text):
        """Info messages - Cyan + Dim"""
        return f"{Color.DIM}{Color.CYAN}{text}{Color.RESET}"

def chat_completion_stream(messages):
    """
    Sends a chat completion request to the LLM using urllib.
    Yields content chunks from the SSE stream.
    Supports Anthropic Prompt Caching when enabled.
    Updates global actual_token_cache with real token counts from API.
    """
    global last_input_tokens

    # Rate limiting: Configurable delay
    if config.RATE_LIMIT_DELAY > 0:
        print(Color.info(f"[System] Waiting {config.RATE_LIMIT_DELAY}s for rate limit..."))
        time.sleep(config.RATE_LIMIT_DELAY)

    # Apply prompt caching if enabled (deepcopy to preserve original)
    processed_messages = messages
    if config.ENABLE_PROMPT_CACHING and is_anthropic_provider():
        processed_messages = copy.deepcopy(messages)
        processed_messages = apply_cache_breakpoints(processed_messages)

    url = f"{config.BASE_URL}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.API_KEY}",
        "User-Agent": "BrianCoder/1.0"
    }

    # Add Anthropic-specific headers if caching enabled
    if config.ENABLE_PROMPT_CACHING and is_anthropic_provider():
        headers["anthropic-beta"] = "prompt-caching-2024-07-31"
        if config.DEBUG_MODE:
            print(Color.info("[System] Prompt caching enabled - added anthropic-beta header"))

    data = {
        "model": config.MODEL_NAME,
        "messages": processed_messages,
        "stream": True,
        "stream_options": {"include_usage": True}  # Request usage data in streaming (OpenAI)
    }

    # Debug: Log request details
    if config.DEBUG_MODE:
        print(Color.info(f"\n[Request Debug]"))
        print(Color.info(f"  URL: {url}"))
        print(Color.info(f"  Model: {config.MODEL_NAME}"))
        print(Color.info(f"  Messages count: {len(processed_messages)}"))

        # Estimate total tokens
        total_chars = sum(len(str(m.get('content', ''))) for m in processed_messages)
        estimated_tokens = total_chars // 4
        print(Color.info(f"  Estimated input tokens: {estimated_tokens:,}"))

        # Check if structured content (caching applied)
        has_structured = any(isinstance(m.get('content'), list) for m in processed_messages)
        print(Color.info(f"  Structured content (caching): {has_structured}"))

        # Show first message structure
        if processed_messages:
            first_content = processed_messages[0].get('content', '')
            if isinstance(first_content, list):
                print(Color.info(f"  First message: [list with {len(first_content)} blocks]"))
            else:
                print(Color.info(f"  First message: [string, {len(str(first_content))} chars]"))
        print()

    try:
        req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers)
        with urllib.request.urlopen(req, timeout=config.API_TIMEOUT) as response:
            # Parse Server-Sent Events (SSE)
            usage_info = None
            for line in response:
                line = line.decode('utf-8').strip()
                if line.startswith("data: "):
                    data_str = line[6:] # Remove "data: " prefix
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk_json = json.loads(data_str)

                        # Extract usage information (both OpenAI and Anthropic formats)
                        if "usage" in chunk_json:
                            usage_info = chunk_json["usage"]

                        # Extract content delta
                        # Structure: choices[0].delta.content
                        if "choices" in chunk_json and len(chunk_json["choices"]) > 0:
                            delta = chunk_json["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                    except json.JSONDecodeError:
                        continue

            # Update global token tracking with actual values from API
            if usage_info:
                # Both OpenAI and Anthropic use "input_tokens" or "prompt_tokens"
                input_tokens = usage_info.get("input_tokens") or usage_info.get("prompt_tokens", 0)
                output_tokens = usage_info.get("output_tokens") or usage_info.get("completion_tokens", 0)
                if input_tokens > 0:
                    last_input_tokens = input_tokens

                # Display actual token usage in DEBUG mode
                if config.DEBUG_MODE:
                    total_tokens = input_tokens + output_tokens
                    print(f"\n{Color.info('[Token Usage]')}")
                    print(f"{Color.info(f'  Input: {input_tokens:,} tokens')}")
                    print(f"{Color.info(f'  Output: {output_tokens:,} tokens')}")
                    print(f"{Color.info(f'  Total: {total_tokens:,} tokens')}\n")

            # Display usage information if available and caching is enabled
            if usage_info and config.ENABLE_PROMPT_CACHING and is_anthropic_provider():
                input_tokens = usage_info.get("input_tokens", 0)
                output_tokens = usage_info.get("output_tokens", 0)
                cache_creation_tokens = usage_info.get("cache_creation_input_tokens", 0)
                cache_read_tokens = usage_info.get("cache_read_input_tokens", 0)

                if cache_creation_tokens > 0 or cache_read_tokens > 0:
                    print(f"\n\n{Color.info('[Token Usage]')}")
                    print(f"{Color.info(f'  Input: {input_tokens:,} tokens')}")
                    print(f"{Color.info(f'  Output: {output_tokens:,} tokens')}")
                    if cache_creation_tokens > 0:
                        print(f"{Color.info(f'  Cache Created: {cache_creation_tokens:,} tokens')}")
                    if cache_read_tokens > 0:
                        savings = int(cache_read_tokens * 0.9)
                        print(f"{Color.success(f'  Cache Hit: {cache_read_tokens:,} tokens (saved ~{savings:,} tokens worth of cost!)')}\n")
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        yield f"\n{Color.error(f'[HTTP Error {e.code}]: {e.reason}')}\n"

        # Try to parse error JSON
        try:
            error_json = json.loads(error_body)
            yield f"{Color.error('Error Details:')}\n"
            if 'error' in error_json:
                error_info = error_json['error']
                if isinstance(error_info, dict):
                    error_type = error_info.get('type', 'unknown')
                    error_message = error_info.get('message', 'No message')
                    yield f"{Color.error(f'  Type: {error_type}')}\n"
                    yield f"{Color.error(f'  Message: {error_message}')}\n"
                else:
                    yield f"{Color.error(f'  {error_info}')}\n"
            else:
                yield f"{Color.error(f'  {error_json}')}\n"
        except:
            yield f"{Color.error(f'Raw Error Body:')}\n{error_body[:500]}\n"

        # Debug: Show request info that caused error
        if config.DEBUG_MODE:
            yield f"\n{Color.info('[Debug Info]')}\n"
            yield f"{Color.info(f'  Model: {config.MODEL_NAME}')}\n"
            yield f"{Color.info(f'  Message count: {len(processed_messages)}')}\n"
            total_chars = sum(len(str(m.get('content', ''))) for m in processed_messages)
            yield f"{Color.info(f'  Estimated tokens: {total_chars // 4:,}')}\n"

    except urllib.error.URLError as e:
        yield f"\n{Color.error(f'[Connection Error]: {e}')}"

# --- 3. History Management ---

def save_conversation_history(messages):
    """Saves conversation history to a JSON file if enabled in config."""
    if not config.SAVE_HISTORY:
        return

    try:
        with open(config.HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(messages, f, indent=2, ensure_ascii=False)
        print(Color.success(f"[System] History saved to {config.HISTORY_FILE}"))
    except Exception as e:
        print(Color.error(f"[System] Failed to save history: {e}"))

def load_conversation_history():
    """Loads conversation history from JSON file if it exists."""
    if not config.SAVE_HISTORY:
        return None

    try:
        if os.path.exists(config.HISTORY_FILE):
            with open(config.HISTORY_FILE, 'r', encoding='utf-8') as f:
                messages = json.load(f)
                print(Color.success(f"[System] Loaded {len(messages)} messages from {config.HISTORY_FILE}"))
                return messages
    except Exception as e:
        print(Color.error(f"[System] Failed to load history: {e}"))

    return None

# --- 4. ReAct Logic ---

def parse_action(text):
    """
    Parses the last 'Action: Tool(args)' from the text.
    Improved to handle triple-quotes and nested parentheses.
    """
    if config.DEBUG_MODE:
        print(f"[DEBUG] parse_action input: {text[:200]}...")

    # Find "Action: tool_name("
    pattern = r"Action:\s*(\w+)\("
    match = re.search(pattern, text, re.DOTALL)

    if not match:
        if config.DEBUG_MODE:
            print(f"[DEBUG] parse_action: No Action found")
        return None, None

    tool_name = match.group(1)
    start_pos = match.end()  # Position after "tool_name("

    # Find matching closing parenthesis
    paren_count = 1
    in_single_quote = False
    in_double_quote = False
    in_triple_single = False
    in_triple_double = False
    i = start_pos

    while i < len(text) and paren_count > 0:
        # Check for triple quotes first
        if i + 2 < len(text):
            if text[i:i+3] == '"""':
                if not in_single_quote and not in_triple_single:
                    in_triple_double = not in_triple_double
                    i += 3
                    continue
            elif text[i:i+3] == "'''":
                if not in_double_quote and not in_triple_double:
                    in_triple_single = not in_triple_single
                    i += 3
                    continue

        char = text[i]

        # Handle escape sequences
        if i > 0 and text[i-1] == '\\':
            i += 1
            continue

        # Track quotes (only if not in triple quotes)
        if not in_triple_single and not in_triple_double:
            if char == '"' and not in_single_quote:
                in_double_quote = not in_double_quote
            elif char == "'" and not in_double_quote:
                in_single_quote = not in_single_quote

        # Count parentheses (only if not in any quotes)
        if not (in_single_quote or in_double_quote or in_triple_single or in_triple_double):
            if char == '(':
                paren_count += 1
            elif char == ')':
                paren_count -= 1

        i += 1

    if paren_count == 0:
        args_str = text[start_pos:i-1]  # Extract arguments
        if config.DEBUG_MODE:
            print(f"[DEBUG] parse_action found: {tool_name}({args_str[:100]}...)")
        return tool_name, args_str
    else:
        if config.DEBUG_MODE:
            print(f"[DEBUG] parse_action: Unmatched parentheses")
        return None, None

def parse_tool_arguments(args_str):
    """
    Safely parses tool arguments from string.
    Supports: key="value", key='value', key=123, key=triple-quote
    Returns: (args_list, kwargs_dict)
    """
    args = []
    kwargs = {}

    # Trim whitespace
    args_str = args_str.strip()
    if not args_str:
        return args, kwargs

    i = 0
    while i < len(args_str):
        # Skip whitespace and commas
        while i < len(args_str) and args_str[i] in ' ,\n':
            i += 1

        if i >= len(args_str):
            break

        # Check if it's a keyword argument (key=value)
        key_match = re.match(r'(\w+)\s*=\s*', args_str[i:])

        if key_match:
            # Keyword argument
            key = key_match.group(1)
            i += key_match.end()

            # Parse value
            value, chars_consumed = parse_value(args_str[i:])
            kwargs[key] = value
            i += chars_consumed
        else:
            # Positional argument
            value, chars_consumed = parse_value(args_str[i:])
            args.append(value)
            i += chars_consumed

    return args, kwargs

def parse_value(text):
    """
    Parses a single value from text.
    Returns: (value, chars_consumed)
    """
    text = text.lstrip()

    if not text:
        return None, 0

    # Triple-quoted string (""" or ''')
    if text.startswith('"""') or text.startswith("'''"):
        quote = text[:3]
        end_pos = text.find(quote, 3)
        if end_pos == -1:
            raise ValueError(f"Unclosed triple-quote string")
        value = text[3:end_pos]
        return value, end_pos + 3

    # Regular quoted string (" or ')
    if text[0] in '"\'':
        quote = text[0]
        i = 1
        value = ""
        while i < len(text):
            if text[i] == '\\' and i + 1 < len(text):
                # Handle escape sequences
                next_char = text[i + 1]
                if next_char == 'n':
                    value += '\n'
                elif next_char == 't':
                    value += '\t'
                elif next_char == '\\':
                    value += '\\'
                elif next_char == quote:
                    value += quote
                else:
                    value += next_char
                i += 2
            elif text[i] == quote:
                return value, i + 1
            else:
                value += text[i]
                i += 1
        raise ValueError(f"Unclosed string")

    # Number or identifier
    match = re.match(r'([^,)\s]+)', text)
    if match:
        value_str = match.group(1)
        # Try to parse as number
        try:
            if '.' in value_str:
                return float(value_str), len(value_str)
            else:
                return int(value_str), len(value_str)
        except ValueError:
            # Return as string
            return value_str, len(value_str)

    return None, 0

def execute_tool(tool_name, args_str):
    if tool_name not in tools.AVAILABLE_TOOLS:
        return f"Error: Tool '{tool_name}' not found."

    func = tools.AVAILABLE_TOOLS[tool_name]
    try:
        # Parse arguments safely
        parsed_args, parsed_kwargs = parse_tool_arguments(args_str)

        if config.DEBUG_MODE:
            print(f"[DEBUG] Parsed args: {parsed_args}, kwargs: {parsed_kwargs}")

        result = func(*parsed_args, **parsed_kwargs)
        return result

    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        return f"Error parsing/executing arguments: {e}\n{error_detail}\nargs_str was: {args_str[:200]}"

# --- 5. Context Management ---

def estimate_tokens(messages):
    """Estimates token count based on characters (4 chars ~= 1 token)."""
    total_chars = sum(len(str(m.get("content", ""))) for m in messages)
    return total_chars // 4

# ============================================================
# Prompt Caching Helper Functions
# ============================================================

def is_anthropic_provider():
    """
    Detects if current provider is Anthropic based on BASE_URL or MODEL_NAME.

    Returns:
        bool: True if Anthropic API is being used
    """
    base_url_lower = config.BASE_URL.lower()
    model_lower = config.MODEL_NAME.lower()

    # Direct Anthropic API
    if "anthropic.com" in base_url_lower:
        return True

    # Claude models via OpenRouter or other proxies
    if "claude" in model_lower:
        return True

    return False

def estimate_message_tokens(message):
    """
    Estimates token count for a single message.
    Uses 4 chars ≈ 1 token heuristic.

    Args:
        message: dict with "content" field (str or list)

    Returns:
        int: estimated token count
    """
    content = message.get("content", "")

    # Handle string content
    if isinstance(content, str):
        return len(content) // 4

    # Handle structured content (list of blocks)
    if isinstance(content, list):
        total_chars = 0
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                total_chars += len(block.get("text", ""))
        return total_chars // 4

    return 0


def get_actual_tokens(messages):
    """
    Gets actual token count using hybrid approach:
    1. If we have actual token count from last API call, use it
    2. Otherwise, use estimation

    Args:
        messages: list of message dicts

    Returns:
        int: actual or estimated token count
    """
    global last_input_tokens

    # If we have recent actual token count from API, use it
    if last_input_tokens > 0:
        return last_input_tokens

    # Fallback to estimation
    return sum(estimate_message_tokens(m) for m in messages)


def get_token_count_from_api(messages):
    """
    [DEPRECATED - Not used by compress_history anymore]
    Gets actual token count from API without generating response.
    Uses max_tokens=1 to minimize cost and get usage info quickly.

    Note: compress_history now uses last_input_tokens from regular API calls
    instead of making additional API calls. This function is kept for
    potential future use.

    Args:
        messages: list of message dicts

    Returns:
        int: actual input token count, or 0 if failed
    """
    try:
        url = f"{config.BASE_URL}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.API_KEY}",
        }

        # Non-streaming request with minimal output
        data = {
            "model": config.MODEL_NAME,
            "messages": messages,
            "max_tokens": 1,  # Minimal output to save cost
            "stream": False   # Non-streaming to get usage immediately
        }

        req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))

            # Extract token count from usage
            if "usage" in result:
                usage = result["usage"]
                # Both OpenAI and Anthropic formats
                input_tokens = usage.get("input_tokens") or usage.get("prompt_tokens", 0)

                if config.DEBUG_MODE:
                    print(Color.info(f"[Token Count API] Got actual count: {input_tokens:,} tokens"))

                return input_tokens

    except Exception as e:
        if config.DEBUG_MODE:
            print(Color.warning(f"[Token Count API] Failed: {e}"))

    return 0

def _calculate_cache_interval(messages, max_breakpoints):
    """
    Dynamically calculates optimal cache interval based on message count.

    Args:
        messages: list of message dicts
        max_breakpoints: maximum allowed breakpoints (typically 3)

    Returns:
        int: interval between cache breakpoints
    """
    # Exclude system message from count
    message_count = len(messages) - 1  # -1 for system message

    if message_count <= 1:
        return 1

    # Reserve 1 breakpoint for system message
    available_breakpoints = max_breakpoints - 1

    if available_breakpoints <= 0:
        return message_count  # No dynamic breakpoints

    # Calculate interval to evenly distribute breakpoints
    interval = max(1, message_count // available_breakpoints)

    return interval

def convert_to_cache_format(content, add_cache_control=False):
    """
    Converts string content to structured format for prompt caching.

    Args:
        content: str or list (message content)
        add_cache_control: bool (whether to add cache control marker)

    Returns:
        list: structured content blocks
    """
    # Already in structured format
    if isinstance(content, list):
        if add_cache_control and content:
            # Add cache_control to last block
            content[-1]["cache_control"] = {"type": "ephemeral"}
        return content

    # Convert string to structured format
    block = {
        "type": "text",
        "text": content
    }

    if add_cache_control:
        block["cache_control"] = {"type": "ephemeral"}

    return [block]

def apply_cache_breakpoints(messages):
    """
    Applies cache breakpoints to messages based on configuration.

    Args:
        messages: list of message dicts (standard format)

    Returns:
        list: messages with cache_control applied (modified in-place)
    """
    if not config.ENABLE_PROMPT_CACHING:
        return messages

    if not is_anthropic_provider():
        if config.DEBUG_MODE:
            print(Color.info("[System] Prompt caching disabled: non-Anthropic provider"))
        return messages

    max_breakpoints = min(config.MAX_CACHE_BREAKPOINTS, 4)  # Anthropic max = 4
    breakpoint_count = 0

    # 1. System message always gets cache breakpoint (if exists and meets min tokens)
    if messages and messages[0].get("role") == "system":
        tokens = estimate_message_tokens(messages[0])
        if tokens >= config.MIN_CACHE_TOKENS:
            messages[0]["content"] = convert_to_cache_format(
                messages[0]["content"],
                add_cache_control=True
            )
            breakpoint_count += 1
            if config.DEBUG_MODE:
                print(Color.info(f"[System] Cache breakpoint 1/{max_breakpoints}: System message ({tokens} tokens)"))

    # 2. Dynamic breakpoints in message history
    if breakpoint_count < max_breakpoints and len(messages) > 1:
        # Determine interval
        if config.CACHE_INTERVAL > 0:
            interval = config.CACHE_INTERVAL
        else:
            interval = _calculate_cache_interval(messages, max_breakpoints)

        if config.DEBUG_MODE:
            print(Color.info(f"[System] Cache interval: {interval} messages"))

        # Apply breakpoints at intervals (working backwards from recent messages)
        # This ensures most recent context is cached
        for i in range(len(messages) - 1, 0, -interval):
            if breakpoint_count >= max_breakpoints:
                break

            tokens = estimate_message_tokens(messages[i])
            if tokens >= config.MIN_CACHE_TOKENS:
                messages[i]["content"] = convert_to_cache_format(
                    messages[i]["content"],
                    add_cache_control=True
                )
                breakpoint_count += 1
                if config.DEBUG_MODE:
                    print(Color.info(f"[System] Cache breakpoint {breakpoint_count}/{max_breakpoints}: Message {i} ({tokens} tokens)"))

    if config.DEBUG_MODE:
        print(Color.info(f"[System] Total cache breakpoints applied: {breakpoint_count}/{max_breakpoints}"))

    return messages

def show_context_usage(messages, use_actual=True):
    """
    Displays current context usage information.

    Args:
        messages: list of message dicts
        use_actual: if True, use actual tokens from API (hybrid mode)
    """
    if use_actual:
        current_tokens = get_actual_tokens(messages)
        source = "actual" if last_input_tokens > 0 else "estimated"
    else:
        current_tokens = sum(estimate_message_tokens(m) for m in messages)
        source = "estimated"

    limit_tokens = config.MAX_CONTEXT_CHARS // 4
    threshold_tokens = int(limit_tokens * config.COMPRESSION_THRESHOLD)

    usage_pct = int((current_tokens / limit_tokens) * 100) if limit_tokens > 0 else 0

    # Color coding based on usage
    if usage_pct >= 100:
        color = Color.error
        status = "OVER LIMIT"
    elif usage_pct >= 80:
        color = Color.warning
        status = "HIGH"
    elif usage_pct >= 50:
        color = Color.info
        status = "MEDIUM"
    else:
        color = Color.success
        status = "OK"

    bar_length = 20
    filled = int(bar_length * usage_pct / 100)
    bar = '█' * filled + '░' * (bar_length - filled)

    # Show source in debug mode
    if config.DEBUG_MODE:
        print(color(f"[Context: {current_tokens:,}/{limit_tokens:,} tokens ({usage_pct}%) {bar} {status}] ({source})"))
    else:
        print(color(f"[Context: {current_tokens:,}/{limit_tokens:,} tokens ({usage_pct}%) {bar} {status}]"))


def compress_history(messages):
    """
    Compresses history if it exceeds the token limit.
    Strategy: Keep System messages + Last N messages. Summarize the middle.
    Uses last_input_tokens from API (no additional API call).
    Supports both single and chunked compression modes.
    """
    if not config.ENABLE_COMPRESSION:
        return messages

    limit_tokens = config.MAX_CONTEXT_CHARS // 4
    threshold_tokens = int(limit_tokens * config.COMPRESSION_THRESHOLD)

    # Use last_input_tokens from previous API call (no additional API call)
    current_tokens = get_actual_tokens(messages)
    token_source = "actual" if last_input_tokens > 0 else "estimated"

    if current_tokens < threshold_tokens:
        return messages

    print(Color.warning(f"\n[System] Context size ({current_tokens:,} {token_source} tokens) exceeded threshold ({threshold_tokens:,}). Compressing..."))

    if not messages:
        return messages

    # Separate system messages from regular messages (like Strix)
    system_msgs = [m for m in messages if m.get("role") == "system"]
    regular_msgs = [m for m in messages if m.get("role") != "system"]

    # Check if history is too short
    keep_recent = config.COMPRESSION_KEEP_RECENT
    if len(regular_msgs) <= keep_recent:
        print(Color.info(f"[System] History too short to compress ({len(regular_msgs)} <= {keep_recent} recent)."))
        return messages

    # Keep last N messages
    recent_msgs = regular_msgs[-keep_recent:]
    old_msgs = regular_msgs[:-keep_recent]

    if not old_msgs:
        return messages

    # Choose compression mode
    mode = config.COMPRESSION_MODE.lower()

    if mode == "chunked":
        # Chunked compression (like Strix)
        print(Color.info(f"[System] Using chunked compression (chunk_size={config.COMPRESSION_CHUNK_SIZE})..."))
        compressed = _compress_chunked(old_msgs)
    else:
        # Single compression (default, faster and cheaper)
        print(Color.info("[System] Using single compression..."))
        compressed = [_compress_single(old_msgs)]

    # Construct new history: system messages + compressed + recent
    new_history = system_msgs + compressed + recent_msgs

    # Calculate new token count
    new_tokens = sum(estimate_message_tokens(m) for m in new_history)
    reduction_pct = int((1 - new_tokens / current_tokens) * 100) if current_tokens > 0 else 0

    print(Color.success(f"[System] Compression complete. Tokens reduced: {current_tokens:,} ({token_source}) -> {new_tokens:,} (estimated) = {reduction_pct}% reduction"))

    return new_history


def _compress_single(messages):
    """Single-pass compression: summarize all messages at once"""
    summary_prompt = "Summarize the following conversation history concisely. Focus on completed tasks, key decisions, and current state. Ignore minor chatter."

    conversation_text = ""
    for m in messages:
        role = m.get("role", "unknown")
        content = str(m.get("content", ""))[:1000]
        conversation_text += f"{role}: {content}\n"

    summary_request = [
        {"role": "system", "content": "You are a helpful assistant that summarizes conversation history for an AI agent."},
        {"role": "user", "content": f"{summary_prompt}\n\n{conversation_text}"}
    ]

    print(Color.info("[System] Generating summary..."), end="", flush=True)
    summary_content = ""
    try:
        for chunk in chat_completion_stream(summary_request):
            summary_content += chunk
        print(Color.success(" Done."))

        return {
            "role": "system",
            "content": f"[Previous Conversation Summary ({len(messages)} messages)]: {summary_content}"
        }
    except Exception as e:
        print(Color.error(f"\n[System] Failed to generate summary: {e}"))
        return messages[0] if messages else {"role": "system", "content": "[Compression failed]"}


def _compress_chunked(messages):
    """Chunked compression: summarize in chunks (like Strix)"""
    chunk_size = config.COMPRESSION_CHUNK_SIZE
    compressed = []

    total_chunks = (len(messages) + chunk_size - 1) // chunk_size
    print(Color.info(f"[System] Compressing {len(messages)} messages in {total_chunks} chunks..."))

    for i in range(0, len(messages), chunk_size):
        chunk = messages[i:i + chunk_size]
        chunk_num = i // chunk_size + 1

        print(Color.info(f"[System] Chunk {chunk_num}/{total_chunks}..."), end="", flush=True)

        summary_prompt = "Summarize the following conversation segment concisely. Focus on completed tasks, key decisions, and current state."

        conversation_text = ""
        for m in chunk:
            role = m.get("role", "unknown")
            content = str(m.get("content", ""))[:1000]
            conversation_text += f"{role}: {content}\n"

        summary_request = [
            {"role": "system", "content": "You are a helpful assistant that summarizes conversation history for an AI agent."},
            {"role": "user", "content": f"{summary_prompt}\n\n{conversation_text}"}
        ]

        try:
            summary_content = ""
            for chunk_data in chat_completion_stream(summary_request):
                summary_content += chunk_data

            compressed.append({
                "role": "system",
                "content": f"[Summary chunk {chunk_num}/{total_chunks} ({len(chunk)} messages)]: {summary_content}"
            })
            print(Color.success(" Done."))
        except Exception as e:
            print(Color.error(f" Failed: {e}"))
            # Keep original first message as fallback
            if chunk:
                compressed.append(chunk[0])

    return compressed

def process_observation(observation, messages):
    """
    Processes observation before adding to message history.
    Handles large file truncation and context management.
    Returns updated messages list.
    """
    # Check if adding observation would exceed context limit
    limit_tokens = config.MAX_CONTEXT_CHARS // 4
    threshold_tokens = int(limit_tokens * config.COMPRESSION_THRESHOLD)
    
    # Step 1: First check if observation itself is too large
    observation_msg = {"role": "user", "content": f"Observation: {observation}"}
    observation_tokens = estimate_message_tokens(observation_msg)

    if observation_tokens > limit_tokens * 0.3:  # Observation > 30% of limit (stricter)
        original_size = len(observation)
        lines = observation.split('\n')
        total_lines = len(lines)

        # Show first N lines as preview + guidance
        PREVIEW_LINES = config.LARGE_FILE_PREVIEW_LINES
        preview_lines = lines[:PREVIEW_LINES]
        preview = '\n'.join(preview_lines)
        
        # Safety Truncation: Ensure preview itself isn't too huge (e.g. if lines are very long)
        # Limit preview to 50% of MAX_OBSERVATION_CHARS
        MAX_PREVIEW_CHARS = config.MAX_OBSERVATION_CHARS // 2
        if len(preview) > MAX_PREVIEW_CHARS:
            preview = preview[:MAX_PREVIEW_CHARS] + f"\n... [Preview truncated at {MAX_PREVIEW_CHARS} chars] ..."

        # Calculate max readable lines (based on context limit)
        MAX_READABLE_LINES = (config.MAX_OBSERVATION_CHARS // 80)  # Assume ~80 chars per line

        observation = f"""[File Preview - Too large to display completely]

Showing first {PREVIEW_LINES} lines (Total: {total_lines:,} lines, {original_size:,} characters)

--- BEGIN PREVIEW ---
{preview}
--- END PREVIEW ---

💡 File is too large for full display. You can read up to ~{MAX_READABLE_LINES} lines at a time.

To read specific sections:
1. Use read_lines(path, start_line, end_line)
   Examples:
   - read_lines(path, start_line=100, end_line=200)           # Lines 100-200
   - read_lines(path, start_line={max(1, total_lines-100)}, end_line={total_lines})  # Last 100 lines

2. Use grep_file(pattern, path) to search for patterns
   Example:
   - grep_file(pattern="module\\s+\\w+", path)   # Find modules
   - grep_file(pattern="always.*@", path)        # Find always blocks

3. Ask the user which part they want to see
"""
        observation_msg = {"role": "user", "content": f"Observation: {observation}"}
        observation_tokens = estimate_message_tokens(observation_msg)
        print(Color.warning(f"[System] ⚠️  Large observation truncated: {original_size:,} chars → {config.MAX_OBSERVATION_CHARS:,} chars ({total_lines:,} lines total)"))

    # Step 2: Check total context size
    current_tokens = sum(estimate_message_tokens(m) for m in messages)
    total_tokens = current_tokens + observation_tokens

    if total_tokens > threshold_tokens and config.ENABLE_COMPRESSION:
        print(Color.warning(f"\n[System] ⚠️  Adding observation would exceed threshold ({total_tokens:,} > {threshold_tokens:,} tokens)"))
        print(Color.info("[System] Compressing history before adding observation..."))
        messages = compress_history(messages)

        # Re-calculate after compression
        current_tokens = sum(estimate_message_tokens(m) for m in messages)
        total_tokens = current_tokens + observation_tokens

        # If still exceeding after compression, force truncate observation
        if total_tokens > threshold_tokens:
            print(Color.warning(f"[System] ⚠️  Still exceeding threshold after compression. Force truncating observation..."))
            original_size = len(observation)
            # Limit observation to 20% of limit to be safe
            max_safe_tokens = int(limit_tokens * 0.2)
            max_safe_chars = max_safe_tokens * 4

            if len(observation) > max_safe_chars:
                observation = observation[:max_safe_chars] + f"\n\n[Observation truncated: {original_size:,} → {max_safe_chars:,} chars to prevent context overflow]"
                observation_msg = {"role": "user", "content": f"Observation: {observation}"}
                observation_tokens = estimate_message_tokens(observation_msg)
                print(Color.info(f"[System] Observation truncated to {observation_tokens:,} tokens"))

    messages.append(observation_msg)
    return messages


# --- 6. Main Loop ---

def chat_loop():
    # Try to load existing conversation history
    loaded_messages = load_conversation_history()
    if loaded_messages:
        messages = loaded_messages
        print(Color.system("[System] Resuming from previous conversation.\n"))
    else:
        messages = [
            {"role": "system", "content": config.SYSTEM_PROMPT}
        ]

    print(Color.BOLD + Color.CYAN + f"Brian Coder Agent (Zero-Dependency) initialized." + Color.RESET)
    print(Color.system(f"Connecting to: {config.BASE_URL}"))
    print(Color.system(f"Rate Limit: {config.RATE_LIMIT_DELAY}s | Max Iterations: {config.MAX_ITERATIONS}"))
    print(Color.system(f"History: {'Enabled' if config.SAVE_HISTORY else 'Disabled'}"))
    print(Color.system(f"Compression: {'Enabled' if config.ENABLE_COMPRESSION else 'Disabled'} (Threshold: {int(config.COMPRESSION_THRESHOLD*100)}%)"))
    print(Color.system(f"Prompt Caching: {'Enabled' if config.ENABLE_PROMPT_CACHING else 'Disabled'}"))

    # Show initial context usage
    show_context_usage(messages)

    print(Color.info("\nType 'exit' or 'quit' to stop.\n"))

    while True:
        try:
            user_input = input(Color.user("You: ") + Color.RESET)
            if user_input.lower() in ["exit", "quit"]:
                break
            
            messages.append({"role": "user", "content": user_input})

            # ReAct Loop: Configurable max iterations with error tracking
            consecutive_errors = 0
            last_error_observation = None
            MAX_CONSECUTIVE_ERRORS = 3

            for iteration in range(config.MAX_ITERATIONS):
                # Context Management: Compress if needed
                messages = compress_history(messages)

                # Show context usage before each iteration
                if config.DEBUG_MODE or iteration == 0:
                    show_context_usage(messages)

                print(Color.agent(f"Agent (Iteration {iteration+1}/{config.MAX_ITERATIONS}): "), end="", flush=True)

                collected_content = ""
                # Call LLM via urllib (collect without printing)
                for content_chunk in chat_completion_stream(messages):
                    collected_content += content_chunk

                # Apply colors to complete text and print
                colored_output = collected_content
                colored_output = colored_output.replace("Thought:", Color.CYAN + "Thought:" + Color.RESET)
                colored_output = colored_output.replace("Action:", Color.YELLOW + "Action:" + Color.RESET)

                print(colored_output)
                print()

                # Add assistant response to history
                messages.append({"role": "assistant", "content": collected_content})

                # Check for Action
                tool_name, args_str = parse_action(collected_content)

                if tool_name:
                    print(Color.tool(f"  🔧 Tool: {tool_name}"))
                    observation = execute_tool(tool_name, args_str)

                    # Smart preview based on tool type
                    if tool_name in ['read_file', 'read_lines']:
                        # For file reads, show first N lines (configurable)
                        lines = observation.split('\n')[:config.TOOL_RESULT_PREVIEW_LINES]
                        obs_preview = '\n'.join(lines) + f"\n... ({len(observation)} chars total)"
                    elif len(observation) > config.TOOL_RESULT_PREVIEW_CHARS:
                        obs_preview = observation[:config.TOOL_RESULT_PREVIEW_CHARS] + f"... ({len(observation)} chars total)"
                    else:
                        obs_preview = observation

                    print(Color.info(f"  ✓ Result: {obs_preview}\n"))

                    # Error detection: check if observation contains error indicators
                    is_error = any(indicator in observation.lower() for indicator in
                                  ['error', 'failed', 'exception', 'traceback', 'syntax error'])

                    if is_error:
                        # Check if it's the same error repeating
                        if observation == last_error_observation:
                            consecutive_errors += 1
                            print(Color.warning(f"  [System] ⚠️  Consecutive error #{consecutive_errors}/{MAX_CONSECUTIVE_ERRORS}"))

                            if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                                print(Color.error(f"  [System] ❌ Same error occurred {MAX_CONSECUTIVE_ERRORS} times. Stopping to prevent infinite loop."))
                                messages.append({
                                    "role": "user",
                                    "content": f"Observation: {observation}\n\n[System] The same error occurred {MAX_CONSECUTIVE_ERRORS} times consecutively. Please ask the user for help or try a different approach."
                                })
                                break
                        else:
                            # Different error, reset counter
                            consecutive_errors = 1
                            last_error_observation = observation
                    else:
                        # Success! Reset error counter
                        consecutive_errors = 0
                        last_error_observation = None

                    # Process observation (handles large files and context management)
                    messages = process_observation(observation, messages)
                else:
                    break
            
        except KeyboardInterrupt:
            print(Color.warning("\nExiting..."))
            save_conversation_history(messages)
            break
        except Exception as e:
            print(Color.error(f"\nAn error occurred: {e}"))
            pass

    # Save history on normal exit
    save_conversation_history(messages)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--prompt":
        # One-shot mode with ReAct loop
        prompt = sys.argv[2]
        messages = [
            {"role": "system", "content": config.SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
        
        print(Color.user(f"User: {prompt}\n"))

        # ReAct loop (configurable max iterations)
        consecutive_errors = 0
        last_error_observation = None
        MAX_CONSECUTIVE_ERRORS = 3

        for iteration in range(config.MAX_ITERATIONS):
            # Context Management: Compress if needed (same as chat_loop)
            messages = compress_history(messages)
            
            # Show context usage before each iteration
            if config.DEBUG_MODE or iteration == 0:
                show_context_usage(messages)
            
            print(Color.agent(f"Agent (Iteration {iteration+1}/{config.MAX_ITERATIONS}): "), end="", flush=True)
            collected_content = ""
            for chunk in chat_completion_stream(messages):
                collected_content += chunk

            # Apply colors to complete text and print
            colored_output = collected_content
            colored_output = colored_output.replace("Thought:", Color.CYAN + "Thought:" + Color.RESET)
            colored_output = colored_output.replace("Action:", Color.YELLOW + "Action:" + Color.RESET)

            print(colored_output)
            print()

            messages.append({"role": "assistant", "content": collected_content})

            # Check for Action
            tool_name, args_str = parse_action(collected_content)

            # Check for hallucinated Observation
            if "Observation:" in collected_content and not tool_name:
                print(Color.warning("  [System] ⚠️  Agent hallucinated an Observation. Correcting..."))
                messages.append({"role": "assistant", "content": collected_content})
                messages.append({
                    "role": "user", 
                    "content": "[System] You generated 'Observation:' yourself. PLEASE DO NOT DO THIS. You must output an Action, wait for me to execute it, and then I will give you the Observation. Now, please output the correct Action."
                })
                continue

            if tool_name:
                print(Color.tool(f"  🔧 Tool: {tool_name}"))
                observation = execute_tool(tool_name, args_str)

                # Smart preview based on tool type
                if tool_name in ['read_file', 'read_lines']:
                    # For file reads, show first N lines (configurable)
                    lines = observation.split('\n')[:config.TOOL_RESULT_PREVIEW_LINES]
                    obs_preview = '\n'.join(lines) + f"\n... ({len(observation)} chars total)"
                elif len(observation) > config.TOOL_RESULT_PREVIEW_CHARS:
                    obs_preview = observation[:config.TOOL_RESULT_PREVIEW_CHARS] + f"... ({len(observation)} chars total)"
                else:
                    obs_preview = observation

                print(Color.info(f"  ✓ Result: {obs_preview}\n"))

                # Error detection: check if observation contains error indicators
                # More robust check: look for "error:" or "exception:" pattern, or "failed"
                obs_lower = observation.lower()
                is_error = any(indicator in obs_lower for indicator in
                              ['error:', 'exception:', 'traceback', 'syntax error', 'compilation failed'])
                
                # Special case: if it's just a file content read that happens to contain "error", it's not an execution error
                if tool_name in ['read_file', 'read_lines', 'grep_file', 'get_plan'] and "error" in obs_lower:
                    # For these tools, unless it starts with "Error:", it's likely just content
                    if not observation.strip().lower().startswith("error:"):
                        is_error = False

                if is_error:
                    # Check if it's the same error repeating
                    if observation == last_error_observation:
                        consecutive_errors += 1
                        print(Color.warning(f"  [System] ⚠️  Consecutive error #{consecutive_errors}/{MAX_CONSECUTIVE_ERRORS}"))

                        if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                            print(Color.error(f"  [System] ❌ Same error occurred {MAX_CONSECUTIVE_ERRORS} times. Stopping to prevent infinite loop."))
                            messages.append({
                                "role": "user",
                                "content": f"Observation: {observation}\n\n[System] The same error occurred {MAX_CONSECUTIVE_ERRORS} times consecutively. Please ask the user for help or try a different approach."
                            })
                            break
                    else:
                        # Different error, reset counter
                        consecutive_errors = 1
                        last_error_observation = observation
                else:
                    # Success! Reset error counter
                    consecutive_errors = 0
                    last_error_observation = None

                    # Process observation (handles large files and context management)
                    messages = process_observation(observation, messages)
            else:
                break
    else:
        chat_loop()
