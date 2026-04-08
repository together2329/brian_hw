"""Naver Finance research report list crawler.

Crawls the company research report listing pages at:
    https://finance.naver.com/research/company_list.naver

Supports filtering by:
  - Stock code  (searchType=itemCode, itemCode=005930)
  - Keyword     (searchType=keyword, keyword=삼성전자)
  - Broker      (brokerCode=...)
  - Date range  (writeFromDate, writeToDate)
"""
from __future__ import annotations

import re
import time
from typing import List, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .models import ReportInfo

# ── Constants ──────────────────────────────────────────────────────────────
BASE_URL = "https://finance.naver.com/research/company_list.naver"
DETAIL_URL = "https://finance.naver.com/research/company_read.naver"
ITEM_URL = "https://finance.naver.com/item/main.naver"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Referer": "https://finance.naver.com/",
}
ENCODING = "euc-kr"
REQUEST_DELAY = 0.3  # seconds between page requests (polite crawling)


class NaverReportCrawler:
    """Crawls Naver Finance research report listings."""

    def __init__(self, delay: float = REQUEST_DELAY):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.delay = delay

    # ── Public API ─────────────────────────────────────────────────────────

    def fetch_reports(
        self,
        stock_code: Optional[str] = None,
        keyword: Optional[str] = None,
        broker_code: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        max_pages: int = 1,
    ) -> List[ReportInfo]:
        """Fetch research report listings matching the given filters.

        Parameters
        ----------
        stock_code : str, optional
            6-digit stock code, e.g. ``"005930"`` for Samsung Electronics.
        keyword : str, optional
            Company name keyword (used when stock_code is not given).
        broker_code : str, optional
            Broker code filter (Naver internal code).
        date_from : str, optional
            Start date ``"YYYYMMDD"``.
        date_to : str, optional
            End date ``"YYYYMMDD"``.
        max_pages : int
            Maximum number of listing pages to crawl (default 1 = latest).

        Returns
        -------
        list[ReportInfo]
        """
        all_reports: List[ReportInfo] = []

        params = self._build_params(
            stock_code=stock_code,
            keyword=keyword,
            broker_code=broker_code,
            date_from=date_from,
            date_to=date_to,
        )

        for page in range(1, max_pages + 1):
            params["page"] = page
            reports = self._fetch_page(params)
            if not reports:
                break
            all_reports.extend(reports)
            if page < max_pages:
                time.sleep(self.delay)

        return all_reports

    def fetch_latest(self, stock_code: str, count: int = 5) -> List[ReportInfo]:
        """Convenience: fetch the *count* most recent reports for a stock code."""
        reports = self.fetch_reports(stock_code=stock_code, max_pages=1)
        return reports[:count]

    # ── Internal ───────────────────────────────────────────────────────────

    @staticmethod
    def _build_params(
        stock_code: Optional[str] = None,
        keyword: Optional[str] = None,
        broker_code: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> dict:
        params: dict = {}

        if stock_code:
            params["searchType"] = "itemCode"
            params["itemCode"] = stock_code
        elif keyword:
            params["searchType"] = "keyword"
            params["keyword"] = keyword

        if broker_code:
            params["brokerCode"] = broker_code
        if date_from:
            params["writeFromDate"] = date_from
        if date_to:
            params["writeToDate"] = date_to

        return params

    def _fetch_page(self, params: dict) -> List[ReportInfo]:
        """Fetch and parse a single listing page."""
        resp = self.session.get(BASE_URL, params=params, timeout=15)
        resp.encoding = ENCODING
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        return self._parse_listing(soup)

    def _parse_listing(self, soup: BeautifulSoup) -> List[ReportInfo]:
        """Parse the HTML table of report listings into ReportInfo objects."""
        reports: List[ReportInfo] = []

        # The report table is the second <table> with class "type_1" or
        # the table containing the report rows.
        table = soup.find("table", class_="type_1")
        if not table:
            # Fallback: find table with report links
            table = soup.find("table")

        if not table:
            return reports

        rows = table.find_all("tr")
        for row in rows:
            report = self._parse_row(row)
            if report:
                reports.append(report)

        return reports

    def _parse_row(self, row) -> Optional[ReportInfo]:
        """Parse a single <tr> into a ReportInfo, or None if not a report row."""
        tds = row.find_all("td")
        if len(tds) < 5:
            return None

        # ── Column 0: Stock name + link ──
        stock_link = tds[0].find("a")
        if not stock_link:
            return None
        stock_name = stock_link.get_text(strip=True)
        stock_href = stock_link.get("href", "")
        stock_code = self._extract_code(stock_href)

        # ── Column 1: Report title + detail link ──
        title_link = tds[1].find("a")
        if not title_link:
            return None
        title = title_link.get_text(strip=True)
        detail_href = title_link.get("href", "")
        detail_url = urljoin(BASE_URL, detail_href) if detail_href else None

        # ── Column 2: Broker name ──
        broker = tds[2].get_text(strip=True)

        # ── Column 3: PDF download link ──
        pdf_a = tds[3].find("a")
        pdf_url = ""
        if pdf_a and pdf_a.get("href"):
            pdf_url = pdf_a["href"]
            if not pdf_url.startswith("http"):
                pdf_url = urljoin(BASE_URL, pdf_url)

        # ── Column 4: Date ──
        date_text = tds[4].get_text(strip=True)

        # ── Column 5 (optional): Read count ──
        read_count = 0
        if len(tds) >= 6:
            rc_text = tds[5].get_text(strip=True).replace(",", "")
            if rc_text.isdigit():
                read_count = int(rc_text)

        if not pdf_url:
            return None

        return ReportInfo(
            stock_name=stock_name,
            stock_code=stock_code,
            title=title,
            broker=broker,
            pdf_url=pdf_url,
            report_date=date_text,
            read_count=read_count,
            detail_url=detail_url,
        )

    @staticmethod
    def _extract_code(href: str) -> str:
        """Extract stock code from a Naver Finance item URL.

        e.g. ``/item/main.naver?code=005930`` → ``"005930"``
        """
        m = re.search(r"code=(\d{6})", href)
        return m.group(1) if m else ""
