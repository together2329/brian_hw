"""
Session Management System (OpenCode-Inspired)

OpenCode의 세션 관리 장점을 도입:
1. 세션 저장/복원 (Session Storage)
2. 세션 컴팩션 (History Compression)
3. 스냅샷 기능 (Snapshot)
4. 복원 기능 (Revert)
5. 메시지/파트 구조

Zero-dependency: 표준 라이브러리만 사용
"""

import os
import json
import hashlib
import shutil
import tempfile
import time
import threading
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Callable, Literal, Union
from enum import Enum
from uuid import uuid4


# ============================================================
# Configuration
# ============================================================

# Default storage directory
DEFAULT_STORAGE_DIR = Path.home() / ".brian_coder" / "sessions"

# Compaction settings
PRUNE_MINIMUM_TOKENS = 20_000       # Minimum tokens to trigger pruning
PRUNE_PROTECT_TOKENS = 40_000       # Tokens to protect before pruning
PRUNE_PROTECTED_TOOLS = {"skill", "spawn_explore", "spawn_plan"}

# Token estimation (chars per token)
CHARS_PER_TOKEN = 4


# ============================================================
# Data Models
# ============================================================

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class PartType(str, Enum):
    TEXT = "text"
    TOOL = "tool"
    REASONING = "reasoning"
    STEP_START = "step_start"
    STEP_FINISH = "step_finish"
    PATCH = "patch"
    SNAPSHOT = "snapshot"
    COMPACTION = "compaction"


class ToolStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class TokenUsage:
    """Token usage tracking"""
    input: int = 0
    output: int = 0
    reasoning: int = 0
    cache_read: int = 0
    cache_write: int = 0

    def total(self) -> int:
        return self.input + self.output + self.reasoning


@dataclass
class SessionMetadata:
    """Session metadata"""
    id: str
    project_id: str = ""
    directory: str = ""
    parent_id: Optional[str] = None
    title: str = ""
    version: str = "1.0.0"
    created_at: float = field(default_factory=lambda: time.time())
    updated_at: float = field(default_factory=lambda: time.time())
    compacting_at: Optional[float] = None
    archived_at: Optional[float] = None

    # Summary information
    summary: Optional[Dict[str, Any]] = None

    # Revert state
    revert: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "directory": self.directory,
            "parent_id": self.parent_id,
            "title": self.title,
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "compacting_at": self.compacting_at,
            "archived_at": self.archived_at,
            "summary": self.summary,
            "revert": self.revert
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionMetadata':
        return cls(
            id=data["id"],
            project_id=data.get("project_id", ""),
            directory=data.get("directory", ""),
            parent_id=data.get("parent_id"),
            title=data.get("title", ""),
            version=data.get("version", "1.0.0"),
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time()),
            compacting_at=data.get("compacting_at"),
            archived_at=data.get("archived_at"),
            summary=data.get("summary"),
            revert=data.get("revert")
        )


@dataclass
class MessageInfo:
    """Message information"""
    id: str
    session_id: str
    role: str
    agent: str = ""
    model_id: str = ""
    provider_id: str = ""
    created_at: float = field(default_factory=lambda: time.time())
    completed_at: Optional[float] = None
    cost: float = 0.0
    tokens: TokenUsage = field(default_factory=TokenUsage)
    error: Optional[Dict[str, Any]] = None
    summary: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "role": self.role,
            "agent": self.agent,
            "model_id": self.model_id,
            "provider_id": self.provider_id,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "cost": self.cost,
            "tokens": asdict(self.tokens),
            "error": self.error,
            "summary": self.summary
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MessageInfo':
        tokens_data = data.get("tokens", {})
        return cls(
            id=data["id"],
            session_id=data["session_id"],
            role=data["role"],
            agent=data.get("agent", ""),
            model_id=data.get("model_id", ""),
            provider_id=data.get("provider_id", ""),
            created_at=data.get("created_at", time.time()),
            completed_at=data.get("completed_at"),
            cost=data.get("cost", 0.0),
            tokens=TokenUsage(**tokens_data) if tokens_data else TokenUsage(),
            error=data.get("error"),
            summary=data.get("summary")
        )


