"""
Simple Integration Tests - File Existence and Structure

Tests that key files exist and have expected structure.
"""

import pytest
from pathlib import Path


class TestFileStructure:
    """Test that all required files exist"""

    @pytest.fixture
    def project_root(self):
        """Get project root directory"""
        return Path(__file__).parent.parent.parent

    def test_tool_descriptions_directory_exists(self, project_root):
        """Test tool_descriptions directory was created"""
        tool_desc_dir = project_root / "core" / "tool_descriptions"
        assert tool_desc_dir.exists(), "tool_descriptions directory not found"
        assert tool_desc_dir.is_dir()

    def test_tool_descriptions_init_exists(self, project_root):
        """Test __init__.py exists in tool_descriptions"""
        init_file = project_root / "core" / "tool_descriptions" / "__init__.py"
        assert init_file.exists(), "__init__.py not found"
        assert init_file.is_file()

    def test_tools_directory_exists(self, project_root):
        """Test tools subdirectory exists"""
        tools_dir = project_root / "core" / "tool_descriptions" / "tools"
        assert tools_dir.exists()
        assert tools_dir.is_dir()

    def test_all_5_tool_txt_files_exist(self, project_root):
        """Test all 5 tool .txt files exist"""
        tools_dir = project_root / "core" / "tool_descriptions" / "tools"

        required_files = [
            "read_file.txt",
            "rag_search.txt",
            "write_file.txt",
            "analyze_verilog_module.txt",
            "replace_in_file.txt"
        ]

        for filename in required_files:
            file_path = tools_dir / filename
            assert file_path.exists(), f"{filename} not found"
            assert file_path.is_file()

    def test_config_file_updated(self, project_root):
        """Test .config file has ENABLE_TOOL_DESCRIPTIONS"""
        config_file = project_root / ".config"

        if config_file.exists():
            content = config_file.read_text()
            assert "ENABLE_TOOL_DESCRIPTIONS" in content, \
                   ".config file missing ENABLE_TOOL_DESCRIPTIONS flag"

    def test_config_py_has_function(self, project_root):
        """Test src/config.py has build_base_system_prompt function"""
        config_py = project_root / "src" / "config.py"

        assert config_py.exists(), "src/config.py not found"

        content = config_py.read_text()
        assert "def build_base_system_prompt" in content, \
               "build_base_system_prompt function not found in config.py"
        assert "LEGACY_SYSTEM_PROMPT" in content, \
               "LEGACY_SYSTEM_PROMPT backup not found"

    def test_main_py_updated(self, project_root):
        """Test src/main.py has allowed_tools parameter"""
        main_py = project_root / "src" / "main.py"

        assert main_py.exists(), "src/main.py not found"

        content = main_py.read_text()
        assert "allowed_tools" in content, \
               "allowed_tools parameter not found in main.py"


class TestToolDescriptionContent:
    """Test tool description files have expected content"""

    @pytest.fixture
    def project_root(self):
        return Path(__file__).parent.parent.parent

    @pytest.fixture
    def tools_dir(self, project_root):
        return project_root / "core" / "tool_descriptions" / "tools"

    def test_read_file_txt_content(self, tools_dir):
        """Test read_file.txt has expected sections"""
        file_path = tools_dir / "read_file.txt"
        content = file_path.read_text()

        # Check for required sections
        assert "# Tool:" in content
        assert "## Signature" in content
        assert "## Description" in content
        assert "## Good Examples" in content
        assert "## Bad Examples" in content
        assert "## Verilog" in content or "## verilog" in content.lower()
        assert "## Tool Precedence" in content
        assert "## Error Recovery" in content

    def test_rag_search_txt_content(self, tools_dir):
        """Test rag_search.txt has expected sections"""
        file_path = tools_dir / "rag_search.txt"
        content = file_path.read_text()

        # RAG search specific checks
        assert "semantic" in content.lower() or "RAG" in content
        assert "## Good Examples" in content
        assert "## Bad Examples" in content
        assert "grep" in content.lower(), "Should mention grep comparison"

    def test_all_files_have_minimum_length(self, tools_dir):
        """Test all .txt files meet minimum length requirement"""
        required_files = [
            ("read_file.txt", 120),
            ("rag_search.txt", 150),
            ("write_file.txt", 120),
            ("analyze_verilog_module.txt", 150),
            ("replace_in_file.txt", 180)
        ]

        for filename, min_lines in required_files:
            file_path = tools_dir / filename
            lines = file_path.read_text().split('\n')
            actual_lines = len(lines)

            assert actual_lines >= min_lines, \
                   f"{filename}: Expected >={min_lines} lines, got {actual_lines}"

    def test_all_files_have_good_examples(self, tools_dir):
        """Test all files have Good Examples section with ✅ markers"""
        for txt_file in tools_dir.glob("*.txt"):
            content = txt_file.read_text()
            assert "## Good Examples" in content, f"{txt_file.name} missing Good Examples"
            assert "✅" in content, f"{txt_file.name} missing ✅ markers"

    def test_all_files_have_bad_examples(self, tools_dir):
        """Test all files have Bad Examples section with ❌ markers"""
        for txt_file in tools_dir.glob("*.txt"):
            content = txt_file.read_text()
            assert "## Bad Examples" in content, f"{txt_file.name} missing Bad Examples"
            assert "❌" in content, f"{txt_file.name} missing ❌ markers"


class TestPythonCodeValidity:
    """Test Python code is valid"""

    @pytest.fixture
    def project_root(self):
        return Path(__file__).parent.parent.parent

    def test_init_py_is_valid_python(self, project_root):
        """Test __init__.py is valid Python code"""
        init_file = project_root / "core" / "tool_descriptions" / "__init__.py"

        # This will raise SyntaxError if invalid
        import py_compile
        py_compile.compile(str(init_file), doraise=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
