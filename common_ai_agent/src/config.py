import os
import sys
from pathlib import Path

# Keep top-level `config` and package `src.config` as one live module. The
# app is intentionally runnable both as `python src/textual_main.py` and via
# package imports; without this alias, runtime provider switches can update
# one config object while llm_client reads another.
if __name__ == "config":
    sys.modules.setdefault("src.config", sys.modules[__name__])
elif __name__ == "src.config":
    sys.modules.setdefault("config", sys.modules[__name__])


def _apply_workspace_env_early():
    """
    Parse -w/--workflow/--workspace from sys.argv BEFORE load_env_file() runs,
    so workspace.json [env] overrides have priority over .env/.config files.
    Only sets env vars that are not already set in the shell environment.
    """
    workspace_name = None
    argv = sys.argv[1:]
    for i, arg in enumerate(argv):
        if arg in ('-w', '-wf', '--workflow', '--workspace') and i + 1 < len(argv):
            workspace_name = argv[i + 1]
            break
        if arg.startswith('--workflow=') or arg.startswith('--workspace='):
            workspace_name = arg.split('=', 1)[1]
            break
    if not workspace_name:
        return

    # Locate workflow directory relative to this file (src/ → .. → workflow/)
    workflow_root = Path(__file__).parent.parent.parent / "new_feature" / "workflow"
    ws_json = workflow_root / workspace_name / "workspace.json"
    if not ws_json.exists():
        # Fallback: look for workflow/ next to common_ai_agent
        workflow_root2 = Path(__file__).parent.parent / "workflow"
        ws_json = workflow_root2 / workspace_name / "workspace.json"
    if not ws_json.exists():
        return

    try:
        import json
        data = json.loads(ws_json.read_text(encoding="utf-8"))
        env_overrides = data.get("env", {})
        for key, value in env_overrides.items():
            if key and value is not None and key not in os.environ:
                os.environ[key] = str(value)
        # Signal which workspace is active
        if "ACTIVE_WORKSPACE" not in os.environ:
            os.environ["ACTIVE_WORKSPACE"] = workspace_name
    except Exception:
        pass


_apply_workspace_env_early()
_INITIAL_ENV_KEYS = frozenset(os.environ)

# ── .env loading + hot reload ─────────────────────────────────────────────
# Two failure modes are addressed here:
#   1. First-load: shell-set vars must NOT be clobbered by .env
#      → force_reload=False keeps existing os.environ values.
#   2. Hot reload: when the user edits .env mid-session, os.environ still
#      holds the old values. force_reload=True overwrites them so
#      reload_env() can pick the edits up without restarting the process.
# Session/runtime keys (workspace, etc.) are protected from overwrite —
# editing .env should never silently switch the active workspace.

# .env-derived keys that runtime mutates and should NOT be force-restored
# from .env on hot reload. ACTIVE_WORKSPACE in particular is set by the
# CLI -w flag and survives /workspace switches.
_PROTECTED_ENV_KEYS = frozenset({
    'ACTIVE_WORKSPACE', 'WORKSPACE', 'ACTIVE_PROJECT',
})

_ALLOW_EMPTY_ENV_KEYS = frozenset({
    'LLM_MODEL_NAME_2', 'LLM_MODEL_NAME_3',
    'LLM_BASE_NAME_2', 'LLM_BASE_NAME_3',
    'LLM_BASE_MODEL_2', 'LLM_BASE_MODEL_3',
})

_MODEL_DROPDOWN_KEYS = ('LLM_MODEL_NAME', 'LLM_MODEL_NAME_2', 'LLM_MODEL_NAME_3')
_BASE_MODEL_DROPDOWN_KEYS = ('LLM_BASE_NAME', 'LLM_BASE_NAME_2', 'LLM_BASE_NAME_3')
_LEGACY_MODEL_DROPDOWN_KEYS = ('LLM_BASE_MODEL', 'LLM_BASE_MODEL_2', 'LLM_BASE_MODEL_3')

# mtime cache: path -> last seen mtime. reload_env() only does I/O when at
# least one .env file has changed since the previous successful reload.
_ENV_MTIME_CACHE: dict = {}


def _env_search_paths() -> list:
    """Return the .env / .config search paths in priority order.

    First entry has highest precedence — but precedence is enforced via
    "first writer wins" (once os.environ has a key, later files don't
    overwrite). On force_reload=True the LAST writer wins so later edits
    in the project-local .env override stale ~/.config values.
    """
    return [
        Path.home() / '.config' / 'common_ai_agent' / 'config',
        Path(__file__).parent.parent / '.config',
        Path(__file__).parent.parent / '.env',
        Path(__file__).parent / '.env',
    ]


def load_env_file(force_reload: bool = False):
    """Read .env / .config files into os.environ.

    force_reload=False: only set keys not already present (boot-time;
    preserves shell-supplied values).
    force_reload=True: overwrite existing os.environ with the latest
    .env value, except for keys in _PROTECTED_ENV_KEYS.
    """
    for env_path in _env_search_paths():
        if not env_path.exists():
            continue
        try:
            with open(env_path, encoding='utf-8') as f:
                lines = f.readlines()
        except OSError:
            continue
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' not in line:
                continue
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()
            if '#' in value:
                value = value.split('#')[0].strip()
            if not key or (not value and key not in _ALLOW_EMPTY_ENV_KEYS):
                continue
            if key in _PROTECTED_ENV_KEYS:
                continue
            if force_reload or key not in os.environ:
                os.environ[key] = value


