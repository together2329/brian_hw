"""
Performance & Benchmark Test Suite

Tests execution performance of major components:
- RAG indexing speed
- Graph search latency
- Memory operations
- SubAgent response time

Uses pytest-benchmark for accurate measurements.
Run with: pytest tests/test_performance.py -v --benchmark-only
"""
import sys
import os
import unittest
import tempfile
import shutil
import time

# Import modules - path setup handled by conftest.py
from rag_db import RAGDatabase
from graph_lite import GraphLite, Node, Edge, SimpleBM25
from memory import MemorySystem
from procedural_memory import ProceduralMemory, Action


class TestRAGPerformance(unittest.TestCase):
    """Benchmark RAG operations"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.rag = RAGDatabase()
        
        # Create test Verilog file
        self.test_file = os.path.join(self.temp_dir, "test_module.v")
        with open(self.test_file, 'w') as f:
            f.write("""
module test_counter(
    input clk,
    input reset,
    output reg [7:0] count
);
    always @(posedge clk) begin
        if (reset) count <= 0;
        else count <= count + 1;
    end
endmodule

module test_fsm(
    input clk,
    input reset,
    input start,
    output reg done
);
    reg [1:0] state;
    localparam IDLE = 0, RUN = 1, DONE = 2;
    
    always @(posedge clk or posedge reset) begin
        if (reset) state <= IDLE;
        else case(state)
            IDLE: if (start) state <= RUN;
            RUN: state <= DONE;
            DONE: state <= IDLE;
        endcase
    end
    
    assign done = (state == DONE);
endmodule
""")
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_chunking_speed(self):
        """Test Verilog chunking performance"""
        start = time.perf_counter()
        
        # Chunk the file (without embeddings for speed test)
        chunk_count = self.rag.index_file(self.test_file, quiet=True, skip_embeddings=True)
        
        elapsed = time.perf_counter() - start
        
        self.assertGreater(chunk_count, 0)
        self.assertLess(elapsed, 5.0, f"Chunking took too long: {elapsed:.3f}s")
        
        print(f"\n  Chunking: {chunk_count} chunks in {elapsed*1000:.1f}ms")


class TestGraphPerformance(unittest.TestCase):
    """Benchmark GraphLite operations"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.graph = GraphLite(memory_dir=self.temp_dir)
        
        # Add many nodes for testing
        for i in range(100):
            node = Node(
                id=f"node_{i}",
                type="TestNode",
                data={"index": i, "name": f"Test Node {i}", "value": i * 10}
            )
            self.graph.add_node(node)
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_node_lookup_speed(self):
        """Test node lookup performance"""
        start = time.perf_counter()
        
        # Lookup 100 nodes
        for i in range(100):
            node = self.graph.get_node(f"node_{i}")
        
        elapsed = time.perf_counter() - start
        
        self.assertLess(elapsed, 0.1, f"Lookup too slow: {elapsed*1000:.1f}ms for 100 lookups")
        print(f"\n  Node lookup: 100 lookups in {elapsed*1000:.1f}ms ({elapsed*10:.2f}ms each)")
    
    def test_bm25_search_speed(self):
        """Test BM25 search performance"""
        bm25 = SimpleBM25()
        
        # Build corpus
        corpus = [f"document {i} about topic {i % 10}" for i in range(100)]
        bm25.fit(corpus)
        
        start = time.perf_counter()
        
        # Run 50 searches
        for i in range(50):
            scores = bm25.get_scores(f"topic {i % 10}")
        
        elapsed = time.perf_counter() - start
        
        self.assertLess(elapsed, 0.5, f"BM25 search too slow: {elapsed*1000:.1f}ms for 50 searches")
        print(f"\n  BM25 search: 50 searches in {elapsed*1000:.1f}ms ({elapsed*20:.2f}ms each)")


