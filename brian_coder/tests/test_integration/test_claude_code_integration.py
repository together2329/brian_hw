#!/usr/bin/env python3
"""
Test script to validate Claude Code integration into Brian Coder
"""

import sys
import os

# Add brian_coder to path
sys.path.insert(0, '/Users/brian/Desktop/Project/brian_hw/brian_coder')
sys.path.insert(0, '/Users/brian/Desktop/Project/brian_hw/brian_coder/src')
sys.path.insert(0, '/Users/brian/Desktop/Project/brian_hw/brian_coder/core')

def test_config_flags():
    """Test that new config flags exist"""
    print("\n" + "="*60)
    print("TEST 1: Config Flags")
    print("="*60)

    import config

    # Check new flags
    flags_to_check = [
        'ENABLE_TODO_WRITE_TOOL',
        'ENABLE_ENHANCED_TOOL_DESCRIPTIONS'
    ]

    for flag in flags_to_check:
        if hasattr(config, flag):
            value = getattr(config, flag)
            print(f"✅ {flag} = {value}")
        else:
            print(f"❌ {flag} NOT FOUND")
            return False

    return True


def test_tool_registration():
    """Test that todo_write is registered in AVAILABLE_TOOLS"""
    print("\n" + "="*60)
    print("TEST 2: Tool Registration")
    print("="*60)

    from core import tools

    # Check todo_write exists
    if 'todo_write' in tools.AVAILABLE_TOOLS:
        print("✅ todo_write is registered in AVAILABLE_TOOLS")

        # Test the function signature
        func = tools.AVAILABLE_TOOLS['todo_write']
        print(f"✅ Function: {func.__name__}")

        # Check docstring
        if func.__doc__:
            first_line = func.__doc__.strip().split('\n')[0]
            print(f"✅ Docstring: {first_line[:60]}...")

        return True
    else:
        print("❌ todo_write NOT FOUND in AVAILABLE_TOOLS")
        print(f"Available tools: {list(tools.AVAILABLE_TOOLS.keys())}")
        return False


def test_tool_descriptions():
    """Test that new tool description files exist and are loadable"""
    print("\n" + "="*60)
    print("TEST 3: Tool Description Files")
    print("="*60)

    from pathlib import Path

    base_path = Path('/Users/brian/Desktop/Project/brian_hw/brian_coder/core/tool_descriptions/tools')

    new_files = [
        'run_command.txt',
        'find_files.txt',
        'list_dir.txt',
        'todo_write.txt'
    ]

    enhanced_files = [
        'read_file.txt',
        'grep_file.txt'
    ]

    all_exist = True

    print("\nNew tool description files:")
    for filename in new_files:
        filepath = base_path / filename
        if filepath.exists():
            size = filepath.stat().st_size
            lines = len(filepath.read_text().split('\n'))
            print(f"✅ {filename:20} ({lines:4} lines, {size:6} bytes)")
        else:
            print(f"❌ {filename:20} NOT FOUND")
            all_exist = False

    print("\nEnhanced tool description files:")
    for filename in enhanced_files:
        filepath = base_path / filename
        if filepath.exists():
            size = filepath.stat().st_size
            lines = len(filepath.read_text().split('\n'))
            print(f"✅ {filename:20} ({lines:4} lines, {size:6} bytes)")
        else:
            print(f"❌ {filename:20} NOT FOUND")
            all_exist = False

    return all_exist


def test_tool_description_loader():
    """Test that tool descriptions can be loaded"""
    print("\n" + "="*60)
    print("TEST 4: Tool Description Loader")
    print("="*60)

    try:
        from core.tool_descriptions import get_loader, format_tool_for_prompt

        loader = get_loader()
        print("✅ DescriptionLoader imported successfully")

        # Test loading a new tool description
        test_tools = ['run_command', 'todo_write', 'find_files']

        for tool_name in test_tools:
            try:
                formatted = format_tool_for_prompt(tool_name, include_examples=True)
                if formatted:
                    lines = formatted.count('\n')
                    print(f"✅ {tool_name:20} loaded ({lines:4} lines)")
                else:
                    print(f"⚠️  {tool_name:20} returned empty")
            except Exception as e:
                print(f"❌ {tool_name:20} error: {e}")
                return False

        return True

    except Exception as e:
        print(f"❌ Failed to import tool_descriptions: {e}")
        return False


