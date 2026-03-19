"""
Interactive TAB completion test

실제로 TAB 키를 눌러서 자동완성이 작동하는지 테스트합니다.
"""

import sys
import os

# Add brian_coder to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'brian_coder/src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'brian_coder'))

from core.slash_commands import get_registry

print("=" * 70)
print("🧪 TAB Autocomplete Interactive Test")
print("=" * 70)

# Get registry (this sets up readline autocomplete)
registry = get_registry()

print("\n✅ Slash command registry initialized")
print(f"✅ {len(registry.get_completions())} commands available")
print(f"\n📋 Available commands:")
for cmd in registry.get_completions():
    print(f"   {cmd}")

print("\n" + "=" * 70)
print("TAB Autocomplete Instructions:")
print("=" * 70)
print("1. Type /h and press TAB")
print("   → Should autocomplete to /help")
print()
print("2. Type /c and press TAB TAB (double TAB)")
print("   → Should show all /c* options: /clear /compact /config /context")
print()
print("3. Type /st and press TAB")
print("   → Should autocomplete to /status")
print()
print("4. Press ↑ (up arrow) to see command history")
print()
print("5. Type 'quit' to exit")
print("=" * 70)
print()

# Interactive loop

while True:
    try:
        user_input = input("\033[1;36mYou: \033[0m").strip()

        if user_input.lower() in ['quit', 'exit', 'q']:
            print("\n👋 Goodbye!")
            break

        # Execute command if it's a slash command
        if user_input.startswith('/'):
            result = registry.execute(user_input)
            if result:
                print(result)
        else:
            print(f"💬 Regular message: {user_input}")

    except (EOFError, KeyboardInterrupt):
        print("\n\n👋 Goodbye!")
        break
    except Exception as e:
        print(f"\n❌ Error: {e}")

# Save history on exit
registry.save_history()
print("\n✅ Command history saved")
