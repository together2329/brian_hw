"""
Critical issue tests for memory system in real context.
These tests look for actual problems and edge cases.
"""

import unittest
import tempfile
import os
import json
import sys
import time
from pathlib import Path

_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(_script_dir))

sys.path.insert(0, _script_dir)
sys.path.insert(0, _project_root)

from lib.memory import MemorySystem
from lib.procedural_memory import ProceduralMemory, Action, Trajectory


class TestMemoryPromptInjectionIssues(unittest.TestCase):
    """실제로 preferences가 prompt에 주입되는지 검증"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.memory_system = MemorySystem(memory_dir=self.temp_dir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_preference_actually_affects_prompt_context(self):
        """Preference가 저장되었지만 실제로 LLM이 볼 프롬프트에 있는가?"""
        # 선호도 저장
        self.memory_system.update_preference("coding_style", "functional_programming")
        self.memory_system.update_preference("language_preference", "Rust")

        # 프롬프트 포맷팅
        formatted = self.memory_system.format_all_for_prompt()

        # ISSUE 1: 빈 문자열이면 LLM이 볼 것이 없음
        if not formatted:
            self.fail("❌ ISSUE: format_all_for_prompt() returns empty string even with preferences saved")

        # ISSUE 2: 내용이 너무 짧으면 무시될 수 있음
        self.assertGreater(len(formatted), 20,
                          "❌ ISSUE: Formatted preferences too short, may be ignored by LLM")

        # ISSUE 3: 실제 값이 포함되지 않으면 무의미
        self.assertIn("functional_programming", formatted,
                     "❌ ISSUE: Actual preference value not in formatted output")
        self.assertIn("Rust", formatted,
                     "❌ ISSUE: Language preference not appearing in prompt")

    def test_multiple_preferences_properly_formatted(self):
        """여러 선호도가 올바르게 포맷되는가?"""
        prefs = {
            "coding_style": "snake_case",
            "response_length": "concise",
            "error_verbosity": "detailed",
            "comment_style": "docstring"
        }

        for key, value in prefs.items():
            self.memory_system.update_preference(key, value)

        formatted = self.memory_system.format_all_for_prompt()

        # ISSUE: 모든 선호도가 포함되지 않을 수 있음
        missing = []
        for value in prefs.values():
            if value not in formatted:
                missing.append(value)

        if missing:
            self.fail(f"❌ ISSUE: These preferences missing from formatted output: {missing}")

    def test_project_context_not_being_used(self):
        """Project context가 저장되지만 format_all_for_prompt()에 포함되는가?"""
        self.memory_system.update_project_context("main_file", "src/main.py")
        self.memory_system.update_project_context("project_type", "PCIe SystemVerilog")

        formatted = self.memory_system.format_all_for_prompt()

        # ISSUE: 프로젝트 컨텍스트가 포맷되지 않을 수 있음
        if "Project Context" not in formatted:
            self.fail("❌ ISSUE: Project Context section not in formatted output, context may be ignored")

    def test_empty_vs_none_preferences(self):
        """빈 문자열과 None의 차이가 있는가?"""
        self.memory_system.update_preference("empty_pref", "")
        self.memory_system.update_preference("normal_pref", "value")

        formatted = self.memory_system.format_all_for_prompt()

        # ISSUE: 빈 문자열도 프롬프트에 포함될 수 있음
        lines = formatted.split('\n')
        for line in lines:
            if "empty_pref" in line and ":" in line:
                # 빈 값이 "- Empty Pref: " 형태로 남음
                self.assertWarns(None, lambda: None,
                    msg="⚠️  WARNING: Empty preference values appearing in prompt")


class TestProceduralMemoryRetrievalQuality(unittest.TestCase):
    """Procedural memory가 실제로 관련성 있는 결과를 반환하는가?"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.procedural_memory = ProceduralMemory(memory_dir=self.temp_dir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_similarity_score_too_permissive(self):
        """유사도 점수가 너무 높아서 관련 없는 작업도 반환하는가?"""
        # 한 가지 작업만 저장
        actions = [Action(tool="read_file", args="test.py", result="success")]
        self.procedural_memory.build(
            task_description="Fix Python syntax errors",
            actions=actions,
            outcome="success",
            iterations=1
        )
        self.procedural_memory.save()

        # 완전히 다른 작업으로 검색
        results = self.procedural_memory.retrieve(
            "Design Verilog FIFO buffer for PCIe protocol",
            limit=1
        )

        # ISSUE: 관련 없는 작업도 높은 점수로 반환될 수 있음
        if results:
            score, traj = results[0]
            if score > 0.8:
                self.fail(f"❌ ISSUE: Unrelated trajectory returned with high score {score:.2f}. "
                         f"Retrieved: '{traj.task_description[:50]}...'")

    def test_similarity_too_strict_missing_relevant(self):
        """유사도가 너무 엄격해서 관련 작업을 놓치는가?"""
        # 관련된 작업 저장
        actions = [
            Action(tool="read_file", args="config.py", result="success"),
            Action(tool="write_file", args="config.py", result="success")
        ]
        self.procedural_memory.build(
            task_description="Update Python configuration file with new settings",
            actions=actions,
            outcome="success",
            iterations=2
        )
        self.procedural_memory.save()

        # 매우 유사한 작업으로 검색
        results = self.procedural_memory.retrieve(
            "Modify Python config file to add new parameters",
            limit=3
        )

        # ISSUE: 명확히 관련된 작업을 못 찾을 수 있음
        if not results:
            self.fail("❌ ISSUE: No results returned for clearly similar task")

        score, traj = results[0]
        if score < 0.3:
            self.fail(f"❌ ISSUE: Similar task returned with too low score {score:.2f}. "
                     f"Threshold may be too strict.")

    def test_retrieve_with_empty_database(self):
        """빈 데이터베이스에서 검색할 때 에러가 나는가?"""
        # 아무것도 저장 안 함
        try:
            results = self.procedural_memory.retrieve("any task", limit=5)

            # ISSUE: None이 반환될 수 있음
            if results is None:
                self.fail("❌ ISSUE: retrieve() returns None instead of empty list")

            # 정상: 빈 리스트
            self.assertIsInstance(results, list)
            self.assertEqual(len(results), 0)
        except Exception as e:
            self.fail(f"❌ ISSUE: Exception when retrieving from empty database: {e}")

    def test_no_outcome_data_in_retrieval(self):
        """검색 결과에 task outcome (success/failure)가 표시되지 않을 수 있음"""
        actions = [
            Action(tool="write_file", args="broken.py", result="error")
        ]
        self.procedural_memory.build(
            task_description="Write Python file but it failed",
            actions=actions,
            outcome="failure",
            iterations=5
        )
        self.procedural_memory.save()

        results = self.procedural_memory.retrieve("write python file", limit=1)

        if results:
            score, traj = results[0]

            # ISSUE: 실패한 작업이 성공과 구분되지 않을 수 있음
            # main.py line 466: "if traj.outcome == 'success':"만 특별 처리
            # 실패는 어떻게 표시되는가?

            if traj.outcome == "failure":
                # 제대로 표시되지 않으면 LLM이 실패한 방법을 반복할 수 있음
                self.assertGreater(len(traj.errors_encountered), 0,
                                  "⚠️  ISSUE: Failed trajectory has no errors_encountered, "
                                  "LLM won't know what went wrong")


