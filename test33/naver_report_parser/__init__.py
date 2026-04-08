"""Naver Finance Research Report PDF Parser.

Quick start:
    python -m naver_report_parser.cli 005930
"""
__version__ = "1.0.0"

from .cli import main
from .crawler import NaverReportCrawler
from .formatter import format_table, format_json, format_csv, format_compact_table
from .models import ParsedReport, ReportInfo
from .parser import ReportParser

__all__ = [
    "main",
    "NaverReportCrawler",
    "ReportParser",
    "ParsedReport",
    "ReportInfo",
    "format_table",
    "format_json",
    "format_csv",
    "format_compact_table",
]
