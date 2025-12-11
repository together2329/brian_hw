"""
PCIe Spec-to-Code Integration Test

Tests if the AI agent can:
1. Index PCIe spec documents and Verilog code
2. Search for relevant spec information
3. Apply spec knowledge to analyze/improve code
4. Generate code based on spec requirements

Requires: Valid API key in config
"""
import sys
import os
import unittest
import tempfile
import shutil

# Path setup
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src import config


def api_available():
    """Check if API key is configured"""
    return (
        config.API_KEY and 
        config.API_KEY != "your-openai-api-key-here" and
        len(config.API_KEY) > 20
    )


# Project paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PCIE_SPEC_DIR = os.path.join(PROJECT_ROOT, "..", "PCIe")
PCIE_MSG_RECEIVER = os.path.join(PROJECT_ROOT, "..", "pcie_msg_receiver.v")


@unittest.skipUnless(api_available(), "No valid API key configured")
class TestPCIeSpecIndexing(unittest.TestCase):
    """Test PCIe spec document indexing"""
    
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.mkdtemp()
        cls.rag_dir = os.path.join(cls.temp_dir, ".rag")
    
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.temp_dir, ignore_errors=True)
    
    def test_index_pcie_spec(self):
        """Test indexing PCIe Transaction Layer spec"""
        from rag_db import RAGDatabase
        
        rag = RAGDatabase(rag_dir=self.rag_dir)
        
        spec_file = os.path.join(PCIE_SPEC_DIR, "02_Transaction Layer", "transaction_layer.md")
        
        if not os.path.exists(spec_file):
            self.skipTest(f"PCIe spec file not found: {spec_file}")
        
        # Index spec (may take time due to size)
        chunks = rag.index_file(spec_file, category="spec", quiet=True, skip_embeddings=False)
        
        self.assertGreater(chunks, 0, "Should create chunks from spec")
        print(f"\n  Indexed PCIe spec: {chunks} chunks")
    
    def test_search_tlp_types(self):
        """Test searching for TLP type information in spec"""
        from rag_db import RAGDatabase
        
        rag = RAGDatabase(rag_dir=self.rag_dir)
        
        spec_file = os.path.join(PCIE_SPEC_DIR, "02_Transaction Layer", "transaction_layer.md")
        
        if not os.path.exists(spec_file):
            self.skipTest(f"PCIe spec file not found")
        
        # Index if not already indexed
        rag.index_file(spec_file, category="spec", quiet=True, skip_embeddings=False)
        
        # Search for TLP types
        results = rag.search("TLP Type Memory Read Write Completion", categories="spec", limit=5)
        
        self.assertGreater(len(results), 0, "Should find TLP type information")
        
        # Check that results contain relevant content
        found_tlp = False
        for score, chunk in results:
            if "TLP" in chunk.content or "Memory" in chunk.content or "Completion" in chunk.content:
                found_tlp = True
                break
        
        self.assertTrue(found_tlp, "Should find TLP-related content")
        print(f"\n  Found {len(results)} chunks about TLP types")