def _env_bool(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in ("true", "1", "yes", "on")


def _source_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _resolve_source_path(value: str) -> str:
    raw = os.path.expandvars(os.path.expanduser(str(value or "").strip()))
    if not raw:
        return ""
    path = Path(raw)
    if not path.is_absolute():
        path = _source_root() / path
    return str(path.resolve(strict=False))


def _first_readable(paths: list[Path]) -> Path:
    for path in paths:
        if path.is_file() and os.access(path, os.R_OK):
            return path
    return paths[0] if paths else Path()


def _resolve_pdk_env_defaults() -> None:
    """Populate PDK env vars from common_ai_agent/pdk when not explicit."""
    root = _resolve_source_path(os.getenv("PDK_ROOT") or "pdk")
    os.environ["PDK_ROOT"] = root

    sky130_root_raw = os.getenv("SKY130_PDK_ROOT", "").strip()
    if sky130_root_raw:
        sky130_root = _resolve_source_path(sky130_root_raw)
    else:
        sky130_root = str((Path(root) / "sky130").resolve(strict=False))
    os.environ["SKY130_PDK_ROOT"] = sky130_root

    sky130 = Path(sky130_root)
    lib_dir = sky130 / "lib"
    lib_default = _first_readable([
        lib_dir / "sky130_fd_sc_hd__ss_100C_1v40.lib",
        lib_dir / "sky130_fd_sc_hd__ss_n40C_1v40.lib",
        *sorted(lib_dir.glob("*.lib")),
    ])
    defaults = {
        "PDK_LIB_PATH": lib_dir,
        "SKY130_LIB": lib_default,
        "SKY130_TLEF": sky130 / "lef" / "sky130_fd_sc_hd.tlef",
        "SKY130_LEF": sky130 / "lef" / "sky130_fd_sc_hd_merged.lef",
        "SKY130_TRACKS": sky130 / "make_tracks.tcl",
        "SKY130_RCX_RULES": sky130 / "rcx_patterns.rules",
    }
    for key, default in defaults.items():
        raw = os.getenv(key, "").strip()
        os.environ[key] = _resolve_source_path(raw) if raw else str(Path(default).resolve(strict=False))


def pdk_status() -> dict:
    """Return resolved PDK paths and readability for UI/debug surfaces."""
    _resolve_pdk_env_defaults()
    keys = (
        "PDK_ROOT",
        "SKY130_PDK_ROOT",
        "PDK_LIB_PATH",
        "SKY130_LIB",
        "SKY130_TLEF",
        "SKY130_LEF",
        "SKY130_TRACKS",
        "SKY130_RCX_RULES",
    )
    paths: dict[str, dict[str, object]] = {}
    for key in keys:
        raw = os.getenv(key, "")
        path = Path(raw) if raw else Path()
        paths[key] = {
            "path": raw,
            "exists": path.exists() if raw else False,
            "readable": path.is_file() and os.access(path, os.R_OK) if raw else False,
            "is_symlink": path.is_symlink() if raw else False,
            "resolved": str(path.resolve(strict=False)) if raw else "",
        }
    return {
        "source_root": str(_source_root()),
        "cwd": str(Path.cwd().resolve(strict=False)),
        "paths": paths,
        "ok": bool(paths.get("SKY130_LIB", {}).get("readable")),
    }


def _canonical_model_dropdown_key(key: str) -> str:
    raw = str(key or "").strip()
    for group in (_MODEL_DROPDOWN_KEYS, _BASE_MODEL_DROPDOWN_KEYS, _LEGACY_MODEL_DROPDOWN_KEYS):
        if raw in group:
            return _MODEL_DROPDOWN_KEYS[group.index(raw)]
    return raw


def _model_dropdown_value(index: int) -> str:
    for group in (_MODEL_DROPDOWN_KEYS, _BASE_MODEL_DROPDOWN_KEYS, _LEGACY_MODEL_DROPDOWN_KEYS):
        value = os.getenv(group[index], "").strip()
        if value:
            return value
    return ""


def _apply_model_dropdown_selection() -> None:
    if (
        "MODEL_NAME" in _INITIAL_ENV_KEYS
        or "LLM_PROFILE" in _INITIAL_ENV_KEYS
    ):
        return
    selected_key = _canonical_model_dropdown_key(os.getenv("LLM_SELECTED_MODEL_KEY", ""))
    model = ""
    if selected_key in _MODEL_DROPDOWN_KEYS:
        model = _model_dropdown_value(_MODEL_DROPDOWN_KEYS.index(selected_key))
    else:
        return
    if not model:
        return
    globals()['MODEL_NAME'] = model
    os.environ['LLM_MODEL_NAME'] = model
    os.environ['MODEL_NAME'] = model
    os.environ['LLM_ACTIVE_MODEL_NAME'] = model
    os.environ['LLM_ACTIVE_BASE_NAME'] = model
    os.environ['LLM_ACTIVE_BASE_MODEL'] = model


def _should_apply_env_profile() -> bool:
    if "LLM_PROFILE" in _INITIAL_ENV_KEYS:
        return True
    explicit_single_model = (
        "LLM_MODEL_NAME" in _INITIAL_ENV_KEYS
        or "MODEL_NAME" in _INITIAL_ENV_KEYS
        or "LLM_BASE_URL" in _INITIAL_ENV_KEYS
        or "LLM_API_KEY" in _INITIAL_ENV_KEYS
    )
    return not explicit_single_model


def _refresh_runtime_globals():
    """Re-derive the module-level config globals from current os.environ.

    Called after a force-reload so callers using `config.MODEL_NAME` see
    the new value without re-importing the module. Mirrors the assignment
    block lower in this file — keep them in sync if either side changes.
    """
    _resolve_pdk_env_defaults()
    g = globals()
    g['BASE_URL'] = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    g['API_KEY'] = os.getenv("LLM_API_KEY", "your-openai-api-key-here")
    g['MODEL_NAME'] = os.getenv("LLM_MODEL_NAME", "gpt-4o-mini")
    g['PRIMARY_MODEL'] = os.getenv("PRIMARY_MODEL", g['MODEL_NAME'])
    g['SECONDARY_MODEL'] = os.getenv("SECONDARY_MODEL", g['MODEL_NAME'])
    g['CURSOR_AGENT_ENABLE'] = os.getenv("CURSOR_AGENT_ENABLE", "false").lower() == "true"
    g['CURSOR_AGENT_MODEL'] = os.getenv("CURSOR_AGENT_MODEL", "auto")
    g['CURSOR_AGENT_YOLO'] = os.getenv("CURSOR_AGENT_YOLO", "false").lower() == "true"
    g['CURSOR_AGENT_MODE'] = os.getenv("CURSOR_AGENT_MODE", "")
    g['CURSOR_AGENT_WORKSPACE'] = os.getenv("CURSOR_AGENT_WORKSPACE", "")
    g['CURSOR_AGENT_ACTIVE_MODE'] = os.getenv("CURSOR_AGENT_ACTIVE_MODE", "false").lower() == "true"
    g['CLAUDE_CLI_ENABLE'] = os.getenv("CLAUDE_CLI_ENABLE", "false").lower() == "true"
    g['CLAUDE_CLI_MODEL'] = os.getenv("CLAUDE_CLI_MODEL", "sonnet")
    g['CLAUDE_CLI_PERMISSION_MODE'] = os.getenv("CLAUDE_CLI_PERMISSION_MODE", "default")
    g['CLAUDE_CLI_TOOLS'] = os.getenv("CLAUDE_CLI_TOOLS", "")
    g['CLAUDE_CLI_WORKSPACE'] = os.getenv("CLAUDE_CLI_WORKSPACE", "")
    g['CLAUDE_CLI_NO_SESSION_PERSISTENCE'] = os.getenv("CLAUDE_CLI_NO_SESSION_PERSISTENCE", "true").lower() in ("true", "1", "yes")
    g['CLAUDE_CLI_OUTPUT_FORMAT'] = os.getenv("CLAUDE_CLI_OUTPUT_FORMAT", "json").lower()
    try:
        g['CLAUDE_CLI_TIMEOUT_SEC'] = int(os.getenv("CLAUDE_CLI_TIMEOUT_SEC", "300"))
    except ValueError:
        g['CLAUDE_CLI_TIMEOUT_SEC'] = 300
    # Mirror Azure auto-switch from initial load (config.py:126-134)
    if (os.getenv("LLM_PROVIDER", "openai").lower() == "azure"
            and os.getenv("AZURE_OPENAI_ENDPOINT")):
        dep = os.getenv("AZURE_OPENAI_DEPLOYMENT") or g['MODEL_NAME']
        g['MODEL_NAME'] = dep
        g['BASE_URL'] = os.getenv("AZURE_OPENAI_ENDPOINT", "").rstrip("/")
        if os.getenv("AZURE_OPENAI_API_KEY"):
            g['API_KEY'] = os.getenv("AZURE_OPENAI_API_KEY", "")
    layout = os.getenv("ATLAS_CENTER_LAYOUT", "classic").lower()
    g['ATLAS_CENTER_LAYOUT'] = layout if layout in ("classic", "tabbed") else "classic"
    g['ATLAS_CHAT_FEED_SUMMARY'] = _env_bool("ATLAS_CHAT_FEED_SUMMARY", "true")
    reasoning_mode = os.getenv("REASONING_MODE", os.getenv("REASONING_EFFORT", "medium")).lower()
    g['REASONING_MODE'] = reasoning_mode
    g['REASONING_EFFORT'] = reasoning_mode
    _apply_model_dropdown_selection()
    if "is_cli_backend_model" in g and is_cli_backend_model(g['MODEL_NAME']):
        activate_cli_backend(g['MODEL_NAME'])
    elif g.get('CURSOR_AGENT_ENABLE') or g.get('CLAUDE_CLI_ENABLE'):
        os.environ["ENABLE_NATIVE_TOOL_CALLS"] = "false"
    for key in ("PDK_ROOT", "PDK_LIB_PATH", "SKY130_PDK_ROOT", "SKY130_LIB",
                "SKY130_TLEF", "SKY130_LEF", "SKY130_TRACKS", "SKY130_RCX_RULES"):
        g[key] = os.getenv(key, "")


def reload_env() -> bool:
    """Re-read .env files and refresh module globals if any file changed.

    mtime-cached: returns immediately when nothing has changed since the
    previous call, so it's safe to invoke on hot paths (per LLM call,
    per /api/info request).

    Returns True iff at least one .env file's mtime changed (and thus
    the in-memory config was refreshed).
    """
    changed = False
    for env_path in _env_search_paths():
        try:
            mtime = env_path.stat().st_mtime if env_path.exists() else 0.0
        except OSError:
            mtime = 0.0
        prev = _ENV_MTIME_CACHE.get(str(env_path), -1.0)
        if mtime != prev:
            _ENV_MTIME_CACHE[str(env_path)] = mtime
            changed = True
    if changed:
        load_env_file(force_reload=True)
        _resolve_pdk_env_defaults()
        _refresh_runtime_globals()
        # Re-apply the active profile after refreshing globals so an edit
        # to PROFILE_<active>_* in .env is picked up live. Guarded against
        # the first call during module bootstrap, where _apply_profile is
        # defined later in the file.
        try:
            active = os.getenv("LLM_PROFILE", "").strip()
            if active and _should_apply_env_profile():
                _apply_profile(active)  # type: ignore[name-defined]
            _apply_model_dropdown_selection()
        except NameError:
            pass
    return changed


# Prime the mtime cache + load files for the first time.
for _p in _env_search_paths():
    try:
        _ENV_MTIME_CACHE[str(_p)] = _p.stat().st_mtime if _p.exists() else 0.0
    except OSError:
        _ENV_MTIME_CACHE[str(_p)] = 0.0
load_env_file()
_resolve_pdk_env_defaults()

# Configuration for the Internal LLM
# Users can override these via environment variables

# ============================================================
# OpenAI ChatGPT API Configuration (기본 설정)
# ============================================================
BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
API_KEY = os.getenv("LLM_API_KEY", "your-openai-api-key-here")
MODEL_NAME = os.getenv("LLM_MODEL_NAME", "gpt-4o-mini")
SSL_VERIFY = os.getenv("SSL_VERIFY", "true").lower() != "false"  # set false for corporate proxy
CUSTOM_PRICE = os.getenv("CUSTOM_PRICE", "false").lower() == "true"  # GLM flat $1/$0/$1 per 1M when true
PRIMARY_MODEL = os.getenv("PRIMARY_MODEL", MODEL_NAME)

# ============================================================
# Azure OpenAI Configuration
# ============================================================
# Set LLM_PROVIDER=azure to enable Azure OpenAI mode.
# Required env vars when using Azure:
#   AZURE_OPENAI_ENDPOINT  — e.g. https://my-resource.openai.azure.com
#   AZURE_OPENAI_API_KEY   — your Azure API key
#   AZURE_OPENAI_DEPLOYMENT — deployment name (e.g. gpt-4o-mini-deploy)
#   AZURE_OPENAI_API_VERSION — API version (default: 2024-06-01)
# ============================================================
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()  # openai | azure | anthropic | openrouter | zai
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2025-04-01-preview")

# Responses API mode: uses /responses endpoint instead of /chat/completions.
# Required for Azure gpt-5-codex models and OpenAI codex models.
# When enabled, transforms messages→input, system→instructions, max_tokens→max_output_tokens.
USE_RESPONSES_API = os.getenv("USE_RESPONSES_API", "false").lower() in ("true", "1", "yes")

# Force Chat Completions API for gpt-5* models (opt-out of Responses API).
# When true, models matching *gpt*5* use /chat/completions even if they would
# otherwise be routed to /responses (e.g. gpt-5-codex, gpt-5.1-codex).
FORCE_CHAT_COMPLETIONS_GPT5 = os.getenv("FORCE_CHAT_COMPLETIONS_GPT5", "false").lower() in ("true", "1", "yes")

# Azure auto-detection: if LLM_PROVIDER=azure, override BASE_URL/API_KEY/MODEL_NAME
if LLM_PROVIDER == "azure" and AZURE_OPENAI_ENDPOINT:
    if not AZURE_OPENAI_API_KEY:
        AZURE_OPENAI_API_KEY = API_KEY  # fallback to LLM_API_KEY
    if not AZURE_OPENAI_DEPLOYMENT:
        AZURE_OPENAI_DEPLOYMENT = MODEL_NAME  # fallback to LLM_MODEL_NAME
    # Azure uses a different URL pattern — llm_client.py builds the full path
    BASE_URL = AZURE_OPENAI_ENDPOINT.rstrip("/")
    API_KEY = AZURE_OPENAI_API_KEY
    MODEL_NAME = AZURE_OPENAI_DEPLOYMENT

# ============================================================
# LLM Profile System  (multi-provider: deepseek / glm / kimi / ...)
# ============================================================
# Each profile bundles BASE_URL + API_KEY + MODEL together so /model
# <name> can switch the entire trio in one shot.  Define profiles in
# .env using the PROFILE_<name>_* prefix:
#
#   PROFILE_glm_BASE_URL=https://api.z.ai/api/coding/paas/v4
#   PROFILE_glm_API_KEY=...
#   PROFILE_glm_MODEL=glm-5.1
#
# Selection (highest priority first):
#   1. /model <name>   — set at runtime via slash command (this session)
#   2. --model <name>  — CLI flag (sets LLM_PROFILE before config import)
#   3. LLM_PROFILE     — env var
#   4. <none>          — fall back to LLM_BASE_URL / LLM_API_KEY /
#                        LLM_MODEL_NAME (legacy single-provider mode)
# ============================================================

def list_profiles() -> list:
    """Names of every profile defined via PROFILE_<name>_MODEL in env.

    The MODEL key is treated as the canonical marker — a profile must at
    least name a model. BASE_URL / API_KEY can fall through to the
    top-level LLM_BASE_URL / LLM_API_KEY when omitted (handy for
    same-provider, different-model setups).
    """
    seen = set()
    for k in os.environ:
        if k.startswith("PROFILE_") and k.endswith("_MODEL"):
            name = k[len("PROFILE_"):-len("_MODEL")]
            if name:
                seen.add(name)
    return sorted(seen)


def get_profile(name: str) -> dict:
    """Return the BASE_URL/API_KEY/MODEL trio for a profile, or {} if
    the profile has no MODEL set (= not defined)."""
    pfx = f"PROFILE_{name}_"
    model = os.getenv(pfx + "MODEL", "").strip()
    if not model:
        return {}
    return {
        "name": name,
        "base_url": os.getenv(pfx + "BASE_URL", "").strip()
                    or os.getenv("LLM_BASE_URL", "").strip(),
        "api_key": os.getenv(pfx + "API_KEY", "").strip()
                   or os.getenv("LLM_API_KEY", "").strip(),
        "model": model,
    }


def _apply_profile(name: str) -> bool:
    """Apply a profile to the live module globals + os.environ so dispatch
    (LLM call) and external workers (cmux) both see the same trio.
    Returns True on success, False if the profile is undefined."""
    p = get_profile(name)
    if not p:
        return False
    g = globals()
    g['BASE_URL'] = p['base_url'] or g.get('BASE_URL', '')
    g['API_KEY'] = p['api_key'] or g.get('API_KEY', '')
    g['MODEL_NAME'] = p['model']
    # Mirror to env so cmux workers / sub-processes pick up the same values.
    if p['base_url']:
        os.environ['LLM_BASE_URL'] = p['base_url']
    if p['api_key']:
        os.environ['LLM_API_KEY'] = p['api_key']
    os.environ['LLM_MODEL_NAME'] = p['model']
    os.environ['MODEL_NAME'] = p['model']
    os.environ['LLM_PROFILE'] = name
    return True


def set_active_profile(name: str) -> bool:
    """Public entry point — switch the active LLM profile by name.

    No-op + returns False when `name` doesn't match any defined profile,
    so callers (slash commands, CLI flag) can fall back to single-model
    switching (MODEL_SWITCH:<literal-name>) when the user passes a bare
    model name rather than a profile.

    Side effect: when switching to a non-OpenAI profile, automatically
    deactivates opencode-OAuth so Codex headers / ChatGPT-OAuth Bearer do
    not leak into the next provider's request (glm, deepseek, anthropic).
    `deactivate_opencode_oauth` may be undefined when this is called at
    early bootstrap; we guard with globals() to stay import-safe.
    """
    ok = _apply_profile(name)
    if ok:
        _deact_cli = globals().get("deactivate_cli_backends")
        if callable(_deact_cli):
            _deact_cli()
        _deact = globals().get("deactivate_opencode_oauth")
        if callable(_deact) and globals().get("USE_OPENCODE_OAUTH"):
            _deact()
    return ok


# Apply LLM_PROFILE if set in env (boot-time selection: --model flag
# or shell export). After this point, BASE_URL / API_KEY / MODEL_NAME
# reflect the active profile rather than the bare LLM_* vars.
_active_profile = os.getenv("LLM_PROFILE", "").strip()
if _active_profile and _should_apply_env_profile():
    _apply_profile(_active_profile)
_apply_model_dropdown_selection()

PDK_ROOT = os.getenv("PDK_ROOT", "")
PDK_LIB_PATH = os.getenv("PDK_LIB_PATH", "")
SKY130_PDK_ROOT = os.getenv("SKY130_PDK_ROOT", "")
SKY130_LIB = os.getenv("SKY130_LIB", "")
SKY130_TLEF = os.getenv("SKY130_TLEF", "")
SKY130_LEF = os.getenv("SKY130_LEF", "")
SKY130_TRACKS = os.getenv("SKY130_TRACKS", "")
SKY130_RCX_RULES = os.getenv("SKY130_RCX_RULES", "")

# ============================================================
# cursor-agent Backend Configuration
# ============================================================
CURSOR_AGENT_ENABLE = os.getenv("CURSOR_AGENT_ENABLE", "false").lower() == "true"
CURSOR_AGENT_MODEL = os.getenv("CURSOR_AGENT_MODEL", "auto")
CURSOR_AGENT_YOLO = os.getenv("CURSOR_AGENT_YOLO", "false").lower() == "true"
CURSOR_AGENT_MODE = os.getenv("CURSOR_AGENT_MODE", "")       # "ask" | "plan" | "" (full agent)
CURSOR_AGENT_WORKSPACE = os.getenv("CURSOR_AGENT_WORKSPACE", "")  # path; empty = cwd
# Active mode: instructs the primary LLM to delegate most execution to cursor_agent tool
CURSOR_AGENT_ACTIVE_MODE = os.getenv("CURSOR_AGENT_ACTIVE_MODE", "false").lower() == "true"

# ============================================================
# Claude CLI Backend Configuration
# ============================================================
CLAUDE_CLI_ENABLE = os.getenv("CLAUDE_CLI_ENABLE", "false").lower() == "true"
CLAUDE_CLI_MODEL = os.getenv("CLAUDE_CLI_MODEL", "sonnet")
CLAUDE_CLI_PERMISSION_MODE = os.getenv("CLAUDE_CLI_PERMISSION_MODE", "default")
CLAUDE_CLI_TOOLS = os.getenv("CLAUDE_CLI_TOOLS", "")
CLAUDE_CLI_WORKSPACE = os.getenv("CLAUDE_CLI_WORKSPACE", "")
CLAUDE_CLI_NO_SESSION_PERSISTENCE = os.getenv("CLAUDE_CLI_NO_SESSION_PERSISTENCE", "true").lower() in ("true", "1", "yes")
CLAUDE_CLI_OUTPUT_FORMAT = os.getenv("CLAUDE_CLI_OUTPUT_FORMAT", "json").lower()
try:
    CLAUDE_CLI_TIMEOUT_SEC = int(os.getenv("CLAUDE_CLI_TIMEOUT_SEC", "300"))
except ValueError:
    CLAUDE_CLI_TIMEOUT_SEC = 300

_CLI_BACKEND_ALIASES = {
    "cursor": "cursor",
    "cursor-cli": "cursor",
    "cursor-agent": "cursor",
    "claude": "claude",
    "claude-cli": "claude",
    "claude-code": "claude",
}


def _parse_cli_backend_model(name: str):
    """Return (backend, optional_model) for CLI backend aliases.

    Supported forms:
      cursor-cli
      cursor-cli:<cursor-model>
      claude-cli
      claude-cli:<claude-model>
    """
    raw = (name or "").strip()
    if not raw:
        return None
    low = raw.lower()
    if low in _CLI_BACKEND_ALIASES:
        return (_CLI_BACKEND_ALIASES[low], "")
    for sep in (":", "/"):
        head, found, rest = low.partition(sep)
        if found and head in _CLI_BACKEND_ALIASES:
            return (_CLI_BACKEND_ALIASES[head], raw.split(sep, 1)[1].strip())
    return None


def is_cli_backend_model(name: str) -> bool:
    return _parse_cli_backend_model(name) is not None


def deactivate_cli_backends() -> None:
    """Disable subprocess-backed LLM backends when switching back to API models."""
    global CURSOR_AGENT_ENABLE, CLAUDE_CLI_ENABLE
    CURSOR_AGENT_ENABLE = False
    CLAUDE_CLI_ENABLE = False
    os.environ["CURSOR_AGENT_ENABLE"] = "false"
    os.environ["CLAUDE_CLI_ENABLE"] = "false"


def activate_cli_backend(name: str) -> bool:
    """Activate cursor-agent or Claude Code as the LLM backend.

    This is intentionally separate from provider profiles: no HTTP BASE_URL/API_KEY
    is used, and llm_client dispatches through the local CLI process.
    """
    parsed = _parse_cli_backend_model(name)
    if parsed is None:
        return False
    backend, requested_model = parsed

    global CURSOR_AGENT_ENABLE, CURSOR_AGENT_MODEL
    global CLAUDE_CLI_ENABLE, CLAUDE_CLI_MODEL
    global MODEL_NAME, USE_RESPONSES_API

    _deact_oauth = globals().get("deactivate_opencode_oauth")
    if callable(_deact_oauth) and globals().get("USE_OPENCODE_OAUTH"):
        _deact_oauth()

    if backend == "cursor":
        model = requested_model or os.getenv("CURSOR_AGENT_MODEL", CURSOR_AGENT_MODEL or "auto") or "auto"
        CURSOR_AGENT_ENABLE = True
        CLAUDE_CLI_ENABLE = False
        CURSOR_AGENT_MODEL = model
        MODEL_NAME = "cursor-cli"
        os.environ["CURSOR_AGENT_ENABLE"] = "true"
        os.environ["CLAUDE_CLI_ENABLE"] = "false"
        os.environ["CURSOR_AGENT_MODEL"] = model
        os.environ["LLM_ACTIVE_MODEL_NAME"] = f"cursor-cli:{model}"
    else:
        model = requested_model or os.getenv("CLAUDE_CLI_MODEL", CLAUDE_CLI_MODEL or "sonnet") or "sonnet"
        CLAUDE_CLI_ENABLE = True
        CURSOR_AGENT_ENABLE = False
        CLAUDE_CLI_MODEL = model
        MODEL_NAME = "claude-cli"
        os.environ["CLAUDE_CLI_ENABLE"] = "true"
        os.environ["CURSOR_AGENT_ENABLE"] = "false"
        os.environ["CLAUDE_CLI_MODEL"] = model
        os.environ["LLM_ACTIVE_MODEL_NAME"] = f"claude-cli:{model}"

    USE_RESPONSES_API = False
    os.environ["USE_RESPONSES_API"] = "false"
    os.environ["ENABLE_NATIVE_TOOL_CALLS"] = "false"
    os.environ["LLM_MODEL_NAME"] = MODEL_NAME
    os.environ["MODEL_NAME"] = MODEL_NAME
    os.environ["LLM_ACTIVE_BASE_NAME"] = MODEL_NAME
    os.environ["LLM_ACTIVE_BASE_MODEL"] = MODEL_NAME
    os.environ.pop("LLM_PROFILE", None)
    return True


# When a CLI backend is active, force ReAct text mode so the system prompt
# includes Action:/Observation: instructions that subprocess CLIs can follow.
# CLI subprocess backends do not consume OpenAI-style tool schemas.
if is_cli_backend_model(MODEL_NAME):
    activate_cli_backend(MODEL_NAME)

if CURSOR_AGENT_ENABLE or CLAUDE_CLI_ENABLE:
    os.environ["ENABLE_NATIVE_TOOL_CALLS"] = "false"

# ============================================================
# opencode OAuth Backend (ChatGPT Plus/Pro via shared auth.json)
# ============================================================
# Reuses the existing gpt-5 Responses API code path; only swaps the
# endpoint to Codex (https://chatgpt.com/backend-api/codex/responses)
# and replaces the API key with a ChatGPT OAuth Bearer token loaded from
# opencode's ~/.local/share/opencode/auth.json (refreshed in-process when
# expired). This lets common_ai_agent use the user's ChatGPT subscription
# quota instead of paying for separate OpenAI API credits.
#
# Env vars:
#   USE_OPENCODE_OAUTH=true                  toggle
#   OPENCODE_AUTH_PATH=...                   override auth.json location
#   OPENCODE_MODEL=gpt-5.4                   default model when enabled
# ============================================================
USE_OPENCODE_OAUTH = os.getenv("USE_OPENCODE_OAUTH", "true").lower() == "true"
OPENCODE_ACCOUNT_ID = ""

# Incremental write toggles. When true, the workspace system prompt is
# rewritten to instruct the LLM to build large generated artifacts
# section-by-section via replace_in_file (skeleton first, then replace
# each TBD slot) instead of one huge write_file. Pairs with the
# file_changed bridge event so the preview / SSOT view / file tree
# auto-refresh as each section lands. Defaults on — disable by setting
# the env var to 0/false.
SSOT_INCREMENTAL_WRITE = os.getenv("SSOT_INCREMENTAL_WRITE", "true").lower() in ("true", "1", "yes", "on")
RTL_INCREMENTAL_WRITE  = os.getenv("RTL_INCREMENTAL_WRITE",  "true").lower() in ("true", "1", "yes", "on")

# Expose every per-IP .git as a clone+push target over the same FastAPI
# host:port the backend is already serving. When true:
#   • IP scaffolding sets `receive.denyCurrentBranch = updateInstead` so
#     a regular `git push` to the working repo updates HEAD + working
#     tree if clean, and is refused (without corrupting state) otherwise.
#   • The /git/<ip>.git/* routes proxy through git-http-backend so
#     anyone on the LAN can `git clone http://<host>:<port>/git/<ip>.git`
#     and `git push` back. AuthMiddleware whitelists /git/.
# Default on. Disable with BARE_GIT_OPTION=0 if you want IPs to stay
# strictly local-only.
BARE_GIT_OPTION = os.getenv("BARE_GIT_OPTION", "true").lower() in ("true", "1", "yes", "on")

# Snapshot the pre-OAuth provider trio so deactivate_opencode_oauth() can
# restore it when the user `--model`-switches back to a non-OpenAI profile.
_PRE_OAUTH_BASE_URL = BASE_URL
_PRE_OAUTH_API_KEY = API_KEY
_PRE_OAUTH_LLM_PROVIDER = LLM_PROVIDER


def activate_opencode_oauth(model: str = "") -> bool:
    """Switch the live config to ChatGPT-OAuth / Codex routing.

    Idempotent — safe to call repeatedly (e.g. when `--model gpt-5.5` is
    passed at runtime after a prior glm/deepseek profile was active).

    Args:
        model: optional gpt-5* model id to activate. Empty → keep current
               MODEL_NAME if it's already a gpt-5*, else default to gpt-5.5.
    Returns:
        True on success, False when no opencode credential is available.
    """
    global API_KEY, BASE_URL, LLM_PROVIDER, MODEL_NAME, USE_OPENCODE_OAUTH
    global OPENCODE_ACCOUNT_ID, USE_RESPONSES_API
    _deact_cli = globals().get("deactivate_cli_backends")
    if callable(_deact_cli):
        _deact_cli()
    try:
        from src.opencode_backend import get_credentials, CODEX_BASE_URL
    except Exception as e:
        print(f"[opencode-oauth] activate failed: {e}")
        return False
    cred = get_credentials("openai")
    if not (cred and cred.get("access")):
        print("[opencode-oauth] no credential — run "
              "`python -m src.opencode_backend login`")
        return False
    API_KEY = cred["access"]
    BASE_URL = CODEX_BASE_URL
    LLM_PROVIDER = "openai"
    OPENCODE_ACCOUNT_ID = cred.get("accountId", "") or ""
    USE_RESPONSES_API = True
    USE_OPENCODE_OAUTH = True
    if model:
        MODEL_NAME = model
    elif not MODEL_NAME.lower().startswith("gpt-5"):
        MODEL_NAME = os.getenv("OPENCODE_MODEL", "gpt-5.5")
    os.environ["LLM_API_KEY"] = API_KEY
    os.environ["LLM_BASE_URL"] = BASE_URL
    os.environ["LLM_PROVIDER"] = "openai"
    os.environ["LLM_MODEL_NAME"] = MODEL_NAME
    os.environ["MODEL_NAME"] = MODEL_NAME
    os.environ["OPENCODE_ACCOUNT_ID"] = OPENCODE_ACCOUNT_ID
    os.environ["USE_RESPONSES_API"] = "true"
    os.environ["USE_OPENCODE_OAUTH"] = "true"
    return True


def deactivate_opencode_oauth() -> None:
    """Restore the pre-OAuth BASE_URL/API_KEY/LLM_PROVIDER so a subsequent
    glm/deepseek/anthropic call doesn't carry Codex auth into the wrong
    backend. Called automatically when set_active_profile() switches to a
    non-OpenAI profile.
    """
    global API_KEY, BASE_URL, LLM_PROVIDER, USE_OPENCODE_OAUTH, USE_RESPONSES_API
    BASE_URL = _PRE_OAUTH_BASE_URL
    API_KEY = _PRE_OAUTH_API_KEY
    LLM_PROVIDER = _PRE_OAUTH_LLM_PROVIDER
    USE_OPENCODE_OAUTH = False
    # Mirror activate_opencode_oauth's USE_RESPONSES_API=True flip — without
    # resetting it here, a deactivated session keeps routing to /responses
    # even after BASE_URL is restored to a Chat-Completions-only backend
    # (e.g. Z.AI), producing HTTP 404 on every call.
    USE_RESPONSES_API = False
    os.environ["LLM_BASE_URL"] = BASE_URL
    os.environ["LLM_API_KEY"] = API_KEY
    os.environ["LLM_PROVIDER"] = LLM_PROVIDER
    os.environ["USE_OPENCODE_OAUTH"] = "false"
    os.environ["USE_RESPONSES_API"] = "false"


def is_opencode_model(name: str) -> bool:
    """Heuristic: should `--model <name>` route through opencode-OAuth?"""
    n = (name or "").lower().strip()
    if n.startswith("openai/"):
        n = n.split("/", 1)[1]
    return n.startswith("gpt-5") or ("gpt" in n and "codex" in n)


if USE_OPENCODE_OAUTH and not (CURSOR_AGENT_ENABLE or CLAUDE_CLI_ENABLE):
    if not activate_opencode_oauth():
        USE_OPENCODE_OAUTH = False

# ============================================================
# OpenRouter Configuration (주석 처리됨)
# ============================================================
# BASE_URL = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")
# API_KEY = os.getenv("LLM_API_KEY", "sk-or-v1-...")
# MODEL_NAME = os.getenv("LLM_MODEL_NAME", "meta-llama/llama-3.3-70b-instruct:free")

# Rate limiting
# ──────────────────────────────────────────────────────────────────────────────
# TPM (Tokens Per Minute): max tokens allowed in a 60s sliding window.
#   Set to 0 to disable. Typical values:
#     Free tier:  20,000   |   Pro tier:  200,000   |   Enterprise: 2,000,000
# RPM (Requests Per Minute): max API calls in a 60s sliding window.
#   Set to 0 to disable. Typical values:
#     Free tier:  10       |   Pro tier:  60         |   Enterprise: 500
#
# These replace the old RATE_LIMIT_DELAY (fixed delay between calls).
# If both TPM/RPM are 0, falls back to RATE_LIMIT_DELAY behavior.
# ──────────────────────────────────────────────────────────────────────────────
TPM_LIMIT = int(os.getenv("TPM_LIMIT", "0"))
RPM_LIMIT = int(os.getenv("RPM_LIMIT", "0"))

# Legacy: fixed delay (seconds) between API calls. Ignored when TPM/RPM > 0.
# Set to 0 to disable.
RATE_LIMIT_DELAY = float(os.getenv("RATE_LIMIT_DELAY", "5"))

# MCP (Model Context Protocol) integration
# Set ENABLE_MCP=true and configure servers in .mcp.json
ENABLE_MCP      = os.getenv("ENABLE_MCP", "false").lower() in ("true", "1", "yes")
MCP_CONFIG_PATH = os.getenv("MCP_CONFIG_PATH", ".mcp.json")
# Secrets for MCP servers — referenced as ${VAR} in .mcp.json env blocks
MCP_Z_AI_API_KEY = os.getenv("MCP_Z_AI_API_KEY", "")

# Maximum number of ReAct loop iterations
# Increased to allow for error recovery attempts (3 retries per error)
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "100"))

