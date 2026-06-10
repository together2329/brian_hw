"""Tests for src/config.py reload_env() + profile switching.

Covers the contract that fixes the "edited .env but UI still shows old
model" bug: edits to .env must propagate without a process restart, and
profile switching must update BASE_URL+API_KEY+MODEL_NAME atomically.
"""
import importlib
import os
import sys
import unittest
from pathlib import Path
from unittest import mock


_PROJECT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_PROJECT / "src"))


def _fresh_config(env: dict, env_file_text: str = ""):
    """Reload src.config under a controlled os.environ + temp .env path.

    Patches the search path list so the module reads only the temp file
    (no leakage from the real ~/.config or project .env), then forces a
    re-import so module-level globals are recomputed.
    """
    desired_env = dict(env)
    import config as _cfg
    importlib.reload(_cfg)
    # config.py loads the real project .env during import. Keep these tests
    # hermetic by restoring the caller-supplied model/profile environment and
    # then refreshing module globals from that controlled state.
    controlled_prefixes = ("LLM_", "PROFILE_", "MODEL_NAME",
                           "PRIMARY_MODEL", "SECONDARY_MODEL")
    for key in list(os.environ):
        if key.startswith(controlled_prefixes) and key not in desired_env:
            os.environ.pop(key, None)
    for key, value in desired_env.items():
        if key.startswith(controlled_prefixes):
            os.environ[key] = value
    _cfg._refresh_runtime_globals()
    active_profile = os.environ.get("LLM_PROFILE", "").strip()
    if active_profile:
        _cfg._apply_profile(active_profile)
    return _cfg


class TestReloadEnv(unittest.TestCase):
    """reload_env() must pick up .env edits via mtime watching."""

    def setUp(self):
        # Save and clear LLM_* + PROFILE_* so the test doesn't depend on
        # whatever the real shell happens to export.
        self._saved_env = {}
        for k in list(os.environ):
            if k.startswith(("LLM_", "PROFILE_", "MODEL_NAME",
                             "PRIMARY_MODEL", "SECONDARY_MODEL",
                             "USE_OPENCODE_OAUTH", "USE_RESPONSES_API",
                             "OPENCODE_")):
                self._saved_env[k] = os.environ.pop(k)

    def tearDown(self):
        # Restore original env so other tests aren't polluted.
        for k in list(os.environ):
            if k.startswith(("LLM_", "PROFILE_", "MODEL_NAME",
                             "PRIMARY_MODEL", "SECONDARY_MODEL",
                             "USE_OPENCODE_OAUTH", "USE_RESPONSES_API",
                             "OPENCODE_")):
                os.environ.pop(k, None)
        os.environ.update(self._saved_env)

    def test_reload_env_updates_model_name_after_env_edit(self):
        """End-to-end: edit a tmp .env, call reload_env(), MODEL_NAME refreshes.

        Points the search path at a single throwaway tmp file so the test
        is hermetic — the real project .env never participates.
        """
        import tempfile
        import time
        os.environ["LLM_MODEL_NAME"] = "model-a"
        cfg = _fresh_config(os.environ)
        self.assertEqual(cfg.MODEL_NAME, "model-a")

        with tempfile.TemporaryDirectory() as tmp:
            env_path = Path(tmp) / ".env"
            env_path.write_text("LLM_MODEL_NAME=model-b\n")
            # Spoof mtime cache so reload_env sees a "change" → triggers
            # force_reload + refresh of module globals.
            with mock.patch.object(cfg, "_env_search_paths",
                                   return_value=[env_path]):
                cfg._ENV_MTIME_CACHE.clear()
                cfg.reload_env()
        self.assertEqual(cfg.MODEL_NAME, "model-b",
            "reload_env() should pick up the new LLM_MODEL_NAME without restart")

    def test_reload_env_protects_active_workspace(self):
        """ACTIVE_WORKSPACE must NOT be clobbered by .env on reload —
        runtime-set workspace state must survive a config refresh."""
        os.environ["ACTIVE_WORKSPACE"] = "tb-gen"
        cfg = _fresh_config(os.environ)
        cfg._ENV_MTIME_CACHE.clear()
        cfg.reload_env()
        self.assertEqual(os.environ["ACTIVE_WORKSPACE"], "tb-gen")

    def test_reload_env_does_not_rollback_runtime_model_override(self):
        """CLI/slash model switches must not be reverted by .env hot reload.

        This covers `textual_main.py --model gpt-5.3-codex`: healthz calls
        reload_env(), but the UI must keep showing the runtime model instead
        of a stale dropdown selection from .env.
        """
        import tempfile

        os.environ["LLM_MODEL_NAME"] = "gpt-5.3-codex"
        os.environ["MODEL_NAME"] = "gpt-5.3-codex"
        os.environ["LLM_BASE_URL"] = "https://chatgpt.com/backend-api/codex"
        os.environ["LLM_RUNTIME_MODEL_OVERRIDE"] = "1"
        cfg = _fresh_config(os.environ)
        self.assertEqual(cfg.MODEL_NAME, "gpt-5.3-codex")

        with tempfile.TemporaryDirectory() as tmp:
            env_path = Path(tmp) / ".env"
            env_path.write_text(
                "\n".join([
                    "LLM_MODEL_NAME=glm-5.1",
                    "LLM_SELECTED_MODEL_KEY=LLM_MODEL_NAME",
                    "LLM_PROFILE=glm",
                    "PROFILE_glm_MODEL=glm-5.1",
                    "PROFILE_glm_BASE_URL=https://api.z.ai/api/coding/paas/v4",
                    "",
                ]),
                encoding="utf-8",
            )
            with mock.patch.object(cfg, "_env_search_paths", return_value=[env_path]):
                cfg._ENV_MTIME_CACHE.clear()
                cfg.reload_env()

        self.assertEqual(cfg.MODEL_NAME, "gpt-5.3-codex")
        self.assertEqual(os.environ["LLM_MODEL_NAME"], "gpt-5.3-codex")
        self.assertEqual(os.environ["LLM_BASE_URL"], "https://chatgpt.com/backend-api/codex")


