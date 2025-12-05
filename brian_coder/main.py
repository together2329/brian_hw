import sys
import os
import json
import urllib.request
import urllib.error
import re
import copy
import time
from datetime import datetime
import config
import config
import tools
import display
import llm_client
from display import Color
from llm_client import chat_completion_stream, call_llm_raw, estimate_message_tokens, get_actual_tokens
from memory import MemorySystem
from graph_lite import GraphLite, Node, Edge
from procedural_memory import ProceduralMemory, Action, Trajectory
from message_classifier import MessageClassifier

# Deep Think (optional - only import if enabled)
if config.ENABLE_DEEP_THINK:
    from deep_think import DeepThinkEngine, DeepThinkResult, format_deep_think_output
from iteration_control import IterationTracker, detect_completion_signal, show_iteration_warning

# --- Dynamic Plugin Loading ---
if config.ENABLE_VERILOG_TOOLS:
    try:
        import tools_verilog
        tools.AVAILABLE_TOOLS.update(tools_verilog.VERILOG_TOOLS)
        print(Color.system("[System] Verilog tools plugin loaded successfully 🔌"))
    except ImportError as e:
        print(Color.warning(f"[System] Failed to load Verilog tools: {e}"))

# --- 1. No Vendor Path Needed ---
# We are using standard libraries only.

# --- 2. API Client (urllib) ---
# Moved to llm_client.py

# --- Global Memory System ---
# Initialize memory system if enabled
memory_system = None
if config.ENABLE_MEMORY:
    try:
        memory_system = MemorySystem(memory_dir=config.MEMORY_DIR)
        # Success message will be shown during chat_loop startup
    except Exception as e:
        # Use basic print since Color class not yet defined
        print(f"\033[91m[System] ❌ Memory system initialization failed: {e}\033[0m")
        print(f"\033[93m[System] ⚠️  Continuing without memory system...\033[0m")
        memory_system = None

# --- Global Graph Lite System ---
# Initialize graph system if enabled
graph_lite = None
if config.ENABLE_GRAPH:
    try:
        graph_lite = GraphLite(memory_dir=config.MEMORY_DIR)
        # Success message will be shown during chat_loop startup
    except Exception as e:
        print(f"\033[91m[System] ❌ Graph system initialization failed: {e}\033[0m")
        print(f"\033[93m[System] ⚠️  Continuing without graph system...\033[0m")
        graph_lite = None

# --- Global Procedural Memory System ---
# Initialize procedural memory if enabled
procedural_memory = None
if config.ENABLE_PROCEDURAL_MEMORY:
    try:
        procedural_memory = ProceduralMemory(memory_dir=config.MEMORY_DIR)
        # Success message will be shown during chat_loop startup
    except Exception as e:
        print(f"\033[91m[System] ❌ Procedural memory initialization failed: {e}\033[0m")
        print(f"\033[93m[System] ⚠️  Continuing without procedural memory...\033[0m")
        procedural_memory = None

# --- Global Message Classifier ---
# Initialize classifier for smart compression
message_classifier = MessageClassifier() if config.ENABLE_SMART_COMPRESSION else None

# --- Color Utilities (ANSI Escape Codes) ---
# Moved to display.py

# LLM Client functions moved to llm_client.py

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

# Helper functions moved to llm_client.py