# API timeout in seconds (how long to wait for API response)
# Set to 0 to disable timeout (not recommended)
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "600"))

# Streaming timeout: per-read socket timeout for streaming requests.
# Must be higher than API_TIMEOUT — reasoning models (GLM, DeepSeek) can think
# silently for minutes before emitting the first token, causing socket.timeout.
STREAM_API_TIMEOUT = int(os.getenv("STREAM_API_TIMEOUT", "1800"))

# Timeout for non-streaming requests (full response must arrive within this time)
NONSTREAM_API_TIMEOUT = int(os.getenv("NONSTREAM_API_TIMEOUT", "1800"))

# Inactivity watchdog: kill stream if NO data arrives for this many seconds.
# Reasoning models (DeepSeek, GLM) can think silently for several minutes —
# set this high enough to avoid false-positive "Read timeout" mid-reasoning.
STREAM_INACTIVITY_TIMEOUT = int(os.getenv("STREAM_INACTIVITY_TIMEOUT", "180"))

# Maximum output tokens per LLM response (0 = no limit)
# MAX_OUTPUT_TOKENS: per-LLM-call output budget. Tool-call args (e.g.
# todo_write([...10 detailed tasks])) eat from this budget too, so a
# tight cap can streaming-truncate large args mid-JSON. Default lifted
# to 65536 so the modern reasoning models (GPT-5.x, GLM-5.x) have room
# for both reasoning + a generous tool-call payload.
MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", "65536"))

# Maximum reasoning/thinking tokens (GLM, DeepSeek etc.).
# For reasoning models, this EXPANDS the max_tokens budget so reasoning
# tokens don't eat into the visible content budget:
#   effective max_tokens = MAX_OUTPUT_TOKENS + MAX_REASONING_TOKENS
# Set to 0 to disable the expansion.
# Recommended: 8000-16000 to give the model room to think AND produce content.
MAX_REASONING_TOKENS = int(os.getenv("MAX_REASONING_TOKENS", "0"))

# Reasoning effort for Responses API models (GPT-5.x, o1, o3, o4).
# Local env var name is REASONING_MODE, but the API field is reasoning.effort.
# Controls how much compute the model spends "thinking" before responding.
# Options: none | low | medium | high | xhigh
# Default: medium (good balance of quality and speed/cost)
# - none:   request no reasoning effort when the model supports it
# - low:    fastest official reasoning tier
# - medium: balanced (recommended for coding agents)
# - high:   deeper reasoning, slower, more expensive
# - xhigh:  extra-high reasoning on supported models
REASONING_MODE = os.getenv("REASONING_MODE", os.getenv("REASONING_EFFORT", "medium")).lower()
# Backward-compatible alias for older code/tests that still read REASONING_EFFORT.
REASONING_EFFORT = REASONING_MODE

# Ask Responses API providers for a visible reasoning summary when reasoning is enabled.
# Default: true. Some compatible backends may ignore this field even when supplied.
RESPONSES_REASONING_SUMMARY = os.getenv("RESPONSES_REASONING_SUMMARY", "true").lower() in ("true", "1", "yes")

# GLM-5/5.1 thinking control (Chat Completions path)
# GLM_THINKING_TYPE: "enabled" (default, GLM-5 default) | "disabled"
# GLM_CLEAR_THINKING: true = clear reasoning each turn (default)
#                     false = preserved thinking (reasoning carried into next turn)
GLM_THINKING_TYPE  = os.getenv("GLM_THINKING_TYPE", "enabled")
GLM_CLEAR_THINKING = os.getenv("GLM_CLEAR_THINKING", "false").lower() not in ("false", "0", "no")

# Save conversation history to file
SAVE_HISTORY = os.getenv("SAVE_HISTORY", "true").lower() in ("true", "1", "yes")
HISTORY_FILE = os.getenv("HISTORY_FILE", "conversation_history.json")
# TODO_FILE / TODO_ERROR_FILE: anchor relative paths to the project
# root so the WRITE side (agent → main.todo_tracker → save() into
# config.TODO_FILE) and the READ side (atlas_ui /api/todos pointing
# at PROJECT_ROOT/current_todos.json) always agree, regardless of
# where the agent server's cwd happened to be when it started.
def _abs_under_project_root(rel_or_abs: str, default_name: str) -> str:
    from pathlib import Path as _Pa
    p = _Pa(rel_or_abs or default_name)
    if p.is_absolute():
        return str(p)
    # src/config.py → common_ai_agent/src/ → common_ai_agent/ (project root)
    project_root = _Pa(__file__).resolve().parent.parent
    return str((project_root / p).resolve())

TODO_FILE = _abs_under_project_root(os.getenv("TODO_FILE", ""), "current_todos.json")
TODO_ERROR_FILE = _abs_under_project_root(os.getenv("TODO_ERROR_FILE", ""), "current_todos_error.json")
COST_FILE      = os.getenv("COST_FILE", "")                   # .session/<project>/cost.json

# Session directory layout (set by _setup_session at runtime)
SESSION_DIR = os.getenv("SESSION_DIR", "")            # .session/<project_name>
ACTIVE_PROJECT = os.getenv("ACTIVE_PROJECT", "default")  # current active project name

# Step-by-step execution mode
STEP_BY_STEP_MODE = os.getenv("STEP_BY_STEP_MODE", "false").lower() in ("true", "1", "yes")

# Execution mode: agent (default loop), chat (limited iterations), step (pause after each action)
EXECUTION_MODE = os.getenv("EXECUTION_MODE", "agent")  # agent | chat | step
# Chat mode iteration limit: 0=respond only (no tools), N=run N ReAct iterations with tools
CHAT_MAX_ITERATIONS = int(os.getenv("CHAT_MAX_ITERATIONS", "1"))

# Debug mode - show detailed parsing and execution info
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() in ("true", "1", "yes")

# Performance tracking - print timing for each phase of the ReAct loop
PERF_TRACKING = os.getenv("PERF_TRACKING", "false").lower() in ("true", "1", "yes")

# Show token usage stats after each LLM response (✽ in X · out Y · sum Z tokens)
SHOW_TOKEN_STATS = os.getenv("SHOW_TOKEN_STATS", "true").lower() in ("true", "1", "yes")
# Show token stats in sidebar (TUI only); hides them from main log when true
SHOW_TOKEN_STATS_SIDEBAR = os.getenv("SHOW_TOKEN_STATS_SIDEBAR", "true").lower() in ("true", "1", "yes")

# Include LLM reasoning in message context (stored in history for next turn)
REASONING_IN_CONTEXT = os.getenv("REASONING_IN_CONTEXT", "false").lower() in ("true", "1", "yes")

# Display LLM reasoning tokens in terminal (dim text before content)
REASONING_DISPLAY = os.getenv("REASONING_DISPLAY", "true").lower() in ("true", "1", "yes")

# Enable streaming mode (token-by-token). false = wait for full response then display.
# Non-streaming cleanly separates reasoning/content but shows nothing until complete.
ENABLE_STREAMING = os.getenv("ENABLE_STREAMING", "true").lower() in ("true", "1", "yes")

# Enable rich Markdown rendering for LLM textual output (Textual UI).
# Disable to stream raw text line-by-line for maximum performance.
# Default: true
ENABLE_MARKDOWN_RENDER = os.getenv("ENABLE_MARKDOWN_RENDER", "true").lower() in ("true", "1", "yes")
ENABLE_CLICK_TO_COPY   = os.getenv("ENABLE_CLICK_TO_COPY", "false").lower() in ("true", "1", "yes")

# Streaming token delay (milliseconds). 0 = disabled. Use for debugging display issues.
STREAM_TOKEN_DELAY_MS = float(os.getenv("STREAM_TOKEN_DELAY_MS", "0"))

# RAG Debug mode - show detailed RAG search/indexing info
DEBUG_RAG = os.getenv("DEBUG_RAG", "false").lower() in ("true", "1", "yes")

# SubAgent Debug mode - show detailed SubAgent execution info
# Shows: parsing details, error checks, stall detection, tool calls (color-coded)
DEBUG_SUBAGENT = os.getenv("DEBUG_SUBAGENT", "false").lower() in ("true", "1", "yes")

# Context Flow Debug mode - monitor agent context sharing
# Shows: SharedContext updates, agent interactions, efficiency metrics
DEBUG_CONTEXT_FLOW = os.getenv("DEBUG_CONTEXT_FLOW", "false").lower() in ("true", "1", "yes")

# Full Prompt Debug - show complete input messages to LLM
FULL_PROMPT_DEBUG = os.getenv("FULL_PROMPT_DEBUG", "false").lower() in ("true", "1", "yes")

# Limit the number of messages shown in Full Prompt Debug
# If True, only shows the last N messages
FULL_PROMPT_DEBUG_LIMIT_ENABLED = os.getenv("FULL_PROMPT_DEBUG_LIMIT_ENABLED", "true").lower() in ("true", "1", "yes")

