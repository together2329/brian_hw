"""
Pytest configuration and fixtures for test_core
"""
import sys
import os

# Add paths for imports
_tests_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_tests_dir)
sys.path.insert(0, os.path.join(_project_root, 'src'))
sys.path.insert(0, os.path.join(_project_root, 'core'))
sys.path.insert(0, os.path.join(_project_root, 'lib'))
sys.path.insert(0, os.path.join(_project_root, 'agents'))
sys.path.insert(0, os.path.join(_project_root, 'agents', 'sub_agents'))
sys.path.insert(0, _project_root)

import pytest


@pytest.fixture(scope="session")
def rag_database():
    """Shared RAG database instance for tests"""
    from rag_db import RAGDatabase
    return RAGDatabase()


@pytest.fixture(scope="session")
def graph_lite():
    """Shared GraphLite instance for tests"""
    from graph_lite import GraphLite
    return GraphLite()
