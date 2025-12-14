"""
HybridRAG - Unified Search Engine for Specification Documents

Combines three search methods:
1. Embedding Search (semantic similarity)
2. BM25 Search (keyword matching)
3. Graph Traversal (relationship-based)

Features:
- RRF (Reciprocal Rank Fusion) for score combination
- ASCII visualization for debugging
- Integration with SpecGraph for context expansion

Zero-dependency (stdlib only).
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Callable, Any
from datetime import datetime

# Import config for DEBUG_MODE
try:
    import config
except ImportError:
    class config:
        DEBUG_MODE = False


@dataclass
class SearchResult:
    """A unified search result."""
    id: str
    score: float
    content: str
    source_file: str
    chunk_type: str
    category: str = "unknown"  # Added for compatibility with SmartRAG
    metadata: Dict = field(default_factory=dict)

    # Source tracking for visualization
    sources: Dict[str, float] = field(default_factory=dict)  # {"embedding": 0.8, "bm25": 0.6}

    # Phase A: Distance from origin node (for graph traversal)
    distance: int = 0  # 0 = direct match, 1+ = hops away


class HybridRAG:
    """
    Unified search engine combining Embedding + BM25 + Graph.
    
    Usage:
        hybrid = HybridRAG(rag_db, graph_lite, spec_graph)
        results = hybrid.search("TLP header format")
    """
    
    def __init__(self, rag_db=None, graph_lite=None, spec_graph=None):
        """
        Initialize HybridRAG.
        
        Args:
            rag_db: RAGDatabase instance for embedding search
            graph_lite: GraphLite instance for hybrid/BM25 search
            spec_graph: SpecGraph instance for relationship traversal
        """
        self.rag_db = rag_db
        self.graph_lite = graph_lite
        self.spec_graph = spec_graph
        
        # Weights for RRF
        self.alpha_embedding = 0.4
        self.alpha_bm25 = 0.3
        self.alpha_graph = 0.3
        
        # RRF constant
        self.rrf_k = 60
    
    def search(self, query: str, limit: int = 10,
               use_embedding: bool = True,
               use_bm25: bool = True,
               use_graph: bool = True,
               graph_hops: int = 2) -> List[SearchResult]:
        """
        Perform hybrid search combining all methods.
        
        Args:
            query: Search query
            limit: Maximum results
            use_embedding: Enable embedding search
            use_bm25: Enable BM25 search
            use_graph: Enable graph traversal
            graph_hops: Depth for graph traversal
            
        Returns:
            List of SearchResult objects
        """
        # Collect results from each method
        embedding_results = []
        bm25_results = []
        graph_results = []
        
        # 1. Embedding Search (via rag_db)
        if use_embedding and self.rag_db:
            try:
                raw_results = self.rag_db.search(query, limit=limit * 2)
                embedding_results = self._convert_rag_results(raw_results, "embedding")
            except Exception as e:
                if config.DEBUG_MODE:
                    print(f"[HybridRAG] Embedding search failed: {e}")
        
        # 2. BM25 Search (via graph_lite)
        if use_bm25 and self.graph_lite:
            try:
                raw_results = self.graph_lite.bm25_search(query, limit=limit * 2)
                bm25_results = self._convert_graph_results(raw_results, "bm25")
            except Exception as e:
                if config.DEBUG_MODE:
                    print(f"[HybridRAG] BM25 search failed: {e}")
        
        # 3. Graph Traversal (via spec_graph)
        if use_graph and self.spec_graph:
            try:
                # First find initial matches via embedding
                if embedding_results:
                    top_id = embedding_results[0].id
                    # Find related via graph
                    related = self.spec_graph.traverse_related(
                        f"spec_{top_id}", hops=graph_hops
                    )
                    graph_results = self._convert_graph_traversal(related)
            except Exception as e:
                if config.DEBUG_MODE:
                    print(f"[HybridRAG] Graph traversal failed: {e}")
        
        # 4. RRF Fusion
        fused_results = self._rrf_fusion(
            embedding_results, bm25_results, graph_results
        )
        
        # 5. Visualization (DEBUG mode)
        if config.DEBUG_MODE:
            self._print_search_viz(
                query=query,
                embedding_results=embedding_results,
                bm25_results=bm25_results,
                graph_results=graph_results,
                final_results=fused_results[:limit]
            )
        
        return fused_results[:limit]
    
    def _convert_rag_results(self, results: List, source: str) -> List[SearchResult]:
        """Convert RAG search results to SearchResult format."""
        converted = []
        for score, chunk in results:
            converted.append(SearchResult(
                id=chunk.id,
                score=score,
                content=chunk.content[:500],
                source_file=chunk.source_file,
                chunk_type=chunk.chunk_type,
                category=getattr(chunk, 'category', 'unknown'),
                metadata=chunk.metadata,
                sources={source: score}
            ))
        return converted
    
    def _convert_graph_results(self, results: List, source: str) -> List[SearchResult]:
        """Convert GraphLite search results to SearchResult format."""
        converted = []
        for score, node in results:
            converted.append(SearchResult(
                id=node.id,
                score=score,
                content=node.data.get("content", node.data.get("description", ""))[:500],
                source_file=node.data.get("source_file", ""),
                chunk_type=node.type,
                category="memory",  # GraphLite nodes are typically memories
                metadata=node.data,
                sources={source: score}
            ))
        return converted
    
    def _convert_graph_traversal(self, related: List[Tuple]) -> List[SearchResult]:
        """Convert graph traversal results to SearchResult format."""
        converted = []
        for node_id, distance, path in related:
            node = self.spec_graph.nodes.get(node_id)
            if not node:
                continue
            
            # Score decreases with distance
            score = 1.0 / (distance + 1)
            
            converted.append(SearchResult(
                id=node.id,
                score=score,
                content=node.content_preview,
                source_file=node.metadata.get("source_file", ""),
                chunk_type=node.node_type,
                category="spec",  # SpecGraph nodes are spec
                metadata={"path": path, "distance": distance},
                sources={"graph": score},
                distance=distance  # Phase A: Set distance field
            ))
        return converted
    
    def _rrf_fusion(self, embedding_results: List[SearchResult],
                    bm25_results: List[SearchResult],
                    graph_results: List[SearchResult]) -> List[SearchResult]:
        """
        Combine results using Reciprocal Rank Fusion.
        
        RRF score = sum(weight * 1/(k + rank)) for each ranking
        """
        result_scores: Dict[str, Dict] = {}
        
        # Process embedding results
        for rank, result in enumerate(embedding_results):
            rrf_score = self.alpha_embedding * (1.0 / (self.rrf_k + rank + 1))
            if result.id not in result_scores:
                result_scores[result.id] = {"result": result, "score": 0, "sources": {}}
            result_scores[result.id]["score"] += rrf_score
            result_scores[result.id]["sources"]["embedding"] = result.score
        
        # Process BM25 results
        for rank, result in enumerate(bm25_results):
            rrf_score = self.alpha_bm25 * (1.0 / (self.rrf_k + rank + 1))
            if result.id not in result_scores:
                result_scores[result.id] = {"result": result, "score": 0, "sources": {}}
            result_scores[result.id]["score"] += rrf_score
            result_scores[result.id]["sources"]["bm25"] = result.score
        
        # Process graph results
        for rank, result in enumerate(graph_results):
            rrf_score = self.alpha_graph * (1.0 / (self.rrf_k + rank + 1))
            if result.id not in result_scores:
                result_scores[result.id] = {"result": result, "score": 0, "sources": {}}
            result_scores[result.id]["score"] += rrf_score
            result_scores[result.id]["sources"]["graph"] = result.score

        # Create final results with distance-weighted scoring (Phase A)
        final_results = []
        for data in result_scores.values():
            result = data["result"]
            base_score = data["score"]

            # Apply distance penalty if available
            if result.distance > 0:
                # distance_penalty = 1.0 / (1 + distance * 0.5)
                # Examples:
                # - distance=0: penalty=1.0 (no change)
                # - distance=1: penalty=0.67 (33% reduction)
                # - distance=2: penalty=0.5 (50% reduction)
                # - distance=3: penalty=0.4 (60% reduction)
                distance_penalty = 1.0 / (1.0 + result.distance * 0.5)
                result.score = base_score * distance_penalty
            else:
                result.score = base_score

            result.sources = data["sources"]
            final_results.append(result)
        
        # Sort by score
        final_results.sort(key=lambda x: x.score, reverse=True)
        return final_results
    
    def _print_search_viz(self, query: str, 
                          embedding_results: List[SearchResult],
                          bm25_results: List[SearchResult],
                          graph_results: List[SearchResult],
                          final_results: List[SearchResult]):
        """Print detailed step-by-step ASCII visualization of hybrid search."""
        
        # Helper to print candidate list
        def print_candidates(name: str, results: List[SearchResult]):
            print(f"│  [{name}] Found {len(results)} candidates:")
            if not results:
                print(f"│     (None)")
            for i, r in enumerate(results[:3]):
                content = r.content.replace('\n', ' ')[:60]
                # Format: [Score] (ID) Content...
                print(f"│     {i+1}. [{r.score:.3f}] ({r.id}) {content}...")
            print(f"│")

        print(f"\n┌{'─'*70}┐")
        print(f"│  [HybridRAG] Process for: \"{query[:45]}\"{'':>{23-min(len(query), 45)}}│")
        print(f"├{'─'*70}┤")
        
        # Step A: Embedding
        print_candidates("Step A: Embedding", embedding_results)
        
        # Step B: BM25
        print_candidates("Step B: BM25", bm25_results)
        
        # Step C: Graph
        print_candidates("Step C: Graph", graph_results)
        
        print(f"├{'─'*70}┤")
        print(f"│  [Fusion] RRF Combined Results ({len(final_results)} total)                     │")
        print(f"│  Weights: Emb={self.alpha_embedding}, BM25={self.alpha_bm25}, Graph={self.alpha_graph}                  │")
        print(f"├{'─'*70}┤")
        
        # Final Results
        for i, result in enumerate(final_results[:5]):
            content = result.content[:60].replace('\n', ' ')
            sources = []
            if "embedding" in result.sources: sources.append("Emb")
            if "bm25" in result.sources: sources.append("BM25")
            if "graph" in result.sources: sources.append("Graph")
            source_str = "/".join(sources)
            
            print(f"│  {i+1}. [Score: {result.score:.4f}] {source_str:<12}                         │")
            print(f"│      {content:<64}│")
            print(f"│      File: {result.source_file.split('/')[-1]:<58}│")
            
        print(f"└{'─'*70}┘\n")


# Singleton instance
_hybrid_rag_instance = None

def get_hybrid_rag() -> HybridRAG:
    """Get or create the singleton HybridRAG instance with all components."""
    global _hybrid_rag_instance

    if _hybrid_rag_instance is None:
        # Import dependencies
        from rag_db import get_rag_db
        try:
            from graph_lite import get_graph_lite
        except ImportError:
            get_graph_lite = lambda: None

        try:
            from spec_graph import get_spec_graph
        except ImportError:
            get_spec_graph = lambda: None

        # Initialize with all available components
        rag_db = get_rag_db()
        graph_lite = get_graph_lite()
        spec_graph = get_spec_graph()

        _hybrid_rag_instance = HybridRAG(rag_db, graph_lite, spec_graph)

    return _hybrid_rag_instance

# Convenience function
def create_hybrid_rag(rag_db=None, graph_lite=None, spec_graph=None) -> HybridRAG:
    """Create a HybridRAG instance with optional components."""
    return HybridRAG(rag_db, graph_lite, spec_graph)