@dataclass
class Part:
    """Message part (text, tool call, etc.)"""
    id: str
    message_id: str
    session_id: str
    type: str
    created_at: float = field(default_factory=lambda: time.time())

    # Text content
    text: str = ""

    # Tool information
    tool_name: str = ""
    call_id: str = ""
    tool_status: str = "pending"
    tool_input: Optional[Dict[str, Any]] = None
    tool_output: Optional[str] = None
    tool_error: Optional[str] = None
    tool_title: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    compacted_at: Optional[float] = None

    # Snapshot information
    snapshot_hash: Optional[str] = None

    # Patch information
    patch_hash: Optional[str] = None
    patch_files: List[str] = field(default_factory=list)

    # Step information
    step_reason: str = ""
    step_cost: float = 0.0
    step_tokens: Optional[TokenUsage] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "id": self.id,
            "message_id": self.message_id,
            "session_id": self.session_id,
            "type": self.type,
            "created_at": self.created_at
        }

        if self.type == PartType.TEXT.value:
            result["text"] = self.text

        elif self.type == PartType.TOOL.value:
            result.update({
                "tool_name": self.tool_name,
                "call_id": self.call_id,
                "tool_status": self.tool_status,
                "tool_input": self.tool_input,
                "tool_output": self.tool_output,
                "tool_error": self.tool_error,
                "tool_title": self.tool_title,
                "start_time": self.start_time,
                "end_time": self.end_time,
                "compacted_at": self.compacted_at
            })

        elif self.type == PartType.SNAPSHOT.value:
            result["snapshot_hash"] = self.snapshot_hash

        elif self.type == PartType.PATCH.value:
            result["patch_hash"] = self.patch_hash
            result["patch_files"] = self.patch_files

        elif self.type in (PartType.STEP_START.value, PartType.STEP_FINISH.value):
            result["snapshot_hash"] = self.snapshot_hash
            result["step_reason"] = self.step_reason
            result["step_cost"] = self.step_cost
            if self.step_tokens:
                result["step_tokens"] = asdict(self.step_tokens)

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Part':
        step_tokens = None
        if data.get("step_tokens"):
            step_tokens = TokenUsage(**data["step_tokens"])

        return cls(
            id=data["id"],
            message_id=data["message_id"],
            session_id=data["session_id"],
            type=data["type"],
            created_at=data.get("created_at", time.time()),
            text=data.get("text", ""),
            tool_name=data.get("tool_name", ""),
            call_id=data.get("call_id", ""),
            tool_status=data.get("tool_status", "pending"),
            tool_input=data.get("tool_input"),
            tool_output=data.get("tool_output"),
            tool_error=data.get("tool_error"),
            tool_title=data.get("tool_title"),
            start_time=data.get("start_time"),
            end_time=data.get("end_time"),
            compacted_at=data.get("compacted_at"),
            snapshot_hash=data.get("snapshot_hash"),
            patch_hash=data.get("patch_hash"),
            patch_files=data.get("patch_files", []),
            step_reason=data.get("step_reason", ""),
            step_cost=data.get("step_cost", 0.0),
            step_tokens=step_tokens
        )


@dataclass
class MessageWithParts:
    """Message with all its parts"""
    info: MessageInfo
    parts: List[Part] = field(default_factory=list)


# ============================================================
# Session Storage
# ============================================================

