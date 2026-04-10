"""
Pytest configuration for tests/test_workflow/.

Sets up sys.path so `from workflow.loader import ...` resolves without
depending on the parent conftest execution order.
"""
import sys
import os

_this_dir  = os.path.dirname(os.path.abspath(__file__))   # tests/test_workflow/
_tests_dir = os.path.dirname(_this_dir)                    # tests/
_proj_root = os.path.dirname(_tests_dir)                   # common_ai_agent/

sys.path.insert(0, _proj_root)                             # workflow.*, core.*, lib.*
sys.path.insert(0, os.path.join(_proj_root, "src"))        # config, llm_client, etc.

PROJECT_ROOT = _proj_root
WORKFLOW_DIR = os.path.join(_proj_root, "workflow")
