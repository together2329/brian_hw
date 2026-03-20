"""
Tools Test Suite

Comprehensive tests for basic file/command tools:
- read_file / write_file
- run_command
- list_dir
- grep_file / read_lines / find_files
- replace_in_file / replace_lines
- git_status / git_diff
- create_plan / get_plan / mark_step_done
"""
import sys
import os
import unittest
import tempfile
import shutil

# Import tools - path setup handled by conftest.py
from tools import (
    read_file, write_file, run_command, list_dir,
    grep_file, read_lines, find_files,
    replace_in_file, replace_lines,
    git_status, git_diff,
    create_plan, get_plan, mark_step_done
)


class TestReadWriteFile(unittest.TestCase):
    """Test read_file and write_file functions"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test.txt")
    
    def tearDown(self):
        """Clean up temp files"""
        shutil.rmtree(self.temp_dir)
    
    def test_write_file_creates_file(self):
        """Test that write_file creates a new file"""
        result = write_file(self.test_file, "Hello World")
        self.assertIn("Successfully", result)
        self.assertTrue(os.path.exists(self.test_file))
    
    def test_read_file_returns_content(self):
        """Test that read_file returns file content"""
        # First write
        write_file(self.test_file, "Test Content")
        
        # Then read
        content = read_file(self.test_file)
        self.assertEqual(content.strip(), "Test Content")
    
    def test_read_file_not_found(self):
        """Test read_file with non-existent file"""
        result = read_file("/nonexistent/path/file.txt")
        self.assertIn("Error", result)
    
    def test_write_file_overwrites(self):
        """Test that write_file overwrites existing content"""
        write_file(self.test_file, "First")
        write_file(self.test_file, "Second")
        
        content = read_file(self.test_file)
        self.assertIn("Second", content)
        self.assertNotIn("First", content)


class TestRunCommand(unittest.TestCase):
    """Test run_command function"""
    
    def test_simple_command(self):
        """Test simple echo command"""
        result = run_command("echo 'Hello'")
        self.assertIn("Hello", result)
    
    def test_command_with_pipes(self):
        """Test command with pipes"""
        result = run_command("echo 'abc' | cat")
        self.assertIn("abc", result)
    
    def test_ls_command(self):
        """Test ls command"""
        result = run_command("ls -la")
        # Should not error
        self.assertNotIn("Error", result)
    
    def test_invalid_command(self):
        """Test invalid command returns error"""
        result = run_command("nonexistent_command_xyz")
        self.assertIn("Error", result)


class TestListDir(unittest.TestCase):
    """Test list_dir function"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create some test files
        for name in ["file1.txt", "file2.py", "file3.v"]:
            with open(os.path.join(self.temp_dir, name), 'w') as f:
                f.write("test")
        
        # Create a subdirectory
        os.makedirs(os.path.join(self.temp_dir, "subdir"))
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.temp_dir)
    
    def test_list_dir_returns_files(self):
        """Test that list_dir returns files"""
        result = list_dir(self.temp_dir)
        self.assertIn("file1.txt", result)
        self.assertIn("file2.py", result)
    
    def test_list_dir_shows_subdir(self):
        """Test that list_dir shows subdirectories"""
        result = list_dir(self.temp_dir)
        self.assertIn("subdir", result)
    
    def test_list_dir_invalid_path(self):
        """Test list_dir with invalid path"""
        result = list_dir("/nonexistent/path")
        # Should handle gracefully
        self.assertIsInstance(result, str)


class TestGrepFile(unittest.TestCase):
    """Test grep_file function"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test.txt")
        
        # Create file with searchable content
        content = """line 1: hello world
