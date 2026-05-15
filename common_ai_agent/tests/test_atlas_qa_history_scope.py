from pathlib import Path


WORKSPACE_JSX = Path(__file__).resolve().parents[1] / "frontend" / "atlas" / "workspace.jsx"


def test_qa_history_rejects_legacy_entries_without_scope():
    src = WORKSPACE_JSX.read_text()

    assert "QA_HISTORY_STORAGE_PREFIX = 'atlasQaHistory:'" in src
    assert "const hasEntryScope = !!entrySession || !!entryIp;" in src
    assert (
        "if (!hasEntryScope && (scopeSession || (scopeIp && scopeIp !== 'default'))) return false;"
        in src
    )


def test_qa_history_snapshots_and_rendering_are_scoped():
    src = WORKSPACE_JSX.read_text()

    assert "session: normalizeUiSession(flow.session || currentSession || window.ACTIVE_SESSION || '')" in src
    assert "visibleQaHistory" in src
    assert "QaHistoryPanel history={visibleQaHistory}" not in src
