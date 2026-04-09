# Firecrawl Setup Guide for Common AI Agent

This guide explains how to bring up **Firecrawl** so that the `web_search`, `web_fetch`, and `web_extract` tools work in Common AI Agent.

---

## Overview

Common AI Agent uses a **self-hosted Firecrawl** instance as its web-scraping backend. The agent's web tools (`core/tools_web.py`) send HTTP requests to a Firecrawl API server running locally.

### Architecture

```
Common AI Agent
  └─ tools_web.py
       ├─ web_search()   → POST http://localhost:3002/v1/search
       ├─ web_fetch()    → POST http://localhost:3002/v0/scrape
       └─ web_extract()  → POST http://localhost:3002/v1/extract
                │
                ▼
        Firecrawl API Server (port 3002)
```

---

## Prerequisites

- **Docker** (recommended) or **Node.js 18+ with pnpm**
- ~4 GB RAM minimum for the Firecrawl stack
- API keys for the search provider (see below)

---

## Option A: Docker (Recommended)

### 1. Clone the Firecrawl repo

```bash
git clone https://github.com/mendableai/firecrawl.git
cd firecrawl
```

### 2. Configure environment

```bash
cp docker-compose.yaml.example docker-compose.yaml
```

Edit `docker-compose.yaml` or create a `.env` file in the firecrawl root with:

```env
# Required — get from https://www.firecrawl.dev/ (free tier available)
FIRECRAWL_API_KEY=fc-your-api-key-here

# Search provider (choose one)
# For Google: set GOOGLE_SEARCH_API_KEY + GOOGLE_SEARCH_CX_ID
# For Bing:   set BING_SEARCH_API_KEY
# For SearXNG: self-hosted, no key needed

# Server config
PORT=3002
HOST=0.0.0.0
```

### 3. Start the services

```bash
docker compose up -d
```

This starts:
- **Firecrawl API** on port `3002`
- **Redis** (queue/cache)
- **Playwright** (JS rendering)

### 4. Verify it's running

```bash
curl -s http://localhost:3002/health | jq
```

Expected response:
```json
{ "status": "ok" }
```

---

## Option B: Native (pnpm)

### 1. Clone & install

```bash
git clone https://github.com/mendableai/firecrawl.git
cd firecrawl
pnpm install
```

### 2. Configure

```bash
cp apps/api/.env.example apps/api/.env
```

Edit `apps/api/.env` with your API keys (same as Docker option above).

### 3. Start dependencies (Redis)

```bash
# macOS
brew install redis
brew services start redis

# Linux
sudo systemctl start redis
```

### 4. Start the API server

```bash
cd apps/api
pnpm run start:production
```

The server listens on **port 3002** by default.

---

## Configure Common AI Agent

### 1. Enable web tools

Edit `~/.config/common_ai_agent/config` (or the project `.config` file):

```ini
ENABLE_WEB_TOOLS=true
FIRECRAWL_API_URL=http://localhost:3002
FIRECRAWL_TIMEOUT=30
```

### 2. Restart the agent

Restart your Common AI Agent session so it picks up the new config.

---

## Usage

Once Firecrawl is running and web tools are enabled, you can use:

### `web_search` — Search the web
```
web_search(query="PCIe 6.0 specification details", limit=5)
web_search(query="latest Python tutorial", limit=3, tbs="qdr:w")   # past week
```

### `web_fetch` — Scrape a URL
```
web_fetch(url="https://docs.python.org/3/library/urllib.html")
web_fetch(url="https://example.com", formats="html", wait_for=5000)
```

### `web_extract` — Extract structured data
```
web_extract(
  urls="https://example.com/product",
  prompt="Extract product name, price, and availability"
)
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `Firecrawl service is not reachable at http://localhost:3002` | Start the server: `cd firecrawl && docker compose up -d` |
| Timeout errors | Increase `FIRECRAWL_TIMEOUT` (e.g., `60`) in `.config` |
| Search returns no results | Check your search API keys (Google/Bing) in Firecrawl's `.env` |
| JS-heavy pages return empty | Increase `wait_for` parameter (e.g., `5000` ms) |
| Bot detection / CAPTCHA | Try `web_search()` instead of `web_fetch()` — may have cached results |
| Port already in use | Change `FIRECRAWL_API_URL` to a different port (e.g., `3003`) |

### Check if Firecrawl is running

```bash
# Quick health check
curl -s http://localhost:3002/health

# Test a search
curl -X POST http://localhost:3002/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query":"hello world","limit":1}'
```

---

## Quick Start Summary

```bash
# 1. Clone Firecrawl
git clone https://github.com/mendableai/firecrawl.git ~/firecrawl
cd ~/firecrawl

# 2. Set up env (add your search API keys)
cp docker-compose.yaml.example docker-compose.yaml
# Edit .env with your keys

# 3. Start
docker compose up -d

# 4. Verify
curl http://localhost:3002/health

# 5. Enable in Common AI Agent config
echo "ENABLE_WEB_TOOLS=true" >> ~/.config/common_ai_agent/config

# 6. Restart your agent session — done!
```

---

## Files Reference

| File | Purpose |
|------|---------|
| `core/tools_web.py` | Web tool implementations (search, fetch, extract) |
| `src/config.py` | Reads `ENABLE_WEB_TOOLS`, `FIRECRAWL_API_URL`, `FIRECRAWL_TIMEOUT` |
| `.config` | Agent config file where web tools are enabled/disabled |
| `core/tool_schema.py` | Tool schema definitions for the LLM |
| `core/tool_descriptions/tools/web_*.txt` | Detailed tool usage guides |
