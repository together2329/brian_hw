#!/usr/bin/env python3
"""Append one orchestrator chat row for UI screenshot tests.

The UI's CHAT tab hydrates from AtlasDB trace_events where
event_type='chat_message'. This helper keeps the e2e screenshot scripts from
reimplementing SQLite schema details in JavaScript.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--ip", required=True)
    parser.add_argument("--user-id", required=True)
    parser.add_argument("--display-name", default="")
    parser.add_argument("--role", required=True)
    parser.add_argument("--db-path", default="")
    args = parser.parse_args()

    sys.path.insert(0, str(_repo_root()))
    from core.atlas_db import AtlasDB  # noqa: WPS433

    content = sys.stdin.read().strip()
    if not content:
        return 0

    project_root = Path(args.project_root).expanduser().resolve()
    db_path = (
        args.db_path
        or os.environ.get("ATLAS_TRACE_DB_PATH")
        or os.environ.get("ATLAS_DB_PATH")
        or str(Path.home() / ".common_ai_agent" / "atlas.db")
    )
    ip = args.ip.strip()
    user_id = args.user_id.strip() or "admin"

    with AtlasDB(db_path) as db:
        workspace = db.upsert_workspace(
            project_root.name or "default",
            owner_user_id=user_id,
            local_path=str(project_root),
        )
        ip_row = db.upsert_ip_block(
            workspace["id"],
            ip,
            ssot_path=f"{ip}/yaml/{ip}.ssot.yaml",
        )
        row = db.record_chat_message(
            ip_row["id"],
            user_id,
            content,
            display_name=args.display_name or user_id,
            workspace_id=workspace["id"],
            role=args.role,
        )
    print(row.get("id", ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
