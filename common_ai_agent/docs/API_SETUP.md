# API Setup Guide

## OpenAI

```bash
export LLM_BASE_URL="https://api.openai.com/v1"
export LLM_API_KEY="sk-proj-YOUR_KEY"
export LLM_MODEL_NAME="gpt-4o-mini"
python3 src/main.py
```

Models: `gpt-4o-mini` (fast, cheap), `gpt-4o` (powerful)

## OpenRouter

```bash
export LLM_BASE_URL="https://openrouter.ai/api/v1"
export LLM_API_KEY="sk-or-v1-YOUR_KEY"
export LLM_MODEL_NAME="openrouter/z-ai/glm-4.7"
python3 src/main.py
```

Free models: `meta-llama/llama-3.3-70b-instruct:free`, `google/gemini-flash-1.5:free`

## Local / vLLM

```bash
export LLM_BASE_URL="http://localhost:8000/v1"
export LLM_API_KEY="none"
export LLM_MODEL_NAME="your-model-name"
python3 src/main.py
```

Any OpenAI-compatible API endpoint works.

## Sub-Agent Models

```bash
# Primary agent (main loop)
export PRIMARY_MODEL="openrouter/z-ai/glm-4.7"

# Sub-agents (explore, execute, review, task)
export SUBAGENT_LOW_MODEL="openrouter/qwen/qwen3-next-80b-a3b-instruct"

# Plan agent (high reasoning)
export SUBAGENT_HIGH_MODEL="openrouter/z-ai/glm-4.7"
```

## Troubleshooting

| Error | Fix |
|-------|-----|
| HTTP 401 | Check API key |
| HTTP 429 | Increase `RATE_LIMIT_DELAY` (default: 5s) |
| Model not found | Check model name for provider |
| Timeout | Check `LLM_BASE_URL` connectivity |
