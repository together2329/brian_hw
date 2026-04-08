"""SEC EDGAR API client for US public company financial data.

Fetches company filings, financial statements (XBRL), and key metrics
from the SEC EDGAR system. Targets optical/semiconductor supply chain:
Micron (MU), Lumentum (LITE), Coherent (COHR), Corning (GLW), Fabrinet (FN).

API Reference:
    - Company ticker lookup: https://www.sec.gov/files/company_tickers.json
    - Submissions:           https://data.sec.gov/submissions/CIK{CIK}.json
    - XBRL Company Facts:    https://data.sec.gov/api/xbrl/companyfacts/CIK{CIK}.json

SEC requires User-Agent header with contact info for bulk access.
"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin

import requests

from .errors import NetworkError

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────
SEC_HEADERS = {
    "User-Agent": "NaverReportParser/1.0 research@example.com",
    "Accept": "application/json",
}
SEC_BASE = "https://data.sec.gov"
SUBMISSIONS_URL = SEC_BASE + "/submissions/CIK{cik}.json"
COMPANY_FACTS_URL = SEC_BASE + "/api/xbrl/companyfacts/CIK{cik}.json"
TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"

MAX_RETRIES = 3
RETRY_BACKOFF = 1.0
REQUEST_DELAY = 0.15  # SEC rate limit: 10 req/s

# ── Pre-configured target stocks ──────────────────────────────────────────
TARGET_STOCKS = {
    "MU":   {"cik": "0000723125", "name": "Micron Technology, Inc.",       "sic": "3674"},
    "LITE": {"cik": "0001633978", "name": "Lumentum Holdings Inc.",        "sic": "3661"},
    "COHR": {"cik": "0000820318", "name": "Coherent Corp.",               "sic": "3661"},
    "GLW":  {"cik": "0000024741", "name": "Corning Inc.",                  "sic": "3229"},
    "FN":   {"cik": "0001408710", "name": "Fabrinet",                      "sic": "3674"},
}

# XBRL fact tags → friendly names
REVENUE_TAGS = [
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "Revenues",
    "Revenue",
    "SalesRevenueNet",
    "SalesRevenueServicesNet",
]
NET_INCOME_TAGS = [
    "NetIncomeLoss",
    "ProfitLoss",
]
OPERATING_INCOME_TAGS = [
    "OperatingIncomeLoss",
]
GROSS_PROFIT_TAGS = [
    "GrossProfit",
]
RD_EXPENSE_TAGS = [
    "ResearchAndDevelopmentExpense",
]
EPS_DILUTED_TAGS = [
    "EarningsPerShareDiluted",
]
EPS_BASIC_TAGS = [
    "EarningsPerShareBasic",
]
TOTAL_ASSETS_TAGS = [
    "Assets",
]
STOCKHOLDERS_EQUITY_TAGS = [
    "StockholdersEquity",
]
SHARES_OUTSTANDING_TAGS = [
    "EntityCommonStockSharesOutstanding",
    "CommonStockSharesOutstanding",
    "WeightedAverageNumberOfDilutedSharesOutstanding",
]
CASH_TAGS = [
    "CashAndCashEquivalentsAtCarryingValue",
    "CashCashEquivalentsAndShortTermInvestments",
]

ALL_METRIC_TAGS: Dict[str, List[str]] = {
    "revenue": REVENUE_TAGS,
    "gross_profit": GROSS_PROFIT_TAGS,
    "operating_income": OPERATING_INCOME_TAGS,
    "net_income": NET_INCOME_TAGS,
    "rd_expense": RD_EXPENSE_TAGS,
    "eps_diluted": EPS_DILUTED_TAGS,
    "eps_basic": EPS_BASIC_TAGS,
    "total_assets": TOTAL_ASSETS_TAGS,
    "stockholders_equity": STOCKHOLDERS_EQUITY_TAGS,
    "shares_outstanding": SHARES_OUTSTANDING_TAGS,
    "cash": CASH_TAGS,
}


# ── Data Models ───────────────────────────────────────────────────────────

@dataclass
class CompanyInfo:
    """Basic company information from SEC EDGAR."""
    ticker: str
    cik: str
    name: str = ""
    sic: str = ""
    sic_description: str = ""
    exchanges: List[str] = field(default_factory=list)
    fiscal_year_end: str = ""
    category: str = ""
    state: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class FilingInfo:
    """Information about a single SEC filing."""
    accession_number: str
    form: str
    filing_date: str
    primary_document: str = ""
    description: str = ""
    size: int = 0

    @property
    def url(self) -> str:
        """URL to the filing directory on EDGAR."""
        accn = self.accession_number.replace("-", "")
        return f"https://www.sec.gov/Archives/edgar/data/{accn[:10]}/{self.accession_number}/"

    @property
    def document_url(self) -> str:
        """Direct URL to the primary document."""
        return self.url + self.primary_document if self.primary_document else self.url

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class FinancialPeriod:
    """Financial data for a single fiscal period."""
    fiscal_year: int
    fiscal_period: str        # "FY", "Q1", "Q2", "Q3", "Q4"
    form: str                 # "10-K" or "10-Q"
    end_date: str             # e.g. "2025-08-28"
    filed_date: str = ""      # e.g. "2025-10-15"

    # ── Income Statement ──
    revenue: Optional[float] = None
    gross_profit: Optional[float] = None
    operating_income: Optional[float] = None
    net_income: Optional[float] = None
    rd_expense: Optional[float] = None
    eps_basic: Optional[float] = None
    eps_diluted: Optional[float] = None

    # ── Balance Sheet ──
    total_assets: Optional[float] = None
    stockholders_equity: Optional[float] = None
    cash: Optional[float] = None

    # ── Per-Share / Shares ──
    shares_outstanding: Optional[float] = None

    # ── Computed Ratios ──
    gross_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    net_margin: Optional[float] = None
    roe: Optional[float] = None

    def compute_ratios(self) -> None:
        """Compute derived financial ratios from raw values."""
        if self.revenue and self.revenue != 0:
            if self.gross_profit is not None:
                self.gross_margin = round(self.gross_profit / self.revenue * 100, 2)
            if self.operating_income is not None:
                self.operating_margin = round(self.operating_income / self.revenue * 100, 2)
            if self.net_income is not None:
                self.net_margin = round(self.net_income / self.revenue * 100, 2)
        if self.stockholders_equity and self.stockholders_equity != 0 and self.net_income is not None:
            self.roe = round(self.net_income / self.stockholders_equity * 100, 2)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class CompanyFinancials:
    """Comprehensive financial data for a company."""
    company: CompanyInfo
    latest_annual: Optional[FinancialPeriod] = None
    latest_quarterly: Optional[FinancialPeriod] = None
    annual_history: List[FinancialPeriod] = field(default_factory=list)
    quarterly_history: List[FinancialPeriod] = field(default_factory=list)
    recent_filings: List[FilingInfo] = field(default_factory=list)

    def summary(self) -> str:
        """Return a human-readable summary string."""
        lines = []
        c = self.company
        lines.append("=" * 60)
        lines.append(f"  {c.name} ({c.ticker}) — SEC EDGAR Financial Summary")
        lines.append(f"  CIK: {c.cik}  |  SIC: {c.sic_description or c.sic}")
        lines.append(f"  Filer Category: {c.category}")
        lines.append("=" * 60)

        if self.latest_annual:
            a = self.latest_annual
            lines.append(f"\n  📊 Latest Annual (FY{a.fiscal_year}, 10-K)")
            lines.append(f"  {'─' * 50}")
            self._format_period(lines, a, "  ")

        if self.latest_quarterly:
            q = self.latest_quarterly
            lines.append(f"\n  📊 Latest Quarterly (FY{q.fiscal_year} {q.fiscal_period}, 10-Q)")
            lines.append(f"  {'─' * 50}")
            self._format_period(lines, q, "  ")

        if self.annual_history and len(self.annual_history) > 1:
            lines.append(f"\n  📈 Annual Revenue Trend")
            lines.append(f"  {'─' * 50}")
            for p in self.annual_history:
                rev = f"${p.revenue / 1e9:.2f}B" if p.revenue else "N/A"
                ni = f"${p.net_income / 1e9:.2f}B" if p.net_income is not None else "N/A"
                margin = f"{p.net_margin}%" if p.net_margin is not None else "N/A"
                lines.append(f"  FY{p.fiscal_year}: Rev={rev:>10s}  NI={ni:>10s}  Margin={margin:>8s}")

        if self.recent_filings:
            lines.append(f"\n  📋 Recent Filings (top 10)")
            lines.append(f"  {'─' * 50}")
            for f in self.recent_filings[:10]:
                lines.append(f"  [{f.filing_date}] {f.form:6s} {f.description[:40]}")

        lines.append("=" * 60)
        return "\n".join(lines)

    @staticmethod
    def _format_period(lines: list, p: FinancialPeriod, indent: str = "") -> None:
        """Add formatted period data to lines."""
        def fmt_usd(val: Optional[float], unit: str = "B") -> str:
            if val is None:
                return "N/A"
            if unit == "B":
                return f"${val / 1e9:.2f}B"
            return f"${val:,.0f}"

        lines.append(f"{indent}Revenue:       {fmt_usd(p.revenue)}")
        lines.append(f"{indent}Gross Profit:  {fmt_usd(p.gross_profit)}  (Margin: {p.gross_margin or 'N/A'}%)")
        lines.append(f"{indent}Operating Inc: {fmt_usd(p.operating_income)}  (Margin: {p.operating_margin or 'N/A'}%)")
        lines.append(f"{indent}Net Income:    {fmt_usd(p.net_income)}  (Margin: {p.net_margin or 'N/A'}%)")
        lines.append(f"{indent}R&D Expense:   {fmt_usd(p.rd_expense)}")
        if p.eps_diluted is not None:
            lines.append(f"{indent}EPS (Diluted): ${p.eps_diluted:.2f}")
        if p.eps_basic is not None:
            lines.append(f"{indent}EPS (Basic):   ${p.eps_basic:.2f}")
        lines.append(f"{indent}Total Assets:  {fmt_usd(p.total_assets)}")
        lines.append(f"{indent}Equity:        {fmt_usd(p.stockholders_equity)}")
        if p.roe is not None:
            lines.append(f"{indent}ROE:           {p.roe}%")
        if p.shares_outstanding is not None:
            lines.append(f"{indent}Shares Out:    {p.shares_outstanding:,.0f}")

    def to_dict(self) -> dict:
        return {
            "company": self.company.to_dict(),
            "latest_annual": self.latest_annual.to_dict() if self.latest_annual else None,
            "latest_quarterly": self.latest_quarterly.to_dict() if self.latest_quarterly else None,
            "annual_history": [p.to_dict() for p in self.annual_history],
            "quarterly_history": [p.to_dict() for p in self.quarterly_history],
            "recent_filings": [f.to_dict() for f in self.recent_filings],
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


# ── SEC EDGAR Client ──────────────────────────────────────────────────────

class SECEdgarClient:
    """Client for fetching US public company data from SEC EDGAR APIs.

    Usage::

        client = SECEdgarClient()
        # Pre-configured stock
        data = client.get_financials("MU")
        print(data.summary())

        # Any ticker (looked up via SEC ticker database)
        data = client.get_financials("AAPL")

        # Compare multiple stocks
        results = client.compare(["MU", "LITE", "COHR", "GLW", "FN"])
    """

    def __init__(self, delay: float = REQUEST_DELAY):
        self.session = requests.Session()
        self.session.headers.update(SEC_HEADERS)
        self.delay = delay
        self._ticker_cache: Optional[Dict[str, dict]] = None
        self._last_request_time: float = 0.0

    # ── Public API ─────────────────────────────────────────────────────

    def lookup_ticker(self, ticker: str) -> CompanyInfo:
        """Look up a ticker symbol to get company info and CIK number.

        Parameters
        ----------
        ticker : str
            Stock ticker symbol, e.g. ``"MU"``.

        Returns
        -------
        CompanyInfo

        Raises
        ------
        ValueError
            Ticker not found in SEC database.
        NetworkError
            API request failed.
        """
        ticker = ticker.upper().strip()

        # Check pre-configured stocks first
        if ticker in TARGET_STOCKS:
            info = TARGET_STOCKS[ticker]
            # Enrich from submissions API
            try:
                sub = self._fetch_submissions(info["cik"])
                return self._parse_company_info(ticker, info["cik"], sub)
            except Exception:
                return CompanyInfo(
                    ticker=ticker,
                    cik=info["cik"],
                    name=info["name"],
                    sic=info["sic"],
                )

        # Look up from SEC ticker database
        ticker_map = self._load_ticker_map()
        entry = ticker_map.get(ticker)
        if not entry:
            raise ValueError(
                f"Ticker '{ticker}' not found in SEC EDGAR database. "
                f"Check https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&company={ticker}"
            )

        cik = str(entry["cik_str"]).zfill(10)
        sub = self._fetch_submissions(cik)
        return self._parse_company_info(ticker, cik, sub)

    def get_filings(
        self,
        ticker: str,
        form: Optional[str] = None,
        count: int = 20,
    ) -> List[FilingInfo]:
        """Get recent filings for a company.

        Parameters
        ----------
        ticker : str
            Stock ticker symbol.
        form : str, optional
            Filter by form type (e.g. ``"10-K"``, ``"10-Q"``, ``"8-K"``).
        count : int
            Maximum number of filings to return.

        Returns
        -------
        list[FilingInfo]
        """
        cik = self._resolve_cik(ticker)
        sub = self._fetch_submissions(cik)
        recent = sub.get("filings", {}).get("recent", {})

        filings: List[FilingInfo] = []
        forms = recent.get("form", [])
        dates = recent.get("filingDate", [])
        accns = recent.get("accessionNumber", [])
        docs = recent.get("primaryDocument", [])
        descs = recent.get("primaryDocDescription", [])
        sizes = recent.get("size", [])

        for i in range(min(len(forms), 1000)):
            f = forms[i]
            if form and f != form:
                continue

            filing = FilingInfo(
                accession_number=accns[i] if i < len(accns) else "",
                form=f,
                filing_date=dates[i] if i < len(dates) else "",
                primary_document=docs[i] if i < len(docs) else "",
                description=descs[i] if i < len(descs) else "",
                size=sizes[i] if i < len(sizes) else 0,
            )
            filings.append(filing)
            if len(filings) >= count:
                break

        return filings

    def get_financials(
        self,
        ticker: str,
        years: int = 4,
    ) -> CompanyFinancials:
        """Get comprehensive financial data for a company.

        Fetches company info, XBRL financial facts (annual + quarterly),
        and recent filings.

        Parameters
        ----------
        ticker : str
            Stock ticker symbol.
        years : int
            Number of historical annual periods to include (default 4).

        Returns
        -------
        CompanyFinancials
        """
        # 1. Resolve company info
        cik = self._resolve_cik(ticker)
        company = self.lookup_ticker(ticker)

        # 2. Fetch XBRL facts
        self._rate_limit()
        facts = self._fetch_company_facts(cik)

        # 3. Parse annual periods
        annual_periods = self._extract_periods(facts, form="10-K", limit=years)
        for p in annual_periods:
            p.compute_ratios()
        annual_periods.sort(key=lambda x: x.fiscal_year)

        # 4. Parse quarterly periods (latest 8)
        quarterly_periods = self._extract_periods(facts, form="10-Q", limit=8)
        for p in quarterly_periods:
            p.compute_ratios()
        quarterly_periods.sort(key=lambda x: (x.fiscal_year, x.fiscal_period))

        # 5. Get recent filings
        filings = self.get_filings(ticker, count=15)

        # 6. Build result
        result = CompanyFinancials(
            company=company,
            latest_annual=annual_periods[-1] if annual_periods else None,
            latest_quarterly=quarterly_periods[-1] if quarterly_periods else None,
            annual_history=annual_periods,
            quarterly_history=quarterly_periods,
            recent_filings=filings,
        )

        return result

    def compare(self, tickers: List[str], years: int = 3) -> Dict[str, CompanyFinancials]:
        """Fetch and compare financials for multiple companies.

        Parameters
        ----------
        tickers : list[str]
            List of ticker symbols.
        years : int
            Number of historical annual periods.

        Returns
        -------
        dict[str, CompanyFinancials]
        """
        results: Dict[str, CompanyFinancials] = {}
        for ticker in tickers:
            logger.info("Fetching SEC EDGAR data for %s ...", ticker)
            try:
                results[ticker] = self.get_financials(ticker, years=years)
            except Exception as e:
                logger.error("Failed to fetch %s: %s", ticker, e)
        return results

    def format_comparison(self, results: Dict[str, CompanyFinancials]) -> str:
        """Format a comparison table of multiple companies.

        Parameters
        ----------
        results : dict[str, CompanyFinancials]
            Results from ``compare()``.

        Returns
        -------
        str
            Formatted comparison table.
        """
        lines = []
        lines.append("=" * 100)
        lines.append("  SEC EDGAR — Optical/Semiconductor Supply Chain Comparison")
        lines.append("=" * 100)

        # Header
        hdr_tickers = list(results.keys())
        hdr = f"  {'Metric':<25s}"
        for t in hdr_tickers:
            hdr += f" │ {t:>15s}"
        lines.append(hdr)
        lines.append("─" * len(hdr))

        # Collect latest annual data
        metrics = [
            ("Revenue", "revenue", "B"),
            ("Gross Profit", "gross_profit", "B"),
            ("Operating Income", "operating_income", "B"),
            ("Net Income", "net_income", "B"),
            ("R&D Expense", "rd_expense", "B"),
            ("EPS (Diluted)", "eps_diluted", "raw"),
            ("Total Assets", "total_assets", "B"),
            ("Equity", "stockholders_equity", "B"),
            ("", "", ""),
            ("Gross Margin", "gross_margin", "%"),
            ("Operating Margin", "operating_margin", "%"),
            ("Net Margin", "net_margin", "%"),
            ("ROE", "roe", "%"),
        ]

        for label, attr, unit in metrics:
            if not label:
                lines.append("─" * len(hdr))
                continue

            row = f"  {label:<25s}"
            for ticker in hdr_tickers:
                fin = results.get(ticker)
                if not fin or not fin.latest_annual:
                    row += f" │ {'N/A':>15s}"
                    continue

                val = getattr(fin.latest_annual, attr, None)
                if val is None:
                    formatted = "N/A"
                elif unit == "B":
                    formatted = f"${val / 1e9:.2f}B"
                elif unit == "%":
                    formatted = f"{val:.1f}%"
                else:
                    formatted = f"${val:.2f}"
                row += f" │ {formatted:>15s}"
            lines.append(row)

        # FY info
        fy_row = f"  {'Fiscal Year':<25s}"
        for ticker in hdr_tickers:
            fin = results.get(ticker)
            if fin and fin.latest_annual:
                fy_row += f" │ {'FY' + str(fin.latest_annual.fiscal_year):>15s}"
            else:
                fy_row += f" │ {'N/A':>15s}"
        lines.append("─" * len(hdr))
        lines.append(fy_row)

        # Q info
        q_row = f"  {'Latest Quarter':<25s}"
        for ticker in hdr_tickers:
            fin = results.get(ticker)
            if fin and fin.latest_quarterly:
                q = fin.latest_quarterly
                q_row += f" │ {f'FY{q.fiscal_year} {q.fiscal_period}':>15s}"
            else:
                q_row += f" │ {'N/A':>15s}"
        lines.append(q_row)

        lines.append("=" * 100)
        return "\n".join(lines)

    # ── Internal: API Calls ────────────────────────────────────────────

    def _rate_limit(self) -> None:
        """Ensure we don't exceed SEC rate limits (10 req/s)."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
        self._last_request_time = time.time()

    def _request_json(self, url: str) -> dict:
        """Make a GET request with retry and return parsed JSON."""
        last_exc: Optional[Exception] = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                self._rate_limit()
                resp = self.session.get(url, timeout=20)
                resp.raise_for_status()
                return resp.json()

            except requests.exceptions.ConnectionError as e:
                last_exc = e
                logger.warning("SEC API connection error (attempt %d/%d): %s", attempt, MAX_RETRIES, e)
            except requests.exceptions.Timeout as e:
                last_exc = e
                logger.warning("SEC API timeout (attempt %d/%d): %s", attempt, MAX_RETRIES, e)
            except requests.exceptions.HTTPError as e:
                status = e.response.status_code if e.response is not None else None
                if status and 400 <= status < 500 and status != 429:
                    raise NetworkError(
                        f"SEC API HTTP {status}: {e}",
                        url=url,
                        status_code=status,
                        detail=str(e),
                    ) from e
                last_exc = e
                logger.warning("SEC API HTTP %s (attempt %d/%d): %s", status, attempt, MAX_RETRIES, e)
            except requests.exceptions.RequestException as e:
                last_exc = e
                logger.warning("SEC API error (attempt %d/%d): %s", attempt, MAX_RETRIES, e)

            if attempt < MAX_RETRIES:
                wait = RETRY_BACKOFF * (2 ** (attempt - 1))
                logger.info("Retrying SEC API in %.1fs ...", wait)
                time.sleep(wait)

        raise NetworkError(
            f"SEC API request failed ({MAX_RETRIES} retries): {last_exc}",
            url=url,
            detail=str(last_exc),
        ) from last_exc

    def _fetch_submissions(self, cik: str) -> dict:
        """Fetch company submissions metadata."""
        url = SUBMISSIONS_URL.format(cik=cik)
        return self._request_json(url)

    def _fetch_company_facts(self, cik: str) -> dict:
        """Fetch XBRL company facts (all financial data)."""
        url = COMPANY_FACTS_URL.format(cik=cik)
        return self._request_json(url)

    def _load_ticker_map(self) -> Dict[str, dict]:
        """Load and cache the SEC ticker → CIK mapping."""
        if self._ticker_cache is not None:
            return self._ticker_cache

        data = self._request_json(TICKERS_URL)
        ticker_map: Dict[str, dict] = {}
        for entry in data.values():
            ticker_map[entry["ticker"].upper()] = entry
        self._ticker_cache = ticker_map
        return ticker_map

    def _resolve_cik(self, ticker: str) -> str:
        """Resolve a ticker to its CIK number (zero-padded to 10 digits)."""
        ticker = ticker.upper().strip()
        if ticker in TARGET_STOCKS:
            return TARGET_STOCKS[ticker]["cik"]
        entry = self._load_ticker_map().get(ticker)
        if not entry:
            raise ValueError(f"Ticker '{ticker}' not found in SEC EDGAR database.")
        return str(entry["cik_str"]).zfill(10)

    @staticmethod
    def _parse_company_info(ticker: str, cik: str, sub: dict) -> CompanyInfo:
        """Parse company info from submissions response."""
        return CompanyInfo(
            ticker=ticker,
            cik=cik,
            name=sub.get("name", ""),
            sic=sub.get("sic", ""),
            sic_description=sub.get("sicDescription", ""),
            exchanges=sub.get("exchanges", []),
            fiscal_year_end=sub.get("fiscalYearEnd", ""),
            category=sub.get("category", ""),
            state=sub.get("addresses", {}).get("business", {}).get("stateOrCountry", ""),
        )

    # ── Internal: XBRL Data Extraction ─────────────────────────────────

    def _extract_periods(
        self,
        facts: dict,
        form: str = "10-K",
        limit: int = 4,
    ) -> List[FinancialPeriod]:
        """Extract financial periods from XBRL company facts.

        The SEC XBRL API returns restated prior-year data alongside current-year
        data in each filing (e.g. FY2025 10-K contains end=2023, end=2024, AND
        end=2025 entries all with fy=2025). We use **end_date** as the unique
        period identifier and pick values from the most recent filing.

        Parameters
        ----------
        facts : dict
            XBRL company facts JSON.
        form : str
            "10-K" for annual, "10-Q" for quarterly.
        limit : int
            Maximum number of periods to return.

        Returns
        -------
        list[FinancialPeriod]
        """
        us_gaap = facts.get("facts", {}).get("us-gaap", {})
        dei = facts.get("facts", {}).get("dei", {})

        # Use end_date as the unique key.  For each (end_date, metric) keep
        # the value from the filing with the highest fy (most recent filing).
        # Structure: { end_date: { "end_date": str, "fy_highest": int, metrics... } }
        periods_by_end: Dict[str, dict] = {}

        def _merge_metric(v: dict, metric_name: str) -> None:
            """Merge a single XBRL value into periods_by_end."""
            end_date = v.get("end", "")
            if not end_date:
                return
            fy = v.get("fy", 0)
            fp = v.get("fp", "")

            if end_date not in periods_by_end:
                periods_by_end[end_date] = {
                    "end_date": end_date,
                    "fy_highest": fy,
                    "fiscal_period": fp,
                    "form": v.get("form", form),
                    "filed_date": v.get("filed", ""),
                }
            entry = periods_by_end[end_date]

            # Prefer data from the most recent filing (highest fy)
            if fy > entry["fy_highest"]:
                entry["fy_highest"] = fy
                entry["fiscal_period"] = fp
                entry["filed_date"] = v.get("filed", "")
                entry["form"] = v.get("form", form)

            # Set metric value — when multiple XBRL entries exist for the
            # same end_date (e.g. consolidated + segment breakdowns), keep
            # the value with the **largest absolute magnitude** because the
            # consolidated total is always the biggest.  Within the same fy,
            # prefer the larger value; across different fy values, prefer the
            # most recent filing's data.
            val = v.get("val")
            if val is not None:
                existing_fy = entry.get(f"_metric_fy_{metric_name}", 0)
                existing_val = entry.get(metric_name)
                should_set = False
                if metric_name not in entry or existing_val is None:
                    should_set = True
                elif fy > existing_fy:
                    # Newer filing — accept its value
                    should_set = True
                elif fy == existing_fy and abs(val) > abs(existing_val):
                    # Same filing, same end_date — keep larger absolute value
                    # (consolidated total > segment values)
                    should_set = True
                if should_set:
                    entry[metric_name] = val
                    entry[f"_metric_fy_{metric_name}"] = fy

        # For each metric, extract values for the requested form
        for metric_name, tags in ALL_METRIC_TAGS.items():
            values = self._find_xbrl_values(us_gaap, tags, form=form)
            for v in values:
                _merge_metric(v, metric_name)

        # Also get shares outstanding from DEI taxonomy
        shares_tags = ["EntityCommonStockSharesOutstanding"]
        shares_vals = self._find_xbrl_values(dei, shares_tags, form=form)
        for v in shares_vals:
            _merge_metric(v, "shares_outstanding")

        # Sort by end_date descending and pick the top `limit` periods with revenue
        sorted_ends = sorted(periods_by_end.keys(), reverse=True)

        periods: List[FinancialPeriod] = []
        for end_date in sorted_ends:
            data = periods_by_end[end_date]
            if data.get("revenue") is None:
                continue

            # Determine fiscal_year from the end_date (actual period end), not from
            # fy_highest which is the filing year and is the same for both current
            # and restated prior-year data in a single filing.
            end_date_str = data["end_date"]
            end_year = int(end_date_str[:4])
            fy = end_year
            # For companies with non-calendar fiscal years (e.g. MU ends in Aug),
            # the fiscal year label typically matches the calendar year of the end date.
            # The XBRL fp=FY entry's end_date tells us the true period.

            p = FinancialPeriod(
                fiscal_year=fy,
                fiscal_period=data.get("fiscal_period", "FY" if form == "10-K" else ""),
                form=data.get("form", form),
                end_date=data["end_date"],
                filed_date=data.get("filed_date", ""),
                revenue=data.get("revenue"),
                gross_profit=data.get("gross_profit"),
                operating_income=data.get("operating_income"),
                net_income=data.get("net_income"),
                rd_expense=data.get("rd_expense"),
                eps_basic=data.get("eps_basic"),
                eps_diluted=data.get("eps_diluted"),
                total_assets=data.get("total_assets"),
                stockholders_equity=data.get("stockholders_equity"),
                cash=data.get("cash"),
                shares_outstanding=data.get("shares_outstanding"),
            )
            p.compute_ratios()
            periods.append(p)
            if len(periods) >= limit:
                break

        return periods

    @staticmethod
    def _find_xbrl_values(
        taxonomy: dict,
        tags: List[str],
        form: str = "10-K",
    ) -> List[dict]:
        """Find XBRL values for a list of possible tags in a taxonomy.

        Aggregates form-filtered values from **all** matching tags, not
        just the first.  This is important because a company may report
        under different XBRL tags in different periods (e.g. one tag for
        older filings, another for recent ones).  The caller
        (``_extract_periods``) deduplicates by end_date and keeps the
        largest absolute value per metric.

        Falls back to unfiltered data only if NO tag has any form match.
        """
        # Pass 1 — collect form-filtered values from ALL tags
        all_filtered: List[dict] = []
        for tag in tags:
            if tag not in taxonomy:
                continue
            tag_data = taxonomy[tag]
            units = tag_data.get("units", {})
            for unit_key, values in units.items():
                filtered = [v for v in values if v.get("form") == form]
                all_filtered.extend(filtered)

        if all_filtered:
            return all_filtered

        # Pass 2 — fallback: first tag with any data (cross-form)
        for tag in tags:
            if tag not in taxonomy:
                continue
            tag_data = taxonomy[tag]
            units = tag_data.get("units", {})
            for unit_key, values in units.items():
                if values:
                    return values

        return []


# ── Convenience Functions ─────────────────────────────────────────────────

def fetch_stock(ticker: str, years: int = 4) -> CompanyFinancials:
    """Quick fetch for a single stock. Convenience wrapper.

    >>> data = fetch_stock("MU")
    >>> print(data.summary())
    """
    client = SECEdgarClient()
    return client.get_financials(ticker, years=years)


def fetch_comparison(
    tickers: Optional[List[str]] = None,
    years: int = 3,
) -> str:
    """Fetch and format a comparison of supply chain stocks.

    Default tickers: MU, LITE, COHR, GLW, FN

    >>> print(fetch_comparison())
    """
    if tickers is None:
        tickers = list(TARGET_STOCKS.keys())
    client = SECEdgarClient()
    results = client.compare(tickers, years=years)
    return client.format_comparison(results)
