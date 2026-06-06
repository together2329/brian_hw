from pathlib import Path
import importlib
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_extract_markdown_import_assets_groups_relative_and_recorded_paths():
    import_evidence_assets = importlib.import_module("core.import_evidence_assets")
    ImportEvidenceAssets = import_evidence_assets.ImportEvidenceAssets
    extract_markdown_import_assets = import_evidence_assets.extract_markdown_import_assets

    markdown = "\n".join(
        [
            "![figure](visual/page-002.png)",
            "![embedded](images/chart.png)",
            "### `mctp_assembler/req/imports/images/extracted.png`",
            "![remote](https://example.test/image.png)",
            "![inline](data:image/png;base64,AAAA)",
            "",
        ]
    )

    assets = extract_markdown_import_assets(markdown, "mctp_assembler/req/imports/spec.md")

    assert assets == ImportEvidenceAssets(
        image_paths=(
            "mctp_assembler/req/imports/images/chart.png",
            "mctp_assembler/req/imports/images/extracted.png",
        ),
        visual_paths=("mctp_assembler/req/imports/visual/page-002.png",),
    )
