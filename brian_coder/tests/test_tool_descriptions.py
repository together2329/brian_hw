"""
Unit Tests for Tool Description System

Tests the DescriptionLoader and tool description parsing.
"""

import pytest
from pathlib import Path
import sys
import os

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.tool_descriptions import get_loader, format_tool_for_prompt, ToolDescription


class TestDescriptionLoader:
    """Test DescriptionLoader class"""

    def test_loader_singleton(self):
        """Test that loader is a singleton"""
        loader1 = get_loader()
        loader2 = get_loader()
        assert loader1 is loader2

    def test_loader_initialization(self):
        """Test loader initializes correctly"""
        loader = get_loader()
        assert loader.base_dir is not None
        assert loader.tools_dir is not None
        assert loader.tools_dir.exists()

    def test_get_all_tool_names(self):
        """Test getting list of all tools"""
        loader = get_loader()
        tools = loader.get_all_tool_names()

        # Should have our 5 tools
        expected_tools = ["read_file", "rag_search", "write_file",
                         "analyze_verilog_module", "replace_in_file"]

        for tool in expected_tools:
            assert tool in tools, f"Tool {tool} not found in {tools}"

    def test_load_read_file_description(self):
        """Test loading read_file.txt"""
        loader = get_loader()
        desc = loader.load_tool_description("read_file")

        assert desc is not None
        assert desc.name == "read_file"
        assert desc.description != ""
        assert desc.signature != ""
        assert len(desc.examples_good) >= 5, f"Expected >=5 good examples, got {len(desc.examples_good)}"
        assert len(desc.examples_bad) >= 5, f"Expected >=5 bad examples, got {len(desc.examples_bad)}"
        assert desc.verilog_specific != ""
        assert desc.tool_precedence != ""

    def test_load_rag_search_description(self):
        """Test loading rag_search.txt (most important tool)"""
        loader = get_loader()
        desc = loader.load_tool_description("rag_search")

        assert desc is not None
        assert desc.name == "rag_search"
        assert "semantic" in desc.description.lower() or "RAG" in desc.description
        assert len(desc.examples_good) >= 5
        assert len(desc.examples_bad) >= 5
        assert "rag_search > grep" in desc.tool_precedence.lower() or "prefer rag" in desc.tool_precedence.lower()

    def test_load_all_5_tools(self):
        """Test all Phase 2 tools have valid descriptions"""
        loader = get_loader()
        required_tools = ["read_file", "rag_search", "write_file",
                         "analyze_verilog_module", "replace_in_file"]

        for tool_name in required_tools:
            desc = loader.load_tool_description(tool_name)
            assert desc is not None, f"Tool {tool_name} description not loaded"
            assert desc.name == tool_name
            assert len(desc.examples_good) > 0, f"{tool_name} has no good examples"
            assert len(desc.examples_bad) > 0, f"{tool_name} has no bad examples"

    def test_nonexistent_tool(self):
        """Test loading nonexistent tool returns None"""
        loader = get_loader()
        desc = loader.load_tool_description("nonexistent_tool_xyz")
        assert desc is None

    def test_caching(self):
        """Test that descriptions are cached"""
        loader = get_loader()

        # Load twice
        desc1 = loader.load_tool_description("read_file")
        desc2 = loader.load_tool_description("read_file")

        # Should be same object (cached)
        assert desc1 is desc2


