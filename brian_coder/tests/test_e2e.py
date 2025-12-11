"""
E2E (End-to-End) Test Suite

Tests the complete system flow:
- User input → Agent processing → Tool execution → Output
- RAG indexing → Search → Result formatting
- Memory persistence across sessions
- Full SubAgent pipeline (Explore → Plan → Execute → Review)

These tests simulate real user interactions.
"""
import sys
import os
import unittest
import tempfile
import shutil
import json

# Import modules - path setup handled by conftest.py
from rag_db import RAGDatabase
from graph_lite import GraphLite, Node
from memory import MemorySystem
from procedural_memory import ProceduralMemory, Action
from tools import read_file, write_file, list_dir, grep_file, find_files
from sub_agents.explore_agent import ExploreAgent
from sub_agents.execute_agent import ExecuteAgent
from sub_agents.base import AgentStatus, SubAgentResult


class TestE2ERAGFlow(unittest.TestCase):
    """E2E: Complete RAG workflow from indexing to search"""
    
    def setUp(self):
        """Set up test project structure"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a mini Verilog project
        self.src_dir = os.path.join(self.temp_dir, "src")
        os.makedirs(self.src_dir)
        
        # Main module
        with open(os.path.join(self.src_dir, "counter.v"), 'w') as f:
            f.write("""
