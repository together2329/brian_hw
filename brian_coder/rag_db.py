"""
Verilog Agentic RAG Database

Zero-Dependency RAG system for Verilog/Testbench/Spec documents.
Features:
- Hierarchical chunking (Module → Ports → Wires → Always → Assign)
- Category-based indexing with descriptions
- Hash-based incremental re-indexing
- Semantic search via embeddings

Storage: JSON files in ~/.brian_rag/
"""
import json
import hashlib
import re
import os
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple


@dataclass
class Chunk:
    """
    A chunk of code/document for RAG search.
    
    Attributes:
        id: Unique identifier
        source_file: Path to original file
        category: "verilog", "testbench", or "spec"
        level: Hierarchical level (1-5 for Verilog)
        chunk_type: "module", "port", "wire", "always", "assign", "section"
        content: Actual code/text content
        start_line: Starting line in source file
        end_line: Ending line in source file
        embedding: Vector embedding for semantic search
        metadata: Additional info (module_name, etc.)
    """
    id: str
    source_file: str
    category: str
    level: int
    chunk_type: str
    content: str
    start_line: int
    end_line: int
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Chunk':
        return cls(**data)


@dataclass
class CategoryConfig:
    """Configuration for a RAG category."""
    name: str
    enabled: bool
    description: str
    include: List[str]
    exclude: List[str]