def test_system_prompt():
    """Test that system prompt includes TodoWrite guidelines"""
    print("\n" + "="*60)
    print("TEST 5: System Prompt with TodoWrite Guidelines")
    print("="*60)

    import config

    # Build system prompt with all tools
    prompt = config.build_base_system_prompt(allowed_tools=None)

    # Check for TodoWrite section
    if "TASK MANAGEMENT WITH TODOWRITE" in prompt:
        print("✅ TodoWrite guidelines section found in system prompt")

        # Check for key phrases
        key_phrases = [
            "todo_write",
            "in_progress",
            "activeForm",
            "3+ distinct steps"
        ]

        found_count = 0
        for phrase in key_phrases:
            if phrase in prompt:
                found_count += 1
                print(f"  ✅ Found: '{phrase}'")
            else:
                print(f"  ❌ Missing: '{phrase}'")

        # Check Task Management category
        if "### Task Management" in prompt:
            print("✅ Task Management category section found")
        else:
            print("⚠️  Task Management category section not found")

        return found_count >= 3
    else:
        print("❌ TodoWrite guidelines NOT FOUND in system prompt")

        # Debug: show what sections exist
        sections = [line for line in prompt.split('\n') if line.startswith('#')]
        print(f"\nFound sections: {sections[:10]}")

        return False


def test_todo_write_function():
    """Test the todo_write function directly"""
    print("\n" + "="*60)
    print("TEST 6: todo_write Function Execution")
    print("="*60)

    from core import tools

    # Test input
    test_todos = [
        {
            "content": "Test step 1",
            "activeForm": "Testing step 1",
            "status": "in_progress"
        },
        {
            "content": "Test step 2",
            "activeForm": "Testing step 2",
            "status": "pending"
        }
    ]

    try:
        result = tools.todo_write(test_todos)

        if "Error" in result:
            print(f"❌ Function returned error: {result}")
            return False
        else:
            print("✅ todo_write executed successfully")
            print(f"\nResult:\n{result[:200]}...")
            return True

    except Exception as e:
        print(f"❌ Exception during execution: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_parallel_execution_guidance():
    """Test that parallel execution guidance exists in tool descriptions"""
    print("\n" + "="*60)
    print("TEST 7: Parallel Execution Guidance")
    print("="*60)

    from pathlib import Path

    base_path = Path('/Users/brian/Desktop/Project/brian_hw/brian_coder/core/tool_descriptions/tools')

    files_to_check = {
        'read_file.txt': 'parallel',
        'grep_file.txt': 'parallel',
        'run_command.txt': 'NEVER use for file'
    }

    all_found = True

    for filename, search_term in files_to_check.items():
        filepath = base_path / filename
        if filepath.exists():
            content = filepath.read_text().lower()
            if search_term.lower() in content:
                print(f"✅ {filename:20} contains '{search_term}'")
            else:
                print(f"❌ {filename:20} missing '{search_term}'")
                all_found = False
        else:
            print(f"❌ {filename:20} NOT FOUND")
            all_found = False

    return all_found


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("CLAUDE CODE INTEGRATION TEST SUITE")
    print("="*60)

    tests = [
        ("Config Flags", test_config_flags),
        ("Tool Registration", test_tool_registration),
        ("Tool Description Files", test_tool_descriptions),
        ("Tool Description Loader", test_tool_description_loader),
        ("System Prompt", test_system_prompt),
        ("todo_write Function", test_todo_write_function),
        ("Parallel Execution Guidance", test_parallel_execution_guidance),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n❌ {test_name} crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status:8} - {test_name}")

    print(f"\n{passed_count}/{total_count} tests passed ({passed_count*100//total_count}%)")

    if passed_count == total_count:
        print("\n🎉 ALL TESTS PASSED! Integration successful!")
        return 0
    else:
        print(f"\n⚠️  {total_count - passed_count} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