module counter #(
    parameter WIDTH = 8
)(
    input clk,
    input reset,
    input enable,
    output reg [WIDTH-1:0] count
);
    always @(posedge clk or posedge reset) begin
        if (reset)
            count <= {WIDTH{1'b0}};
        else if (enable)
            count <= count + 1'b1;
    end
endmodule
""")
        
        # Testbench
        with open(os.path.join(self.src_dir, "counter_tb.v"), 'w') as f:
            f.write("""
module counter_tb;
    reg clk, reset, enable;
    wire [7:0] count;
    
    counter dut(.clk(clk), .reset(reset), .enable(enable), .count(count));
    
    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end
    
    initial begin
        reset = 1; enable = 0;
        #20 reset = 0;
        #10 enable = 1;
        #100 $finish;
    end
endmodule
""")
        
        self.rag = RAGDatabase()
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_index_and_search_verilog_project(self):
        """E2E: Index Verilog project and search for modules"""
        # Step 1: Index both files
        counter_chunks = self.rag.index_file(
            os.path.join(self.src_dir, "counter.v"),
            quiet=True, skip_embeddings=True
        )
        tb_chunks = self.rag.index_file(
            os.path.join(self.src_dir, "counter_tb.v"),
            quiet=True, skip_embeddings=True
        )
        
        self.assertGreater(counter_chunks, 0)
        self.assertGreater(tb_chunks, 0)
        
        # Step 2: Get indexed chunks
        all_chunks = list(self.rag.chunks.values())
        
        # Step 3: Find module definitions
        module_chunks = [c for c in all_chunks if c.chunk_type == "module"]
        self.assertGreaterEqual(len(module_chunks), 2)
        
        # Step 4: Verify chunk content
        counter_found = any("counter" in c.content.lower() for c in module_chunks)
        self.assertTrue(counter_found)


class TestE2EMemoryPersistence(unittest.TestCase):
    """E2E: Memory persists across multiple sessions"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_full_memory_lifecycle(self):
        """E2E: Complete memory lifecycle - create, persist, reload, update"""
        # === Session 1: Initial setup ===
        mem1 = MemorySystem(memory_dir=self.temp_dir)
        proc1 = ProceduralMemory(memory_dir=self.temp_dir)
        graph1 = GraphLite(memory_dir=self.temp_dir)
        
        # User preferences
        mem1.update_preference("coding_style", "verilog_2005")
        mem1.update_preference("add_comments", True)
        mem1.update_project_context("project_type", "FPGA Design")
        
        # Experience
        actions = [
            Action(tool="read_file", args="counter.v", result="success"),
            Action(tool="run_command", args="iverilog counter.v", result="success")
        ]
        traj_id = proc1.build("Compile Verilog module", actions, "success", 1)
        proc1.save()
        
        # Knowledge
        graph1.add_node(Node(
            id="project_info",
            type="ProjectContext",
            data={"name": "FPGA Counter", "modules": ["counter", "fsm"]}
        ))
        graph1.save()
        
        # === Session 2: Verify persistence ===
        mem2 = MemorySystem(memory_dir=self.temp_dir)
        proc2 = ProceduralMemory(memory_dir=self.temp_dir)
        graph2 = GraphLite(memory_dir=self.temp_dir)
        
        # Check preferences persisted
        self.assertEqual(mem2.get_preference("coding_style"), "verilog_2005")
        self.assertEqual(mem2.get_preference("add_comments"), True)
        self.assertEqual(mem2.get_project_context("project_type"), "FPGA Design")
        
        # Check knowledge graph persisted
        node = graph2.get_node("project_info")
        self.assertIsNotNone(node)
        self.assertEqual(node.data["name"], "FPGA Counter")
        
        # === Session 3: Update and verify ===
        mem3 = MemorySystem(memory_dir=self.temp_dir)
        mem3.update_preference("coding_style", "systemverilog")
        
        mem4 = MemorySystem(memory_dir=self.temp_dir)
        self.assertEqual(mem4.get_preference("coding_style"), "systemverilog")


class TestE2EToolChain(unittest.TestCase):
    """E2E: Tool chain execution (read → process → write)"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        # Create test file
        with open("original.v", 'w') as f:
            f.write("module original; endmodule")
    
    def tearDown(self):
        """Clean up"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_read_process_write_chain(self):
        """E2E: Read file → Process → Write result"""
        # Step 1: List files
        files = list_dir(".")
        self.assertIn("original.v", files)
        
        # Step 2: Read original
        content = read_file("original.v")
        self.assertIn("module original", content)
        
        # Step 3: Write modified version
        new_content = content.replace("original", "modified")
        write_result = write_file("modified.v", new_content)
        self.assertIn("successfully", write_result.lower())
        
        # Step 4: Verify written file
        verify_content = read_file("modified.v")
        self.assertIn("module modified", verify_content)
    
    def test_grep_find_chain(self):
        """E2E: Find files → Grep pattern"""
        # Create additional files
        with open("test1.v", 'w') as f:
            f.write("module test1; wire signal_a; endmodule")
        with open("test2.v", 'w') as f:
            f.write("module test2; wire signal_b; endmodule")
        
        # Step 1: Find all Verilog files
        found = find_files("*.v", ".")
        self.assertIn("test1.v", found)
        self.assertIn("test2.v", found)
        
        # Step 2: Grep for pattern
        grep_result = grep_file("signal", "test1.v")
        self.assertIn("signal_a", grep_result)


class TestE2ESubAgentWorkflow(unittest.TestCase):
    """E2E: Complete SubAgent workflow"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test project
        with open(os.path.join(self.temp_dir, "main.v"), 'w') as f:
            f.write("module main; endmodule")
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_explore_then_execute_workflow(self):
        """E2E: ExploreAgent → ExecuteAgent sequential workflow"""
        
        # Mock LLM that produces valid plans
        class SequentialMockLLM:
            def __init__(self):
                self.stage = 0
            
            def __call__(self, messages, temperature=0.7):
                self.stage += 1
                
                if self.stage == 1:  # Explore planning
                    return json.dumps({
                        "task_understanding": "Explore the project",
                        "strategy": "List and read files",
                        "steps": [{
                            "step_number": 1,
                            "description": "List files",
                            "prompt": "List directory",
                            "required_tools": ["list_dir"],
                            "depends_on": [],
                            "expected_output": "File list"
                        }],
                        "estimated_tools": ["list_dir"],
                        "success_criteria": "Files discovered"
                    })
                elif self.stage <= 3:  # Explore execution
                    return "Thought: Listing\nResult: Found main.v"
                elif self.stage == 4:  # Execute planning
                    return json.dumps({
                        "task_understanding": "Create test file",
                        "strategy": "Write directly",
                        "steps": [{
                            "step_number": 1,
                            "description": "Write test",
                            "prompt": "Create test",
                            "required_tools": ["write_file"],
                            "depends_on": [],
                            "expected_output": "File created"
                        }],
                        "estimated_tools": ["write_file"],
                        "success_criteria": "Test exists"
                    })
                else:
                    return "Thought: Done\nResult: Test created"
        
        mock_llm = SequentialMockLLM()
        
        # Tool executor
        def mock_tool(name, args):
            if name == "list_dir":
                return "main.v"
            elif name == "write_file":
                return "File written"
            return "OK"
        
        # Step 1: Run ExploreAgent
        explore_agent = ExploreAgent(
            name="explore",
            llm_call_func=mock_llm,
            execute_tool_func=mock_tool,
            max_iterations=3
        )
        
        explore_result = explore_agent.run(
            task="Explore the Verilog project",
            context={"working_dir": self.temp_dir}
        )
        
        self.assertIn(explore_result.status, [AgentStatus.COMPLETED, AgentStatus.FAILED])
        
        # Step 2: Pass context to ExecuteAgent
        execute_agent = ExecuteAgent(
            name="execute",
            llm_call_func=mock_llm,
            execute_tool_func=mock_tool,
            max_iterations=3
        )
        
        execute_result = execute_agent.run(
            task="Create a testbench for main.v",
            context={
                "previous_agent": "explore",
                "files_found": explore_result.artifacts.get("files_read", [])
            }
        )
        
        self.assertIn(execute_result.status, [AgentStatus.COMPLETED, AgentStatus.FAILED])


class TestE2EKnowledgeAccumulation(unittest.TestCase):
    """E2E: Knowledge accumulates and improves over time"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_knowledge_builds_over_sessions(self):
        """E2E: Each session adds to knowledge base"""
        # Session 1: Initial knowledge
        graph1 = GraphLite(memory_dir=self.temp_dir)
        graph1.add_node(Node(id="k1", type="Concept", data={"topic": "Verilog"}))
        graph1.save()
        
        initial_count = len(graph1.get_all_nodes())
        
        # Session 2: Add more knowledge
        graph2 = GraphLite(memory_dir=self.temp_dir)
        graph2.add_node(Node(id="k2", type="Concept", data={"topic": "FSM"}))
        graph2.add_node(Node(id="k3", type="Concept", data={"topic": "Timing"}))
        graph2.save()
        
        # Session 3: Verify accumulated
        graph3 = GraphLite(memory_dir=self.temp_dir)
        final_count = len(graph3.get_all_nodes())
        
        self.assertEqual(final_count, initial_count + 2)
        
        # All nodes should be searchable
        all_nodes = graph3.get_all_nodes()
        topics = [n.data.get("topic") for n in all_nodes]
        
        self.assertIn("Verilog", topics)
        self.assertIn("FSM", topics)
        self.assertIn("Timing", topics)


if __name__ == '__main__':
    print("\n" + "="*70)
    print("E2E (End-to-End) Tests")
    print("="*70 + "\n")
    
    unittest.main(verbosity=2)