# Number of recent messages to show when limiting is enabled
FULL_PROMPT_DEBUG_LIMIT_COUNT = int(os.getenv("FULL_PROMPT_DEBUG_LIMIT_COUNT", "5"))

# Limit the number of lines shown per message in Full Prompt Debug
FULL_PROMPT_DEBUG_LINE_LIMIT_ENABLED = os.getenv("FULL_PROMPT_DEBUG_LINE_LIMIT_ENABLED", "true").lower() in ("true", "1", "yes")

# Number of lines to show per message when limiting is enabled
FULL_PROMPT_DEBUG_LINE_LIMIT_COUNT = int(os.getenv("FULL_PROMPT_DEBUG_LINE_LIMIT_COUNT", "20"))

# Tool Description System (OpenCode Integration)
# When enabled, loads detailed tool descriptions from .txt files
ENABLE_TOOL_DESCRIPTIONS = os.getenv("ENABLE_TOOL_DESCRIPTIONS", "true").lower() in ("true", "1", "yes")

# ============================================================
# Native Tool Call Support (Function Calling)
# ============================================================
# When true: uses structured JSON tool_calls API instead of ReAct text parsing.
ENABLE_NATIVE_TOOL_CALLS = os.getenv("ENABLE_NATIVE_TOOL_CALLS", "false").lower() in ("true", "1", "yes")
TOOL_SCHEMA_COMPACT     = os.getenv("TOOL_SCHEMA_COMPACT", "false").lower() in ("true", "1", "yes")

# ============================================================
# Mode-gated tool unlocking
# ============================================================
# Default ON: all todo tools (todo_write/todo_remove/todo_update/
# todo_add/todo_status) are exposed in Normal Mode too, so the agent
# can manage its own task list during execution without flipping into
# Plan Mode first. Set UNLOCK_NORMAL_MODE_TOOLS=false to restore the
# old gating (todo_write/todo_remove plan-only; todo_update execution-
# only).
UNLOCK_NORMAL_MODE_TOOLS = os.getenv("UNLOCK_NORMAL_MODE_TOOLS", "true").lower() in ("true", "1", "yes")

# ============================================================
# RTL dialect for the rtl-gen / ssot-gen workflows
# ============================================================
# RTL syntax policy for rtl-gen / ssot-gen workflows.
# Filenames stay .sv for toolflow compatibility, and generated RTL uses the
# project SystemVerilog subset: input logic/output logic ports, internal logic,
# localparam state encoding, always @(...), and no
# package/import/interface/modport/function/task/for/while constructs.
RTL_DIALECT = "systemverilog_2012"
_RTL_FILE_EXT_RAW = os.getenv("RTL_FILE_EXT", ".sv").strip().lower()
RTL_FILE_EXT = _RTL_FILE_EXT_RAW if _RTL_FILE_EXT_RAW in (".v", ".sv") else ".sv"

# ============================================================
# Type Validation & Linting (Zero-Dependency Features)
# ============================================================
# Enable parameter type validation (always available - uses standard library only)
# Validates tool parameters before execution using type hints
ENABLE_TYPE_VALIDATION = os.getenv("ENABLE_TYPE_VALIDATION", "true").lower() in ("true", "1", "yes")

# Enable automatic linting after file writes (optional - uses external tools if available)
# Checks Python files with compile() + pyflakes, Verilog files with configured simulator
# Falls back gracefully if external tools not installed
ENABLE_LINTING = os.getenv("ENABLE_LINTING", "true").lower() in ("true", "1", "yes")

# pyslang: IEEE 1800-2017 SV parser/linter (pip install pyslang, no binary needed)
# When true AND pyslang is importable, used as primary Verilog linter + AST tools.
# Falls back to VERILOG_SIMULATOR if pyslang not installed or ENABLE_PYSLANG=false.
ENABLE_PYSLANG = os.getenv("ENABLE_PYSLANG", "true").lower() in ("true", "1", "yes")

# Verilog simulator fallback (used when pyslang unavailable or ENABLE_PYSLANG=false)
# Options: "vcs" (default, Synopsys commercial), "iverilog" (open-source), "verilator"
VERILOG_SIMULATOR = os.getenv("VERILOG_SIMULATOR", "vcs")

# Enable automatic git version control (git init + add + commit on write/replace)
GIT_VERSION_CONTROL_ENABLE = os.getenv("GIT_VERSION_CONTROL_ENABLE", "true").lower() in ("true", "1", "yes")

# Permission flags — control whether destructive shell commands are allowed in run_command.
# Default ON: rm/mv are usable from run_command without an extra permission flip.
# Always-blocked-regardless: sudo, shutdown/reboot/halt/poweroff, mkfs, `dd if=`,
# `git reset --hard`, `git clean -f` — see `_is_dangerous_command()` in core/tools.py.
# Toggle at runtime with: /permission rm on|off  or  /permission mv on|off
# Set ALLOW_RM=false / ALLOW_MV=false in .env to restore the old gated behaviour.
ALLOW_RM = os.getenv("ALLOW_RM", "true").lower() in ("true", "1", "yes")
ALLOW_MV = os.getenv("ALLOW_MV", "true").lower() in ("true", "1", "yes")
AUTO_CHMOD_WRITE = os.getenv("AUTO_CHMOD_WRITE", "false").lower() in ("true", "1", "yes")

# Tool data limits — max items/lines actually returned to the LLM context.
# These control what the agent sees. Higher = more context, more tokens.
TOOL_READ_MAX_LINES   = int(os.getenv("TOOL_READ_MAX_LINES",   "3000"))  # read_file lines sent to LLM
TOOL_FIND_MAX_RESULTS = int(os.getenv("TOOL_FIND_MAX_RESULTS", "1000"))  # find_files entries sent to LLM
TOOL_GREP_MAX_FILES   = int(os.getenv("TOOL_GREP_MAX_FILES",   "50"))    # grep_file max files scanned
TOOL_GREP_MAX_MATCHES = int(os.getenv("TOOL_GREP_MAX_MATCHES", "200"))   # grep_file max match blocks
TOOL_LIST_MAX_ENTRIES = int(os.getenv("TOOL_LIST_MAX_ENTRIES", "1000"))  # list_dir entries sent to LLM

# Display limits — max items/lines shown in the terminal UI (does NOT affect LLM context).
# Lower = cleaner terminal output. The agent still gets the full data above.
DISPLAY_READ_MAX_LINES   = int(os.getenv("DISPLAY_READ_MAX_LINES",   "10"))   # lines shown in result preview
DISPLAY_FIND_MAX_RESULTS = int(os.getenv("DISPLAY_FIND_MAX_RESULTS", "20"))   # find results shown
DISPLAY_GREP_MAX_LINES   = int(os.getenv("DISPLAY_GREP_MAX_LINES",   "15"))   # grep output lines shown
DISPLAY_LIST_MAX_ENTRIES = int(os.getenv("DISPLAY_LIST_MAX_ENTRIES", "30"))   # list_dir entries shown
DISPLAY_RESULT_MAX_CHARS = int(os.getenv("DISPLAY_RESULT_MAX_CHARS", "2000")) # total chars in any result preview
DISPLAY_TOOL_DETAIL      = os.getenv("DISPLAY_TOOL_DETAIL", "true").lower() in ("true", "1", "yes")  # syntax-highlighted read/grep/list preview

# Atlas web UI: max chars per tool_result obs sent over WebSocket to
# the browser. Display-only — LLM still sees the full tool output
# (those caps live in TOOL_*_MAX above). Bigger = user sees more of
# long reads/greps without "[truncated]"; costs zero LLM tokens.
WS_TOOL_RESULT_MAX_CHARS = int(os.getenv("WS_TOOL_RESULT_MAX_CHARS", "32000"))

# Safe display truncation — used by safe_truncate_output() to cap large tool results.
# These prevent the terminal UI from breaking on very large outputs (trees, long reads, grep floods).
DISPLAY_MAX_TOOL_LINES   = int(os.getenv("DISPLAY_MAX_TOOL_LINES",   "80"))    # max lines before truncation
DISPLAY_MAX_TOOL_CHARS   = int(os.getenv("DISPLAY_MAX_TOOL_CHARS",   "8000"))  # max total chars before truncation
DISPLAY_SAFE_CODE_BLOCK_LINES = int(os.getenv("DISPLAY_SAFE_CODE_BLOCK_LINES", "150"))  # max lines in a single code block

# Commit message verbosity: "simple" | "summary"
GIT_COMMIT_MSG_MODE = os.getenv("GIT_COMMIT_MSG_MODE", "simple")
GIT_COMMIT_SUMMARY_TEMPERATURE = float(os.getenv("GIT_COMMIT_SUMMARY_TEMPERATURE", "0.3"))

# Secondary model: lightweight tasks (git commit summary, spec summarization, etc.)
# Uses same LLM_BASE_URL / LLM_API_KEY — no separate auth needed.
SECONDARY_MODEL = os.getenv("SECONDARY_MODEL", MODEL_NAME)

# Enable LSP integration (optional - requires LSP server installed)
# Uses pylsp, pyright, or jedi-language-server for advanced diagnostics
# Gracefully disabled if no LSP server found
ENABLE_LSP = os.getenv("ENABLE_LSP", "false").lower() in ("true", "1", "yes")

# ============================================================
# Skill System Configuration (Claude Code Style)
# ============================================================
# Enable/Disable skill system (plugin-based domain expertise)
# When enabled, loads domain-specific prompts dynamically based on task context
ENABLE_SKILL_SYSTEM = os.getenv("ENABLE_SKILL_SYSTEM", "true").lower() in ("true", "1", "yes")

# User skills directory (for custom skills)
# Users can add SKILL.md files here for project-specific expertise
SKILLS_DIR = os.getenv("SKILLS_DIR", "~/.common_ai_agent/skills")

# Auto-detect skills based on keywords and file patterns
# If false, skills must be manually activated
SKILL_AUTO_DETECT = os.getenv("SKILL_AUTO_DETECT", "true").lower() in ("true", "1", "yes")

# Activation threshold for skill auto-detection (0.0-1.0)
# Lower = more skills activated, Higher = only highly relevant skills
# Default: 0.15 (sensitive - activates skills with 1-2 keyword matches)
SKILL_ACTIVATION_THRESHOLD = float(os.getenv("SKILL_ACTIVATION_THRESHOLD", "0.15"))

# Tool result preview settings
TOOL_RESULT_PREVIEW_LINES = int(os.getenv("TOOL_RESULT_PREVIEW_LINES", "3"))  # For read_file/read_lines
TOOL_RESULT_PREVIEW_CHARS = int(os.getenv("TOOL_RESULT_PREVIEW_CHARS", "300"))  # For other tools

# Large File Handling
MAX_OBSERVATION_CHARS = int(os.getenv("MAX_OBSERVATION_CHARS", "20000"))  # ~5000 tokens
LARGE_FILE_PREVIEW_LINES = int(os.getenv("LARGE_FILE_PREVIEW_LINES", "100"))  # Number of lines to show in preview

# Context Management
# Token limit for the model context window (0 = no limit, use estimated from chars)
# Set to your model's actual context window size for best results.
MAX_CONTEXT_TOKENS = int(os.getenv("MAX_CONTEXT_TOKENS", "128000"))  # Default: 128K tokens
# Threshold to trigger compression (0.0 to 1.0)
# Default: 0.9 (90% of 128K = ~115K tokens)
# Old value 0.8 was too conservative, causing compression every iteration
COMPRESSION_THRESHOLD = float(os.getenv("COMPRESSION_THRESHOLD", "0.9"))
# Enable/Disable compression
# Default: True
ENABLE_COMPRESSION = os.getenv("ENABLE_COMPRESSION", "true").lower() in ("true", "1", "yes")

# Compression mode: 'single' or 'chunked'
# single: Summarize all old messages in one go (faster, cheaper)
# chunked: Summarize in chunks (better for very long histories)
COMPRESSION_MODE = os.getenv("COMPRESSION_MODE", "single")

# Chunk size for chunked compression (number of messages per chunk)
# Only used when COMPRESSION_MODE=chunked
COMPRESSION_CHUNK_SIZE = int(os.getenv("COMPRESSION_CHUNK_SIZE", "10"))

# Number of recent messages to keep unchanged during compression
# Recommended: 4-15 messages
COMPRESSION_KEEP_RECENT = int(os.getenv("COMPRESSION_KEEP_RECENT", "4"))
# Most-recently-accessed tool call paths to embed in compression system msg (0=disable)
COMPRESSION_TOOL_CALL_PATHS = int(os.getenv("COMPRESSION_TOOL_CALL_PATHS", "0"))

# Hard cap on conversation_text fed to the summarizer LLM, in characters.
# 0 = derive from MAX_CONTEXT_TOKENS * 4 * COMPRESSION_INPUT_BUDGET_RATIO.
# Set explicitly when you need a fixed budget regardless of model context size.
COMPRESSION_INPUT_MAX_CHARS = int(os.getenv("COMPRESSION_INPUT_MAX_CHARS", "0"))
# Fraction of MAX_CONTEXT_TOKENS used for compression input (0.2-0.8).
# 0.5 = use up to half the context window for the conversation text being summarized,
# leaving the other half for the prompt + output. Larger = less head+tail truncation
# of long sessions, smaller = faster/cheaper summarization calls.
COMPRESSION_INPUT_BUDGET_RATIO = float(os.getenv("COMPRESSION_INPUT_BUDGET_RATIO", "0.5"))

# Per-message smart-truncation caps (used by compressor._smart_truncate).
# Bump these if your tool results / assistant turns are getting silently
# chopped before the summarizer sees them. Plain text vs tool results have
# separate caps; high-value content (code/error/diff) gets multiplied.
SMART_TRUNCATE_TEXT_MAX = int(os.getenv("SMART_TRUNCATE_TEXT_MAX", "2000"))
SMART_TRUNCATE_TOOL_MAX = int(os.getenv("SMART_TRUNCATE_TOOL_MAX", "2000"))
SMART_TRUNCATE_HIGHVALUE_MULT = float(os.getenv("SMART_TRUNCATE_HIGHVALUE_MULT", "2.0"))

# Number of LLM retry attempts on empty/failed response (0 = no retry)
LLM_RETRY_COUNT = int(os.getenv("LLM_RETRY_COUNT", "1"))

# Enable Smart Compression (selective preservation based on importance)
# NOTE: Default changed to "false" - using Traditional Compression for simplicity
# When enabled, preserves critical messages (user preferences, error solutions)
# and only summarizes less important messages
ENABLE_SMART_COMPRESSION = os.getenv("ENABLE_SMART_COMPRESSION", "false").lower() in ("true", "1", "yes")

# Pre-compression analysis: ask LLM what's important before compressing.
# LLM analyzes current context → generates a focused summary instruction →
# that instruction guides compression so critical context is preserved.
# Adds one extra LLM call before compression. Default: false
COMPRESSION_PRE_ANALYSIS = os.getenv("COMPRESSION_PRE_ANALYSIS", "false").lower() in ("true", "1", "yes")

# Todo work log: allow LLM to append progress notes to tasks via todo_note().
# Notes survive compression and appear in review/rejection prompts.
# Default: true
ENABLE_TODO_NOTES = os.getenv("ENABLE_TODO_NOTES", "true").lower() in ("true", "1", "yes")

# ============================================================
# Dynamic Context Pruning Configuration
# ============================================================
# Preemptive compression threshold (0.0 to 1.0)
# Triggers compression earlier to prevent emergency situations
# Default: 0.85 (85% of context limit)
PREEMPTIVE_COMPRESSION_THRESHOLD = float(os.getenv("PREEMPTIVE_COMPRESSION_THRESHOLD", "0.85"))

# Enable turn-based message protection during compression
# When enabled, protects recent N turns instead of N messages
# Default: true (recommended for better conversation continuity)
ENABLE_TURN_PROTECTION = os.getenv("ENABLE_TURN_PROTECTION", "false").lower() in ("true", "1", "yes")

# Number of recent turns to protect from compression
# Only used when ENABLE_TURN_PROTECTION=true
# Default: 3 (protects last 3 user-assistant exchanges)
TURN_PROTECTION_COUNT = int(os.getenv("TURN_PROTECTION_COUNT", "3"))

# ============================================================
# Prompt Caching Configuration
# ============================================================
# Enable prompt caching — works with Anthropic (explicit) and Z.AI/OpenAI (implicit)
# Default: true. Set ENABLE_PROMPT_CACHING=false in .config to disable.
ENABLE_PROMPT_CACHING = os.getenv("ENABLE_PROMPT_CACHING", "true").lower() in ("true", "1", "yes")

