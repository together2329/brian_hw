"""
LLM Client for Brian Coder.
Handles API communication, streaming, token counting, and prompt caching.
Zero-dependency (uses urllib).

OpenCode-Inspired Features:
- Multi-provider support (agent-specific models)
- Agent-aware API calls
- Dynamic model switching
"""
import json
import ssl
import urllib.request
import urllib.error
import time
import copy
import re
import sys
import os
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

# Add paths for imports
_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_script_dir)
sys.path.insert(0, _script_dir)
sys.path.insert(0, os.path.join(_project_root, 'lib'))
sys.path.insert(0, os.path.join(_project_root, 'core'))

import config
from display import Color

# --- Global Token Tracking ---
# Stores actual token counts from API responses
# Structure: {"message_index": actual_token_count}
actual_token_cache = {}
last_input_tokens = 0  # Last reported input tokens from API
last_output_tokens = 0  # Last reported output tokens from API

# --- Cache Token Tracking (Anthropic Prompt Caching) ---
last_cache_creation_tokens = 0  # Last cache creation tokens
last_cache_read_tokens = 0      # Last cache read tokens
total_cache_created = 0         # Total cache tokens created this session
total_cache_read = 0            # Total cache tokens read this session


# ============================================================
# Provider Configuration (OpenCode-Inspired)
# ============================================================

@dataclass
class ProviderConfig:
    """Provider-specific configuration"""
    provider_id: str
    base_url: str
    api_key: str
    model_id: str
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    max_tokens: Optional[int] = None

    @classmethod
    def from_env(cls, provider_id: str = "default") -> 'ProviderConfig':
        """Create from environment/config defaults"""
        return cls(
            provider_id=provider_id,
            base_url=config.BASE_URL,
            api_key=config.API_KEY,
            model_id=config.MODEL_NAME
        )


# Provider registry (cached configs)
_provider_cache: Dict[str, ProviderConfig] = {}


def get_provider_config(provider_id: str = None, model_id: str = None) -> ProviderConfig:
    """
    Get provider configuration for a specific provider/model.

    Args:
        provider_id: Provider name (anthropic, openai, openrouter, etc.)
        model_id: Model name override

    Returns:
        ProviderConfig with API details
    """
    # Default to env config
    if not provider_id and not model_id:
        return ProviderConfig.from_env()

    cache_key = f"{provider_id or 'default'}:{model_id or 'default'}"
    if cache_key in _provider_cache:
        return _provider_cache[cache_key]

    # Build config based on provider
    provider_id = provider_id or ""
    provider_lower = provider_id.lower()

    # Known provider base URLs
    provider_urls = {
        "anthropic": "https://api.anthropic.com/v1",
        "openai": "https://api.openai.com/v1",
        "openrouter": "https://openrouter.ai/api/v1",
        "google": "https://generativelanguage.googleapis.com/v1beta",
        "groq": "https://api.groq.com/openai/v1",
        "together": "https://api.together.xyz/v1",
        "deepinfra": "https://api.deepinfra.com/v1/openai",
        "mistral": "https://api.mistral.ai/v1",
    }

    # Get base URL
    base_url = provider_urls.get(provider_lower, config.BASE_URL)

    # Get API key from env (PROVIDER_API_KEY or fallback)
    env_key = f"{provider_id.upper()}_API_KEY"
    api_key = os.getenv(env_key, config.API_KEY)

    provider_config = ProviderConfig(
        provider_id=provider_id or "default",
        base_url=base_url,
        api_key=api_key,
        model_id=model_id or config.MODEL_NAME
    )

    _provider_cache[cache_key] = provider_config
    return provider_config


