"""
Display utilities for Brian Coder.
Handles ANSI color codes and terminal output formatting.
"""

class Color:
    """ANSI color codes for terminal output"""
    # Basic colors
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    
    # Styles
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RESET = '\033[0m'
    
    @staticmethod
    def system(text):
        """System messages - Cyan"""
        return f"{Color.CYAN}{text}{Color.RESET}"
    
    @staticmethod
    def user(text):
        """User messages - Green"""
        return f"{Color.GREEN}{text}{Color.RESET}"
    
    @staticmethod
    def agent(text):
        """Agent messages - Blue"""
        return f"{Color.BLUE}{text}{Color.RESET}"
    
    @staticmethod
    def tool(text):
        """Tool names - Magenta"""
        return f"{Color.MAGENTA}{text}{Color.RESET}"
    
    @staticmethod
    def success(text):
        """Success messages - Green + Bold"""
        return f"{Color.BOLD}{Color.GREEN}{text}{Color.RESET}"
    
    @staticmethod
    def warning(text):
        """Warning messages - Yellow"""
        return f"{Color.YELLOW}{text}{Color.RESET}"
    
    @staticmethod
    def error(text):
        """Error messages - Red + Bold"""
        return f"{Color.BOLD}{Color.RED}{text}{Color.RESET}"
    
    @staticmethod
    def info(text):
        """Info messages - Cyan + Dim"""
        return f"{Color.DIM}{Color.CYAN}{text}{Color.RESET}"

    @staticmethod
    def debug(text):
        """Debug messages - Purple/Magenta"""
        return f"{Color.MAGENTA}{text}{Color.RESET}"
        
    @staticmethod
    def action(text):
        """Action messages (e.g. key decisions) - Green + Bold + Underline"""
        return f"{Color.BOLD}{Color.GREEN}\033[4m{text}{Color.RESET}"

    
    @staticmethod
    def diff_add(text):
        """Added lines in diff - Green background"""
        return f"{Color.GREEN}+ {text}{Color.RESET}"
    
    @staticmethod
    def diff_remove(text):
        """Removed lines in diff - Red"""
        return f"{Color.RED}- {text}{Color.RESET}"
    
    @staticmethod
    def diff_context(text):
        """Context lines in diff - Dim"""
        return f"{Color.DIM}  {text}{Color.RESET}"


def format_diff(old_text, new_text, context_lines=3):
    """
    Generate a visual unified diff between old and new text.
    Uses Python standard library only (no external dependencies).
    
    Args:
        old_text: Original text content
        new_text: New text content  
        context_lines: Number of context lines around changes
    
    Returns:
        Formatted diff string with colors
    """
    import difflib
    
    old_lines = old_text.splitlines(keepends=True)
    new_lines = new_text.splitlines(keepends=True)
    
    diff = difflib.unified_diff(
        old_lines, new_lines,
        fromfile='before',
        tofile='after',
        n=context_lines
    )
    
    result = []
    for line in diff:
        line_stripped = line.rstrip('\n')
        if line.startswith('+++') or line.startswith('---'):
            result.append(f"{Color.BOLD}{Color.CYAN}{line_stripped}{Color.RESET}")
        elif line.startswith('@@'):
            result.append(f"{Color.MAGENTA}{line_stripped}{Color.RESET}")
        elif line.startswith('+'):
            result.append(Color.diff_add(line_stripped[1:]))
        elif line.startswith('-'):
            result.append(Color.diff_remove(line_stripped[1:]))
        else:
            result.append(Color.diff_context(line_stripped[1:] if line.startswith(' ') else line_stripped))
    
    return '\n'.join(result) if result else "[No changes detected]"
