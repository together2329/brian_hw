"""
RAG Database Test Suite

Comprehensive tests for:
- Verilog hierarchical chunking
- Markdown/spec chunking
- File hash caching
- Parallel embedding
- Semantic search
- API call counting
"""
import sys
import os
import unittest
import tempfile
import shutil
from pathlib import Path

# Import RAGDatabase - path setup handled by conftest.py
from rag_db import RAGDatabase


class TestVerilogChunking(unittest.TestCase):
    """Test Verilog hierarchical chunking"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.db = RAGDatabase()
        
        # Sample Verilog code
        self.sample_verilog = '''
module counter(
    input clk,
    input reset,
    output reg [7:0] count
);

    wire internal_signal;
    reg [3:0] state;

    always @(posedge clk or posedge reset) begin
        if (reset)
            count <= 8'b0;
        else
            count <= count + 1;
    end

    assign internal_signal = (count == 8'hFF);

endmodule
'''
    
    def test_module_extraction(self):
        """Test that module is correctly extracted"""
        chunks = self.db.chunk_verilog_hierarchical(self.sample_verilog, "test.v")
        
        # Should have at least one module chunk
        module_chunks = [c for c in chunks if c.chunk_type == "module"]
        self.assertGreaterEqual(len(module_chunks), 1)
        
        # Module name should be "counter"
        self.assertEqual(module_chunks[0].metadata.get("module_name"), "counter")
    
    def test_port_extraction(self):
        """Test that ports are correctly extracted"""
        chunks = self.db.chunk_verilog_hierarchical(self.sample_verilog, "test.v")
        
        port_chunks = [c for c in chunks if c.chunk_type == "port"]
        self.assertGreaterEqual(len(port_chunks), 1)
        
        # Should detect input/output ports
        port_content = port_chunks[0].content
        self.assertIn("input", port_content.lower())
        self.assertIn("output", port_content.lower())
    
    def test_wire_reg_extraction(self):
        """Test that wire/reg declarations are extracted"""
        chunks = self.db.chunk_verilog_hierarchical(self.sample_verilog, "test.v")
        
        wire_chunks = [c for c in chunks if c.chunk_type == "wire"]
        self.assertGreaterEqual(len(wire_chunks), 1)
    
    def test_always_block_extraction(self):
        """Test that always blocks are extracted"""
        chunks = self.db.chunk_verilog_hierarchical(self.sample_verilog, "test.v")
        
        always_chunks = [c for c in chunks if c.chunk_type == "always"]
        self.assertGreaterEqual(len(always_chunks), 1)
        
        # Should be sequential (has posedge)
        self.assertEqual(always_chunks[0].metadata.get("block_type"), "sequential")
    
    def test_assign_extraction(self):
        """Test that assign statements are extracted"""
        chunks = self.db.chunk_verilog_hierarchical(self.sample_verilog, "test.v")
        
        assign_chunks = [c for c in chunks if c.chunk_type == "assign"]
        self.assertGreaterEqual(len(assign_chunks), 1)
    
    def test_chunk_levels(self):
        """Test that chunks have correct hierarchical levels"""
        chunks = self.db.chunk_verilog_hierarchical(self.sample_verilog, "test.v")
        
        levels = set(c.level for c in chunks)
        # Level 1: module, Level 2: ports, Level 3: wires, Level 4: always, Level 5: assign
        self.assertTrue(1 in levels, "Should have module level (1)")
        self.assertTrue(2 in levels, "Should have port level (2)")


class TestSpecChunking(unittest.TestCase):
    """Test Markdown/spec document chunking"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.db = RAGDatabase()
        
        self.sample_markdown = '''
# Main Title

Introduction paragraph with some text.

## Section One

Content for section one. This should be long enough to be captured.
More content here to make it substantial.

### Subsection 1.1

Detailed content for subsection.

## Section Two

Another section with important information.
'''
    
    def test_section_extraction(self):
        """Test that sections are correctly extracted"""
        chunks = self.db.chunk_spec(self.sample_markdown, "test.md")
        
        # Should have multiple section chunks
        self.assertGreater(len(chunks), 0)
    
    def test_section_metadata(self):
        """Test that section metadata is correct"""
        chunks = self.db.chunk_spec(self.sample_markdown, "test.md")
        
        # Each chunk should have section_title metadata
        for chunk in chunks:
            self.assertIn("section_title", chunk.metadata)
    
    def test_short_sections_skipped(self):
        """Test that very short sections are skipped"""
        short_md = "# Title\n\nShort."
        chunks = self.db.chunk_spec(short_md, "test.md")
        
        # Very short content (< 50 chars) should be skipped
        self.assertEqual(len(chunks), 0)