class TestToolDescription:
    """Test ToolDescription dataclass and formatting"""

    def test_format_for_prompt_includes_examples(self):
        """Test formatted output includes good/bad examples"""
        loader = get_loader()
        desc = loader.load_tool_description("read_file")

        formatted = desc.format_for_prompt(include_examples=True)

        # Should include example markers
        assert "✅" in formatted or "Good" in formatted
        assert "❌" in formatted or "Bad" in formatted

        # Should include sections
        assert desc.name in formatted
        assert desc.signature in formatted

    def test_format_for_prompt_without_examples(self):
        """Test formatting without examples"""
        loader = get_loader()
        desc = loader.load_tool_description("read_file")

        formatted = desc.format_for_prompt(include_examples=False)

        # Should still have basic info
        assert desc.name in formatted
        assert desc.signature in formatted

    def test_format_tool_for_prompt_function(self):
        """Test format_tool_for_prompt helper function"""
        formatted = format_tool_for_prompt("read_file", include_examples=True)

        assert "read_file" in formatted
        assert "✅" in formatted or "Good" in formatted
        assert "Verilog" in formatted or "verilog" in formatted

    def test_format_nonexistent_tool(self):
        """Test formatting nonexistent tool returns fallback"""
        formatted = format_tool_for_prompt("nonexistent_tool")

        assert "nonexistent_tool" in formatted
        assert "No detailed description" in formatted


class TestVerilogSpecificContent:
    """Test that Verilog-specific content is present"""

    def test_read_file_verilog_scenarios(self):
        """Test read_file has Verilog examples"""
        loader = get_loader()
        desc = loader.load_tool_description("read_file")

        # Check for Verilog-related keywords
        full_text = desc.description + desc.verilog_specific
        assert any(keyword in full_text.lower() for keyword in
                  ["verilog", "rtl", "testbench", "module"])

    def test_rag_search_verilog_patterns(self):
        """Test rag_search has Verilog query patterns"""
        loader = get_loader()
        desc = loader.load_tool_description("rag_search")

        full_text = desc.description + desc.verilog_specific
        # Should mention signal, FSM, protocol, etc.
        assert any(keyword in full_text.lower() for keyword in
                  ["signal", "fsm", "protocol", "axi", "pcie"])

    def test_analyze_verilog_module_deep_mode(self):
        """Test analyze_verilog_module mentions deep mode"""
        loader = get_loader()
        desc = loader.load_tool_description("analyze_verilog_module")

        full_text = desc.description + desc.signature
        assert "deep" in full_text.lower()
        assert "FSM" in full_text or "fsm" in full_text.lower()


class TestToolPrecedence:
    """Test that tool precedence guidelines are present"""

    def test_rag_search_precedence_over_grep(self):
        """Test rag_search clearly states precedence over grep"""
        loader = get_loader()
        desc = loader.load_tool_description("rag_search")

        precedence_text = desc.tool_precedence.lower()

        # Should mention rag > grep or similar
        assert ("rag" in precedence_text and "grep" in precedence_text) or \
               "prefer" in precedence_text

    def test_replace_in_file_precedence_over_write(self):
        """Test replace_in_file precedence over write_file"""
        loader = get_loader()
        desc = loader.load_tool_description("replace_in_file")

        precedence_text = desc.tool_precedence.lower()

        # Should mention replace > write for modifications
        assert "replace" in precedence_text or "safer" in precedence_text

    def test_all_tools_have_precedence(self):
        """Test all tools have tool precedence section"""
        loader = get_loader()
        tools = ["read_file", "rag_search", "write_file",
                "analyze_verilog_module", "replace_in_file"]

        for tool_name in tools:
            desc = loader.load_tool_description(tool_name)
            assert desc.tool_precedence != "", f"{tool_name} missing tool precedence"


class TestErrorRecovery:
    """Test that error recovery sections exist"""

    def test_all_tools_have_error_recovery(self):
        """Test all tools have error recovery guidelines"""
        loader = get_loader()
        tools = ["read_file", "rag_search", "write_file",
                "analyze_verilog_module", "replace_in_file"]

        for tool_name in tools:
            desc = loader.load_tool_description(tool_name)
            assert len(desc.error_recovery) >= 3, \
                   f"{tool_name} should have >=3 error recovery items, has {len(desc.error_recovery)}"

    def test_replace_in_file_fuzzy_matching(self):
        """Test replace_in_file mentions fuzzy matching strategies"""
        loader = get_loader()
        desc = loader.load_tool_description("replace_in_file")

        full_text = desc.description + " ".join(desc.error_recovery)

        # Should mention fuzzy matching or strategies
        assert "fuzzy" in full_text.lower() or "strategies" in full_text.lower()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
