#!/usr/bin/env bash
set -u

IP="${IP_NAME:-${1:-}}"
ROOT="${ATLAS_PROJECT_ROOT:-${ATLAS_ROOT:-.}}"

if [ -z "$IP" ]; then
    echo "[ip-signoff] usage: run_ip_signoff.sh <ip> [--root <ip-parent>]" >&2
    exit 2
fi

shift || true
while [ $# -gt 0 ]; do
    case "$1" in
        --root) ROOT="${2:-}"; shift 2 ;;
        --root=*) ROOT="${1#--root=}"; shift ;;
        *) echo "[ip-signoff] unknown argument: $1" >&2; exit 2 ;;
    esac
done

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
python3 "$SCRIPT_DIR/check_ip_signoff.py" "$IP" --root "$ROOT"
