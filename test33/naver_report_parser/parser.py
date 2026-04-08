"""PDF download and text extraction for Naver Finance research reports.

Downloads PDFs from stock.pstatic.net and extracts structured data using
pdfplumber: text, tables, investment opinions, target prices, financials.
"""
from __future__ import annotations

import io
import re
from typing import List, Optional

import pdfplumber
import requests
from bs4 import BeautifulSoup

from .models import ParsedReport, ReportInfo

# ── Constants ──────────────────────────────────────────────────────────────
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Referer": "https://finance.naver.com/",
}
PDF_TIMEOUT = 30  # seconds


class ReportParser:
    """Downloads and parses Naver Finance research report PDFs."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    # ── Public API ─────────────────────────────────────────────────────────

    def parse(self, report: ReportInfo) -> ParsedReport:
        """Download and parse a research report PDF.

        Parameters
        ----------
        report : ReportInfo
            A report listing object (from ``NaverReportCrawler``).

        Returns
        -------
        ParsedReport
            Structured extraction result.
        """
        pdf_bytes = self._download_pdf(report.pdf_url)
        return self.parse_bytes(pdf_bytes, report=report)

    def parse_bytes(
        self, pdf_bytes: bytes, report: Optional[ReportInfo] = None
    ) -> ParsedReport:
        """Parse a PDF from raw bytes.

        Parameters
        ----------
        pdf_bytes : bytes
            Raw PDF file content.
        report : ReportInfo, optional
            Pre-existing metadata to pre-fill.

        Returns
        -------
        ParsedReport
        """
        parsed = ParsedReport()
        if report:
            parsed.stock_name = report.stock_name
            parsed.stock_code = report.stock_code
            parsed.title = report.title
            parsed.broker = report.broker
            parsed.report_date = report.report_date

        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            pages_text: List[str] = []
            all_tables: list = []

            for page in pdf.pages:
                # Extract text
                text = page.extract_text() or ""
                pages_text.append(text)

                # Extract tables
                tables = page.extract_tables()
                for tbl in tables:
                    all_tables.append(tbl)

            full_text = "\n\n".join(pages_text)
            parsed.full_text = full_text
            parsed.tables = all_tables

            # Parse structured fields from text
            if pages_text:
                self._extract_metadata(parsed, pages_text)
                self._extract_investment_opinion(parsed, pages_text, all_tables)
                self._extract_financials(parsed, pages_text, all_tables)

        return parsed

    def parse_url(self, pdf_url: str) -> ParsedReport:
        """Download and parse a PDF from a direct URL."""
        pdf_bytes = self._download_pdf(pdf_url)
        return self.parse_bytes(pdf_bytes)

    # ── PDF Download ───────────────────────────────────────────────────────

    def _download_pdf(self, url: str) -> bytes:
        """Download a PDF file and return its raw bytes."""
        resp = self.session.get(url, timeout=PDF_TIMEOUT)
        resp.raise_for_status()
        return resp.content

    # ── Metadata Extraction ────────────────────────────────────────────────

    def _extract_metadata(self, parsed: ParsedReport, pages_text: List[str]) -> None:
        """Extract stock name, code, title, date, analyst from page 1."""
        page1 = pages_text[0] if pages_text else ""
        if not page1:
            return

        lines = page1.split("\n")

        # ── Date: "2026년 4월 8일" or "2026/04/08" or "2026.04.07" ──
        for line in lines:
            stripped = line.strip()
            m = re.match(r"(\d{4})\s*년\s*(\d{1,2})\s*월\s*(\d{1,2})\s*일", stripped)
            if m:
                if not parsed.report_date:
                    parsed.report_date = f"{m.group(1)}.{m.group(2).zfill(2)}.{m.group(3).zfill(2)}"
                break
            # "2026/04/08" or "2026.04.07"
            m = re.match(r"(\d{4})[/.](\d{1,2})[/.](\d{1,2})", stripped)
            if m:
                if not parsed.report_date:
                    parsed.report_date = f"{m.group(1)}.{m.group(2).zfill(2)}.{m.group(3).zfill(2)}"
                break

        # ── Analyst: various patterns ──
        # "▶ Analyst 박준영" / "이수림 반도체" / "최보영 연구위원"
        if not parsed.analyst:
            # Pattern: "▶ Analyst 이름" or "Analyst 이름"
            m = re.search(r"(?:▶\s*)?[Aa]nalyst\s+(\S+)", page1)
            if m:
                parsed.analyst = m.group(1)
            else:
                # Pattern: "이름 연구위원" or "이름 애널리스트"
                m = re.search(r"^(\S{2,4})\s+(?:연구위원|애널리스트|수석연구원|연구원)", page1, re.MULTILINE)
                if m:
                    parsed.analyst = m.group(1)
                else:
                    # Pattern: "이름 부서명" with email (DS투자증권 style)
                    m = re.search(r"(\S{2,4})\s+\S+\s*\n.*?[\w.-]+@[\w.-]+", page1)
                    if m:
                        parsed.analyst = m.group(1)

        # ── Stock code from "(005930)" or "(066570)" pattern ──
        if not parsed.stock_code:
            m = re.search(r"\((\d{6})\)", page1)
            if m:
                parsed.stock_code = m.group(1)

        # ── Stock name: various patterns ──
        if not parsed.stock_name:
            # Pattern 1: line after "기업분석" / "산업분석" etc.
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped in ("기업분석", "산업분석", "기업분석(report)", "기업실적"):
                    if i + 1 < len(lines):
                        parsed.stock_name = lines[i + 1].strip()
                    break

            # Pattern 2: "삼성전자(005930)" in text
            if not parsed.stock_name:
                m = re.search(r"([가-힣A-Z]+(?:전자|증권|건설|화학|제약|바이오|에너지|시스템|머티리얼|디스플레이|하이닉스|자동차|중공업|전기|금융|생명|카드|물산|로템|에어|航空航天))\s*\(\d{6}\)", page1)
                if m:
                    parsed.stock_name = m.group(1)

            # Pattern 3: standalone line with known stock name (before stock code)
            if not parsed.stock_name:
                m = re.search(r"^([가-힣]{2,10})\s*\n\s*\(?(\d{6})\)?", page1, re.MULTILINE)
                if m:
                    parsed.stock_name = m.group(1)

        # ── Title: various patterns ──
        if not parsed.title:
            # Pattern 1: after stock code line
            for i, line in enumerate(lines):
                if re.search(r"\(\d{6}\)", line):
                    if i + 1 < len(lines):
                        candidate = lines[i + 1].strip()
                        if candidate and "Analyst" not in candidate and "▶" not in candidate:
                            parsed.title = candidate
                    break

            # Pattern 2: "삼성전자(066570) TITLE" on same line
            if not parsed.title:
                m = re.search(r"\(\d{6}\)\s*(.+?)(?:\n|$)", page1)
                if m:
                    candidate = m.group(1).strip()
                    if candidate and len(candidate) > 5:
                        parsed.title = candidate

        # ── Broker: "[증권사명리서치]" on page 2+ ──
        if not parsed.broker:
            for pt in pages_text[1:3]:
                m = re.search(r"\[(\S+리서치)\]", pt)
                if m:
                    parsed.broker = m.group(1)
                    break

    # ── Investment Opinion Extraction ──────────────────────────────────────

    def _extract_investment_opinion(
        self,
        parsed: ParsedReport,
        pages_text: List[str],
        tables: list,
    ) -> None:
        """Extract investment opinion, target price, current price, upside."""
        page1 = pages_text[0] if pages_text else ""

        # ── Investment opinion from page 1 text ──
        # Common patterns: "Buy", "Sell", "Hold", "매수", "매도", "중립"
        opinion_patterns = [
            (r"\b(Buy)\b", "Buy"),
            (r"\b(Sell)\b", "Sell"),
            (r"\b(Hold)\b", "Hold"),
            (r"\b(OutPerform)\b", "OutPerform"),
            (r"\b(UnderPerform)\b", "UnderPerform"),
            (r"\b(MarketPerform)\b", "MarketPerform"),
            (r"매수", "매수"),
            (r"매도", "매도"),
            (r"중립", "중립"),
        ]
        for pattern, label in opinion_patterns:
            if re.search(pattern, page1):
                parsed.investment_opinion = label
                break

        # ── Target price ──
        m = re.search(r"목표주가[^:]*:?\s*([\d,]+)\s*원", page1)
        if m:
            parsed.target_price = int(m.group(1).replace(",", ""))

        # ── Current price ──
        m = re.search(r"현재\s*주가[^)]*\)?\s*([\d,]+)\s*원", page1)
        if m:
            parsed.current_price = int(m.group(1).replace(",", ""))

        # ── Upside ──
        m = re.search(r"상승여력\s*[▲▲]?\s*([\d.]+)\s*%", page1)
        if m:
            parsed.upside = float(m.group(1))

        # ── Fallback: extract from investment opinion table ──
        for tbl in tables:
            if not tbl or len(tbl) < 2:
                continue
            flat = " ".join(str(c) for row in tbl for c in (row or []))
            if "목표주가" in flat and not parsed.target_price:
                m = re.search(r"([\d,]+)\s*원", flat)
                if m:
                    parsed.target_price = int(m.group(1).replace(",", ""))

    # ── Financial Data Extraction ──────────────────────────────────────────

    def _extract_financials(
        self,
        parsed: ParsedReport,
        pages_text: List[str],
        tables: list,
    ) -> None:
        """Extract revenue, operating income, net income, EPS, PER, PBR, ROE
        from financial tables in the report."""
        full_text = "\n".join(pages_text)

        # ── Try to find financial table with header row containing key fields ──
        for tbl in tables:
            if not tbl or len(tbl) < 2:
                continue
            header = [str(c).strip() if c else "" for c in tbl[0]]

            # Look for income-statement style tables
            col_index = self._find_estimate_col(header)
            if col_index is None:
                continue

            for row in tbl[1:]:
                cells = [str(c).strip() if c else "" for c in row]
                label = cells[0] if cells else ""

                if not label:
                    continue

                val = self._safe_int(cells[col_index]) if col_index < len(cells) else None

                if "매출액" in label and "매출총" not in label:
                    if parsed.revenue is None and val is not None:
                        parsed.revenue = val
                elif "영업이익" in label:
                    if parsed.op_income is None and val is not None:
                        parsed.op_income = val
                elif "당기순이익" in label or "순이익" in label:
                    if parsed.net_income is None and val is not None:
                        parsed.net_income = val

        # ── Extract PER, PBR, ROE from text ──
        # Page 1 often has "P/B 2.0배, P/E 4.4배"
        m = re.search(r"P/E\s*([\d.]+)\s*배", full_text)
        if m:
            parsed.per = float(m.group(1))

        m = re.search(r"P/B\s*([\d.]+)\s*배", full_text)
        if m:
            parsed.pbr = float(m.group(1))

        # ROE from tables
        for tbl in tables:
            if not tbl or len(tbl) < 2:
                continue
            for row in tbl:
                cells = [str(c).strip() if c else "" for c in row]
                label = cells[0] if cells else ""
                if "ROE" in label.upper():
                    for cell in cells[1:]:
                        m = re.match(r"([\d.]+)", cell)
                        if m:
                            parsed.roe = float(m.group(1))
                            break
            if parsed.roe is not None:
                break

        # ── EPS from text/tables ──
        m = re.search(r"EPS\s*[\(（][^)）]*[\)）]?\s*([\d,]+)", full_text)
        if m:
            parsed.eps = float(m.group(1).replace(",", ""))

        # EPS from financial tables
        if parsed.eps is None:
            for tbl in tables:
                if not tbl or len(tbl) < 2:
                    continue
                for row in tbl:
                    cells = [str(c).strip() if c else "" for c in row]
                    label = cells[0] if cells else ""
                    if "EPS" in label.upper():
                        col = self._find_estimate_col(
                            [str(c).strip() if c else "" for c in tbl[0]]
                        )
                        if col and col < len(cells):
                            parsed.eps = self._safe_float(cells[col])
                        break

    # ── Utility Methods ────────────────────────────────────────────────────

    @staticmethod
    def _find_estimate_col(header: List[str]) -> Optional[int]:
        """Find the column index for the latest estimate year in a header row.

        Prefers columns like '2026E', '2026F', '2026P', or the rightmost
        year-like column.
        """
        best: Optional[int] = None
        best_year: int = 0

        for i, cell in enumerate(header):
            cell = cell.strip()
            # Prefer columns with E/F/P suffix (estimates)
            m = re.match(r"(20\d{2})[EFP]", cell)
            if m:
                year = int(m.group(1))
                if year > best_year:
                    best_year = year
                    best = i
            # Also consider plain year columns
            m = re.match(r"(20\d{2})$", cell)
            if m and best is None:
                year = int(m.group(1))
                if year > best_year:
                    best_year = year
                    best = i

        return best

    @staticmethod
    def _safe_int(text: str) -> Optional[int]:
        """Parse a numeric string with commas to int, return None on failure."""
        if not text:
            return None
        cleaned = text.replace(",", "").replace(" ", "").strip()
        # Remove trailing negative sign or parentheses for negative numbers
        cleaned = cleaned.replace("(", "-").replace(")", "")
        try:
            return int(float(cleaned))
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _safe_float(text: str) -> Optional[float]:
        """Parse a numeric string to float, return None on failure."""
        if not text:
            return None
        cleaned = text.replace(",", "").replace(" ", "").strip()
        cleaned = cleaned.replace("(", "-").replace(")", "")
        try:
            return float(cleaned)
        except (ValueError, TypeError):
            return None
