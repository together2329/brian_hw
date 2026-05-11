#!/usr/bin/env bash
# Fetch the CDN JS/CSS bundle into frontend/atlas/vendor/ so the
# Atlas UI works without unpkg.com / jsdelivr access.
#
# Usage:
#   bash scripts/fetch_atlas_vendor.sh
#
# After the download succeeds, manually switch the <script> src= and
# <link> href= values in frontend/atlas/index.html from
#   https://unpkg.com/<pkg>@<ver>/<path>
# to
#   /static/vendor/<pkg>@<ver>/<path>
# (or whatever your local mount prefix is).

set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$ROOT/frontend/atlas/vendor"
mkdir -p "$DEST"

URLS=(
  "https://unpkg.com/react@18.3.1/umd/react.development.js"
  "https://unpkg.com/react-dom@18.3.1/umd/react-dom.development.js"
  "https://unpkg.com/@babel/standalone@7.29.0/babel.min.js"
  "https://unpkg.com/marked@9/marked.min.js"
  "https://unpkg.com/dompurify@3.1.6/dist/purify.min.js"
  "https://unpkg.com/prismjs@1.29.0/themes/prism-tomorrow.css"
  "https://unpkg.com/prismjs@1.29.0/components/prism-core.min.js"
  "https://unpkg.com/prismjs@1.29.0/plugins/autoloader/prism-autoloader.min.js"
)

for url in "${URLS[@]}"; do
  rel="${url#https://unpkg.com/}"
  out="$DEST/$rel"
  mkdir -p "$(dirname "$out")"
  echo "  → $rel"
  curl -fsSL --retry 3 -o "$out" "$url"
done

echo
echo "Vendored under: $DEST"
echo "Total:"
du -sh "$DEST"
echo
echo "Next: rewrite https://unpkg.com/... URLs in"
echo "  frontend/atlas/index.html"
echo "to /vendor/... (or your preferred local prefix)."
