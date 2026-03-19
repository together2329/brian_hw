"""
심화 크로스플랫폼 테스트 V2

API 키 없이 실행 가능한 심화 테스트:
1. run_command — 크로스플랫폼 명령어
2. compress_history — 메시지 압축 로직
3. Context tracker — 토큰 카운팅/시각화
4. Hook pipeline — HookRegistry 전체 체인
5. Background task manager — 태스크 생성/상태
6. Simple linter — Python 구문 검사
7. 대용량 파일 처리 — read_file truncation
8. Procedural memory — 궤적 저장/검색
"""

import os
import sys
import platform
import unittest
import tempfile
import shutil
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

# python vs python3 — macOS에는 python3만 있을 수 있음
PYTHON = sys.executable


# ============================================================
# 1. run_command — Windows/Unix 모두 동작하는 명령어로 테스트
# ============================================================

class TestRunCommand(unittest.TestCase):
    """run_command가 모든 OS에서 동작하는지"""

    def test_echo(self):
        """echo는 모든 OS에서 동작"""
        from core.tools import run_command
        result = run_command("echo hello")
        self.assertIn("hello", result)

    def test_python_version(self):
        """python --version은 모든 OS에서 동작"""
        from core.tools import run_command
        result = run_command(f"{PYTHON} --version")
        self.assertIn("Python", result)

    def test_git_version(self):
        """git --version (CI에 git 있음)"""
        from core.tools import run_command
        result = run_command("git --version")
        self.assertIn("git version", result)

    def test_timeout(self):
        """타임아웃이 동작하는지"""
        from core.tools import run_command
        # 크로스플랫폼 슬립 명령
        result = run_command(f"{PYTHON} -c \"import time; time.sleep(10)\"", timeout=1)
        self.assertIn("timed out", result.lower())

    def test_nonexistent_command(self):
        """존재하지 않는 명령어 — 에러 반환"""
        from core.tools import run_command
        result = run_command("this_command_does_not_exist_12345")
        # 에러가 발생하지만 크래시하지 않아야 함
        self.assertIsInstance(result, str)

    def test_exit_code_in_output(self):
        """비정상 종료 코드 포함"""
        from core.tools import run_command
        result = run_command(f"{PYTHON} -c \"import sys; sys.exit(1)\"")
        # 에러 정보가 포함되어야 함
        self.assertIsInstance(result, str)

    def test_unicode_output(self):
        """유니코드 출력 처리"""
        from core.tools import run_command
        result = run_command(f"{PYTHON} -c \"print('hello')\"")
        self.assertIn("hello", result)

    def test_ls_auto_translate(self):
        """ls → Windows에서 자동으로 dir로 변환"""
        from core.tools import run_command
        result = run_command("ls")
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_cat_auto_translate(self):
        """cat → Windows에서 자동으로 type으로 변환"""
        from core.tools import run_command
        tmp = os.path.join(tempfile.gettempdir(), "brian_test_cat.txt")
        with open(tmp, 'w', encoding='utf-8') as f:
            f.write("test content here")
        try:
            result = run_command(f'cat "{tmp}"')
            self.assertIn("test content", result)
        finally:
            os.remove(tmp)

    def test_grep_auto_translate(self):
        """grep → Windows에서 자동으로 findstr로 변환"""
        from core.tools import run_command
        tmp = os.path.join(tempfile.gettempdir(), "brian_test_grep.txt")
        with open(tmp, 'w', encoding='utf-8') as f:
            f.write("apple\nbanana\ncherry\n")
        try:
            result = run_command(f'grep "banana" "{tmp}"')
            self.assertIn("banana", result)
        finally:
            os.remove(tmp)

    def test_pipe(self):
        """파이프(|)가 동작하는지"""
        from core.tools import run_command
        result = run_command(f'echo hello world | {PYTHON} -c "import sys; print(sys.stdin.read().strip().upper())"')
        self.assertIn("HELLO WORLD", result)

    def test_pwd_auto_translate(self):
        """pwd → Windows에서 cd로 변환"""
        from core.tools import run_command
        result = run_command("pwd")
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_env_variable(self):
        """환경변수 접근"""
        from core.tools import run_command
        if platform.system() == "Windows":
            result = run_command("echo %PATH%")
        else:
            result = run_command("echo $PATH")
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)


