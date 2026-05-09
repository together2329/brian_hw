#!/usr/bin/env python3
"""
Migrate existing JSON sessions to SQLite.

Reads old JSON files from ~/.common_ai_agent/sessions/ and inserts them
into the new SQLite database (core/atlas_db.py schema).
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.atlas_db import AtlasDB


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Migrate JSON sessions to SQLite"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and count, but do NOT write to SQLite",
    )
    parser.add_argument(
        "--source-dir",
        type=str,
        default=str(Path.home() / ".common_ai_agent" / "sessions"),
        help="Override source directory",
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default=str(Path.home() / ".common_ai_agent" / "atlas.db"),
        help="Override SQLite database path",
    )
    parser.add_argument(
        "--user-id",
        type=str,
        default="legacy",
        help="Assign specific user_id to all migrated sessions",
    )
    return parser.parse_args()


def load_json_file(path: Path) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f), None
    except Exception as exc:
        return None, f"{exc.__class__.__name__}: {exc}"


def discover_sessions(source_dir: Path) -> List[Path]:
    session_dir = source_dir / "session"
    if not session_dir.exists():
        return []
    return sorted(session_dir.glob("*.json"))


def discover_messages(source_dir: Path, session_id: str) -> List[Path]:
    msg_dir = source_dir / "message" / session_id
    if not msg_dir.exists():
        return []
    return sorted(msg_dir.glob("*.json"))


def discover_parts(source_dir: Path, message_id: str) -> List[Path]:
    part_dir = source_dir / "part" / message_id
    if not part_dir.exists():
        return []
    return sorted(part_dir.glob("*.json"))


def migrate_sessions(
    db: AtlasDB,
    source_dir: Path,
    user_id: str,
    dry_run: bool,
) -> Tuple[int, int, int, List[str], int, int]:
    sessions_found = 0
    sessions_migrated = 0
    messages_migrated = 0
    parts_migrated = 0
    errors: List[str] = []
    skipped = 0

    session_files = discover_sessions(source_dir)
    sessions_found = len(session_files)

    for sess_path in session_files:
        data, err = load_json_file(sess_path)
        if err:
            rel = sess_path.relative_to(source_dir) if str(sess_path).startswith(str(source_dir)) else sess_path.name
            errors.append(f"session/{Path(rel).name}: {err}")
            continue

        if data is None:
            skipped += 1
            continue

        sess_id = data.get("id")
        if not sess_id:
            errors.append(f"session/{sess_path.name}: missing 'id' field")
            skipped += 1
            continue

        if not dry_run:
            try:
                status = "archived" if data.get("archived_at") is not None else "active"
                summary_val = data.get("summary")

                db.import_session(
                    session_id=sess_id,
                    user_id=user_id,
                    project_id=data.get("project_id", ""),
                    directory=data.get("directory", ""),
                    title=data.get("title", ""),
                    status=status,
                    created_at=data.get("created_at"),
                    updated_at=data.get("updated_at"),
                    archived_at=data.get("archived_at"),
                    summary=summary_val,
                )
                sessions_migrated += 1
            except Exception as exc:
                errors.append(f"session/{sess_path.name}: {exc.__class__.__name__}: {exc}")
                continue
        else:
            sessions_migrated += 1

        msg_files = discover_messages(source_dir, sess_id)
        for msg_path in msg_files:
            msg_data, msg_err = load_json_file(msg_path)
            if msg_err:
                rel = msg_path.relative_to(source_dir) if str(msg_path).startswith(str(source_dir)) else msg_path.name
                errors.append(f"message/{rel}: {msg_err}")
                continue

            if msg_data is None:
                skipped += 1
                continue

            msg_id = msg_data.get("id")
            if not msg_id:
                errors.append(f"message/{msg_path.name}: missing 'id' field")
                skipped += 1
                continue

            if not dry_run:
                try:
                    tokens = msg_data.get("tokens", {}) or {}
                    error_val = msg_data.get("error")

                    db.import_message(
                        message_id=msg_id,
                        session_id=sess_id,
                        role=msg_data.get("role", ""),
                        agent=msg_data.get("agent", ""),
                        model_id=msg_data.get("model_id", ""),
                        provider_id=msg_data.get("provider_id", ""),
                        created_at=msg_data.get("created_at"),
                        completed_at=msg_data.get("completed_at"),
                        cost=float(msg_data.get("cost", 0.0)),
                        tokens_input=int(tokens.get("input", 0)),
                        tokens_output=int(tokens.get("output", 0)),
                        tokens_reasoning=int(tokens.get("reasoning", 0)),
                        error=error_val,
                    )
                    messages_migrated += 1
                except Exception as exc:
                    errors.append(f"message/{msg_path.name}: {exc.__class__.__name__}: {exc}")
                    continue
            else:
                messages_migrated += 1

            part_files = discover_parts(source_dir, msg_id)
            for part_path in part_files:
                part_data, part_err = load_json_file(part_path)
                if part_err:
                    rel = part_path.relative_to(source_dir) if str(part_path).startswith(str(source_dir)) else part_path.name
                    errors.append(f"part/{rel}: {part_err}")
                    continue

                if part_data is None:
                    skipped += 1
                    continue

                part_id = part_data.get("id")
                if not part_id:
                    errors.append(f"part/{part_path.name}: missing 'id' field")
                    skipped += 1
                    continue

                if not dry_run:
                    try:
                        step_tokens = part_data.get("step_tokens", {}) or {}
                        patch_files = part_data.get("patch_files")
                        tool_input = part_data.get("tool_input")

                        db.import_part(
                            part_id=part_id,
                            message_id=msg_id,
                            session_id=sess_id,
                            part_type=part_data.get("type", ""),
                            created_at=part_data.get("created_at"),
                            text=part_data.get("text"),
                            tool_name=part_data.get("tool_name"),
                            call_id=part_data.get("call_id"),
                            tool_status=part_data.get("tool_status", "pending"),
                            tool_input=tool_input,
                            tool_output=part_data.get("tool_output"),
                            tool_error=part_data.get("tool_error"),
                            tool_title=part_data.get("tool_title"),
                            start_time=part_data.get("start_time"),
                            end_time=part_data.get("end_time"),
                            compacted_at=part_data.get("compacted_at"),
                            snapshot_hash=part_data.get("snapshot_hash"),
                            patch_hash=part_data.get("patch_hash"),
                            patch_files=patch_files,
                            step_reason=part_data.get("step_reason"),
                            step_cost=float(part_data.get("step_cost", 0.0)) if part_data.get("step_cost") is not None else None,
                            step_tokens_input=int(step_tokens.get("input", 0)) if step_tokens else None,
                            step_tokens_output=int(step_tokens.get("output", 0)) if step_tokens else None,
                        )
                        parts_migrated += 1
                    except Exception as exc:
                        errors.append(f"part/{part_path.name}: {exc.__class__.__name__}: {exc}")
                        continue
                else:
                    parts_migrated += 1

    return sessions_found, sessions_migrated, messages_migrated, errors, skipped, parts_migrated


def print_report(
    source_dir: str,
    db_path: str,
    sessions_found: int,
    sessions_migrated: int,
    messages_migrated: int,
    parts_migrated: int,
    errors: List[str],
    skipped: int,
    dry_run: bool,
) -> None:
    prefix = "[DRY RUN] " if dry_run else ""
    print()
    print(f"{prefix}Session Migration Report")
    print("=" * max(24, len(prefix) + 24))
    print(f"Source: {source_dir}")
    print(f"Target: {db_path}")
    print(f"Sessions found: {sessions_found}")
    print(f"Sessions migrated: {sessions_migrated}")
    print(f"Messages migrated: {messages_migrated:,}")
    print(f"Parts migrated: {parts_migrated:,}")
    print(f"Errors: {len(errors)} (see details below)")
    print(f"Skipped: {skipped}")
    print()
    if errors:
        print("Errors:")
        for err in errors:
            print(f"  - {err}")
        print()
    print("Migration complete!")
    print()


def main() -> int:
    args = parse_args()
    source_dir = Path(args.source_dir).expanduser().resolve()
    db_path = Path(args.db_path).expanduser().resolve()
    user_id = args.user_id

    db: Optional[AtlasDB] = None
    if not args.dry_run:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        db = AtlasDB(str(db_path))
        db.init_db()
        db.import_user(
            user_id=user_id,
            username=user_id,
            display_name="Legacy Migrated User",
            role="user",
        )

    sessions_found, sessions_migrated, messages_migrated, errors, skipped, parts_migrated = migrate_sessions(
        db=db or AtlasDB(":memory:"),
        source_dir=source_dir,
        user_id=user_id,
        dry_run=args.dry_run,
    )

    print_report(
        source_dir=str(source_dir),
        db_path=str(db_path),
        sessions_found=sessions_found,
        sessions_migrated=sessions_migrated,
        messages_migrated=messages_migrated,
        parts_migrated=parts_migrated,
        errors=errors,
        skipped=skipped,
        dry_run=args.dry_run,
    )

    if db:
        db.close()

    return 0 if len(errors) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
