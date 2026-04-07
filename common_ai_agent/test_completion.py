"""
Run: python3 test_completion.py
Type '/' → should show slash command completions
Type '@' → should show file completions
Ctrl+C to quit
"""
import sys, os
sys.path.insert(0, 'vendor')
sys.path.insert(0, 'src')
sys.path.insert(0, 'core')

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.shortcuts import CompleteStyle

class TestCompleter(Completer):
    COMMANDS = ['/help', '/plan', '/todo', '/model', '/clear',
                '/compact', '/status', '/tools', '/config', '/git']

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        print(f"\n[DEBUG] get_completions called: {text!r}", end='', flush=True)

        if text.startswith('/'):
            for cmd in self.COMMANDS:
                if cmd.startswith(text):
                    yield Completion(cmd, start_position=-len(text), display=cmd)

        elif '@' in text:
            at_pos = text.rfind('@')
            partial = text[at_pos + 1:]
            base = '.'
            if '/' in partial:
                dir_part, stem = partial.rsplit('/', 1)
                base = dir_part or '.'
            else:
                stem = partial
            try:
                for name in sorted(os.listdir(base)):
                    if name.startswith('.'): continue
                    if stem and not name.lower().startswith(stem.lower()): continue
                    is_dir = os.path.isdir(os.path.join(base, name))
                    display = name + ('/' if is_dir else '')
                    yield Completion(display, start_position=-len(partial), display=display)
            except OSError:
                pass

session = PromptSession(
    completer=TestCompleter(),
    complete_while_typing=True,
    complete_style=CompleteStyle.COLUMN,
)

print("Type '/' for commands, '@' for files. Ctrl+C to quit.\n")
try:
    while True:
        result = session.prompt('> ')
        print(f'Input: {result!r}')
except (KeyboardInterrupt, EOFError):
    print('\nBye.')
