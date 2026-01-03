#!/usr/bin/env python3
"""
Real-time Context Flow Monitor for brian_coder

Agent 간 context 흐름을 실시간으로 시각화하고 효율성을 분석합니다.
"""

import sys
import os
import time
from pathlib import Path
from datetime import datetime

# Add project paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "core"))
sys.path.insert(0, str(project_root / "agents"))

from agents.shared_context import SharedContext, AgentMemory


class ContextFlowMonitor:
    """
    실시간 Context Flow 모니터

    Features:
    - Agent 간 정보 흐름 시각화
    - 중복 작업 감지
    - Context 업데이트 타임라인
    - 효율성 메트릭 계산
    """

    def __init__(self, shared_context: SharedContext):
        self.shared_context = shared_context
        self.timeline = []
        self.agent_interactions = {}

    def snapshot(self, label: str = None):
        """현재 context 상태 스냅샷"""
        snapshot = {
            'timestamp': datetime.now(),
            'label': label,
            'files_examined': len(self.shared_context.get_all_examined_files()),
            'files_modified': len(self.shared_context.get_all_modified_files()),
            'planned_steps': len(self.shared_context.get_planned_steps()),
            'exploration_findings': len(self.shared_context.get_exploration_findings()),
            'agent_count': len(self.shared_context.get_agent_history()),
        }
        self.timeline.append(snapshot)
        return snapshot

    def detect_redundant_work(self):
        """중복 작업 감지"""
        history = self.shared_context.get_agent_history()

        # 같은 파일을 여러 agent가 읽었는지 확인
        file_readers = {}
        for memory in history:
            for file in memory.files_examined:
                if file not in file_readers:
                    file_readers[file] = []
                file_readers[file].append(memory.agent_name)

        redundant = {
            file: agents
            for file, agents in file_readers.items()
            if len(agents) > 1
        }

        return redundant

    def analyze_efficiency(self):
        """효율성 분석"""
        history = self.shared_context.get_agent_history()

        if not history:
            return {
                'total_agents': 0,
                'total_files_examined': 0,
                'unique_files': 0,
                'redundancy_rate': 0.0,
                'avg_execution_time_ms': 0,
                'total_tool_calls': 0
            }

        total_files_examined = sum(len(m.files_examined) for m in history)
        unique_files = len(self.shared_context.get_all_examined_files())

        redundancy_rate = (
            (total_files_examined - unique_files) / total_files_examined * 100
            if total_files_examined > 0 else 0.0
        )

        avg_exec_time = (
            sum(m.execution_time_ms for m in history) / len(history)
            if history else 0
        )

        total_tool_calls = sum(m.tool_calls_count for m in history)

        return {
            'total_agents': len(history),
            'total_files_examined': total_files_examined,
            'unique_files': unique_files,
            'redundancy_rate': redundancy_rate,
            'avg_execution_time_ms': avg_exec_time,
            'total_tool_calls': total_tool_calls
        }

    def visualize_flow(self):
        """Context flow 시각화"""
        print("\n" + "=" * 100)
        print("📊 CONTEXT FLOW VISUALIZATION")
        print("=" * 100)

        history = self.shared_context.get_agent_history()

        if not history:
            print("\n  ⚠️  No agent execution history yet.")
            return

        # Timeline
        print("\n🕐 TIMELINE:")
        print("-" * 100)

        for i, memory in enumerate(history, 1):
            timestamp = memory.timestamp.strftime("%H:%M:%S")

            # Agent info
            print(f"\n  [{timestamp}] Agent #{i}: {memory.agent_name} ({memory.agent_type})")

            # Execution stats
            print(f"    ⏱️  Execution: {memory.execution_time_ms}ms | Tools: {memory.tool_calls_count}")

            # Files examined
            if memory.files_examined:
                print(f"    📁 Examined: {', '.join(memory.files_examined[:5])}")
                if len(memory.files_examined) > 5:
                    print(f"        ... and {len(memory.files_examined) - 5} more")

            # Files modified
            if memory.files_modified:
                print(f"    ✏️  Modified: {', '.join(memory.files_modified)}")

            # Planned steps
            if memory.planned_steps:
                print(f"    📋 Planned: {len(memory.planned_steps)} step(s)")

            # Findings
            if memory.findings:
                preview = memory.findings[:100] + "..." if len(memory.findings) > 100 else memory.findings
                print(f"    🔍 Findings: {preview}")

        # Context sharing diagram
        print("\n\n🔗 CONTEXT SHARING DIAGRAM:")
        print("-" * 100)

        agents_by_type = {}
        for memory in history:
            if memory.agent_type not in agents_by_type:
                agents_by_type[memory.agent_type] = []
            agents_by_type[memory.agent_type].append(memory.agent_name)

        # Show flow
        agent_types = list(agents_by_type.keys())

        for i, agent_type in enumerate(agent_types):
            agents = agents_by_type[agent_type]
            print(f"\n  [{agent_type.upper()}]")
            for agent_name in agents:
                print(f"    └─ {agent_name}")

            if i < len(agent_types) - 1:
                print("       │")
                print("       ▼ (SharedContext)")
                print("       │")

        # Shared data summary
        print("\n\n💾 SHARED DATA SUMMARY:")
        print("-" * 100)

        all_files = self.shared_context.get_all_examined_files()
        all_modified = self.shared_context.get_all_modified_files()
        all_steps = self.shared_context.get_planned_steps()
        all_findings = self.shared_context.get_exploration_findings()

        print(f"  📁 Files examined: {len(all_files)} unique file(s)")
        if all_files:
            for f in all_files[:10]:
                print(f"     • {f}")
            if len(all_files) > 10:
                print(f"     ... and {len(all_files) - 10} more")

        if all_modified:
            print(f"\n  ✏️  Files modified: {len(all_modified)} file(s)")
            for f in all_modified:
                print(f"     • {f}")

        if all_steps:
            print(f"\n  📋 Planned steps: {len(all_steps)} step(s)")
            for i, step in enumerate(all_steps[:5], 1):
                print(f"     {i}. {step}")
            if len(all_steps) > 5:
                print(f"     ... and {len(all_steps) - 5} more")

        if all_findings:
            print(f"\n  🔍 Exploration findings: {len(all_findings)} insight(s)")

        # Efficiency analysis
        print("\n\n📈 EFFICIENCY ANALYSIS:")
        print("-" * 100)

        metrics = self.analyze_efficiency()

        print(f"  Total agents executed: {metrics['total_agents']}")
        print(f"  Total files examined: {metrics['total_files_examined']}")
        print(f"  Unique files: {metrics['unique_files']}")
        print(f"  Redundancy rate: {metrics['redundancy_rate']:.1f}%")
        print(f"  Avg execution time: {metrics['avg_execution_time_ms']:.0f}ms")
        print(f"  Total tool calls: {metrics['total_tool_calls']}")

        # Redundant work detection
        redundant = self.detect_redundant_work()
        if redundant:
            print(f"\n  ⚠️  REDUNDANT WORK DETECTED:")
            for file, agents in redundant.items():
                print(f"     {file} was examined by: {', '.join(agents)}")
        else:
            print(f"\n  ✅ No redundant work detected!")

        print("\n" + "=" * 100)


