"""
Zero-Dependency Knowledge Graph (Graphiti-inspired)

Provides:
- In-memory graph storage (Dict + List)
- JSON persistence
- Embedding-based semantic search (urllib API calls)
- Pure Python cosine similarity (no numpy)
- Entity and relation extraction via LLM

Zero-dependency (stdlib only + urllib for API calls).
"""
import json
import math
import uuid
from dataclasses import dataclass, asdict, field
from collections import OrderedDict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
import urllib.request
import urllib.parse


@dataclass
class Node:
    """
    Graph node representing an entity, episode, or community.

    Attributes:
        id: Unique identifier
        type: Node type (Entity, Episodic, Community)
        data: Arbitrary data dictionary
        embedding: Optional embedding vector for semantic search
        created_at: ISO format timestamp
    """
    id: str
    type: str  # "Entity", "Episodic", "Community"
    data: Dict[str, Any]
    embedding: Optional[List[float]] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Node':
        """Create Node from dictionary."""
        return cls(**data)


@dataclass
class Edge:
    """
    Graph edge representing a relationship between nodes.

    Attributes:
        source: Source node ID
        target: Target node ID
        relation: Relationship type (e.g., WORKS_ON, USES, PART_OF)
        valid_time: ISO format timestamp when relation became valid
        confidence: Confidence score (0.0-1.0)
    """
    source: str
    target: str
    relation: str
    valid_time: str = field(default_factory=lambda: datetime.now().isoformat())
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Edge':
        """Create Edge from dictionary."""
        return cls(**data)


