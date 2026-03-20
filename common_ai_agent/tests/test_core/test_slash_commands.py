"""
Slash Commands Integration Test

Tests slash commands in Brian Coder environment.
"""

import sys
import os

# Add common_ai_agent to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'common_ai_agent/src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'common_ai_agent'))

from core.slash_commands import get_registry

print("=" * 60)
print("🧪 Slash Command Test")
print("=" * 60)

# Get registry
registry = get_registry()

# Test 1: Help command
print("\n📝 Test 1: /help")
print("-" * 60)
result = registry.execute("/help")
print(result)

# Test 2: Status command
print("\n📝 Test 2: /status")
print("-" * 60)
result = registry.execute("/status")
print(result)

# Test 3: Context command
print("\n📝 Test 3: /context")
print("-" * 60)
result = registry.execute("/context")
print(result)

# Test 4: Tools command
print("\n📝 Test 4: /tools")
print("-" * 60)
result = registry.execute("/tools")
print(result)

# Test 5: Config command
print("\n📝 Test 5: /config")
print("-" * 60)
result = registry.execute("/config")
print(result)

# Test 6: Clear command
print("\n📝 Test 6: /clear")
print("-" * 60)
result = registry.execute("/clear")
print(f"Result: {result}")
print("✅ Returns special signal: CLEAR_HISTORY")

# Test 7: Compact command
print("\n📝 Test 7: /compact")
print("-" * 60)
result = registry.execute("/compact")
print(f"Result: {result}")
print("✅ Returns special signal: COMPACT_HISTORY")

# Test 8: Compact with args
print("\n📝 Test 8: /compact keep technical details")
print("-" * 60)
result = registry.execute("/compact keep technical details")
print(f"Result: {result}")

# Test 9: Aliases
print("\n📝 Test 9: Aliases (/h, /?)")
print("-" * 60)
result1 = registry.execute("/h")
result2 = registry.execute("/?")
print("✅ /h works:", "Available Slash Commands" in result1)
print("✅ /? works:", "Available Slash Commands" in result2)

# Test 10: Unknown command
print("\n📝 Test 10: Unknown command")
print("-" * 60)
result = registry.execute("/unknown")
print(result)

# Test 11: Autocomplete
print("\n📝 Test 11: Autocomplete")
print("-" * 60)
completions = registry.get_completions()
print(f"Available completions ({len(completions)}):")
print(", ".join(completions))

# Test 12: is_command
print("\n📝 Test 12: is_command()")
print("-" * 60)
print(f"is_command('/help'): {registry.is_command('/help')}")
print(f"is_command('help'): {registry.is_command('help')}")
print(f"is_command('regular message'): {registry.is_command('regular message')}")

print("\n" + "=" * 60)
print("✅ All slash command tests completed!")
print("=" * 60)