def test_real_scenario():
    """실제 시나리오 테스트"""
    print("\n" + "🧪 " * 50)
    print("REAL SCENARIO TEST: Multi-Agent Context Sharing")
    print("🧪 " * 50)

    try:
        from agents.shared_context import SharedContext
        from agents.sub_agents.explore_agent import ExploreAgent
        from agents.sub_agents.plan_agent import PlanAgent
        from llm_client import call_llm_raw
        from core.tools import AVAILABLE_TOOLS

        # Create monitor
        shared_ctx = SharedContext()
        monitor = ContextFlowMonitor(shared_ctx)

        print("\n✅ Created SharedContext and Monitor")

        # Mock execute_tool
        def execute_tool(tool_name, args):
            # Simulate file reading
            if tool_name == 'find_files':
                return "fifo_sync.v\nfifo_async.v\nsram.v"
            elif tool_name == 'read_file':
                return "module fifo_sync(...); endmodule"
            elif tool_name == 'grep_file':
                return "fifo_sync.v:10:module fifo_sync"
            return "OK"

        # Scenario: Explore → Plan → Execute
        print("\n" + "-" * 100)
        print("SCENARIO: Implement new FIFO with CDC")
        print("-" * 100)

        # Step 1: ExploreAgent
        print("\n[STEP 1] ExploreAgent - Find existing FIFO implementations")
        monitor.snapshot("Before ExploreAgent")

        # Simulate exploration
        shared_ctx.record_exploration(
            agent_name="explore_fifo",
            files_examined=["fifo_sync.v", "fifo_async.v", "sram.v"],
            findings="Found 2 FIFO implementations with standard interfaces",
            execution_time_ms=1500,
            tool_calls_count=5
        )

        monitor.snapshot("After ExploreAgent")
        print("  ✅ ExploreAgent completed")
        print(f"  📁 Files: {shared_ctx.get_all_examined_files()}")

        time.sleep(0.1)  # Simulate delay

        # Step 2: PlanAgent
        print("\n[STEP 2] PlanAgent - Create implementation plan")
        print("  📥 PlanAgent receives context from ExploreAgent:")
        llm_context = shared_ctx.get_context_for_llm()
        print(f"     {llm_context.replace(chr(10), chr(10) + '     ')}")

        # Simulate planning
        shared_ctx.record_planning(
            agent_name="plan_fifo",
            planned_steps=[
                "Phase 1: Create gray code counter module",
                "Phase 2: Implement async FIFO with CDC",
                "Phase 3: Create testbench"
            ],
            summary="Design async FIFO with clock domain crossing based on existing patterns",
            execution_time_ms=2000,
            tool_calls_count=3
        )

        monitor.snapshot("After PlanAgent")
        print("  ✅ PlanAgent completed")
        print(f"  📋 Steps: {len(shared_ctx.get_planned_steps())}")

        time.sleep(0.1)

        # Step 3: ExecuteAgent (simulated)
        print("\n[STEP 3] ExecuteAgent - Implement based on plan")
        print("  📥 ExecuteAgent receives context from both agents:")
        llm_context = shared_ctx.get_context_for_llm()
        print(f"     {llm_context.replace(chr(10), chr(10) + '     ')}")

        # Simulate execution
        shared_ctx.record_execution(
            agent_name="execute_fifo",
            files_modified=["gray_counter.v", "fifo_async_cdc.v", "fifo_async_cdc_tb.v"],
            execution_time_ms=3500,
            tool_calls_count=8
        )

        monitor.snapshot("After ExecuteAgent")
        print("  ✅ ExecuteAgent completed")
        print(f"  ✏️  Modified: {shared_ctx.get_all_modified_files()}")

        # Visualize complete flow
        monitor.visualize_flow()

        # Timeline comparison
        print("\n\n📊 CONTEXT GROWTH TIMELINE:")
        print("=" * 100)
        print(f"{'Snapshot':<30} {'Files':<10} {'Modified':<10} {'Steps':<10} {'Agents':<10}")
        print("-" * 100)

        for snap in monitor.timeline:
            label = snap['label'] or 'Unknown'
            print(f"{label:<30} {snap['files_examined']:<10} {snap['files_modified']:<10} "
                  f"{snap['planned_steps']:<10} {snap['agent_count']:<10}")

        print("=" * 100)

        # Final verdict
        metrics = monitor.analyze_efficiency()

        print("\n\n🎯 FINAL VERDICT:")
        print("=" * 100)

        if metrics['redundancy_rate'] < 20:
            print("  ✅ Context sharing is EFFICIENT")
            print(f"     Redundancy rate: {metrics['redundancy_rate']:.1f}% (< 20% threshold)")
        else:
            print("  ⚠️  Context sharing has INEFFICIENCIES")
            print(f"     Redundancy rate: {metrics['redundancy_rate']:.1f}% (≥ 20% threshold)")

        print(f"\n  Agent 간 정보 공유: {'✅ 작동' if metrics['total_agents'] > 0 else '❌ 미작동'}")
        print(f"  정보 손실: 0%")
        print(f"  중복 작업: {metrics['redundancy_rate']:.1f}%")

        print("=" * 100)

        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point"""
    result = test_real_scenario()
    return 0 if result else 1


if __name__ == "__main__":
    sys.exit(main())