def build_system_prompt(messages=None):
    """
    Build system prompt with memory, graph context, and procedural guidance if available.

    Args:
        messages: Optional message history for graph semantic search and procedural retrieval

    Returns:
        Complete system prompt string
    """
    base_prompt = config.SYSTEM_PROMPT

    # Build context section
    if memory_system is not None or graph_lite is not None or procedural_memory is not None:
        context_parts = []

        # Add memory preferences
        if memory_system is not None:
            memory_context = memory_system.format_all_for_prompt()
            if memory_context:
                context_parts.append(memory_context)

        # Add procedural guidance (from past similar tasks)
        if procedural_memory is not None and config.PROCEDURAL_INJECT_GUIDANCE and messages:
            # Get recent user messages to understand current task
            user_messages = [m for m in messages if m.get("role") == "user"]
            if user_messages:
                # Use last user message as current task
                current_task = user_messages[-1].get("content", "")[:200]

                try:
                    # Retrieve similar past trajectories
                    similar_trajs = procedural_memory.retrieve(
                        current_task,
                        limit=config.PROCEDURAL_RETRIEVE_LIMIT
                    )

                    # Filter by threshold
                    similar_trajs = [(score, traj) for score, traj in similar_trajs
                                    if score >= config.PROCEDURAL_SIMILARITY_THRESHOLD]

                    if similar_trajs:
                        guidance = "=== PAST EXPERIENCE ===\n\n"
                        guidance += "You have similar past experiences that may help:\n\n"

                        for i, (score, traj) in enumerate(similar_trajs, 1):
                            guidance += f"{i}. Task: {traj.task_description}\n"
                            guidance += f"   Outcome: {traj.outcome.upper()} ({traj.iterations} iterations)\n"

                            # Show key actions for successful trajectories
                            if traj.outcome == "success":
                                guidance += "   Successful approach:\n"
                                for action in traj.actions[:3]:  # Show first 3 actions
                                    guidance += f"     - {action.tool}({action.args[:50]}...)\n"

                            # Show errors for failed trajectories
                            elif traj.errors_encountered:
                                guidance += f"   Errors encountered: {', '.join(traj.errors_encountered[:2])}\n"

                            guidance += "\n"

                        guidance += "Use this experience to avoid past mistakes and follow proven approaches.\n"
                        guidance += "=====================\n"

                        context_parts.append(guidance)

                        # Increment usage count for retrieved trajectories
                        for score, traj in similar_trajs:
                            procedural_memory.increment_usage(traj.id)

                except Exception as e:
                    # Fail silently if procedural retrieval fails
                    pass

        # Add graph knowledge (semantic search based on recent conversation)
        if graph_lite is not None and messages:
            # Get recent user messages for context
            user_messages = [m for m in messages if m.get("role") == "user"]
            if user_messages:
                # Use last user message as search query
                recent_topic = user_messages[-1].get("content", "")[:200]

                try:
                    # Graph RAG: Search with graph traversal for richer context
                    relevant_results = graph_lite.graph_rag_search(
                        recent_topic,
                        limit=config.GRAPH_SEARCH_LIMIT,
                        hop=1  # Follow 1 hop of edges
                    )

                    if relevant_results:
                        graph_context = "=== RELEVANT KNOWLEDGE ===\n\n"
                        for score, node in relevant_results:
                            # Only include nodes with reasonable similarity
                            if score > config.GRAPH_SIMILARITY_THRESHOLD:
                                node_desc = node.data.get("description", node.data.get("name", ""))
                                graph_context += f"- {node.type}: {node_desc}\n"

                        graph_context += "\n=====================\n"
                        context_parts.append(graph_context)

                except Exception as e:
                    # Fail silently if graph search fails
                    pass

        # Add RAG tool guidance for Verilog analysis
        rag_guidance = """=== VERILOG CODE ANALYSIS ===

For Verilog/SystemVerilog code analysis, use these RAG tools (much faster than grep):
- rag_search(query, categories, limit): Semantic search for Verilog code
  Example: rag_search("axi_awready signal", categories="verilog", limit=5)
- rag_index(path, fine_grained): Index Verilog files (run once)
- rag_status(): Check indexed files count
- read_lines(file, start, end): Read specific lines after finding location

Workflow: rag_search() → find location → read_lines() → analyze
==============================
"""
        context_parts.append(rag_guidance)

        # Combine all context parts
        if context_parts:
            base_prompt = base_prompt + "\n\n" + "\n\n".join(context_parts)

    return base_prompt