class SessionStorage:
    """
    Thread-safe session storage using JSON files.

    Directory structure:
    storage_dir/
    ├── session/{session_id}.json        # Session metadata
    ├── message/{session_id}/{msg_id}.json   # Messages
    └── part/{msg_id}/{part_id}.json     # Parts
    """

    def __init__(self, storage_dir: Path = None):
        self.storage_dir = storage_dir or DEFAULT_STORAGE_DIR
        self.storage_dir = Path(self.storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._locks: Dict[str, threading.RLock] = {}
        self._global_lock = threading.RLock()

    def _get_lock(self, key: str) -> threading.RLock:
        """Get or create lock for a key"""
        with self._global_lock:
            if key not in self._locks:
                self._locks[key] = threading.RLock()
            return self._locks[key]

    def _path(self, *parts: str) -> Path:
        """Build path from parts"""
        return self.storage_dir.joinpath(*parts)

    def _read_json(self, path: Path) -> Dict[str, Any]:
        """Thread-safe JSON read"""
        lock = self._get_lock(str(path))
        with lock:
            if not path.exists():
                raise FileNotFoundError(f"Not found: {path}")
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)

    def _write_json(self, path: Path, data: Dict[str, Any]):
        """Thread-safe atomic JSON write"""
        lock = self._get_lock(str(path))
        with lock:
            path.parent.mkdir(parents=True, exist_ok=True)
            # Atomic write using temp file
            fd, temp_path = tempfile.mkstemp(
                dir=path.parent,
                suffix='.tmp'
            )
            try:
                with os.fdopen(fd, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                Path(temp_path).replace(path)
            except Exception:
                Path(temp_path).unlink(missing_ok=True)
                raise

    def _delete(self, path: Path):
        """Thread-safe delete"""
        lock = self._get_lock(str(path))
        with lock:
            if path.exists():
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()

    # ============ Session Operations ============

    def create_session(
        self,
        project_id: str = "",
        directory: str = "",
        parent_id: str = None,
        title: str = ""
    ) -> SessionMetadata:
        """Create a new session"""
        session = SessionMetadata(
            id=str(uuid4()),
            project_id=project_id,
            directory=directory or str(Path.cwd()),
            parent_id=parent_id,
            title=title or f"Session {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        self.save_session(session)
        return session

    def save_session(self, session: SessionMetadata):
        """Save session metadata"""
        path = self._path("session", f"{session.id}.json")
        self._write_json(path, session.to_dict())

    def get_session(self, session_id: str) -> Optional[SessionMetadata]:
        """Get session by ID"""
        try:
            path = self._path("session", f"{session_id}.json")
            data = self._read_json(path)
            return SessionMetadata.from_dict(data)
        except FileNotFoundError:
            return None

    def update_session(
        self,
        session_id: str,
        updater: Callable[[SessionMetadata], None]
    ) -> SessionMetadata:
        """Update session with a function"""
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        session.updated_at = time.time()
        updater(session)
        self.save_session(session)
        return session

    def list_sessions(self, project_id: str = None) -> List[SessionMetadata]:
        """List all sessions, optionally filtered by project"""
        sessions = []
        session_dir = self._path("session")
        if not session_dir.exists():
            return sessions

        for file in session_dir.glob("*.json"):
            try:
                data = self._read_json(file)
                session = SessionMetadata.from_dict(data)
                if project_id is None or session.project_id == project_id:
                    sessions.append(session)
            except Exception:
                continue

        # Sort by updated_at descending
        sessions.sort(key=lambda s: s.updated_at, reverse=True)
        return sessions

    def delete_session(self, session_id: str):
        """Delete session and all its data"""
        # Delete messages
        msg_dir = self._path("message", session_id)
        self._delete(msg_dir)

        # Delete session file
        session_path = self._path("session", f"{session_id}.json")
        self._delete(session_path)

    # ============ Message Operations ============

    def save_message(self, message: MessageInfo):
        """Save message"""
        path = self._path("message", message.session_id, f"{message.id}.json")
        self._write_json(path, message.to_dict())

    def get_message(self, session_id: str, message_id: str) -> Optional[MessageInfo]:
        """Get message by ID"""
        try:
            path = self._path("message", session_id, f"{message_id}.json")
            data = self._read_json(path)
            return MessageInfo.from_dict(data)
        except FileNotFoundError:
            return None

    def update_message(
        self,
        session_id: str,
        message_id: str,
        updater: Callable[[MessageInfo], None]
    ) -> MessageInfo:
        """Update message with a function"""
        message = self.get_message(session_id, message_id)
        if not message:
            raise ValueError(f"Message not found: {message_id}")
        updater(message)
        self.save_message(message)
        return message

    def list_messages(self, session_id: str) -> List[MessageWithParts]:
        """List all messages in a session with their parts"""
        messages = []
        msg_dir = self._path("message", session_id)
        if not msg_dir.exists():
            return messages

        for file in sorted(msg_dir.glob("*.json")):
            try:
                data = self._read_json(file)
                info = MessageInfo.from_dict(data)
                parts = self.list_parts(info.id)
                messages.append(MessageWithParts(info=info, parts=parts))
            except Exception:
                continue

        # Sort by created_at
        messages.sort(key=lambda m: m.info.created_at)
        return messages

    def delete_message(self, session_id: str, message_id: str):
        """Delete message and its parts"""
        # Delete parts directory
        parts_dir = self._path("part", message_id)
        self._delete(parts_dir)

        # Delete message file
        msg_path = self._path("message", session_id, f"{message_id}.json")
        self._delete(msg_path)

    # ============ Part Operations ============

    def save_part(self, part: Part):
        """Save part"""
        path = self._path("part", part.message_id, f"{part.id}.json")
        self._write_json(path, part.to_dict())

    def get_part(self, message_id: str, part_id: str) -> Optional[Part]:
        """Get part by ID"""
        try:
            path = self._path("part", message_id, f"{part_id}.json")
            data = self._read_json(path)
            return Part.from_dict(data)
        except FileNotFoundError:
            return None

    def update_part(
        self,
        message_id: str,
        part_id: str,
        updater: Callable[[Part], None]
    ) -> Part:
        """Update part with a function"""
        part = self.get_part(message_id, part_id)
        if not part:
            raise ValueError(f"Part not found: {part_id}")
        updater(part)
        self.save_part(part)
        return part

    def list_parts(self, message_id: str) -> List[Part]:
        """List all parts for a message"""
        parts = []
        parts_dir = self._path("part", message_id)
        if not parts_dir.exists():
            return parts

        for file in sorted(parts_dir.glob("*.json")):
            try:
                data = self._read_json(file)
                parts.append(Part.from_dict(data))
            except Exception:
                continue

        # Sort by created_at
        parts.sort(key=lambda p: p.created_at)
        return parts

    def delete_part(self, message_id: str, part_id: str):
        """Delete a part"""
        path = self._path("part", message_id, f"{part_id}.json")
        self._delete(path)


# ============================================================
# Snapshot Manager
# ============================================================

class SnapshotManager:
    """
    Manages file system snapshots for session revert.
    Uses git-like hash-based tracking.
    """

    def __init__(self, work_dir: Path = None, snapshot_dir: Path = None):
        self.work_dir = work_dir or Path.cwd()
        self.snapshot_dir = snapshot_dir or (DEFAULT_STORAGE_DIR / "snapshots")
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)

    def _hash_file(self, path: Path) -> str:
        """Calculate SHA256 hash of file"""
        hasher = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)
        return hasher.hexdigest()

    def _hash_content(self, content: bytes) -> str:
        """Calculate SHA256 hash of content"""
        return hashlib.sha256(content).hexdigest()

    def track(self, files: List[str] = None) -> str:
        """
        Create a snapshot of current file states.
        Returns snapshot hash.
        """
        snapshot = {
            "timestamp": time.time(),
            "files": {}
        }

        # If specific files provided, track those
        # Otherwise track all modified files in work_dir
        if files:
            for file_path in files:
                full_path = Path(file_path)
                if not full_path.is_absolute():
                    full_path = self.work_dir / file_path
                if full_path.exists():
                    snapshot["files"][str(file_path)] = {
                        "hash": self._hash_file(full_path),
                        "size": full_path.stat().st_size
                    }

        # Generate snapshot hash
        snapshot_content = json.dumps(snapshot, sort_keys=True).encode()
        snapshot_hash = self._hash_content(snapshot_content)[:16]

        # Save snapshot
        snapshot_path = self.snapshot_dir / f"{snapshot_hash}.json"
        with open(snapshot_path, 'w') as f:
            json.dump(snapshot, f, indent=2)

        return snapshot_hash

    def get_snapshot(self, snapshot_hash: str) -> Optional[Dict[str, Any]]:
        """Get snapshot data"""
        snapshot_path = self.snapshot_dir / f"{snapshot_hash}.json"
        if not snapshot_path.exists():
            return None
        with open(snapshot_path, 'r') as f:
            return json.load(f)

    def diff(self, from_hash: str, to_hash: str = None) -> List[Dict[str, Any]]:
        """
        Calculate diff between two snapshots.
        If to_hash is None, compares with current state.
        """
        from_snapshot = self.get_snapshot(from_hash)
        if not from_snapshot:
            return []

        diffs = []

        if to_hash:
            to_snapshot = self.get_snapshot(to_hash)
            if not to_snapshot:
                return []
            to_files = to_snapshot.get("files", {})
        else:
            to_files = {}
            for file_path, info in from_snapshot.get("files", {}).items():
                full_path = Path(file_path)
                if not full_path.is_absolute():
                    full_path = self.work_dir / file_path
                if full_path.exists():
                    to_files[file_path] = {
                        "hash": self._hash_file(full_path),
                        "size": full_path.stat().st_size
                    }

        # Compare files
        all_files = set(from_snapshot.get("files", {}).keys()) | set(to_files.keys())

        for file_path in all_files:
            from_info = from_snapshot.get("files", {}).get(file_path)
            to_info = to_files.get(file_path)

            if from_info and not to_info:
                # File deleted
                diffs.append({
                    "file": file_path,
                    "action": "deleted"
                })
            elif to_info and not from_info:
                # File added
                diffs.append({
                    "file": file_path,
                    "action": "added"
                })
            elif from_info["hash"] != to_info["hash"]:
                # File modified
                diffs.append({
                    "file": file_path,
                    "action": "modified"
                })

        return diffs


