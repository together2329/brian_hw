"""
Memory System Test Suite

Comprehensive tests for:
- Preference management (CRUD)
- Project context management
- Prompt formatting
- Import/Export
"""
import sys
import os
import unittest
import tempfile
import shutil

# Import MemorySystem - path setup handled by conftest.py
from memory import MemorySystem


class TestPreferenceManagement(unittest.TestCase):
    """Test preference CRUD operations"""
    
    def setUp(self):
        """Set up test fixtures with temp directory"""
        self.temp_dir = tempfile.mkdtemp()
        self.memory = MemorySystem(memory_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_update_preference(self):
        """Test adding/updating a preference"""
        self.memory.update_preference("coding_style", "snake_case")
        value = self.memory.get_preference("coding_style")
        self.assertEqual(value, "snake_case")
    
    def test_get_preference_default(self):
        """Test getting preference with default value"""
        value = self.memory.get_preference("nonexistent", default="default_val")
        self.assertEqual(value, "default_val")
    
    def test_get_preference_none_default(self):
        """Test getting preference returns None if not found"""
        value = self.memory.get_preference("nonexistent")
        self.assertIsNone(value)
    
    def test_remove_preference(self):
        """Test removing a preference"""
        self.memory.update_preference("to_remove", "value")
        result = self.memory.remove_preference("to_remove")
        self.assertTrue(result)
        
        value = self.memory.get_preference("to_remove")
        self.assertIsNone(value)
    
    def test_remove_nonexistent_preference(self):
        """Test removing non-existent preference"""
        result = self.memory.remove_preference("nonexistent")
        self.assertFalse(result)
    
    def test_list_preferences(self):
        """Test listing all preferences"""
        self.memory.update_preference("key1", "value1")
        self.memory.update_preference("key2", "value2")
        
        prefs = self.memory.list_preferences()
        self.assertIn("key1", prefs)
        self.assertIn("key2", prefs)
    
    def test_preference_overwrite(self):
        """Test that updating overwrites existing value"""
        self.memory.update_preference("key", "old")
        self.memory.update_preference("key", "new")
        
        value = self.memory.get_preference("key")
        self.assertEqual(value, "new")


class TestProjectContext(unittest.TestCase):
    """Test project context management"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.memory = MemorySystem(memory_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_update_project_context(self):
        """Test adding project context"""
        self.memory.update_project_context("project_type", "PCIe Verilog")
        value = self.memory.get_project_context("project_type")
        self.assertEqual(value, "PCIe Verilog")
    
    def test_get_project_context_default(self):
        """Test getting context with default"""
        value = self.memory.get_project_context("nonexistent", default="default")
        self.assertEqual(value, "default")
    
    def test_remove_project_context(self):
        """Test removing project context"""
        self.memory.update_project_context("to_remove", "value")
        result = self.memory.remove_project_context("to_remove")
        self.assertTrue(result)
    
    def test_list_project_context(self):
        """Test listing all project context"""
        self.memory.update_project_context("ctx1", "val1")
        self.memory.update_project_context("ctx2", "val2")
        
        ctx = self.memory.list_project_context()
        self.assertIn("ctx1", ctx)


class TestPromptFormatting(unittest.TestCase):
    """Test prompt formatting functions"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.memory = MemorySystem(memory_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_format_preferences_for_prompt(self):
        """Test formatting preferences for LLM prompt"""
        self.memory.update_preference("coding_style", "snake_case")
        
        formatted = self.memory.format_preferences_for_prompt()
        self.assertIsInstance(formatted, str)
        # Formatted output uses title case: "Coding Style"
        self.assertIn("Coding Style", formatted) or self.assertIn("snake_case", formatted)
    
    def test_format_project_context_for_prompt(self):
        """Test formatting project context for LLM prompt"""
        self.memory.update_project_context("project_type", "Verilog")
        
        formatted = self.memory.format_project_context_for_prompt()
        self.assertIsInstance(formatted, str)
    
    def test_format_all_for_prompt(self):
        """Test formatting all memories"""
        self.memory.update_preference("pref1", "val1")
        self.memory.update_project_context("ctx1", "val1")
        
        formatted = self.memory.format_all_for_prompt()
        self.assertIsInstance(formatted, str)


class TestImportExport(unittest.TestCase):
    """Test import/export functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.memory = MemorySystem(memory_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_export_to_dict(self):
        """Test exporting memories to dict"""
        self.memory.update_preference("key", "value")
        
        exported = self.memory.export_to_dict()
        self.assertIsInstance(exported, dict)
        self.assertIn("preferences", exported)
        self.assertIn("project_context", exported)
    
    def test_import_from_dict(self):
        """Test importing memories from dict"""
        data = {
            "preferences": {"imported_pref": "imported_val"},
            "project_context": {"imported_ctx": "ctx_val"}
        }
        
        self.memory.import_from_dict(data)
        
        pref = self.memory.get_preference("imported_pref")
        self.assertEqual(pref, "imported_val")
    
    def test_clear_all(self):
        """Test clearing all memories"""
        self.memory.update_preference("key", "value")
        self.memory.update_project_context("ctx", "val")
        
        self.memory.clear_all()
        
        prefs = self.memory.list_preferences()
        self.assertEqual(len(prefs), 0)


class TestPersistence(unittest.TestCase):
    """Test save/load persistence"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_persistence_across_instances(self):
        """Test that data persists across instances"""
        # Create first instance and add data
        mem1 = MemorySystem(memory_dir=self.temp_dir)
        mem1.update_preference("persistent_key", "persistent_value")
        
        # Create second instance and verify data
        mem2 = MemorySystem(memory_dir=self.temp_dir)
        value = mem2.get_preference("persistent_key")
        self.assertEqual(value, "persistent_value")


if __name__ == '__main__':
    print("\n" + "="*70)
    print("Memory System Test Suite")
    print("="*70 + "\n")
    
    unittest.main(verbosity=2)
