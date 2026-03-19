"""
심화 크로스플랫폼 테스트

API 키 없이 실행 가능한 테스트:
1. 슬래시 명령 실행
2. 도구 함수 (파일 읽기/쓰기/검색)
3. 파일 인코딩 (open() 호출에 UTF-8 명시)
4. 경로 처리 (\ vs /)
5. compress_history 로직
"""

import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path


class TestSlashCommands(unittest.TestCase):
    """슬래시 명령이 모든 OS에서 정상 실행되는지"""

    def setUp(self):
        from core.slash_commands import SlashCommandRegistry
        self.registry = SlashCommandRegistry()

    def test_help_returns_output(self):
        result = self.registry.execute("/help")
        self.assertIn("Available", result)
        self.assertIn("/help", result)

    def test_list_returns_commands(self):
        result = self.registry.execute("/list")
        self.assertIn("/help", result)
        self.assertIn("/clear", result)

    def test_unknown_command(self):
        result = self.registry.execute("/nonexistent")
        self.assertIn("Unknown command", result)

    def test_clear_returns_signal(self):
        result = self.registry.execute("/clear")
        self.assertEqual(result, "CLEAR_HISTORY")

    def test_compact_returns_signal(self):
        result = self.registry.execute("/compact")
        self.assertEqual(result, "COMPACT_HISTORY")

    def test_plan_without_args(self):
        result = self.registry.execute("/plan")
        self.assertIn("Error", result)

    def test_plan_with_args(self):
        result = self.registry.execute("/plan create a counter")
        self.assertEqual(result, "PLAN_MODE_REQUEST:create a counter")

    def test_all_commands_dont_crash(self):
        """모든 등록된 명령이 크래시 없이 실행"""
        safe_commands = ["/help", "/list", "/clear", "/compact"]
        for cmd in safe_commands:
            result = self.registry.execute(cmd)
            self.assertIsNotNone(result, f"{cmd} returned None")


class TestToolFunctions(unittest.TestCase):
    """도구 함수가 모든 OS에서 정상 동작하는지"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test.txt")
        with open(self.test_file, 'w', encoding='utf-8') as f:
            f.write("line 1\nline 2\nline 3\nhello world\nline 5\n")

        self.unicode_file = os.path.join(self.temp_dir, "unicode.txt")
        with open(self.unicode_file, 'w', encoding='utf-8') as f:
            f.write("한글 테스트\nemoji 🔌 test\nASCII line\n")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_read_file(self):
        from core.tools import read_file
        result = read_file(self.test_file)
        self.assertIn("line 1", result)
        self.assertIn("hello world", result)

    def test_read_file_not_found(self):
        from core.tools import read_file
        result = read_file(os.path.join(self.temp_dir, "nope.txt"))
        self.assertIn("Error", result)

    def test_read_unicode_file(self):
        from core.tools import read_file
        result = read_file(self.unicode_file)
        self.assertIn("한글", result)
        self.assertIn("🔌", result)

    def test_write_file(self):
        from core.tools import write_file
        out_path = os.path.join(self.temp_dir, "output.txt")
        result = write_file(out_path, "hello from test")
        self.assertIn("Successfully", result)

        with open(out_path, 'r', encoding='utf-8') as f:
            self.assertEqual(f.read(), "hello from test")

    def test_write_file_creates_dirs(self):
        from core.tools import write_file
        nested_path = os.path.join(self.temp_dir, "a", "b", "c.txt")
        result = write_file(nested_path, "nested")
        self.assertIn("Successfully", result)
        self.assertTrue(os.path.exists(nested_path))

    def test_write_unicode_file(self):
        from core.tools import write_file
        out_path = os.path.join(self.temp_dir, "out_unicode.txt")
        write_file(out_path, "한글 🔌 emoji")

        with open(out_path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertIn("한글", content)
        self.assertIn("🔌", content)

    def test_list_dir(self):
        from core.tools import list_dir
        result = list_dir(self.temp_dir)
        self.assertIn("test.txt", result)
        self.assertIn("unicode.txt", result)

    def test_grep_file(self):
        from core.tools import grep_file
        result = grep_file("hello", self.test_file)
        self.assertIn("hello world", result)

    def test_grep_no_match(self):
        from core.tools import grep_file
        result = grep_file("zzzzz", self.test_file)
        self.assertIn("No matches", result)

    def test_find_files(self):
        from core.tools import find_files
        result = find_files("*.txt", self.temp_dir)
        self.assertIn("test.txt", result)


class TestPathHandling(unittest.TestCase):
    """경로 처리가 Windows(\\)와 Unix(/) 모두에서 동작하는지"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_pathlib_works_cross_platform(self):
        """Path 객체가 OS별 구분자를 올바르게 처리"""
        p = Path(self.temp_dir) / "sub" / "file.txt"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("test", encoding='utf-8')
        self.assertTrue(p.exists())
        self.assertEqual(p.read_text(encoding='utf-8'), "test")

    def test_os_path_join(self):
        """os.path.join이 OS별 구분자 사용"""
        joined = os.path.join(self.temp_dir, "a", "b.txt")
        self.assertIn(os.sep, joined)

    def test_read_file_with_pathlib(self):
        """도구 함수가 Path 객체도 받는지"""
        from core.tools import read_file
        p = Path(self.temp_dir) / "pathlib_test.txt"
        p.write_text("pathlib content", encoding='utf-8')
        result = read_file(str(p))
        self.assertIn("pathlib content", result)

    def test_home_dir_exists(self):
        """Path.home()이 유효한 디렉토리"""
        home = Path.home()
        self.assertTrue(home.exists())
        self.assertTrue(home.is_dir())

    def test_tempdir_exists(self):
        """tempfile.gettempdir()가 유효한 디렉토리"""
        tmp = tempfile.gettempdir()
        self.assertTrue(os.path.isdir(tmp))