# ============================================================
# Session Compactor
# ============================================================

class SessionCompactor:
    """
    Compacts session history to reduce token usage.
    Removes old tool outputs while preserving essential information.
    """

    def __init__(self, storage: SessionStorage, llm_call_func: Callable = None):
        self.storage = storage
        self.llm_call_func = llm_call_func

    def estimate_tokens(self, text: str) -> int:
        """Estimate tokens from text"""
        return len(text) // CHARS_PER_TOKEN

    def is_overflow(
        self,
        tokens: TokenUsage,
        context_limit: int = 128000,
        output_limit: int = 8000
    ) -> bool:
        """Check if context window is exceeded"""
        usable = context_limit - output_limit
        used = tokens.input + tokens.cache_read + tokens.output
        return used > usable

    def prune_session(self, session_id: str) -> int:
        """
        Prune tool outputs from old messages.
        Returns number of tokens pruned.
        """
        messages = self.storage.list_messages(session_id)
        messages.reverse()  # Start from most recent

        total_tokens = 0
        pruned_tokens = 0
        to_prune: List[Part] = []
        turns = 0

        for msg in messages:
            if msg.info.role == MessageRole.USER.value:
                turns += 1

            # Protect last 2 turns
            if turns < 2:
                continue

            # Stop at summary message
            if msg.info.summary:
                break

            for part in reversed(msg.parts):
                if (part.type == PartType.TOOL.value and
                    part.tool_status == ToolStatus.COMPLETED.value):

                    # Skip protected tools
                    if part.tool_name in PRUNE_PROTECTED_TOOLS:
                        continue

                    # Skip already compacted
                    if part.compacted_at:
                        break

                    # Estimate tokens
                    output_text = part.tool_output or ""
                    estimate = self.estimate_tokens(output_text)
                    total_tokens += estimate

                    if total_tokens > PRUNE_PROTECT_TOKENS:
                        pruned_tokens += estimate
                        to_prune.append(part)

        # Apply pruning
        if pruned_tokens > PRUNE_MINIMUM_TOKENS:
            for part in to_prune:
                self.storage.update_part(
                    part.message_id,
                    part.id,
                    lambda p: setattr(p, 'compacted_at', time.time())
                )
            return pruned_tokens

        return 0

    def generate_summary(self, session_id: str) -> str:
        """
        Generate a summary prompt for continuing conversation.
        """
        if not self.llm_call_func:
            return ""

        messages = self.storage.list_messages(session_id)

        # Format messages for LLM
        formatted = []
        for msg in messages:
            content = ""
            for part in msg.parts:
                if part.type == PartType.TEXT.value:
                    content += part.text
                elif part.type == PartType.TOOL.value:
                    content += f"\n[Tool: {part.tool_name}]\n"
                    if part.tool_output and not part.compacted_at:
                        content += f"Output: {part.tool_output[:500]}...\n"

            formatted.append({
                "role": msg.info.role,
                "content": content
            })

        # Add summary request
        formatted.append({
            "role": "user",
            "content": """
Provide a detailed prompt for continuing our conversation above.
Focus on information that would be helpful for continuing the
conversation, including:
- What we did
- What we're doing
- Which files we're working on
- What we're going to do next
(important: new session will not have access to our conversation)
            """.strip()
        })

        # Call LLM
        try:
            response = self.llm_call_func(formatted)
            return response
        except Exception as e:
            return f"Error generating summary: {e}"


