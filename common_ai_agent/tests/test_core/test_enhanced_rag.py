"""
Unit tests for Enhanced Spec RAG modules:
- SpecGraph
- HybridRAG
- Markdown Chunking

Run: python3 -m pytest tests/test_core/test_enhanced_rag.py -v
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'core'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))


class TestSpecGraph(unittest.TestCase):
    """Test: SpecGraph module"""

    def test_add_node(self):
        """Test adding nodes to graph"""
        from spec_graph import SpecGraph, SpecNode
        
        graph = SpecGraph()
        node = SpecNode(
            id="s1",
            node_type="section_h1",
            title="Test Section",
            section_id="1",
            level=1,
            content_preview="Test content..."
        )
        graph.add_node(node)
        
        self.assertEqual(len(graph.nodes), 1)
        self.assertEqual(graph.nodes["s1"].title, "Test Section")

    def test_add_edge(self):
        """Test adding edges between nodes"""
        from spec_graph import SpecGraph, SpecNode
        
        graph = SpecGraph()
        graph.add_node(SpecNode(id="s1", node_type="section_h1", title="Parent", section_id="1", level=1, content_preview=""))
        graph.add_node(SpecNode(id="s2", node_type="section_h2", title="Child", section_id="1.1", level=2, content_preview=""))
        
        graph.add_edge("s1", "s2", "hierarchy")
        
        self.assertEqual(len(graph.edges), 1)
        self.assertEqual(graph.edges[0].edge_type, "hierarchy")

    def test_traverse_related(self):
        """Test graph traversal"""
        from spec_graph import SpecGraph, SpecNode
        
        graph = SpecGraph()
        graph.add_node(SpecNode(id="s1", node_type="section_h1", title="A", section_id="1", level=1, content_preview=""))
        graph.add_node(SpecNode(id="s2", node_type="section_h2", title="B", section_id="1.1", level=2, content_preview=""))
        graph.add_node(SpecNode(id="s3", node_type="section_h3", title="C", section_id="1.1.1", level=3, content_preview=""))
        
        graph.add_edge("s1", "s2", "hierarchy")
        graph.add_edge("s2", "s3", "hierarchy")
        
        related = graph.traverse_related("s1", hops=2)
        
        self.assertGreaterEqual(len(related), 1)
        # Should find s2 at 1 hop
        hop1_nodes = [r[0] for r in related if r[1] == 1]
        self.assertIn("s2", hop1_nodes)

    def test_get_stats(self):
        """Test graph statistics"""
        from spec_graph import SpecGraph, SpecNode
        
        graph = SpecGraph()
        graph.add_node(SpecNode(id="s1", node_type="section_h1", title="A", section_id="1", level=1, content_preview=""))
        graph.add_node(SpecNode(id="t1", node_type="table", title="Table 1", section_id="", level=4, content_preview=""))
        
        stats = graph.get_stats()
        
        self.assertEqual(stats["total_nodes"], 2)
        self.assertEqual(stats["sections"], 1)
        self.assertEqual(stats["tables"], 1)

    def test_visualize_ascii(self):
        """Test ASCII visualization"""
        from spec_graph import SpecGraph, SpecNode
        
        graph = SpecGraph()
        graph.add_node(SpecNode(id="s1", node_type="section_h1", title="Test", section_id="1", level=1, content_preview=""))
        
        viz = graph.visualize_ascii()
        
        self.assertIn("SpecGraph", viz)
        self.assertIn("§1 Test", viz)


class TestHybridRAG(unittest.TestCase):
    """Test: HybridRAG module"""

    def test_init(self):
        """Test HybridRAG initialization"""
        from hybrid_rag import HybridRAG
        
        hybrid = HybridRAG()
        
        self.assertIsNone(hybrid.rag_db)
        self.assertIsNone(hybrid.graph_lite)
        self.assertIsNone(hybrid.spec_graph)

    def test_rrf_fusion(self):
        """Test RRF fusion logic"""
        from hybrid_rag import HybridRAG, SearchResult
        
        hybrid = HybridRAG()
        
        # Create test results
        emb_results = [
            SearchResult(id="a", score=0.9, content="A", source_file="", chunk_type="section"),
            SearchResult(id="b", score=0.7, content="B", source_file="", chunk_type="section"),
        ]
        bm25_results = [
            SearchResult(id="b", score=0.85, content="B", source_file="", chunk_type="section"),
            SearchResult(id="c", score=0.6, content="C", source_file="", chunk_type="section"),
        ]
        
        fused = hybrid._rrf_fusion(emb_results, bm25_results, [])
        
        # "b" should rank high because it appears in both
        self.assertGreater(len(fused), 0)
        ids = [r.id for r in fused]
        self.assertIn("b", ids)

    def test_search_result_sources(self):
        """Test source tracking in search results"""
        from hybrid_rag import SearchResult
        
        result = SearchResult(
            id="test",
            score=0.8,
            content="Test content",
            source_file="test.md",
            chunk_type="section",
            sources={"embedding": 0.8, "bm25": 0.6}
        )
        
        self.assertIn("embedding", result.sources)
        self.assertIn("bm25", result.sources)


class TestMarkdownChunking(unittest.TestCase):
    """Test: Markdown hierarchical chunking"""

    def test_section_extraction_pattern(self):
        """Test section header pattern matching"""
        import re
        
        content = """