class TestMemoryPerformance(unittest.TestCase):
    """Benchmark Memory operations"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.memory = MemorySystem(memory_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_preference_write_speed(self):
        """Test preference write performance"""
        start = time.perf_counter()
        
        # Write 50 preferences
        for i in range(50):
            self.memory.update_preference(f"pref_{i}", f"value_{i}")
        
        elapsed = time.perf_counter() - start
        
        self.assertLess(elapsed, 1.0, f"Preference writes too slow: {elapsed*1000:.1f}ms")
        print(f"\n  Preference writes: 50 writes in {elapsed*1000:.1f}ms")
    
    def test_preference_read_speed(self):
        """Test preference read performance"""
        # Pre-populate
        for i in range(50):
            self.memory.update_preference(f"pref_{i}", f"value_{i}")
        
        start = time.perf_counter()
        
        # Read 100 times
        for i in range(100):
            self.memory.get_preference(f"pref_{i % 50}")
        
        elapsed = time.perf_counter() - start
        
        self.assertLess(elapsed, 0.1, f"Preference reads too slow: {elapsed*1000:.1f}ms")
        print(f"\n  Preference reads: 100 reads in {elapsed*1000:.1f}ms")


class TestProceduralMemoryPerformance(unittest.TestCase):
    """Benchmark ProceduralMemory operations"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.proc_mem = ProceduralMemory(memory_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_trajectory_build_speed(self):
        """Test trajectory build performance"""
        start = time.perf_counter()
        
        # Build 20 trajectories
        for i in range(20):
            actions = [
                Action(tool="read_file", args=f"file_{i}.v", result="success"),
                Action(tool="grep_file", args="pattern", result="found")
            ]
            self.proc_mem.build(
                task_description=f"Task {i}: Debug module",
                actions=actions,
                outcome="success",
                iterations=2
            )
        
        elapsed = time.perf_counter() - start
        
        self.assertLess(elapsed, 1.0, f"Trajectory builds too slow: {elapsed*1000:.1f}ms")
        print(f"\n  Trajectory builds: 20 builds in {elapsed*1000:.1f}ms")
    
    def test_trajectory_retrieve_speed(self):
        """Test trajectory retrieval performance"""
        # Pre-populate
        for i in range(20):
            actions = [Action(tool="test", args="arg", result="ok")]
            self.proc_mem.build(f"Task {i}", actions, "success", 1)
        
        start = time.perf_counter()
        
        # Retrieve 30 times
        for i in range(30):
            results = self.proc_mem.retrieve(f"Task about debugging {i % 5}", limit=3)
        
        elapsed = time.perf_counter() - start
        
        self.assertLess(elapsed, 0.5, f"Retrieval too slow: {elapsed*1000:.1f}ms")
        print(f"\n  Trajectory retrieval: 30 retrievals in {elapsed*1000:.1f}ms")


class TestOverallLatency(unittest.TestCase):
    """Test overall system latency for common operations"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_combined_memory_lookup(self):
        """Test combined memory system lookup"""
        memory = MemorySystem(memory_dir=self.temp_dir)
        proc_mem = ProceduralMemory(memory_dir=self.temp_dir)
        graph = GraphLite(memory_dir=self.temp_dir)
        
        # Pre-populate
        memory.update_preference("style", "clean")
        actions = [Action(tool="test", args="x", result="ok")]
        proc_mem.build("Test task", actions, "success", 1)
        graph.add_node(Node(id="n1", type="T", data={"x": 1}))
        
        start = time.perf_counter()
        
        # Combined lookup (simulating agent preparation)
        for _ in range(10):
            prefs = memory.list_preferences()
            trajs = proc_mem.retrieve("test", limit=2)
            nodes = graph.get_all_nodes()
        
        elapsed = time.perf_counter() - start
        
        self.assertLess(elapsed, 0.5, f"Combined lookup too slow: {elapsed*1000:.1f}ms")
        print(f"\n  Combined lookup: 10 iterations in {elapsed*1000:.1f}ms")


if __name__ == '__main__':
    print("\n" + "="*70)
    print("Performance & Benchmark Tests")
    print("="*70 + "\n")
    
    unittest.main(verbosity=2)
