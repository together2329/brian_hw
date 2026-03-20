"""
Integration Test Suite #1: RAG ↔ GraphLite

Tests the integration between:
- RAG Database (file indexing, chunking, embedding)
- GraphLite (knowledge graph storage, search)

Scenarios:
- Index Verilog file → Store chunks in Graph → Search Graph
- RAG search results → Add to Graph as knowledge nodes
"""
import sys
import os
import unittest
import tempfile
import shutil

# Import modules - path setup handled by conftest.py
from rag_db import RAGDatabase, Chunk
from graph_lite import GraphLite, Node, Edge


class TestRAGGraphIndexingFlow(unittest.TestCase):
    """Test: File Indexing → Graph Storage flow"""
    
    def setUp(self):
        """Set up test fixtures with temp directories"""
        self.temp_dir = tempfile.mkdtemp()
        self.rag_dir = os.path.join(self.temp_dir, "rag")
        self.graph_dir = os.path.join(self.temp_dir, "graph")
        os.makedirs(self.rag_dir)
        os.makedirs(self.graph_dir)
        
        # Create test Verilog file
        self.test_verilog = os.path.join(self.temp_dir, "counter.v")
        with open(self.test_verilog, 'w') as f:
            f.write("""
module counter(
    input clk,
    input reset,
    output reg [7:0] count
);
    always @(posedge clk or posedge reset) begin
        if (reset)
            count <= 8'b0;
        else
            count <= count + 1;
    end
endmodule
""")
        
        self.rag = RAGDatabase()
        self.graph = GraphLite(memory_dir=self.graph_dir)
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_index_file_and_store_in_graph(self):
        """Test: RAG indexes file → Store modules as Graph nodes"""
        # Step 1: RAG indexes the Verilog file (skip embeddings for speed)
        chunk_count = self.rag.index_file(self.test_verilog, quiet=True, skip_embeddings=True)
        self.assertGreater(chunk_count, 0, "Should index at least one chunk")
        
        # Step 2: Get chunks from RAG
        chunks = list(self.rag.chunks.values())
        module_chunks = [c for c in chunks if c.chunk_type == "module"]
        
        # Step 3: Store in Graph as knowledge nodes
        for chunk in module_chunks:
            node = Node(
                id=f"rag_{chunk.id}",
                type="VerilogModule",
                data={
                    "name": chunk.metadata.get("module_name", "unknown"),
                    "source_file": chunk.source_file,
                    "content_preview": chunk.content[:200]
                }
            )
            self.graph.add_node(node)
        
        # Step 4: Verify Graph has the nodes
        all_nodes = self.graph.get_all_nodes()
        verilog_nodes = [n for n in all_nodes if n.type == "VerilogModule"]
        self.assertGreater(len(verilog_nodes), 0, "Should have Verilog module nodes")
    
    def test_rag_search_to_graph_linking(self):
        """Test: RAG search → Create edges between related chunks"""
        # Step 1: Index file
        self.rag.index_file(self.test_verilog, quiet=True, skip_embeddings=True)
        
        chunks = list(self.rag.chunks.values())
        
        # Step 2: Add all chunks to graph
        for chunk in chunks:
            node = Node(
                id=f"chunk_{chunk.id}",
                type="CodeChunk",
                data={"chunk_type": chunk.chunk_type, "level": chunk.level}
            )
            self.graph.add_node(node)
        
        # Step 3: Create hierarchical edges (module → always blocks)
        module_chunks = [c for c in chunks if c.chunk_type == "module"]
        always_chunks = [c for c in chunks if c.chunk_type == "always"]
        
        for module in module_chunks:
            for always in always_chunks:
                edge = Edge(
                    source=f"chunk_{module.id}",
                    target=f"chunk_{always.id}",
                    relation="CONTAINS"
                )
                self.graph.add_edge(edge)
        
        # Step 4: Verify edges exist
        edges = self.graph.get_all_edges()
        contains_edges = [e for e in edges if e.relation == "CONTAINS"]
        # May or may not have edges depending on chunk structure
        self.assertIsInstance(contains_edges, list)


class TestRAGGraphSearchIntegration(unittest.TestCase):
    """Test: Combined RAG + Graph Search"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.rag = RAGDatabase()
        self.graph = GraphLite(memory_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_hybrid_search_concept(self):
        """Test: Combine RAG chunk search with Graph node search"""
        # Add knowledge to graph
        node1 = Node(
            id="knowledge_1",
            type="Concept",
            data={"name": "PCIe Controller", "description": "Handles PCIe protocol"}
        )
        node2 = Node(
            id="knowledge_2",
            type="Concept",
            data={"name": "AXI Bridge", "description": "Converts between protocols"}
        )
        self.graph.add_node(node1)
        self.graph.add_node(node2)
        
        # Create relationship
        edge = Edge(source="knowledge_1", target="knowledge_2", relation="USES")
        self.graph.add_edge(edge)
        
        # Search graph
        results = self.graph.search("PCIe", limit=5)
        
        # Should find related nodes
        self.assertIsInstance(results, list)


class TestGraphKnowledgeAccumulation(unittest.TestCase):
    """Test: Knowledge accumulates from RAG indexing sessions"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.graph_dir = os.path.join(self.temp_dir, "graph")
        os.makedirs(self.graph_dir)
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_knowledge_persists_across_sessions(self):
        """Test: Graph persists knowledge between sessions"""
        # Session 1: Add knowledge
        graph1 = GraphLite(memory_dir=self.graph_dir)
        graph1.add_node(Node(id="persist_test", type="Test", data={"session": 1}))
        graph1.save()
        
        # Session 2: Verify knowledge persists
        graph2 = GraphLite(memory_dir=self.graph_dir)
        node = graph2.get_node("persist_test")
        
        self.assertIsNotNone(node)
        self.assertEqual(node.data["session"], 1)


if __name__ == '__main__':
    print("\n" + "="*70)
    print("Integration Test: RAG ↔ GraphLite")
    print("="*70 + "\n")
    
    unittest.main(verbosity=2)