# ============================================================
# Session Reverter
# ============================================================

class SessionReverter:
    """
    Handles session revert functionality.
    Allows rolling back to a previous state.
    """

    def __init__(
        self,
        storage: SessionStorage,
        snapshot_manager: SnapshotManager
    ):
        self.storage = storage
        self.snapshot = snapshot_manager

    def revert_to_message(
        self,
        session_id: str,
        message_id: str,
        part_id: str = None
    ) -> bool:
        """
        Mark session for revert to a specific message/part.
        Returns True if revert state was set.
        """
        messages = self.storage.list_messages(session_id)

        revert_info = {
            "message_id": message_id,
            "part_id": part_id
        }

        # Find revert point
        found = False
        patches = []

        for msg in messages:
            if not found:
                if msg.info.id == message_id:
                    found = True
                    if part_id:
                        # Find specific part
                        for i, part in enumerate(msg.parts):
                            if part.id == part_id:
                                break
            else:
                # Collect patches after revert point
                for part in msg.parts:
                    if part.type == PartType.PATCH.value:
                        patches.append(part.patch_files)

        if not found:
            return False

        # Save current state as snapshot
        all_files = [f for patch in patches for f in patch]
        if all_files:
            revert_info["snapshot"] = self.snapshot.track(all_files)

        # Update session with revert state
        self.storage.update_session(
            session_id,
            lambda s: setattr(s, 'revert', revert_info)
        )

        return True

    def cleanup_revert(self, session_id: str) -> bool:
        """
        Confirm revert by deleting all messages after revert point.
        """
        session = self.storage.get_session(session_id)
        if not session or not session.revert:
            return False

        messages = self.storage.list_messages(session_id)
        revert_message_id = session.revert["message_id"]

        # Find split point
        preserve_count = 0
        for i, msg in enumerate(messages):
            if msg.info.id == revert_message_id:
                preserve_count = i + 1
                break

        # Delete messages after revert point
        for msg in messages[preserve_count:]:
            self.storage.delete_message(session_id, msg.info.id)

        # Handle part-level revert
        if session.revert.get("part_id") and preserve_count > 0:
            last_msg = messages[preserve_count - 1]
            part_id = session.revert["part_id"]

            found = False
            for part in last_msg.parts:
                if found:
                    self.storage.delete_part(last_msg.info.id, part.id)
                if part.id == part_id:
                    found = True

        # Clear revert state
        self.storage.update_session(
            session_id,
            lambda s: setattr(s, 'revert', None)
        )

        return True

    def cancel_revert(self, session_id: str) -> bool:
        """Cancel revert operation"""
        session = self.storage.get_session(session_id)
        if not session or not session.revert:
            return False

        self.storage.update_session(
            session_id,
            lambda s: setattr(s, 'revert', None)
        )
        return True


