# atlas-pytest-hygiene

## Symptom

pytest collection crashes with:

```
PluginValidationError: unknown hook 'pytest_cmdline_preparse' in plugin <pytest_pymtl3>
INTERNALERROR> ...
```

No tests are collected; the entire run aborts at startup.

## Cause

The system pip package `pytest_plugin/pytest_pymtl3` installed at
`/Users/brian/Library/Python/3.9/lib/python/site-packages/pytest_plugin/pytest_pymtl3.py`
registers the `pytest_cmdline_preparse` hook, which was removed from pytest in
a newer API version. When pytest auto-discovers installed plugins it validates
all hook signatures and raises `PluginValidationError` on the stale hook,
aborting collection before any test file is loaded.

## Resolution

Run pytest with the `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` environment variable.
This prevents pytest from auto-loading installed third-party plugins (including
the broken `pytest_pymtl3`), allowing normal collection and execution.

## Canonical invocation

```
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/ -q
```

For collection-only verification:

```
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/ --collect-only -q
```

See [[atlas-pipeline-screen]] for the broader pipeline test context, and
[[orchestrator-llm-loop-phase3]] for the orchestrator loop implementation that
these tests exercise.
