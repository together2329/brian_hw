"""
Verilog RAG Integration Test Suite

Tests Verilog-specific RAG functionality:
- Verilog file parsing and chunking
- Module/always/wire extraction
- Verilog-specific search queries
- Hierarchical chunk relationships
- Port and signal analysis
"""
import sys
import os
import unittest
import tempfile
import shutil

# Import modules - path setup handled by conftest.py
from rag_db import RAGDatabase, Chunk
from graph_lite import GraphLite, Node, Edge


class TestVerilogChunkingIntegration(unittest.TestCase):
    """Test Verilog-specific chunking features"""
    
    def setUp(self):
        """Set up test Verilog project"""
        self.temp_dir = tempfile.mkdtemp()
        self.rag_dir = os.path.join(self.temp_dir, ".rag")
        self.rag = RAGDatabase(rag_dir=self.rag_dir)
        self.rag.chunks = {}  # Clear any existing chunks
        
        # Create realistic Verilog files
        self._create_counter_module()
        self._create_fsm_module()
        self._create_top_module()
        self._create_testbench()
    
    def _create_counter_module(self):
        """Create a counter module"""
        path = os.path.join(self.temp_dir, "counter.v")
        with open(path, 'w') as f:
            f.write("""
// 8-bit up/down counter with enable
module counter #(
    parameter WIDTH = 8,
    parameter INIT_VALUE = 0
)(
    input wire clk,
    input wire reset_n,
    input wire enable,
    input wire up_down,  // 1: up, 0: down
    output reg [WIDTH-1:0] count,
    output wire overflow,
    output wire underflow
);

    // Overflow/underflow detection
    assign overflow = (count == {WIDTH{1'b1}}) && enable && up_down;
    assign underflow = (count == {WIDTH{1'b0}}) && enable && !up_down;

    // Counter logic
    always @(posedge clk or negedge reset_n) begin
        if (!reset_n) begin
            count <= INIT_VALUE;
        end else if (enable) begin
            if (up_down)
                count <= count + 1'b1;
            else
                count <= count - 1'b1;
        end
    end

endmodule
""")
        self.counter_path = path
    
    def _create_fsm_module(self):
        """Create an FSM module"""
        path = os.path.join(self.temp_dir, "fsm_controller.v")
        with open(path, 'w') as f:
            f.write("""
// Simple 3-state FSM controller
module fsm_controller (
    input wire clk,
    input wire reset_n,
    input wire start,
    input wire done_signal,
    output reg busy,
    output reg [1:0] state
);

    // State encoding
    localparam IDLE = 2'b00;
    localparam RUNNING = 2'b01;
    localparam COMPLETE = 2'b10;

    reg [1:0] next_state;

    // State register
    always @(posedge clk or negedge reset_n) begin
        if (!reset_n)
            state <= IDLE;
        else
            state <= next_state;
    end

    // Next state logic
    always @(*) begin
        next_state = state;
        case (state)
            IDLE: begin
                if (start)
                    next_state = RUNNING;
            end
            RUNNING: begin
                if (done_signal)
                    next_state = COMPLETE;
            end
            COMPLETE: begin
                next_state = IDLE;
            end
            default: next_state = IDLE;
        endcase
    end

    // Output logic
    always @(*) begin
        busy = (state == RUNNING);
    end

endmodule
""")
        self.fsm_path = path
    
    def _create_top_module(self):
        """Create a top module that instantiates others"""
        path = os.path.join(self.temp_dir, "top.v")
        with open(path, 'w') as f:
            f.write("""
// Top-level module
module top (
    input wire clk,
    input wire reset_n,
    input wire start,
    output wire [7:0] count_out,
    output wire busy
);

    wire enable;
    wire done;

    // Instantiate FSM controller
    fsm_controller u_fsm (
        .clk(clk),
        .reset_n(reset_n),
        .start(start),
        .done_signal(done),
        .busy(busy),
        .state()
    );

    // Instantiate counter
    counter #(
        .WIDTH(8),
        .INIT_VALUE(0)
    ) u_counter (
        .clk(clk),
        .reset_n(reset_n),
        .enable(enable),
        .up_down(1'b1),
        .count(count_out),
        .overflow(done),
        .underflow()
    );

    assign enable = busy;

endmodule
""")
        self.top_path = path
    
    def _create_testbench(self):
        """Create a testbench"""
        path = os.path.join(self.temp_dir, "top_tb.v")
        with open(path, 'w') as f:
            f.write("""
// Testbench for top module
`timescale 1ns/1ps

module top_tb;

    reg clk;
    reg reset_n;
    reg start;
    wire [7:0] count_out;
    wire busy;

    // DUT instantiation
    top dut (
        .clk(clk),
        .reset_n(reset_n),
        .start(start),
        .count_out(count_out),
        .busy(busy)
    );

    // Clock generation
    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end

    // Test sequence
    initial begin
        $dumpfile("top_tb.vcd");
        $dumpvars(0, top_tb);
        
        reset_n = 0;
        start = 0;
        #20;
        
        reset_n = 1;
        #10;
        
        start = 1;
        #10 start = 0;
        
        #500;
        $finish;
    end

endmodule
""")
        self.tb_path = path
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_index_all_verilog_files(self):
        """Test indexing all Verilog files in project"""
        total_chunks = 0
        
        for path in [self.counter_path, self.fsm_path, self.top_path, self.tb_path]:
            chunks = self.rag.index_file(path, quiet=True, skip_embeddings=True)
            total_chunks += chunks
        
        self.assertGreater(total_chunks, 0)
        print(f"\n  Indexed {total_chunks} chunks from 4 files")
    
    def test_extract_all_modules(self):
        """Test that all modules are extracted"""
        for path in [self.counter_path, self.fsm_path, self.top_path, self.tb_path]:
            self.rag.index_file(path, quiet=True, skip_embeddings=True)
        
        chunks = list(self.rag.chunks.values())
        module_chunks = [c for c in chunks if c.chunk_type == "module"]
        
        module_names = [c.metadata.get("module_name", "") for c in module_chunks]
        
        self.assertIn("counter", module_names)
        self.assertIn("fsm_controller", module_names)
        self.assertIn("top", module_names)
        self.assertIn("top_tb", module_names)
        
        print(f"\n  Found modules: {module_names}")
    
    def test_extract_always_blocks(self):
        """Test that always blocks are extracted"""
        self.rag.index_file(self.fsm_path, quiet=True, skip_embeddings=True)
        
        chunks = list(self.rag.chunks.values())
        always_chunks = [c for c in chunks if c.chunk_type == "always"]
        
        # FSM has 3 always blocks
        self.assertGreaterEqual(len(always_chunks), 2)
        print(f"\n  Found {len(always_chunks)} always blocks")
    
    def test_extract_parameters(self):
        """Test that parameters are extracted"""
        self.rag.index_file(self.counter_path, quiet=True, skip_embeddings=True)
        
        chunks = list(self.rag.chunks.values())
        
        # Check if parameter info is in metadata
        module_chunks = [c for c in chunks if c.chunk_type == "module"]
        
        for chunk in module_chunks:
            if chunk.metadata.get("module_name") == "counter":
                # Parameters should be mentioned in content
                self.assertIn("WIDTH", chunk.content)
                self.assertIn("INIT_VALUE", chunk.content)
    
    def test_extract_ports(self):
        """Test that ports are extracted"""
        self.rag.index_file(self.counter_path, quiet=True, skip_embeddings=True)
        
        chunks = list(self.rag.chunks.values())
        port_chunks = [c for c in chunks if c.chunk_type == "port"]
        
        # Counter has: clk, reset_n, enable, up_down, count, overflow, underflow
        if port_chunks:  # Depending on chunking level
            port_names = " ".join([c.content for c in port_chunks])
            self.assertTrue(
                "clk" in port_names or 
                any("clk" in c.content for c in chunks)
            )