# ============================================================
# Session Manager (Main Interface)
# ============================================================

class SessionManager:
    """
    Main session management interface.
    Combines storage, compaction, and revert functionality.
    """

    _instance = None

    def __new__(cls, storage_dir: Path = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, storage_dir: Path = None):
        if self._initialized:
            return

        self.storage = SessionStorage(storage_dir)
        self.snapshot = SnapshotManager()
        self.compactor = SessionCompactor(self.storage)
        self.reverter = SessionReverter(self.storage, self.snapshot)

        self._current_session_id: Optional[str] = None
        self._initialized = True

    # ============ Session Operations ============

    def create_session(self, **kwargs) -> SessionMetadata:
        """Create a new session"""
        return self.storage.create_session(**kwargs)

    def get_session(self, session_id: str) -> Optional[SessionMetadata]:
        """Get session by ID"""
        return self.storage.get_session(session_id)

    def list_sessions(self, **kwargs) -> List[SessionMetadata]:
        """List all sessions"""
        return self.storage.list_sessions(**kwargs)

    def delete_session(self, session_id: str):
        """Delete a session"""
        self.storage.delete_session(session_id)

    @property
    def current_session(self) -> Optional[SessionMetadata]:
        """Get current active session"""
        if self._current_session_id:
            return self.storage.get_session(self._current_session_id)
        return None

    def set_current_session(self, session_id: str):
        """Set current active session"""
        self._current_session_id = session_id

    # ============ Message Operations ============

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str = "",
        agent: str = "",
        model_id: str = "",
        provider_id: str = ""
    ) -> MessageInfo:
        """Add a message to a session"""
        message = MessageInfo(
            id=str(uuid4()),
            session_id=session_id,
            role=role,
            agent=agent,
            model_id=model_id,
            provider_id=provider_id
        )
        self.storage.save_message(message)

        # Add text part if content provided
        if content:
            part = Part(
                id=str(uuid4()),
                message_id=message.id,
                session_id=session_id,
                type=PartType.TEXT.value,
                text=content
            )
            self.storage.save_part(part)

        # Update session timestamp
        self.storage.update_session(
            session_id,
            lambda s: setattr(s, 'updated_at', time.time())
        )

        return message

    def add_tool_call(
        self,
        message_id: str,
        session_id: str,
        tool_name: str,
        call_id: str,
        tool_input: Dict[str, Any]
    ) -> Part:
        """Add a tool call part"""
        part = Part(
            id=str(uuid4()),
            message_id=message_id,
            session_id=session_id,
            type=PartType.TOOL.value,
            tool_name=tool_name,
            call_id=call_id,
            tool_status=ToolStatus.RUNNING.value,
            tool_input=tool_input,
            start_time=time.time()
        )
        self.storage.save_part(part)
        return part

    def complete_tool_call(
        self,
        message_id: str,
        part_id: str,
        output: str,
        title: str = "",
        error: str = None
    ):
        """Complete a tool call"""
        self.storage.update_part(
            message_id,
            part_id,
            lambda p: (
                setattr(p, 'tool_status', ToolStatus.ERROR.value if error else ToolStatus.COMPLETED.value),
                setattr(p, 'tool_output', output if not error else None),
                setattr(p, 'tool_error', error),
                setattr(p, 'tool_title', title),
                setattr(p, 'end_time', time.time())
            )
        )

    def get_messages(self, session_id: str) -> List[MessageWithParts]:
        """Get all messages in a session"""
        return self.storage.list_messages(session_id)

    # ============ Compaction ============

    def prune_session(self, session_id: str) -> int:
        """Prune old tool outputs"""
        return self.compactor.prune_session(session_id)

    def generate_summary(self, session_id: str) -> str:
        """Generate session summary for continuation"""
        return self.compactor.generate_summary(session_id)

    # ============ Revert ============

    def revert_to(
        self,
        session_id: str,
        message_id: str,
        part_id: str = None
    ) -> bool:
        """Mark session for revert"""
        return self.reverter.revert_to_message(session_id, message_id, part_id)

    def confirm_revert(self, session_id: str) -> bool:
        """Confirm and execute revert"""
        return self.reverter.cleanup_revert(session_id)

    def cancel_revert(self, session_id: str) -> bool:
        """Cancel pending revert"""
        return self.reverter.cancel_revert(session_id)

    # ============ Snapshot ============

    def create_snapshot(self, files: List[str] = None) -> str:
        """Create a snapshot of current state"""
        return self.snapshot.track(files)

    def get_diff(self, from_hash: str, to_hash: str = None) -> List[Dict]:
        """Get diff between snapshots"""
        return self.snapshot.diff(from_hash, to_hash)


# ============================================================
# Convenience Functions
# ============================================================

def get_session_manager(storage_dir: Path = None) -> SessionManager:
    """Get or create SessionManager singleton"""
    return SessionManager(storage_dir)


def create_session(**kwargs) -> SessionMetadata:
    """Create a new session"""
    return get_session_manager().create_session(**kwargs)


def list_sessions(**kwargs) -> List[SessionMetadata]:
    """List all sessions"""
    return get_session_manager().list_sessions(**kwargs)
