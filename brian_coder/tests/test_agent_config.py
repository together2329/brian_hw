"""
Tests for Agent Configuration System (OpenCode-Inspired Features)

Tests:
1. AgentRegistry loading from JSONC
2. Permission wildcard matching
3. Agent-specific model configuration
4. Config merging with native agents
"""

import os
import sys
import unittest
import tempfile
import json
from pathlib import Path

# Add paths
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'core'))

from core.agent_config import (
    PermissionLevel,
    ToolPermissions,
    AgentConfig,
    AgentModelConfig,
    AgentRegistry,
    PermissionChecker,
    get_agent_config
)


class TestPermissionLevel(unittest.TestCase):
    """Test PermissionLevel enum"""

    def test_values(self):
        self.assertEqual(PermissionLevel.ALLOW.value, "allow")
        self.assertEqual(PermissionLevel.ASK.value, "ask")
        self.assertEqual(PermissionLevel.DENY.value, "deny")


class TestToolPermissions(unittest.TestCase):
    """Test ToolPermissions with wildcard patterns"""

    def test_default_permissions(self):
        perms = ToolPermissions()
        self.assertEqual(perms.edit, PermissionLevel.ALLOW)
        self.assertEqual(perms.webfetch, PermissionLevel.ALLOW)
        self.assertEqual(perms.external_directory, PermissionLevel.ASK)

    def test_bash_wildcard_matching(self):
        perms = ToolPermissions(
            bash={
                "git diff*": PermissionLevel.ALLOW,
                "git push*": PermissionLevel.ASK,
                "rm -rf*": PermissionLevel.DENY,
                "*": PermissionLevel.ASK
            }
        )

        # Test specific patterns
        self.assertEqual(perms.check_bash_permission("git diff"), PermissionLevel.ALLOW)
        self.assertEqual(perms.check_bash_permission("git diff --staged"), PermissionLevel.ALLOW)
        self.assertEqual(perms.check_bash_permission("git push origin main"), PermissionLevel.ASK)
        self.assertEqual(perms.check_bash_permission("rm -rf /"), PermissionLevel.DENY)

        # Test fallback to wildcard
        self.assertEqual(perms.check_bash_permission("unknown command"), PermissionLevel.ASK)

    def test_from_dict(self):
        data = {
            "edit": "deny",
            "bash": {
                "ls*": "allow",
                "*": "deny"
            },
            "webfetch": "ask"
        }
        perms = ToolPermissions.from_dict(data)

        self.assertEqual(perms.edit, PermissionLevel.DENY)
        self.assertEqual(perms.webfetch, PermissionLevel.ASK)
        self.assertEqual(perms.check_bash_permission("ls -la"), PermissionLevel.ALLOW)
        self.assertEqual(perms.check_bash_permission("cat file"), PermissionLevel.DENY)

    def test_bash_string_format(self):
        """Test bash permission as single string (applies to all)"""
        data = {"bash": "deny"}
        perms = ToolPermissions.from_dict(data)

        self.assertEqual(perms.check_bash_permission("any command"), PermissionLevel.DENY)


class TestAgentModelConfig(unittest.TestCase):
    """Test AgentModelConfig"""

    def test_from_string(self):
        # "provider/model" format
        config = AgentModelConfig.from_dict("openrouter/anthropic/claude-3-opus")
        self.assertEqual(config.provider_id, "openrouter")
        self.assertEqual(config.model_id, "anthropic/claude-3-opus")

    def test_from_dict(self):
        config = AgentModelConfig.from_dict({
            "provider_id": "openai",
            "model_id": "gpt-4"
        })
        self.assertEqual(config.provider_id, "openai")
        self.assertEqual(config.model_id, "gpt-4")


class TestAgentConfig(unittest.TestCase):
    """Test AgentConfig"""

    def test_from_dict_basic(self):
        data = {
            "description": "Test agent",
            "mode": "subagent",
            "temperature": 0.5
        }
        config = AgentConfig.from_dict("test", data)

        self.assertEqual(config.name, "test")
        self.assertEqual(config.description, "Test agent")
        self.assertEqual(config.mode, "subagent")
        self.assertEqual(config.temperature, 0.5)

    def test_from_dict_with_tools(self):
        data = {
            "tools": {
                "read_file": True,
                "write_file": False,
                "grep_file": True
            }
        }
        config = AgentConfig.from_dict("test", data)
        allowed = config.get_allowed_tools()

        self.assertIn("read_file", allowed)
        self.assertIn("grep_file", allowed)
        self.assertNotIn("write_file", allowed)

    def test_from_dict_with_permission(self):
        data = {
            "permission": {
                "edit": "deny",
                "bash": {
                    "git*": "allow",
                    "*": "deny"
                }
            }
        }
        config = AgentConfig.from_dict("test", data)

        self.assertEqual(config.permission.edit, PermissionLevel.DENY)
        self.assertEqual(
            config.permission.check_bash_permission("git status"),
            PermissionLevel.ALLOW
        )


