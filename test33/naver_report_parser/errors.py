"""Custom exceptions for Naver Finance research report parser.

Hierarchy::

    NaverReportError
    ├── CrawlError
    │   ├── NetworkError
    │   └── ParseError
    └── PDFError
        ├── PDFDownloadError
        └── PDFParseError
"""
from __future__ import annotations


class NaverReportError(Exception):
    """Base exception for all naver_report_parser errors."""

    def __init__(self, message: str = "", *, detail: str = ""):
        self.detail = detail
        super().__init__(message)


# ── Crawl Errors ───────────────────────────────────────────────────────────

class CrawlError(NaverReportError):
    """Error while crawling Naver Finance listing pages."""


class NetworkError(CrawlError):
    """Network-level error (connection, timeout, DNS, HTTP status).

    Attributes
    ----------
    status_code : int or None
        HTTP status code if applicable.
    url : str
        The URL that was being requested.
    """

    def __init__(
        self,
        message: str = "",
        *,
        url: str = "",
        status_code: int | None = None,
        detail: str = "",
    ):
        self.url = url
        self.status_code = status_code
        super().__init__(message, detail=detail)


class ParseError(CrawlError):
    """Error parsing HTML listing page."""


# ── PDF Errors ─────────────────────────────────────────────────────────────

class PDFError(NaverReportError):
    """Error related to PDF processing."""


class PDFDownloadError(PDFError):
    """Error downloading a PDF file.

    Attributes
    ----------
    url : str
        The PDF URL that failed.
    """

    def __init__(self, message: str = "", *, url: str = "", detail: str = ""):
        self.url = url
        super().__init__(message, detail=detail)


class PDFParseError(PDFError):
    """Error parsing PDF content (corrupted, encrypted, empty, etc.).

    Attributes
    ----------
    pdf_url : str or None
        URL or filename of the PDF.
    page : int or None
        Page number where parsing failed, if known.
    """

    def __init__(
        self,
        message: str = "",
        *,
        pdf_url: str | None = None,
        page: int | None = None,
        detail: str = "",
    ):
        self.pdf_url = pdf_url
        self.page = page
        super().__init__(message, detail=detail)
