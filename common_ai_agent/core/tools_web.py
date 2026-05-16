"""
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
"""

import json
import os
import urllib.request
import urllib.error
from typing import Dict, Optional


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

def _get_api_url() -> str:
    """Read Firecrawl API URL from environment."""
    return os.environ.get("FIRECRAWL_API_URL", "http://localhost:3002")


def _get_timeout() -> int:
    """Read request timeout from environment."""
    try:
        return int(os.environ.get("FIRECRAWL_TIMEOUT", "30"))
    except (ValueError, TypeError):
        return 30


# ---------------------------------------------------------------------------
# HTTP helper
# ---------------------------------------------------------------------------

def _firecrawl_request(endpoint: str, payload: dict) -> dict:
    """
    Send a POST request to the Firecrawl API.

    Args:
        endpoint: API path (e.g. '/v1/search')
        payload:  JSON body

    Returns:
        Parsed JSON response as dict

    Raises:
        RuntimeError: If Firecrawl service is unreachable or returns error
    """
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
    """
    Serialize result dict to JSON string, truncating if too large.
    Large responses are trimmed to avoid context bloat.
    """
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
# CLI engines — Claude Code (`claude-cli`) and Cursor Agent (`cursor-cli`)
# act as alternative WebSearch / WebFetch backends when Firecrawl is not
# available (no API key, server down). They use the LLM CLI's built-in
# WebSearch / WebFetch tools and return the answer text directly.
# ---------------------------------------------------------------------------

def _cli_available(binary: str) -> bool:
    import shutil
    return bool(shutil.which(binary))


def _search_via_claude_cli(query: str, limit: int = 5, timeout_sec: int = 120) -> str:
    try:
        from src.claude_cli_backend import claude_cli_call
    except ModuleNotFoundError:
        from claude_cli_backend import claude_cli_call  # type: ignore
    prompt = (
        f"Use WebSearch to find up to {limit} results for: {query}\n"
        "Return the top results as a concise list with title + URL + 1-line snippet each."
    )
    return claude_cli_call(
        messages=[{"role": "user", "content": prompt}],
        model="sonnet",
        permission_mode="bypassPermissions",
        tools="WebSearch,WebFetch",
        no_session_persistence=True,
        output_format="json",
        timeout_sec=timeout_sec,
    )


def _fetch_via_claude_cli(url: str, timeout_sec: int = 120) -> str:
    try:
        from src.claude_cli_backend import claude_cli_call
    except ModuleNotFoundError:
        from claude_cli_backend import claude_cli_call  # type: ignore
    prompt = (
        f"Use WebFetch to retrieve and summarize the content at: {url}\n"
        "Return the main content as markdown."
    )
    return claude_cli_call(
        messages=[{"role": "user", "content": prompt}],
        model="sonnet",
        permission_mode="bypassPermissions",
        tools="WebFetch,WebSearch",
        no_session_persistence=True,
        output_format="json",
        timeout_sec=timeout_sec,
    )


def _search_via_cursor_cli(query: str, limit: int = 5) -> str:
    try:
        from src.cursor_agent_backend import cursor_agent_call
    except ModuleNotFoundError:
        from cursor_agent_backend import cursor_agent_call  # type: ignore
    prompt = (
        f"Search the web for up to {limit} results for: {query}\n"
        "Return the top results as a concise list with title + URL + 1-line snippet each."
    )
    return cursor_agent_call(
        messages=[{"role": "user", "content": prompt}],
        model="auto",
        yolo=True,
    )


def _fetch_via_cursor_cli(url: str) -> str:
    try:
        from src.cursor_agent_backend import cursor_agent_call
    except ModuleNotFoundError:
        from cursor_agent_backend import cursor_agent_call  # type: ignore
    prompt = (
        f"Fetch the content of this URL and summarize the main body as markdown: {url}"
    )
    return cursor_agent_call(
        messages=[{"role": "user", "content": prompt}],
        model="auto",
        yolo=True,
    )


def _engine_fallback_chain(engine: str) -> list[str]:
    """Resolve ``engine`` argument to an ordered try-list."""
    e = (engine or "auto").strip().lower()
    if e == "firecrawl":
        return ["firecrawl"]
    if e in ("claude", "claude-cli"):
        return ["claude-cli"]
    if e in ("cursor", "cursor-cli", "cursor-agent"):
        return ["cursor-cli"]
    # "auto" — prefer Firecrawl (cheapest), then the CLI backends.
    chain = ["firecrawl"]
    if _cli_available("claude"):
        chain.append("claude-cli")
    if _cli_available("cursor-agent"):
        chain.append("cursor-cli")
    return chain


# ---------------------------------------------------------------------------
# Tool: web_search
# ---------------------------------------------------------------------------

