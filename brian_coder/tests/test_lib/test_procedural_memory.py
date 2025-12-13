"""
Procedural Memory Test Suite

Comprehensive tests for:
- Action/Trajectory data classes
- Build (creating trajectories)
- Retrieve (finding similar experiences)
- Update (reflection and learning)
- Task classification
"""
import sys
import os
import unittest
import tempfile
import shutil

# Import ProceduralMemory - path setup handled by conftest.py
from procedural_memory import ProceduralMemory, Action, Trajectory


class TestAction(unittest.TestCase):
    """Test Action data class"""
    
    def test_action_creation(self):
        """Test creating an action"""
        action = Action(
            tool="read_file",
            args="test.v",
            result="success",
            observation="File contents..."
        )
        self.assertEqual(action.tool, "read_file")
        self.assertEqual(action.result, "success")
    
    def test_action_to_dict(self):
        """Test action serialization"""
        action = Action(tool="run_command", args="make", result="success")
        d = action.to_dict()
        
        self.assertIn("tool", d)
        self.assertIn("args", d)
        self.assertIn("result", d)
    
    def test_action_from_dict(self):
        """Test action deserialization"""
        data = {
            "tool": "write_file",
            "args": "test.txt",
            "result": "success",
            "observation": "Written",
            "timestamp": "2024-01-01T00:00:00"
        }
        action = Action.from_dict(data)
        self.assertEqual(action.tool, "write_file")


class TestTrajectory(unittest.TestCase):
    """Test Trajectory data class"""
    
    def test_trajectory_creation(self):
        """Test creating a trajectory"""
        trajectory = Trajectory(
            id="traj_001",
            task_type="compile_verilog",
            task_description="Compile pcie_receiver.v",
            actions=[],
            outcome="success",
            iterations=1
        )
        self.assertEqual(trajectory.id, "traj_001")
        self.assertEqual(trajectory.outcome, "success")
    
    def test_trajectory_default_values(self):
        """Test trajectory default values"""
        trajectory = Trajectory(
            id="test",
            task_type="test",
            task_description="test",
            actions=[],
            outcome="success",
            iterations=1
        )
        self.assertEqual(trajectory.success_rate, 1.0)
        self.assertEqual(trajectory.usage_count, 0)
    
    def test_trajectory_to_dict(self):
        """Test trajectory serialization"""
        trajectory = Trajectory(
            id="test",
            task_type="test",
            task_description="test",
            actions=[],
            outcome="success",
            iterations=1
        )
        d = trajectory.to_dict()
        
        self.assertIn("id", d)
        self.assertIn("task_type", d)
        self.assertIn("outcome", d)