class GraphLite:
    """
    Zero-Dependency Knowledge Graph (Graphiti-inspired)

    Features:
    - In-memory graph + JSON persistence
    - Embedding-based semantic search (via urllib API calls)
    - Pure Python cosine similarity (no numpy)
    - Temporal graph support
    - LLM-based entity/relation extraction

    Storage:
    - Nodes: Dict[node_id, Node]
    - Edges: List[Edge]
    - Files: graph_nodes.json, graph_edges.json
    """

    def __init__(self, memory_dir: str = ".brian_memory"):
        """
        Initialize GraphLite system.

        Args:
            memory_dir: Directory for storing graph files (default: ~/.brian_memory)
        """
        self.memory_dir = Path.home() / memory_dir
        self.nodes: Dict[str, Node] = {}
        self.edges: List[Edge] = []

        self.nodes_file = self.memory_dir / "graph_nodes.json"
        self.edges_file = self.memory_dir / "graph_edges.json"

        # Embedding cache to avoid redundant API calls
        self._embedding_cache: OrderedDict[str, List[float]] = OrderedDict()

        self._ensure_initialized()
        self._load()

    def _ensure_initialized(self):
        """Ensure memory directory and files exist."""
        self.memory_dir.mkdir(parents=True, exist_ok=True)

        if not self.nodes_file.exists():
            self.nodes_file.write_text("{}")

        if not self.edges_file.exists():
            self.edges_file.write_text("[]")

    # ==================== Core Graph Operations ====================

    def add_node(self, node: Node) -> None:
        """
        Add a node to the graph.

        Args:
            node: Node to add
        """
        self.nodes[node.id] = node

    def find_node_by_name(self, name: str, node_type: Optional[str] = None) -> Optional[Node]:
        """
        Find a node by its name (case-insensitive search).

        Args:
            name: Node name to search for (in node.data["name"])
            node_type: Optional node type filter

        Returns:
            First matching node, or None if not found
        """
        name_lower = name.lower()
        
        for node in self.nodes.values():
            # Check type filter
            if node_type is not None and node.type != node_type:
                continue
            
            # Check name match (case-insensitive)
            node_name = node.data.get("name", "").lower()
            if node_name == name_lower:
                return node
        
        return None

    def add_or_update_node(self, node: Node) -> str:
        """
        Add a new node or update existing one if duplicate found.
        
        Uses name-based deduplication to prevent duplicate entities.
        If an existing node with the same name is found, merges the data
        and updates the embedding.

        Args:
            node: Node to add or merge

        Returns:
            Node ID (existing or new)
        """
        # Check for existing node with same name
        node_name = node.data.get("name", "")
        
        if node_name:
            existing = self.find_node_by_name(node_name, node_type=node.type)
            
            if existing:
                # Update existing node's data (merge)
                existing.data.update(node.data)
                
                # Update embedding if provided
                if node.embedding:
                    existing.embedding = node.embedding
                
                return existing.id
        
        # No duplicate found, add as new node
        self.add_node(node)
        return node.id

    def add_edge(self, edge: Edge) -> None:
        """
        Add an edge to the graph.

        Args:
            edge: Edge to add
        """
        self.edges.append(edge)

    def get_node(self, node_id: str) -> Optional[Node]:
        """
        Retrieve a node by ID.

        Args:
            node_id: Node ID to retrieve

        Returns:
            Node if found, None otherwise
        """
        return self.nodes.get(node_id)

    def find_neighbors(self, node_id: str, relation: Optional[str] = None) -> List[Node]:
        """
        Find all neighbors of a node.

        Args:
            node_id: Source node ID
            relation: Optional relation filter (e.g., "WORKS_ON")

        Returns:
            List of neighbor nodes
        """
        neighbors = []

        for edge in self.edges:
            if edge.source == node_id:
                if relation is None or edge.relation == relation:
                    target_node = self.get_node(edge.target)
                    if target_node:
                        neighbors.append(target_node)

        return neighbors

    def get_all_nodes(self) -> List[Node]:
        """
        Get all nodes in the graph.

        Returns:
            List of all nodes
        """
        return list(self.nodes.values())

    def get_all_edges(self) -> List[Edge]:
        """
        Get all edges in the graph.

        Returns:
            List of all edges
        """
        return self.edges

    def delete_node(self, node_id: str) -> bool:
        """
        Delete a node and all its associated edges.

        Args:
            node_id: Node ID to delete

        Returns:
            True if deleted, False if not found
        """
        if node_id not in self.nodes:
            return False

        # Remove node
        del self.nodes[node_id]

        # Remove all edges connected to this node
        self.edges = [
            edge for edge in self.edges
            if edge.source != node_id and edge.target != node_id
        ]

        return True

    # ==================== A-MEM Auto-Linking ====================

    def add_note_with_auto_linking(self, content: str, context: dict = None) -> str:
        """
        A-MEM style: Add free-form note with automatic linking.
        
        Uses 2-step process:
        1. Embedding-based candidate filtering (fast)
        2. LLM-based linking decision (accurate)
        
        Args:
            content: Free-form note content
            context: Optional context dict (e.g., {"topic": "debugging", "file": "..."})
        
        Returns:
            Node ID of created note
        """
        # Create note with embedding
        note = Node(
            id=self.generate_node_id("note"),
            type="Note",
            data={
                "content": content,
                "context": context or {},
                "timestamp": datetime.now().isoformat()
            },
            embedding=self.get_embedding(content)
        )
        
        # Step 1: Find candidates via embedding similarity
        candidates = []
        for existing in self.nodes.values():
            if existing.embedding is None:
                continue
            
            # Skip self-comparison
            if existing.id == note.id:
                continue
            
            score = self.cosine_similarity(note.embedding, existing.embedding)
            
            # Import config at runtime to avoid circular dependency
            try:
                import config
                threshold = config.AMEM_SIMILARITY_THRESHOLD
            except:
                threshold = 0.6
            
            # Debug: print all similarities
            print(f"[Graph] Similarity to {existing.id[:12]}: {score:.3f} (threshold: {threshold})")
            
            if score >= threshold:
                candidates.append((score, existing))
                print(f"[Graph] → Added as candidate!")
        
        print(f"[Graph] Total candidates after filtering: {len(candidates)}")
        
        # Sort by similarity and limit
        candidates.sort(reverse=True, key=lambda x: x[0])
        
        try:
            import config
            max_candidates = config.AMEM_MAX_CANDIDATES
        except:
            max_candidates = 10
        
        candidates = candidates[:max_candidates]
        
        # Step 2: LLM decides which to link
        if candidates:
            linked_ids = self._llm_link_decision(note, candidates)
            
            # Create edges
            for target_id in linked_ids:
                edge = Edge(
                    source=note.id,
                    target=target_id,
                    relation="RELATED_TO",
                    confidence=0.9  # High confidence from LLM decision
                )
                self.add_edge(edge)
        
        # Add node to graph
        self.add_node(note)
        
        return note.id
    
    def _llm_link_decision(self, new_note: Node, candidates: List[Tuple[float, Node]]) -> List[str]:
        """
        Use LLM to decide which candidate notes should be linked.
        
        Args:
            new_note: The new note to link
            candidates: List of (score, node) tuples from embedding search
        
        Returns:
            List of node IDs to link to
        """
        # Prepare candidate descriptions
        candidate_descriptions = []
        for i, (score, node) in enumerate(candidates):
            content = node.data.get("content", node.data.get("description", node.data.get("name", "")))
            candidate_descriptions.append(f"{i}. [{node.type}] {content[:100]}")
        
        # Build prompt
        prompt = f"""You are analyzing memory connections for a knowledge graph.

New memory note:
"{new_note.data['content']}"

Candidate notes to potentially link (sorted by similarity):
{chr(10).join(candidate_descriptions)}

For EACH candidate, decide if it should be linked based on:
- EQUIVALENCE: Same concept, different wording → LINK
- CAUSAL: One causes or affects the other → LINK
- COMPLEMENTARY: Provides additional context → LINK
- CONTRADICTORY: Conflicts with new note → DON'T LINK
- IRRELEVANT: No meaningful connection → DON'T LINK

Return ONLY the indices to link as comma-separated numbers (e.g., "0,2,3").
If no links are appropriate, return "NONE".

Indices to link:"""
        
        try:
            # Use existing LLM call pattern from extract_entities
            from main import call_llm_raw
            
            # Get temperature from config
            try:
                import config
                temperature = config.AMEM_LINK_TEMPERATURE
            except:
                temperature = 0.3
            
            print(f"[Graph] Calling LLM for linking decision (temp={temperature})...")
            response = call_llm_raw(prompt, temperature=temperature).strip()
            print(f"[Graph] LLM response: {response}")
            
            # Parse response
            if response.upper() == "NONE" or not response:
                print(f"[Graph] No links suggested by LLM")
                return []
            
            # Extract indices
            indices = []
            for part in response.split(','):
                part = part.strip()
                if part.isdigit():
                    idx = int(part)
                    if 0 <= idx < len(candidates):
                        indices.append(candidates[idx][1].id)
                        print(f"[Graph] Linking to candidate {idx}: {candidates[idx][1].id}")
            
            print(f"[Graph] Total links created: {len(indices)}")
            return indices
            
        except Exception as e:
            print(f"[Graph] LLM linking decision failed: {e}")
            import traceback
            traceback.print_exc()
            return []

    # ==================== Embedding & Search ====================

    def get_embedding(self, text: str, api_key: Optional[str] = None,
                     base_url: Optional[str] = None,
                     model: Optional[str] = None) -> List[float]:
        """
        Get embedding for text using OpenAI API via urllib (zero-dependency).

        Args:
            text: Text to embed
            api_key: API key (if None, will try to load from config)
            base_url: API base URL (if None, uses config.EMBEDDING_BASE_URL)
            model: Embedding model name (if None, uses config.EMBEDDING_MODEL)

        Returns:
            Embedding vector (list of floats)
        """
        # Load config values if not provided
        try:
            import config
            if api_key is None:
                api_key = config.EMBEDDING_API_KEY
            if base_url is None:
                base_url = config.EMBEDDING_BASE_URL
            if model is None:
                model = config.EMBEDDING_MODEL
        except (ImportError, AttributeError) as e:
            if api_key is None:
                raise ValueError("API key not provided and not found in config")
            # Fallback defaults if config not available
            base_url = base_url or "https://api.openai.com/v1"
            model = model or "text-embedding-3-small"

        # Check cache first
        cache_key = f"{model}:{text[:100]}"  # Use first 100 chars as key
        if cache_key in self._embedding_cache:
            self._embedding_cache.move_to_end(cache_key)
            return self._embedding_cache[cache_key]

        # Prepare API request
        url = f"{base_url}/embeddings"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        data = {
            "input": text,
            "model": model
        }

        try:
            request = urllib.request.Request(
                url,
                data=json.dumps(data).encode('utf-8'),
                headers=headers
            )

            with urllib.request.urlopen(request, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))
                embedding = result["data"][0]["embedding"]

                # Cache the result
                self._embedding_cache[cache_key] = embedding
                
                # Enforce LRU limit (e.g., 1000 items)
                if len(self._embedding_cache) > 1000:
                    self._embedding_cache.popitem(last=False)

                return embedding

        except Exception as e:
            # Log warning but return zero vector to allow agent to continue
            print(f"[Warning] Embedding API failed: {e}")
            print("[Warning] Continuing without embeddings for this text")
            # Return zero vector as fallback (text-embedding-3-small dimension)
            return [0.0] * 1536

    def cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors (pure Python, no numpy).

        Args:
            v1: First vector
            v2: Second vector

        Returns:
            Cosine similarity score (-1.0 to 1.0)
        """
        if len(v1) != len(v2):
            raise ValueError(f"Vector dimensions don't match: {len(v1)} vs {len(v2)}")

        dot_product = sum(a * b for a, b in zip(v1, v2))
        norm_a = math.sqrt(sum(a * a for a in v1))
        norm_b = math.sqrt(sum(b * b for b in v2))

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)

    def search(self, query: str, limit: int = 10,
               node_type: Optional[str] = None) -> List[Tuple[float, Node]]:
        """
        Semantic search using embeddings (brute-force, suitable for < 5000 nodes).

        Args:
            query: Search query
            limit: Maximum number of results
            node_type: Optional node type filter

        Returns:
            List of (score, node) tuples, sorted by score (descending)
        """
        # Get query embedding
        try:
            query_embedding = self.get_embedding(query)
        except Exception as e:
            print(f"[Graph] Failed to get query embedding: {e}")
            return []

        results = []

        for node in self.nodes.values():
            # Apply type filter
            if node_type is not None and node.type != node_type:
                continue

            # Skip nodes without embeddings
            if node.embedding is None:
                continue

            # Calculate similarity
            try:
                score = self.cosine_similarity(query_embedding, node.embedding)
                results.append((score, node))
            except Exception:
                continue

        # Sort by score (descending)
        results.sort(reverse=True, key=lambda x: x[0])

        return results[:limit]

    # ==================== LLM Integration ====================

    def extract_entities_from_text(self, text: str,
                                   llm_call_func=None) -> List[Dict[str, Any]]:
        """
        Extract entities from text using LLM.

        Args:
            text: Text to extract entities from
            llm_call_func: Optional custom LLM call function

        Returns:
            List of entity dictionaries with keys: name, type, description
        """
        if llm_call_func is None:
            # Use default LLM call from main.py
            try:
                from main import call_llm_raw
                llm_call_func = call_llm_raw
            except ImportError:
                raise RuntimeError("No LLM call function available")

        prompt = f"""Extract entities from the following text.
