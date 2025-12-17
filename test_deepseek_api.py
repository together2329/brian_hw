#!/usr/bin/env python3
"""
Comprehensive test to check DeepSeek API response patterns
Tests various prompt types to see reasoning vs content behavior
"""
import os
import sys
import json
import urllib.request
import time

# Test cases - various prompt types
TEST_CASES = [
    {"name": "Simple greeting", "prompt": "Say hello in one sentence."},
    {"name": "Math problem", "prompt": "What is 2 + 2? Answer with just the number."},
    {"name": "Code request", "prompt": "Write a Python function to add two numbers. Just the code."},
    {"name": "Question", "prompt": "What is the capital of France? One word answer."},
    {"name": "Complex reasoning", "prompt": "Explain why the sky is blue in one paragraph."},
    {"name": "Tool-like request", "prompt": "Thought: I need to read a file.\nAction: read_file(path='test.py')"},
]

def run_test(api_key, base_url, model_name, prompt, test_name):
    """Run a single test and return results"""
    
    url = f"{base_url}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    
    data = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "stream": True,
    }
    
    reasoning_chars = 0
    content_chars = 0
    has_reasoning = False
    has_content = False
    
    try:
        req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers)
        
        with urllib.request.urlopen(req, timeout=60) as response:
            for line in response:
                line = line.decode('utf-8').strip()
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                        if "choices" in chunk and len(chunk["choices"]) > 0:
                            delta = chunk["choices"][0].get("delta", {})
                            
                            reasoning = delta.get("reasoning") or delta.get("reasoning_content", "")
                            if reasoning:
                                has_reasoning = True
                                reasoning_chars += len(reasoning)
                            
                            content = delta.get("content", "")
                            if content:
                                has_content = True
                                content_chars += len(content)
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        return {"name": test_name, "error": str(e)}
    
    return {
        "name": test_name,
        "has_reasoning": has_reasoning,
        "has_content": has_content,
        "reasoning_chars": reasoning_chars,
        "content_chars": content_chars,
        "reasoning_only": has_reasoning and not has_content,
        "content_only": has_content and not has_reasoning,
        "both": has_reasoning and has_content,
    }

def main():
    # Load .env
    env_path = os.path.join(os.path.dirname(__file__), "brian_coder", ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ[key] = val
    
    api_key = os.environ.get("LLM_API_KEY") or os.environ.get("API_KEY")
    base_url = os.environ.get("LLM_BASE_URL", "https://openrouter.ai/api/v1")
    model_name = os.environ.get("LLM_MODEL_NAME", "deepseek/deepseek-v3.2-speciale")
    
    if not api_key:
        print("Error: LLM_API_KEY not found")
        sys.exit(1)
    
    print(f"Model: {model_name}")
    print("=" * 70)
    print(f"{'Test Name':<25} {'Reasoning':<12} {'Content':<12} {'Pattern':<15}")
    print("=" * 70)
    
    results = []
    for i, test in enumerate(TEST_CASES):
        print(f"\r[{i+1}/{len(TEST_CASES)}] Testing: {test['name']:<20}", end="", flush=True)
        
        result = run_test(api_key, base_url, model_name, test['prompt'], test['name'])
        results.append(result)
        
        # Rate limit
        time.sleep(2)
    
    # Clear line and print results
    print("\r" + " " * 60 + "\r", end="")
    
    for r in results:
        if "error" in r:
            print(f"{r['name']:<25} ERROR: {r['error']}")
        else:
            pattern = "BOTH" if r['both'] else ("REASONING" if r['reasoning_only'] else ("CONTENT" if r['content_only'] else "NONE"))
            r_chars = f"{r['reasoning_chars']}c" if r['has_reasoning'] else "-"
            c_chars = f"{r['content_chars']}c" if r['has_content'] else "-"
            print(f"{r['name']:<25} {r_chars:<12} {c_chars:<12} {pattern:<15}")
    
    print("=" * 70)
    
    # Summary
    reasoning_only = sum(1 for r in results if r.get('reasoning_only'))
    content_only = sum(1 for r in results if r.get('content_only'))
    both = sum(1 for r in results if r.get('both'))
    
    print(f"\nSummary:")
    print(f"  Reasoning only: {reasoning_only}")
    print(f"  Content only: {content_only}")
    print(f"  Both: {both}")
    
    if reasoning_only > 0:
        print(f"\n⚠️  WARNING: {reasoning_only} cases with reasoning only - need fallback!")
    else:
        print(f"\n✅ All responses have content - no fallback needed")

if __name__ == "__main__":
    main()