class TestMemoryFileSystemIssues(unittest.TestCase):
    """메모리 저장소의 파일 시스템 문제"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_concurrent_write_issue(self):
        """두 메모리 인스턴스가 동시에 쓸 때 데이터 손실이 있는가?"""
        memory1 = MemorySystem(memory_dir=self.temp_dir)
        memory2 = MemorySystem(memory_dir=self.temp_dir)

        # 인스턴스 1에 데이터 쓰기
        memory1.update_preference("key1", "value1")

        # 인스턴스 2에 데이터 쓰기 (동시성 문제)
        memory2.update_preference("key2", "value2")

        # 둘 다 저장되었는가?
        memory3 = MemorySystem(memory_dir=self.temp_dir)

        # ISSUE: 후자의 쓰기가 전자를 덮어쓸 수 있음
        prefs = memory3.list_preferences()

        if "key1" not in prefs:
            self.fail("❌ ISSUE: Concurrent writes cause data loss. key1 missing.")
        if "key2" not in prefs:
            self.fail("❌ ISSUE: Concurrent writes cause data loss. key2 missing.")

    def test_large_preference_value(self):
        """매우 큰 선호도 값을 저장할 수 있는가?"""
        large_value = "x" * 100000  # 100KB
        self.memory_system = MemorySystem(memory_dir=self.temp_dir)

        try:
            self.memory_system.update_preference("large_text", large_value)

            # 로드할 수 있는가?
            retrieved = self.memory_system.get_preference("large_text")

            if retrieved != large_value:
                self.fail("❌ ISSUE: Large value corrupted or truncated on save/load")
        except Exception as e:
            self.fail(f"❌ ISSUE: Cannot handle large preference values: {e}")

    def test_special_characters_in_preferences(self):
        """특수 문자가 보존되는가?"""
        self.memory_system = MemorySystem(memory_dir=self.temp_dir)

        special_values = {
            "quotes": 'He said "hello"',
            "newlines": "line1\nline2\nline3",
            "unicode": "한글, 日本語, العربية, emoji: 🎉",
            "json": '{"key": "value"}',
            "regex": r"pattern.*\d+[a-z]"
        }

        for key, value in special_values.items():
            self.memory_system.update_preference(key, value)

        # 다시 로드
        memory2 = MemorySystem(memory_dir=self.temp_dir)

        for key, expected in special_values.items():
            retrieved = memory2.get_preference(key)

            if retrieved != expected:
                self.fail(f"❌ ISSUE: Special characters corrupted in '{key}': "
                         f"expected {repr(expected)}, got {repr(retrieved)}")


class TestMemoryPerformanceIssues(unittest.TestCase):
    """메모리 시스템의 성능 문제"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.memory_system = MemorySystem(memory_dir=self.temp_dir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_slow_preference_updates(self):
        """많은 선호도 업데이트가 느려지는가?"""
        start = time.time()

        # 100개의 선호도 추가
        for i in range(100):
            self.memory_system.update_preference(f"pref_{i}", f"value_{i}")

        elapsed = time.time() - start

        # ISSUE: 각 update_preference()마다 파일 I/O (라인 89)
        # 100번 x 파일 쓰기 = 느림
        if elapsed > 5.0:
            self.fail(f"❌ ISSUE: 100 preferences took {elapsed:.2f}s. "
                     f"Each update() does file I/O (line 89). "
                     f"Need batch update method.")

    def test_procedural_memory_search_slowdown(self):
        """트라젝토리가 많아지면 검색이 느려지는가?"""
        procedural_memory = ProceduralMemory(memory_dir=self.temp_dir)

        # 50개 트라젝토리 추가
        for i in range(50):
            actions = [Action(tool=f"tool_{i}", args=f"args_{i}", result="success")]
            procedural_memory.build(
                task_description=f"Task {i}: Do something with file{i}.py",
                actions=actions,
                outcome="success",
                iterations=1
            )
        procedural_memory.save()

        # 검색 시간 측정
        start = time.time()
        results = procedural_memory.retrieve("file25.py", limit=5)
        elapsed = time.time() - start

        # ISSUE: 임베딩이나 BM25 없이 선형 비교로 O(n)
        if elapsed > 1.0:
            self.fail(f"❌ ISSUE: Search took {elapsed:.3f}s for 50 trajectories. "
                     f"May scale poorly with more data.")