# Prompt Caching Optimization Mode
# Options:
#   - "legacy": Single-string system message (current behavior, safe fallback)
#   - "optimized": Multi-block system message (40-50% cost reduction)
# Default: "legacy" (backward compatible)
# NOTE: Only effective when ENABLE_PROMPT_CACHING=true and using Anthropic models
CACHE_OPTIMIZATION_MODE = os.getenv("CACHE_OPTIMIZATION_MODE", "legacy").lower()

# Token Cost Configuration (per 1M tokens, USD)
# Set these in .config to enable cost tracking in the sidebar.
# Example for GLM-5.1: LLM_COST_INPUT_PER_M=0.14 LLM_COST_CACHE_PER_M=0.07 LLM_COST_OUTPUT_PER_M=0.28
LLM_COST_INPUT_PER_M  = float(os.getenv("LLM_COST_INPUT_PER_M",  "0"))
LLM_COST_CACHE_PER_M  = float(os.getenv("LLM_COST_CACHE_PER_M",  "0"))
LLM_COST_OUTPUT_PER_M = float(os.getenv("LLM_COST_OUTPUT_PER_M", "0"))

# Feature Flags
ENABLE_VERILOG_TOOLS = os.getenv("ENABLE_VERILOG_TOOLS", "false").lower() in ("true", "1", "yes")
ENABLE_CMUX_TOOLS = os.getenv("CMUX_ENABLE", "false").lower() in ("true", "1", "yes")
ENABLE_TMUX_TOOLS = os.getenv("TMUX_ENABLE", "false").lower() in ("true", "1", "yes")
ENABLE_WEB_TOOLS = os.getenv("ENABLE_WEB_TOOLS", "false").lower() in ("true", "1", "yes")
FIRECRAWL_API_URL = os.getenv("FIRECRAWL_API_URL", "http://localhost:3002")
FIRECRAWL_TIMEOUT = int(os.getenv("FIRECRAWL_TIMEOUT", "30"))

# Image Read — analyze images using vision-capable models
# When enabled, adds read_image() tool that sends images to a vision model.
# Uses OpenAI Chat Completions API format (compatible with Z.AI, OpenRouter, etc.)
ENABLE_IMAGE_READ     = os.getenv("ENABLE_IMAGE_READ", "false").lower() in ("true", "1", "yes")
IMAGE_READ_API_KEY    = os.getenv("IMAGE_READ_API_KEY", API_KEY)
IMAGE_READ_BASE_URL   = os.getenv("IMAGE_READ_BASE_URL", BASE_URL)
IMAGE_READ_MODEL      = os.getenv("IMAGE_READ_MODEL", "glm-4.6v")  # Z.AI GLM-4.6V by default
IMAGE_READ_MAX_SIZE   = int(os.getenv("IMAGE_READ_MAX_SIZE", "8"))  # max MB per image
IMAGE_READ_TIMEOUT    = int(os.getenv("IMAGE_READ_TIMEOUT", "30"))  # seconds

# Maximum cache breakpoints (1-4, Anthropic allows up to 4)
# Default: 3 (System message + 2 dynamic points in history)
MAX_CACHE_BREAKPOINTS = int(os.getenv("MAX_CACHE_BREAKPOINTS", "3"))

# Cache interval - how often to place breakpoints in message history
# If 0 or not set: use dynamic calculation based on history length
# If set to N: place breakpoint every N messages
# Default: 0 (dynamic calculation)
CACHE_INTERVAL = int(os.getenv("CACHE_INTERVAL", "0"))

# Minimum tokens required for caching
# Claude Sonnet/Opus: 1024, Claude Haiku: 2048
# Default: 1024
MIN_CACHE_TOKENS = int(os.getenv("MIN_CACHE_TOKENS", "1024"))

# ============================================================
# Session Recovery Configuration
# ============================================================
# Enable/Disable session recovery system
# When enabled, creates automatic recovery points and allows rollback on errors
# Default: true (recommended for stability)
ENABLE_SESSION_RECOVERY = os.getenv("ENABLE_SESSION_RECOVERY", "true").lower() in ("true", "1", "yes")

# Maximum number of recovery attempts after consecutive errors
# System will try to rollback and retry up to this many times
# Default: 3
MAX_RECOVERY_ATTEMPTS = int(os.getenv("MAX_RECOVERY_ATTEMPTS", "3"))

# Automatically create recovery points
# When enabled, creates a recovery point after each user message
# Default: true (recommended)
AUTO_RECOVERY_POINT = os.getenv("AUTO_RECOVERY_POINT", "true").lower() in ("true", "1", "yes")

# ============================================================
# Embedding Configuration (for Memory System)
# ============================================================
# Embedding API URL (OpenAI compatible)
EMBEDDING_BASE_URL = os.getenv("EMBEDDING_BASE_URL", "https://api.openai.com/v1")

# Embedding API Key (fallback to LLM_API_KEY if not set)
EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY", API_KEY)

# Embedding model name
# OpenAI: text-embedding-3-small (1536 dim, $0.00002/1K tokens)
#         text-embedding-3-large (3072 dim, $0.00013/1K tokens)
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

# Embedding dimension (auto-detected, optional override)
# Optional: Auto-detect if not set
_emb_dim_env = os.getenv("EMBEDDING_DIMENSION")
EMBEDDING_DIMENSION = int(_emb_dim_env) if _emb_dim_env else None

# ============================================================
# Memory System Configuration
# ============================================================
# Enable/Disable memory system
ENABLE_MEMORY = os.getenv("ENABLE_MEMORY", "false").lower() in ("true", "1", "yes")

# Memory directory (relative to home directory)
MEMORY_DIR = os.getenv("MEMORY_DIR", ".memory")

# Enable automatic preference extraction from user messages (Mem0-style)
# When enabled, Common AI Agent will detect preferences in user messages
# and automatically learn them without explicit instruction
# Default: true
ENABLE_AUTO_EXTRACT = os.getenv("ENABLE_AUTO_EXTRACT", "true").lower() in ("true", "1", "yes")

# ============================================================
# Graph Lite Configuration (Knowledge Graph)
# ============================================================
# Enable/Disable graph system
ENABLE_GRAPH = os.getenv("ENABLE_GRAPH", "false").lower() in ("true", "1", "yes")

# Auto-extract knowledge from conversations (end of session)
GRAPH_AUTO_EXTRACT = os.getenv("GRAPH_AUTO_EXTRACT", "true").lower() in ("true", "1", "yes")

# Number of relevant nodes to inject into context (semantic search)
GRAPH_SEARCH_LIMIT = int(os.getenv("GRAPH_SEARCH_LIMIT", "5"))

# Similarity threshold for graph search results (0.0-1.0)
# Only nodes with similarity >= this value will be included in context
GRAPH_SIMILARITY_THRESHOLD = float(os.getenv("GRAPH_SIMILARITY_THRESHOLD", "0.5"))

# Number of recent messages to use for knowledge extraction
GRAPH_EXTRACTION_MESSAGES = int(os.getenv("GRAPH_EXTRACTION_MESSAGES", "10"))

# ============================================================
# A-MEM Configuration (Auto-Linking)
# ============================================================
# Similarity threshold for finding candidate notes to link (0.0-1.0)
AMEM_SIMILARITY_THRESHOLD = float(os.getenv("AMEM_SIMILARITY_THRESHOLD", "0.5"))

# Maximum number of candidate notes to send to LLM for linking decision
AMEM_MAX_CANDIDATES = int(os.getenv("AMEM_MAX_CANDIDATES", "10"))

# LLM temperature for linking decisions (lower = more logical/deterministic)
AMEM_LINK_TEMPERATURE = float(os.getenv("AMEM_LINK_TEMPERATURE", "0.3"))

# ============================================================
# ACE Credit Assignment Configuration
# ============================================================
# Enable credit tracking for graph nodes (ACE-style feedback)
# When enabled, tracks which knowledge nodes helped or harmed task completion
ENABLE_CREDIT_TRACKING = os.getenv("ENABLE_CREDIT_TRACKING", "true").lower() in ("true", "1", "yes")

# Minimum quality score to include a node in search results (-1.0 to 1.0)
# Nodes with quality below this will be excluded/deprioritized
# Quality = (helpful - harmful) / (helpful + harmful + 1)
NODE_QUALITY_THRESHOLD = float(os.getenv("NODE_QUALITY_THRESHOLD", "-0.3"))

# ============================================================
# Knowledge Curator Configuration (ACE-style)
# ============================================================
# Enable/Disable knowledge curator (automatic node cleanup)
ENABLE_CURATOR = os.getenv("ENABLE_CURATOR", "true").lower() in ("true", "1", "yes")

# Run curation every N conversations
CURATOR_INTERVAL = int(os.getenv("CURATOR_INTERVAL", "10"))

# Days of inactivity before pruning unused nodes
CURATOR_PRUNE_DAYS = int(os.getenv("CURATOR_PRUNE_DAYS", "30"))

# Minimum harmful count before considering deletion
# Node deleted if: harmful > helpful AND harmful >= this threshold
CURATOR_HARMFUL_THRESHOLD = int(os.getenv("CURATOR_HARMFUL_THRESHOLD", "2"))

# ============================================================
# Hybrid Search Configuration (BM25 + Embedding)
# ============================================================
# Search method: "embedding", "bm25", or "hybrid"
# hybrid uses RRF (Reciprocal Rank Fusion) to combine both
SEARCH_METHOD = os.getenv("SEARCH_METHOD", "hybrid")

# Alpha weight for hybrid search (0.0-1.0)
# Higher = more weight on embedding similarity
# Lower = more weight on BM25 keyword matching
HYBRID_ALPHA = float(os.getenv("HYBRID_ALPHA", "0.8"))

# ============================================================
# RAG Auto-Indexing Configuration
# ============================================================
# Enable/Disable automatic RAG indexing on startup
# When enabled, automatically indexes files based on ~/.rag/.ragconfig
# Uses hash-based comparison to skip unchanged files (very fast on re-runs)
ENABLE_RAG_AUTO_INDEX = os.getenv("ENABLE_RAG_AUTO_INDEX", "false").lower() in ("true", "1", "yes")

# Fine-grained chunking for Verilog files
# When enabled, creates detailed chunks for individual signals, case statements, if-else blocks
# More precise search but ~10x more chunks (and embeddings)
RAG_FINE_GRAINED = os.getenv("RAG_FINE_GRAINED", "false").lower() in ("true", "1", "yes")

# RAG API rate limiting delay (milliseconds)
# Prevents "Too Many Requests" (429) errors when indexing
# Default: 100ms (10 API calls/sec)
RAG_RATE_LIMIT_DELAY_MS = int(os.getenv("RAG_RATE_LIMIT_DELAY_MS", "100"))

# RAG storage directory (absolute or ~-prefixed path)
# Default: "~/.rag" (stored in home directory, not project dir)
RAG_DIR = os.getenv("RAG_DIR", "~/.rag")

# RAG config file path (.ragconfig location)
# Default: None (uses RAG_DIR/.ragconfig)
# Set to project .ragconfig path for project-specific indexing patterns
RAG_CONFIG_PATH = os.getenv("RAG_CONFIG_PATH", None)

# RAG Optimization Settings
# Chunk size for splitting documents (characters)
# Reduced to 1200 for better semantic precision (matches embedding limits)
RAG_CHUNK_SIZE = int(os.getenv("RAG_CHUNK_SIZE", "1200"))

# Check overlap size
RAG_CHUNK_OVERLAP = int(os.getenv("RAG_CHUNK_OVERLAP", "200"))

# Batch size for embedding API calls
RAG_EMBEDDING_BATCH_SIZE = int(os.getenv("RAG_EMBEDDING_BATCH_SIZE", "50"))

# Enable persistent caching (SQLite)
RAG_ENABLE_PERSISTENT_CACHE = os.getenv("RAG_ENABLE_PERSISTENT_CACHE", "true").lower() in ("true", "1", "yes")

# Search Algorithm: 'vector', 'hybrid_simple', 'hybrid_rrf'
RAG_SEARCH_ALGORITHM = os.getenv("RAG_SEARCH_ALGORITHM", "hybrid_simple")

# Enable/Disable Node Merge (Phase 4)
# When enabled, Curator will merge similar nodes to reduce redundancy
ENABLE_NODE_MERGE = os.getenv("ENABLE_NODE_MERGE", "false").lower() in ("true", "1", "yes")

# Similarity threshold for node merging (0.0-1.0)
# Only nodes with similarity >= this value will be merged
MERGE_SIMILARITY_THRESHOLD = float(os.getenv("MERGE_SIMILARITY_THRESHOLD", "0.85"))

# ============================================================
# Smart RAG Decision Configuration
# ============================================================
# Enable/Disable automatic RAG context injection
# When enabled, automatically searches RAG and injects relevant context
ENABLE_SMART_RAG = os.getenv("ENABLE_SMART_RAG", "false").lower() in ("true", "1", "yes")

# High threshold: score >= this -> use RAG context directly
SMART_RAG_HIGH_THRESHOLD = float(os.getenv("SMART_RAG_HIGH_THRESHOLD", "0.75"))

# Low threshold: score < this -> ignore RAG results
SMART_RAG_LOW_THRESHOLD = float(os.getenv("SMART_RAG_LOW_THRESHOLD", "0.0"))

# Number of top results to consider
SMART_RAG_TOP_K = int(os.getenv("SMART_RAG_TOP_K", "3"))

# Enable LLM judgment for mid-score results (between low and high threshold)
# When enabled, asks LLM to judge relevance for ambiguous cases
SMART_RAG_LLM_JUDGE = os.getenv("SMART_RAG_LLM_JUDGE", "true").lower() in ("true", "1", "yes")

# ============================================================
# Procedural Memory Configuration (Memp)
# ============================================================
# Enable/Disable procedural memory system (learning from past experiences)
ENABLE_PROCEDURAL_MEMORY = os.getenv("ENABLE_PROCEDURAL_MEMORY", "false").lower() in ("true", "1", "yes")

# Maximum number of similar trajectories to retrieve for guidance
PROCEDURAL_RETRIEVE_LIMIT = int(os.getenv("PROCEDURAL_RETRIEVE_LIMIT", "3"))

# Minimum similarity score to use a trajectory (0.0-1.0)
PROCEDURAL_SIMILARITY_THRESHOLD = float(os.getenv("PROCEDURAL_SIMILARITY_THRESHOLD", "0.5"))

# Enable trajectory guidance injection into prompts
PROCEDURAL_INJECT_GUIDANCE = os.getenv("PROCEDURAL_INJECT_GUIDANCE", "true").lower() in ("true", "1", "yes")

# ============================================================
# Deep Think Configuration (Hypothesis Branching)
# ============================================================
# Enable/Disable Deep Think system (parallel hypothesis reasoning)
ENABLE_DEEP_THINK = os.getenv("ENABLE_DEEP_THINK", "true").lower() in ("true", "1", "yes")

# Number of hypotheses to generate per task
DEEP_THINK_NUM_HYPOTHESES = int(os.getenv("DEEP_THINK_NUM_HYPOTHESES", "3"))

# Enable simulation step (run first_action for each hypothesis)
DEEP_THINK_ENABLE_SIMULATION = os.getenv("DEEP_THINK_ENABLE_SIMULATION", "true").lower() in ("true", "1", "yes")

# Scoring weights (must sum to 1.0)
DEEP_THINK_WEIGHT_EXPERIENCE = float(os.getenv("DEEP_THINK_WEIGHT_EXPERIENCE", "0.30"))
DEEP_THINK_WEIGHT_KNOWLEDGE = float(os.getenv("DEEP_THINK_WEIGHT_KNOWLEDGE", "0.20"))
DEEP_THINK_WEIGHT_COHERENCE = float(os.getenv("DEEP_THINK_WEIGHT_COHERENCE", "0.25"))
DEEP_THINK_WEIGHT_SIMULATION = float(os.getenv("DEEP_THINK_WEIGHT_SIMULATION", "0.15"))
DEEP_THINK_WEIGHT_CONFIDENCE = float(os.getenv("DEEP_THINK_WEIGHT_CONFIDENCE", "0.10"))

# LLM temperature for hypothesis generation (higher = more diverse)
DEEP_THINK_TEMPERATURE = float(os.getenv("DEEP_THINK_TEMPERATURE", "0.7"))

# Timeout for parallel tool execution (seconds)
DEEP_THINK_TOOL_TIMEOUT = int(os.getenv("DEEP_THINK_TOOL_TIMEOUT", "10"))