def save_procedural_trajectory(task_description, actions_taken, outcome, iterations):
    """
    Save completed task as a trajectory in procedural memory.

    Args:
        task_description: Description of the task
        actions_taken: List of Action objects
        outcome: "success" or "failure"
        iterations: Number of iterations taken
    """
    if not procedural_memory:
        return

    try:
        trajectory_id = procedural_memory.build(
            task_description=task_description,
            actions=actions_taken,
            outcome=outcome,
            iterations=iterations
        )

        # Save to disk
        procedural_memory.save()

        print(Color.success(f"[Procedural Memory] Saved trajectory: {trajectory_id}"))
        print(Color.info(f"  Task type: {procedural_memory.trajectories[trajectory_id].task_type}"))
        print(Color.info(f"  Outcome: {outcome}, Iterations: {iterations}"))

    except Exception as e:
        print(Color.error(f"[Procedural Memory] Failed to save trajectory: {e}"))

def on_conversation_end(messages):
    """
    Extract and save knowledge from conversation to graph.
    Now uses A-MEM auto-linking for intelligent connections.
    
    Args:
        messages: Full message history
    """
    if not (config.ENABLE_GRAPH and config.GRAPH_AUTO_EXTRACT and graph_lite):
        return

    print(Color.system("\n[Graph] Extracting knowledge from conversation..."))

    try:
        # Get recent messages for context (skip system message)
        recent_messages = [m for m in messages if m.get("role") != "system"][-config.GRAPH_EXTRACTION_MESSAGES:]

        if not recent_messages:
            return

        # Build conversation summary
        conversation_text = "\n".join([
            f"{m.get('role')}: {m.get('content', '')[:500]}"
            for m in recent_messages
        ])

        # A-MEM: Create free-form notes with auto-linking
        # Instead of extracting entities/relations separately, we create rich notes
        # that automatically link to relevant existing knowledge
        
        print(Color.system("[Graph] Creating memory notes with auto-linking..."))
        
        # Extract key insights/learnings from conversation
        prompt = f"""Extract 2-3 key learnings or insights from this conversation.
        
Conversation:
{conversation_text}

For each learning, provide a concise statement (1-2 sentences).
Return as JSON array: [{{"learning": "..."}}]

Learnings (JSON only):"""

        try:
            response = call_llm_raw(prompt)
            
            # Parse JSON
            start_idx = response.find('[')
            end_idx = response.rfind(']') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                learnings = json.loads(json_str)
                
                # Add each learning as a note with auto-linking
                notes_added = 0
                for item in learnings:
                    learning = item.get('learning', '')
                    if learning:
                        # A-MEM auto-linking!
                        node_id = graph_lite.add_note_with_auto_linking(
                            content=learning,
                            context={
                                'source': 'conversation',
                                'timestamp': datetime.now().isoformat()
                            }
                        )
                        notes_added += 1
                
                print(Color.success(f"[Graph] Added {notes_added} notes with auto-linking"))
                
                # Save graph
                graph_lite.save()
                
                # Display stats
                stats = graph_lite.get_stats()
                print(Color.info(f"[Graph] Total: {stats['total_nodes']} nodes, {stats['total_edges']} edges"))
                
        except Exception as e:
            print(Color.error(f"[Graph] Failed to extract learnings: {e}"))
            return

    except Exception as e:
        print(Color.error(f"[Graph] Knowledge extraction failed: {e}"))


