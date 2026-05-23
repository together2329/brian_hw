"""
core/tools_web.py — Cursor CLI-backed web tools for common_ai_agent

Provides web search/fetch capabilities through cursor-agent CLI.
The structured web_extract tool still uses Firecrawl's extract endpoint.

Tools:
  web_search  — Search the web via Cursor CLI
  websearch   — Alias for web_search
  web_fetch   — Fetch/summarize a specific URL via Cursor CLI
  web_extract — AI-powered structured data extraction from URLs

Configuration (.config):
  ENABLE_WEB_TOOLS=true          # Enable/disable (default: false)
  WEB_CURSOR_MODEL=auto          # cursor-agent model
  WEB_CURSOR_TIMEOUT=120         # cursor-agent timeout in seconds
  WEB_CURSOR_YOLO=true           # non-interactive cursor-agent execution
  FIRECRAWL_API_URL=http://localhost:3002  # Firecrawl endpoint for web_extract
  FIRECRAWL_TIMEOUT=30           # Firecrawl request timeout in seconds
"""

import json
import os
import shutil
import subprocess
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


def _get_cursor_timeout() -> int:
    """Read cursor-agent timeout from environment."""
    try:
        return max(1, int(os.environ.get("WEB_CURSOR_TIMEOUT", "120")))
    except (ValueError, TypeError):
        return 120


def _get_cursor_model() -> str:
    return os.environ.get("WEB_CURSOR_MODEL", "auto").strip() or "auto"


def _cursor_yolo_enabled() -> bool:
    return os.environ.get("WEB_CURSOR_YOLO", "true").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


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
# Cursor CLI engine. Web search/fetch intentionally do not fall back to
# Firecrawl or Claude; Cursor is the required backend for this tool surface.
# ---------------------------------------------------------------------------

def _cursor_agent_text(stdout: str) -> str:
    """Extract assistant text/result from cursor-agent stream-json output."""
    chunks: list[str] = []
    final_result = ""
    for raw in str(stdout or "").splitlines():
        raw = raw.strip()
        if not raw:
            continue
        try:
            item = json.loads(raw)
        except json.JSONDecodeError:
            chunks.append(raw)
            continue
        if item.get("type") == "assistant" and "timestamp_ms" in item:
            for block in item.get("message", {}).get("content", []):
                if isinstance(block, dict) and block.get("type") == "text":
                    chunks.append(block.get("text", ""))
        elif item.get("type") == "result":
            final_result = str(item.get("result") or "")
    text = "".join(chunks).strip()
    return text or final_result.strip()


def _cursor_agent_request(prompt: str) -> str:
    exe = shutil.which(os.environ.get("WEB_CURSOR_BIN", "cursor-agent"))
    if not exe:
        raise RuntimeError("cursor-agent not found in PATH")
    cmd = [exe, "--model", _get_cursor_model()]
    if _cursor_yolo_enabled():
        cmd.append("--yolo")
    cmd += [
        "--print",
        "--output-format",
        "stream-json",
        "--stream-partial-output",
        "-p",
        prompt,
    ]
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=_get_cursor_timeout(),
    )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()
        raise RuntimeError(f"cursor-agent failed rc={proc.returncode}: {detail[:800]}")
    text = _cursor_agent_text(proc.stdout)
    if not text:
        raise RuntimeError("cursor-agent returned empty output")
    return text


def _search_via_cursor_cli(query: str, limit: int = 5, lang: str = "en", tbs: str = "") -> str:
    prompt = (
        "[ATLAS web_search]\n"
        "Use Cursor's web search capability only. Do not inspect or edit local files.\n"
        f"Query: {query}\n"
        f"Max results: {limit}\n"
        f"Language preference: {lang or 'any'}\n"
        f"Time filter hint: {tbs or 'none'}\n\n"
        "Return concise Markdown with:\n"
        "- engine: cursor-cli\n"
        "- query\n"
        "- results, each with title, URL, and one-line snippet\n"
    )
    return _cursor_agent_request(prompt)


def _fetch_via_cursor_cli(url: str) -> str:
    prompt = (
        "[ATLAS web_fetch]\n"
        "Use Cursor's web fetch/search capability only. Do not inspect or edit local files.\n"
        f"URL: {url}\n\n"
        "Return concise Markdown with:\n"
        "- engine: cursor-cli\n"
        "- title/source URL if available\n"
        "- the main page content summary\n"
    )
    return _cursor_agent_request(prompt)


# ---------------------------------------------------------------------------
# Tool: web_search
# ---------------------------------------------------------------------------

def web_search(query: str, limit: int = 5, lang: str = "en", tbs: str = "", engine: str = "cursor-cli") -> str:
    """
    Search the web through Cursor CLI only.

    Args:
        query: Search query string
        limit: Maximum number of results (1-20, default: 5)
        lang:  Language code preference (default: 'en', use 'ko' for Korean)
        tbs:   Time filter — 'qdr:d' (day), 'qdr:w' (week),
               'qdr:m' (month), 'qdr:y' (year), '' (any time)
        engine: accepted for backward compatibility, ignored; Cursor CLI is forced.

    Returns:
        Cursor CLI's text answer.
    """
    query = str(query or "").strip()
    if not query:
        return "Error: query is required."
    limit = max(1, min(20, int(limit)))
    try:
        return _search_via_cursor_cli(query, limit=limit, lang=lang, tbs=tbs)
    except subprocess.TimeoutExpired:
        return f"web_search failed — cursor-agent timed out after {_get_cursor_timeout()}s"
    except Exception as exc:
        return f"web_search failed — cursor-cli: {exc}"


def websearch(query: str, limit: int = 5, lang: str = "en", tbs: str = "", engine: str = "cursor-cli") -> str:
    """Alias for ``web_search`` for models that emit websearch as one word."""
    return web_search(query=query, limit=limit, lang=lang, tbs=tbs, engine=engine)


# ---------------------------------------------------------------------------
# Tool: web_fetch
# ---------------------------------------------------------------------------

def web_fetch(url: str, formats: str = "markdown", wait_for: int = 3000, engine: str = "cursor-cli") -> str:
    """
    Fetch/summarize content from a specific URL through Cursor CLI only.

    Args:
        url:      URL to scrape
        formats:  Kept for backward compatibility; Cursor returns Markdown text.
        wait_for: Kept for backward compatibility; Cursor controls page loading.
        engine:   accepted for backward compatibility, ignored; Cursor CLI is forced.

    Returns:
        Cursor CLI's text answer.
    """
    url = str(url or "").strip()
    if not url:
        return "Error: url is required."
    try:
        return _fetch_via_cursor_cli(url)
    except subprocess.TimeoutExpired:
        return f"web_fetch failed — cursor-agent timed out after {_get_cursor_timeout()}s"
    except Exception as exc:
        return f"web_fetch failed — cursor-cli: {exc}"


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
    "websearch":   websearch,
    "web_fetch":   web_fetch,
    "web_extract": web_extract,
}
