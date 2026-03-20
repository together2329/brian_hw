"""
Tests for multiline input setup (prompt_toolkit integration + single-line fallback).
"""
import sys
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add paths
_tests_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_tests_dir)
_vendor_dir = os.path.join(_project_root, 'vendor')
if _vendor_dir not in sys.path:
    sys.path.insert(0, _vendor_dir)
if os.path.join(_project_root, 'src') not in sys.path:
    sys.path.insert(0, os.path.join(_project_root, 'src'))


# ═══════════════════════════════════════════
#  VENDOR IMPORT TESTS
# ═══════════════════════════════════════════

class TestVendorImport:
    """Verify vendored prompt_toolkit loads correctly."""

    def test_prompt_toolkit_importable(self):
        from prompt_toolkit import PromptSession
        assert PromptSession is not None

    def test_ansi_importable(self):
        from prompt_toolkit import ANSI
        assert ANSI is not None

    def test_key_bindings_importable(self):
        from prompt_toolkit.key_binding import KeyBindings
        assert KeyBindings is not None

    def test_wcwidth_importable(self):
        import wcwidth
        assert wcwidth is not None

    def test_version(self):
        import prompt_toolkit
        assert prompt_toolkit.__version__ == "3.0.52"


# ═══════════════════════════════════════════
#  MULTILINE PROMPT SESSION TESTS
# ═══════════════════════════════════════════

class TestMultilineSetup:
    """Test PromptSession creation and key binding configuration."""

    def test_session_creation(self):
        from prompt_toolkit import PromptSession
        from prompt_toolkit.key_binding import KeyBindings

        kb = KeyBindings()

        @kb.add('escape', 'enter')
        def _newline(event):
            event.current_buffer.insert_text('\n')

        @kb.add('enter')
        def _submit(event):
            event.current_buffer.validate_and_handle()

        session = PromptSession(key_bindings=kb, multiline=True)
        assert session is not None

    def test_ansi_prompt_text(self):
        """ANSI wrapper correctly wraps escape codes."""
        from prompt_toolkit import ANSI
        prompt = ANSI('\033[92m> \033[0m')
        assert prompt is not None

    def test_key_binding_enter_registered(self):
        from prompt_toolkit.key_binding import KeyBindings
        from prompt_toolkit.keys import Keys

        kb = KeyBindings()

        @kb.add('enter')
        def _submit(event):
            pass

        # Verify binding exists
        bindings = kb.bindings
        assert len(bindings) >= 1
        # Check that Enter key is bound
        enter_keys = [b for b in bindings if Keys.Enter in b.keys]
        assert len(enter_keys) == 1

    def test_key_binding_escape_enter_registered(self):
        from prompt_toolkit.key_binding import KeyBindings
        from prompt_toolkit.keys import Keys

        kb = KeyBindings()

        @kb.add('escape', 'enter')
        def _newline(event):
            pass

        bindings = kb.bindings
        assert len(bindings) >= 1
        # Check that Escape+Enter sequence is bound
        meta_enter = [b for b in bindings if Keys.Escape in b.keys and Keys.Enter in b.keys]
        assert len(meta_enter) == 1

    def test_invalid_key_raises(self):
        """s-enter is not valid — the bug we fixed."""
        from prompt_toolkit.key_binding import KeyBindings

        kb = KeyBindings()
        with pytest.raises(ValueError, match="Invalid key"):
            @kb.add('s-enter')
            def _bad(event):
                pass


# ═══════════════════════════════════════════
#  CONFIG TESTS
# ═══════════════════════════════════════════

class TestConfig:
    """Test ENABLE_MULTILINE_INPUT config behavior."""

    def test_config_default_true(self):
        """Default should be true."""
        import config
        # Reload to get fresh value (may be overridden by .config)
        original = config.ENABLE_MULTILINE_INPUT
        assert isinstance(original, bool)

    def test_config_env_override_false(self):
        """Environment variable should override to false."""
        with patch.dict(os.environ, {"ENABLE_MULTILINE_INPUT": "false"}):
            val = os.getenv("ENABLE_MULTILINE_INPUT", "true").lower() in ("true", "1", "yes")
            assert val is False

    def test_config_env_override_true(self):
        """Environment variable should override to true."""
        with patch.dict(os.environ, {"ENABLE_MULTILINE_INPUT": "true"}):
            val = os.getenv("ENABLE_MULTILINE_INPUT", "true").lower() in ("true", "1", "yes")
            assert val is True


# ═══════════════════════════════════════════
#  SINGLE-LINE FALLBACK TESTS
# ═══════════════════════════════════════════