# Main Title

## Section 2.1

Some content here.

### Section 2.1.1

More content.
"""
        pattern = re.compile(r'^(#{1,3})\s+(.+)$', re.MULTILINE)
        matches = list(pattern.finditer(content))
        
        self.assertEqual(len(matches), 3)
        self.assertEqual(matches[0].group(2), "Main Title")
        self.assertEqual(matches[1].group(2), "Section 2.1")

    def test_table_extraction_pattern(self):
        """Test table pattern matching"""
        import re
        
        content = """
| Field | Size |
|-------|------|
| Fmt   | 2    |
| Type  | 5    |
"""
        pattern = re.compile(r'(\|[^\n]+\|\n)+', re.MULTILINE)
        matches = list(pattern.finditer(content))
        
        self.assertEqual(len(matches), 1)

    def test_code_block_pattern(self):
        """Test code block pattern matching"""
        import re
        
        content = """
Some text.

```verilog
module test();
endmodule
```

More text.
"""
        pattern = re.compile(r'```(\w*)\n(.*?)```', re.DOTALL)
        matches = list(pattern.finditer(content))
        
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].group(1), "verilog")

    def test_chunk_splitting(self):
        """Test splitting of long sections"""
        from rag_db import RAGDatabase
        
        db = RAGDatabase()
        db._ensure_initialized()  # Ensure RAG dir exists
        
        # Create long content (> 1500 chars)
        # 1600 chars: should be split into 2 chunks (1500 + remainder)
        long_text = "A" * 1600
        content = f"# Long Section\n\n{long_text}"
        
        chunks = db.chunk_markdown_hierarchical(content, "test_file.md")
        
        # Filter for section chunks only (ignore potential document chunk if hierarchy fails, but here it should pass)
        section_chunks = [c for c in chunks if c.chunk_type.startswith("section")]
        
        # Verify splitting
        # Chunk 1: 0-1500 chars
        # Chunk 2: 1300-1600 chars (step 1300)
        self.assertGreaterEqual(len(section_chunks), 2)
        self.assertEqual(len(section_chunks[0].content), 1500)
        self.assertEqual(len(section_chunks[1].content), 300) # 1600 - 1300 = 300
        
        # Verify metadata
        self.assertIn("(Part 1/2)", section_chunks[0].metadata['summary'])
        self.assertIn("(Part 2/2)", section_chunks[1].metadata['summary'])

class TestEmbeddingAutoDetect(unittest.TestCase):
    """Test: Auto-detection of embedding dimension"""
    
    def test_auto_detect(self):
        """Test calling get_embedding_dimension"""
        import sys
        import os
        
        # Mock config to force auto-detection
        import config
        original_dim = config.EMBEDDING_DIMENSION
        config.EMBEDDING_DIMENSION = None
        
        from llm_client import get_embedding_dimension
        
        try:
            # This will try to call API. 
            # If no API key, it might fail, but let's see if it handles failure gracefully (return 1536)
            # OR if we have keys, it returns actual dim.
            dim = get_embedding_dimension()
            self.assertIsInstance(dim, int)
            self.assertGreater(dim, 0)
        finally:
            config.EMBEDDING_DIMENSION = original_dim




if __name__ == "__main__":
    unittest.main()