@unittest.skipUnless(api_available(), "No valid API key configured")
class TestPCIeCodeAnalysis(unittest.TestCase):
    """Test analyzing PCIe Verilog code using spec knowledge"""
    
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.mkdtemp()
        cls.rag_dir = os.path.join(cls.temp_dir, ".rag")
    
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.temp_dir, ignore_errors=True)
    
    def test_index_pcie_verilog(self):
        """Test indexing PCIe Verilog code"""
        from rag_db import RAGDatabase
        
        rag = RAGDatabase(rag_dir=self.rag_dir)
        
        if not os.path.exists(PCIE_MSG_RECEIVER):
            self.skipTest(f"PCIe Verilog file not found: {PCIE_MSG_RECEIVER}")
        
        chunks = rag.index_file(PCIE_MSG_RECEIVER, category="verilog", quiet=True, skip_embeddings=False)
        
        self.assertGreater(chunks, 0, "Should create chunks from Verilog")
        print(f"\n  Indexed pcie_msg_receiver.v: {chunks} chunks")
    
    def test_find_fragment_handling(self):
        """Test finding fragment handling code"""
        from rag_db import RAGDatabase
        
        rag = RAGDatabase(rag_dir=self.rag_dir)
        
        if not os.path.exists(PCIE_MSG_RECEIVER):
            self.skipTest(f"PCIe Verilog file not found")
        
        rag.index_file(PCIE_MSG_RECEIVER, category="verilog", quiet=True, skip_embeddings=False)
        
        # Search for fragment handling
        results = rag.search("fragment assembly S_PKT M_PKT L_PKT SG_PKT", categories="verilog", limit=5)
        
        self.assertGreater(len(results), 0, "Should find fragment handling code")
        
        # Check content
        found_fragment = False
        for score, chunk in results:
            if "S_PKT" in chunk.content or "fragment" in chunk.content.lower():
                found_fragment = True
                break
        
        self.assertTrue(found_fragment, "Should find S_PKT fragment code")
        print(f"\n  Found {len(results)} chunks about fragment handling")