def chat_completion_with_config(
    messages: List[Dict[str, Any]],
    provider_config: ProviderConfig = None,
    stop: List[str] = None,
    temperature: float = None,
    top_p: float = None
):
    """
    Chat completion with explicit provider configuration.
    Yields content chunks from SSE stream.

    Args:
        messages: List of message dicts
        provider_config: Provider configuration (None = use defaults)
        stop: Stop sequences
        temperature: Override temperature
        top_p: Override top_p

    Yields:
        Content chunks
    """
    if provider_config is None:
        provider_config = ProviderConfig.from_env()

    # Use provided config
    url = f"{provider_config.base_url}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {provider_config.api_key}",
        "User-Agent": "BrianCoder/1.0"
    }

    data = {
        "model": provider_config.model_id,
        "messages": messages,
        "stream": True,
        "stream_options": {"include_usage": True}
    }

    if stop:
        data["stop"] = stop

    # Apply temperature/top_p
    if temperature is not None:
        data["temperature"] = temperature
    elif provider_config.temperature is not None:
        data["temperature"] = provider_config.temperature

    if top_p is not None:
        data["top_p"] = top_p
    elif provider_config.top_p is not None:
        data["top_p"] = provider_config.top_p

    if config.DEBUG_MODE:
        print(Color.info(f"\n[Agent-Aware API Call]"))
        print(Color.info(f"  Provider: {provider_config.provider_id}"))
        print(Color.info(f"  Model: {provider_config.model_id}"))
        print(Color.info(f"  URL: {url}"))

    # Reuse existing streaming logic
    yield from _execute_streaming_request(url, headers, data, messages)


def _execute_streaming_request(url: str, headers: Dict, data: Dict, messages: List):
    """
    Execute streaming request with retry logic.
    Internal helper for chat_completion functions.
    """
    global last_input_tokens, last_output_tokens
    global last_cache_creation_tokens, last_cache_read_tokens
    global total_cache_created, total_cache_read

    max_retries = 3
    initial_delay = 2

    for retry_count in range(max_retries):
        _reasoning_started = False
        _content_started = False

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode('utf-8'),
                headers=headers
            )

            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = True
            ssl_context.verify_mode = ssl.CERT_REQUIRED

            with urllib.request.urlopen(req, timeout=config.API_TIMEOUT, context=ssl_context) as response:
                usage_info = None
                for line in response:
                    line = line.decode('utf-8').strip()
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            chunk_json = json.loads(data_str)

                            if "usage" in chunk_json:
                                usage_info = chunk_json["usage"]

                            if "choices" in chunk_json and len(chunk_json["choices"]) > 0:
                                delta = chunk_json["choices"][0].get("delta", {})

                                reasoning = delta.get("reasoning") or delta.get("reasoning_content", "")
                                if reasoning:
                                    if config.DEBUG_MODE:
                                        if not _reasoning_started:
                                            sys.stdout.write(f"\n\033[36m[REASONING]\033[0m ")
                                            _reasoning_started = True
                                            _content_started = False
                                        sys.stdout.write(f"\033[36m{reasoning}\033[0m")
                                        sys.stdout.flush()
                                    yield reasoning

                                content = delta.get("content", "")
                                if content:
                                    if config.DEBUG_MODE:
                                        if not _content_started:
                                            sys.stdout.write(f"\n\n\033[32m[CONTENT]\033[0m ")
                                            _content_started = True
                                        sys.stdout.write(f"\033[32m{content}\033[0m")
                                        sys.stdout.flush()
                                    yield content
                        except json.JSONDecodeError:
                            continue

                if usage_info:
                    input_tokens = usage_info.get("input_tokens") or usage_info.get("prompt_tokens", 0)
                    output_tokens = usage_info.get("output_tokens") or usage_info.get("completion_tokens", 0)
                    if input_tokens > 0:
                        last_input_tokens = input_tokens
                    if output_tokens > 0:
                        last_output_tokens = output_tokens

                    if config.DEBUG_MODE:
                        total_tokens = input_tokens + output_tokens
                        print(f"\n{Color.info('[Token Usage]')}")
                        print(f"{Color.info(f'  Input: {input_tokens:,} tokens')}")
                        print(f"{Color.info(f'  Output: {output_tokens:,} tokens')}")
                        print(f"{Color.info(f'  Total: {total_tokens:,} tokens')}\n")

                return

        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            is_retryable = e.code == 429 or (500 <= e.code < 600)

            if is_retryable and retry_count < max_retries - 1:
                delay = initial_delay * (2 ** retry_count)
                print(Color.warning(f"\n[Retry {retry_count + 1}/{max_retries}] HTTP {e.code}: {e.reason}"))
                print(Color.warning(f"Waiting {delay}s before retry...\n"))
                time.sleep(delay)
                continue

            yield f"\n{Color.error(f'[HTTP Error {e.code}]: {e.reason}')}\n"
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
            except:
                yield f"{Color.error(f'Raw Error Body:')}\n{error_body[:500]}\n"
            return

        except (urllib.error.URLError, ssl.SSLError) as e:
            if retry_count < max_retries - 1:
                delay = initial_delay * (2 ** retry_count)
                error_msg = str(e.reason) if hasattr(e, 'reason') else str(e)
                print(Color.warning(f"\n[Retry {retry_count + 1}/{max_retries}] Connection Error: {error_msg}"))
                print(Color.warning(f"Waiting {delay}s before retry...\n"))
                time.sleep(delay)
                continue

            error_msg = str(e.reason) if hasattr(e, 'reason') else str(e)
            yield f"\n{Color.error(f'[Connection Error]: {error_msg}')}\n"
            return

        except Exception as e:
            error_type = type(e).__name__
            if retry_count < max_retries - 1:
                delay = initial_delay * (2 ** retry_count)
                print(Color.warning(f"\n[Retry {retry_count + 1}/{max_retries}] {error_type}: {e}"))
                print(Color.warning(f"Waiting {delay}s before retry...\n"))
                time.sleep(delay)
                continue

            yield f"\n{Color.error(f'[{error_type}]: {e}')}\n"
            return


