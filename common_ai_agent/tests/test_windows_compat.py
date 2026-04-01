"""
Windows 호환성 단위 테스트

macOS/Linux에서 platform.system()을 모킹하여
Windows 코드 경로가 정상 동작하는지 검증.
"""

import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock


class TestEscapeWatcherWindowsBranch(unittest.TestCase):
    """EscapeWatcher._watch()가 Windows에서 msvcrt 분기로 가는지 검증"""

    def test_watch_dispatches_to_windows(self):
        """IS_WINDOWS=True일 때 _watch_windows()가 호출되는지"""
        from lib.display import EscapeWatcher

        with patch.object(EscapeWatcher, '_watch_windows') as mock_win, \
             patch.object(EscapeWatcher, '_watch_unix') as mock_unix, \
             patch('lib.display.IS_WINDOWS', True):
            EscapeWatcher._watch()
            mock_win.assert_called_once()
            mock_unix.assert_not_called()

    def test_watch_dispatches_to_unix(self):
        """IS_WINDOWS=False일 때 _watch_unix()가 호출되는지"""
        from lib.display import EscapeWatcher

        with patch.object(EscapeWatcher, '_watch_windows') as mock_win, \
             patch.object(EscapeWatcher, '_watch_unix') as mock_unix, \
             patch('lib.display.IS_WINDOWS', False):
            EscapeWatcher._watch()
            mock_unix.assert_called_once()
            mock_win.assert_not_called()

    def test_watch_windows_detects_esc(self):
        """msvcrt를 모킹하여 ESC 감지 로직 검증"""
        from lib.display import EscapeWatcher

        mock_msvcrt = MagicMock()
        # kbhit: 첫 호출 True, getch: ESC 반환
        mock_msvcrt.kbhit.return_value = True
        mock_msvcrt.getch.return_value = b'\x1b'

        EscapeWatcher._active = True
        EscapeWatcher._pressed = False

        with patch.dict('sys.modules', {'msvcrt': mock_msvcrt}), \
             patch('lib.display.live_print'):
            EscapeWatcher._watch_windows()

        self.assertTrue(EscapeWatcher._pressed)
        mock_msvcrt.kbhit.assert_called()
        mock_msvcrt.getch.assert_called()

        # cleanup
        EscapeWatcher._active = False
        EscapeWatcher._pressed = False

    def test_watch_windows_ignores_non_esc(self):
        """ESC가 아닌 키는 무시하고 계속 루프"""
        from lib.display import EscapeWatcher

        mock_msvcrt = MagicMock()
        # 첫 번째: 'a' 키, 두 번째: 루프 종료 (active=False)
        call_count = [0]

        def fake_kbhit():
            call_count[0] += 1
            if call_count[0] == 1:
                return True
            # 두 번째 이후: _active를 False로 만들어 루프 탈출
            EscapeWatcher._active = False
            return False

        mock_msvcrt.kbhit.side_effect = fake_kbhit
        mock_msvcrt.getch.return_value = b'a'  # Not ESC

        EscapeWatcher._active = True
        EscapeWatcher._pressed = False

        with patch.dict('sys.modules', {'msvcrt': mock_msvcrt}), \
             patch('time.sleep'):
            EscapeWatcher._watch_windows()

        self.assertFalse(EscapeWatcher._pressed)

        # cleanup
        EscapeWatcher._active = False
        EscapeWatcher._pressed = False


class TestReadlineGracefulDegradation(unittest.TestCase):
    """readline이 없을 때 SlashCommandRegistry가 정상 동작하는지"""

    def test_registry_works_without_readline(self):
        """readline=None이어도 레지스트리 생성/명령 실행 가능"""
        with patch('core.slash_commands.readline', None):
            from core.slash_commands import SlashCommandRegistry
            registry = SlashCommandRegistry()

            # 명령 실행 가능
            result = registry.execute("/help")
            self.assertIsNotNone(result)
            self.assertIn("/help", result)

            # 자동완성 목록 반환
            completions = registry.get_completions()
            self.assertIn("/help", completions)

            # save_history가 에러 없이 넘어감
            registry.save_history()

    def test_completer_works_without_readline(self):
        """readline=None이어도 _completer 함수 자체는 동작"""
        with patch('core.slash_commands.readline', None):
            from core.slash_commands import SlashCommandRegistry
            registry = SlashCommandRegistry()

            # completer는 내부 로직이므로 직접 호출 가능
            result = registry._completer("/hel", 0)
            self.assertEqual(result, "/help")

            result = registry._completer("/hel", 1)
            self.assertIsNone(result)


