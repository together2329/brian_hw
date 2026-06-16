from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _config_values() -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in (PROJECT_ROOT / ".config").read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def test_checked_in_reasoning_effort_defaults_to_xhigh():
    values = _config_values()
    assert values["REASONING_MODE"] == "xhigh"
    assert values["REASONING_EFFORT"] == "xhigh"


def test_config_code_fallback_reasoning_effort_is_xhigh():
    source = (PROJECT_ROOT / "src" / "config.py").read_text(encoding="utf-8")
    assert 'os.getenv("REASONING_MODE", os.getenv("REASONING_EFFORT", "xhigh"))' in source
