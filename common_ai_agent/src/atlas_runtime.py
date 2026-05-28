"""ATLAS server runtime — extracted from src/atlas_ui.py.

Hosts the uvicorn/multiprocessing bootstrap (`run_atlas_ui`), the admin
sub-server launcher (`_launch_admin_server`), and the CLI entry point
(`main`). Imports atlas_ui only inside function bodies so this module
loads independently (avoids a top-level circular import while atlas_ui
re-exports `main` / `run_atlas_ui` for backward compat).

Phase 4 of refactor/atlas-modular: move-only (no behavior change).
"""
from __future__ import annotations

import argparse
import asyncio
import errno
import io
import json
import logging
import multiprocessing
import os
import contextvars
import re
import signal
import socket
import subprocess
import sys
import time
import threading
import traceback
import uuid
from pathlib import Path
from typing import Any, Optional

# main() references these as bare names (atlas_ui.py imports them at
# lines 146-151 from core/atlas_exec_policy.py). Import directly here so
# the lookup resolves against this module's globals without going through
# the lazy hydration helper.
from core.atlas_exec_policy import (
    EXEC_MODE_ORCHESTRATOR,
    apply_exec_mode_env,
    current_exec_mode,
    normalize_exec_mode,
)












# The __main__ guard MUST sit after every callee `main()` reaches. Until now
# it lived at line ~1093 — above `_source_root` and `_resolve_workflow_root`
# (orphan-appended by Phase 6a). The bug only surfaced when callers omit
# `--workflow-root`, because the old `main()` guarded the resolver call
# behind `if args.workflow_root:` and that branch swallowed the lookup.


# Phase 28: all entrypoints moved to atlas_runtime_run.py — re-export shim.
from src.atlas_runtime_run import (
    _hydrate_atlas_ui_globals,
    run_atlas_ui,
    _launch_admin_server,
    main,
    _source_root,
    _resolve_workflow_root,
)
