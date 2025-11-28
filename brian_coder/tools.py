import os
import subprocess
import json

def read_file(path):
    """Reads the content of a file."""
    try:
        if not os.path.exists(path):
            return f"Error: File '{path}' does not exist."
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"

def write_file(path, content):
    """Writes content to a file. Overwrites if exists."""
    try:
        dir_name = os.path.dirname(path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote to '{path}'."
    except Exception as e:
        return f"Error writing file: {e}"

def run_command(command):
    """Runs a shell command and returns output."""
    try:
        # Security Note: In a real production agent, you'd want to sandbox this.
        # Since this is for internal use by a developer, we use subprocess directly.
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=30
        )
        output = result.stdout
        if result.stderr:
            output += f"\nSTDERR:\n{result.stderr}"
        return output.strip()
    except subprocess.TimeoutExpired:
        return "Error: Command timed out."
    except Exception as e:
        return f"Error running command: {e}"

def list_dir(path="."):
    """Lists files in a directory."""
    try:
        return "\n".join(os.listdir(path))
    except Exception as e:
        return f"Error listing directory: {e}"

# Registry of available tools
AVAILABLE_TOOLS = {
    "read_file": read_file,
    "write_file": write_file,
    "run_command": run_command,
    "list_dir": list_dir
}
