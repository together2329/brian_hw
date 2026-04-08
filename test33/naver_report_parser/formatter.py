"""Output formatting for parsed research reports.

Supports three output formats:
  - table:  Rich console table (default)
  - json:   JSON array of structured fields
  - csv:    CSV with one row per report
"""
from __future__ import annotations

import csv
import io
import json
from typing import List

from .models import ParsedReport

# ── Table formatting ───────────────────────────────────────────────────────

def format_table(reports: List[ParsedReport], compact: bool = False) -> str:
    """Format reports as a text table.

    Parameters
    ----------
    reports : list[ParsedReport]
        Parsed report results.
    compact : bool
        If True, show only key fields in a single-row-per-report format.

    Returns
    -------
    str
        Formatted table string.
    """
    if not reports:
        return "📭 분석된 리포트가 없습니다."

    if compact:
        return format_compact_table(reports)

    parts = []
    for i, r in enumerate(reports, 1):
        parts.append(_format_single_report(r, i))
    return "\n".join(parts)


def _format_single_report(r: ParsedReport, idx: int) -> str:
    """Format a single report as a detailed card."""
    lines = []
    lines.append(f"{'═' * 55}")
    lines.append(f"  📊 리포트 #{idx}")
    lines.append(f"{'─' * 55}")
    lines.append(f"  종목    : {r.stock_name} ({r.stock_code})")
    lines.append(f"  증권사  : {r.broker}")
    lines.append(f"  날짜    : {r.report_date}")
    lines.append(f"  애널리스트: {r.analyst or 'N/A'}")
    lines.append(f"  제목    : {r.title[:60]}{'...' if len(r.title) > 60 else ''}")
    lines.append(f"{'─' * 55}")

    # Investment opinion section
    opinion = r.investment_opinion or "N/A"
    lines.append(f"  투자의견: {opinion}")

    if r.target_price is not None:
        tp_str = f"{r.target_price:,}원"
        if r.current_price is not None:
            tp_str += f"  (현재가 {r.current_price:,}원)"
        if r.upside is not None:
            tp_str += f"  ▲{r.upside}%"
        lines.append(f"  목표주가: {tp_str}")
    else:
        lines.append(f"  목표주가: N/A")

    lines.append(f"{'─' * 55}")

    # Financials section
    fin_parts = []
    if r.revenue is not None:
        fin_parts.append(f"매출 {r.revenue:,}억")
    if r.op_income is not None:
        fin_parts.append(f"영업이익 {r.op_income:,}억")
    if r.net_income is not None:
        fin_parts.append(f"순이익 {r.net_income:,}억")
    if r.eps is not None:
        fin_parts.append(f"EPS {r.eps:,.0f}원")
    if r.per is not None:
        fin_parts.append(f"PER {r.per}배")
    if r.pbr is not None:
        fin_parts.append(f"PBR {r.pbr}배")
    if r.roe is not None:
        fin_parts.append(f"ROE {r.roe}%")

    if fin_parts:
        # Split into rows of ~3 items
        for i in range(0, len(fin_parts), 3):
            chunk = fin_parts[i:i + 3]
            lines.append(f"  {' │ '.join(chunk)}")
    else:
        lines.append(f"  (재무 데이터 없음)")

    lines.append(f"{'═' * 55}")
    return "\n".join(lines)


def format_compact_table(reports: List[ParsedReport]) -> str:
    """Format reports as a compact comparison table."""
    lines = []

    # Header
    hdr = (
        f"{'#':>2} │ {'증권사':<8} │ {'의견':<5} │ "
        f"{'목표가':>10} │ {'현재가':>10} │ {'↑%':>6} │ "
        f"{'매출(억)':>10} │ {'OP(억)':>10} │ {'EPS':>8} │ {'PER':>5}"
    )
    sep = "─" * len(hdr)
    lines.append(f"{'═' * len(hdr)}")
    lines.append(hdr)
    lines.append(sep)

    for i, r in enumerate(reports, 1):
        tp = f"{r.target_price:,}" if r.target_price else "-"
        cp = f"{r.current_price:,}" if r.current_price else "-"
        up = f"{r.upside:.1f}" if r.upside else "-"
        rev = f"{r.revenue:,}" if r.revenue else "-"
        op = f"{r.op_income:,}" if r.op_income else "-"
        eps = f"{r.eps:,.0f}" if r.eps else "-"
        per = f"{r.per:.1f}" if r.per else "-"

        lines.append(
            f"{i:>2} │ {r.broker:<8} │ {r.investment_opinion or '-':<5} │ "
            f"{tp:>10} │ {cp:>10} │ {up:>6} │ "
            f"{rev:>10} │ {op:>10} │ {eps:>8} │ {per:>5}"
        )

    lines.append(f"{'═' * len(hdr)}")
    return "\n".join(lines)


# ── JSON formatting ────────────────────────────────────────────────────────

def format_json(reports: List[ParsedReport], indent: int = 2) -> str:
    """Format reports as a JSON array."""
    data = [r.to_dict() for r in reports]
    return json.dumps(data, indent=indent, ensure_ascii=False)


# ── CSV formatting ─────────────────────────────────────────────────────────

CSV_FIELDS = [
    "stock_name", "stock_code", "broker", "report_date", "analyst", "title",
    "investment_opinion", "target_price", "current_price", "upside",
    "revenue", "op_income", "net_income", "eps", "per", "pbr", "roe",
]

CSV_HEADERS_KR = {
    "stock_name": "종목명",
    "stock_code": "종목코드",
    "broker": "증권사",
    "report_date": "날짜",
    "analyst": "애널리스트",
    "title": "제목",
    "investment_opinion": "투자의견",
    "target_price": "목표주가",
    "current_price": "현재주가",
    "upside": "상승여력(%)",
    "revenue": "매출액(억)",
    "op_income": "영업이익(억)",
    "net_income": "순이익(억)",
    "eps": "EPS",
    "per": "PER",
    "pbr": "PBR",
    "roe": "ROE(%)",
}


def format_csv(reports: List[ParsedReport], korean_header: bool = True) -> str:
    """Format reports as CSV."""
    buf = io.StringIO()
    writer = csv.writer(buf)

    if korean_header:
        writer.writerow([CSV_HEADERS_KR[f] for f in CSV_FIELDS])
    else:
        writer.writerow(CSV_FIELDS)

    for r in reports:
        d = r.to_dict()
        row = [d.get(f, "") for f in CSV_FIELDS]
        writer.writerow(row)

    return buf.getvalue()


# ── Summary line ───────────────────────────────────────────────────────────

def format_summary_line(reports: List[ParsedReport]) -> str:
    """One-line summary for terminal logging."""
    n = len(reports)
    if n == 0:
        return "📭 리포트 없음"

    opinions = [r.investment_opinion for r in reports if r.investment_opinion]
    avg_upside = None
    upsides = [r.upside for r in reports if r.upside is not None]
    if upsides:
        avg_upside = sum(upsides) / len(upsides)

    parts = [f"📋 {n}개 리포트"]
    if opinions:
        from collections import Counter
        cnt = Counter(opinions)
        parts.append("의견: " + ", ".join(f"{k}×{v}" for k, v in cnt.most_common()))
    if avg_upside is not None:
        parts.append(f"평균 상승여력: {avg_upside:.1f}%")

    return " | ".join(parts)
