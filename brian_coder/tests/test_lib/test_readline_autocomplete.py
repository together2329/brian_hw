"""
Test readline autocomplete functionality
"""

import readline
import sys

# Commands to autocomplete
commands = ["/help", "/status", "/context", "/clear", "/compact", "/tools", "/config"]

def completer(text, state):
    """Simple completer for testing"""
    options = [cmd for cmd in commands if cmd.startswith(text)]
    if state < len(options):
        return options[state]
    return None

# Setup readline
readline.set_completer(completer)
readline.set_completer_delims(' \t\n')

# Check which readline we're using
print("=" * 60)
print("Readline Autocomplete Test")
print("=" * 60)
print(f"Readline module: {readline.__doc__[:50] if readline.__doc__ else 'Unknown'}...")
print(f"Readline version: {readline.__version__ if hasattr(readline, '__version__') else 'N/A'}")

# Try to detect libedit vs GNU readline
try:
    # GNU readline specific
    readline.parse_and_bind("tab: complete")
    print("Backend: GNU Readline")
except:
    try:
        # libedit (macOS default) specific
        readline.parse_and_bind("bind ^I rl_complete")
        print("Backend: libedit (macOS)")
    except:
        print("Backend: Unknown")

print("\n" + "=" * 60)
print("Instructions:")
print("=" * 60)
print("Type /h and press TAB to see autocomplete")
print("Type /c and press TAB twice to see all options")
print("Type 'quit' to exit")
print("=" * 60)
print()

# Test loop
while True:
    try:
        user_input = input("Test> ")
        if user_input.lower() in ['quit', 'exit', 'q']:
            break

        if user_input in commands:
            print(f"✅ Command recognized: {user_input}")
        elif user_input.startswith('/'):
            print(f"❌ Unknown command: {user_input}")
            print(f"💡 Available: {', '.join(commands)}")
        else:
            print(f"ℹ️  Not a command (doesn't start with /)")
    except (EOFError, KeyboardInterrupt):
        print("\nExiting...")
        break

print("\n✅ Test completed")