def call_llm_for_agent(
    messages: List[Dict[str, Any]],
    agent_name: str = None,
    temperature: float = None
) -> str:
    """
    Call LLM with agent-specific configuration (non-streaming).

    Args:
        messages: List of message dicts
        agent_name: Agent name to look up config (optional)
        temperature: Override temperature

    Returns:
        Complete response text
    """
    provider_config = ProviderConfig.from_env()  # Default

    # Try to get agent-specific config
    if agent_name:
        try:
            from core.agent_config import get_agent_config
            agent = get_agent_config(agent_name)
            if agent and agent.model:
                provider_config = get_provider_config(
                    provider_id=agent.model.provider_id,
                    model_id=agent.model.model_id
                )
                if agent.temperature is not None and temperature is None:
                    temperature = agent.temperature
        except ImportError:
            pass  # agent_config not available

    url = f"{provider_config.base_url}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {provider_config.api_key}"
    }

    data = {
        "model": provider_config.model_id,
        "messages": messages,
        "stream": False
    }

    if temperature is not None:
        data["temperature"] = temperature

    try:
        request = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers=headers
        )

        with urllib.request.urlopen(request, timeout=config.API_TIMEOUT) as response:
            result = json.loads(response.read().decode('utf-8'))
            content = result["choices"][0]["message"]["content"]
            # Sanitize metadata tokens
            content = re.sub(r'<\|final<\|[^>]*\|>', '', content)
            content = re.sub(r'<\|[^|<>]+\|>', '', content)
            content = re.sub(r'<\|[a-z_]+$', '', content)
            return content.strip()

    except Exception as e:
        return f"Error calling LLM: {e}"

