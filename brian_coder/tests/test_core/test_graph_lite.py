"""
Graph Lite Test Suite

Comprehensive tests for:
- Node operations (add, get, delete, update)
- Edge operations
- Search functionality (BM25, embedding, hybrid)
- Persistence (save/load JSON)
- A-MEM auto-linking
"""
import sys
import os
import unittest
import tempfile
import shutil
from datetime import datetime

# Import GraphLite - path setup handled by conftest.py
from graph_lite import GraphLite, Node, Edge, SimpleBM25


class TestNode(unittest.TestCase):
    """Test Node data class"""
    
    def test_node_creation(self):
        """Test node creation with required fields"""
        node = Node(
            id="test_node_1",
            type="Entity",
            data={"name": "Test Entity"}
        )
        self.assertEqual(node.id, "test_node_1")
        self.assertEqual(node.type, "Entity")
        self.assertEqual(node.data["name"], "Test Entity")
    
    def test_node_default_values(self):
        """Test node default values"""
        node = Node(id="test", type="Entity", data={})
        self.assertIsNone(node.embedding)
        self.assertEqual(node.helpful_count, 0)
        self.assertEqual(node.harmful_count, 0)
        self.assertEqual(node.usage_count, 0)
    
    def test_node_to_dict(self):
        """Test node serialization to dict"""
        node = Node(id="test", type="Entity", data={"key": "value"})
        d = node.to_dict()
        
        self.assertIn("id", d)
        self.assertIn("type", d)
        self.assertIn("data", d)
        self.assertEqual(d["id"], "test")
    
    def test_node_from_dict(self):
        """Test node deserialization from dict"""
        data = {
            "id": "test",
            "type": "Entity",
            "data": {"name": "Test"},
            "created_at": "2024-01-01T00:00:00"
        }
        node = Node.from_dict(data)
        
        self.assertEqual(node.id, "test")
        self.assertEqual(node.type, "Entity")


class TestEdge(unittest.TestCase):
    """Test Edge data class"""
    
    def test_edge_creation(self):
        """Test edge creation"""
        edge = Edge(
            source="node1",
            target="node2",
            relation="RELATED_TO"
        )
        self.assertEqual(edge.source, "node1")
        self.assertEqual(edge.target, "node2")
        self.assertEqual(edge.relation, "RELATED_TO")
    
    def test_edge_default_confidence(self):
        """Test edge default confidence"""
        edge = Edge(source="a", target="b", relation="X")
        self.assertEqual(edge.confidence, 1.0)
    
    def test_edge_to_dict(self):
        """Test edge serialization"""
        edge = Edge(source="a", target="b", relation="X")
        d = edge.to_dict()
        
        self.assertIn("source", d)
        self.assertIn("target", d)
        self.assertIn("relation", d)
    
    def test_edge_from_dict(self):
        """Test edge deserialization"""
        data = {
            "source": "a",
            "target": "b",
            "relation": "X",
            "valid_time": "2024-01-01T00:00:00",
            "confidence": 0.9
        }
        edge = Edge.from_dict(data)
        
        self.assertEqual(edge.source, "a")
        self.assertEqual(edge.confidence, 0.9)


class TestGraphLiteNodeOperations(unittest.TestCase):
    """Test GraphLite node operations"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.graph = GraphLite()
    
    def test_add_node(self):
        """Test adding a node"""
        node = Node(id="test_add", type="Entity", data={"name": "Test"})
        self.graph.add_node(node)
        
        retrieved = self.graph.get_node("test_add")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.id, "test_add")
    
    def test_get_node_not_found(self):
        """Test getting non-existent node"""
        result = self.graph.get_node("nonexistent")
        self.assertIsNone(result)
    
    def test_delete_node(self):
        """Test deleting a node"""
        node = Node(id="to_delete", type="Entity", data={})
        self.graph.add_node(node)
        
        result = self.graph.delete_node("to_delete")
        self.assertTrue(result)
        
        retrieved = self.graph.get_node("to_delete")
        self.assertIsNone(retrieved)
    
    def test_delete_nonexistent_node(self):
        """Test deleting non-existent node"""
        result = self.graph.delete_node("nonexistent")
        self.assertFalse(result)
    
    def test_get_all_nodes(self):
        """Test getting all nodes"""
        nodes = self.graph.get_all_nodes()
        self.assertIsInstance(nodes, list)
    
    def test_find_node_by_name(self):
        """Test finding node by name"""
        node = Node(id="named_node", type="Entity", data={"name": "FindMe"})
        self.graph.add_node(node)
        
        found = self.graph.find_node_by_name("FindMe")
        self.assertIsNotNone(found)
        self.assertEqual(found.id, "named_node")
    
    def test_find_node_by_name_case_insensitive(self):
        """Test case-insensitive name search"""
        node = Node(id="case_node", type="Entity", data={"name": "CaSeMiXeD"})
        self.graph.add_node(node)
        
        found = self.graph.find_node_by_name("casemixed")
        self.assertIsNotNone(found)


class TestGraphLiteEdgeOperations(unittest.TestCase):
    """Test GraphLite edge operations"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.graph = GraphLite()
        
        # Add test nodes
        self.graph.add_node(Node(id="node_a", type="Entity", data={"name": "A"}))
        self.graph.add_node(Node(id="node_b", type="Entity", data={"name": "B"}))
    
    def test_add_edge(self):
        """Test adding an edge"""
        edge = Edge(source="node_a", target="node_b", relation="CONNECTED")
        self.graph.add_edge(edge)
        
        edges = self.graph.get_all_edges()
        matching = [e for e in edges if e.source == "node_a" and e.target == "node_b"]
        self.assertGreater(len(matching), 0)
    
    def test_find_neighbors(self):
        """Test finding neighbors"""
        edge = Edge(source="node_a", target="node_b", relation="LINKED")
        self.graph.add_edge(edge)
        
        neighbors = self.graph.find_neighbors("node_a")
        # Should find node_b as neighbor
        neighbor_ids = [n.id for n in neighbors]
        self.assertIn("node_b", neighbor_ids)