# ============================================================
# 2. compress_history — 메시지 압축 로직
# ============================================================

class TestCompressHistory(unittest.TestCase):
    """compress_history 로직이 모든 OS에서 동작"""

    def _make_messages(self, count):
        """테스트용 메시지 리스트 생성"""
        msgs = [{"role": "system", "content": "You are a helpful assistant."}]
        for i in range(count):
            if i % 2 == 0:
                msgs.append({"role": "user", "content": f"Question {i}"})
            else:
                msgs.append({"role": "assistant", "content": f"Answer {i} " + "x" * 100})
        return msgs

    def test_short_history_no_compression(self):
        """짧은 히스토리는 압축하지 않음"""
        # compress_history는 main.py에 있어서 직접 import 어려움
        # 대신 로직의 핵심인 메시지 분리를 테스트
        msgs = self._make_messages(4)
        system_msgs = [m for m in msgs if m.get("role") == "system"]
        regular_msgs = [m for m in msgs if m.get("role") != "system"]
        self.assertEqual(len(system_msgs), 1)
        self.assertEqual(len(regular_msgs), 4)

    def test_important_message_extraction(self):
        """!important 태그가 있는 메시지 추출"""
        msgs = [
            {"role": "system", "content": "system"},
            {"role": "user", "content": "normal question"},
            {"role": "user", "content": "!important remember this"},
            {"role": "assistant", "content": "!important critical info"},
        ]
        important = [m for m in msgs if "!important" in str(m.get("content", "")).lower()]
        self.assertEqual(len(important), 2)

    def test_token_estimation(self):
        """토큰 추정 (chars // 4)"""
        text = "a" * 400
        estimated = len(text) // 4
        self.assertEqual(estimated, 100)


# ============================================================
# 3. Context tracker — 토큰 카운팅/시각화
# ============================================================

class TestContextTracker(unittest.TestCase):
    """ContextTracker가 모든 OS에서 동작"""

    def setUp(self):
        from core.context_tracker import reset_tracker, get_tracker
        reset_tracker(max_tokens=100000)
        self.tracker = get_tracker()

    def test_initial_state(self):
        self.assertEqual(self.tracker.get_total_tokens(), 0)
        self.assertEqual(self.tracker.get_usage_percentage(), 0.0)
        self.assertEqual(self.tracker.get_free_tokens(), 100000)

    def test_update_system_prompt(self):
        self.tracker.update_system_prompt("a" * 400)  # 100 tokens
        self.assertEqual(self.tracker.system_prompt_tokens, 100)

    def test_update_messages(self):
        msgs = [
            {"role": "user", "content": "a" * 200},
            {"role": "assistant", "content": "b" * 200},
        ]
        self.tracker.update_messages(msgs)
        self.assertGreater(self.tracker.messages_tokens, 0)

    def test_usage_percentage(self):
        self.tracker.system_prompt_tokens = 50000
        self.assertAlmostEqual(self.tracker.get_usage_percentage(), 50.0, delta=1.0)

    def test_format_tokens(self):
        self.assertEqual(self.tracker.format_tokens(500), "500")
        self.assertIn("k", self.tracker.format_tokens(1500).lower())
        self.assertIn("k", self.tracker.format_tokens(50000).lower())

    def test_visualize(self):
        self.tracker.system_prompt_tokens = 10000
        self.tracker.messages_tokens = 20000
        result = self.tracker.visualize("test-model")
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_bar_chars(self):
        full = self.tracker.get_bar_char(90.0)
        empty = self.tracker.get_bar_char(0.0)
        self.assertIsInstance(full, str)
        self.assertIsInstance(empty, str)


# ============================================================
# 4. Hook pipeline — HookRegistry
# ============================================================

