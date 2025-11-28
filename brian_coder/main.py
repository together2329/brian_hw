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

def chat_completion_stream(messages):
    """
    Sends a chat completion request to the LLM using urllib.
    Yields content chunks from the SSE stream.
    """
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

# --- 3. ReAct Logic ---

def parse_action(text):
    """Parses the last 'Action: Tool(args)' from the text."""
    match = re.search(r"Action:\s*(\w+)\((.*)\)", text, re.DOTALL)
    if match:
        tool_name = match.group(1)
        args_str = match.group(2)
        return tool_name, args_str
    return None, None

def execute_tool(tool_name, args_str):
    if tool_name not in tools.AVAILABLE_TOOLS:
        return f"Error: Tool '{tool_name}' not found."
    
    func = tools.AVAILABLE_TOOLS[tool_name]
    try:
        # Helper to parse arguments
        def _proxy(*args, **kwargs):
            return args, kwargs
        
        # Eval safely-ish
        parsed_args, parsed_kwargs = eval(f"_proxy({args_str})", {"_proxy": _proxy})
        return func(*parsed_args, **parsed_kwargs)

    except Exception as e:
        return f"Error parsing/executing arguments: {e}"

# --- 4. Main Loop ---

def chat_loop():
    messages = [
        {"role": "system", "content": config.SYSTEM_PROMPT}
    ]

    print(f"Brian Coder Agent (Zero-Dependency) initialized.")
    print(f"Connecting to: {config.BASE_URL}")
    print("Type 'exit' or 'quit' to stop.\n")

    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() in ["exit", "quit"]:
                break
            
            messages.append({"role": "user", "content": user_input})

            # ReAct Loop: Max 5 turns
            for _ in range(5):
                print("Agent (Thinking): ", end="", flush=True)
                
                collected_content = ""
                # Call LLM via urllib
                for content_chunk in chat_completion_stream(messages):
                    print(content_chunk, end="", flush=True)
                    collected_content += content_chunk
                print("\n")

                # Add assistant response to history
                messages.append({"role": "assistant", "content": collected_content})

                # Check for Action
                tool_name, args_str = parse_action(collected_content)
                
                if tool_name:
                    print(f"  [System] Executing {tool_name}...")
                    observation = execute_tool(tool_name, args_str)
                    print(f"  [System] Observation: {observation}\n")
                    
                    messages.append({
                        "role": "user", 
                        "content": f"Observation: {observation}"
                    })
                else:
                    break
            
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"\nAn error occurred: {e}")
            pass

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--prompt":
        # One-shot mode
        prompt = sys.argv[2]
        client = chat_completion_stream([
            {"role": "system", "content": config.SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ])
        print(f"User: {prompt}")
        print("Agent: ", end="", flush=True)
        for chunk in client:
            print(chunk, end="", flush=True)
        print("\n")
    else:
        chat_loop()
