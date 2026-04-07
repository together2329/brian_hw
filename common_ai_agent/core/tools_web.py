\"\"\"
core/tools_web.py — Firecrawl-powered web tools for common_ai_agent

Provides web search, fetch, and extract capabilities via locally-hosted
or remote Firecrawl API. Zero-dependency (uses urllib.request).

Tools:
  web_search  — Search the web and get scraped results
  web_fetch   — Scrape a specific URL
  web_extract — AI-powered structured data extraction from URLs

Configuration (.config):
  ENABLE_WEB_TOOLS=true          # Enable/disable (default: false)
  FIRECRAWL_API_URL=http://localhost:3002  # Firecrawl endpoint
  FIRECRAWL_TIMEOUT=30           # Request timeout in seconds
\"\"\"

import json
import os
import urllib.request
import urllib.error
from typing import Dict, Optional


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

def _get_api_url() -> str:
    \"\"\"Read Firecrawl API URL from environment.\"\"\"
    return os.environ.get("FIRECRAWL_API_URL", "http://localhost:3002")


def _get_timeout() -> int:
    \"\"\"Read request timeout from environment.\"\"\"
    try:
        return int(os.environ.get("FIRECRAWL_TIMEOUT", "30"))
    except (ValueError, TypeError):
        return 30


# ---------------------------------------------------------------------------
# HTTP helper
# ---------------------------------------------------------------------------

def _firecrawl_request(endpoint: str, payload: dict) -> dict:
    \"\"\"
    Send a POST request to the Firecrawl API.

    Args:
        endpoint: API path (e.g. '/v1/search')
        payload:  JSON body

    Returns:
        Parsed JSON response as dict

    Raises:
        RuntimeError: If Firecrawl service is unreachable or returns error
    \"\"\"
    api_url = _get_api_url()
    timeout = _get_timeout()
    url = f"{api_url.rstrip('/')}/{endpoint.lstrip('/')}"

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body)
    except urllib.error.ConnectionError:
        raise RuntimeError(
            f"Firecrawl service is not reachable at {api_url}. "
            f"Start it first: cd /path/to/firecrawl/apps/api && pnpm run start:production"
        )
    except urllib.error.HTTPError as e:
        error_body = ""
        try:
            error_body = e.read().decode("utf-8")[:500]
        except Exception:
            pass
        raise RuntimeError(
            f"Firecrawl API error (HTTP {e.code}): {error_body}"
        )
    except urllib.error.URLError as e:
        raise RuntimeError(
            f"Firecrawl request failed: {e.reason}. "
            f"Ensure Firecrawl is running at {api_url}"
        )
    except json.JSONDecodeError:
        raise RuntimeError("Firecrawl returned invalid JSON")


# ---------------------------------------------------------------------------
# Output truncation
# ---------------------------------------------------------------------------

_MAX_RESULT_CHARS = 8000


def _truncate_result(data: dict, max_chars: int = _MAX_RESULT_CHARS) -> str:
    \"\"\"
    Serialize result dict to JSON string, truncating if too large.
    Large responses are trimmed to avoid context bloat.
    \"\"\"
    text = json.dumps(data, indent=2, ensure_ascii=False)
    if len(text) > max_chars:
        truncated = text[:max_chars]
        trailer = (
            "\n\n... [Truncated: %d total chars, showing first %d]"
            % (len(text), max_chars)
        )
        return truncated + trailer
    return text


# ---------------------------------------------------------------------------
# Tool: web_search
# ---------------------------------------------------------------------------

def web_search(query: str, limit: int = 5, lang: str = "en", tbs: str = "") -> str:
    \"\"\"
    Search the web using Firecrawl Search API. Returns scraped content
    (markdown) for each result.

    Args:
        query: Search query string
        limit: Maximum number of results (1-20, default: 5)
        lang:  Language code (default: 'en', use 'ko' for Korean)
        tbs:   Time filter — 'qdr:d' (day), 'qdr:w' (week),
               'qdr:m' (month), 'qdr:y' (year), '' (any time)

    Returns:
        JSON string with search results (title, url, content for each)
    \"\"\"
    limit = max(1, min(20, int(limit)))

    payload = {
        "query": query,
        "limit": limit,
        "scrapeOptions": {
            "formats": ["markdown"],
        },
    }
    if lang:
        payload["lang"] = lang
    if tbs:
        payload["tbs"] = tbs

    try:
        result = _firecrawl_request("/v1/search", payload)
    except RuntimeError as e:
        return f"Error: {e}"

    # Format results for readability
    if not result.get("success", True):
        return f"Search failed: {result.get('error', 'Unknown error')}"

    data = result.get("data", [])
    if not data:
        return f"No results found for query: '{query}'"

    formatted = []
    for i, item in enumerate(data, 1):
        entry = {
            "index": i,
            "title": item.get("metadata", {}).get("title", ""),
            "url": item.get("metadata", {}).get("sourceURL", item.get("url", "")),
            "content": item.get("markdown", item.get("content", ""))[:2000],
        }
        formatted.append(entry)

    return _truncate_result({"results": formatted, "total": len(formatted)})