# ============================================================
# Sub-Agent Configuration (Claude Code Style)
# ============================================================
# Enable/Disable Sub-Agent system (replaces Deep Think when enabled)
# When enabled, Orchestrator analyzes tasks and spawns specialized agents
ENABLE_SUB_AGENTS = os.getenv("ENABLE_SUB_AGENTS", "false").lower() in ("true", "1", "yes")

# Enable parallel execution of sub-agents
# Default: false (sequential execution for stability)
SUB_AGENT_PARALLEL_ENABLED = os.getenv("SUB_AGENT_PARALLEL_ENABLED", "false").lower() in ("true", "1", "yes")

# Maximum iterations per sub-agent
SUB_AGENT_MAX_ITERATIONS = int(os.getenv("SUB_AGENT_MAX_ITERATIONS", "10"))

# Maximum parallel workers when parallel execution is enabled
SUB_AGENT_MAX_WORKERS = int(os.getenv("SUB_AGENT_MAX_WORKERS", "3"))

# Timeout for each sub-agent (seconds)
SUB_AGENT_TIMEOUT = int(os.getenv("SUB_AGENT_TIMEOUT", "60"))

# ============================================================
# ReAct Parallel Execution Configuration
# ============================================================
# Enable parallel execution of multiple Actions in the ReAct loop.
# When LLM outputs multiple Actions, eligible read-only tools can run concurrently.
ENABLE_REACT_PARALLEL = os.getenv("ENABLE_REACT_PARALLEL", "true").lower() in ("true", "1", "yes")

# Human-in-the-loop: allow user to inject messages between react loop iterations.
# When enabled, input typed during agent execution is queued and injected as a
# user message after the current iteration's tools finish, before the next LLM call.
ENABLE_HUMAN_IN_THE_LOOP = os.getenv("ENABLE_HUMAN_IN_THE_LOOP", "true").lower() in ("true", "1", "yes")

# Enhanced parallel execution using ActionDependencyAnalyzer (Claude Code style)
# - Automatic dependency analysis
# - Intelligent batching (read-only → parallel, write → barrier)
# - File conflict detection
# Set to False to use legacy simple allowlist-based parallelism
ENABLE_ENHANCED_PARALLEL = os.getenv("ENABLE_ENHANCED_PARALLEL", "true").lower() in ("true", "1", "yes")

# Maximum parallel workers for ReAct actions
REACT_MAX_WORKERS = int(os.getenv("REACT_MAX_WORKERS", "5"))

# Lines to preview when write_file runs (parallel or sequential). 0 = disable (show brief)
WRITE_PREVIEW_LINES = int(os.getenv("WRITE_PREVIEW_LINES", "15"))

# Max lines to show for edit/replace tool results. 0 = disable (show brief)
EDIT_PREVIEW_MAX_LINES = int(os.getenv("EDIT_PREVIEW_MAX_LINES", "50"))

# Timeout for a parallel action batch (seconds)
REACT_ACTION_TIMEOUT = int(os.getenv("REACT_ACTION_TIMEOUT", "30"))

# Global timeout for ANY single tool execution (seconds).
# This is the last-resort safety net — if a tool hangs beyond this, it is force-killed.
# Applies to both serial and parallel tool execution paths.
REACT_TOOL_GLOBAL_TIMEOUT = int(os.getenv("REACT_TOOL_GLOBAL_TIMEOUT", "300"))

# ============================================================
# Todo Tracking System (Phase 2 - Claude Code Style)
# ============================================================
# Enable todo tracking for multi-step tasks
# Displays real-time progress with ✅ ▶️ ⏸️ icons
ENABLE_TODO_TRACKING = os.getenv("ENABLE_TODO_TRACKING", "true").lower() in ("true", "1", "yes")
ACTION_REMINDER = os.getenv("ACTION_REMINDER", "true").lower() in ("true", "1", "yes")
ACTION_REMINDER_TEXT = os.getenv(
    "ACTION_REMINDER_TEXT",
    "If further action is needed, output it now: Action: tool_name(param=value)",
)
TODO_STAGNATION_LIMIT = int(os.getenv("TODO_STAGNATION_LIMIT", "50"))
TODO_AUTO_ADVANCE_THRESHOLD = int(os.getenv("TODO_AUTO_ADVANCE_THRESHOLD", "5"))
TODO_TEXT_ONLY_LIMIT = int(os.getenv("TODO_TEXT_ONLY_LIMIT", "50"))
EXECUTION_NO_ACTION_GUARD = os.getenv("EXECUTION_NO_ACTION_GUARD", "true").lower() in ("true", "1", "yes")
EXECUTION_NO_ACTION_RETRY_LIMIT = int(os.getenv("EXECUTION_NO_ACTION_RETRY_LIMIT", "3"))
EXECUTION_NO_ACTION_COMPACT_CHARS = int(os.getenv("EXECUTION_NO_ACTION_COMPACT_CHARS", "4000"))
PLAN_TODO_WRITE_MAX = int(os.getenv("PLAN_TODO_WRITE_MAX", "10"))
MAX_REJECTION_LIMIT = int(os.getenv("MAX_REJECTION_LIMIT", "50"))

# Inject .UPD_RULE.md before default RULES in system prompt so it takes precedence.
# true  = PROJECT RULES appear before default RULES (recommended)
# false = PROJECT RULES appear after (old behavior — may be overridden by defaults)
UPD_RULE_PRIORITY_INJECT = os.getenv("UPD_RULE_PRIORITY_INJECT", "false").lower() in ("true", "1", "yes")

# Periodically re-inject .UPD_RULE.md into continuation_prompt every turn.
# true  = remind the model of PROJECT RULES alongside each task reminder
# false = PROJECT RULES only in system prompt (may be forgotten in long sessions)
UPD_RULE_PERIODIC_INJECT = os.getenv("UPD_RULE_PERIODIC_INJECT", "false").lower() in ("true", "1", "yes")

# Auto-advance to next todo when current step completes
# If False, todos stay in_progress until manually completed
TODO_AUTO_ADVANCE = os.getenv("TODO_AUTO_ADVANCE", "true").lower() in ("true", "1", "yes")

# ============================================================
# Proactive Mode Configuration
# ============================================================
# When enabled, the agent will show a proactive message after idle timeout
PROACTIVE_ENABLED = os.getenv("PROACTIVE_ENABLED", "false").lower() in ("true", "1", "yes")
PROACTIVE_IDLE_SECONDS = int(os.getenv("PROACTIVE_IDLE_SECONDS", "30"))
PROACTIVE_MESSAGE = os.getenv("PROACTIVE_MESSAGE", "🤔 Still here? Need help with anything?")
PROACTIVE_MAX_CYCLES = int(os.getenv("PROACTIVE_MAX_CYCLES", "10"))  # Max proactive injections before stopping (0 = unlimited)

# ============================================================
# TodoWrite Tool (Claude Code Integration)
# ============================================================
# Enable TodoWrite as an explicit tool (in addition to auto-parsing)
# When enabled, LLM can explicitly call todo_write() tool
# When disabled, only auto-parsing from text works (legacy behavior)
ENABLE_TODO_WRITE_TOOL = os.getenv("ENABLE_TODO_WRITE_TOOL", "true").lower() in ("true", "1", "yes")

# Enhanced tool descriptions with Claude Code patterns
# Adds "parallel execution", "when NOT to use", and detailed parameter constraints
# When disabled, uses legacy simple descriptions
ENABLE_ENHANCED_TOOL_DESCRIPTIONS = os.getenv("ENABLE_ENHANCED_TOOL_DESCRIPTIONS", "true").lower() in ("true", "1", "yes")

# ============================================================
# Multiline Input (prompt_toolkit)
# ============================================================
# Enable multiline input mode using prompt_toolkit
# When enabled: Enter = newline, Meta+Enter (ESC then Enter) or Ctrl+D = submit
# When disabled: standard single-line input() (default)
ENABLE_MULTILINE_INPUT = os.getenv("ENABLE_MULTILINE_INPUT", "true").lower() in ("true", "1", "yes")

# UI mode: "textual" (terminal TUI) | "web" (FastAPI + SSE browser UI) | "atlas" (Atlas WebSocket UI)
UI_MODE = os.getenv("UI_MODE", "textual").lower()
WEB_UI_PORT = int(os.getenv("WEB_UI_PORT", "8080"))
ATLAS_UI_PORT = int(os.getenv("ATLAS_UI_PORT", "8765"))

# Atlas UI center column layout:
#   "classic" (default): chat feed + inline ask_user prompt — original behavior.
#   "tabbed":            Chat / Preview / Q&A tabs in the center column;
#                        UI auto-switches to Q&A when ask_user fires and back
#                        to Chat after submission. Mirrors the textual UI's
#                        breadcrumb-tab batched ask_user flow.
ATLAS_CENTER_LAYOUT = os.getenv("ATLAS_CENTER_LAYOUT", "classic").lower()
if ATLAS_CENTER_LAYOUT not in ("classic", "tabbed"):
    ATLAS_CENTER_LAYOUT = "classic"

# Atlas chat feed cleanup layer:
#   true  = concise reasoning tail + cleaned todo/tool summaries (default)
#   false = show rawer reasoning/tool output for debugging the transcript
ATLAS_CHAT_FEED_SUMMARY = _env_bool("ATLAS_CHAT_FEED_SUMMARY", "true")

# sim_debug elaboration backend: "dual" | "pyslang" | "verilator" | "slang"
# Used by /api/hierarchy and /api/trace. Override via the
# SIM_DEBUG_ELAB_BACKEND env var or this config value.
SIM_DEBUG_ELAB_BACKEND = os.getenv("SIM_DEBUG_ELAB_BACKEND", "dual").lower()

# ============================================================
# Phase 4: Autonomous Decision-Making
# ============================================================

# LLM 기반 복잡도 분석 활성화
# When enabled, uses LLM to analyze task complexity instead of simple heuristics
AUTONOMOUS_COMPLEXITY_ANALYSIS = os.getenv("AUTONOMOUS_COMPLEXITY_ANALYSIS", "false").lower() in ("true", "1", "yes")

# LLM 복잡도 분석 시 사용할 temperature (0.0-1.0)
# Lower = more consistent, Higher = more creative
AUTONOMOUS_TEMPERATURE = float(os.getenv("AUTONOMOUS_TEMPERATURE", "0.3"))

# System Prompt with ReAct instructions
SYSTEM_PROMPT = """You are an intelligent coding agent named Common AI Agent.
You can read files, write code, and run terminal commands to help the user.
Always use surgical edits (replace_in_file or multi_replace) to modify only the necessary parts and save tokens.

TOOLS:
You have access to the following tools:

Basic File Tools:
1. read_file(path="path/to/file") - Read entire file content
2. write_file(path="path/to/file", content="file content") - Write/overwrite file
3. run_command(command="ls -la") - Execute shell commands
4. list_dir(path=".") - List directory contents

File Search & Navigation:
5. grep_file(pattern="regex_pattern", path="path/to/file", context_lines=2) - Search for pattern in file with context
6. read_lines(path="path/to/file", start_line=10, end_line=20) - Read specific line range
7. find_files(pattern="*.py", directory=".", max_depth=None) - Find files matching pattern

File Editing:
8. replace_in_file(path="path/to/file", old_text="old", new_text="new", count=-1, start_line=None, end_line=None) - Replace text occurrences (optionally within specific lines)
9. replace_lines(path="path/to/file", start_line=10, end_line=20, new_content="new code") - Replace line range

Git Tools:
10. git_status() - Show current git status
11. git_diff(path=None) - Show git diff (optionally for specific file)
12. git_revert(path="path/to/file") - Revert uncommitted changes to a file

Sub-Agent Tools:
30. background_task(agent="workflow", prompt="implement the change") - Delegate to sub-agent (explore/workflow)
31. background_output(task_id="bg_xxxx") - Get background task result
32. todo_update(index=1, status="completed") - Update todo item status (index is REQUIRED and MUST be 1-based. 1=first task, 2=second, etc.)

RELIABILITY RULES:
1. Always update your todo status immediately after completing the associated work in the SAME TURN.
2. Use the exact 1-based index provided in the "[Todo X/Y] Next Task N: ..." status footer.

FORMAT:
To use a tool, you must use the following format exactly:

Thought: [Your reasoning about what to do next]
Action: [ToolName]([Arguments])

CRITICAL: NEVER use "tool_call" or any other block format. ALWAYS use "Action:".

The user will then respond with:
Observation: [Output of the tool]

You can then continue with more Thought/Action/Observation steps.
When you have finished the task or need to ask the user a question, respond normally (without Action:).

CRITICAL - DO NOT GENERATE OBSERVATIONS:
You must NEVER generate lines starting with "Observation:".
The system will provide the Observation to you after you execute an Action.
If you generate "Observation:", the system will think you are done and stop.
ALWAYS wait for the system to provide the Observation.

CRITICAL - Triple-Quoted Strings:
When writing files with multi-line content, you MUST use actual triple quotes.

DO NOT USE PLACEHOLDERS OR PSEUDO-CODE:
❌ WRONG: content=TRIPLE_QUOTE_START...TRIPLE_QUOTE_END
❌ WRONG: content="[your code here]"
❌ WRONG: content="..." (placeholder)

CORRECT FORMAT - Use actual triple quotes (three double-quotes or three single-quotes):
✅ CORRECT: content=\"\"\"actual code here\"\"\"
✅ CORRECT: content='''actual code here'''

This is MANDATORY for:
- Source code files (.py, .v, .c, .js, etc.)
- Configuration files (.yaml, .json, .toml, etc.)
- Scripts (.sh, .bash, etc.)
- Any content with multiple lines

EXAMPLES:

Example 1 - Single line content:
User: Create a hello world python file.
Thought: I need to create a file named hello.py.
Action: write_file(path="hello.py", content="print('Hello World')")
Observation: Successfully wrote to 'hello.py'.

Example 2 - Multi-line content (USE ACTUAL TRIPLE QUOTES):
User: Create a Python hello world script.
Thought: I need to create hello.py with proper Python syntax. I will use triple quotes.
Action: write_file(path="hello.py", content=\"\"\"#!/usr/bin/env python3

def main():
    print("Hello World")

if __name__ == "__main__":
    main()
\"\"\")
Observation: Successfully wrote to 'hello.py'.

ERROR RECOVERY - NEVER GIVE UP:
You are a persistent agent. When you encounter errors, you MUST analyze and fix them.
NEVER output phrases like "I give up" or "I cannot proceed".

When a command or action fails:
1. Read the error message carefully
2. Identify the root cause
3. Use diagnostic tools (read_lines, grep_file) to examine the problem
4. Fix the issue (replace_in_file, replace_lines, or write_file)
5. Retry the failed command
6. Repeat up to 3 times before asking user for help

Example Error Recovery Workflow:
User: Run the tests
Action: run_command(command="pytest test_utils.py")
Observation: Error: test_utils.py:15: SyntaxError: invalid syntax

Thought: There's a syntax error at line 15. Let me examine the code around that line.
Action: read_lines(path="test_utils.py", start_line=13, end_line=17)
Observation: 13: def test_calculation():
14: result = calculate(10, 20  <- missing closing parenthesis
15: assert result == 30

Thought: I see the problem - missing closing parenthesis on line 14. Let me fix it.
Action: replace_in_file(path="test_utils.py", old_text="result = calculate(10, 20", new_text="result = calculate(10, 20)", start_line=14, end_line=14)
Observation: Replaced 1 occurrence in test_utils.py

Thought: Now let me retry the tests.
Action: run_command(command="pytest test_utils.py")
Observation: Success! All tests passed.

ANOTHER ERROR RECOVERY EXAMPLE - Import Issues:
Action: run_command(command="python main.py")
Observation: Error: ModuleNotFoundError: No module named 'utils'

Thought: Let me check the import statements and file structure.
Action: read_lines(path="main.py", start_line=1, end_line=5)
Observation: Shows import structure

Thought: The import path is incorrect. Let me check if utils.py exists.
Action: list_dir(path=".")
Observation: [File list showing utils.py in src/ subdirectory]

Thought: I need to fix the import path to include the src directory.
Action: replace_in_file(path="main.py", old_text="import utils", new_text="from src import utils")
Observation: Replaced 1 occurrence in main.py

Thought: Now let me retry execution.
Action: run_command(command="python main.py")
Observation: Success!

PERSISTENCE RULES:
- Try fixing at least 3 times before asking for help
- Always examine the actual code when errors occur
- Use read_lines to see context around error locations
- Use replace_in_file for small targeted fixes
- Use write_file for major restructuring
- After fixing, ALWAYS retry the failed command
- Keep trying until success or 3 failed fix attempts
IMPORTANT: You can execute MULTIPLE actions in a single turn.
If you need to run multiple commands or read multiple files, list them one after another.

Example of Multi-Action:
Thought: I need to check two files.
Action: read_file(path="file1.py")
Action: read_file(path="file2.py")

The system will execute them sequentially and provide all observations.

TASK TRACKING (for complex multi-step tasks):
**IMPORTANT: Only use TodoWrite when the user explicitly asks you to create a todo list or track tasks. Do NOT proactively create todos without being instructed.**
When working on complex tasks with multiple steps, use TodoWrite to track progress:

TodoWrite:
- [ ] Step 1: Explore existing implementations
- [ ] Step 2: Design interface specification
- [ ] Step 3: Implement RTL
- [ ] Step 4: Create testbench
- [ ] Step 5: Run simulation

The system will automatically:
1. Mark current step as "in progress" (▶️)
2. Mark completed steps as "done" (✅)
3. Show progress visualization

Only ONE step can be in_progress at a time.
Mark steps complete IMMEDIATELY after finishing them.

Example with TodoWrite:
Thought: This task requires multiple steps. Let me create a todo list.
TodoWrite:
- [ ] Explore codebase for similar modules
- [ ] Design the interface
- [ ] Write the implementation
- [ ] Test the module

Thought: Now let me start with the first step.
Action: grep_file(pattern="module.*fifo", path="*.v")

# ============================================================
# AUTONOMOUS DECISION-MAKING (Phase 4)
# ============================================================

When deciding how to approach a task, consider:

1. **Task Complexity**:
   - Simple (1-2 actions): Direct execution
   - Medium (3-5 steps): Direct execution (do NOT auto-create todos)
   - Complex (6+ steps): Direct execution unless user explicitly asks for todo tracking

2. **Tool Selection**:
   - **Parallel execution**: Use multiple read-only tools simultaneously
   - **Sequential execution**: Write tools create barriers
   - **Sub-agents**: Use background_task for delegation
   - **Todo tracking**: Use todo_update/todo_add for task progress during execution

Focus on using the right tools for the task at hand.

"""

