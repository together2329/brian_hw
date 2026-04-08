#!/usr/bin/env python3
"""CLI for Naver Finance research report analysis.

Usage:
    python -m naver_report_parser.cli 005930
    python -m naver_report_parser.cli 005930 -n 5 --format json
    python -m naver_report_parser.cli 005930 --format csv -o reports.csv
    python -m naver_report_parser.cli --pdf ./report.pdf

Commands:
    <stock_code>       Analyze latest reports for a stock code
    --pdf <file>       Analyze a single local PDF file

Output formats:
    table   Rich console table (default)
    json    JSON array
    csv     CSV with Korean headers
    compact Compact comparison table
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import List, Optional

from .crawler import NaverReportCrawler
from .errors import CrawlError, NaverReportError, PDFError
from .formatter import format_table, format_json, format_csv, format_compact_table, format_summary_line
from .models import ParsedReport, ReportInfo
from .parser import ReportParser


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="naver_report_parser",
        description="네이버 증권 리서치 리포트 분석 도구",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "예시:\n"
            "  python -m naver_report_parser.cli 005930\n"
            "  python -m naver_report_parser.cli 005930 -n 5 --format json\n"
            "  python -m naver_report_parser.cli 005930 --format csv -o result.csv\n"
            "  python -m naver_report_parser.cli --pdf ./samsung_report.pdf\n"
        ),
    )

    # Positional: stock code
    parser.add_argument(
        "stock_code",
        nargs="?",
        help="종목코드 (예: 005930)",
    )

    # PDF mode
    parser.add_argument(
        "--pdf",
        type=str,
        default=None,
        help="로컬 PDF 파일 경로 (크롤링 대신 단일 파일 분석)",
    )

    # Options
    parser.add_argument(
        "-n", "--count",
        type=int,
        default=3,
        help="분석할 최신 리포트 수 (기본: 3)",
    )
    parser.add_argument(
        "-f", "--format",
        choices=["table", "json", "csv", "compact"],
        default="table",
        help="출력 형식 (기본: table)",
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="출력 파일 경로 (지정하지 않으면 stdout)",
    )
    parser.add_argument(
        "--no-download",
        action="store_true",
        help="PDF 다운로드 없이 리포트 목록만 출력",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="PDF 다운로드 간 지연 시간(초, 기본: 0.5)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="진행 상황 상세 출력",
    )

    return parser.parse_args(argv)


def _log(msg: str, verbose: bool = True) -> None:
    """Print a log message to stderr."""
    if verbose:
        print(f"  {msg}", file=sys.stderr)


def _analyze_single_pdf(pdf_path: str) -> ParsedReport:
    """Analyze a single local PDF file."""
    parser = ReportParser()
    pdf_bytes = Path(pdf_path).read_bytes()
    return parser.parse_bytes(pdf_bytes)


def _crawl_and_analyze(
    stock_code: str,
    count: int,
    no_download: bool = False,
    delay: float = 0.5,
    verbose: bool = False,
) -> tuple:
    """Crawl reports and optionally parse PDFs.

    Returns
    -------
    tuple of (List[ReportInfo], List[ParsedReport])
    """
    # Step 1: Crawl report listings
    _log(f"🔍 [{stock_code}] 리포트 목록 조회 중...", verbose)
    try:
        crawler = NaverReportCrawler()
        report_list = crawler.fetch_latest(stock_code, count=count)
    except CrawlError as e:
        _log(f"❌ 크롤링 오류: {e}", verbose)
        return [], []
    except Exception as e:
        _log(f"❌ 예상치 못한 오류: {e}", verbose)
        return [], []

    if not report_list:
        _log(f"📭 리포트를 찾을 수 없습니다: {stock_code}", verbose)
        return [], []

    _log(f"📋 {len(report_list)}개 리포트 발견", verbose)
    for r in report_list:
        _log(f"   [{r.report_date}] {r.broker} - {r.title[:40]}...", verbose)

    if no_download:
        return report_list, []

    # Step 2: Download and parse PDFs
    parser = ReportParser()
    parsed_reports: List[ParsedReport] = []

    for i, report in enumerate(report_list):
        label = f"[{i + 1}/{len(report_list)}]"
        _log(f"{label} {report.broker} PDF 다운로드 & 분석 중...", verbose)
        try:
            parsed = parser.parse(report)
            parsed_reports.append(parsed)
            _log(
                f"{label} ✅ {parsed.investment_opinion or '?'} "
                f"목표가 {parsed.target_price or 'N/A':,}원"
                if parsed.target_price
                else f"{label} ✅ 완료",
                verbose,
            )
        except PDFError as e:
            _log(f"{label} ❌ PDF 오류: {e}", verbose)
        except Exception as e:
            _log(f"{label} ❌ 예상치 못한 오류: {e}", verbose)

        if i < len(report_list) - 1:
            time.sleep(delay)

    return report_list, parsed_reports


def _format_output(
    parsed_reports: List[ParsedReport],
    fmt: str,
) -> str:
    """Format parsed reports into the requested output format."""
    if fmt == "json":
        return format_json(parsed_reports)
    elif fmt == "csv":
        return format_csv(parsed_reports)
    elif fmt == "compact":
        return format_compact_table(parsed_reports)
    else:
        return format_table(parsed_reports)


def main(argv: Optional[List[str]] = None) -> int:
    """Main CLI entry point.

    Returns
    -------
    int
        Exit code (0 = success, 1 = error).
    """
    args = parse_args(argv)

    # ── Validate inputs ──
    if not args.stock_code and not args.pdf:
        print("❌ 종목코드 또는 --pdf 경로를 입력하세요.", file=sys.stderr)
        print("   사용법: python -m naver_report_parser.cli 005930", file=sys.stderr)
        return 1

    # ── Mode 1: Single PDF analysis ──
    if args.pdf:
        if not Path(args.pdf).exists():
            print(f"❌ 파일을 찾을 수 없습니다: {args.pdf}", file=sys.stderr)
            return 1

        print(f"📄 PDF 분석: {args.pdf}", file=sys.stderr)
        try:
            parsed = _analyze_single_pdf(args.pdf)
        except PDFError as e:
            print(f"❌ PDF 분석 오류: {e}", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"❌ PDF 분석 실패: {e}", file=sys.stderr)
            return 1

        output = _format_output([parsed], args.format)

    # ── Mode 2: Crawl + analyze ──
    else:
        stock_code = args.stock_code.strip()
        if len(stock_code) != 6 or not stock_code.isdigit():
            print(f"❌ 잘못된 종목코드: {stock_code} (6자리 숫자)", file=sys.stderr)
            return 1

        print(f"📊 종목코드 {stock_code} 리포트 분석 시작", file=sys.stderr)
        report_list, parsed_reports = _crawl_and_analyze(
            stock_code=stock_code,
            count=args.count,
            no_download=args.no_download,
            delay=args.delay,
            verbose=args.verbose,
        )

        if not report_list:
            return 1

        if args.no_download:
            # Just show listing info
            for r in report_list:
                print(
                    f"[{r.report_date}] {r.broker:10s} | {r.title}",
                    file=sys.stderr,
                )
            return 0

        if not parsed_reports:
            print("❌ 분석된 리포트가 없습니다.", file=sys.stderr)
            return 1

        # Summary line
        print(format_summary_line(parsed_reports), file=sys.stderr)

        output = _format_output(parsed_reports, args.format)

    # ── Write output ──
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"💾 저장 완료: {args.output}", file=sys.stderr)
    else:
        print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