@unittest.skipUnless(api_available(), "No valid API key configured")
class TestSpecToCodePipeline(unittest.TestCase):
    """Test full pipeline: Spec search → LLM analysis → Code understanding"""
    
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.mkdtemp()
        cls.rag_dir = os.path.join(cls.temp_dir, ".rag")
    
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.temp_dir, ignore_errors=True)
    
    def test_spec_to_code_tlp_format(self):
        """Test: Search spec for TLP format → LLM explains → Apply to code"""
        from rag_db import RAGDatabase
        from llm_client import call_llm_raw
        
        rag = RAGDatabase(rag_dir=self.rag_dir)
        
        spec_file = os.path.join(PCIE_SPEC_DIR, "02_Transaction Layer", "transaction_layer.md")
        
        if not os.path.exists(spec_file):
            self.skipTest("PCIe spec not found")
        
        # Step 1: Index spec
        rag.index_file(spec_file, category="spec", quiet=True, skip_embeddings=False)
        
        # Step 2: Search for TLP format info
        results = rag.search("TLP Fmt Type field encoding Memory Read Write", categories="spec", limit=3)
        
        self.assertGreater(len(results), 0, "Spec search should find results")
        
        # Step 3: Build context from spec
        spec_context = "PCIe Specification:\n"
        for score, chunk in results:
            spec_context += f"\n{chunk.content[:1500]}\n"
        
        # Step 4: Ask LLM to explain based on spec
        messages = [
            {"role": "system", "content": "You are a PCIe expert. Answer based on the provided specification."},
            {"role": "user", "content": f"{spec_context}\n\nQuestion: What are the Fmt[2:0] values for 3 DW and 4 DW headers?"}
        ]
        
        response = call_llm_raw(messages)
        
        # Verify LLM used spec knowledge
        self.assertIsNotNone(response)
        # Should mention Fmt values or DW headers
        self.assertTrue(
            "000" in response or "001" in response or "DW" in response.upper() or "header" in response.lower(),
            f"LLM should explain Fmt values from spec. Got: {response[:200]}"
        )
        
        print(f"\n  Spec→LLM pipeline passed!")
        print(f"  LLM response: {response[:200]}...")
    
    def test_code_analysis_with_spec(self):
        """Test: Analyze Verilog code using PCIe spec knowledge"""
        from rag_db import RAGDatabase
        from llm_client import call_llm_raw
        
        rag = RAGDatabase(rag_dir=self.rag_dir)
        
        spec_file = os.path.join(PCIE_SPEC_DIR, "02_Transaction Layer", "transaction_layer.md")
        
        if not os.path.exists(spec_file) or not os.path.exists(PCIE_MSG_RECEIVER):
            self.skipTest("Required files not found")
        
        # Index both spec and code
        rag.index_file(spec_file, category="spec", quiet=True, skip_embeddings=False)
        rag.index_file(PCIE_MSG_RECEIVER, category="verilog", quiet=True, skip_embeddings=False)
        
        # Search spec for fragment/message handling
        spec_results = rag.search("TLP fragment assembly message completion", categories="spec", limit=2)
        
        # Search code for fragment handling
        code_results = rag.search("fragment S_PKT M_PKT L_PKT assembly", categories="verilog", limit=2)
        
        # Build combined context
        context = "=== PCIe Specification ===\n"
        for score, chunk in spec_results:
            context += f"{chunk.content[:800]}\n"
        
        context += "\n=== Verilog Implementation ===\n"
        for score, chunk in code_results:
            context += f"{chunk.content[:800]}\n"
        
        # Ask LLM to analyze
        messages = [
            {"role": "system", "content": "You are a PCIe hardware designer. Analyze code compliance with spec."},
            {"role": "user", "content": f"{context}\n\nDoes the Verilog code correctly implement PCIe message fragmentation as per the spec? Briefly explain."}
        ]
        
        response = call_llm_raw(messages)
        
        self.assertIsNotNone(response)
        self.assertGreater(len(response), 50, "Response should be detailed")
        
        print(f"\n  Spec+Code analysis passed!")
        print(f"  Analysis: {response[:300]}...")
    
    def test_generate_code_from_spec(self):
        """Test: Generate Verilog code based on PCIe spec requirements"""
        from rag_db import RAGDatabase
        from llm_client import call_llm_raw
        
        rag = RAGDatabase(rag_dir=self.rag_dir)
        
        spec_file = os.path.join(PCIE_SPEC_DIR, "02_Transaction Layer", "transaction_layer.md")
        
        if not os.path.exists(spec_file):
            self.skipTest("PCIe spec not found")
        
        # Index spec
        rag.index_file(spec_file, category="spec", quiet=True, skip_embeddings=False)
        
        # Search for TLP header format
        results = rag.search("TLP header Fmt Type Length field format", categories="spec", limit=3)
        
        # Build context
        spec_context = ""
        for score, chunk in results:
            spec_context += f"{chunk.content[:1000]}\n"
        
        # Ask LLM to generate code
        messages = [
            {"role": "system", "content": "You are a Verilog RTL designer. Generate code based on PCIe spec."},
            {"role": "user", "content": f"""Based on this PCIe spec:

{spec_context}

Generate a Verilog function or module that parses the TLP header first DW to extract:
- Fmt[2:0]
- Type[4:0]
- Length[9:0]

Keep it simple, just the parsing logic."""}
        ]
        
        response = call_llm_raw(messages)
        
        self.assertIsNotNone(response)
        # Should contain Verilog-like content
        verilog_keywords = ["module", "input", "output", "wire", "reg", "assign", "function"]
        found_verilog = any(kw in response.lower() for kw in verilog_keywords)
        
        self.assertTrue(found_verilog, "LLM should generate Verilog code")
        
        print(f"\n  Spec→Code generation passed!")
        print(f"  Generated code preview: {response[:400]}...")


class TestConfigCheck(unittest.TestCase):
    """Always runs - checks test configuration"""
    
    def test_pcie_files_exist(self):
        """Check if PCIe files exist in project"""
        spec_exists = os.path.isdir(PCIE_SPEC_DIR)
        code_exists = os.path.exists(PCIE_MSG_RECEIVER)
        
        print(f"\n  PCIe Spec Dir exists: {spec_exists}")
        print(f"  PCIe Verilog exists: {code_exists}")
        
        if not spec_exists and not code_exists:
            print("  ⚠️  No PCIe files found - some tests will be skipped")


if __name__ == '__main__':
    print("\n" + "="*70)
    print("PCIe Spec-to-Code Integration Tests")
    print("="*70)
    print(f"API Key: {'Configured' if api_available() else 'NOT CONFIGURED'}")
    print(f"Model: {config.MODEL_NAME}")
    print(f"PCIe Spec Dir: {PCIE_SPEC_DIR}")
    print(f"PCIe Verilog: {PCIE_MSG_RECEIVER}")
    print("="*70 + "\n")
    
    unittest.main(verbosity=2)