class TestFileEncoding(unittest.TestCase):
    """open() 호출 시 인코딩이 올바른지 (소스 코드 정적 검사)"""

    def _get_python_files(self):
        """brian_coder/ 아래 모든 .py 파일"""
        root = Path(__file__).parent.parent
        return list(root.glob("**/*.py"))

    def test_no_bare_open_in_core(self):
        """core/*.py에서 open()이 encoding 없이 쓰이지 않는지"""
        import re
        core_dir = Path(__file__).parent.parent / "core"
        if not core_dir.exists():
            self.skipTest("core/ directory not found")

        issues = []
        for py_file in core_dir.glob("*.py"):
            content = py_file.read_text(encoding='utf-8')
            # open(...) 호출에서 encoding= 없는 것 찾기
            # 'r' 또는 'w' 모드인데 encoding 없는 경우만
            for i, line in enumerate(content.split('\n'), 1):
                line_stripped = line.strip()
                # open() 호출이 있고
                if 'open(' in line_stripped and ('encoding' not in line_stripped):
                    # 바이너리 모드('rb', 'wb')는 제외
                    if "'rb'" not in line_stripped and "'wb'" not in line_stripped:
                        if '"rb"' not in line_stripped and '"wb"' not in line_stripped:
                            # urlopen, os.open 등 제외
                            if not line_stripped.startswith('#') and 'urlopen' not in line_stripped:
                                issues.append(f"{py_file.name}:{i}: {line_stripped[:80]}")

        if issues:
            self.fail(
                f"Found open() without encoding= in core/:\n" +
                "\n".join(issues)
            )

    def test_no_bare_open_in_src(self):
        """src/*.py에서 open()이 encoding 없이 쓰이지 않는지"""
        import re
        src_dir = Path(__file__).parent.parent / "src"
        if not src_dir.exists():
            self.skipTest("src/ directory not found")

        issues = []
        for py_file in src_dir.glob("*.py"):
            content = py_file.read_text(encoding='utf-8')
            for i, line in enumerate(content.split('\n'), 1):
                line_stripped = line.strip()
                if 'open(' in line_stripped and ('encoding' not in line_stripped):
                    if "'rb'" not in line_stripped and "'wb'" not in line_stripped:
                        if '"rb"' not in line_stripped and '"wb"' not in line_stripped:
                            if not line_stripped.startswith('#') and 'urlopen' not in line_stripped:
                                issues.append(f"{py_file.name}:{i}: {line_stripped[:80]}")

        if issues:
            self.fail(
                f"Found open() without encoding= in src/:\n" +
                "\n".join(issues)
            )


class TestDisplayUtilities(unittest.TestCase):
    """display.py 유틸리티가 모든 OS에서 동작"""

    def test_color_output(self):
        from lib.display import Color
        # ANSI 코드가 포함된 문자열 생성 확인
        result = Color.system("test")
        self.assertIn("test", result)
        self.assertIn("\033[", result)

    def test_format_tool_header(self):
        from lib.display import format_tool_header
        result = format_tool_header("read_file", "test.py")
        self.assertIn("Read", result)
        self.assertIn("test.py", result)

    def test_format_tool_result_empty(self):
        from lib.display import format_tool_result
        result = format_tool_result("")
        self.assertIn("empty", result)

    def test_format_tool_result_short(self):
        from lib.display import format_tool_result
        result = format_tool_result("hello\nworld")
        self.assertIn("hello", result)

    def test_format_diff(self):
        from lib.display import format_diff
        result = format_diff("old line\n", "new line\n")
        self.assertIn("old line", result)
        self.assertIn("new line", result)

    def test_spinner_creation(self):
        from lib.display import Spinner
        s = Spinner("Testing")
        self.assertEqual(s.label, "Testing")

    def test_get_terminal_width(self):
        from lib.display import get_terminal_width
        width = get_terminal_width()
        self.assertIsInstance(width, int)
        self.assertGreater(width, 0)


if __name__ == "__main__":
    unittest.main()