Return JSON array with format: [{{"name": "...", "type": "Person|Project|Tool|Concept", "description": "..."}}]

Text: {text[:1000]}

Entities (JSON only):"""

        try:
            response = llm_call_func(prompt)

            # Parse JSON from response
            # Try to find JSON array in response
            start_idx = response.find('[')
            end_idx = response.rfind(']') + 1

            if start_idx != -1 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                entities = json.loads(json_str)
                return entities if isinstance(entities, list) else []

            return []

        except Exception as e:
            print(f"[Graph] Failed to extract entities: {e}")
            return []

    def extract_relations_from_text(self, text: str, entities: List[Dict[str, Any]],
                                   llm_call_func=None) -> List[Dict[str, Any]]:
        """
        Extract relations between entities from text using LLM.

        Args:
            text: Text to extract relations from
            entities: List of entities to find relations between
            llm_call_func: Optional custom LLM call function

        Returns:
            List of relation dictionaries with keys: source, target, relation, confidence
        """
        if llm_call_func is None:
            try:
                from main import call_llm_raw
                llm_call_func = call_llm_raw
            except ImportError:
                raise RuntimeError("No LLM call function available")

        entity_names = [e.get('name', '') for e in entities]

        prompt = f"""Given entities: {', '.join(entity_names)}