def chat_completion_stream(messages, stop=None):
    """
    Sends a chat completion request to the LLM using urllib.
    Yields content chunks from the SSE stream.
    Supports Anthropic Prompt Caching when enabled.
    Updates global actual_token_cache with real token counts from API.
    """
    global last_input_tokens, last_output_tokens
    global last_cache_creation_tokens, last_cache_read_tokens
    global total_cache_created, total_cache_read

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

    if stop:
        data["stop"] = stop

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
        
        # FULL_PROMPT_DEBUG: Show complete input messages
        if getattr(config, 'FULL_PROMPT_DEBUG', False):
            print(Color.info("\n" + "="*60))
            print(Color.info("[FULL PROMPT DEBUG] Complete input messages:"))
            print(Color.info("="*60))
            msgs_to_show = processed_messages
            start_index = 0

            # Check for limit configuration
            if getattr(config, 'FULL_PROMPT_DEBUG_LIMIT_ENABLED', True):
                limit_count = getattr(config, 'FULL_PROMPT_DEBUG_LIMIT_COUNT', 5)
                total_msgs = len(processed_messages)
                
                if total_msgs > limit_count:
                    start_index = total_msgs - limit_count
                    if start_index > 0:
                        print(Color.info(f"\n... [Skipping {start_index} earlier messages (showing last {limit_count})] ..."))
                        msgs_to_show = processed_messages[start_index:]

            # Check for line limit configuration
            line_limit_enabled = getattr(config, 'FULL_PROMPT_DEBUG_LINE_LIMIT_ENABLED', True)
            line_limit_count = getattr(config, 'FULL_PROMPT_DEBUG_LINE_LIMIT_COUNT', 20)

            for i, msg in enumerate(msgs_to_show):
                real_idx = start_index + i + 1
                role = msg.get('role', 'unknown')
                content = str(msg.get('content', ''))
                
                print(Color.info(f"\n--- Message {real_idx} [{role}] ---"))
                
                # Colorize Action and Thought in debug output using regex for potential multi-matches
                import re
                
                # Colors
                CYAN = "\033[96m"
                YELLOW = "\033[93m" 
                RESET = "\033[0m"

                colored_lines = []
                lines = content.splitlines()
                for line in lines[:line_limit_count] if line_limit_enabled and len(lines) > line_limit_count else lines:
                    # Highlight "Action:"
                    line = re.sub(r'(Action:)', YELLOW + r'\1' + RESET, line)
                    # Highlight "Thought:"
                    line = re.sub(r'(Thought:)', CYAN + r'\1' + RESET, line)
                    colored_lines.append(line)
                
                if line_limit_enabled and len(lines) > line_limit_count:
                    # Print first N lines and truncation notice
                    print('\n'.join(colored_lines))
                    print(Color.info(f"... [truncated, {len(lines) - line_limit_count} lines hidden (total {len(lines)} lines)]"))
                else:
                    # Default large message handling (fallback to char truncation)
                    content_to_print = '\n'.join(colored_lines)
                    if len(content) > 5000:
                        print(content_to_print[:5000])
                        print(Color.info(f"... [truncated, total {len(content)} chars]"))
                    else:
                        print(content_to_print)
            print(Color.info("="*60 + "\n"))
        print()

    # Retry logic for transient errors
    max_retries = 3
    initial_delay = 2  # seconds
    
    for retry_count in range(max_retries):
        # Local state for label tracking (resets each retry)
        _reasoning_started = False
        _content_started = False

        try:
            req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers)

            # Create SSL context for more stable connections
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = True
            ssl_context.verify_mode = ssl.CERT_REQUIRED

            with urllib.request.urlopen(req, timeout=config.API_TIMEOUT, context=ssl_context) as response:
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
                                
                                # Handle reasoning fields (DeepSeek models)
                                # Can be: "reasoning", "reasoning_content", or "reasoning_details"
                                reasoning = delta.get("reasoning") or delta.get("reasoning_content", "")
                                if reasoning:
                                    if config.DEBUG_MODE:
                                        # Print reasoning in cyan with label (thinking process)
                                        if not _reasoning_started:
                                            sys.stdout.write(f"\n\033[36m[REASONING]\033[0m ")
                                            _reasoning_started = True
                                            _content_started = False
                                        sys.stdout.write(f"\033[36m{reasoning}\033[0m") 
                                        sys.stdout.flush()
                                    # Yield reasoning so it's captured (use both reasoning + content)
                                    yield reasoning
                                
                                content = delta.get("content", "")
                                if content:
                                    if config.DEBUG_MODE:
                                        # Print content label when first content arrives
                                        if not _content_started:
                                            sys.stdout.write(f"\n\n\033[32m[CONTENT]\033[0m ")
                                            _content_started = True
                                        # Also print content for streaming display
                                        sys.stdout.write(f"\033[32m{content}\033[0m")
                                        sys.stdout.flush()
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
                    if output_tokens > 0:
                        last_output_tokens = output_tokens

                    # Display actual token usage (always show for visibility)
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

                    # Update cache token tracking
                    last_cache_creation_tokens = cache_creation_tokens
                    last_cache_read_tokens = cache_read_tokens
                    total_cache_created += cache_creation_tokens
                    total_cache_read += cache_read_tokens

                    if cache_creation_tokens > 0 or cache_read_tokens > 0:
                        print(f"\n\n{Color.info('[Token Usage]')}")
                        print(f"{Color.info(f'  Input: {input_tokens:,} tokens')}")
                        print(f"{Color.info(f'  Output: {output_tokens:,} tokens')}")
                        if cache_creation_tokens > 0:
                            print(f"{Color.info(f'  Cache Created: {cache_creation_tokens:,} tokens (Total Session: {total_cache_created:,})')}")
                        if cache_read_tokens > 0:
                            savings = int(cache_read_tokens * 0.9)
                            total_savings = int(total_cache_read * 0.9)
                            print(f"{Color.success(f'  Cache Hit: {cache_read_tokens:,} tokens (saved ~{savings:,} tokens)')}")
                            print(f"{Color.success(f'  Total Session Cache Hits: {total_cache_read:,} tokens (saved ~{total_savings:,} tokens!)')}\n")
                
                # Success! Exit retry loop
                return
                
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            
            # Check if error is retryable
            is_retryable = e.code == 429 or (500 <= e.code < 600)
            
            if is_retryable and retry_count < max_retries - 1:
                # Calculate exponential backoff delay
                delay = initial_delay * (2 ** retry_count)
                print(Color.warning(f"\n[Retry {retry_count + 1}/{max_retries}] HTTP {e.code}: {e.reason}"))
                print(Color.warning(f"Waiting {delay}s before retry...\n"))
                time.sleep(delay)
                continue
            
            # Non-retryable error or max retries reached
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
            
            return

        except urllib.error.URLError as e:
            # Connection error - retry
            if retry_count < max_retries - 1:
                delay = initial_delay * (2 ** retry_count)
                error_msg = str(e.reason) if hasattr(e, 'reason') else str(e)

                # Special handling for SSL errors
                if 'SSL' in error_msg or 'ssl' in error_msg.lower():
                    print(Color.warning(f"\n[Retry {retry_count + 1}/{max_retries}] SSL Error: {error_msg}"))
                    print(Color.warning(f"This is usually a temporary network issue."))
                else:
                    print(Color.warning(f"\n[Retry {retry_count + 1}/{max_retries}] Connection Error: {error_msg}"))

                print(Color.warning(f"Waiting {delay}s before retry...\n"))
                time.sleep(delay)
                continue

            # Max retries reached
            error_msg = str(e.reason) if hasattr(e, 'reason') else str(e)
            yield f"\n{Color.error(f'[Connection Error]: {error_msg}')}\n"
            yield f"{Color.warning('Tip: If SSL errors persist, check your network connection or try again later.')}\n"
            return

        except ssl.SSLError as e:
            # Explicit SSL error handling (backup catch)
            if retry_count < max_retries - 1:
                delay = initial_delay * (2 ** retry_count)
                print(Color.warning(f"\n[Retry {retry_count + 1}/{max_retries}] SSL Handshake Error: {e}"))
                print(Color.warning(f"This is usually a temporary network/server issue."))
                print(Color.warning(f"Waiting {delay}s before retry...\n"))
                time.sleep(delay)
                continue

            # Max retries reached
            yield f"\n{Color.error(f'[SSL Error]: {e}')}\n"
            yield f"{Color.warning('Possible causes:')}\n"
            yield f"{Color.warning('  1. Temporary network instability')}\n"
            yield f"{Color.warning('  2. API server maintenance')}\n"
            yield f"{Color.warning('  3. Firewall/proxy interference')}\n"
            yield f"{Color.info('Try again in a few moments.')}\n"
            return

        except Exception as e:
            # Catch-all for unexpected errors
            error_type = type(e).__name__
            if retry_count < max_retries - 1:
                delay = initial_delay * (2 ** retry_count)
                print(Color.warning(f"\n[Retry {retry_count + 1}/{max_retries}] Unexpected error ({error_type}): {e}"))
                print(Color.warning(f"Waiting {delay}s before retry...\n"))
                time.sleep(delay)
                continue

            # Max retries reached
            yield f"\n{Color.error(f'[{error_type}]: {e}')}\n"
            yield f"{Color.info('If this persists, please check your network connection.')}\n"
            return