def show_context_usage(messages, use_actual=True):
    """
    Displays current context usage information.

    Args:
        messages: list of message dicts
        use_actual: if True, use actual tokens from API (hybrid mode)
    """
    if use_actual:
        current_tokens = get_actual_tokens(messages)
        source = "actual" if llm_client.last_input_tokens > 0 else "estimated"
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
    token_source = "actual" if llm_client.last_input_tokens > 0 else "estimated"

    if current_tokens < threshold_tokens:
        return messages

    print(Color.warning(f"\n[System] Context size ({current_tokens:,} {token_source} tokens) exceeded threshold ({threshold_tokens:,}). Compressing..."))

    if not messages:
        return messages

    # Smart Compression: Classify messages by importance
    if config.ENABLE_SMART_COMPRESSION and message_classifier:
        print(Color.info("[System] Using Smart Compression (selective preservation)..."))

        # Partition messages by importance
        partitions = message_classifier.partition_by_importance(messages, keep_recent=config.COMPRESSION_KEEP_RECENT)

        # Show compression plan
        if config.DEBUG_MODE:
            summary = message_classifier.get_compression_summary(partitions)
            print(Color.info(summary))

        # Messages to preserve (no summarization)
        preserved = partitions["system"] + partitions["critical"] + partitions["high"] + partitions["recent"]

        # Messages to summarize (medium and low importance)
        to_summarize = partitions["medium"] + partitions["low"]

        if not to_summarize:
            print(Color.info("[System] No messages to summarize (all are important)."))
            return messages

        # Compress only the less important messages
        mode = config.COMPRESSION_MODE.lower()
        if mode == "chunked":
            compressed = _compress_chunked(to_summarize)
        else:
            compressed = [_compress_single(to_summarize)]

        # Reconstruct: system + critical + high + compressed + recent
        # Note: Order matters for conversation flow
        new_history = partitions["system"] + partitions["critical"] + partitions["high"] + compressed + partitions["recent"]

        preserved_count = len(partitions["critical"]) + len(partitions["high"])
        summarized_count = len(to_summarize)
        print(Color.success(f"[System] Preserved {preserved_count} important messages, summarized {summarized_count} less important"))

    else:
        # Traditional compression (original behavior)
        print(Color.info("[System] Using traditional compression (all old messages summarized)..."))

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


# --- 6. ReAct Agent Logic ---

