#!/usr/bin/env python3
"""
Demo script to showcase colored output
컬러 출력 데모 스크립트
"""

# Import the Color class from main.py
import sys
import os

# Simple ANSI color codes for standalone demo
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


def demo_colors():
    """Demonstrate all color types"""
    print("\n" + "="*60)
    print(Color.BOLD + Color.CYAN + "컬러 출력 데모 (Color Output Demo)" + Color.RESET)
    print("="*60 + "\n")
    
    # System messages
    print(Color.system("[System] 시스템 메시지 - Cyan 색상"))
    print(Color.info("[System] 정보 메시지 - Dim Cyan 색상\n"))
    
    # User messages
    print(Color.user("You: 사용자 입력 - Green 색상\n"))
    
    # Agent messages
    print(Color.agent("Agent (Iteration 1/5): 에이전트 응답 - Blue 색상\n"))
    
    # Tool messages
    print(Color.tool("  🔧 Tool: read_file - Magenta 색상"))
    print(Color.info("  ✓ Result: File read successfully... - Info 색상\n"))
    
    # Success messages
    print(Color.success("[System] ✓ 히스토리 저장 완료 - Bold Green\n"))
    
    # Warning messages
    print(Color.warning("[System] ⚠️  경고: Context 크기 초과 - Yellow\n"))
    
    # Error messages
    print(Color.error("[System] ❌ 에러 발생 - Bold Red\n"))
    
    # Compression demo
    print(Color.warning("[System] Context size (50000 chars) exceeded threshold (40000). Compressing..."))
    print(Color.info("[System] Generating summary of old history..."), end="", flush=True)
    import time
    time.sleep(1)
    print(Color.success(" Done."))
    print(Color.success("[System] Compression complete. Size reduced: 50000 -> 25000 chars\n"))
    
    # ReAct loop simulation
    print(Color.agent("Agent (Iteration 1/5): "), end="")
    print("Thinking... 파일을 읽어야겠습니다.\n")
    print(Color.tool("  🔧 Tool: read_file"))
    print(Color.info("  ✓ Result: Successfully read file.py...\n"))
    
    print(Color.agent("Agent (Iteration 2/5): "), end="")
    print("파일 내용을 수정하겠습니다.\n")
    print(Color.tool("  🔧 Tool: write_file"))
    print(Color.warning("  [System] ⚠️  Consecutive error #1/3"))
    print(Color.info("  ✓ Result: Error: Permission denied...\n"))
    
    print(Color.warning("\nExiting..."))
    
    print("\n" + "="*60)
    print(Color.BOLD + "색상 구분으로 가독성이 크게 향상됩니다! 🎨" + Color.RESET)
    print("="*60 + "\n")


if __name__ == "__main__":
    demo_colors()