def call_llm_raw(prompt, temperature=0.7):
    """
    Call LLM without streaming (for extraction tasks).

    Args:
        prompt: Either a string prompt OR a list of message dicts
                e.g., [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
        temperature: Sampling temperature (default: 0.7)

    Returns:
        Complete response text
    """
    url = f"{config.BASE_URL}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.API_KEY}"
    }

    # Support both string prompt and messages list
    if isinstance(prompt, list):
        messages = prompt
    else:
        messages = [{"role": "user", "content": prompt}]

    data = {
        "model": config.MODEL_NAME,
        "messages": messages,
        "temperature": temperature,
        "stream": False
    }
    
    try:
        request = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers=headers
        )
        
        with urllib.request.urlopen(request, timeout=config.API_TIMEOUT) as response:
            result = json.loads(response.read().decode('utf-8'))
            content = result["choices"][0]["message"]["content"]
            # Sanitize: Remove OpenRouter/provider metadata tokens
            # Patterns like <|start|>, <|channel|>, <|message|>, <|final<|...|>
            # First handle nested patterns like <|final<|message|>
            content = re.sub(r'<\|final<\|[^>]*\|>', '', content)
            # Then handle simple patterns like <|start|>, <|end|>, etc.
            content = re.sub(r'<\|[^|<>]+\|>', '', content)
            # Clean up any remaining <| or |> artifacts
            content = re.sub(r'<\|[a-z_]+$', '', content)  # Trailing <|word
            return content.strip()

    except Exception as e:
        return f"Error calling LLM: {e}"

