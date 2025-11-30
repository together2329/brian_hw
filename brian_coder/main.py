import sys
import os
import json
import urllib.request
import urllib.error
import re
import config
import tools

# --- 1. No Vendor Path Needed ---
# We are using standard libraries only.

# --- 2. API Client (urllib) ---

import time

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
    """
    # Rate limiting: Configurable delay
    if config.RATE_LIMIT_DELAY > 0:
        print(Color.info(f"[System] Waiting {config.RATE_LIMIT_DELAY}s for rate limit..."))
        time.sleep(config.RATE_LIMIT_DELAY)
    
    url = f"{config.BASE_URL}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.API_KEY}",
        "User-Agent": "BrianCoder/1.0"
    }
    data = {
        "model": config.MODEL_NAME,
        "messages": messages,
        "stream": True
    }
    
    try:
        req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers)
        with urllib.request.urlopen(req) as response:
            # Parse Server-Sent Events (SSE)
            for line in response:
                line = line.decode('utf-8').strip()
                if line.startswith("data: "):
                    data_str = line[6:] # Remove "data: " prefix
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk_json = json.loads(data_str)
                        # Extract content delta
                        # Structure: choices[0].delta.content
                        if "choices" in chunk_json and len(chunk_json["choices"]) > 0:
                            delta = chunk_json["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                    except json.JSONDecodeError:
                        continue
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        yield f"\n[HTTP Error {e.code}]: {e.reason}\nBody: {error_body}"
    except urllib.error.URLError as e:
        yield f"\n[Connection Error]: {e}"

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

def compress_history(messages):
    """
    Compresses history if it exceeds the limit.
    Strategy: Keep System (0) + Last 4 messages. Summarize the middle.
    """
    if not config.ENABLE_COMPRESSION:
        return messages

    current_chars = sum(len(str(m.get("content", ""))) for m in messages)
    limit = config.MAX_CONTEXT_CHARS
    threshold = limit * config.COMPRESSION_THRESHOLD
    
    if current_chars < threshold:
        return messages
        
    print(Color.warning(f"\n[System] Context size ({current_chars} chars) exceeded threshold ({int(threshold)}). Compressing..."))
    
    # Keep system prompt
    if not messages:
        return messages
        
    system_msg = messages[0]
    
    # If history is short, don't compress
    if len(messages) < 6:
        print(Color.info("[System] History too short to compress."))
        return messages
    
    # Keep last 4 messages (User-Agent-User-Agent usually)
    # Ensure we don't cut off in the middle of a tool use if possible, but simple count is safer for now
    recent_msgs = messages[-4:]
    
    # Messages to summarize (exclude system prompt and recent messages)
    to_summarize = messages[1:-4]
    
    if not to_summarize:
        return messages
        
    summary_prompt = "Summarize the following conversation history concisely. Focus on completed tasks, key decisions, and current state. Ignore minor chatter."
    conversation_text = ""
    for m in to_summarize:
        role = m.get("role", "unknown")
        content = str(m.get("content", ""))[:1000] # Truncate individual messages if too huge
        conversation_text += f"{role}: {content}\n"
    
    # Call LLM for summary
    summary_request = [
        {"role": "system", "content": "You are a helpful assistant that summarizes conversation history for an AI agent."},
        {"role": "user", "content": f"{summary_prompt}\n\n{conversation_text}"}
    ]
    
    print(Color.info("[System] Generating summary of old history..."), end="", flush=True)
    summary_content = ""
    try:
        # We reuse the existing stream function but consume it silently
        for chunk in chat_completion_stream(summary_request):
            summary_content += chunk
        print(Color.success(" Done."))
    except Exception as e:
        print(Color.error(f"\n[System] Failed to generate summary: {e}"))
        return messages # Abort compression on error
        
    # Construct new history
    new_history = [system_msg]
    
    # Check if there was already a summary
    # If the first message after system was a summary, we might want to include it in the new summary
    # But for simplicity, we just append the new summary. 
    # Ideally, the LLM would have summarized the previous summary too if it was in `to_summarize`.
    
    new_history.append({
        "role": "system", 
        "content": f"[Previous Conversation Summary]: {summary_content}"
    })
    new_history.extend(recent_msgs)
    
    new_chars = sum(len(str(m.get("content", ""))) for m in new_history)
    print(Color.success(f"[System] Compression complete. Size reduced: {current_chars} -> {new_chars} chars"))
    
    return new_history

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
    print(Color.info("Type 'exit' or 'quit' to stop.\n"))

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

                    messages.append({
                        "role": "user",
                        "content": f"Observation: {observation}"
                    })
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

                messages.append({
                    "role": "user",
                    "content": f"Observation: {observation}"
                })
            else:
                break
    else:
        chat_loop()