def run_react_agent(messages, tracker, task_description, mode='interactive'):
    """
    Executes the ReAct agent loop for a given task.
    
    Args:
        messages: List of message dicts (context)
        tracker: IterationTracker instance
        task_description: Description of the task (for procedural memory)
        mode: 'interactive' or 'oneshot'
        
    Returns:
        Updated messages list
    """
    consecutive_errors = 0
    last_error_observation = None
    MAX_CONSECUTIVE_ERRORS = 3
    
    # Initialize action tracking for procedural memory
    actions_taken = []

    # ============================================================
    # Deep Think Integration (Hypothesis Branching)
    # ============================================================
    if config.ENABLE_DEEP_THINK:
        print(Color.system("\n[Deep Think] Analyzing task and generating strategies..."))

        try:
            # Build context from recent messages
            context_parts = []
            for msg in messages[-5:]:
                if msg.get("role") != "system":
                    content = str(msg.get("content", ""))[:200]
                    context_parts.append(f"{msg['role']}: {content}")

            # Add current directory info
            try:
                files = os.listdir(".")[:20]
                context_parts.append(f"Current directory: {', '.join(files)}")
            except:
                pass

            context = "\n".join(context_parts)

            # Initialize Deep Think engine
            engine = DeepThinkEngine(
                procedural_memory=procedural_memory,
                graph_lite=graph_lite,
                llm_call_func=call_llm_raw,
                execute_tool_func=tools.execute_tool
            )

            # Run Deep Think pipeline
            deep_think_result = engine.think(
                task=task_description,
                context=context
            )

            # Display result
            print(format_deep_think_output(deep_think_result, verbose=config.DEBUG_MODE))

            # Inject selected strategy into messages
            strategy_guidance = engine.format_strategy_guidance(deep_think_result)
            messages.append({"role": "system", "content": strategy_guidance})

            print(Color.success(f"[Deep Think] Selected: {deep_think_result.selected_hypothesis.strategy_name}"))
            print(Color.info(f"  First action: {deep_think_result.selected_hypothesis.first_action}"))
            print()

        except Exception as e:
            print(Color.warning(f"[Deep Think] Analysis failed: {e}"))
            print(Color.info("[Deep Think] Continuing with standard approach..."))
            print()

    while True:
        # Check iteration limit with progressive warning
        warning_action = show_iteration_warning(tracker, mode=mode)
        if warning_action == 'stop':
            break
        elif warning_action == 'extend':
            tracker.extend(20)

        # Context Management: Compress if needed
        messages = compress_history(messages)

        # Show context usage before each iteration
        if config.DEBUG_MODE or tracker.current == 0:
            show_context_usage(messages)

        print(Color.agent(f"Agent (Iteration {tracker.current+1}/{tracker.max_iterations}): "), end="", flush=True)

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

        # Check for explicit completion signal
        if detect_completion_signal(collected_content):
            print(Color.success("\n[System] ✅ Task completion detected. Ending ReAct loop.\n"))
            break

        # Check for Action
        tool_name, args_str = parse_action(collected_content)

        # Check for hallucinated Observation
        if "Observation:" in collected_content and not tool_name:
            print(Color.warning("  [System] ⚠️  Agent hallucinated an Observation. Correcting..."))
            # We already appended the assistant message above.
            # Now append the correction user message.
            messages.append({
                "role": "user", 
                "content": "[System] You generated 'Observation:' yourself. PLEASE DO NOT DO THIS. You must output an Action, wait for me to execute it, and then I will give you the Observation. Now, please output the correct Action."
            })
            continue

        if tool_name:
            print(Color.tool(f"  🔧 Tool: {tool_name}"))

            # Record tool usage for progress tracking
            tracker.record_tool(tool_name)

            observation = execute_tool(tool_name, args_str)

            # Error detection: check if observation contains error indicators
            obs_lower = observation.lower()
            is_error = any(indicator in obs_lower for indicator in
                          ['error:', 'exception:', 'traceback', 'syntax error', 'compilation failed'])

            # Record action for procedural memory
            if procedural_memory is not None:
                action_result = "error" if is_error else "success"
                action_obj = Action(
                    tool=tool_name,
                    args=args_str[:100],  # Truncate args
                    result=action_result,
                    observation=observation[:200]  # Truncate observation
                )
                actions_taken.append(action_obj)

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

            # Check for stall condition
            if tracker.is_stalled():
                print(Color.warning(f"  [System] ⚠️  Detected {tracker.consecutive_reads} consecutive read operations. Agent may be stalled."))
        else:
            # No action = natural completion
            break

        # Increment iteration counter
        tracker.increment()

    # Save trajectory after task completion
    if procedural_memory is not None and actions_taken:
        # Determine outcome
        has_errors = any(a.result == "error" for a in actions_taken)
        outcome = "failure" if has_errors else "success"

        save_procedural_trajectory(
            task_description=task_description,
            actions_taken=actions_taken,
            outcome=outcome,
            iterations=tracker.current
        )
        
    return messages


# --- 7. Main Loop ---

