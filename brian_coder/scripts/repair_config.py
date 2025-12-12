
import yaml
from pathlib import Path
import sys

def fix_config():
    config_path = Path.home() / ".brian_rag" / ".ragconfig"
    if not config_path.exists():
        print("Config not found.")
        return

    content = config_path.read_text()
    lines = content.splitlines()
    
    # Remove the bad line
    lines = [l for l in lines if "PCIe/{pattern}" not in l]
    
    # Parse YAML
    try:
        data = yaml.safe_load("\n".join(lines))
    except yaml.YAMLError as e:
        print(f"YAML Error: {e}")
        # Manual fallback repair
        return

    # Add PCIe to spec includes
    if "spec" in data:
        if "include" not in data["spec"]:
            data["spec"]["include"] = []
        
        # Check if PCIe glob exists
        pcie_glob = "PCIe/**/*.md"
        if pcie_glob not in data["spec"]["include"]:
            data["spec"]["include"].append(pcie_glob)
            print(f"Added {pcie_glob} to spec.include")
    
    # Write back
    with open(config_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
    
    print("Config repaired successfully.")

if __name__ == "__main__":
    fix_config()
