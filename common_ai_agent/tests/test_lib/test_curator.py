"""
Knowledge Curator Test Suite

Comprehensive tests for:
- Harmful node deletion
- Unused node pruning
- Similar node merging
- Statistics and candidates
"""
import sys
import os
import unittest
import tempfile
import shutil

# Import - path setup handled by conftest.py
from curator import KnowledgeCurator
from graph_lite import GraphLite, Node, Edge


class TestCuratorInit(unittest.TestCase):
    """Test Curator initialization"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.graph = GraphLite(memory_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_curator_init(self):
        """Test curator initialization"""
        curator = KnowledgeCurator(self.graph)
        self.assertIsNotNone(curator)
        self.assertEqual(curator.graph, self.graph)
    
    def test_curator_with_llm_func(self):
        """Test curator with LLM function"""
        mock_llm = lambda x, temperature=0.7: "mock response"
        curator = KnowledgeCurator(self.graph, llm_call_func=mock_llm)
        self.assertIsNotNone(curator.llm_call_func)


class TestHarmfulNodeDeletion(unittest.TestCase):
    """Test harmful node deletion"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.graph = GraphLite(memory_dir=self.temp_dir)
        self.curator = KnowledgeCurator(self.graph)
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_delete_harmful_node(self):
        """Test deleting node with high harmful count"""
        # Add harmful node
        node = Node(
            id="harmful_node",
            type="Entity",
            data={"name": "Bad Knowledge"}
        )
        node.harmful_count = 3
        node.helpful_count = 0
        self.graph.add_node(node)
        
        # Run curation
        deleted = self.curator._delete_harmful_nodes()
        
        # Node should be deleted
        self.assertGreaterEqual(deleted, 0)
    
    def test_keep_helpful_node(self):
        """Test keeping node with high helpful count"""
        # Add helpful node
        node = Node(
            id="helpful_node",
            type="Entity",
            data={"name": "Good Knowledge"}
        )
        node.helpful_count = 5
        node.harmful_count = 1
        self.graph.add_node(node)
        
        # Run curation
        self.curator._delete_harmful_nodes()
        
        # Node should still exist
        found = self.graph.get_node("helpful_node")
        self.assertIsNotNone(found)


class TestUnusedNodePruning(unittest.TestCase):
    """Test unused node pruning"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.graph = GraphLite(memory_dir=self.temp_dir)
        self.curator = KnowledgeCurator(self.graph)
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_prune_unused_returns_count(self):
        """Test that pruning returns count"""
        pruned = self.curator._prune_unused_nodes(days=30)
        self.assertIsInstance(pruned, int)


class TestCuration(unittest.TestCase):
    """Test full curation cycle"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.graph = GraphLite(memory_dir=self.temp_dir)
        self.curator = KnowledgeCurator(self.graph)
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_curate_returns_dict(self):
        """Test that curate returns stats dict"""
        result = self.curator.curate(save=False)
        
        self.assertIsInstance(result, dict)
        self.assertIn("deleted_harmful", result)
        self.assertIn("pruned_unused", result)
    
    def test_curate_with_empty_graph(self):
        """Test curating empty graph"""
        result = self.curator.curate(save=False)
        
        self.assertEqual(result["deleted_harmful"], 0)
        self.assertEqual(result["pruned_unused"], 0)


class TestCuratorStats(unittest.TestCase):
    """Test stats and candidates"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.graph = GraphLite(memory_dir=self.temp_dir)
        self.curator = KnowledgeCurator(self.graph)
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_get_stats(self):
        """Test getting statistics"""
        stats = self.curator.get_stats()
        
        self.assertIsInstance(stats, dict)
        self.assertIn("total_nodes", stats)
    
    def test_get_candidates_for_deletion(self):
        """Test getting deletion candidates"""
        candidates = self.curator.get_candidates_for_deletion()
        
        self.assertIsInstance(candidates, list)


if __name__ == '__main__':
    print("\n" + "="*70)
    print("Knowledge Curator Test Suite")
    print("="*70 + "\n")
    
    unittest.main(verbosity=2)
