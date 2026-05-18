"""Tests for the import_document orchestrator tool."""
import json
import textwrap
from pathlib import Path

import pytest

from src.orchestrator.tools import import_document


@pytest.fixture
def tmp_ip(tmp_path):
    """Create a temporary IP directory."""
    ip_dir = tmp_path / "test_ip"
    ip_dir.mkdir()
    return ip_dir


@pytest.fixture
def sample_txt(tmp_path):
    """Create a sample .txt requirement file."""
    p = tmp_path / "req.txt"
    p.write_text(textwrap.dedent("""\
        # Test Requirement
        A simple 4-bit up-counter with synchronous reset.
    """), encoding="utf-8")
    return p


@pytest.fixture
def sample_pdf(tmp_path):
    """Create a minimal valid PDF for testing.

    Uses reportlab if available; otherwise writes a tiny stub PDF
    that PyMuPDF can open (single-page, minimal objects).
    """
    pdf_path = tmp_path / "spec.pdf"
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        c = canvas.Canvas(str(pdf_path), pagesize=letter)
        c.drawString(72, 700, "Test PDF Requirement Document")
        c.drawString(72, 680, "A UART with 8-bit data width and parity support.")
        c.save()
        return pdf_path
    except ImportError:
        pass

    # Minimal hand-crafted PDF (one page with "Hello" text)
    pdf_path.write_bytes(
        b"%PDF-1.0\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]"
        b"/Parent 2 0 R/Resources<</Font<</F1 4 0 R>>>>"
        b"/Contents 5 0 R>>endobj\n"
        b"4 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
        b"5 0 obj<</Length 44>>stream\n"
        b"BT /F1 12 Tf 100 700 Td (Hello PDF) Tj ET\n"
        b"endstream\nendobj\n"
        b"xref\n0 6\n"
        b"0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n"
        b"0000000115 00000 n \n0000000266 00000 n \n0000000340 00000 n \n"
        b"trailer<</Size 6/Root 1 0 R>>\nstartxref\n434\n%%EOF\n"
    )
    return pdf_path


# ------------------------------------------------------------------
# Test cases
# ------------------------------------------------------------------


def test_import_txt_file(tmp_ip, sample_txt):
    result, summary = import_document(
        ip="test_ip", path=str(sample_txt), project_root=tmp_ip.parent
    )
    assert result["ok"] is True
    assert result["doc_type"] == "txt"
    assert result["char_count"] > 0
    assert result["requirement_source_id"].startswith("req_")

    # Manifest written
    manifest_path = tmp_ip / "req" / "import_manifest.json"
    assert manifest_path.is_file()
    manifest = json.loads(manifest_path.read_text())
    assert manifest["sha256"] == result["sha256"]
    assert manifest["doc_type"] == "txt"
    assert manifest["requirement_source_id"] == result["requirement_source_id"]

    # Source markdown written
    md_path = tmp_ip / "req" / "source" / "test_ip.md"
    assert md_path.is_file()
    assert "up-counter" in md_path.read_text()


def test_import_pdf_file(tmp_ip, sample_pdf):
    result, summary = import_document(
        ip="test_ip", path=str(sample_pdf), project_root=tmp_ip.parent
    )
    assert result["ok"] is True
    assert result["doc_type"] == "pdf"
    assert result["char_count"] > 0

    md_path = tmp_ip / "req" / "source" / "test_ip.md"
    assert md_path.is_file()
    extracted = md_path.read_text()
    assert len(extracted) > 0


def test_import_md_file(tmp_ip):
    md_file = tmp_ip.parent / "spec.md"
    md_file.write_text("# MD Spec\nA simple counter.", encoding="utf-8")

    result, _ = import_document(
        ip="test_ip", path=str(md_file), project_root=tmp_ip.parent
    )
    assert result["ok"] is True
    assert result["doc_type"] == "md"


def test_file_not_found(tmp_ip):
    result, summary = import_document(
        ip="test_ip", path="/nonexistent/file.pdf", project_root=tmp_ip.parent
    )
    assert result["ok"] is False
    assert "not found" in result["error"]


def test_invalid_ip_rejected(tmp_path, sample_txt):
    result, summary = import_document(
        ip="../escape", path=str(sample_txt), project_root=tmp_path
    )
    assert result["ok"] is False
    assert "valid ip" in result["error"]
    assert not (tmp_path.parent / "escape").exists()


def test_import_creates_directories(tmp_path, sample_txt):
    """IP directory should be auto-created if missing."""
    ip_root = tmp_path / "new_ip"
    # Don't create ip_root — import_document should handle it via mkdir(parents=True)

    result, _ = import_document(
        ip="new_ip", path=str(sample_txt), project_root=tmp_path
    )
    assert result["ok"] is True
    assert (tmp_path / "new_ip" / "req" / "import_manifest.json").is_file()


def test_import_idempotent_overwrite(tmp_ip, sample_txt):
    """Running import twice overwrites previous files without error."""
    r1, _ = import_document(
        ip="test_ip", path=str(sample_txt), project_root=tmp_ip.parent
    )
    r2, _ = import_document(
        ip="test_ip", path=str(sample_txt), project_root=tmp_ip.parent
    )
    assert r1["ok"] is True
    assert r2["ok"] is True
    # IDs should differ (UUID-based)
    assert r1["requirement_source_id"] != r2["requirement_source_id"]
    # But sha256 is the same (same file)
    assert r1["sha256"] == r2["sha256"]


def test_evidence_summary_is_string(tmp_ip, sample_txt):
    """The second element of the tuple must be a short string."""
    _, summary = import_document(
        ip="test_ip", path=str(sample_txt), project_root=tmp_ip.parent
    )
    assert isinstance(summary, str)
    assert len(summary) <= 2_100  # within evidence cap
