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
