#!/usr/bin/env bash
# Provision the local Perforce (Helix Core) workspace for ATLAS / common_ai_agent.
#
# Creates a single stream client bound to //GOOD_SOC/GOOD_IP, rooted at the
# project root, plus a .p4config (connection) and .p4ignore (exclusions) so the
# Perforce SCM adapter (core/scm_perforce.py) can talk to the server.
#
# Idempotent: safe to re-run. Usage:
#   scripts/perforce_setup.sh [PROJECT_ROOT]
#
# Env overrides: P4PORT (default localhost:1666), P4USER (default $USER),
#   P4CLIENT (default atlas_GOOD_IP), P4_STREAM (default //GOOD_SOC/GOOD_IP).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${1:-$(cd "$SCRIPT_DIR/.." && pwd)}"

P4PORT="${P4PORT:-localhost:1666}"
P4USER="${P4USER:-$(id -un)}"
P4CLIENT="${P4CLIENT:-atlas_GOOD_IP}"
P4_STREAM="${P4_STREAM:-//GOOD_SOC/GOOD_IP}"

export P4PORT P4USER

echo "== Perforce setup =="
echo "  PROJECT_ROOT : $PROJECT_ROOT"
echo "  P4PORT       : $P4PORT"
echo "  P4USER       : $P4USER"
echo "  P4CLIENT     : $P4CLIENT"
echo "  Stream       : $P4_STREAM"

command -v p4 >/dev/null 2>&1 || { echo "ERROR: p4 not found on PATH" >&2; exit 127; }

# 1) Tell p4 to honor per-tree config + ignore files.
p4 set P4CONFIG=.p4config
p4 set P4IGNORE=.p4ignore

# 2) Confirm server reachability + ticket.
if ! p4 -p "$P4PORT" -u "$P4USER" login -s >/dev/null 2>&1; then
  echo "WARNING: not logged in (security>=3 needs a ticket). Run: p4 -p $P4PORT -u $P4USER login" >&2
fi

# 3) .p4config (connection) at the project root — found by p4 walking up the tree.
P4CONFIG_FILE="$PROJECT_ROOT/.p4config"
cat > "$P4CONFIG_FILE" <<EOF
P4PORT=$P4PORT
P4USER=$P4USER
P4CLIENT=$P4CLIENT
EOF
echo "wrote $P4CONFIG_FILE"

# 4) .p4ignore — keep secrets/build junk/sessions out of Perforce (defense in depth).
P4IGNORE_FILE="$PROJECT_ROOT/.p4ignore"
if [ ! -f "$P4IGNORE_FILE" ]; then
  cat > "$P4IGNORE_FILE" <<'EOF'
# Secrets / local config — never submit
.env
.env.*
.p4config
.mcp.json
# VCS / tooling state
.git/
.gitignore
.omc/
.omx/
.cursor/
.claude/
.github/
# Sessions / scratch / logs
.session/
.session_debug/
.workers/
.deep_test/
.rag/
.benchmarks/
.pytest_cache/
artifacts/
cmd_output_*.txt
*.log
# Build / deps / caches
node_modules/
dist/
__pycache__/
*.pyc
*.pyo
# Databases / binaries
*.db
*.db-shm
*.db-wal
*.vcd
EOF
  echo "wrote $P4IGNORE_FILE"
else
  echo "kept existing $P4IGNORE_FILE"
fi

# 5) Stream client rooted at PROJECT_ROOT (1:1 mapping <ip> <-> $P4_STREAM/<ip>).
if p4 -p "$P4PORT" -u "$P4USER" clients -e "$P4CLIENT" 2>/dev/null | grep -q "^Client $P4CLIENT "; then
  echo "client $P4CLIENT already exists — leaving as is"
else
  # clobber: allow `p4 sync -f` to overwrite writable local files (the
  # "있으면 overwrite" pull behavior the UI's Sync button needs).
  p4 -p "$P4PORT" -u "$P4USER" client -S "$P4_STREAM" -o "$P4CLIENT" \
    | sed -E "s|^Root:.*|Root:\t$PROJECT_ROOT|" \
    | sed "s/noclobber/clobber/" \
    | p4 -p "$P4PORT" -u "$P4USER" client -i
  echo "created stream client $P4CLIENT (clobber enabled)"
fi

# 6) Keep .p4config out of git (machine/connection specific).
GITIGNORE="$PROJECT_ROOT/.gitignore"
if [ -f "$GITIGNORE" ] && ! grep -qxF '.p4config' "$GITIGNORE"; then
  printf '\n# Perforce local connection config\n.p4config\n' >> "$GITIGNORE"
  echo "appended .p4config to .gitignore"
fi

echo "== done =="
p4 -p "$P4PORT" -u "$P4USER" -c "$P4CLIENT" info | grep -E '^(User|Client) name|^Client root|^Server' || true
