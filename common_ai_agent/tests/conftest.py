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