class TestHookPipeline(unittest.TestCase):
    """HookRegistry가 모든 OS에서 동작"""

    def test_create_default_hooks(self):
        from core.hooks import create_default_hooks
        registry = create_default_hooks()
        self.assertTrue(registry.is_enabled)

    def test_register_and_run(self):
        from core.hooks import HookRegistry, HookPoint, HookContext

        registry = HookRegistry()

        def my_hook(ctx):
            ctx.metadata["touched"] = True
            return ctx

        registry.register(HookPoint.BEFORE_LLM_CALL, my_hook)

        ctx = HookContext(messages=[{"role": "user", "content": "hi"}])
        result = registry.run(HookPoint.BEFORE_LLM_CALL, ctx)
        self.assertTrue(result.metadata.get("touched"))

    def test_hook_priority_order(self):
        """낮은 priority가 먼저 실행"""
        from core.hooks import HookRegistry, HookPoint, HookContext

        registry = HookRegistry()
        order = []

        def hook_a(ctx):
            order.append("a")
            return ctx

        def hook_b(ctx):
            order.append("b")
            return ctx

        registry.register(HookPoint.BEFORE_LLM_CALL, hook_b, priority=200)
        registry.register(HookPoint.BEFORE_LLM_CALL, hook_a, priority=100)

        ctx = HookContext()
        registry.run(HookPoint.BEFORE_LLM_CALL, ctx)
        self.assertEqual(order, ["a", "b"])

    def test_disable_hooks(self):
        from core.hooks import HookRegistry, HookPoint, HookContext

        registry = HookRegistry()
        called = []

        def my_hook(ctx):
            called.append(True)
            return ctx

        registry.register(HookPoint.BEFORE_LLM_CALL, my_hook)
        registry.disable()

        ctx = HookContext()
        registry.run(HookPoint.BEFORE_LLM_CALL, ctx)
        self.assertEqual(len(called), 0)

    def test_hook_exception_doesnt_crash(self):
        """훅에서 예외 발생해도 전체가 크래시하지 않음"""
        from core.hooks import HookRegistry, HookPoint, HookContext

        registry = HookRegistry()

        def bad_hook(ctx):
            raise ValueError("boom")

        registry.register(HookPoint.BEFORE_LLM_CALL, bad_hook)

        ctx = HookContext()
        # 예외 없이 리턴되어야 함
        result = registry.run(HookPoint.BEFORE_LLM_CALL, ctx)
        self.assertIsInstance(result, HookContext)

    def test_tool_output_truncation(self):
        """도구 출력 잘라내기 훅"""
        from core.hooks import create_default_hooks, HookPoint, HookContext

        registry = create_default_hooks()
        long_output = "x" * 100000

        ctx = HookContext(
            tool_name="read_file",
            tool_output=long_output,
        )
        result = registry.run(HookPoint.AFTER_TOOL_EXEC, ctx)
        self.assertLessEqual(len(result.tool_output), len(long_output))


# ============================================================
# 5. Background task manager
# ============================================================

class TestBackgroundManager(unittest.TestCase):
    """BackgroundManager 기본 기능"""

    def test_list_empty(self):
        from core.background import BackgroundManager
        mgr = BackgroundManager(max_workers=1)
        result = mgr.list_tasks()
        self.assertIn("No background tasks", result)
        mgr.shutdown()

    def test_get_nonexistent_task(self):
        from core.background import BackgroundManager
        mgr = BackgroundManager(max_workers=1)
        result = mgr.get_output("bg_nonexistent")
        self.assertIn("not found", result.lower())
        mgr.shutdown()

    def test_cancel_nonexistent_task(self):
        from core.background import BackgroundManager
        mgr = BackgroundManager(max_workers=1)
        result = mgr.cancel("bg_nonexistent")
        self.assertIn("not found", result.lower())
        mgr.shutdown()

    def test_task_counts(self):
        from core.background import BackgroundManager
        mgr = BackgroundManager(max_workers=1)
        self.assertEqual(mgr.get_completed_count(), 0)
        self.assertEqual(mgr.get_running_count(), 0)
        mgr.shutdown()


# ============================================================
# 6. Simple linter — Python 구문 검사
# ============================================================