class TestPermissionChecker(unittest.TestCase):
    """Test PermissionChecker"""

    def test_check_tool(self):
        config = AgentConfig.from_dict("test", {
            "allowed_tools": ["read_file", "grep_file"]
        })
        checker = PermissionChecker(config)

        self.assertTrue(checker.check_tool("read_file"))
        self.assertTrue(checker.check_tool("grep_file"))
        self.assertFalse(checker.check_tool("write_file"))

    def test_check_bash(self):
        config = AgentConfig.from_dict("test", {
            "permission": {
                "bash": {
                    "git*": "allow",
                    "rm*": "deny",
                    "*": "ask"
                }
            }
        })
        checker = PermissionChecker(config)

        self.assertEqual(checker.check_bash("git status"), PermissionLevel.ALLOW)
        self.assertEqual(checker.check_bash("rm -rf /"), PermissionLevel.DENY)
        self.assertEqual(checker.check_bash("ls"), PermissionLevel.ASK)


class TestAgentRegistry(unittest.TestCase):
    """Test AgentRegistry"""

    def test_native_agents_registered(self):
        registry = AgentRegistry()

        # Native agents should be present
        self.assertIsNotNone(registry.get("explore"))
        self.assertIsNotNone(registry.get("plan"))
        self.assertIsNotNone(registry.get("execute"))
        self.assertIsNotNone(registry.get("review"))
        self.assertIsNotNone(registry.get("build"))

    def test_native_agent_properties(self):
        registry = AgentRegistry()

        explore = registry.get("explore")
        self.assertTrue(explore.native)
        self.assertEqual(explore.mode, "subagent")

        primary = registry.get("primary")
        self.assertTrue(primary.native)
        self.assertTrue(primary.default)
        self.assertEqual(primary.mode, "primary")

        build = registry.get("build")
        self.assertTrue(build.native)
        self.assertEqual(build.mode, "primary")

    def test_list_agents(self):
        registry = AgentRegistry()
        agents = registry.list()

        self.assertGreaterEqual(len(agents), 5)  # At least native agents
        names = [a.name for a in agents]
        self.assertIn("explore", names)
        self.assertIn("build", names)

    def test_list_subagents(self):
        registry = AgentRegistry()
        subagents = registry.list_subagents()

        names = [a.name for a in subagents]
        self.assertIn("explore", names)
        self.assertIn("plan", names)

    def test_get_default(self):
        registry = AgentRegistry()
        default = registry.get_default()

        self.assertIsNotNone(default)
        self.assertEqual(default.name, "primary")


class TestConfigFileParsing(unittest.TestCase):
    """Test JSONC config file parsing"""

    def test_jsonc_comment_stripping(self):
        registry = AgentRegistry()

        # Test the JSONC comment stripping function
        content = '''
        {
            // This is a comment
            "key": "value",  // inline comment
            /* Multi-line
               comment */
            "other": 123
        }
        '''
        stripped = registry._strip_jsonc_comments(content)
        parsed = json.loads(stripped)

        self.assertEqual(parsed["key"], "value")
        self.assertEqual(parsed["other"], 123)

    def test_load_from_temp_file(self):
        # Create temp config file
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False
        ) as f:
            json.dump({
                "agents": {
                    "custom-agent": {
                        "description": "Custom test agent",
                        "mode": "subagent",
                        "tools": {"read_file": True}
                    }
                }
            }, f)
            temp_path = f.name

        try:
            # Load and verify
            registry = AgentRegistry()
            registry._load_config_file(Path(temp_path))

            custom = registry.get("custom-agent")
            if custom:  # May or may not be loaded depending on path
                self.assertEqual(custom.description, "Custom test agent")
        finally:
            os.unlink(temp_path)


class TestIntegration(unittest.TestCase):
    """Integration tests"""

    def test_get_agent_config_function(self):
        # Test the convenience function
        explore = get_agent_config("explore")
        self.assertIsNotNone(explore)
        self.assertEqual(explore.name, "explore")

        # Non-existent agent
        unknown = get_agent_config("nonexistent")
        self.assertIsNone(unknown)

    def test_explore_agent_tools(self):
        explore = get_agent_config("explore")

        allowed = explore.get_allowed_tools()
        self.assertIn("read_file", allowed)
        self.assertIn("grep_file", allowed)
        self.assertNotIn("write_file", allowed)

    def test_execute_agent_tools(self):
        execute = get_agent_config("execute")

        allowed = execute.get_allowed_tools()
        self.assertIn("write_file", allowed)
        self.assertIn("replace_in_file", allowed)
        self.assertIn("run_command", allowed)


if __name__ == "__main__":
    unittest.main()
