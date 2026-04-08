#!/usr/bin/env python3
"""
ACE 엔비디아밸류체인액티브 ETF (483320) — Comprehensive Analysis
================================================================
Combines:
  1. Naver Finance ETF info (holdings, price, description)
  2. SEC EDGAR XBRL API (financial fundamentals for all US-listed holdings)
  3. Supply chain position analysis (optical/semiconductor focus)

Usage:
  python3 nvidia_valuechain_analysis.py

Requirements:
  - naver_report_parser.sec_edgar module
  - requests, beautifulsoup4
"""

import sys, json, time
sys.path.insert(0, '.')

from naver_report_parser.sec_edgar import SECEdgarClient


def get_etf_info_from_naver(code='483320'):
    """Fetch ETF basic info and holdings from Naver Finance."""
    import requests
    from bs4 import BeautifulSoup

    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}

    url = f'https://finance.naver.com/item/main.naver?code={code}'
    resp = requests.get(url, headers=headers)
    resp.encoding = 'utf-8'
    soup = BeautifulSoup(resp.text, 'html.parser')

    # ETF Name
    name = soup.select_one('.wrap_company h2 a')
    name_text = name.text.strip() if name else f"ETF {code}"

    # Price
    price_el = soup.select_one('.no_today .blind')
    price = price_el.text.strip() if price_el else "N/A"

    # Description
    desc_el = soup.select_one('.description')
    desc = desc_el.text.strip()[:200] if desc_el else ""

    # Holdings table
    holdings_raw = []
    tables = soup.find_all('table')
    for table in tables:
        ths = table.select('th')
        th_text = ' '.join(th.get_text(strip=True) for th in ths)
        if '구성종목' in th_text:
            for row in table.select('tbody tr'):
                tds = row.select('td')
                if len(tds) >= 2:
                    h_name = tds[0].get_text(strip=True)
                    shares = tds[1].get_text(strip=True)
                    if h_name:
                        holdings_raw.append({'name': h_name, 'shares': shares})

    return {
        'code': code,
        'name': name_text,
        'price': price,
        'description': desc,
        'holdings_raw': holdings_raw,
    }


# ETF Holdings with weights (from Investing.com data, updated 2026.04.08)
ETF_HOLDINGS = [
    {"ticker": "NVDA", "name": "NVIDIA Corp",                     "weight": 22.67},
    {"ticker": "TSM",  "name": "Taiwan Semiconductor (ADR)",      "weight": 16.02},
    {"ticker": "VRT",  "name": "Vertiv Holdings",                 "weight":  7.03},
    {"ticker": "ARM",  "name": "ARM Holdings (ADR)",              "weight":  3.95},
    {"ticker": "TER",  "name": "Teradyne Inc",                    "weight":  3.94},
    {"ticker": "LITE", "name": "Lumentum Holdings",               "weight":  3.68},
    {"ticker": "MRVL", "name": "Marvell Technology",              "weight":  3.64},
    {"ticker": "CRWV", "name": "CoreWeave Inc",                   "weight":  3.53},
    # Korean stocks (no SEC data):
    # {"name": "SK하이닉스 Futures", "weight": 6.92},
    # {"name": "삼성전자 (005930.KS)", "weight": 3.77},
]

# Pre-configured optical supply chain stocks (for comparison)
OPTICAL_SUPPLY_CHAIN = [
    {"ticker": "MU",   "name": "Micron Technology"},
    {"ticker": "COHR", "name": "Coherent Corp"},
    {"ticker": "GLW",  "name": "Corning Inc"},
    {"ticker": "FN",   "name": "Fabrinet"},
]

# Supply chain position mapping
CHAIN_SEGMENTS = {
    "GPU/AI Chips":          ["NVDA", "MRVL"],
    "Chip Architecture":     ["ARM"],
    "Foundry/Manufacturing": ["TSM", "MU"],
    "Packaging/Testing":     ["TER"],
    "Optical/Networking":    ["LITE", "COHR", "GLW", "FN"],
    "Data Center Infra":     ["VRT", "CRWV"],
}