def estimate_tokens(messages):
    """Estimates token count based on characters (4 chars ~= 1 token)."""
    total_chars = sum(len(str(m.get("content", ""))) for m in messages)
    return total_chars // 4

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


def get_last_usage():
    """
    Get token usage from last API call.

    Returns:
        dict: {
            "input": int,
            "output": int,
            "total": int,
            "cache_created": int,      # Cache creation tokens (if caching enabled)
            "cache_read": int,         # Cache read tokens (if caching enabled)
            "total_cache_created": int,  # Session total cache created
            "total_cache_read": int      # Session total cache read
        }
        Returns None if no API call has been made yet.
    """
    global last_input_tokens, last_output_tokens
    global last_cache_creation_tokens, last_cache_read_tokens
    global total_cache_created, total_cache_read

    if last_input_tokens == 0 and last_output_tokens == 0:
        return None

    return {
        "input": last_input_tokens,
        "output": last_output_tokens,
        "total": last_input_tokens + last_output_tokens,
        "cache_created": last_cache_creation_tokens,
        "cache_read": last_cache_read_tokens,
        "total_cache_created": total_cache_created,
        "total_cache_read": total_cache_read
    }


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
        content = messages[0].get("content")

        # Multi-block format (optimized mode): check if already has cache_control
        if isinstance(content, list):
            # Check if any block already has cache_control (from optimized mode)
            has_cache = any(
                isinstance(block, dict) and "cache_control" in block
                for block in content
            )
            if has_cache:
                breakpoint_count += 1  # Count it but don't modify
                if config.DEBUG_MODE:
                    total_tokens = estimate_message_tokens(messages[0])
                    print(Color.info(f"[System] Cache breakpoint 1/{max_breakpoints}: System message (multi-block, pre-configured, {total_tokens} tokens)"))
            else:
                # Legacy list format without cache_control: apply it to last block
                tokens = estimate_message_tokens(messages[0])
                if tokens >= config.MIN_CACHE_TOKENS:
                    messages[0]["content"] = convert_to_cache_format(content, add_cache_control=True)
                    breakpoint_count += 1
                    if config.DEBUG_MODE:
                        print(Color.info(f"[System] Cache breakpoint 1/{max_breakpoints}: System message (list format, {tokens} tokens)"))
        else:
            # Single string format (legacy mode)
            tokens = estimate_message_tokens(messages[0])
            if tokens >= config.MIN_CACHE_TOKENS:
                messages[0]["content"] = convert_to_cache_format(content, add_cache_control=True)
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

    return messages
    return structured_content