# ============================================================
# Tool Description System (OpenCode Integration)
# ============================================================

# Backup of original SYSTEM_PROMPT for legacy mode
LEGACY_SYSTEM_PROMPT = SYSTEM_PROMPT


def _load_prompt_fragment(filename: str):
    """
    Load workflow/prompts/<filename>. Returns None if not found (→ hardcoded fallback).
    Priority:
      1. Active workspace prompts/<filename>   (workspace-specific override)
      2. workflow/prompts/<filename>            (shared fragment)
    """
    import builtins as _b
    candidates = []
    ws_msgs = getattr(_b, "_WORKSPACE_HOOK_MESSAGES", {})
    ws_dir = ws_msgs.get("_workspace_dir")
    if ws_dir:
        candidates.append(Path(ws_dir) / "prompts" / filename)
    candidates.append(Path(__file__).parent.parent / "workflow" / "prompts" / filename)
    for p in candidates:
        try:
            if p.exists():
                return p.read_text(encoding="utf-8").strip()
        except Exception:
            pass
    return None


def build_base_system_prompt(allowed_tools: set = None, plan_mode: bool = False, todo_active: bool = False) -> str:
    """
    Build compact system prompt (~5K tokens).
    Tool descriptions are minimal (name + signature + when-to-use).
    Detailed examples removed — LLM infers usage from signatures.
    """
    # cursor-agent backend: use dedicated minimal prompt so cursor-agent
    # outputs Action: lines for todo tracking instead of using internal tools
    if CURSOR_AGENT_ENABLE:
        import os as _os
        _prompt_path = _os.path.join(
            _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
            "workflow", "prompts", "cursor_agent.md"
        )
        try:
            with open(_prompt_path, "r") as _f:
                return _f.read()
        except Exception:
            pass  # fall through to normal prompt

    if not ENABLE_TOOL_DESCRIPTIONS:
        # Legacy fallback
        return LEGACY_SYSTEM_PROMPT

    try:
        from core import tools
    except ImportError:
        return LEGACY_SYSTEM_PROMPT

    # Determine tool list
    if allowed_tools is None:
        tool_list = set(tools.AVAILABLE_TOOLS.keys())
    else:
        tool_list = set(t for t in tools.AVAILABLE_TOOLS if t in allowed_tools)

    # Filter out blocked tools based on mode
    if plan_mode:
        tool_list = tool_list - PLAN_MODE_BLOCKED_TOOLS
    else:
        tool_list = tool_list - NORMAL_MODE_BLOCKED_TOOLS

    def _tool_line(name, sig, desc):
        """Format one tool line, only if available."""
        if name in tool_list:
            return f"- {name}({sig}) — {desc}"
        return None

    # ── COMPACT TOOL TABLE ──
    tool_lines = {
        "File I/O": [
            _tool_line("read_file", 'path', "Read entire file. Use instead of run_command(cat). For large files, use grep_file first."),
            _tool_line("read_lines", 'path, start_line, end_line', "Read line range. Use after grep to target sections."),
            _tool_line("write_file", 'path, content', "Write file. Use instead of run_command(echo/tee). Create NEW or overwrite."),
            _tool_line("replace_in_file", 'path, old_text, new_text', "Edit existing files. ALWAYS read first to get exact text."),
            _tool_line("replace_lines", 'path, start_line, end_line, new_content', "Replace line range in existing files."),
            _tool_line("list_dir", 'path', "List directory contents. Use instead of run_command(ls)."),
            _tool_line("run_command", 'command', "Execute shell command. Use ONLY for: build, test, git, simulation, make. NOT for reading/writing/searching files or listing dirs."),
        ],
        "Search": [
            _tool_line("grep_file", 'pattern, path', "Regex search in file(s). Use instead of run_command(grep). Use BEFORE read_file on large files."),
            _tool_line("find_files", 'pattern, path', "Glob search for files. Use instead of run_command(find). Prefer over repeated list_dir."),
        ],
        "Git": [
            _tool_line("git_status", '', "Show working tree status."),
            _tool_line("git_diff", 'path', "Show unstaged changes."),
            _tool_line("git_revert", 'path', "Revert uncommitted changes to a file."),
        ]
    }

    # Task Management (conditional)
    # todo_write is DESTRUCTIVE — replaces the entire task list — so it stays
    # plan-mode-only regardless of UNLOCK_NORMAL_MODE_TOOLS. Without this
    # restriction the agent can wipe a 12-item list down to 3 just by
    # re-emitting todo_write during execution. Use todo_add / todo_update /
    # todo_remove for incremental edits in Normal mode.
    _unlock_all = UNLOCK_NORMAL_MODE_TOOLS
    task_tools = []
    if plan_mode:
        task_tools.append(_tool_line("todo_write", 'tasks', "Create task list (Plan Mode only — REPLACES all existing tasks). Format: [{content, activeForm, status, command, on_reject}]. command: shell str or {tool,args} dict — runs LLM-free, auto approved/rejected. on_reject: 1-based task index to jump to on failure."))
    if plan_mode or _unlock_all:
        task_tools.append(_tool_line("todo_remove", 'index', "Remove a task (index REQUIRED, 1-based)."))

    if todo_active or _unlock_all:
        task_tools.append(_tool_line("todo_update", 'index, status, content, detail', "Update task status (index REQUIRED, 1-based)."))
        task_tools.append(_tool_line("todo_add", 'content, priority, index', "Add task (index is target position, 1-based) — non-destructive, use this in Normal mode instead of todo_write."))
        task_tools.append(_tool_line("todo_status", '', "Show current task progress."))
    
    task_tools = [t for t in task_tools if t]
    if task_tools:
        tool_lines["Task Management"] = task_tools

    # Workflow / IP scaffolding / interactive Q&A (visible in text mode too).
    # Atlas uses /new-ip as the single user-facing IP creation flow; keep
    # scaffold_ip visible only as a legacy/internal fallback for older prompts.
    workflow_tools = [
        _tool_line("scaffold_ip", 'name, root="."',
                   "Create the canonical IP directory layout under <root>/<name>/ "
                   "(yaml, rtl, list, tb, tc, sim, sdc, lint, doc, req). "
                   "Idempotent legacy fallback. Prefer /new-ip <name>; do not "
                   "call scaffold_ip after /new-ip because /new-ip already "
                   "created the layout and initial SSOT draft."),
        _tool_line("ask_user", 'question, kind, options=[], subtitle="", questions=None',
                   "Ask the user one or more decisions via the GUI/TUI and "
                   "BLOCK until answered. Single mode: pass question+kind+options. "
                   "kind: single|multi|input. options: list of {id,label,detail?}. "
                   "BATCHED mode: pass questions=[{question,kind,options,subtitle}, ...] "
                   "to ask N related questions at once — user navigates with ←/→ and "
                   "submits all in one click (much less disruptive than N sequential "
                   "calls). PREFER batched when you have multiple related TBDs."),
        _tool_line("read_doc", 'path',
                   "Convert PDF/DOCX/PPTX/XLSX/HTML → markdown (≤32k chars) via "
                   "markitdown. Use when the user references a spec/datasheet/"
                   "requirement doc in a non-text format."),
    ]
    workflow_tools = [t for t in workflow_tools if t]
    if workflow_tools:
        tool_lines["Workflow"] = workflow_tools

    tool_lines["Sub-Agents"] = [
        _tool_line("background_task", 'agent, prompt', "Delegate to sub-agent (explore/workflow)."),
        _tool_line("background_output", 'task_id', "Get sub-agent result."),
        _tool_line("background_cancel", 'task_id', "Cancel sub-agent."),
        _tool_line("background_list", '', "List active sub-agents."),
    ]

    # Worker tools (Commander → Worker HTTP dispatch)
    worker_tools = [
        _tool_line("worker_call", 'worker, task, model="", timeout=600', "Send task to Worker agent (HTTP). Blocks until done. Returns result dict."),
        _tool_line("worker_status", 'worker, run_id', "Poll Worker run progress."),
        _tool_line("worker_result", 'worker, run_id', "Get Worker run final result."),
    ]
    worker_tools = [t for t in worker_tools if t]
    if worker_tools:
        tool_lines["Worker (Remote)"] = worker_tools

    # Spec navigation tools
    if "spec_navigate" in tool_list:
        tool_lines["Spec Navigation"] = [
            _tool_line("spec_navigate", 'spec, node_id="root"',
                       "Navigate PCIe/UCIe/NVMe spec by section ID. "
                       "Start with node_id='root' for TOC, drill into sections. "
                       "Leaf nodes contain full spec text. Use for ALL spec questions."),
        ]

    # cmux tools (conditional)
    if ENABLE_CMUX_TOOLS and "cmux_capture" in tool_list:
        tool_lines["cmux (modifiable_ai_agent)"] = [
            _tool_line("cmux_tree",               '',                      "List all cmux surfaces. Run first to find surface refs."),
            _tool_line("cmux_capture",            'lines=200',             "Capture modifiable_ai_agent screen text."),
            _tool_line("cmux_send",               'text',                  "Send text to modifiable_ai_agent (Enter auto-appended)."),
            _tool_line("cmux_send_key",           'key',                   "Send special key (ctrl+c, ctrl+q, escape, enter)."),
            _tool_line("cmux_restart_modifiable", '',                      "Quit and restart modifiable_ai_agent."),
            _tool_line("cmux_set_surface",        'surface_ref',           "Save surface ref to config for other cmux tools."),
            _tool_line("cmux_notify",             'title, body=""',        "Send macOS notification."),
            _tool_line("cmux_new_pane",           'direction="right", command=""',       "Split current workspace: create new pane (left/right/up/down)."),
            _tool_line("cmux_new_workspace",      'name="", command="", cwd=""',         "Create a new cmux workspace, optionally running a command."),
            _tool_line("cmux_list_panes",         'workspace=""',                        "List panes in current (or given) workspace."),
            _tool_line("cmux_focus_pane",         'pane',                                "Move focus to a pane by ref (e.g. 'pane:1')."),
            _tool_line("cmux_resize_pane",        'pane, direction, amount=5',           "Resize a pane: direction L/R/U/D, amount in cells."),
            _tool_line("cmux_move_surface",       'surface, direction',                  "Drag a surface into a new split pane (left/right/up/down)."),
        ]

    # tmux tools (conditional)
    if ENABLE_TMUX_TOOLS and "tmux_capture" in tool_list:
        tool_lines["tmux"] = [
            _tool_line("tmux_list_panes",         '',                      "List all panes in the agentic tmux session."),
            _tool_line("tmux_capture",            'pane="agentic:0.0", lines=200', "Capture pane screen text."),
            _tool_line("tmux_send_keys",          'keys, pane="agentic:0.0"',      "Send keys to a pane (Enter auto-appended)."),
            _tool_line("tmux_new_window",         'name="", command=""',   "Create a new tmux window."),
            _tool_line("tmux_kill_pane",          'pane',                  "Kill a tmux pane."),
        ]

    # Verilog tools (conditional)
    if ENABLE_VERILOG_TOOLS and "analyze_verilog_module" in tool_list:
        tool_lines["Verilog Analysis"] = [
            _tool_line("analyze_verilog_module", 'path', "Parse module ports, parameters, FSM."),
            _tool_line("find_signal_usage", 'signal, path', "Find signal assignments/references."),
            _tool_line("find_module_definition", 'module_name, directory', "Locate module source file."),
            _tool_line("extract_module_hierarchy", 'path', "Get instantiation tree."),
            _tool_line("generate_module_testbench", 'path', "Auto-generate testbench."),
            _tool_line("find_potential_issues", 'path', "Lint-like checks."),
            _tool_line("analyze_timing_paths", 'path', "Timing analysis hints."),
            _tool_line("generate_module_docs", 'path', "Auto-generate documentation."),
            _tool_line("suggest_optimizations", 'path', "Optimization suggestions."),
        ]

    # Web tools (conditional — requires Firecrawl)
    if ENABLE_WEB_TOOLS and "web_search" in tool_list:
        tool_lines["Web"] = [
            _tool_line("web_search", 'query, limit=5, lang="en", tbs=""', "Search the web via Firecrawl. Returns titles, URLs, content."),
            _tool_line("web_fetch", 'url, formats="markdown"', "Scrape a URL and return markdown/html content."),
            _tool_line("web_extract", 'urls, prompt="", schema=""', "Extract structured data from URLs using AI."),
        ]
 
    # Image tools (conditional — requires ENABLE_IMAGE_READ=true)
    if ENABLE_IMAGE_READ and "read_image" in tool_list:
        tool_lines["Image"] = [
            _tool_line("read_image", 'path, prompt="Describe this image in detail."', "Analyze image via vision model. Supports PNG/JPEG/GIF/WebP/BMP."),
        ]

    # ── BUILD PROMPT ──
    parts = []

    # Identity
    # Skip base identity when a workspace is active — the workspace system_prompt.md
    # defines the agent role. Injecting a second "coding agent" label here causes
    # the LLM to answer "who are you" with the base identity instead of the workspace role.
    _active_ws = os.environ.get("ACTIVE_WORKSPACE", "").strip()
    if not _active_ws:
        _identity = _load_prompt_fragment("identity.md")
        parts.append(
            (_identity + "\n") if _identity else "You are Common AI Agent, an intelligent coding agent.\n"
        )

    # Format
    _native_mode = os.getenv("ENABLE_NATIVE_TOOL_CALLS", "false").lower() in ("true", "1", "yes")
    # Codex/Responses API models tend to echo ReAct templates literally — use simpler format
    _codex_mode = False
    try:
        from src.llm_client import is_responses_api_model
        _codex_mode = is_responses_api_model()
    except ImportError:
        pass

    if _native_mode or _codex_mode:
        parts.append(
            "Use the provided function tools to complete tasks. "
            "Call tools when you need information or to take actions. "
            "You may call multiple tools in one turn for parallel execution.\n"
        )
    else:
        _fmt = _load_prompt_fragment("format.md")
        parts.append(
            (_fmt + "\n") if _fmt else (
                "FORMAT (strict ReAct loop):\n"
                "Thought: [reasoning]\n"
                "Action: tool_name(arg=\"value\")\n"
                "- Multiple Actions per turn = parallel execution.\n"
                "- Use triple quotes for multi-line: content=\"\"\"...\"\"\".\n"
                "- NEVER generate \"Observation:\" — the system provides it.\n"
                "- NEVER say 'Let me check...' or 'I will...' without an Action in the same turn.\n"
                "- If you need information, call the tool NOW — do not narrate first.\n"
            )
        )

    # Tool table (skip in native mode — LLM sees schemas via API tools param)
    if _native_mode:
        parts.append("TOOLS: (use function tools provided by the API)\n")
    else:
        parts.append("TOOLS:\n")
        for category, lines in tool_lines.items():
            available = [l for l in lines if l is not None]
            if available:
                parts.append(f"{category}:")
                parts.extend(available)
                parts.append("")

    # .UPD_RULE.md — load early so PROJECT RULES can override defaults below
    _upd_rule_paths = [
        Path.home() / ".common_ai_agent" / ".UPD_RULE.md",   # global
        Path(__file__).parent.parent / ".UPD_RULE.md",        # project
    ]
    _upd_rule_parts = []
    for _p in _upd_rule_paths:
        if _p.exists():
            try:
                _text = _p.read_text(encoding="utf-8").strip()
                if _text:
                    _upd_rule_parts.append(_text)
            except Exception:
                pass
    _upd_rule_text = "\n\n".join(_upd_rule_parts) if _upd_rule_parts else ""

    # PROJECT RULES injected BEFORE default rules so they take precedence
    if _upd_rule_text and UPD_RULE_PRIORITY_INJECT:
        parts.append(
            "\n=== PROJECT RULES (override defaults below) ===\n"
            + _upd_rule_text
            + "\n=== END PROJECT RULES ===\n"
        )
    elif _upd_rule_text:
        # Legacy: append after rules (lower priority)
        parts.append("\n=== PROJECT RULES ===\n" + _upd_rule_text + "\n=====================")

    # Core rules — try loading from file first, fall back to hardcoded
    _rules_file = _load_prompt_fragment("rules_normal.md") if not plan_mode else None
    if _rules_file:
        parts.append(_rules_file + "\n")
        # Append Plan Mode instructions if active
        if plan_mode:
            _plan_rules = _load_prompt_fragment("rules_plan.md")
            if _plan_rules:
                parts.append(_plan_rules + "\n")
            parts.append(PLAN_MODE_PROMPT)
        return "\n".join(parts)

    # Core rules (compressed) — PROJECT RULES above override these if they conflict
    rules_parts = [
        "RULES (defaults — PROJECT RULES above take precedence):\n",
        "\n1. PARALLEL EXECUTION:\n",
        "   - Read-only tools are parallel-safe: read_file, read_lines, grep_file, list_dir, find_files, git_status, git_diff.\n"
    ]
    if not plan_mode:
        rules_parts.append("   - Write tools create sequential barriers: write_file, replace_in_file, run_command.\n")

    rules_parts.append("\n2. FILE OPERATIONS:\n")
    if plan_mode:
        rules_parts.append("   - You are in PLAN MODE. File modifications are BLOCKED until the plan is confirmed.\n")
    else:
        rules_parts.append("   - New file → write_file(). Existing file → replace_in_file(). NEVER write_file() on existing.\n")
        rules_parts.append("   - ALWAYS read_file/read_lines BEFORE replace_in_file. Copy exact text including indentation.\n")
        rules_parts.append("   - Include 5+ lines of context in old_text for unique matching.\n")

    if not plan_mode:
        rules_parts.append(
            "\n3. TODO TOOLS — MANDATORY WORKFLOW:\n"
            "   - When a todo list is active, EVERY task MUST follow this exact sequence:\n"
            "       (a) todo_update(index=N, status='in_progress')   ← BEFORE any work on task N\n"
            "       (b) Do the work (write_file, replace_in_file, run_command, …)\n"
            "       (c) todo_update(index=N, status='completed')    ← AFTER work is done\n"
            "       (d) Verify the result\n"
            "       (e) todo_update(index=N, status='approved', reason='what you verified')\n"
            "   - NEVER write files, run commands, or invoke any mutating tool while the\n"
            "     current task is still 'pending'. Bump it to 'in_progress' first.\n"
            "   - Only ONE task may be 'in_progress' at a time. Bump previous to 'completed'\n"
            "     before starting the next.\n"
            "   - Do NOT call todo_write in execution mode (Plan Mode only).\n"
            "   - If you need to rewrite the entire task list, switch back to Plan Mode.\n"
        )

    rules_parts.append(
        "\n4. LARGE FILE STRATEGY:\n"
        "   - Files >500 lines: grep_file first → read_lines on found sections. Never blind-read.\n"
        "\n"
        "5. SEARCH PRIORITY: grep_file > find_files > list_dir.\n"
        "   - Search in current directory (.) first. NEVER expand to parent dirs unless explicitly told.\n"
        "   - If not found in ., report it — do not guess other locations.\n"
        "\n"
        "6. SURGICAL EDITING:\n"
        "   - Replace ONLY the specific changed block. Never replace entire classes/functions for small changes.\n"
        "   - Always include 5+ lines of surrounding context in old_text for unique matching.\n"
        "\n"
        "7. ANTI-HALLUCINATION:\n"
        "   - Never analyze a file you haven't read. Never invent tool results.\n"
        "   - If tool fails, adapt search — don't pretend results exist.\n"
    )
    if not ENABLE_MARKDOWN_RENDER:
        rules_parts.append(
            "\n8. TEXT FORMATTING:\n"
            "   - Markdown rendering is DISABLED. Do NOT use markdown syntax "
            "(like ``` , **, _, ##) in your thoughts or responses. Provide plain text only.\n"
        )
    parts.append("".join(rules_parts))

    # Append Plan Mode instructions if active
    if plan_mode:
        _plan_rules = _load_prompt_fragment("rules_plan.md")
        if _plan_rules:
            parts.append(_plan_rules + "\n")
        parts.append(PLAN_MODE_PROMPT)

    return "\n".join(parts)