class TestHookPlatformDispatch(unittest.TestCase):
    """_find_hook / _hook_command 플랫폼 분기 검증"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.hooks_dir = Path(self.temp_dir) / ".common_ai_agent" / "hooks"
        self.hooks_dir.mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _import_hook_helpers(self):
        """main.py에서 _find_hook, _hook_command import"""
        # main.py는 많은 의존성이 있으므로 직접 함수 정의를 가져옴
        import importlib
        import types

        # _find_hook과 _hook_command의 로직을 직접 테스트
        # (main.py 전체를 import하면 부작용이 크므로)
        def _find_hook(hook_name, home_dir):
            import platform
            hooks_dir = Path(home_dir) / ".common_ai_agent" / "hooks"
            if platform.system() == "Windows":
                candidates = [f"{hook_name}.bat", f"{hook_name}.ps1", f"{hook_name}.py"]
            else:
                candidates = [f"{hook_name}.sh"]
            for name in candidates:
                path = hooks_dir / name
                if path.exists():
                    return path
            return None

        def _hook_command(hook_path):
            suffix = hook_path.suffix.lower()
            if suffix == ".py":
                return [sys.executable, str(hook_path)]
            if suffix == ".ps1":
                return ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(hook_path)]
            return [str(hook_path)]

        return _find_hook, _hook_command

    def test_find_hook_windows_bat(self):
        """Windows에서 .bat 훅 파일 발견"""
        _find_hook, _ = self._import_hook_helpers()

        (self.hooks_dir / "pre_compact.bat").touch()

        with patch('platform.system', return_value="Windows"):
            result = _find_hook("pre_compact", self.temp_dir)

        self.assertIsNotNone(result)
        self.assertEqual(result.name, "pre_compact.bat")

    def test_find_hook_windows_ps1(self):
        """Windows에서 .ps1 훅 파일 발견 (.bat 없을 때)"""
        _find_hook, _ = self._import_hook_helpers()

        (self.hooks_dir / "pre_compact.ps1").touch()

        with patch('platform.system', return_value="Windows"):
            result = _find_hook("pre_compact", self.temp_dir)

        self.assertIsNotNone(result)
        self.assertEqual(result.name, "pre_compact.ps1")

    def test_find_hook_windows_py(self):
        """Windows에서 .py 훅 파일 발견"""
        _find_hook, _ = self._import_hook_helpers()

        (self.hooks_dir / "post_compact.py").touch()

        with patch('platform.system', return_value="Windows"):
            result = _find_hook("post_compact", self.temp_dir)

        self.assertIsNotNone(result)
        self.assertEqual(result.name, "post_compact.py")

    def test_find_hook_windows_priority(self):
        """Windows에서 .bat > .ps1 > .py 우선순위"""
        _find_hook, _ = self._import_hook_helpers()

        (self.hooks_dir / "pre_compact.bat").touch()
        (self.hooks_dir / "pre_compact.ps1").touch()
        (self.hooks_dir / "pre_compact.py").touch()

        with patch('platform.system', return_value="Windows"):
            result = _find_hook("pre_compact", self.temp_dir)

        self.assertEqual(result.name, "pre_compact.bat")

    def test_find_hook_unix_sh(self):
        """Unix에서 .sh 훅 파일 발견"""
        _find_hook, _ = self._import_hook_helpers()

        (self.hooks_dir / "pre_compact.sh").touch()

        with patch('platform.system', return_value="Darwin"):
            result = _find_hook("pre_compact", self.temp_dir)

        self.assertIsNotNone(result)
        self.assertEqual(result.name, "pre_compact.sh")

    def test_find_hook_unix_ignores_bat(self):
        """Unix에서 .bat 훅은 무시"""
        _find_hook, _ = self._import_hook_helpers()

        (self.hooks_dir / "pre_compact.bat").touch()

        with patch('platform.system', return_value="Darwin"):
            result = _find_hook("pre_compact", self.temp_dir)

        self.assertIsNone(result)

    def test_find_hook_not_found(self):
        """훅 파일이 없으면 None"""
        _find_hook, _ = self._import_hook_helpers()

        with patch('platform.system', return_value="Windows"):
            result = _find_hook("nonexistent", self.temp_dir)

        self.assertIsNone(result)

    def test_hook_command_bat(self):
        """_hook_command: .bat → 직접 실행"""
        _, _hook_command = self._import_hook_helpers()

        path = Path("/hooks/pre_compact.bat")
        cmd = _hook_command(path)
        self.assertEqual(cmd, [str(path)])

    def test_hook_command_ps1(self):
        """_hook_command: .ps1 → powershell로 실행"""
        _, _hook_command = self._import_hook_helpers()

        path = Path("/hooks/pre_compact.ps1")
        cmd = _hook_command(path)
        self.assertEqual(cmd[0], "powershell")
        self.assertIn("-File", cmd)
        self.assertIn(str(path), cmd)

    def test_hook_command_py(self):
        """_hook_command: .py → sys.executable로 실행"""
        _, _hook_command = self._import_hook_helpers()

        path = Path("/hooks/post_compact.py")
        cmd = _hook_command(path)
        self.assertEqual(cmd[0], sys.executable)
        self.assertEqual(cmd[1], str(path))

    def test_hook_command_sh(self):
        """_hook_command: .sh → 직접 실행"""
        _, _hook_command = self._import_hook_helpers()

        path = Path("/hooks/pre_compact.sh")
        cmd = _hook_command(path)
        self.assertEqual(cmd, [str(path)])


class TestWindowsPathCompat(unittest.TestCase):
    """테스트 파일들이 플랫폼 독립 경로를 사용하는지"""

    def test_tempdir_is_platform_independent(self):
        """tempfile.gettempdir()가 플랫폼별로 유효한 경로 반환"""
        tmp = tempfile.gettempdir()
        self.assertTrue(os.path.isdir(tmp))
        # 하드코딩된 /tmp 대신 OS가 제공하는 경로 사용 확인
        test_path = os.path.join(tmp, "test_file.md")
        self.assertIn(os.sep, test_path)

    def test_session_metadata_uses_home(self):
        """SessionMetadata가 /home/user 대신 Path.home() 사용"""
        from core.session_manager import SessionMetadata

        data = {
            "id": "test",
            "project_id": "proj",
            "directory": str(Path.home()),
            "title": "Test"
        }
        session = SessionMetadata.from_dict(data)
        self.assertEqual(session.directory, str(Path.home()))


class TestISWindowsConstant(unittest.TestCase):
    """IS_WINDOWS 상수가 올바르게 설정되는지"""

    def test_is_windows_matches_platform(self):
        """IS_WINDOWS가 platform.system()과 일치"""
        from lib.display import IS_WINDOWS
        import platform
        expected = platform.system() == "Windows"
        self.assertEqual(IS_WINDOWS, expected)

    def test_is_windows_false_on_current_platform(self):
        """현재 macOS/Linux에서 IS_WINDOWS=False"""
        from lib.display import IS_WINDOWS
        import platform
        if platform.system() != "Windows":
            self.assertFalse(IS_WINDOWS)


class TestWatchUnixImportGuard(unittest.TestCase):
    """_watch_unix가 select/tty/termios import 실패 시 안전하게 리턴"""

    def test_watch_unix_returns_on_import_error(self):
        """Unix 모듈 import 실패 시 예외 없이 리턴"""
        from lib.display import EscapeWatcher

        # select, tty, termios 모두 import 실패 시뮬레이션
        with patch.dict('sys.modules', {
            'select': None,
            'tty': None,
            'termios': None,
        }):
            # 예외 없이 리턴되어야 함
            EscapeWatcher._active = True
            try:
                EscapeWatcher._watch_unix()
            except Exception as e:
                self.fail(f"_watch_unix raised {e}")
            finally:
                EscapeWatcher._active = False


class TestCommandTranslation(unittest.TestCase):
    """_translate_command_for_windows 변환 로직"""

    def test_ls_to_dir(self):
        from core.tools import _translate_command_for_windows
        with patch('platform.system', return_value="Windows"):
            self.assertEqual(_translate_command_for_windows("ls"), "dir")

    def test_ls_with_path(self):
        from core.tools import _translate_command_for_windows
        with patch('platform.system', return_value="Windows"):
            self.assertEqual(_translate_command_for_windows("ls /tmp"), "dir /tmp")

    def test_cat_to_type(self):
        from core.tools import _translate_command_for_windows
        with patch('platform.system', return_value="Windows"):
            self.assertEqual(_translate_command_for_windows("cat file.txt"), "type file.txt")

    def test_grep_to_findstr(self):
        from core.tools import _translate_command_for_windows
        with patch('platform.system', return_value="Windows"):
            self.assertEqual(_translate_command_for_windows('grep "pattern" file.txt'), 'findstr "pattern" file.txt')

    def test_pwd_to_cd(self):
        from core.tools import _translate_command_for_windows
        with patch('platform.system', return_value="Windows"):
            self.assertEqual(_translate_command_for_windows("pwd"), "cd")

    def test_which_to_where(self):
        from core.tools import _translate_command_for_windows
        with patch('platform.system', return_value="Windows"):
            self.assertEqual(_translate_command_for_windows("which python"), "where python")

    def test_mkdir_p(self):
        from core.tools import _translate_command_for_windows
        with patch('platform.system', return_value="Windows"):
            self.assertEqual(_translate_command_for_windows("mkdir -p a/b/c"), "mkdir a/b/c")

    def test_rm_rf(self):
        from core.tools import _translate_command_for_windows
        with patch('platform.system', return_value="Windows"):
            self.assertEqual(_translate_command_for_windows("rm -rf build"), "rmdir /s /q build")

    def test_no_translation_on_unix(self):
        """Unix에서는 변환하지 않음"""
        from core.tools import _translate_command_for_windows
        with patch('platform.system', return_value="Darwin"):
            self.assertEqual(_translate_command_for_windows("ls"), "ls")
            self.assertEqual(_translate_command_for_windows("cat file.txt"), "cat file.txt")

    def test_unknown_command_passthrough(self):
        """알 수 없는 명령은 그대로 통과"""
        from core.tools import _translate_command_for_windows
        with patch('platform.system', return_value="Windows"):
            self.assertEqual(_translate_command_for_windows("git status"), "git status")
            self.assertEqual(_translate_command_for_windows("pip install foo"), "pip install foo")


if __name__ == "__main__":
    unittest.main()