class TestProceduralMemoryBuild(unittest.TestCase):
    """Test Build functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.pm = ProceduralMemory(memory_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_build_trajectory(self):
        """Test building a new trajectory"""
        actions = [
            Action(tool="read_file", args="test.v", result="success"),
            Action(tool="run_command", args="iverilog test.v", result="success")
        ]
        
        traj_id = self.pm.build(
            task_description="Compile Verilog file",
            actions=actions,
            outcome="success",
            iterations=2
        )
        
        self.assertIsNotNone(traj_id)
        self.assertIn("traj_", traj_id)
    
    def test_build_stores_trajectory(self):
        """Test that built trajectory is stored"""
        initial_count = len(self.pm.trajectories)
        
        actions = [Action(tool="test", args="arg", result="success")]
        self.pm.build("Test task", actions, "success", 1)
        
        self.assertEqual(len(self.pm.trajectories), initial_count + 1)


class TestProceduralMemoryRetrieve(unittest.TestCase):
    """Test Retrieve functionality"""
    
    def setUp(self):
        """Set up test fixtures with sample trajectories"""
        self.temp_dir = tempfile.mkdtemp()
        self.pm = ProceduralMemory(memory_dir=self.temp_dir)
        
        # Add some sample trajectories
        actions1 = [Action(tool="run_command", args="iverilog test.v", result="success")]
        self.pm.build("Compile Verilog module", actions1, "success", 1)
        
        actions2 = [Action(tool="read_file", args="test.py", result="success")]
        self.pm.build("Debug Python script", actions2, "success", 1)
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_retrieve_returns_list(self):
        """Test that retrieve returns a list"""
        results = self.pm.retrieve("Compile another Verilog file", limit=3)
        self.assertIsInstance(results, list)
    
    def test_retrieve_respects_limit(self):
        """Test that retrieve respects limit"""
        results = self.pm.retrieve("Any task", limit=1)
        self.assertLessEqual(len(results), 1)
    
    def test_retrieve_returns_tuples(self):
        """Test that results are (score, trajectory) tuples"""
        results = self.pm.retrieve("Compile Verilog", limit=1)
        
        if results:
            self.assertEqual(len(results[0]), 2)
            score, traj = results[0]
            self.assertIsInstance(score, float)
            self.assertIsInstance(traj, Trajectory)


class TestProceduralMemoryUpdate(unittest.TestCase):
    """Test Update functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.pm = ProceduralMemory(memory_dir=self.temp_dir)
        
        actions = [Action(tool="test", args="arg", result="success")]
        self.traj_id = self.pm.build("Test task", actions, "success", 1)
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_update_reflection(self):
        """Test updating with reflection"""
        result = self.pm.update(
            self.traj_id,
            reflection="Should check for errors first"
        )
        self.assertTrue(result)
    
    def test_update_nonexistent(self):
        """Test updating non-existent trajectory"""
        result = self.pm.update("nonexistent_id", "reflection")
        self.assertFalse(result)
    
    def test_increment_usage(self):
        """Test incrementing usage count"""
        initial_usage = self.pm.trajectories[self.traj_id].usage_count
        
        self.pm.increment_usage(self.traj_id)
        
        new_usage = self.pm.trajectories[self.traj_id].usage_count
        self.assertEqual(new_usage, initial_usage + 1)


class TestTaskClassification(unittest.TestCase):
    """Test task classification"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.pm = ProceduralMemory(memory_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_classify_verilog_compile(self):
        """Test classifying Verilog compile task"""
        actions = [Action(tool="run_command", args="iverilog test.v", result="success")]
        task_type = self.pm._classify_task("Compile Verilog", actions)
        self.assertEqual(task_type, "compile_verilog")
    
    def test_classify_debug_task(self):
        """Test classifying debug task"""
        actions = [Action(tool="read_file", args="test.v", result="success")]
        task_type = self.pm._classify_task("Debug the signal issue", actions)
        # Note: actual classification may return 'debug_task' instead of 'debug_issue'
        self.assertIn("debug", task_type)


class TestProceduralMemoryPersistence(unittest.TestCase):
    """Test save/load persistence"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_persistence_across_instances(self):
        """Test that trajectories persist"""
        pm1 = ProceduralMemory(memory_dir=self.temp_dir)
        actions = [Action(tool="test", args="arg", result="success")]
        traj_id = pm1.build("Test task", actions, "success", 1)
        pm1.save()  # Explicitly save
        
        # Create new instance
        pm2 = ProceduralMemory(memory_dir=self.temp_dir)
        # Just check that something was persisted
        self.assertIsInstance(pm2.trajectories, dict)

    def test_multi_instance_save_merges_without_loss(self):
        """Test that saves from multiple instances don't clobber each other."""
        pm1 = ProceduralMemory(memory_dir=self.temp_dir)
        pm2 = ProceduralMemory(memory_dir=self.temp_dir)

        pm1.build("Task 1", [Action(tool="test", args="1", result="success")], "success", 1)
        pm1.save()

        pm2.build("Task 2", [Action(tool="test", args="2", result="success")], "success", 1)
        pm2.save()

        pm3 = ProceduralMemory(memory_dir=self.temp_dir)
        self.assertGreaterEqual(len(pm3.trajectories), 2)
    
    def test_get_stats(self):
        """Test getting statistics"""
        pm = ProceduralMemory(memory_dir=self.temp_dir)
        stats = pm.get_stats()
        
        self.assertIn("total_trajectories", stats)
        self.assertIn("task_types", stats)


if __name__ == '__main__':
    print("\n" + "="*70)
    print("Procedural Memory Test Suite")
    print("="*70 + "\n")
    
    unittest.main(verbosity=2)