# =========================================================================
# Embedding Utilities (Centralized)
# =========================================================================

# Cache for embedding dimension
_cached_embedding_dim = None

# Cache for embeddings (LRU)
# Key: {model}:{text_hash}, Value: list[float]
_embedding_cache = {}

def get_embedding(text: str, model: str = None) -> List[float]:
    """
    Get embedding for text using configured API.
    Handles caching and retries.
    
    Args:
        text: Text to embed
        model: Model name override (optional)
        
    Returns:
        List of floats (embedding vector)
    """
    if model is None:
        model = config.EMBEDDING_MODEL
        
    # Check cache
    cache_key = f"{model}:{hash(text)}"
    if cache_key in _embedding_cache:
        # Simple LRU: re-insert to move to end (Python 3.7+ dicts preserve order)
        val = _embedding_cache.pop(cache_key)
        _embedding_cache[cache_key] = val
        return val
        
    # Prepare API request
    url = f"{config.EMBEDDING_BASE_URL}/embeddings"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.EMBEDDING_API_KEY or config.API_KEY}",
        "User-Agent": "BrianCoder-Embedding"
    }
    data = {
        "input": text,
        "model": model,
        "encoding_format": "float"
    }
    
    # Retry logic
    max_retries = 3
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(
                url, 
                data=json.dumps(data).encode('utf-8'),
                headers=headers
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))
                embedding = result["data"][0]["embedding"]
                
                # Cache result
                _embedding_cache[cache_key] = embedding
                # Maintain cache size (max 1000)
                if len(_embedding_cache) > 1000:
                    try:
                        # Remove first item (oldest)
                        _embedding_cache.pop(next(iter(_embedding_cache)))
                    except StopIteration:
                        pass
                        
                return embedding
        except Exception as e:
            if attempt < max_retries - 1:
                delay = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                print(Color.warning(f"[Embedding] Retry {attempt+1}/{max_retries} in {delay}s: {e}"))
                time.sleep(delay)
                continue
            
            # Final attempt failed - simple error, no traceback
            print(Color.error(f"[Embedding] Failed after {max_retries} attempts: {e}"))
            raise e
            
    # Should not reach here
    return []

def get_embedding_dimension() -> int:
    """
    Get the embedding dimension.
    If config.EMBEDDING_DIMENSION is set, returns it.
    Otherwise, auto-detects by making a test API call.
    """
    global _cached_embedding_dim
    
    # 1. Check runtime cache
    if _cached_embedding_dim is not None:
        return _cached_embedding_dim
        
    # Try to detect from API first (Prioritize reality over config)
    try:
        if config.DEBUG_MODE:
            print(f"{Color.info('[System] Probing embedding dimension...')}")
            
        test_emb = get_embedding("test")
        if test_emb and len(test_emb) > 0:
            _cached_embedding_dim = len(test_emb)
            if config.DEBUG_MODE:
                print(f"{Color.success(f'[System] Detected embedding dimension: {_cached_embedding_dim}')}")
            return _cached_embedding_dim
    except Exception as e:
        if config.DEBUG_MODE:
            print(f"{Color.warning(f'[System] Dimension probe failed: {e}')}")

    # Fallback: If manually configured, use that
    if config.EMBEDDING_DIMENSION is not None and config.EMBEDDING_DIMENSION > 0:
        _cached_embedding_dim = config.EMBEDDING_DIMENSION
        return _cached_embedding_dim

    # Final fallback
    _cached_embedding_dim = 1536
    return 1536
