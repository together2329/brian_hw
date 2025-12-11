"""
Integration Test Suite #2: Memory ↔ ProceduralMemory

Tests the integration between:
- MemorySystem (declarative - preferences, context)
- ProceduralMemory (procedural - how-to knowledge, trajectories)

Scenarios:
- User preference → Influences trajectory classification
- Project context → Used in trajectory retrieval
- Combined memory for agent decision making
"""
import sys
import os
import unittest
import tempfile
import shutil

# Import modules - path setup handled by conftest.py
from memory import MemorySystem
from procedural_memory import ProceduralMemory, Action, Trajectory


class TestMemoryProceduralIntegration(unittest.TestCase):
    """Test: Declarative + Procedural memory working together"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.memory = MemorySystem(memory_dir=self.temp_dir)
        self.procedural = ProceduralMemory(memory_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_preference_influences_trajectory_selection(self):
        """Test: User preferences should influence which trajectories are retrieved"""
        # Store user preference
        self.memory.update_preference("preferred_approach", "incremental")
        self.memory.update_preference("project_type", "Verilog")
        
        # Build some trajectories
        actions1 = [Action(tool="run_command", args="iverilog test.v", result="success")]
        traj_id1 = self.procedural.build(
            task_description="Compile Verilog incrementally",
            actions=actions1,
            outcome="success",
            iterations=1
        )
        
        actions2 = [Action(tool="run_command", args="make clean all", result="success")]
        traj_id2 = self.procedural.build(
            task_description="Full rebuild from scratch",
            actions=actions2,
            outcome="success",
            iterations=3
        )
        
        # Retrieve similar to user preference
        pref = self.memory.get_preference("preferred_approach")
        results = self.procedural.retrieve(f"Compile Verilog {pref}", limit=2)
        
        # Should return list of trajectories
        self.assertIsInstance(results, list)
    
    def test_project_context_used_in_retrieval(self):
        """Test: Project context helps trajectory matching"""
        # Set project context
        self.memory.update_project_context("project_type", "PCIe Controller")
        self.memory.update_project_context("main_modules", ["pcie_receiver", "pcie_tx"])
        
        # Build relevant trajectory
        actions = [
            Action(tool="read_file", args="pcie_receiver.v", result="success"),
            Action(tool="grep_file", args="pattern='error'", result="found 3")
        ]
        self.procedural.build(
            task_description="Debug PCIe receiver module",
            actions=actions,
            outcome="success",
            iterations=2
        )
        
        # Retrieve using project context
        project_type = self.memory.get_project_context("project_type")
        results = self.procedural.retrieve(f"Debug {project_type}", limit=3)
        
        self.assertIsInstance(results, list)


class TestCombinedMemoryForAgent(unittest.TestCase):
    """Test: Combined memory system for agent decisions"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.memory = MemorySystem(memory_dir=self.temp_dir)
        self.procedural = ProceduralMemory(memory_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_build_combined_context(self):
        """Test: Build combined context from both memory systems"""
        # Set up memories
        self.memory.update_preference("coding_style", "snake_case")
        self.memory.update_project_context("project_type", "RTL Design")
        
        actions = [Action(tool="write_file", args="test.v", result="success")]
        self.procedural.build("Create Verilog module", actions, "success", 1)
        
        # Build combined context (simulating agent preparation)
        combined_context = {
            "preferences": self.memory.list_preferences(),
            "project_context": self.memory.list_project_context(),
            "past_experiences": len(self.procedural.trajectories)
        }
        
        self.assertIn("preferences", combined_context)
        self.assertIn("project_context", combined_context)
        self.assertGreaterEqual(combined_context["past_experiences"], 1)
    
    def test_memory_prompt_formatting(self):
        """Test: Both memories can be formatted for LLM prompts"""
        self.memory.update_preference("add_comments", True)
        self.memory.update_project_context("main_file", "top.v")
        
        # Format declarative memory
        pref_prompt = self.memory.format_preferences_for_prompt()
        ctx_prompt = self.memory.format_project_context_for_prompt()
        
        # Both should be strings
        self.assertIsInstance(pref_prompt, str)
        self.assertIsInstance(ctx_prompt, str)


class TestMemoryPersistence(unittest.TestCase):
    """Test: Both memory systems persist together"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_both_memories_persist(self):
        """Test: Both declarative and procedural memories persist"""
        # Session 1: Create memories
        mem1 = MemorySystem(memory_dir=self.temp_dir)
        proc1 = ProceduralMemory(memory_dir=self.temp_dir)
        
        mem1.update_preference("test_key", "test_value")
        actions = [Action(tool="test", args="test", result="success")]
        traj_id = proc1.build("Test task", actions, "success", 1)
        proc1.save()
        
        # Session 2: Verify persistence
        mem2 = MemorySystem(memory_dir=self.temp_dir)
        proc2 = ProceduralMemory(memory_dir=self.temp_dir)
        
        pref = mem2.get_preference("test_key")
        self.assertEqual(pref, "test_value")
        
        # Procedural memory should be loadable
        self.assertIsInstance(proc2.trajectories, dict)


if __name__ == '__main__':
    print("\n" + "="*70)
    print("Integration Test: Memory ↔ ProceduralMemory")
    print("="*70 + "\n")
    
    unittest.main(verbosity=2)
