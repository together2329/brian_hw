"""
Integration Test Suite #3: DeepThink ↔ ProceduralMemory ↔ GraphLite

Tests the Deep Think scoring pipeline that combines:
- ProceduralMemory (experience score)
- GraphLite (knowledge score)
- LLM (coherence score - mocked)

Scenarios:
- Score hypotheses using all memory systems
- ACE credit assignment flow
- Full Deep Think pipeline (branching → scoring → selection)
"""
import sys
import os
import unittest
import tempfile
import shutil

# Import modules - path setup handled by conftest.py
from deep_think import (
    Hypothesis, DeepThinkResult,
    HypothesisBrancher, ParallelReasoner, HypothesisScorer, DeepThinkEngine
)
from procedural_memory import ProceduralMemory, Action
from graph_lite import GraphLite, Node


class TestDeepThinkScoringPipeline(unittest.TestCase):
    """Test: Deep Think scoring uses all memory systems"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.proc_mem = ProceduralMemory(memory_dir=self.temp_dir)
        self.graph = GraphLite(memory_dir=self.temp_dir)
        
        # Add some experience data
        actions = [
            Action(tool="read_file", args="main.v", result="success"),
            Action(tool="grep_file", args="pattern='error'", result="found")
        ]
        self.proc_mem.build(
            task_description="Debug Verilog module",
            actions=actions,
            outcome="success",
            iterations=2
        )
        
        # Add some knowledge
        self.graph.add_node(Node(
            id="knowledge_debug",
            type="Concept",
            data={"name": "Verilog Debugging", "description": "Techniques for debugging"}
        ))
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_scorer_uses_procedural_memory(self):
        """Test: Scorer retrieves from ProceduralMemory"""
        scorer = HypothesisScorer(
            procedural_memory=self.proc_mem,
            graph_lite=self.graph
        )
        
        hyp = Hypothesis(
            id="test_hyp",
            strategy_name="debug-first",
            description="Start by debugging",
            first_action="read_file('main.v')",
            reasoning="Similar to past successful debug session"
        )
        
        # Score experience
        exp_score = scorer.score_experience(hyp, "Debug Verilog")
        
        # Should get a score (neutral 0.5 or higher if match)
        self.assertGreaterEqual(exp_score, 0.0)
        self.assertLessEqual(exp_score, 1.0)
    
    def test_scorer_uses_graph_knowledge(self):
        """Test: Scorer searches GraphLite for knowledge"""
        scorer = HypothesisScorer(
            procedural_memory=self.proc_mem,
            graph_lite=self.graph
        )
        
        hyp = Hypothesis(
            id="test_hyp",
            strategy_name="knowledge-based",
            description="Use Verilog debugging techniques",
            first_action="list_dir('.')",
            reasoning="Leverage existing knowledge"
        )
        
        # Score knowledge (returns tuple)
        knowledge_score, referenced_ids = scorer.score_knowledge(hyp)
        
        self.assertGreaterEqual(knowledge_score, 0.0)
        self.assertIsInstance(referenced_ids, list)
    
    def test_score_all_combines_dimensions(self):
        """Test: score_all calculates weighted final score"""
        scorer = HypothesisScorer(
            procedural_memory=self.proc_mem,
            graph_lite=self.graph
        )
        
        hypotheses = [
            Hypothesis(
                id="hyp1", strategy_name="approach1", description="First approach",
                first_action="read_file('test.v')", reasoning="Test"
            ),
            Hypothesis(
                id="hyp2", strategy_name="approach2", description="Second approach",
                first_action="list_dir('.')", reasoning="Test"
            )
        ]
        
        # Score all
        scored_hyps, referenced_ids = scorer.score_all(hypotheses, "Debug task")
        
        # Each hypothesis should have scores
        for hyp in scored_hyps:
            self.assertIn("experience", hyp.scores)
            self.assertIn("knowledge", hyp.scores)
            self.assertIn("confidence", hyp.scores)
            self.assertGreater(hyp.final_score, 0.0)


class TestACECreditAssignment(unittest.TestCase):
    """Test: ACE-style credit assignment through Deep Think"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.graph = GraphLite(memory_dir=self.temp_dir)
        
        # Add knowledge nodes for credit tracking
        self.graph.add_node(Node(
            id="credit_node_1",
            type="Concept",
            data={"name": "Test Knowledge 1"}
        ))
        self.graph.add_node(Node(
            id="credit_node_2",
            type="Concept",
            data={"name": "Test Knowledge 2"}
        ))
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_referenced_nodes_tracked(self):
        """Test: Nodes referenced during scoring are tracked"""
        scorer = HypothesisScorer(graph_lite=self.graph)
        
        hyp = Hypothesis(
            id="test", strategy_name="test", description="Test Knowledge",
            first_action="test", reasoning="test"
        )
        
        # Score knowledge - should return referenced node IDs
        score, refs = scorer.score_knowledge(hyp)
        
        # refs should be a list (may be empty or contain IDs)
        self.assertIsInstance(refs, list)
    
    def test_credit_can_be_assigned_to_nodes(self):
        """Test: Referenced nodes can receive credit"""
        # Simulate scoring that returns node IDs
        referenced_ids = ["credit_node_1", "credit_node_2"]
        
        # Assign helpful credit
        updated = self.graph.update_node_credits(referenced_ids, "helpful")
        
        # Verify credit was assigned
        node1 = self.graph.get_node("credit_node_1")
        self.assertEqual(node1.helpful_count, 1)


class TestFullDeepThinkFlow(unittest.TestCase):
    """Test: Complete Deep Think pipeline execution"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.proc_mem = ProceduralMemory(memory_dir=self.temp_dir)
        self.graph = GraphLite(memory_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_brancher_creates_hypotheses(self):
        """Test: Brancher creates fallback hypothesis without LLM"""
        brancher = HypothesisBrancher()
        
        hypotheses = brancher.branch(
            task="Test task",
            context="Test context",
            num_hypotheses=3
        )
        
        # Should create at least default hypothesis
        self.assertGreaterEqual(len(hypotheses), 1)
        self.assertIsInstance(hypotheses[0], Hypothesis)
    
    def test_scorer_produces_rankings(self):
        """Test: Scorer produces sortable rankings"""
        scorer = HypothesisScorer(
            procedural_memory=self.proc_mem,
            graph_lite=self.graph
        )
        
        hypotheses = [
            Hypothesis(id="h1", strategy_name="a", description="A",
                      first_action="test", reasoning="test", confidence=0.8),
            Hypothesis(id="h2", strategy_name="b", description="B",
                      first_action="test", reasoning="test", confidence=0.3),
        ]
        
        scored, _ = scorer.score_all(hypotheses, "Test")
        
        # Should be sortable by final_score
        sorted_hyps = sorted(scored, key=lambda h: h.final_score, reverse=True)
        self.assertEqual(len(sorted_hyps), 2)


if __name__ == '__main__':
    print("\n" + "="*70)
    print("Integration Test: DeepThink ↔ ProceduralMemory ↔ GraphLite")
    print("="*70 + "\n")
    
    unittest.main(verbosity=2)