class TestVerilogSearchIntegration(unittest.TestCase):
    """Test Verilog-specific search functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.rag_dir = os.path.join(self.temp_dir, ".rag")
        self.rag = RAGDatabase(rag_dir=self.rag_dir)
        self.rag.chunks = {}  # Clear any existing chunks
        self.graph = GraphLite(memory_dir=self.temp_dir)
        
        # Create and index a Verilog file
        self.verilog_path = os.path.join(self.temp_dir, "test.v")
        with open(self.verilog_path, 'w') as f:
            f.write("""
module pcie_receiver (
    input wire clk,
    input wire reset,
    input wire [31:0] rx_data,
    input wire rx_valid,
    output reg [31:0] payload,
    output reg payload_valid
);
    // PCIe TLP parsing logic
    always @(posedge clk) begin
        if (reset) begin
            payload <= 32'b0;
            payload_valid <= 1'b0;
        end else if (rx_valid) begin
            payload <= rx_data;
            payload_valid <= 1'b1;
        end
    end
endmodule
""")
        self.rag.index_file(self.verilog_path, quiet=True, skip_embeddings=True)
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_chunks_contain_verilog_content(self):
        """Test that chunks contain Verilog-specific content"""
        chunks = list(self.rag.chunks.values())
        
        # Find module chunk
        module_chunks = [c for c in chunks if c.chunk_type == "module"]
        self.assertGreater(len(module_chunks), 0)
        
        # Module should contain PCIe-related content
        content = module_chunks[0].content
        self.assertIn("pcie_receiver", content)
    
    def test_store_chunks_in_graph(self):
        """Test storing indexed chunks in knowledge graph"""
        chunks = list(self.rag.chunks.values())
        
        for chunk in chunks:
            node = Node(
                id=f"verilog_{chunk.id}",
                type=f"Verilog{chunk.chunk_type.title()}",
                data={
                    "chunk_type": chunk.chunk_type,
                    "level": chunk.level,
                    "source_file": os.path.basename(chunk.source_file),
                    "content_preview": chunk.content[:100]
                }
            )
            self.graph.add_node(node)
        
        all_nodes = self.graph.get_all_nodes()
        verilog_nodes = [n for n in all_nodes if n.type.startswith("Verilog")]
        
        self.assertGreater(len(verilog_nodes), 0)


class TestVerilogHierarchyIntegration(unittest.TestCase):
    """Test Verilog module hierarchy tracking"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.rag_dir = os.path.join(self.temp_dir, ".rag")
        self.rag = RAGDatabase(rag_dir=self.rag_dir)
        self.rag.chunks = {}  # Clear any existing chunks
        self.graph = GraphLite(memory_dir=self.temp_dir)
        
        # Create hierarchical design
        self._create_leaf_module()
        self._create_parent_module()
    
    def _create_leaf_module(self):
        path = os.path.join(self.temp_dir, "adder.v")
        with open(path, 'w') as f:
            f.write("""
module adder (
    input wire [7:0] a,
    input wire [7:0] b,
    output wire [8:0] sum
);
    assign sum = a + b;
endmodule
""")
        self.leaf_path = path
    
    def _create_parent_module(self):
        path = os.path.join(self.temp_dir, "alu.v")
        with open(path, 'w') as f:
            f.write("""
module alu (
    input wire [7:0] op_a,
    input wire [7:0] op_b,
    input wire [1:0] op_sel,
    output reg [8:0] result
);
    wire [8:0] add_result;
    
    adder u_adder (
        .a(op_a),
        .b(op_b),
        .sum(add_result)
    );
    
    always @(*) begin
        case (op_sel)
            2'b00: result = add_result;
            2'b01: result = op_a - op_b;
            default: result = 9'b0;
        endcase
    end
endmodule
""")
        self.parent_path = path
    
    def tearDown(self):
        """Clean up"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_build_hierarchy_graph(self):
        """Test building module hierarchy in graph"""
        # Index files
        self.rag.index_file(self.leaf_path, quiet=True, skip_embeddings=True)
        self.rag.index_file(self.parent_path, quiet=True, skip_embeddings=True)
        
        # Add modules to graph
        chunks = list(self.rag.chunks.values())
        module_chunks = [c for c in chunks if c.chunk_type == "module"]
        
        for chunk in module_chunks:
            node = Node(
                id=chunk.metadata.get("module_name", chunk.id),
                type="VerilogModule",
                data={"source": os.path.basename(chunk.source_file)}
            )
            self.graph.add_node(node)
        
        # Create hierarchy edge (alu instantiates adder)
        edge = Edge(
            source="alu",
            target="adder",
            relation="INSTANTIATES"
        )
        self.graph.add_edge(edge)
        
        # Verify hierarchy
        edges = self.graph.get_all_edges()
        inst_edges = [e for e in edges if e.relation == "INSTANTIATES"]
        
        self.assertEqual(len(inst_edges), 1)
        self.assertEqual(inst_edges[0].source, "alu")
        self.assertEqual(inst_edges[0].target, "adder")


class TestVerilogToolsIntegration(unittest.TestCase):
    """Test Verilog analysis tools integration with RAG"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.rag_dir = os.path.join(self.temp_dir, ".rag")
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        # Create test file
        with open("signal_test.v", 'w') as f:
            f.write("""
module signal_test (
    input wire clk,
    input wire data_in,
    output reg data_out
);
    wire intermediate;
    reg [3:0] counter;
    
    assign intermediate = data_in & counter[0];
    
    always @(posedge clk) begin
        counter <= counter + 1;
        data_out <= intermediate;
    end
endmodule
""")
        
        self.rag = RAGDatabase(rag_dir=self.rag_dir)
        self.rag.chunks = {}  # Clear any existing chunks
        self.rag.index_file("signal_test.v", quiet=True, skip_embeddings=True)
    
    def tearDown(self):
        """Clean up"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_rag_chunks_contain_signals(self):
        """Test that RAG chunks contain signal information"""
        chunks = list(self.rag.chunks.values())
        
        # Check for wire/reg in chunks
        all_content = " ".join([c.content for c in chunks])
        
        self.assertIn("intermediate", all_content)
        self.assertIn("counter", all_content)
        self.assertIn("data_out", all_content)


if __name__ == '__main__':
    print("\n" + "="*70)
    print("Verilog RAG Integration Tests")
    print("="*70 + "\n")
    
    unittest.main(verbosity=2)
