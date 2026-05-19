# SSOT Import — Multi-Format Markdown Converter (2026-05-19)

`/api/ssot/import/upload` now accepts PowerPoint, Word, and PDF in addition to
the existing plain-text/markdown formats. The handler keeps the original
upload byte-for-byte and emits a Markdown rendering plus extracted images,
so downstream `/import` always operates on Markdown.

## Accepted extensions

`src/atlas_ui.py` `_SSOT_IMPORT_EXTENSIONS`:

- Text/markup: `.md`, `.txt`, `.rst`, `.yaml`, `.yml`, `.json`, `.xml`, `.csv`, `.tsv`
- RTL/source: `.sv`, `.svh`, `.v`, `.vh`, `.py`, `.c`, `.cpp`, `.h`, `.f`, `.sdc`, `.tcl`, `.rpt`, `.log`
- Office/PDF (new): `.pdf`, `.pptx`, `.docx`
- `.doc` (legacy Word) is recognised but rejected with `legacy .doc not supported (save as .docx)`.
  Reason: there is no pure-Python parser for the binary `.doc` format; users
  should re-save as `.docx`.

## On-disk layout

For an IP `<ip>` and upload index `<idx>` at millisecond timestamp `<ts>`:

```
<ip>/req/imports/
  originals/
    <ts>_<idx>_<original_filename>          # untouched bytes
  <ts>_<idx>_<basename>.md                  # converted markdown
  images/
    <ts>_<idx>_<n>.<ext>                    # extracted embedded images
```

The original is always written first. If conversion fails, the original
remains on disk and the response carries `convert_error` for that entry; the
batch does not abort.

## Conversion rules per suffix

| Suffix | Library | Markdown source | Images |
|---|---|---|---|
| `.md` `.txt` `.rst` | stdlib | bytes decoded as UTF-8 (errors=replace) | none |
| `.pdf` | `pymupdf4llm.to_markdown` for text; `PyMuPDF` (`fitz`) for images | per-page Markdown | `doc.extract_image(xref)` for each XObject |
| `.pptx` | `python-pptx` | `## Slide N` per slide + text-frame paragraphs | `shape.image.blob` for `MSO_SHAPE_TYPE.PICTURE` shapes |
| `.docx` | `python-docx` | paragraph text; `Heading 1/2/3` style → `#`/`##`/`###` | image relations on the document part |

Tables and complex formatting are intentionally not preserved — the goal is
ingestible Markdown text plus a copy of the embedded images.

## Response shape

```json
{
  "ok": true,
  "ip": "atcdmac100",
  "saved": [
    {
      "name": "spec.pptx",
      "bytes": 29424,
      "original_path": "atcdmac100/req/imports/originals/1779195886526_0_spec.pptx",
      "md_path":       "atcdmac100/req/imports/1779195886526_0_spec.md",
      "image_paths":   ["atcdmac100/req/imports/images/1779195886526_0_1.png"],
      "path":          "atcdmac100/req/imports/1779195886526_0_spec.md"
    }
  ],
  "paths": ["atcdmac100/req/imports/1779195886526_0_spec.md"],
  "errors": [],
  "command": "/import --ip atcdmac100 @atcdmac100/req/imports/1779195886526_0_spec.md"
}
```

`paths` (and the generated `command`) intentionally point at the converted
Markdown so `/import` consumes text rather than binary. If a conversion failed,
`path` falls back to `original_path` for that entry so the operator can decide
how to handle it manually; `convert_error` is set for that entry and the same
message is appended to top-level `errors`.

## Size limit

`max_bytes` raised from 12 MiB to 32 MiB to accommodate typical PDF specs and
image-heavy decks while still capping pathological uploads.

## Dependencies

`requirements.txt` now lists:

- `python-pptx`
- `python-docx`
- `pymupdf4llm`
- `PyMuPDF` (used directly for PDF image extraction)

`markitdown` is intentionally not used: it requires Python ≥ 3.10 and this
host runs 3.9.6.

## Smoke results (2026-05-19)

Helper run against generated fixtures (1×slide pptx with embedded PNG,
2-section docx with heading levels + image, 2-line PDF with image):

```
.pdf  → md 42 B  + 1 image
.pptx → md 65 B  + 1 image  (## Slide 1 / ## Slide 2 headings emitted)
.docx → md 96 B  + 1 image  (# / ## headings preserved)
.md passthrough → exact byte-equal text
corrupt .pptx → md_path=None, error="convert failed: Package not found at ..."
                (handler keeps the original, batch continues)
```

## Restart note

After deploying this change, the running atlas_ui Python process must be
restarted — the route handler and helper are wired inside `create_app()`, so a
hot reload does not pick them up.