line 2: foo bar
line 3: hello again
line 4: goodbye
line 5: hello foo
"""
        with open(self.test_file, 'w') as f:
            f.write(content)
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.temp_dir)
    
    def test_grep_finds_pattern(self):
        """Test that grep finds matching lines"""
        result = grep_file("hello", self.test_file, context_lines=0)
        self.assertIn("hello", result)
    
    def test_grep_no_match(self):
        """Test grep with no matches"""
        result = grep_file("nonexistent_pattern", self.test_file)
        # Should indicate no matches found
        self.assertIn("no matches", result.lower())


class TestReadLines(unittest.TestCase):
    """Test read_lines function"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test.txt")
        
        # Create file with numbered lines
        lines = [f"Line {i}\n" for i in range(1, 11)]
        with open(self.test_file, 'w') as f:
            f.writelines(lines)
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.temp_dir)
    
    def test_read_specific_lines(self):
        """Test reading specific line range"""
        result = read_lines(self.test_file, 3, 5)
        self.assertIn("Line 3", result)
        self.assertIn("Line 5", result)
    
    def test_read_single_line(self):
        """Test reading single line"""
        result = read_lines(self.test_file, 1, 1)
        self.assertIn("Line 1", result)


class TestFindFiles(unittest.TestCase):
    """Test find_files function"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create files with different extensions
        for name in ["test1.py", "test2.py", "module.v", "data.txt"]:
            with open(os.path.join(self.temp_dir, name), 'w') as f:
                f.write("test")
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.temp_dir)
    
    def test_find_by_extension(self):
        """Test finding files by extension"""
        result = find_files("*.py", self.temp_dir)
        self.assertIn("test1.py", result)
        self.assertIn("test2.py", result)
        self.assertNotIn("module.v", result)


class TestReplaceInFile(unittest.TestCase):
    """Test replace_in_file function"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test.txt")
        
        with open(self.test_file, 'w') as f:
            f.write("foo bar foo baz")
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.temp_dir)
    
    def test_replace_single(self):
        """Test replacing single occurrence"""
        result = replace_in_file(self.test_file, "foo", "XXX", count=1)
        
        content = read_file(self.test_file)
        self.assertIn("XXX", content)
        self.assertIn("foo", content)  # Second occurrence should remain
    
    def test_replace_all(self):
        """Test replacing occurrences with line specification"""
        # With multiple occurrences, need to specify line range or use unique text
        # Create file with unique occurrence
        write_file(self.test_file, "unique_text bar baz")
        result = replace_in_file(self.test_file, "unique_text", "REPLACED")
        
        content = read_file(self.test_file)
        self.assertIn("REPLACED", content)
        self.assertNotIn("unique_text", content)


class TestReplaceLines(unittest.TestCase):
    """Test replace_lines function"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test.txt")
        
        lines = ["Line 1\n", "Line 2\n", "Line 3\n", "Line 4\n"]
        with open(self.test_file, 'w') as f:
            f.writelines(lines)
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.temp_dir)
    
    def test_replace_line_range(self):
        """Test replacing a range of lines"""
        result = replace_lines(self.test_file, 2, 3, "NEW LINE 2\nNEW LINE 3\n")
        
        content = read_file(self.test_file)
        self.assertIn("NEW LINE 2", content)
        self.assertIn("Line 1", content)
        self.assertIn("Line 4", content)


class TestPlanTools(unittest.TestCase):
    """Test plan-related tools"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.original_dir = os.getcwd()
        self.temp_dir = tempfile.mkdtemp()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        """Clean up"""
        os.chdir(self.original_dir)
        shutil.rmtree(self.temp_dir)
    
    def test_create_plan(self):
        """Test creating a plan"""
        result = create_plan("Test Task", "Step 1\nStep 2\nStep 3")
        self.assertIn("created", result.lower())
        self.assertTrue(os.path.exists("current_plan.md"))
    
    def test_get_plan(self):
        """Test getting plan content"""
        create_plan("Test Task", "Step 1\nStep 2")
        result = get_plan()
        self.assertIn("Step 1", result)
        self.assertIn("Step 2", result)
    
    def test_mark_step_done(self):
        """Test marking step as done"""
        create_plan("Test Task", "Step 1\nStep 2")
        result = mark_step_done(1)
        self.assertIn("done", result.lower())


if __name__ == '__main__':
    print("\n" + "="*70)
    print("Tools Test Suite")
    print("="*70 + "\n")
    
    unittest.main(verbosity=2)
