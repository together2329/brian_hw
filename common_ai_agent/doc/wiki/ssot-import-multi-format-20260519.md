# SSOT Import — Multi-Format Markdown Converter (2026-05-19)

`/api/ssot/import/upload` now accepts PowerPoint, Word, PDF, and HTML in
addition to the existing plain-text/markdown formats. The handler keeps the
original upload byte-for-byte and emits a Markdown rendering, so downstream
`/import` always operates on Markdown.

## Conversion engine

[`markitdown`](https://github.com/microsoft/markitdown) under Python 3.10,
invoked from the 3.9 atlas_ui process via `subprocess`:

| Concern | Decision |
|---|---|
| Why subprocess? | atlas_ui runs on Python 3.9.6; markitdown >= 0.1 requires Python >= 3.10. |
| External Python | `/opt/homebrew/bin/python3.10` (configurable via `_SSOT_MARKITDOWN_PY` in `src/atlas_ui.py`). Falls back to `shutil.which("python3.10")` if the hard-coded path is missing. |
| Timeout | 60 s per file. |
| Install | `python3.10 -m pip install 'markitdown[all]'` on the host running atlas_ui. |
| Images | markitdown inlines embedded images as base64 data URIs (docx) or relative refs (pptx). No separate `images/` directory is materialised. |

## Accepted extensions

`src/atlas_ui.py` `_SSOT_IMPORT_EXTENSIONS`:

- Text/markup (passthrough, no markitdown): `.md`, `.txt`, `.rst`, `.yaml`, `.yml`, `.json`, `.xml`, `.csv`, `.tsv`
- RTL/source (passthrough as text): `.sv`, `.svh`, `.v`, `.vh`, `.py`, `.c`, `.cpp`, `.h`, `.f`, `.sdc`, `.tcl`, `.rpt`, `.log`
- Office/PDF/Web (converted via markitdown): `.pdf`, `.pptx`, `.docx`, `.html`, `.htm`

`_SSOT_IMPORT_PASSTHROUGH = {".md", ".txt", ".rst"}` is the small set that is
copied verbatim into a `.md` file. Other text-ish suffixes that arrive (e.g.
`.sv`, `.py`) currently flow through markitdown — its plain-text reader gives
a sensible passthrough as well.

## On-disk layout

For IP `<ip>`, upload index `<idx>`, millisecond timestamp `<ts>`:

```
<ip>/req/imports/
  originals/
    <ts>_<idx>_<original_filename>     # untouched bytes
  <ts>_<idx>_<basename>.md             # markitdown-converted markdown
```

The original is always written first. If markitdown fails, the original
remains on disk and the response carries `convert_error` for that entry; the
batch does not abort.

## Response shape

```json
{
  "ok": true,
  "ip": "atcdmac100",
  "saved": [
    {
      "name": "spec.pptx",
      "bytes": 29424,
      "original_path": "atcdmac100/req/imports/originals/1779196112754_0_spec.pptx",
      "md_path":       "atcdmac100/req/imports/1779196112754_0_spec.md",
      "path":          "atcdmac100/req/imports/1779196112754_0_spec.md"
    }
  ],
  "paths": ["atcdmac100/req/imports/1779196112754_0_spec.md"],
  "errors": [],
  "command": "/import --ip atcdmac100 @atcdmac100/req/imports/1779196112754_0_spec.md"
}
```

`paths` (and the generated `command`) intentionally point at the converted
Markdown so `/import` consumes text rather than binary. If conversion failed,
`path` points at `original_path` for that entry and `convert_error` is set.

## Size limit

`max_bytes` raised from 12 MiB to 32 MiB.

## Smoke results (2026-05-19)

Helper run against generated fixtures:

```
.pdf  ->  41 B  ('Hello PDF (line 1) / Hello PDF (line 2)')
.pptx -> 125 B  ('<!-- Slide number: 1 --> # Hello PPTX ...')
.docx -> 131 B  ('# Doc Title / ## Section A ...')
.md passthrough -> exact byte-equal text
corrupt .pptx -> markitdown rc=0, body 'not a pptx' (upstream parses arbitrary
                 bytes as plain text); handler does not crash.
```

## Restart note

After deploying this change, the running atlas_ui Python process must be
restarted - the route handler and helper are wired inside `create_app()`, so a
hot reload does not pick them up.

## Augment 2026-05-19: markitdown + cursor-agent vision

`_convert_upload_to_markdown` now has two distinct stages:

1. **Text rendering.** Try `markitdown` via subprocess first (Python 3.10 host
   at `/opt/homebrew/bin/python3.10`). If markitdown succeeds, its stdout is
   the Markdown body. If it fails (subprocess error, non-zero exit, timeout,
   missing 3.10), the per-format extractor (`pymupdf4llm` for `.pdf`,
   `python-pptx` for `.pptx`, `python-docx` for `.docx`) writes the body
   instead. The per-format extractors stay in the codebase as the backup
   path so a missing 3.10 toolchain does not break uploads.
2. **Image extraction.** Always runs the per-format path because markitdown
   does not emit clean image files: `PyMuPDF`/`fitz` for `.pdf`, `python-pptx`
   `PICTURE` shapes for `.pptx`, `doc.part.rels` image relations for `.docx`.
   Extracted images land in `<ip>/req/imports/images/<ts>_<idx>_<n>.<ext>`.
3. **Image descriptions.** For each extracted image, the handler shells out
   to `cursor-agent` (`/Users/brian/.local/bin/cursor-agent`, model
   `sonnet-4`, 30 s timeout) with `Describe the content of @<img> in 2-3
   sentences ...`. The descriptions are appended to the `.md` file under a
   `## Extracted Images` heading, one `### \`<rel/path>\`` block per image,
   with `_(no description)_` as a placeholder when the CLI is unavailable or
   fails. Vision failures never block the upload.

The response payload now carries `image_paths` per saved entry
(repo-relative POSIX paths). When no images were extracted the list is empty
and no `## Extracted Images` section is appended.

On-disk layout extends to:

```
<ip>/req/imports/
  originals/
    <ts>_<idx>_<original_filename>
  images/
    <ts>_<idx>_<n>.<ext>
  <ts>_<idx>_<basename>.md   # markitdown body + '## Extracted Images' tail
```

## Related

- [[ssot-conversion-flow-20260519]] — full upload → `/import` → `/grill-me` →
  `/to-ssot` → `check_ssot_disk.sh` pipeline and why each stage is split for
  human audit. This page covers stage 1 only; that page covers the chain.