Find relationships in the text: {text[:1000]}

Return JSON array: [{{"source": "entity1", "target": "entity2", "relation": "WORKS_ON|USES|PART_OF|CREATES|...", "confidence": 0.0-1.0}}]

Relations (JSON only):"""

        try:
            response = llm_call_func(prompt)

            # Parse JSON from response
            start_idx = response.find('[')
            end_idx = response.rfind(']') + 1

            if start_idx != -1 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                relations = json.loads(json_str)
                return relations if isinstance(relations, list) else []

            return []

        except Exception as e:
            print(f"[Graph] Failed to extract relations: {e}")
            return []

    # ==================== Persistence ====================

    def save(self) -> None:
        """Save graph to JSON files."""
        try:
            # Save nodes
            nodes_data = {
                node_id: node.to_dict()
                for node_id, node in self.nodes.items()
            }
            self.nodes_file.write_text(json.dumps(nodes_data, indent=2, ensure_ascii=False))

            # Save edges
            edges_data = [edge.to_dict() for edge in self.edges]
            self.edges_file.write_text(json.dumps(edges_data, indent=2, ensure_ascii=False))

        except Exception as e:
            print(f"[Graph] Failed to save: {e}")

    def _load(self) -> None:
        """Load graph from JSON files."""
        try:
            # Load nodes
            nodes_data = json.loads(self.nodes_file.read_text())
            self.nodes = {
                node_id: Node.from_dict(node_dict)
                for node_id, node_dict in nodes_data.items()
            }

            # Load edges
            edges_data = json.loads(self.edges_file.read_text())
            self.edges = [Edge.from_dict(edge_dict) for edge_dict in edges_data]

        except Exception as e:
            # Initialize empty graph on load failure
            self.nodes = {}
            self.edges = []

    # ==================== Utilities ====================

    def generate_node_id(self, prefix: str = "node") -> str:
        """
        Generate a unique node ID.

        Args:
            prefix: Prefix for node ID

        Returns:
            Unique node ID (e.g., "node_a1b2c3d4")
        """
        return f"{prefix}_{uuid.uuid4().hex[:8]}"

    def get_stats(self) -> Dict[str, int]:
        """
        Get graph statistics.

        Returns:
            Dictionary with node/edge counts
        """
        node_types = {}
        for node in self.nodes.values():
            node_types[node.type] = node_types.get(node.type, 0) + 1

        return {
            'total_nodes': len(self.nodes),
            'total_edges': len(self.edges),
            'node_types': node_types,
            'nodes_with_embeddings': sum(1 for n in self.nodes.values() if n.embedding)
        }

    def clear(self) -> None:
        """Clear all nodes and edges (caution!)."""
        self.nodes.clear()
        self.edges.clear()
        self._embedding_cache.clear()