class RAGDatabase:
    """
    Zero-Dependency RAG Database for Verilog projects.
    
    Features:
    - Hierarchical Verilog chunking
    - Category-based organization
    - Hash-based incremental indexing
    - Semantic search via embeddings
    """

    def __init__(self, rag_dir: str = ".brian_rag", fine_grained: bool = False):
        """
        Initialize RAG Database.

        Args:
            rag_dir: Directory for RAG storage (relative to home)
            fine_grained: If True, create more detailed chunks (individual signals,
                         case statements, etc.) for precise search. Default is False.
        """
        self.rag_dir = Path.home() / rag_dir
        self.index_path = self.rag_dir / "rag_index.json"
        self.config_file = self.rag_dir / ".ragconfig"
        self.fine_grained = fine_grained

        self.chunks: Dict[str, Chunk] = {}
        self.file_hashes: Dict[str, str] = {}
        self.categories: Dict[str, CategoryConfig] = {}

        # Rate limiting settings (load from config, convert ms to seconds)
        self.api_call_count = 0
        self.last_api_call_time = 0
        try:
            from . import config
        except ImportError:
            import config
        # RAG_RATE_LIMIT_DELAY_MS is in milliseconds, convert to seconds
        rate_limit_ms = config.RAG_RATE_LIMIT_DELAY_MS
        self.rate_limit_delay = rate_limit_ms / 1000.0  # Convert ms to seconds

        # Auto-detected embedding dimension (None = not yet detected)
        self.embedding_dimension = None

        self._ensure_initialized()
        self._load()

    def _ensure_initialized(self):
        """Create RAG directory and files if needed."""
        self.rag_dir.mkdir(parents=True, exist_ok=True)
        
        if not self.index_path.exists():
            self.index_path.write_text('{"chunks": {}, "file_hashes": {}}')
        
        # Create default .ragconfig if not exists
        if not self.config_file.exists():
            self._create_default_config()

    def _create_default_config(self):
        """Create default category configuration."""
        default_config = """# .ragconfig - RAG Category Configuration
version: 1

verilog:
  enabled: true
  description: "RTL 소스 코드. 모듈 구현, 신호 정의, 상태머신 분석 시 검색"
  include:
    - "*.v"
    - "*.sv"
  exclude:
    - "*_backup.v"
    - "*_old.v"

testbench:
  enabled: true
  description: "테스트벤치. 시뮬레이션 시나리오, 테스트 케이스, expected 동작 확인 시 검색"
  include:
    - "*_tb.v"
    - "*_test.v"
  exclude: []

spec:
  enabled: true
  description: "프로토콜 스펙, 설계 문서. 프로토콜 규칙, 타이밍 요구사항 확인 시 검색"
  include:
    - "*.md"
    - "*.txt"
  exclude:
    - "README.md"
"""
        self.config_file.write_text(default_config)
    
    def _load_config_patterns(self) -> dict:
        """
        Load patterns from .ragconfig file.
        Returns dict with 'include' and 'exclude' patterns per category.
        """
        patterns = {'include': [], 'exclude': []}
        
        try:
            content = self.config_file.read_text()
            
            # Simple YAML-like parsing (no external dependencies)
            current_category = None
            current_section = None
            
            for line in content.split('\n'):
                stripped = line.strip()
                
                # Skip comments and empty lines
                if not stripped or stripped.startswith('#'):
                    continue
                
                # Category header (verilog:, testbench:, spec:)
                if stripped.endswith(':') and not stripped.startswith('-'):
                    if '  ' not in line:  # Top-level key
                        current_category = stripped[:-1]
                        current_section = None
                    else:  # Nested key (enabled:, include:, exclude:, etc.)
                        key = stripped[:-1]
                        if key in ['include', 'exclude']:
                            current_section = key
                        elif key == 'enabled' or key == 'description':
                            current_section = None
                        
                # List item (  - "*.v")
                elif stripped.startswith('-') and current_category and current_section:
                    # Check if this category is commented out
                    # by looking at original line indentation
                    pattern = stripped[1:].strip().strip('"').strip("'")
                    if pattern:
                        if current_section == 'include':
                            patterns['include'].append(pattern)
                        elif current_section == 'exclude':
                            patterns['exclude'].append(pattern)
                            
        except Exception as e:
            print(f"[RAG] Config parse error: {e}, using defaults")
            patterns = {'include': ["*.v", "*.sv", "*.md"], 'exclude': []}
        
        # Fallback if empty
        if not patterns['include']:
            patterns = {'include': ["*.v", "*.sv", "*.md"], 'exclude': []}
            
        return patterns


    # ==================== Hierarchical Verilog Chunking ====================

    def chunk_verilog_hierarchical(self, content: str, file_path: str) -> List[Chunk]:
        """
        Hierarchical chunking for Verilog files.
        
        Levels:
        1. Module 전체 (개요용)
        2. Port declarations
        3. Wire/Reg declarations
        4. Always blocks
        5. Assign statements
        
        Args:
            content: Verilog file content
            file_path: Path to source file
            
        Returns:
            List of Chunk objects
        """
        chunks = []
        lines = content.split('\n')
        
        # Level 1: Extract full modules
        # Pattern handles:
        # - module name (...);  (with ports, multi-line)
        # - module name;        (no ports, testbench style)
        # - module name #(...) (...); (with parameters)
        module_pattern = re.compile(
            r'module\s+(\w+)\s*(?:#\s*\([^)]*\))?\s*(?:\([^;]*\))?\s*;.*?endmodule',
            re.DOTALL
        )
        
        for match in module_pattern.finditer(content):
            module_name = match.group(1)
            module_content = match.group(0)
            start_pos = match.start()
            end_pos = match.end()
            
            # Calculate line numbers
            start_line = content[:start_pos].count('\n') + 1
            end_line = content[:end_pos].count('\n') + 1
            
            # Level 1: Full module
            chunks.append(Chunk(
                id=self._generate_chunk_id(),
                source_file=file_path,
                category="verilog",
                level=1,
                chunk_type="module",
                content=module_content,
                start_line=start_line,
                end_line=end_line,
                metadata={
                    "module_name": module_name,
                    "summary": f"Module {module_name} - full implementation"
                }
            ))
            
            # Level 2: Port declarations
            port_chunks = self._extract_ports(module_content, file_path, module_name, start_line)
            chunks.extend(port_chunks)
            
            # Level 3: Wire/Reg declarations
            wire_chunks = self._extract_wires(module_content, file_path, module_name, start_line)
            chunks.extend(wire_chunks)
            
            # Level 4: Always blocks
            always_chunks = self._extract_always_blocks(module_content, file_path, module_name, start_line)
            chunks.extend(always_chunks)
            
            # Level 5: Assign statements
            assign_chunks = self._extract_assigns(module_content, file_path, module_name, start_line)
            chunks.extend(assign_chunks)
        
        return chunks

    def _extract_ports(self, module_content: str, file_path: str, 
                       module_name: str, base_line: int) -> List[Chunk]:
        """Extract port declarations (Level 2)."""
        chunks = []
        
        # Match input/output/inout declarations with position tracking
        port_pattern = re.compile(
            r'(input|output|inout)\s+(?:wire|reg)?\s*(?:\[[^\]]+\])?\s*(\w+)',
            re.MULTILINE
        )
        
        ports = []
        first_line = None
        last_line = None
        
        for match in port_pattern.finditer(module_content):
            ports.append(f"{match.group(1)} {match.group(2)}")
            # Track actual line numbers
            line_num = module_content[:match.start()].count('\n') + 1
            if first_line is None:
                first_line = line_num
            last_line = line_num
        
        if ports:
            # Group all ports into one chunk with accurate line numbers
            port_content = "// Port declarations\n" + "\n".join(ports)
            chunks.append(Chunk(
                id=self._generate_chunk_id(),
                source_file=file_path,
                category="verilog",
                level=2,
                chunk_type="port",
                content=port_content,
                start_line=base_line + (first_line - 1) if first_line else base_line,
                end_line=base_line + (last_line - 1) if last_line else base_line,
                metadata={
                    "module_name": module_name,
                    "port_count": len(ports),
                    "summary": f"Port declarations for {module_name}"
                }
            ))
        
        return chunks

    def _extract_wires(self, module_content: str, file_path: str,
                       module_name: str, base_line: int) -> List[Chunk]:
        """Extract wire/reg declarations (Level 3)."""
        chunks = []
        
        # Match wire and reg declarations with position tracking
        wire_pattern = re.compile(
            r'^[ \t]*(wire|reg)\s+(?:\[[^\]]+\])?\s*(\w+)',
            re.MULTILINE
        )
        
        wires = []
        wire_lines = []  # Track line number for each wire
        first_line = None
        last_line = None
        
        for match in wire_pattern.finditer(module_content):
            wires.append(f"{match.group(1)} {match.group(2)}")
            line_num = module_content[:match.start()].count('\n') + 1
            wire_lines.append(line_num)
            if first_line is None:
                first_line = line_num
            last_line = line_num
        
        if wires:
            wire_content = "// Wire/Reg declarations\n" + "\n".join(wires)
            chunks.append(Chunk(
                id=self._generate_chunk_id(),
                source_file=file_path,
                category="verilog",
                level=3,
                chunk_type="wire",
                content=wire_content,
                start_line=base_line + (first_line - 1) if first_line else base_line,
                end_line=base_line + (last_line - 1) if last_line else base_line,
                metadata={
                    "module_name": module_name,
                    "wire_count": len(wires),
                    "summary": f"Wire/Reg declarations for {module_name}"
                }
            ))
        
        # Fine-grained: individual wire/reg declarations with correct line numbers
        if self.fine_grained:
            for wire_decl, line_num in zip(wires, wire_lines):
                signal_name = wire_decl.split()[-1] if wire_decl else "unknown"
                actual_line = base_line + line_num - 1
                chunks.append(Chunk(
                    id=self._generate_chunk_id(),
                    source_file=file_path,
                    category="verilog",
                    level=6,  # Level 6: individual signals
                    chunk_type="signal",
                    content=wire_decl,
                    start_line=actual_line,
                    end_line=actual_line,
                    metadata={
                        "module_name": module_name,
                        "signal_name": signal_name,
                        "summary": f"Signal: {signal_name} in {module_name}"
                    }
                ))
        
        return chunks

    def _extract_always_blocks(self, module_content: str, file_path: str,
                                module_name: str, base_line: int) -> List[Chunk]:
        """Extract always blocks (Level 4), case statements (Level 7), and if-else (Level 9).
        
        Supports:
        - always @(...) begin...end
        - always @(*) single_statement;
        - always_comb begin...end
        - always_ff @(...) begin...end
        - always_latch begin...end
        """
        chunks = []
        
        # Pattern 1: always blocks with begin...end
        always_starts = list(re.finditer(
            r'(always\s*@\s*\([^)]+\)|always_comb|always_ff\s*@\s*\([^)]+\)|always_latch)\s*begin', 
            module_content
        ))
        
        block_num = 0
        for start_match in always_starts:
            block_num += 1
            start_pos = start_match.start()
            
            # Find matching end by counting begin/end with word boundaries
            # Skip: endcase, endfunction, endmodule, etc.
            content_after = module_content[start_match.end():]
            depth = 1
            pos = 0
            
            while depth > 0 and pos < len(content_after):
                # Use regex to find begin/end with word boundaries
                remaining = content_after[pos:]
                
                begin_match = re.search(r'\bbegin\b', remaining)
                end_match = re.search(r'\bend\b(?!case|function|module|task|generate|primitive)', remaining)
                
                next_begin = begin_match.start() + pos if begin_match else -1
                next_end = end_match.start() + pos if end_match else -1
                
                if next_end == -1:
                    break
                
                if next_begin != -1 and next_begin < next_end:
                    depth += 1
                    pos = next_begin + 5
                else:
                    depth -= 1
                    if depth == 0:
                        end_pos = start_match.end() + next_end + 3
                        break
                    pos = next_end + 3
            else:
                end_pos = len(module_content)
            
            always_content = module_content[start_pos:end_pos]
            always_body = always_content[len(start_match.group(0)):-3]  # Remove "always @(...) begin" and "end"
            
            # Calculate line numbers
            start_offset = module_content[:start_pos].count('\n')
            end_offset = module_content[:end_pos].count('\n')
            
            # Determine block type
            if 'posedge' in always_content or 'negedge' in always_content:
                block_type = "sequential"
            else:
                block_type = "combinational"
            
            chunks.append(Chunk(
                id=self._generate_chunk_id(),
                source_file=file_path,
                category="verilog",
                level=4,
                chunk_type="always",
                content=always_content,
                start_line=base_line + start_offset,
                end_line=base_line + end_offset,
                metadata={
                    "module_name": module_name,
                    "block_number": block_num,
                    "block_type": block_type,
                    "summary": f"Always block #{block_num} ({block_type}) in {module_name}"
                }
            ))
            
            # Fine-grained: extract case statements and if-else
            if self.fine_grained:
                # Extract case statements (Level 7)
                case_pattern = re.compile(
                    r'case\s*\(([^)]+)\)(.*?)endcase',
                    re.DOTALL
                )
                case_num = 0
                for case_match in case_pattern.finditer(always_body):
                    case_num += 1
                    case_var = case_match.group(1).strip()
                    case_content = case_match.group(0)
                    
                    # Extract individual case branches
                    case_body = case_match.group(2)
                    
                    chunks.append(Chunk(
                        id=self._generate_chunk_id(),
                        source_file=file_path,
                        category="verilog",
                        level=7,
                        chunk_type="case",
                        content=case_content[:1500],  # Limit size
                        start_line=base_line + start_offset,
                        end_line=base_line + end_offset,
                        metadata={
                            "module_name": module_name,
                            "case_variable": case_var,
                            "summary": f"case({case_var}) in {module_name}"
                        }
                    ))
                
                # Extract if-else blocks (Level 9)
                if_pattern = re.compile(
                    r'if\s*\(([^)]+)\)\s*begin',
                    re.MULTILINE
                )
                for if_match in if_pattern.finditer(always_body):
                    condition = if_match.group(1).strip()[:60]  # Truncate long conditions
                    
                    chunks.append(Chunk(
                        id=self._generate_chunk_id(),
                        source_file=file_path,
                        category="verilog",
                        level=9,
                        chunk_type="if_block",
                        content=f"if ({if_match.group(1)})",
                        start_line=base_line + start_offset,
                        end_line=base_line + start_offset,
                        metadata={
                            "module_name": module_name,
                            "condition": condition,
                            "summary": f"if({condition}) in {module_name}"
                        }
                    ))
                
                # Extract non-blocking assignments (<=) - Level 8
                nb_assign_pattern = re.compile(r'(\w+)\s*<=\s*([^;]+);')
                for asgn_match in nb_assign_pattern.finditer(always_body):
                    signal = asgn_match.group(1)
                    value = asgn_match.group(2).strip()[:50]
                    
                    chunks.append(Chunk(
                        id=self._generate_chunk_id(),
                        source_file=file_path,
                        category="verilog",
                        level=8,
                        chunk_type="nb_assign",
                        content=asgn_match.group(0),
                        start_line=base_line + start_offset,
                        end_line=base_line + start_offset,
                        metadata={
                            "module_name": module_name,
                            "signal_name": signal,
                            "summary": f"{signal} <= {value}... in {module_name}"
                        }
                    ))
                
                # Extract blocking assignments (=) - Level 10
                # Careful: exclude <=, ==, !=, >=, ===, !==
                b_assign_pattern = re.compile(r'(\w+)\s*(?<![<>=!])=(?![=])\s*([^;]+);')
                for asgn_match in b_assign_pattern.finditer(always_body):
                    signal = asgn_match.group(1)
                    value = asgn_match.group(2).strip()[:50]
                    
                    # Skip false positives (case labels, etc.)
                    if signal in ['default', 'begin', 'end']:
                        continue
                    
                    chunks.append(Chunk(
                        id=self._generate_chunk_id(),
                        source_file=file_path,
                        category="verilog",
                        level=10,
                        chunk_type="b_assign",
                        content=asgn_match.group(0),
                        start_line=base_line + start_offset,
                        end_line=base_line + start_offset,
                        metadata={
                            "module_name": module_name,
                            "signal_name": signal,
                            "summary": f"{signal} = {value}... in {module_name}"
                        }
                    ))
        
        # Pattern 2: Single-statement always blocks (without begin...end)
        # e.g., always @(*) foo = bar;  or  always_comb out = in1 & in2;
        single_stmt_pattern = re.compile(
            r'(always\s*@\s*\([^)]+\)|always_comb|always_ff\s*@\s*\([^)]+\)|always_latch)\s+(?!begin)(\w+\s*[<]?=\s*[^;]+;)',
            re.MULTILINE
        )
        
        for match in single_stmt_pattern.finditer(module_content):
            block_num += 1
            always_type = match.group(1).strip()
            statement = match.group(2).strip()
            
            start_offset = module_content[:match.start()].count('\n')
            end_offset = module_content[:match.end()].count('\n')
            
            if 'posedge' in always_type or 'negedge' in always_type or 'always_ff' in always_type:
                block_type = "sequential"
            else:
                block_type = "combinational"
            
            chunks.append(Chunk(
                id=self._generate_chunk_id(),
                source_file=file_path,
                category="verilog",
                level=4,
                chunk_type="always",
                content=match.group(0),
                start_line=base_line + start_offset,
                end_line=base_line + end_offset,
                metadata={
                    "module_name": module_name,
                    "block_number": block_num,
                    "block_type": block_type,
                    "single_statement": True,
                    "summary": f"Always block #{block_num} ({block_type}, single-stmt) in {module_name}"
                }
            ))
        
        return chunks

    def _extract_assigns(self, module_content: str, file_path: str,
                         module_name: str, base_line: int) -> List[Chunk]:
        """Extract assign statements (Level 5, and Level 11 for fine-grained)."""
        chunks = []
        
        # Match assign statements with position tracking
        assign_pattern = re.compile(
            r'assign\s+(\w+)\s*=\s*([^;]+);',
            re.MULTILINE
        )
        
        assigns = []
        assign_data = []  # Store (signal, value, line_num) for fine-grained
        first_line = None
        last_line = None
        
        for match in assign_pattern.finditer(module_content):
            signal = match.group(1)
            value = match.group(2).strip()
            assigns.append(f"assign {signal} = {value};")
            line_num = module_content[:match.start()].count('\n') + 1
            assign_data.append((signal, value, line_num, match.group(0)))
            if first_line is None:
                first_line = line_num
            last_line = line_num
        
        if assigns:
            # Level 5: Group all assigns
            assign_content = "// Assign statements\n" + "\n".join(assigns)
            chunks.append(Chunk(
                id=self._generate_chunk_id(),
                source_file=file_path,
                category="verilog",
                level=5,
                chunk_type="assign",
                content=assign_content,
                start_line=base_line + (first_line - 1) if first_line else base_line,
                end_line=base_line + (last_line - 1) if last_line else base_line,
                metadata={
                    "module_name": module_name,
                    "assign_count": len(assigns),
                    "summary": f"Assign statements for {module_name}"
                }
            ))
            
            # Level 11: Individual continuous assigns (fine-grained)
            if self.fine_grained:
                for signal, value, line_num, full_stmt in assign_data:
                    actual_line = base_line + line_num - 1
                    chunks.append(Chunk(
                        id=self._generate_chunk_id(),
                        source_file=file_path,
                        category="verilog",
                        level=11,
                        chunk_type="cont_assign",
                        content=full_stmt,
                        start_line=actual_line,
                        end_line=actual_line,
                        metadata={
                            "module_name": module_name,
                            "signal_name": signal,
                            "summary": f"assign {signal} = {value[:30]}... in {module_name}"
                        }
                    ))
        
        return chunks


    # ==================== Testbench Chunking ====================

    def chunk_testbench(self, content: str, file_path: str) -> List[Chunk]:
        """Chunk testbench files (simpler than RTL)."""
        chunks = []
        
        # Use same hierarchical approach as verilog
        chunks.extend(self.chunk_verilog_hierarchical(content, file_path))
        
        # Update category to testbench
        for chunk in chunks:
            chunk.category = "testbench"
        
        return chunks

    # ==================== Spec/Doc Chunking ====================

    def chunk_spec(self, content: str, file_path: str) -> List[Chunk]:
        """Chunk specification/documentation files (Markdown)."""
        chunks = []
        
        # Split by headers (## or ###)
        sections = re.split(r'\n(#{1,3}\s+[^\n]+)\n', content)
        
        current_section = ""
        section_num = 0
        
        for i, part in enumerate(sections):
            if part.startswith('#'):
                current_section = part.strip('# \n')
            elif part.strip():
                section_num += 1
                section_content = part.strip()
                
                if len(section_content) > 50:  # Skip very short sections
                    chunks.append(Chunk(
                        id=self._generate_chunk_id(),
                        source_file=file_path,
                        category="spec",
                        level=1,
                        chunk_type="section",
                        content=section_content[:2000],  # Limit size
                        start_line=1,
                        end_line=1,
                        metadata={
                            "section_title": current_section,
                            "summary": f"Section: {current_section}"
                        }
                    ))
        
        return chunks

    # ==================== Indexing ====================

    def index_file(self, file_path: str, category: str = None) -> int:
        """
        Index a single file.
        
        Args:
            file_path: Path to file
            category: Override category (auto-detect if None)
            
        Returns:
            Number of chunks created
        """
        path = Path(file_path)
        if not path.exists():
            print(f"[RAG] File not found: {file_path}")
            return 0
        
        # Check if reindex needed (hash comparison)
        current_hash = self._get_file_hash(file_path)
        stored_hash = self.file_hashes.get(str(path.resolve()))
        
        if current_hash == stored_hash:
            print(f"[RAG] Skipping (unchanged): {path.name}")
            return 0
        
        # Read content
        content = path.read_text(encoding='utf-8', errors='ignore')
        
        # Auto-detect category
        if category is None:
            if path.suffix in ['.v', '.sv']:
                if '_tb' in path.name or '_test' in path.name:
                    category = "testbench"
                else:
                    category = "verilog"
            elif path.suffix in ['.md', '.txt']:
                category = "spec"
            else:
                category = "verilog"  # Default
        
        # Remove old chunks from this file
        old_chunks = [cid for cid, c in self.chunks.items() 
                      if c.source_file == str(path.resolve())]
        for cid in old_chunks:
            del self.chunks[cid]
        
        # Chunk based on category
        if category in ["verilog"]:
            new_chunks = self.chunk_verilog_hierarchical(content, str(path.resolve()))
        elif category == "testbench":
            new_chunks = self.chunk_testbench(content, str(path.resolve()))
        elif category == "spec":
            new_chunks = self.chunk_spec(content, str(path.resolve()))
        else:
            new_chunks = []
        
        # Generate embeddings for chunks
        for chunk in new_chunks:
            # _get_embedding() handles failures internally by returning zero vector
            chunk.embedding = self._get_embedding(chunk.content[:1000])
            self.chunks[chunk.id] = chunk
        
        # Update hash
        self.file_hashes[str(path.resolve())] = current_hash
        
        # Incremental save after each file (prevents data loss on Ctrl+C)
        self.save()
        
        print(f"[RAG] Indexed: {path.name} ({len(new_chunks)} chunks)")
        return len(new_chunks)

    def index_directory(self, dir_path: str, patterns: List[str] = None,
                        category: str = None) -> int:
        """
        Index all matching files in a directory.

        Args:
            dir_path: Directory path (treated as root for relative patterns)
            patterns: File patterns - supports both:
                     - Absolute paths: "/Users/.../file.v", "/Users/.../dir/*.v"
                     - Relative patterns: "*.v", "*.sv"
                     Reads from .ragconfig if None
            category: Category for all files (auto-detect if None)

        Returns:
            Total chunks created
        """
        import fnmatch
        import glob as glob_module

        # Load patterns from .ragconfig if not specified
        config_patterns = self._load_config_patterns()

        if patterns is None:
            patterns = config_patterns['include']

        exclude_patterns = config_patterns['exclude']

        path = Path(dir_path)
        if not path.exists():
            print(f"[RAG] Directory not found: {dir_path}")
            return 0

        total_chunks = 0
        indexed_files = set()  # Track indexed files to avoid duplicates

        for pattern in patterns:
            # Normalize pattern and handle both absolute and relative paths
            pattern = pattern.strip()

            # Check if pattern contains glob wildcards
            if '*' in pattern or '?' in pattern:
                # Glob pattern - use glob.glob() for absolute paths
                if pattern.startswith('/'):
                    # Absolute glob pattern (e.g., "/Users/.../dir/*.v")
                    matching_files = glob_module.glob(pattern)
                    for file_path in matching_files:
                        file_path_obj = Path(file_path)
                        if file_path_obj.is_file():
                            # Check exclude patterns
                            skip = False
                            for excl in exclude_patterns:
                                if fnmatch.fnmatch(file_path_obj.name, excl):
                                    skip = True
                                    break

                            if not skip and str(file_path_obj.resolve()) not in indexed_files:
                                total_chunks += self.index_file(str(file_path_obj), category)
                                indexed_files.add(str(file_path_obj.resolve()))
                else:
                    # Relative glob pattern - relative to dir_path
                    for file_path in path.rglob(pattern):
                        if file_path.is_file():
                            # Check exclude patterns
                            skip = False
                            for excl in exclude_patterns:
                                if fnmatch.fnmatch(file_path.name, excl):
                                    skip = True
                                    break

                            if not skip and str(file_path.resolve()) not in indexed_files:
                                total_chunks += self.index_file(str(file_path), category)
                                indexed_files.add(str(file_path.resolve()))
            else:
                # No wildcards - treat as file path (absolute or relative)
                if pattern.startswith('/'):
                    # Absolute file path
                    abs_path = Path(pattern)
                    if abs_path.exists() and abs_path.is_file():
                        skip = False
                        for excl in exclude_patterns:
                            if fnmatch.fnmatch(abs_path.name, excl):
                                skip = True
                                break

                        if not skip and str(abs_path.resolve()) not in indexed_files:
                            total_chunks += self.index_file(str(abs_path), category)
                            indexed_files.add(str(abs_path.resolve()))
                    else:
                        print(f"[RAG] File not found: {pattern}")
                else:
                    # Relative file path
                    rel_path = path / pattern
                    if rel_path.exists() and rel_path.is_file():
                        skip = False
                        for excl in exclude_patterns:
                            if fnmatch.fnmatch(rel_path.name, excl):
                                skip = True
                                break

                        if not skip and str(rel_path.resolve()) not in indexed_files:
                            total_chunks += self.index_file(str(rel_path), category)
                            indexed_files.add(str(rel_path.resolve()))

        self.save()
        return total_chunks


    # ==================== Search ====================

    def search(self, query: str, categories: str = "all", 
               limit: int = 5, level: int = None) -> List[Tuple[float, Chunk]]:
        """
        Semantic search across indexed chunks.
        
        Args:
            query: Search query (natural language)
            categories: "verilog", "testbench", "spec", "verilog,testbench", "all"
            limit: Maximum results
            level: Filter by hierarchical level (1-5)
            
        Returns:
            List of (score, chunk) tuples, sorted by score
        """
        # Check for changes before searching
        self._smart_reindex()
        
        # Get query embedding
        try:
            query_embedding = self._get_embedding(query)
        except Exception as e:
            print(f"[RAG] Query embedding failed: {e}")
            return []
        
        # Parse categories
        if categories == "all":
            allowed_categories = ["verilog", "testbench", "spec"]
        else:
            allowed_categories = [c.strip() for c in categories.split(',')]
        
        results = []

        for chunk in self.chunks.values():
            # Filter by category
            if chunk.category not in allowed_categories:
                continue

            # Filter by level
            if level is not None and chunk.level != level:
                continue

            # Calculate similarity (embedding is never None now)
            try:
                score = self._cosine_similarity(query_embedding, chunk.embedding)
                # Filter out zero-score results (from failed embeddings)
                if score > 0.0:
                    results.append((score, chunk))
            except Exception:
                continue
        
        # Sort by score
        results.sort(reverse=True, key=lambda x: x[0])
        
        return results[:limit]

    def _smart_reindex(self):
        """Check for file changes and reindex if needed."""
        for file_path, stored_hash in list(self.file_hashes.items()):
            if Path(file_path).exists():
                current_hash = self._get_file_hash(file_path)
                if current_hash != stored_hash:
                    print(f"[RAG] Change detected: {Path(file_path).name}")
                    self.index_file(file_path)

    # ==================== Embedding (reuse from graph_lite) ====================

    def _get_embedding(self, text: str) -> List[float]:
        """
        Get embedding using existing graph_lite infrastructure.

        Auto-detects embedding dimension from first successful API call.
        Returns zero vector with correct dimension on failure.
        """
        try:
            # Try to use graph_lite's embedding function
            from graph_lite import GraphLite
            graph = GraphLite()
            return graph.get_embedding(text)
        except Exception as e:
            try:
                # Fallback: direct API call with retry logic
                return self._get_embedding_direct(text)
            except Exception as e2:
                # Final fallback: return zero vector (allows search to continue)
                # Dimension is auto-detected from API responses, with fallback to config
                if self.embedding_dimension is None:
                    try:
                        from . import config
                    except ImportError:
                        import config
                    embedding_dim = config.EMBEDDING_DIMENSION
                else:
                    embedding_dim = self.embedding_dimension

                print(f"[RAG] Embedding failed (using zero vector, dim={embedding_dim}): {e2}")
                return [0.0] * embedding_dim

    def _get_embedding_direct(self, text: str) -> List[float]:
        """
        Direct embedding API call with retry logic and rate limiting.

        Handles:
        - Rate limiting (429 Too Many Requests)
        - Network errors and timeouts
        - Exponential backoff retry
        """
        import urllib.request
        import time

        try:
            # Try relative import first (when imported as package)
            try:
                from . import config
            except ImportError:
                import config
            api_key = config.EMBEDDING_API_KEY
            base_url = config.EMBEDDING_BASE_URL
            model = config.EMBEDDING_MODEL
        except Exception as e:
            raise ValueError(f"Embedding config not found: {e}")

        url = f"{base_url}/embeddings"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        data = {
            "input": text[:8000],  # Limit text length
            "model": model
        }

        # Retry configuration
        max_retries = 3
        base_backoff = 1.0  # Start with 1 second

        for attempt in range(max_retries):
            # Rate limiting: enforce minimum delay between API calls
            current_time = time.time()
            time_since_last_call = current_time - self.last_api_call_time
            if time_since_last_call < self.rate_limit_delay:
                sleep_time = self.rate_limit_delay - time_since_last_call
                time.sleep(sleep_time)

            self.last_api_call_time = time.time()
            self.api_call_count += 1

            try:
                request = urllib.request.Request(
                    url,
                    data=json.dumps(data).encode('utf-8'),
                    headers=headers
                )

                with urllib.request.urlopen(request, timeout=30) as response:
                    result = json.loads(response.read().decode('utf-8'))
                    embedding = result["data"][0]["embedding"]

                    # Auto-detect embedding dimension from first successful API call
                    if self.embedding_dimension is None:
                        self.embedding_dimension = len(embedding)
                        print(f"[RAG] Auto-detected embedding dimension: {self.embedding_dimension}")

                    return embedding

            except urllib.error.HTTPError as e:
                if e.code == 429:  # Too Many Requests
                    if attempt < max_retries - 1:
                        # Exponential backoff: 1s, 2s, 4s...
                        backoff_time = base_backoff * (2 ** attempt)
                        print(f"[RAG] Rate limited (429). Retrying in {backoff_time:.1f}s... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(backoff_time)
                    else:
                        raise ValueError(f"API rate limit exceeded after {max_retries} retries")
                else:
                    # Other HTTP errors (400, 401, 403, etc.)
                    raise ValueError(f"API error {e.code}: {e.read().decode('utf-8')}")

            except urllib.error.URLError as e:
                if attempt < max_retries - 1:
                    # Network error, retry with backoff
                    backoff_time = base_backoff * (2 ** attempt)
                    print(f"[RAG] Network error: {e.reason}. Retrying in {backoff_time:.1f}s...")
                    time.sleep(backoff_time)
                else:
                    raise ValueError(f"Network error after {max_retries} retries: {e.reason}")

            except urllib.error.HTTPException as e:
                if attempt < max_retries - 1:
                    backoff_time = base_backoff * (2 ** attempt)
                    time.sleep(backoff_time)
                else:
                    raise ValueError(f"HTTP error after {max_retries} retries: {e}")

    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        """Calculate cosine similarity (pure Python)."""
        import math
        
        if len(v1) != len(v2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(v1, v2))
        norm_a = math.sqrt(sum(a * a for a in v1))
        norm_b = math.sqrt(sum(b * b for b in v2))
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return dot_product / (norm_a * norm_b)

    # ==================== Utilities ====================

    def _generate_chunk_id(self) -> str:
        """Generate unique chunk ID."""
        import uuid
        return f"chunk_{uuid.uuid4().hex[:8]}"

    def _get_file_hash(self, file_path: str) -> str:
        """Calculate MD5 hash of file content."""
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()

    def get_stats(self) -> Dict[str, Any]:
        """Get RAG database statistics."""
        stats = {
            "total_chunks": len(self.chunks),
            "indexed_files": len(self.file_hashes),
            "by_category": {},
            "by_level": {}
        }
        
        for chunk in self.chunks.values():
            cat = chunk.category
            stats["by_category"][cat] = stats["by_category"].get(cat, 0) + 1
            
            lvl = f"level_{chunk.level}"
            stats["by_level"][lvl] = stats["by_level"].get(lvl, 0) + 1
        
        return stats

    def get_categories_info(self) -> str:
        """Get category descriptions for system prompt."""
        info = "=== RAG Categories ===\n"
        info += "Available categories for rag_search():\n"
        
        # Default descriptions
        categories = {
            "verilog": "RTL 소스 코드. 모듈 구현, 신호 정의, 상태머신 분석 시 검색",
            "testbench": "테스트벤치. 시뮬레이션 시나리오, expected 동작 확인 시 검색",
            "spec": "프로토콜 스펙, 설계 문서. 프로토콜 규칙, 타이밍 요구사항 확인 시 검색"
        }
        
        for name, desc in categories.items():
            info += f"• {name}: {desc}\n"
        
        info += "\nChoose relevant categories based on user's question.\n"
        return info

    # ==================== Persistence ====================

    def save(self):
        """Save RAG index to JSON file."""
        try:
            data = {
                "chunks": {cid: c.to_dict() for cid, c in self.chunks.items()},
                "file_hashes": self.file_hashes
            }
            self.index_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"[RAG] Save failed: {e}")

    def _load(self):
        """Load RAG index from JSON file."""
        try:
            data = json.loads(self.index_path.read_text())
            self.chunks = {
                cid: Chunk.from_dict(cdata) 
                for cid, cdata in data.get("chunks", {}).items()
            }
            self.file_hashes = data.get("file_hashes", {})
        except Exception as e:
            self.chunks = {}
            self.file_hashes = {}

    def clear(self):
        """Clear all indexed data."""
        self.chunks.clear()
        self.file_hashes.clear()
        self.save()
        print("[RAG] Database cleared")


# ==================== Convenience Functions ====================

# Global RAG instance (lazy initialization)
_rag_db = None

def get_rag_db() -> RAGDatabase:
    """Get or create global RAG database instance."""
    global _rag_db
    if _rag_db is None:
        _rag_db = RAGDatabase()
    return _rag_db