def web_search(query: str, limit: int = 5, lang: str = "en", tbs: str = "", engine: str = "auto") -> str:
    """
    Search the web. Tries the requested ``engine`` in order, falling back
    to the next on failure. Default ``auto`` prefers Firecrawl (cheapest)
    then the LLM CLI backends (``claude-cli``, ``cursor-cli``) when their
    binaries are installed.

    Args:
        query: Search query string
        limit: Maximum number of results (1-20, default: 5)
        lang:  Language code (default: 'en', use 'ko' for Korean) — Firecrawl only
        tbs:   Time filter — 'qdr:d' (day), 'qdr:w' (week),
               'qdr:m' (month), 'qdr:y' (year), '' (any time) — Firecrawl only
        engine: "auto" | "firecrawl" | "claude-cli" | "cursor-cli"

    Returns:
        JSON-formatted Firecrawl results, or the CLI's text answer.
    """
    limit = max(1, min(20, int(limit)))
    errors: list[str] = []
    for backend in _engine_fallback_chain(engine):
        try:
            if backend == "firecrawl":
                payload = {
                    "query": query,
                    "limit": limit,
                    "scrapeOptions": {"formats": ["markdown"]},
                }
                if lang:
                    payload["lang"] = lang
                if tbs:
                    payload["tbs"] = tbs
                result = _firecrawl_request("/v1/search", payload)
                if not result.get("success", True):
                    raise RuntimeError(f"firecrawl: {result.get('error', 'unknown')}")
                data = result.get("data", [])
                if not data:
                    if engine == "firecrawl":
                        return f"No results found for query: '{query}'"
                    raise RuntimeError("firecrawl: empty results")
                formatted = []
                for i, item in enumerate(data, 1):
                    formatted.append({
                        "index": i,
                        "title": item.get("metadata", {}).get("title", ""),
                        "url": item.get("metadata", {}).get("sourceURL", item.get("url", "")),
                        "content": item.get("markdown", item.get("content", ""))[:2000],
                    })
                return _truncate_result({"engine": "firecrawl", "results": formatted, "total": len(formatted)})
            if backend == "claude-cli":
                return _search_via_claude_cli(query, limit=limit)
            if backend == "cursor-cli":
                return _search_via_cursor_cli(query, limit=limit)
        except Exception as exc:
            errors.append(f"{backend}: {exc}")
            continue
    return "web_search failed — tried " + "; ".join(errors) if errors else (
        f"web_search: no backend available for engine={engine!r}"
    )


# ---------------------------------------------------------------------------
# Tool: web_fetch
# ---------------------------------------------------------------------------

def web_fetch(url: str, formats: str = "markdown", wait_for: int = 3000, engine: str = "auto") -> str:
    """
    Fetch and scrape content from a specific URL. Tries ``engine`` in
    order, falling back to the next on failure. Default ``auto`` prefers
    Firecrawl (full HTML/markdown) and falls back to the LLM CLI
    backends (``claude-cli`` / ``cursor-cli``) when their binaries are
    installed.

    Args:
        url:      URL to scrape
        formats:  Output format — 'markdown' (default), 'html', or 'rawHtml' — Firecrawl only
        wait_for: Milliseconds to wait for JavaScript rendering — Firecrawl only
        engine:   "auto" | "firecrawl" | "claude-cli" | "cursor-cli"

    Returns:
        Markdown / HTML payload from Firecrawl, or the CLI's text summary.
    """
    errors: list[str] = []
    for backend in _engine_fallback_chain(engine):
        try:
            if backend == "firecrawl":
                payload = {
                    "url": url,
                    "formats": [formats] if isinstance(formats, str) else formats,
                }
                if wait_for > 0:
                    payload["waitFor"] = int(wait_for)
                result = _firecrawl_request("/v0/scrape", payload)
                if not result.get("success", True):
                    raise RuntimeError(f"firecrawl: {result.get('error', 'unknown')}")
                data = result.get("data", {})
                if formats in ("html", ["html"]):
                    content = data.get("html", "")
                elif formats in ("rawHtml", ["rawHtml"]):
                    content = data.get("rawHtml", "")
                else:
                    content = data.get("markdown", "")
                if not content:
                    if engine == "firecrawl":
                        return f"No content retrieved from: {url}"
                    raise RuntimeError("firecrawl: empty body")
                metadata = data.get("metadata", {})
                response = {
                    "engine": "firecrawl",
                    "metadata": {
                        "title": metadata.get("title", ""),
                        "url": url,
                        "description": metadata.get("description", ""),
                    },
                    "content": content[:6000],
                }
                if len(content) > 6000:
                    response["truncated"] = (
                        f"Content truncated from {len(content)} to 6000 chars. "
                        "Use web_extract for specific data."
                    )
                return _truncate_result(response)
            if backend == "claude-cli":
                return _fetch_via_claude_cli(url)
            if backend == "cursor-cli":
                return _fetch_via_cursor_cli(url)
        except Exception as exc:
            errors.append(f"{backend}: {exc}")
            continue
    return "web_fetch failed — tried " + "; ".join(errors) if errors else (
        f"web_fetch: no backend available for engine={engine!r}"
    )


# ---------------------------------------------------------------------------
# Tool: web_extract
# ---------------------------------------------------------------------------

def web_extract(
    urls: str,
    prompt: str = "",
    schema: str = "",
) -> str:
    """
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
    """
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
    """
    Poll Firecrawl extract job until complete.

    Returns:
        Final result dict, or error string on failure.
    """
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
