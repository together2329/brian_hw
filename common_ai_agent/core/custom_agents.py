"""
Reusable custom agent definitions.

Definitions are DB-backed and per Atlas user when an owner id is available.
Legacy file definitions under <project-root>/.atlas/custom_agents/*.json remain
available for project-local fallback/import-style use.
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, List, Optional


BASE_AGENTS = {"explore", "execute", "review"}
RESERVED_AGENT_NAMES = BASE_AGENTS | {"workflow", "task", "primary", "build", "orchestrator"}
_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,63}$")


@dataclass(frozen=True)
class CustomAgentDefinition:
    name: str
    base_agent: str
    system_prompt: str
    description: str = ""
    allowed_tools: Optional[List[str]] = None
    model: str = ""
    reasoning_effort: str = ""
    owner_user_id: str = ""
    scope: str = "private"
    id: str = ""
    created_at: float = 0.0
    updated_at: float = 0.0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CustomAgentDefinition":
        name = str(data.get("name", "")).strip()
        base_agent = str(data.get("base_agent", data.get("baseAgent", "explore"))).strip() or "explore"
        system_prompt = str(data.get("system_prompt", data.get("systemPrompt", ""))).strip()
        allowed_tools = parse_allowed_tools(data.get("allowed_tools", data.get("allowedTools")))
        return cls(
            name=name,
            base_agent=base_agent,
            system_prompt=system_prompt,
            description=str(data.get("description", "")).strip(),
            allowed_tools=allowed_tools,
            model=str(data.get("model", "")).strip(),
            reasoning_effort=str(
                data.get("reasoning_effort", data.get("reasoningEffort", data.get("effort", "")))
            ).strip(),
            owner_user_id=str(data.get("owner_user_id", data.get("ownerUserId", ""))).strip(),
            scope=str(data.get("scope", "private")).strip() or "private",
            id=str(data.get("id", "")).strip(),
            created_at=float(data.get("created_at") or data.get("createdAt") or 0.0),
            updated_at=float(data.get("updated_at") or data.get("updatedAt") or 0.0),
        )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        if self.allowed_tools is None:
            data["allowed_tools"] = None
        return data


def project_root(root: str | os.PathLike[str] | None = None) -> Path:
    if root:
        return Path(root).expanduser().resolve()
    env_root = (
        os.environ.get("ATLAS_PROJECT_ROOT")
        or os.environ.get("ATLAS_ROOT")
        or os.environ.get("COMMON_AI_AGENT_PROJECT_ROOT")
    )
    if env_root:
        return Path(env_root).expanduser().resolve()
    return Path.cwd().resolve()


def custom_agent_dir(root: str | os.PathLike[str] | None = None) -> Path:
    return project_root(root) / ".atlas" / "custom_agents"


def _atlas_db(db: Any = None):
    if db is not None:
        return db
    from core.atlas_db import AtlasDB

    return AtlasDB(os.environ.get("ATLAS_DB_PATH") or None)


def _resolve_user_candidate(candidate: str, db: Any = None) -> str:
    value = str(candidate or "").strip()
    if not value:
        return ""
    try:
        atlas = _atlas_db(db)
        user = atlas.get_user(value) or atlas.get_user_by_username(value)
        if user and user.get("id"):
            return str(user["id"])
    except Exception:
        return ""
    return ""


def current_owner_user_id(db: Any = None) -> str:
    """Best-effort current Atlas DB user id for tool/worker execution."""
    db_is_configured = bool(os.environ.get("ATLAS_DB_PATH")) or db is not None
    for key in ("ATLAS_USER_ID", "ATLAS_ACTIVE_USER_ID", "ATLAS_OWNER_USER_ID"):
        value = str(os.environ.get(key, "") or "").strip()
        if value:
            resolved = _resolve_user_candidate(value, db=db)
            if resolved:
                return resolved
            if db_is_configured:
                continue
            return value

    candidates = []
    active_user = str(os.environ.get("ATLAS_ACTIVE_USER", "") or "").strip()
    if active_user:
        candidates.append(active_user)
    memory_user = str(os.environ.get("ATLAS_MEMORY_USER", "") or "").strip()
    if memory_user:
        candidates.append(memory_user)
    session = str(os.environ.get("ATLAS_ACTIVE_SESSION", "") or "").strip().strip("/")
    if session:
        candidates.append(session.split("/", 1)[0])
    default_session = str(os.environ.get("ATLAS_DEFAULT_SESSION_ID", "") or "").strip()
    if default_session:
        candidates.append(default_session)

    if not candidates:
        return ""

    for candidate in candidates:
        resolved = _resolve_user_candidate(candidate, db=db)
        if resolved:
            return resolved
    return ""


def validate_agent_name(name: str, *, allow_reserved: bool = False) -> str:
    normalized = str(name or "").strip()
    if not _NAME_RE.match(normalized):
        raise ValueError("agent name must match [A-Za-z][A-Za-z0-9_-]{0,63}")
    if not allow_reserved and normalized in RESERVED_AGENT_NAMES:
        raise ValueError(f"'{normalized}' is reserved for built-in agents")
    return normalized


def validate_base_agent(base_agent: str) -> str:
    normalized = str(base_agent or "explore").strip() or "explore"
    if normalized not in BASE_AGENTS:
        raise ValueError(f"base_agent must be one of: {', '.join(sorted(BASE_AGENTS))}")
    return normalized


def parse_allowed_tools(value: Any) -> Optional[List[str]]:
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        if text.startswith("["):
            try:
                value = json.loads(text)
            except Exception:
                value = text
        if isinstance(value, str):
            parts = re.split(r"[\s,]+", value)
        else:
            parts = value
    elif isinstance(value, Iterable):
        parts = value
    else:
        parts = [value]

    tools: List[str] = []
    seen = set()
    for item in parts:
        tool = str(item or "").strip()
        if not tool:
            continue
        if tool not in seen:
            seen.add(tool)
            tools.append(tool)
    return tools or None


def save_custom_agent(
    *,
    name: str,
    system_prompt: str,
    base_agent: str = "explore",
    allowed_tools: Any = None,
    description: str = "",
    model: str = "",
    reasoning_effort: str = "",
    owner_user_id: str = "",
    scope: str = "private",
    db: Any = None,
    root: str | os.PathLike[str] | None = None,
) -> CustomAgentDefinition:
    agent_name = validate_agent_name(name)
    base = validate_base_agent(base_agent)
    prompt = str(system_prompt or "").strip()
    if not prompt:
        raise ValueError("system_prompt is required")

    owner = str(owner_user_id or "").strip()
    if owner:
        atlas = _atlas_db(db)
        row = atlas.upsert_custom_agent(
            owner_user_id=owner,
            name=agent_name,
            base_agent=base,
            system_prompt=prompt,
            allowed_tools=parse_allowed_tools(allowed_tools),
            model=model,
            reasoning_effort=reasoning_effort,
            description=description,
            scope=scope,
        )
        return CustomAgentDefinition.from_dict(row)

    now = time.time()
    path = custom_agent_dir(root)
    path.mkdir(parents=True, exist_ok=True)
    existing = load_custom_agent(agent_name, root=root)
    created_at = existing.created_at if existing else now
    definition = CustomAgentDefinition(
        name=agent_name,
        base_agent=base,
        system_prompt=prompt,
        description=str(description or "").strip(),
        allowed_tools=parse_allowed_tools(allowed_tools),
        model=str(model or "").strip(),
        reasoning_effort=str(reasoning_effort or "").strip(),
        created_at=created_at,
        updated_at=now,
    )
    target = path / f"{agent_name}.json"
    target.write_text(json.dumps(definition.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return definition


def load_custom_agent(
    name: str,
    *,
    owner_user_id: str = "",
    include_shared: bool = True,
    db: Any = None,
    root: str | os.PathLike[str] | None = None,
) -> Optional[CustomAgentDefinition]:
    try:
        agent_name = validate_agent_name(name, allow_reserved=True)
    except ValueError:
        return None
    owner = str(owner_user_id or "").strip()
    if owner:
        try:
            row = _atlas_db(db).get_custom_agent(owner, agent_name, include_shared=include_shared)
            if row:
                definition = CustomAgentDefinition.from_dict(row)
                validate_base_agent(definition.base_agent)
                if not definition.system_prompt:
                    raise ValueError(f"custom agent '{agent_name}' has an empty system_prompt")
                return definition
        except Exception:
            pass
        if os.environ.get("ATLAS_DB_PATH") or db is not None:
            return None
    target = custom_agent_dir(root) / f"{agent_name}.json"
    if not target.exists():
        return None
    data = json.loads(target.read_text(encoding="utf-8"))
    definition = CustomAgentDefinition.from_dict(data)
    validate_agent_name(definition.name, allow_reserved=True)
    validate_base_agent(definition.base_agent)
    if not definition.system_prompt:
        raise ValueError(f"custom agent '{agent_name}' has an empty system_prompt")
    return definition


def list_custom_agents(
    *,
    owner_user_id: str = "",
    include_shared: bool = True,
    db: Any = None,
    root: str | os.PathLike[str] | None = None,
) -> List[CustomAgentDefinition]:
    owner = str(owner_user_id or "").strip()
    if owner:
        try:
            rows = _atlas_db(db).list_custom_agents(owner, include_shared=include_shared)
            return [CustomAgentDefinition.from_dict(row) for row in rows]
        except Exception:
            pass
        if os.environ.get("ATLAS_DB_PATH") or db is not None:
            return []
    directory = custom_agent_dir(root)
    if not directory.exists():
        return []
    definitions: List[CustomAgentDefinition] = []
    for path in sorted(directory.glob("*.json")):
        try:
            definitions.append(load_custom_agent(path.stem, root=root))
        except Exception:
            continue
    return [d for d in definitions if d is not None]


def runtime_overrides_for_effort(reasoning_effort: str) -> dict[str, str]:
    effort = str(reasoning_effort or "").strip().lower()
    aliases = {
        "l": "low",
        "m": "medium",
        "med": "medium",
        "mid": "medium",
        "h": "high",
        "hi": "high",
        "x": "xhigh",
        "xh": "xhigh",
        "xhi": "xhigh",
        "max": "xhigh",
    }
    effort = aliases.get(effort, effort)
    if effort not in {"", "none", "low", "medium", "high", "xhigh"}:
        return {}
    if not effort:
        return {}
    return {
        "REASONING_MODE": effort,
        "REASONING_EFFORT": effort,
        "GLM_THINKING_TYPE": "disabled" if effort == "none" else "enabled",
    }


def as_public_dict(definition: CustomAgentDefinition) -> dict[str, Any]:
    data = definition.to_dict()
    prompt = data.get("system_prompt", "")
    data["system_prompt_preview"] = prompt[:240]
    data["system_prompt_chars"] = len(prompt)
    return data
