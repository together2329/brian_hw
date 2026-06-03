"""
Pytest configuration and fixtures for test_core
"""
import sys
import os

# Keep the developer's local .env from leaking SCM provider/adapter overrides
# into the test suite. core.chat_responder auto-loads .env at import time
# (load_dotenv, override=False), so a dev who set ATLAS_SCM_PROVIDER=perforce /
# ATLAS_SCM_ADAPTER_PERFORCE in .env would otherwise change provider-resolution
# defaults for every test. setdefault keeps an explicit shell export winning,
# while pinning a clean ("auto", no override) baseline; tests that exercise a
# specific provider set these via monkeypatch.
os.environ.setdefault("ATLAS_SCM_PROVIDER", "")
os.environ.setdefault("ATLAS_SCM_ADAPTER_PERFORCE", "")

# Same isolation for the interactive worker/runtime settings. Pin env keys
# before .env auto-loads (override=False) so local runtime settings do not leak
# into pytest. Empty worker-policy/max-active values exercise the CODE default:
# strict single-active-owner with the built-in cap. Tests that need session-scoped
# or runtime-db session mode opt in with monkeypatch. Explicit shell exports still
# win (setdefault).
os.environ.setdefault("ATLAS_SESSION_WORKER_POLICY", "")
os.environ.setdefault("ATLAS_SESSION_WORKER_MAX_ACTIVE", "")
os.environ.setdefault("ATLAS_RUNTIME_DB_MODE", "central")

# Add paths for imports
_tests_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_tests_dir)
sys.path.insert(0, os.path.join(_project_root, 'src'))  # config, llm_client etc.
sys.path.insert(0, _project_root)                        # core.*, lib.*, agents.*

import pytest


# Directories under tests/ that import dead modules or need special env.
# Listed here so `pytest tests/` just works for a new contributor without
# explicit --ignore flags.
collect_ignore_glob = [
    "test_integration/test_rag_interactive.py",
    "test_lib/test_deep_think.py",
    "test_lib/test_readline_autocomplete.py",
    "test_e2e.py",
    "test_worker_cmux.py",  # needs cmux env; run manually with `pytest tests/test_worker_cmux.py`
    "test_performance.py",  # imports memory.py / procedural_memory.py (modules removed)
]


def pytest_configure(config):
    """Drop stale user-site plugins that are not part of this repo."""
    pm = config.pluginmanager
    for plugin in list(pm.get_plugins()):
        if getattr(plugin, "__name__", "") == "pytest_plugin.pytest_pymtl3":
            pm.unregister(plugin)


@pytest.fixture(scope="session")
def rag_database():
    """Shared RAG database instance for tests"""
    from core.rag_db import RAGDatabase
    return RAGDatabase()


@pytest.fixture(scope="session")
def graph_lite():
    """Shared GraphLite instance for tests"""
    from core.graph_lite import GraphLite
    return GraphLite()
