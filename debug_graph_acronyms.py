
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'brian_coder')))

from brian_coder.core.spec_graph import get_spec_graph

def check_graph():
    print("Loading Spec Graph...")
    graph = get_spec_graph()
    
    print(f"Graph Stat: {len(graph.nodes)} nodes, {len(graph.edges)} edges")
    
    # Check for "TS" or "Trailer Size"
    targets = ["TS", "Trailer Size", "OHC", "Orthogonal Header Content"]
    
    found = False
    for node_id, node_data in graph.nodes.items():
        # Check ID
        for t in targets:
            if t.lower() in node_id.lower():
                print(f"Match found (ID): {node_id} -> {node_data}")
                found = True
                
        # Check content/aliases if available
        # (spec_graph nodes usually just have 'type' and 'source')
        # But let's see if metadata has anything helpful
    
    if not found:
        print("❌ No matches found for targets in Graph Nodes.")

if __name__ == "__main__":
    check_graph()