# ---------------------------------------------------------------------------
# Tool: web_fetch
# ---------------------------------------------------------------------------

def web_fetch(url: str, formats: str = "markdown", wait_for: int = 3000) -> str:
    \"\"\"
    Fetch and scrape content from a specific URL using Firecrawl Scrape API.

    Args:
        url:      URL to scrape
        formats:  Output format — 'markdown' (default), 'html', or 'rawHtml'
        wait_for: Milliseconds to wait for JavaScript rendering (default: 3000)

    Returns:
        Scraped content in requested format
    \"\"\"
    payload = {
        "url": url,
        "formats": [formats] if isinstance(formats, str) else formats,
    }
    if wait_for > 0:
        payload["waitFor"] = int(wait_for)

    try:
        result = _firecrawl_request("/v0/scrape", payload)
    except RuntimeError as e:
        return f"Error: {e}"

    if not result.get("success", True):
        return f"Fetch failed: {result.get('error', 'Unknown error')}"

    data = result.get("data", {})

    # Extract content in requested format
    content = ""
    if formats == "html" or formats == ["html"]:
        content = data.get("html", "")
    elif formats == "rawHtml" or formats == ["rawHtml"]:
        content = data.get("rawHtml", "")
    else:
        content = data.get("markdown", "")

    if not content:
        return f"No content retrieved from: {url}"

    metadata = data.get("metadata", {})
    header = {
        "title": metadata.get("title", ""),
        "url": url,
        "description": metadata.get("description", ""),
    }

    response = {
        "metadata": header,
        "content": content[:6000],
    }
    if len(content) > 6000:
        response["truncated"] = f"Content truncated from {len(content)} to 6000 chars. Use web_extract for specific data."

    return _truncate_result(response)


# ---------------------------------------------------------------------------
# Tool: web_extract
# ---------------------------------------------------------------------------

def web_extract(
    urls: str,
    prompt: str = "",
    schema: str = "",
) -> str:
    \"\"\"
    Extract structured data from URLs using Firecrawl AI-powered Extract API.
    Useful for pulling specific fields (price, title, date, etc.) from web pages.

    Args:
        urls:   URL(s) to extract from. Single URL or comma-separated list.
        prompt: Natural language instruction for what to extract
                (e.g. 'Extract product name, price, and availability')
        schema: JSON schema defining the output structure.
                Example: '{"type":"object","properties":{"title":{"type":"string"}}}'

    Returns:
        Extracted structured data as JSON
    \"\"\"
    # Parse URLs
    if isinstance(urls, str):
        url_list = [u.strip() for u in urls.split(",") if u.strip()]
    else:
        url_list = urls

    if not url_list:
        return "Error: At least one URL is required."

    payload = {
        "urls": url_list,
    }
    if prompt:
        payload["prompt"] = prompt
    if schema:
        try:
            payload["schema"] = json.loads(schema) if isinstance(schema, str) else schema
        except json.JSONDecodeError:
            return f"Error: Invalid JSON schema: {schema}"

    try:
        result = _firecrawl_request("/v1/extract", payload)
    except RuntimeError as e:
        return f"Error: {e}"

    # Extract API may return immediately or require polling
    if result.get("success") is False:
        return f"Extract failed: {result.get('error', 'Unknown error')}"

    # Check if it's an async job (returns an ID)
    if "id" in result and "data" not in result:
        job_id = result["id"]
        # Poll for result (up to 60 seconds)
        status = _poll_extract_job(job_id)
        if isinstance(status, str):
            return status  # Error message
        result = status

    return _truncate_result(result.get("data", result), max_chars=6000)


def _poll_extract_job(job_id: str, max_wait: int = 60, interval: int = 3) -> dict:
    \"\"\"
    Poll Firecrawl extract job until complete.

    Returns:
        Final result dict, or error string on failure.
    \"\"\"
    import time

    api_url = _get_api_url()
    elapsed = 0

    while elapsed < max_wait:
        time.sleep(interval)
        elapsed += interval

        url = f"{api_url.rstrip('/')}/v1/extract/{job_id}"
        try:
            req = urllib.request.Request(url, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            return f"Error polling extract job {job_id}: {e}"

        status = data.get("status", "")
        if status == "completed":
            return data
        elif status == "failed":
            return f"Extract job failed: {data.get('error', 'Unknown error')}"
        # Otherwise still pending/processing — keep polling

    return f"Error: Extract job {job_id} timed out after {max_wait}s"


# ---------------------------------------------------------------------------
# Tool Registry (exported dict — matches tools_cmux.py pattern)
# ---------------------------------------------------------------------------

WEB_TOOLS = {
    "web_search":  web_search,
    "web_fetch":   web_fetch,
    "web_extract": web_extract,
}