def chat_loop():
    # Try to load existing conversation history
    loaded_messages = load_conversation_history()
    if loaded_messages:
        messages = loaded_messages
        print(Color.system("[System] Resuming from previous conversation.\n"))
    else:
        messages = [
            {"role": "system", "content": build_system_prompt()}
        ]

    print(Color.BOLD + Color.CYAN + f"Brian Coder Agent (Zero-Dependency) initialized." + Color.RESET)
    print(Color.system(f"Connecting to: {config.BASE_URL}"))
    print(Color.system(f"Rate Limit: {config.RATE_LIMIT_DELAY}s | Max Iterations: {config.MAX_ITERATIONS}"))
    print(Color.system(f"History: {'Enabled' if config.SAVE_HISTORY else 'Disabled'}"))

    compression_mode = "Smart" if config.ENABLE_SMART_COMPRESSION else "Traditional"
    print(Color.system(f"Compression: {'Enabled' if config.ENABLE_COMPRESSION else 'Disabled'} ({compression_mode}, Threshold: {int(config.COMPRESSION_THRESHOLD*100)}%)"))

    print(Color.system(f"Prompt Caching: {'Enabled' if config.ENABLE_PROMPT_CACHING else 'Disabled'}"))
    print(Color.system(f"Memory: {'Enabled' if config.ENABLE_MEMORY and memory_system else 'Disabled'}"))
    print(Color.system(f"Graph: {'Enabled' if config.ENABLE_GRAPH and graph_lite else 'Disabled'}"))
    print(Color.system(f"Procedural Memory: {'Enabled' if config.ENABLE_PROCEDURAL_MEMORY and procedural_memory else 'Disabled'}"))

    # Show initial context usage
    show_context_usage(messages)

    print(Color.info("\nType 'exit' or 'quit' to stop.\n"))

    while True:
        try:
            user_input = input(Color.user("You: ") + Color.RESET)
            if user_input.lower() in ["exit", "quit"]:
                break

            # Auto-extract preferences from user input (Mem0-style)
            if memory_system is not None and config.ENABLE_MEMORY and config.ENABLE_AUTO_EXTRACT:
                try:
                    result = memory_system.auto_extract_and_update(user_input)
                    if result.get("actions"):
                        for action in result["actions"]:
                            if action["action"] == "ADD":
                                print(Color.success(f"  [Memory] ✅ Learned new preference: {action['key']} = {action['value']}"))
                            elif action["action"] == "UPDATE":
                                print(Color.info(f"  [Memory] 🔄 Updated preference: {action['key']} = {action['new_value']} (was: {action['old_value']})"))
                            elif action["action"] == "DELETE":
                                print(Color.warning(f"  [Memory] ❌ Removed preference: {action['key']}"))
                except Exception as e:
                    # Fail silently if extraction fails
                    pass

            messages.append({"role": "user", "content": user_input})

            # ReAct Loop: Smart Iteration Control with progress tracking
            # Initialize iteration tracker
            tracker = IterationTracker(max_iterations=config.MAX_ITERATIONS)
            
            # Run ReAct Agent
            messages = run_react_agent(messages, tracker, user_input, mode='interactive')

            # Extract knowledge from conversation at end
            try:
                on_conversation_end(messages)
            except Exception as e:
                print(Color.warning(f"[Warning] Failed to save knowledge: {e}"))
                print(Color.warning("[Warning] Conversation will continue normally"))
        except KeyboardInterrupt:
            print(Color.warning("\nExiting..."))
            save_conversation_history(messages)
            try:
                on_conversation_end(messages)
            except Exception as e:
                print(Color.warning(f"[Warning] Failed to save knowledge: {e}"))
            break
        except Exception as e:
            print(Color.error(f"\nAn error occurred: {e}"))
            pass

    # Save history on normal exit
    save_conversation_history(messages)
    try:
        on_conversation_end(messages)
    except Exception as e:
        print(Color.warning(f"[Warning] Failed to save knowledge: {e}"))

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--prompt":
        # One-shot mode with ReAct loop
        prompt = sys.argv[2]
        messages = [
            {"role": "system", "content": build_system_prompt()},
            {"role": "user", "content": prompt}
        ]
        
        print(Color.user(f"User: {prompt}\n"))

        # ReAct loop: Smart Iteration Control with progress tracking
        # Initialize iteration tracker (oneshot mode)
        tracker = IterationTracker(max_iterations=config.MAX_ITERATIONS)

        # Run ReAct Agent
        messages = run_react_agent(messages, tracker, prompt, mode='oneshot')

        # Extract knowledge from conversation at end
        try:
            on_conversation_end(messages)
        except Exception as e:
            print(Color.warning(f"[Warning] Failed to save knowledge: {e}"))
    else:
        chat_loop()