def main():
    print("=" * 100)
    print("  ACE 엔비디아밸류체인액티브 ETF (483320) — Comprehensive Analysis")
    print("  기초지수: KEDI 글로벌 AI 반도체 지수 | 운용사: 한국투자신통운용")
    print("  상장일: 2024.06.11 | 총보수: 연 0.45% | 순자산: ~1,961억원")
    print("=" * 100)

    # ── ETF Info from Naver ──
    print("\n📡 Fetching ETF info from Naver Finance...")
    etf_info = get_etf_info_from_naver('483320')
    print(f"   Name: {etf_info['name']}")
    print(f"   Price: {etf_info['price']}")

    # ── ETF Holdings ──
    holdings = ETF_HOLDINGS
    optical = OPTICAL_SUPPLY_CHAIN

    print(f"\n📋 ETF Top 10 Holdings (US-listed)")
    print("─" * 60)
    for h in holdings:
        print(f"  {h['weight']:5.2f}%  {h['ticker']:6s}  {h['name']}")
    print(f"\n  Korean holdings (no SEC data):")
    print(f"   6.92%  SK하이닉스 (Futures)")
    print(f"   3.77%  삼성전자 (005930.KS)")
    total_us = sum(h['weight'] for h in holdings)
    print(f"\n  Total US SEC-analyzable: {total_us:.2f}%")
    print(f"  Total Korean: 10.69%")

    # ── Fetch SEC EDGAR Data ──
    client = SECEdgarClient()

    all_tickers = [h['ticker'] for h in holdings] + [o['ticker'] for o in optical]
    all_tickers = list(dict.fromkeys(all_tickers))  # deduplicate

    print(f"\n🔍 Fetching SEC EDGAR data for {len(all_tickers)} companies...")
    print(f"   Tickers: {', '.join(all_tickers)}")
    print()

    results = {}
    for ticker in all_tickers:
        try:
            data = client.get_financials(ticker, years=3)
            results[ticker] = data
            print(f"  ✅ {ticker:6s} — {data.company.name}")
        except Exception as e:
            print(f"  ❌ {ticker:6s} — Error: {e}")

    tickers_with_data = list(results.keys())
    weight_map = {h['ticker']: h['weight'] for h in holdings}
    weight_map.update({o['ticker']: "—" for o in optical})

    # ── Comparison Table ──
    print(f"\n{'=' * 140}")
    print("  📊 NVIDIA VALUE CHAIN ETF — SEC EDGAR Financial Comparison (Latest Annual)")
    print(f"{'=' * 140}")

    metrics_spec = [
        ("Revenue",     "revenue",            "B"),
        ("GrossProfit", "gross_profit",       "B"),
        ("OpIncome",    "operating_income",   "B"),
        ("NetIncome",   "net_income",         "B"),
        ("R&D",         "rd_expense",         "B"),
        ("EPS(Dil)",    "eps_diluted",        "raw"),
        ("GrossMgn",    "gross_margin",       "%"),
        ("OpMgn",       "operating_margin",   "%"),
        ("NetMgn",      "net_margin",         "%"),
        ("ROE",         "roe",                "%"),
        ("Assets",      "total_assets",       "B"),
        ("Equity",      "stockholders_equity","B"),
    ]

    hdr = f"  {'Ticker':<6s} {'Company':<35s} {'ETF%':>6s}"
    for label, _, _ in metrics_spec:
        hdr += f" {label:>10s}"
    print(hdr)
    print("─" * len(hdr))

    for ticker in tickers_with_data:
        fin = results[ticker]
        ann = fin.latest_annual
        row = f"  {ticker:<6s} {fin.company.name[:35]:<35s}"
        w = weight_map.get(ticker, "—")
        row += f" {str(w):>6s}"

        if ann:
            for label, attr, unit in metrics_spec:
                val = getattr(ann, attr, None)
                if val is None:
                    formatted = "N/A"
                elif unit == "B":
                    if abs(val) >= 1e9:
                        formatted = f"${val/1e9:.1f}B"
                    elif abs(val) >= 1e6:
                        formatted = f"${val/1e6:.0f}M"
                    else:
                        formatted = f"${val:,.0f}"
                elif unit == "%":
                    formatted = f"{val:.1f}%"
                else:
                    formatted = f"${val:.2f}"
                row += f" {formatted:>10s}"
        else:
            for _ in metrics_spec:
                row += f" {'N/A':>10s}"
        print(row)

    print("─" * len(hdr))

    # ── Revenue Growth ──
    print(f"\n📈 Annual Revenue Growth Trends")
    print("─" * 100)
    print(f"  {'Ticker':<6s} {'Company':<25s}", end="")
    for _ in range(4):
        print(f" {'FY':>12s}", end="")
    print(f"  {'YoY Growth':>12s}")
    print("  " + "─" * 98)

    for ticker in tickers_with_data:
        fin = results[ticker]
        row = f"  {ticker:<6s} {fin.company.name[:25]:<25s}"
        if fin.annual_history:
            for p in fin.annual_history:
                if p.revenue:
                    row += f" ${p.revenue/1e9:>8.2f}B"
                else:
                    row += f" {'N/A':>12s}"
            growth_str = ""
            if len(fin.annual_history) >= 2:
                latest = fin.annual_history[-1]
                prev = fin.annual_history[-2]
                if latest.revenue and prev.revenue and prev.revenue != 0:
                    growth = (latest.revenue - prev.revenue) / abs(prev.revenue) * 100
                    growth_str = f"{growth:+.1f}%"
                else:
                    growth_str = "N/A"
            row += f"  {growth_str:>12s}"
        print(row)

    # ── Profitability Rankings ──
    print(f"\n🏆 Profitability Rankings (Latest Annual)")
    print("─" * 80)

    for metric_name, attr in [("Gross Margin", "gross_margin"), ("Operating Margin", "operating_margin"),
                               ("Net Margin", "net_margin"), ("ROE", "roe")]:
        print(f"\n  {metric_name}:")
        ranked = []
        for ticker in tickers_with_data:
            fin = results[ticker]
            if fin.latest_annual:
                val = getattr(fin.latest_annual, attr, None)
                if val is not None:
                    ranked.append((ticker, val))
        ranked.sort(key=lambda x: x[1], reverse=True)
        for i, (ticker, val) in enumerate(ranked):
            bar = "█" * int(val / 2) if val > 0 else "░" * int(abs(val) / 2)
            marker = " 👑" if i == 0 else ""
            print(f"    {i+1}. {ticker:6s} {val:>7.1f}% {bar}{marker}")

    # ── ETF Weighted Metrics ──
    print(f"\n📊 ETF Portfolio-Weighted Metrics")
    print("─" * 80)
    total_weight = sum(h['weight'] for h in holdings)
    weighted = {}
    for label, attr, unit in metrics_spec:
        wsum = 0
        wtotal = 0
        for h in holdings:
            fin = results.get(h['ticker'])
            if fin and fin.latest_annual:
                val = getattr(fin.latest_annual, attr, None)
                if val is not None and unit == "%":
                    wsum += val * h['weight']
                    wtotal += h['weight']
        if wtotal > 0 and unit == "%":
            weighted[label] = wsum / wtotal

    if weighted:
        print(f"  {'Metric':<20s} {'Weighted Average':>15s}")
        print(f"  {'─' * 40}")
        for name, val in weighted.items():
            bar = "█" * int(val)
            print(f"  {name:<20s} {val:>8.1f}% {bar}")

    print(f"\n  * Weighted by ETF constituent weights (US stocks only)")
    print(f"  * Total US weight analyzed: {total_weight:.1f}%")

    # ── Quarterly Data ──
    print(f"\n📅 Latest Quarterly Data")
    print("─" * 100)
    print(f"  {'Ticker':<6s} {'Quarter':<12s} {'Revenue':>12s} {'Net Income':>12s} {'Net Margin':>12s}")
    print("  " + "─" * 60)

    for ticker in tickers_with_data:
        fin = results[ticker]
        q = fin.latest_quarterly
        if q:
            rev = f"${q.revenue/1e9:.2f}B" if q.revenue else "N/A"
            ni = f"${q.net_income/1e9:.2f}B" if q.net_income is not None else "N/A"
            nm = f"{q.net_margin:.1f}%" if q.net_margin is not None else "N/A"
            q_label = f"FY{q.fiscal_year} {q.fiscal_period}"
            print(f"  {ticker:<6s} {q_label:<12s} {rev:>12s} {ni:>12s} {nm:>12s}")

    # ── Supply Chain Position ──
    print(f"\n🔗 Value Chain Position Analysis")
    print("─" * 100)

    for segment, tickers_in_segment in CHAIN_SEGMENTS.items():
        print(f"\n  [{segment}]")
        for t in tickers_in_segment:
            if t in results:
                fin = results[t]
                ann = fin.latest_annual
                if ann and ann.revenue:
                    rev_str = f"${ann.revenue/1e9:.2f}B"
                    margin_str = f"{ann.net_margin:.1f}%" if ann.net_margin is not None else "N/A"
                    w_str = f"{weight_map.get(t, '—')}%"
                    print(f"    {t:6s} Rev={rev_str:>10s} NetMargin={margin_str:>8s} ETF Weight={w_str:>6s}")
                else:
                    print(f"    {t:6s} (no annual data)")

    print(f"\n{'=' * 100}")
    print("  ✅ Analysis complete. Data: Naver Finance (ETF info) + SEC EDGAR XBRL API (fundamentals)")
    print(f"{'=' * 100}")


if __name__ == '__main__':
    main()