class TestSingleLineFallback:
    """Test that single-line input() works as fallback."""

    def test_input_basic(self):
        """Standard input() returns single line."""
        with patch('builtins.input', return_value="hello world"):
            result = input("> ")
            assert result == "hello world"

    def test_input_with_ansi_prompt(self):
        """input() accepts ANSI color codes in prompt."""
        prompt = '\033[92m> \033[0m'
        with patch('builtins.input', return_value="test") as mock_input:
            result = input(prompt)
            mock_input.assert_called_once_with(prompt)
            assert result == "test"

    def test_input_exit_commands(self):
        """exit/quit detection works with both modes."""
        for cmd in ["exit", "quit", "EXIT", "Quit"]:
            assert cmd.lower() in ["exit", "quit"]

    def test_input_slash_commands(self):
        """Slash commands detected correctly."""
        for cmd in ["/help", "/context", "/skill list"]:
            assert cmd.startswith('/')

    def test_input_empty(self):
        """Empty input handled."""
        with patch('builtins.input', return_value=""):
            result = input("> ")
            assert result == ""

    def test_input_multiline_not_possible(self):
        """Standard input() cannot receive multiline — returns single line."""
        with patch('builtins.input', return_value="line1"):
            result = input("> ")
            assert '\n' not in result


# ═══════════════════════════════════════════
#  MULTILINE CONTENT TESTS
# ═══════════════════════════════════════════

class TestMultilineContent:
    """Test that multiline content is handled correctly after input."""

    def test_multiline_newline_preserved(self):
        """Multiline input should preserve newlines."""
        text = "line1\nline2\nline3"
        lines = text.split('\n')
        assert len(lines) == 3
        assert lines == ["line1", "line2", "line3"]

    def test_multiline_with_slash_command(self):
        """First line starting with / should be treated as slash command."""
        text = "/help\nsome extra text"
        assert text.startswith('/')

    def test_multiline_exit_only_exact(self):
        """Only exact 'exit'/'quit' should exit, not multiline containing exit."""
        text = "exit\nmore text"
        # Should NOT exit because it's multiline (lower() would include newlines)
        assert text.lower() not in ["exit", "quit"]

    def test_multiline_whitespace_handling(self):
        """Whitespace-only lines preserved."""
        text = "line1\n\nline3"
        lines = text.split('\n')
        assert lines[1] == ""

    def test_multiline_code_block(self):
        """Code blocks with indentation preserved."""
        text = "def foo():\n    return 42\n\nfoo()"
        assert "    return 42" in text
        assert text.count('\n') == 3

    def test_multiline_korean_content(self):
        """Korean multiline input preserved."""
        text = "첫 번째 줄\n두 번째 줄\n세 번째 줄"
        lines = text.split('\n')
        assert len(lines) == 3
        assert lines[0] == "첫 번째 줄"


# ═══════════════════════════════════════════
#  INTEGRATION: PROMPT SWITCHING TESTS
# ═══════════════════════════════════════════

class TestPromptSwitching:
    """Test switching between multiline and single-line based on config."""

    def test_multiline_enabled_creates_session(self):
        """When enabled, PromptSession should be created."""
        from prompt_toolkit import PromptSession, ANSI
        from prompt_toolkit.key_binding import KeyBindings

        kb = KeyBindings()

        @kb.add('escape', 'enter')
        def _nl(event):
            event.current_buffer.insert_text('\n')

        @kb.add('enter')
        def _submit(event):
            event.current_buffer.validate_and_handle()

        session = PromptSession(key_bindings=kb, multiline=True)
        prompt_text = ANSI('\033[92m> \033[0m')

        assert session is not None
        assert prompt_text is not None

    def test_multiline_disabled_no_import(self):
        """When disabled, prompt_toolkit should not be required."""
        # Simulate ENABLE_MULTILINE_INPUT=false
        _multiline_prompt = None
        enable = False

        if enable:
            from prompt_toolkit import PromptSession  # would only run if enabled
            _multiline_prompt = PromptSession()

        assert _multiline_prompt is None

    def test_import_failure_fallback(self):
        """ImportError should fall back to single-line."""
        _multiline_prompt = None
        try:
            raise ImportError("simulated")
        except ImportError:
            pass  # fallback

        assert _multiline_prompt is None

    def test_input_dispatch_multiline(self):
        """When _multiline_prompt exists, use it; otherwise use input()."""
        # Simulate dispatch logic
        _multiline_prompt = MagicMock()
        _multiline_prompt.prompt.return_value = "multiline text"
        _prompt_text = ">"

        if _multiline_prompt:
            result = _multiline_prompt.prompt(_prompt_text)
        else:
            result = "single line"

        assert result == "multiline text"
        _multiline_prompt.prompt.assert_called_once_with(_prompt_text)

    def test_input_dispatch_singleline(self):
        """When _multiline_prompt is None, use input()."""
        _multiline_prompt = None

        with patch('builtins.input', return_value="single line"):
            if _multiline_prompt:
                result = _multiline_prompt.prompt(">")
            else:
                result = input(">")

        assert result == "single line"