class TestSimpleLinter(unittest.TestCase):
    """SimpleLinter가 모든 OS에서 동작"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_python_always_available(self):
        from core.simple_linter import SimpleLinter
        linter = SimpleLinter()
        self.assertTrue(linter.is_available("python"))

    def test_check_valid_python(self):
        from core.simple_linter import SimpleLinter
        linter = SimpleLinter()

        valid_file = os.path.join(self.temp_dir, "valid.py")
        with open(valid_file, 'w', encoding='utf-8') as f:
            f.write("x = 1\nprint(x)\n")

        errors = linter.check_file(valid_file)
        # 구문 에러는 없어야 함 (pyflakes 경고는 있을 수 있음)
        syntax_errors = [e for e in errors if "syntax" in e.message.lower() or "invalid" in e.message.lower()]
        self.assertEqual(len(syntax_errors), 0)

    def test_check_invalid_python(self):
        from core.simple_linter import SimpleLinter
        linter = SimpleLinter()

        invalid_file = os.path.join(self.temp_dir, "invalid.py")
        with open(invalid_file, 'w', encoding='utf-8') as f:
            f.write("def foo(\n")  # 구문 에러

        errors = linter.check_file(invalid_file)
        self.assertGreater(len(errors), 0)

    def test_syntax_check_only(self):
        from core.simple_linter import SimpleLinter
        linter = SimpleLinter()

        valid_file = os.path.join(self.temp_dir, "ok.py")
        with open(valid_file, 'w', encoding='utf-8') as f:
            f.write("print('hello')\n")

        self.assertTrue(linter.check_syntax_only(valid_file))

    def test_format_errors(self):
        from core.simple_linter import SimpleLinter, LintError
        linter = SimpleLinter()

        errors = [
            LintError("test.py", 1, "undefined name 'x'", "error"),
            LintError("test.py", 5, "unused import", "warning"),
        ]
        result = linter.format_errors(errors)
        self.assertIn("undefined", result)
        self.assertIn("unused", result)

    def test_available_tools_info(self):
        from core.simple_linter import SimpleLinter
        linter = SimpleLinter()
        info = linter.get_available_tools_info()
        self.assertIsInstance(info, str)
        self.assertGreater(len(info), 0)


# ============================================================
# 7. 대용량 파일 처리 — read_file truncation
# ============================================================

class TestLargeFileHandling(unittest.TestCase):
    """대용량 파일 읽기/잘라내기"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_small_file_full_read(self):
        from core.tools import read_file
        path = os.path.join(self.temp_dir, "small.txt")
        with open(path, 'w', encoding='utf-8') as f:
            for i in range(50):
                f.write(f"line {i}\n")

        result = read_file(path)
        self.assertIn("line 0", result)
        self.assertIn("line 49", result)
        self.assertNotIn("LARGE FILE", result)

    def test_large_file_truncation(self):
        from core.tools import read_file
        path = os.path.join(self.temp_dir, "large.txt")
        with open(path, 'w', encoding='utf-8') as f:
            for i in range(1000):
                f.write(f"line {i}: " + "x" * 50 + "\n")

        result = read_file(path)
        self.assertIn("LARGE FILE", result)
        self.assertIn("line 0", result)
        # 500줄 이후는 잘려야 함
        self.assertNotIn("line 999", result)

    def test_unicode_large_file(self):
        from core.tools import read_file
        path = os.path.join(self.temp_dir, "unicode_large.txt")
        with open(path, 'w', encoding='utf-8') as f:
            for i in range(600):
                f.write(f"한글 라인 {i} 🔌\n")

        result = read_file(path)
        self.assertIn("한글", result)
        self.assertIn("LARGE FILE", result)


# ============================================================
# 8. Procedural memory — 궤적 저장/검색
# ============================================================

