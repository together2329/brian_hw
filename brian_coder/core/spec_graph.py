"""
Spec Graph - Section Relationship Graph for Specification Documents

Builds a graph of relationships between spec sections:
- Hierarchical: §2.1 → §2.1.1 (parent-child)
- Cross-reference: "See Section 3.2" → §3.2
- Table association: Table 2-3 ← §2

Zero-dependency (stdlib only).
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Set
from datetime import datetime


@dataclass
class SpecNode:
    """A node in the spec graph (section, table, figure)."""
    id: str
    node_type: str  # "section", "table", "figure", "code_block"
    title: str
    section_id: str  # "2.1.1" format
    level: int
    content_preview: str
    parent_id: Optional[str] = None
    metadata: Dict = field(default_factory=dict)


@dataclass  
class SpecEdge:
    """An edge between spec nodes."""
    source_id: str
    target_id: str
    edge_type: str  # "hierarchy", "cross_ref", "contains"
    weight: float = 1.0


class SpecGraph:
    """
    Graph of relationships between specification sections.
    
    Features:
    - Hierarchical relationships (parent/child sections)
    - Cross-references ("See Section X.Y")
    - Table/Figure associations with sections
    - Traversal for related content discovery
    """
    
    def __init__(self):
        self.nodes: Dict[str, SpecNode] = {}
        self.edges: List[SpecEdge] = []
        self._adjacency: Dict[str, List[Tuple[str, str, float]]] = {}  # node_id -> [(target, type, weight)]
    
    def add_node(self, node: SpecNode):
        """Add a node to the graph."""
        self.nodes[node.id] = node
        if node.id not in self._adjacency:
            self._adjacency[node.id] = []
    
    def add_edge(self, source_id: str, target_id: str, edge_type: str, weight: float = 1.0):
        """Add an edge between nodes."""
        if source_id not in self.nodes or target_id not in self.nodes:
            return
        
        edge = SpecEdge(source_id, target_id, edge_type, weight)
        self.edges.append(edge)
        
        # Update adjacency
        if source_id not in self._adjacency:
            self._adjacency[source_id] = []
        self._adjacency[source_id].append((target_id, edge_type, weight))
        
        # Bidirectional for hierarchy
        if edge_type == "hierarchy":
            if target_id not in self._adjacency:
                self._adjacency[target_id] = []
            self._adjacency[target_id].append((source_id, "child_of", weight))
    
    def build_from_chunks(self, chunks: List) -> 'SpecGraph':
        """
        Build graph from RAG chunks.
        
        Args:
            chunks: List of Chunk objects from rag_db.py
            
        Returns:
            self for chaining
        """
        section_map = {}  # section_id -> node_id
        title_map = {}    # title -> node_id (for fast lookup)
        
        # First pass: Create nodes
        for chunk in chunks:
            if chunk.category != "spec":
                continue
                
            node_id = f"spec_{chunk.id}"
            section_id = chunk.metadata.get("section_id", "")
            title = chunk.metadata.get("section_title", chunk.metadata.get("summary", ""))
            
            node = SpecNode(
                id=node_id,
                node_type=chunk.chunk_type,
                title=title,
                section_id=section_id,
                level=chunk.level,
                content_preview=chunk.content[:200],
                metadata=chunk.metadata
            )
            self.add_node(node)
            
            if section_id:
                section_map[section_id] = node_id
            
            # Map title to node_id (prefer sections over others)
            if title:
                if chunk.chunk_type.startswith("section") or title not in title_map:
                    title_map[title] = node_id
        
        # Second pass: Create edges
        for chunk in chunks:
            if chunk.category != "spec":
                continue
                
            node_id = f"spec_{chunk.id}"
            section_id = chunk.metadata.get("section_id", "")
            
            # Hierarchy edges (parent-child)
            if section_id:
                parent_section = self._get_parent_section_id(section_id)
                if parent_section and parent_section in section_map:
                    self.add_edge(section_map[parent_section], node_id, "hierarchy", 1.0)
            
            # Cross-reference edges
            cross_refs = chunk.metadata.get("cross_refs", [])
            for ref in cross_refs:
                if ref in section_map and section_map[ref] != node_id:
                    self.add_edge(node_id, section_map[ref], "cross_ref", 0.8)
            
            # Table/code containment (optimized with title_map)
            parent_section = chunk.metadata.get("parent_section", "") or chunk.metadata.get("parent_h2", "") or chunk.metadata.get("parent_h1", "")
            if parent_section and chunk.chunk_type in ["table", "code_block"]:
                # Use fast lookup instead of iteration
                if parent_section in title_map:
                    self.add_edge(title_map[parent_section], node_id, "contains", 0.9)
        
        return self
    
    def _get_parent_section_id(self, section_id: str) -> Optional[str]:
        """Get parent section ID from child ID (e.g., '2.1.1' -> '2.1')."""
        parts = section_id.split(".")
        if len(parts) > 1:
            return ".".join(parts[:-1])
        return None
    
    def traverse_related(self, node_id: str, hops: int = 2, 
                         edge_types: Optional[Set[str]] = None) -> List[Tuple[str, int, str]]:
        """
        Traverse graph to find related nodes.
        
        Args:
            node_id: Starting node
            hops: Maximum traversal depth
            edge_types: Filter by edge types (None = all)
            
        Returns:
            List of (node_id, distance, relationship_path) tuples
        """
        if node_id not in self.nodes:
            return []
        
        visited = {node_id}
        results = []
        frontier = [(node_id, 0, "")]
        
        while frontier:
            current, depth, path = frontier.pop(0)
            
            if depth > 0:
                results.append((current, depth, path))
            
            if depth >= hops:
                continue
            
            for target, edge_type, weight in self._adjacency.get(current, []):
                if target in visited:
                    continue
                if edge_types and edge_type not in edge_types:
                    continue
                    
                visited.add(target)
                new_path = f"{path}→{edge_type}" if path else edge_type
                frontier.append((target, depth + 1, new_path))
        
        return results
    
    def get_section_path(self, node_id: str) -> str:
        """Get full section path (e.g., '§2.1.1 TLP Header Format')."""
        node = self.nodes.get(node_id)
        if not node:
            return ""
        return f"§{node.section_id} {node.title}" if node.section_id else node.title
    
    def get_stats(self) -> Dict:
        """Get graph statistics."""
        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "sections": len([n for n in self.nodes.values() if n.node_type.startswith("section")]),
            "tables": len([n for n in self.nodes.values() if n.node_type == "table"]),
            "code_blocks": len([n for n in self.nodes.values() if n.node_type == "code_block"]),
            "hierarchy_edges": len([e for e in self.edges if e.edge_type == "hierarchy"]),
            "cross_ref_edges": len([e for e in self.edges if e.edge_type == "cross_ref"]),
        }
    
    def visualize_ascii(self, max_nodes: int = 10) -> str:
        """Generate ASCII visualization of the graph."""
        lines = []
        lines.append("┌" + "─" * 50 + "┐")
        lines.append("│  [SpecGraph] Structure                            │")
        lines.append("├" + "─" * 50 + "┤")
        
        stats = self.get_stats()
        lines.append(f"│  Nodes: {stats['total_nodes']:3} | Edges: {stats['total_edges']:3}                      │")
        lines.append(f"│  Sections: {stats['sections']:2} | Tables: {stats['tables']:2} | Code: {stats['code_blocks']:2}            │")
        lines.append("├" + "─" * 50 + "┤")
        
        # Show section hierarchy
        section_nodes = sorted(
            [n for n in self.nodes.values() if n.node_type.startswith("section")],
            key=lambda x: x.section_id
        )[:max_nodes]
        
        for node in section_nodes:
            indent = "  " * (node.level - 1)
            title = node.title[:30]
            lines.append(f"│  {indent}§{node.section_id} {title:<{40-len(indent)}}│")
        
        lines.append("└" + "─" * 50 + "┘")
        return "\n".join(lines)


# Convenience function
def build_spec_graph_from_chunks(chunks: List) -> SpecGraph:
    """Build a SpecGraph from RAG chunks."""
    graph = SpecGraph()
    return graph.build_from_chunks(chunks)