PLAN_MODE_BLOCKED_TOOLS = frozenset({
    'write_file', 'replace_in_file', 'replace_lines',
    'replace_file_content', 'multi_replace_file_content',
    'apply_diffs', 'run_command', 'git_revert',
    'background_task', 'background_output', 'spawn_explore',
} | (set() if UNLOCK_NORMAL_MODE_TOOLS else {
    # Plan-mode default: use todo_write/todo_add/todo_remove instead of
    # todo_update (which is for execution).
    'todo_update',
}))

# Tools blocked in Normal/Execution mode. Per user request, todo_write is now
# permitted in normal mode too — the agent occasionally needs to (re)build
# the task list mid-execution (e.g. after an unexpected branch in a workflow).
# UNLOCK_NORMAL_MODE_TOOLS=true continues to unlock todo_remove.
NORMAL_MODE_BLOCKED_TOOLS = frozenset() if UNLOCK_NORMAL_MODE_TOOLS else frozenset({
    'todo_remove',  # Task removal only during planning when unlock is off
})


# Update SYSTEM_PROMPT to use new tool description system
# This will be overridden by build_system_prompt() in main.py when needed
SYSTEM_PROMPT = build_base_system_prompt()

# ============================================================
# Mode Prompts
# ============================================================

PLAN_MODE_PROMPT = """

🚨 === PLAN MODE === 🚨
You are in PLAN MODE. Your job is to research and build a concrete task list — NOT to execute.

════════════════════════════════════════
🔴 HARD CONTRACT — TOOL CALLS ARE STRUCTURED, NOT CONTENT 🔴
════════════════════════════════════════
todo_write / todo_add / todo_remove MUST be emitted as REAL native tool
calls (the `tool_calls` field of the assistant message, with name +
arguments JSON). They MUST NOT appear as plain text in the assistant
content stream.

NEVER emit any of these patterns as content text — they are bugs:
  ✗  `to=functions.todo_write {...}`
  ✗  `<|assistant|>to=functions.todo_write {...}`
  ✗  ```json {"todos": [...]}```          ← raw JSON block standing in for a call
  ✗  `Let's execute tool. todo_write(...)` ← prose narrating a call instead of calling it
  ✗  any "channel" / "commentary" markers, ChatML harmony tokens, or function-name
     prefixes leaked into content

If you find yourself ABOUT to type any of those, STOP and emit the
structured tool call instead. The harness only counts a tool call when
it lands in the `tool_calls` field — text that looks like a tool call
is silently dropped, the user has to retry, and you fall into a
retry loop.

✓ The ONLY correct way is: produce a tool_calls entry with
  name="todo_write" and a valid arguments JSON object. The harness
  will dispatch the tool and feed the result back as a `tool` role
  message. Same for todo_add, todo_remove, read_file, grep_file, etc.

════════════════════════════════════════
🟡 ARGUMENT NAMES — use the canonical key
════════════════════════════════════════
The canonical, schema-defined argument keys are:

  todo_write    →  todos=[...]                (NOT items, list, todo_list, data)
  todo_add      →  content="...", activeForm="...", priority="..."
                                              (NOT text, task, description, title, name)
  todo_remove   →  index=<1-based int>        (NOT idx, position, id)
  todo_update   →  index=<int>, status="...", reason="..."

The harness contains a forgiveness layer that maps a few common alias
keys (`items`, `list`, `todo_list`, `text`, `task`, `description`...)
to their canonical equivalents — but DO NOT rely on it. The aliases
exist only to recover from accidental key drift; emitting the wrong
key still wastes a turn and may not be recovered if multiple aliases
collide. Use the canonical names from the start.

WRONG (will work but wastes a turn):
  todo_write(items=[{...}])
  todo_add(text="run lint")

RIGHT:
  todo_write(todos=[{...}])
  todo_add(content="run lint")

════════════════════════════════════════
WORKFLOW
════════════════════════════════════════
1. RESEARCH   → Use read_file, grep_file, list_dir (as TOOL CALLS) to understand the codebase.
2. TODO_WRITE → Call todo_write() AS A TOOL CALL (not as text) to create the task list.
3. REFINE     → Adjust with todo_add / todo_remove (TOOL CALLS) based on user feedback.
4. CONFIRM    → Wait for user approval ('y' / 'confirm' / 'go') before execution.

════════════════════════════════════════
ALLOWED TODO TOOLS  (emit as native tool calls — NEVER as content text)
════════════════════════════════════════
todo_write(todos=[...])
  Create or fully replace the task list. Use this first to establish the plan.
  ⚠️  Emit this as a tool_calls entry. If the harness logs your assistant
      message with `to=functions.todo_write` text in the content body,
      the call did NOT register — re-emit it as a structured tool call.
  Each task — ALL fields REQUIRED (never leave detail or criteria empty):
    {
      "content":    "Short past-tense label (shown when completed)",
      "activeForm": "Present-progressive label (shown while running)",
      "status":     "pending",   # always pending in plan mode
      "priority":   "high",      # high | medium | low
      "detail":     "HOW to implement — specific approach, file paths, key constraints",
      "criteria":   "Newline-separated acceptance checklist (2–4 items)\nEach line = one verifiable condition"
    }

  Example:
    todo_write(todos=[
      {"content": "Analyzed counter module", "activeForm": "Analyzing counter module",
       "status": "pending", "priority": "high",
       "detail": "Read counter.v, identify all ports, FSM states, and clock domains",
       "criteria": "All ports listed\nFSM states documented\nClock domains identified"},
      {"content": "Wrote testbench", "activeForm": "Writing testbench",
       "status": "pending", "priority": "high",
       "detail": "SystemVerilog TB with clock gen, DUT instantiation, directed test cases",
       "criteria": "File compiles without errors\nAll DUT ports connected\nAt least 3 test cases"}
    ])

  Static command fields (optional — run WITHOUT LLM):
    "command":   "make lint"          → shell string executed directly
                 {"tool": "run_command", "args": {"command": "make sim"}}  → tool call
                 Success → auto-approved. Failure → auto-rejected. Output saved to session log.
    "on_reject": 2                    → jump to Task 2 on failure (enables retry loops)

  Static command pipeline example:
    todo_write(todos=[
      {"content": "Implemented RTL",   "activeForm": "Implementing RTL",   "priority": "high",
       "detail": "Write counter.sv with AXI4 interface"},
      {"content": "Passed lint",       "activeForm": "Running lint",
       "command": "verilator --lint-only rtl/*.sv 2>&1", "on_reject": 1},
      {"content": "Passed simulation", "activeForm": "Running simulation",
       "command": "make sim", "on_reject": 1},
      {"content": "Reviewed results",  "activeForm": "Reviewing results",
       "criteria": "Lint clean\nSimulation passes\nCoverage > 80%"},
    ])

todo_add(content, activeForm="", priority="medium", detail="", index=None)
  Append or insert one task. index= is 1-based; omit to append at end.
  Example:
    todo_add(content="Verified timing constraints", activeForm="Verifying timing constraints",
             priority="high", index=2)

todo_remove(index)
  Remove a task by 1-based index.
  Example:
    todo_remove(index=3)

════════════════════════════════════════
BLOCKED IN PLAN MODE
════════════════════════════════════════
🚫 write_file, replace_in_file, replace_lines — DO NOT attempt file writes. They are BLOCKED.
   → Instead: describe WHAT the file should contain in the task's `detail` field.
   → Actual file writing happens in execution mode after plan approval.
   → If you get "[Plan Mode] 'write_file' is blocked" — do NOT retry. Call todo_write() instead.

🚫 run_command, background_task — DO NOT run commands or spawn agents. BLOCKED.
   → Instead: put the command to run as a step in the task's `detail` field.

🚫 todo_update  — DO NOT call todo_update in plan mode. It is blocked.
                  Use todo_add to add tasks, todo_remove to delete, todo_write to replace.
                  todo_update is for execution mode only (marking tasks in_progress / completed).

════════════════════════════════════════
RULES
════════════════════════════════════════
- Read freely: read_file, grep_file, list_dir, read_lines are all available.
- worker_call, worker_status, worker_result are available — you can dispatch tasks to Workers during planning.
- Always call todo_write before asking the user to confirm.
- Keep tasks atomic — one clear deliverable per task.
- Use detail= for acceptance criteria or implementation notes.
- Refine the list as research reveals more — do not rush to confirm.
- Do not begin execution until user explicitly approves.

  Worker command example (static — runs WITHOUT LLM):
    {"tool": "worker_call", "args": {"worker": "http://localhost:8001", "task": "Write hello.txt"}}
    The Worker executes the task; success → auto-approved, failure → auto-rejected.

════════════════════════════════════════
/todo REFERENCE  (user slash commands)
════════════════════════════════════════
  /todo                     show current list
  /todo add <text>          add a task
  /todo rm <N>              remove task N
  /todo mv <N> <M>          move task N to position M
  /todo g <N> <text>        change task N content
  /todo s <N> <status>      force status (p/i/c/a/r)
  /todo s all <status>      force all tasks to a status
  /todo e <N> <field> <val> edit a field

Edit fields: c=content  d=detail  cr=criteria  pr=priority  af=active_form
AI status flow: pending → in_progress → completed → approved

════════════════════════════════════════
SELF-CHECK BEFORE EVERY ASSISTANT TURN
════════════════════════════════════════
Before you finalize a turn that mentions todo_write/todo_add/todo_remove
(or any other tool), verify all four:
  1. STRUCTURED   — emitted as a tool_calls entry (name + arguments JSON),
                    NOT as plain text in the content body
  2. CANONICAL    — argument keys are the canonical names (todos= / content=
                    / index=), not aliases (items / text / idx)
  3. NON-EMPTY    — todos= is a non-empty list; content= is a non-empty
                    string. Empty arguments waste the turn
  4. NO LEAKAGE   — content body has NO `to=functions.X`, no harmony channel
                    markers, no JSON code fences pretending to be a call

If any of (1)–(4) is wrong, the call is invisible or rejected. Re-issue
as a clean structured tool_calls entry.

If your prior turn shows `to=functions.X` or any harmony/channel
marker in content, that call FAILED. Apologize briefly, retry the
SAME tool as a structured tool_calls entry — do not retype the JSON
in content again.

════════════════════════════════════════
RECOVERY FROM A FAILED TOOL CALL
════════════════════════════════════════
If you receive a tool result like:

  Error: 'todos' parameter is required and must be a non-empty list
  Error: 'content' is required.
  Error: 'index' must be a 1-based integer
  TypeError: todo_write() got an unexpected keyword argument 'items'

…it means your prior tool_calls entry had wrong/missing/empty arguments
or used a non-canonical key. DO:
  1. Read the error message literally
  2. Re-emit the SAME tool with corrected canonical arguments
  3. Do NOT switch tools, do NOT add a long explanation, do NOT
     repeat the same wrong call. Fix and retry once.

If the same error fires twice in a row with the same arguments, stop
and ask the user — there may be a deeper schema/version mismatch.
=================="""