class TestProfileSystem(unittest.TestCase):
    """list_profiles / get_profile / set_active_profile contract."""

    def setUp(self):
        self._saved_env = {}
        for k in list(os.environ):
            if k.startswith(("LLM_", "PROFILE_", "MODEL_NAME",
                             "PRIMARY_MODEL", "SECONDARY_MODEL",
                             "USE_OPENCODE_OAUTH", "USE_RESPONSES_API",
                             "OPENCODE_")):
                self._saved_env[k] = os.environ.pop(k)

    def tearDown(self):
        for k in list(os.environ):
            if k.startswith(("LLM_", "PROFILE_", "MODEL_NAME",
                             "PRIMARY_MODEL", "SECONDARY_MODEL",
                             "USE_OPENCODE_OAUTH", "USE_RESPONSES_API",
                             "OPENCODE_")):
                os.environ.pop(k, None)
        os.environ.update(self._saved_env)

    def test_list_profiles_finds_defined_names(self):
        os.environ["PROFILE_glm_MODEL"] = "glm-5.1"
        os.environ["PROFILE_glm_BASE_URL"] = "https://glm.example.com"
        os.environ["PROFILE_kimi_MODEL"] = "kimi-2.6"
        cfg = _fresh_config(os.environ)
        self.assertEqual(cfg.list_profiles(), ["glm", "kimi"])

    def test_get_profile_returns_full_trio(self):
        os.environ["PROFILE_deepseek_BASE_URL"] = "https://api.deepseek.com"
        os.environ["PROFILE_deepseek_API_KEY"] = "sk-deepseek"
        os.environ["PROFILE_deepseek_MODEL"] = "deepseek-v4-pro"
        cfg = _fresh_config(os.environ)
        p = cfg.get_profile("deepseek")
        self.assertEqual(p["model"], "deepseek-v4-pro")
        self.assertEqual(p["base_url"], "https://api.deepseek.com")
        self.assertEqual(p["api_key"], "sk-deepseek")

    def test_get_profile_unknown_returns_empty(self):
        cfg = _fresh_config(os.environ)
        self.assertEqual(cfg.get_profile("nonexistent"), {})

    def test_get_profile_falls_back_to_legacy_keys(self):
        """When PROFILE_<n>_BASE_URL/API_KEY are omitted, fall back to
        the top-level LLM_BASE_URL/LLM_API_KEY (same-provider, different-
        model use case)."""
        os.environ["LLM_BASE_URL"] = "https://shared.example.com"
        os.environ["LLM_API_KEY"] = "shared-key"
        os.environ["PROFILE_alt_MODEL"] = "alt-model"
        cfg = _fresh_config(os.environ)
        p = cfg.get_profile("alt")
        self.assertEqual(p["base_url"], "https://shared.example.com")
        self.assertEqual(p["api_key"], "shared-key")
        self.assertEqual(p["model"], "alt-model")

    def test_set_active_profile_switches_trio_atomically(self):
        os.environ["PROFILE_glm_BASE_URL"] = "https://api.z.ai"
        os.environ["PROFILE_glm_API_KEY"] = "glm-key"
        os.environ["PROFILE_glm_MODEL"] = "glm-5.1"
        cfg = _fresh_config(os.environ)
        ok = cfg.set_active_profile("glm")
        self.assertTrue(ok)
        self.assertEqual(cfg.MODEL_NAME, "glm-5.1")
        self.assertEqual(cfg.BASE_URL, "https://api.z.ai")
        self.assertEqual(cfg.API_KEY, "glm-key")
        # os.environ must mirror so cmux/sub-processes pick it up
        self.assertEqual(os.environ["LLM_MODEL_NAME"], "glm-5.1")
        self.assertEqual(os.environ["LLM_BASE_URL"], "https://api.z.ai")
        self.assertEqual(os.environ["LLM_PROFILE"], "glm")

    def test_set_active_profile_unknown_returns_false(self):
        cfg = _fresh_config(os.environ)
        self.assertFalse(cfg.set_active_profile("does-not-exist"))

    def test_boot_with_llm_profile_env(self):
        """LLM_PROFILE in env at import time activates that profile."""
        os.environ["PROFILE_kimi_MODEL"] = "kimi-2.6"
        os.environ["PROFILE_kimi_BASE_URL"] = "https://kimi.example.com"
        os.environ["PROFILE_kimi_API_KEY"] = "kimi-key"
        os.environ["LLM_PROFILE"] = "kimi"
        cfg = _fresh_config(os.environ)
        self.assertEqual(cfg.MODEL_NAME, "kimi-2.6")
        self.assertEqual(cfg.BASE_URL, "https://kimi.example.com")

    def test_non_opencode_profile_blocks_auto_oauth(self):
        """A provider profile must not be overwritten by default Codex OAuth."""
        os.environ["PROFILE_glm_MODEL"] = "glm-5.1"
        os.environ["PROFILE_glm_BASE_URL"] = "https://api.z.ai"
        os.environ["PROFILE_glm_API_KEY"] = "glm-key"
        os.environ["LLM_PROFILE"] = "glm"
        os.environ["USE_OPENCODE_OAUTH"] = "true"
        cfg = _fresh_config(os.environ)
        self.assertTrue(cfg._active_profile_blocks_auto_opencode())

    def test_profile_fallthrough_uses_original_not_poisoned_topkey(self):
        """review [31]: switching A -> B (B omitting base_url/api_key) must fall
        through to the ORIGINAL top-level LLM_*, never the os.environ value that
        A's apply poisoned — otherwise B's calls go to A's endpoint with A's key.
        """
        import importlib
        # env set BEFORE reload so the import-time original-snapshot captures it
        os.environ["LLM_BASE_URL"] = "https://original.example/v1"
        os.environ["LLM_API_KEY"] = "original-key"
        os.environ["PROFILE_a_MODEL"] = "model-a"
        os.environ["PROFILE_a_BASE_URL"] = "https://provider-a.example/v1"
        os.environ["PROFILE_a_API_KEY"] = "a-key"
        os.environ["PROFILE_b_MODEL"] = "model-b"  # b omits BASE_URL + API_KEY
        import config as cfg
        importlib.reload(cfg)

        self.assertTrue(cfg._apply_profile("a"))
        self.assertEqual(cfg.BASE_URL, "https://provider-a.example/v1")
        # os.environ is now poisoned with A's url; B must NOT inherit it.
        prof_b = cfg.get_profile("b")
        self.assertEqual(prof_b["base_url"], "https://original.example/v1")
        self.assertEqual(prof_b["api_key"], "original-key")
        self.assertTrue(cfg._apply_profile("b"))
        self.assertEqual(cfg.BASE_URL, "https://original.example/v1")
        self.assertEqual(cfg.API_KEY, "original-key")
        self.assertEqual(cfg.MODEL_NAME, "model-b")

    def test_active_provider_returns_consistent_trio(self):
        """review [32]: active_provider() returns the live (base_url, api_key,
        model) trio atomically (same values as the module globals)."""
        os.environ["LLM_BASE_URL"] = "https://prov.example/v1"
        os.environ["LLM_API_KEY"] = "k1"
        os.environ["LLM_MODEL_NAME"] = "m1"
        cfg = _fresh_config(os.environ)
        trio = cfg.active_provider()
        self.assertEqual(trio, (cfg.BASE_URL, cfg.API_KEY, cfg.MODEL_NAME))


if __name__ == "__main__":
    unittest.main()