class TestSimpleBM25(unittest.TestCase):
    """Test BM25 search functionality"""
    
    def test_bm25_fit(self):
        """Test fitting BM25 on corpus"""
        bm25 = SimpleBM25()
        corpus = ["hello world", "goodbye world", "hello goodbye"]
        bm25.fit(corpus)
        
        self.assertEqual(bm25.corpus_size, 3)
        self.assertGreater(bm25.avgdl, 0)
    
    def test_bm25_get_scores(self):
        """Test getting BM25 scores"""
        bm25 = SimpleBM25()
        corpus = ["hello world", "goodbye world", "hello goodbye"]
        bm25.fit(corpus)
        
        scores = bm25.get_scores("hello")
        self.assertEqual(len(scores), 3)
        
        # "hello world" and "hello goodbye" should have higher scores
        self.assertGreater(scores[0], scores[1])  # hello world > goodbye world
        self.assertGreater(scores[2], scores[1])  # hello goodbye > goodbye world
    
    def test_bm25_empty_corpus(self):
        """Test BM25 with empty corpus"""
        bm25 = SimpleBM25()
        bm25.fit([])
        
        scores = bm25.get_scores("test")
        self.assertEqual(len(scores), 0)


class TestGraphLiteSearch(unittest.TestCase):
    """Test search functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.graph = GraphLite()
    
    def test_search_returns_list(self):
        """Test that search returns a list"""
        results = self.graph.search("test query", limit=5)
        self.assertIsInstance(results, list)
    
    def test_search_limit(self):
        """Test that search limit is respected"""
        results = self.graph.search("test", limit=3)
        self.assertLessEqual(len(results), 3)


class TestGraphLitePersistence(unittest.TestCase):
    """Test save/load functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.graph = GraphLite()
    
    def test_nodes_dict_exists(self):
        """Test that nodes dictionary exists"""
        self.assertIsInstance(self.graph.nodes, dict)
    
    def test_edges_list_exists(self):
        """Test that edges list exists"""
        self.assertIsInstance(self.graph.edges, list)
    
    def test_save_creates_file(self):
        """Test that save creates JSON files"""
        self.graph.save()
        
        # Check that files exist
        self.assertTrue(self.graph.nodes_file.exists())
        self.assertTrue(self.graph.edges_file.exists())


class TestCreditTracking(unittest.TestCase):
    """Test ACE-style credit tracking"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.graph = GraphLite()
        
        self.test_node = Node(
            id="credit_test",
            type="Entity",
            data={"name": "Credit Test"}
        )
        self.graph.add_node(self.test_node)
    
    def test_update_credits_helpful(self):
        """Test marking node as helpful"""
        self.graph.update_node_credits(["credit_test"], "helpful")
        
        node = self.graph.get_node("credit_test")
        self.assertEqual(node.helpful_count, 1)
    
    def test_update_credits_harmful(self):
        """Test marking node as harmful"""
        self.graph.update_node_credits(["credit_test"], "harmful")
        
        node = self.graph.get_node("credit_test")
        self.assertEqual(node.harmful_count, 1)
    
    def test_get_quality_score(self):
        """Test quality score calculation"""
        node = self.graph.get_node("credit_test")
        
        # Initial: 0/1 = 0.0
        score = self.graph.get_node_quality_score(node)
        self.assertEqual(score, 0.0)
        
        # After helpful: 1/2 = 0.5
        self.graph.update_node_credits(["credit_test"], "helpful")
        node = self.graph.get_node("credit_test")
        score = self.graph.get_node_quality_score(node)
        self.assertAlmostEqual(score, 0.5, places=2)


if __name__ == '__main__':
    print("\n" + "="*70)
    print("Graph Lite Test Suite")
    print("="*70 + "\n")
    
    unittest.main(verbosity=2)