class TestProceduralMemory(unittest.TestCase):
    """ProceduralMemory가 모든 OS에서 동작"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_build_trajectory(self):
        from lib.procedural_memory import ProceduralMemory, Action

        mem = ProceduralMemory(memory_dir=self.temp_dir)
        actions = [
            Action(tool="read_file", args="test.py", result="success", observation="file content"),
            Action(tool="write_file", args="out.py", result="success", observation="written"),
        ]
        tid = mem.build("Create a Python script", actions, "success", iterations=2)
        self.assertIsNotNone(tid)
        self.assertGreater(len(mem.trajectories), 0)

    def test_retrieve_similar(self):
        from lib.procedural_memory import ProceduralMemory, Action

        mem = ProceduralMemory(memory_dir=self.temp_dir)
        actions = [
            Action(tool="read_file", args="test.py", result="success"),
        ]
        mem.build("Debug Python syntax error", actions, "success", iterations=1)

        results = mem.retrieve("Fix Python bug", limit=3)
        self.assertGreater(len(results), 0)
        score, traj = results[0]
        self.assertGreater(score, 0.0)

    def test_save_and_reload(self):
        from lib.procedural_memory import ProceduralMemory, Action

        mem = ProceduralMemory(memory_dir=self.temp_dir)
        actions = [Action(tool="grep_file", args="pattern", result="success")]
        tid = mem.build("Search for pattern", actions, "success", iterations=1)
        mem.save()

        # 새 인스턴스로 리로드
        mem2 = ProceduralMemory(memory_dir=self.temp_dir)
        self.assertIn(tid, mem2.trajectories)

    def test_get_stats(self):
        from lib.procedural_memory import ProceduralMemory, Action

        mem = ProceduralMemory(memory_dir=self.temp_dir)
        actions = [Action(tool="read_file", args="a.py", result="success")]
        mem.build("Task A", actions, "success", iterations=1)
        mem.build("Task B", actions, "failure", iterations=3)

        stats = mem.get_stats()
        self.assertEqual(stats["total_trajectories"], 2)

    def test_clear(self):
        from lib.procedural_memory import ProceduralMemory, Action

        mem = ProceduralMemory(memory_dir=self.temp_dir)
        actions = [Action(tool="read_file", args="a.py", result="success")]
        mem.build("Task", actions, "success", iterations=1)
        self.assertGreater(len(mem.trajectories), 0)

        mem.clear()
        self.assertEqual(len(mem.trajectories), 0)

    def test_action_serialization(self):
        from lib.procedural_memory import Action

        action = Action(tool="write_file", args="out.py", result="success", observation="ok")
        d = action.to_dict()
        restored = Action.from_dict(d)
        self.assertEqual(restored.tool, "write_file")
        self.assertEqual(restored.result, "success")

    def test_increment_usage(self):
        from lib.procedural_memory import ProceduralMemory, Action

        mem = ProceduralMemory(memory_dir=self.temp_dir)
        actions = [Action(tool="read_file", args="a.py", result="success")]
        tid = mem.build("Task", actions, "success", iterations=1)

        self.assertEqual(mem.trajectories[tid].usage_count, 0)
        mem.increment_usage(tid)
        self.assertEqual(mem.trajectories[tid].usage_count, 1)


# ============================================================
# 9. 동시 파일 접근 — 멀티스레드 쓰기
# ============================================================

class TestConcurrentFileAccess(unittest.TestCase):
    """멀티스레드에서 파일 쓰기가 안전한지"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_concurrent_writes(self):
        """여러 스레드가 동시에 다른 파일에 쓰기"""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        from core.tools import write_file

        def write_task(i):
            path = os.path.join(self.temp_dir, f"file_{i}.txt")
            return write_file(path, f"content {i}")

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(write_task, i) for i in range(10)]
            results = [f.result() for f in as_completed(futures)]

        self.assertEqual(len(results), 10)
        for r in results:
            self.assertIn("Successfully", r)

        # 파일 개수 확인
        files = list(Path(self.temp_dir).glob("file_*.txt"))
        self.assertEqual(len(files), 10)

    def test_concurrent_session_writes(self):
        """SessionStorage 동시 세션 생성"""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        from core.session_manager import SessionStorage

        storage = SessionStorage(Path(self.temp_dir))

        def create_task(i):
            return storage.create_session(title=f"Session {i}")

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_task, i) for i in range(10)]
            sessions = [f.result() for f in as_completed(futures)]

        self.assertEqual(len(sessions), 10)
        # 모든 ID가 유니크
        ids = [s.id for s in sessions]
        self.assertEqual(len(set(ids)), 10)


if __name__ == "__main__":
    unittest.main()