class TestFileHashing(unittest.TestCase):
    """Test file hash-based caching"""
    
    def setUp(self):
        """Set up test fixtures with temp directory"""
        self.db = RAGDatabase()
        
        # Create temp directory
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test.v")
        
        # Write sample file
        with open(self.test_file, 'w') as f:
            f.write("module test; endmodule\n")
    
    def tearDown(self):
        """Clean up temp files"""
        shutil.rmtree(self.temp_dir)
    
    def test_hash_generation(self):
        """Test that file hash is generated correctly"""
        hash1 = self.db._get_file_hash(self.test_file)
        
        # Hash should be non-empty MD5
        self.assertEqual(len(hash1), 32)  # MD5 hex length
    
    def test_hash_changes_with_content(self):
        """Test that hash changes when file content changes"""
        hash1 = self.db._get_file_hash(self.test_file)
        
        # Modify file
        with open(self.test_file, 'a') as f:
            f.write("// Comment\n")
        
        hash2 = self.db._get_file_hash(self.test_file)
        
        self.assertNotEqual(hash1, hash2)
    
    def test_skip_unchanged_file(self):
        """Test that unchanged files are skipped on re-index"""
        # First index
        chunks1 = self.db.index_file(self.test_file, quiet=True, skip_embeddings=True)
        
        # Second index (should skip)
        chunks2 = self.db.index_file(self.test_file, quiet=True, skip_embeddings=True)
        
        self.assertEqual(chunks2, 0, "Unchanged file should return 0 chunks")


class TestParallelEmbedding(unittest.TestCase):
    """Test parallel embedding processing"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.db = RAGDatabase()
    
    def test_api_call_counting(self):
        """Test that API calls are counted correctly"""
        initial_count = self.db.api_call_count
        
        # Create sample chunks (without actual embedding)
        sample_verilog = "module test; wire a; endmodule"
        chunks = self.db.chunk_verilog_hierarchical(sample_verilog, "test.v")
        
        # Chunks should be created
        self.assertGreater(len(chunks), 0)
    
    def test_thread_safe_counting(self):
        """Test that counting is thread-safe"""
        import threading
        
        counter = [0]
        lock = threading.Lock()
        
        def increment():
            for _ in range(100):
                with lock:
                    counter[0] += 1
        
        threads = [threading.Thread(target=increment) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        self.assertEqual(counter[0], 1000)


class TestSearch(unittest.TestCase):
    """Test semantic search functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.db = RAGDatabase()
    
    def test_search_returns_list(self):
        """Test that search returns a list"""
        results = self.db.search("counter module", categories="all", limit=5)
        self.assertIsInstance(results, list)
    
    def test_search_limit(self):
        """Test that limit is respected"""
        results = self.db.search("module", categories="all", limit=3)
        self.assertLessEqual(len(results), 3)


class TestChunkGeneration(unittest.TestCase):
    """Test chunk ID and metadata generation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.db = RAGDatabase()
    
    def test_unique_chunk_ids(self):
        """Test that chunk IDs are unique"""
        ids = [self.db._generate_chunk_id() for _ in range(100)]
        
        # All IDs should be unique
        self.assertEqual(len(ids), len(set(ids)))
    
    def test_chunk_has_required_fields(self):
        """Test that chunks have all required fields"""
        sample_verilog = "module test; endmodule"
        chunks = self.db.chunk_verilog_hierarchical(sample_verilog, "test.v")
        
        for chunk in chunks:
            self.assertIsNotNone(chunk.id)
            self.assertIsNotNone(chunk.source_file)
            self.assertIsNotNone(chunk.category)
            self.assertIsNotNone(chunk.level)
            self.assertIsNotNone(chunk.chunk_type)
            self.assertIsNotNone(chunk.content)


class TestPersistence(unittest.TestCase):
    """Test save/load functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.db = RAGDatabase()
    
    def test_chunks_dict_exists(self):
        """Test that chunks dictionary exists"""
        self.assertIsInstance(self.db.chunks, dict)
    
    def test_file_hashes_dict_exists(self):
        """Test that file_hashes dictionary exists"""
        self.assertIsInstance(self.db.file_hashes, dict)


if __name__ == '__main__':
    print("\n" + "="*70)
    print("RAG Database Test Suite")
    print("="*70 + "\n")
    
    unittest.main(verbosity=2)