class TestAutoExtractIssues(unittest.TestCase):
    """auto_extract_and_update의 실제 문제"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.memory_system = MemorySystem(memory_dir=self.temp_dir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_auto_extract_requires_llm(self):
        """LLM 없이 auto_extract가 작동하는가?"""
        result = self.memory_system.auto_extract_and_update(
            "I prefer Python and snake_case naming",
            llm_call_func=None  # No LLM function
        )

        # ISSUE: LLM이 없으면 작동하지 않음
        if "error" in result:
            self.fail("❌ ISSUE: auto_extract requires LLM but not always provided. "
                     "main.py line 1398 calls this but doesn't check if LLM is available.")

    def test_auto_extract_false_positives(self):
        """의도하지 않은 정보도 선호도로 추출하는가?"""
        result = self.memory_system.auto_extract_and_update(
            "Yesterday I worked on a Python file. It had bugs.",
            llm_call_func=None
        )

        actions = result.get("actions", [])

        # ISSUE: 과도하게 추출할 수 있음
        # "Python" -> coding_language = Python
        # "bugs" -> problem_area = bugs  (너무 일반적)
        # 이런 것들이 실제 선호도가 되면 안 됨

        if len(actions) > 5:
            self.fail(f"❌ ISSUE: auto_extract returned {len(actions)} actions "
                     f"from single sentence. Over-extraction may pollute preferences.")


if __name__ == '__main__':
    unittest.main(verbosity=2)
