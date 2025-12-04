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
