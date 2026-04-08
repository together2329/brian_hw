"""Data models for Naver Finance research reports."""
import json
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class ReportInfo:
    """Metadata for a single research report listing from Naver Finance."""
    stock_name: str
    stock_code: str
    title: str
    broker: str
    pdf_url: str
    report_date: str          # e.g. "26.04.08"
    read_count: int = 0
    detail_url: Optional[str] = None

    def __str__(self) -> str:
        return (
            f"[{self.report_date}] {self.stock_name}({self.stock_code}) | "
            f"{self.title} | {self.broker} | 조회 {self.read_count:,}"
        )


@dataclass
class ParsedReport:
    """Structured extraction result from a single research report PDF."""
    # ── Identification ──
    stock_name: str = ""
    stock_code: str = ""
    title: str = ""
    broker: str = ""
    report_date: str = ""
    analyst: str = ""

    # ── Investment Opinion ──
    investment_opinion: str = ""       # e.g. "Buy", "매수", "Hold"
    target_price: Optional[int] = None  # e.g. 300000
    current_price: Optional[int] = None
    upside: Optional[float] = None     # e.g. 52.7 (%)

    # ── Financial Highlights ──
    revenue: Optional[int] = None      # 매출액 (억원)
    op_income: Optional[int] = None    # 영업이익 (억원)
    net_income: Optional[int] = None   # 순이익 (억원)
    eps: Optional[float] = None
    per: Optional[float] = None
    pbr: Optional[float] = None
    roe: Optional[float] = None

    # ── Raw Content ──
    summary_text: str = ""
    full_text: str = ""
    tables: list = field(default_factory=list)

    def to_dict(self) -> dict:
        """Return a JSON-serializable dict of extracted fields (excludes raw text/tables)."""
        return {
            "stock_name": self.stock_name,
            "stock_code": self.stock_code,
            "title": self.title,
            "broker": self.broker,
            "report_date": self.report_date,
            "analyst": self.analyst,
            "investment_opinion": self.investment_opinion,
            "target_price": self.target_price,
            "current_price": self.current_price,
            "upside": self.upside,
            "revenue": self.revenue,
            "op_income": self.op_income,
            "net_income": self.net_income,
            "eps": self.eps,
            "per": self.per,
            "pbr": self.pbr,
            "roe": self.roe,
        }

    def to_json(self, indent: int = 2, ensure_ascii: bool = False) -> str:
        """Return a JSON string of extracted fields."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=ensure_ascii)

    def summary(self) -> str:
        lines = []
        lines.append(f"═══════════════════════════════════════════")
        lines.append(f"  {self.stock_name} ({self.stock_code}) 리포트 요약")
        lines.append(f"═══════════════════════════════════════════")
        lines.append(f"  증권사  : {self.broker}")
        lines.append(f"  날짜    : {self.report_date}")
        lines.append(f"  애널리스트: {self.analyst}")
        lines.append(f"───────────────────────────────────────────")
        lines.append(f"  투자의견: {self.investment_opinion}")
        if self.target_price is not None:
            tp = f"{self.target_price:,}원"
            cur = f" (현재가 {self.current_price:,}원)" if self.current_price else ""
            up = f" ▲{self.upside}%" if self.upside else ""
            lines.append(f"  목표주가: {tp}{cur}{up}")
        lines.append(f"───────────────────────────────────────────")
        if self.revenue is not None:
            lines.append(f"  매출액  : {self.revenue:,}억원")
        if self.op_income is not None:
            lines.append(f"  영업이익: {self.op_income:,}억원")
        if self.net_income is not None:
            lines.append(f"  순이익  : {self.net_income:,}억원")
        if self.eps is not None:
            lines.append(f"  EPS     : {self.eps:,.0f}원")
        if self.per is not None:
            lines.append(f"  PER     : {self.per}배")
        if self.pbr is not None:
            lines.append(f"  PBR     : {self.pbr}배")
        if self.roe is not None:
            lines.append(f"  ROE     : {self.roe}%")
        lines.append(f"───────────────────────────────────────────")
        if self.summary_text:
            # Show first 500 chars of summary
            text = self.summary_text[:500]
            if len(self.summary_text) > 500:
                text += "..."
            lines.append(f"  요약:\n  {text}")
        lines.append(f"═══════════════════════════════════════════")
        return "\n".join(lines)
