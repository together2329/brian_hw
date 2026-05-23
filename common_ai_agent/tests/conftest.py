"""
Pytest configuration and fixtures for test_core
"""
import sys
import os

# Add paths for imports
_tests_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_tests_dir)
sys.path.insert(0, os.path.join(_project_root, 'src'))  # config, llm_client etc.
sys.path.insert(0, _project_root)                        # core.*, lib.*, agents.*

import pytest


# Directories under tests/ that import dead modules or were never updated
# after the agents.* package was removed. Listed here so `pytest tests/`
# just works for a new contributor without 7 --ignore flags. The files
# themselves remain in the repo so the deletion can be tracked
# separately in `doc/wiki/atlas-test-feature-coverage.md` §5.1.
collect_ignore_glob = [
    "test_agents/*",
    "test_core/test_context_logging.py",
    "test_core/test_debug_config.py",
    "test_integration/test_agent_iterations.py",
    "test_integration/test_rag_interactive.py",
    "test_lib/test_deep_think.py",
    "test_lib/test_readline_autocomplete.py",
    "test_e2e.py",
    "test_worker_cmux.py",  # needs cmux env; run manually with `pytest tests/test_worker_cmux.py`
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
