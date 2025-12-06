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
from collections import OrderedDict, Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
import urllib.request
import urllib.parse
import re


class SimpleBM25:
    """Zero-dependency BM25 implementation."""
    def __init__(self):
        self.k1 = 1.5
        self.b = 0.75
        self.corpus_size = 0
        self.avgdl = 0
        self.idf = {}
        self.inverted_index = defaultdict(list)
        self.doc_len = []

    def fit(self, corpus):
        self.corpus_size = len(corpus)
        self.doc_len = []
        self.inverted_index = defaultdict(list)
        total_len = 0
        doc_freqs = Counter()

        for idx, doc in enumerate(corpus):
            length = len(doc)
            self.doc_len.append(length)
            total_len += length
            
            counts = Counter(doc)
            for term, count in counts.items():
                self.inverted_index[term].append((idx, count))
                doc_freqs[term] += 1

        self.avgdl = total_len / self.corpus_size if self.corpus_size > 0 else 0
        
        self.idf = {}
        for term, freq in doc_freqs.items():
            self.idf[term] = math.log(((self.corpus_size - freq + 0.5) / (freq + 0.5)) + 1)

    def get_scores(self, query):
        scores = [0.0] * self.corpus_size
        for term in query:
            if term not in self.idf: continue
            
            q_idf = self.idf[term]
            for doc_idx, tf in self.inverted_index[term]:
                doc_len = self.doc_len[doc_idx]
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / self.avgdl)
                scores[doc_idx] += q_idf * numerator / denominator
        return scores


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
        helpful_count: ACE-style credit - times this node helped (NEW)
        harmful_count: ACE-style credit - times this node was harmful (NEW)
        last_used_at: Last time this node was referenced (NEW)
        usage_count: Total times this node was referenced (NEW)
    """
    id: str
    type: str  # "Entity", "Episodic", "Community"
    data: Dict[str, Any]
    embedding: Optional[List[float]] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    # ACE Credit Assignment fields
    helpful_count: int = 0
    harmful_count: int = 0
    last_used_at: Optional[str] = None
    usage_count: int = 0

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

        # BM25 index for keyword search (built lazily)
        self._bm25_index = None
        self._bm25_node_ids: List[str] = []
        self._bm25_dirty = True  # Rebuild index when nodes change

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
        self._bm25_dirty = True  # Invalidate BM25 index

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

        self._bm25_dirty = True  # Invalidate BM25 index
        return True

    # ==================== ACE Credit Assignment ====================

    def update_node_credits(self, node_ids: List[str], tag: str) -> int:
        """
        ACE-style credit assignment: Update helpful/harmful counts.

        Args:
            node_ids: List of node IDs that were referenced
            tag: 'helpful', 'harmful', or 'neutral'

        Returns:
            Number of nodes updated
        """
        updated = 0
        now = datetime.now().isoformat()

        for node_id in node_ids:
            node = self.nodes.get(node_id)
            if node:
                if tag == 'helpful':
                    node.helpful_count += 1
                elif tag == 'harmful':
                    node.harmful_count += 1
                # neutral: no count change

                node.last_used_at = now
                node.usage_count += 1
                updated += 1

        return updated

    def get_node_quality_score(self, node: Node) -> float:
        """
        Calculate node quality score (ACE-style).

        Formula: (helpful - harmful) / (helpful + harmful + 1)

        Returns:
            Quality score in range -1.0 to 1.0
            - Positive: More helpful than harmful
            - Zero: Never used or equal helpful/harmful
            - Negative: More harmful than helpful
        """
        total = node.helpful_count + node.harmful_count
        if total == 0:
            return 0.0  # Unused node is neutral
        return (node.helpful_count - node.harmful_count) / (total + 1)

    def get_high_quality_nodes(self, min_score: float = 0.3, limit: int = 20) -> List[Tuple[float, Node]]:
        """
        Get nodes with high quality scores.

        Args:
            min_score: Minimum quality score threshold
            limit: Maximum number of nodes to return

        Returns:
            List of (quality_score, node) tuples, sorted by score descending
        """
        results = []
        for node in self.nodes.values():
            score = self.get_node_quality_score(node)
            if score >= min_score:
                results.append((score, node))

        results.sort(reverse=True, key=lambda x: x[0])
        return results[:limit]

    def get_node_stats(self) -> Dict[str, Any]:
        """
        Get statistics about node quality distribution.

        Returns:
            Dictionary with quality distribution stats
        """
        stats = {
            'total_nodes': len(self.nodes),
            'high_quality': 0,     # quality > 0.5
            'neutral': 0,          # -0.3 <= quality <= 0.5
            'low_quality': 0,      # quality < -0.3
            'never_used': 0,
            'total_helpful': 0,
            'total_harmful': 0
        }

        for node in self.nodes.values():
            stats['total_helpful'] += node.helpful_count
            stats['total_harmful'] += node.harmful_count

            if node.usage_count == 0:
                stats['never_used'] += 1
            else:
                quality = self.get_node_quality_score(node)
                if quality > 0.5:
                    stats['high_quality'] += 1
                elif quality < -0.3:
                    stats['low_quality'] += 1
                else:
                    stats['neutral'] += 1

        return stats

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
            
            if score >= threshold:
                candidates.append((score, existing))
        
        if candidates:
            print(f"[Graph] Found {len(candidates)} link candidates (threshold: {threshold})")
        
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

    # ==================== BM25 Hybrid Search ====================

    def _tokenize(self, text: str) -> List[str]:
        """
        Simple tokenization for BM25 (supports Korean and English).

        Args:
            text: Text to tokenize

        Returns:
            List of tokens
        """
        # Extract alphanumeric words and Korean characters
        tokens = re.findall(r'[a-zA-Z0-9가-힣]+', text.lower())
        # Filter out single character tokens
        return [t for t in tokens if len(t) > 1]

    def _build_bm25_index(self):
        """
        Build BM25 index from all nodes.
        Called lazily when bm25_search is used.
        """
        corpus = []
        self._bm25_node_ids = []

        for node_id, node in self.nodes.items():
            # Extract text content from node
            content_parts = []
            content_parts.append(node.id)
            
            if node.data:
                for key in ['content', 'description', 'text', 'summary', 'definition', 'name']:
                    val = node.data.get(key)
                    if val and isinstance(val, str):
                        content_parts.append(val)
            
            full_text = " ".join(content_parts)
            if full_text.strip():
                tokens = self._tokenize(full_text)
                if tokens:
                    corpus.append(tokens)
                    self._bm25_node_ids.append(node_id)
        
        if corpus:
            self._bm25_index = SimpleBM25()
            self._bm25_index.fit(corpus)
        
        self._bm25_dirty = False

    def bm25_search(self, query: str, limit: int = 10) -> List[Tuple[float, Node]]:
        """
        BM25 keyword search.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of (score, node) tuples sorted by BM25 score
        """
        if self._bm25_dirty or self._bm25_index is None:
            self._build_bm25_index()

        if not self._bm25_index or not self._bm25_node_ids:
            return []

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        scores = self._bm25_index.get_scores(query_tokens)

        # Build (score, node) pairs
        results = []
        for i, score in enumerate(scores):
            if score > 0 and i < len(self._bm25_node_ids):
                node_id = self._bm25_node_ids[i]
                node = self.nodes.get(node_id)
                if node:
                    results.append((score, node))

        # Sort by score descending
        results.sort(reverse=True, key=lambda x: x[0])
        return results[:limit]

    def hybrid_search(self, query: str, limit: int = 10,
                     node_type: Optional[str] = None,
                     alpha: float = 0.7) -> List[Tuple[float, Node]]:
        """
        Hybrid search combining embedding similarity and BM25.
        Uses Reciprocal Rank Fusion (RRF) for score combination.

        Args:
            query: Search query
            limit: Maximum results
            node_type: Optional type filter
            alpha: Weight for embedding (0.0-1.0), BM25 gets (1-alpha)

        Returns:
            List of (score, node) tuples
        """
        # 1. Embedding search
        embedding_results = self.search(query, limit=limit * 2, node_type=node_type)

        # 2. BM25 search (if available)
        # 2. BM25 search
        bm25_results = self.bm25_search(query, limit=limit * 2)

        # If no BM25, fall back to embedding only
        if not bm25_results:
            return embedding_results[:limit]

        # 3. RRF (Reciprocal Rank Fusion)
        # RRF score = sum(1 / (k + rank)) for each ranking
        k = 60  # Standard RRF constant

        node_scores: Dict[str, Dict] = {}

        # Process embedding results
        for rank, (score, node) in enumerate(embedding_results):
            rrf_score = alpha * (1.0 / (k + rank + 1))
            node_scores[node.id] = {'node': node, 'score': rrf_score}

        # Process BM25 results
        for rank, (score, node) in enumerate(bm25_results):
            rrf_score = (1 - alpha) * (1.0 / (k + rank + 1))
            if node.id in node_scores:
                node_scores[node.id]['score'] += rrf_score
            else:
                node_scores[node.id] = {'node': node, 'score': rrf_score}

        # 4. Apply quality score boost (ACE integration)
        for node_id, data in node_scores.items():
            quality = self.get_node_quality_score(data['node'])
            # Quality boost: positive quality increases score, negative decreases
            data['score'] *= (1.0 + quality * 0.3)

        # 5. Sort and return
        results = [(data['score'], data['node']) for data in node_scores.values()]
        results.sort(reverse=True, key=lambda x: x[0])

        return results[:limit]

    def graph_rag_search(self, query: str, limit: int = 10,
                         node_type: Optional[str] = None,
                         hop: int = 1,
                         neighbor_boost: float = 0.8) -> List[Tuple[float, Node]]:
        """
        Graph RAG: Embedding search + Graph traversal for richer context.
        
        Combines semantic similarity with graph structure:
        1. Find seed nodes via embedding similarity
        2. Expand to connected neighbors (follow edges)
        3. Re-rank combined results
        
        Args:
            query: Search query
            limit: Maximum number of results
            node_type: Optional node type filter
            hop: Number of edge hops to follow (default: 1)
            neighbor_boost: Score multiplier for neighbor nodes (0.0-1.0)
        
        Returns:
            List of (score, node) tuples, sorted by score (descending)
        """
        # Step 1: Initial embedding search (get more seeds for expansion)
        seed_limit = max(limit // 2, 3)
        seed_results = self.search(query, limit=seed_limit, node_type=node_type)
        
        if not seed_results:
            return []
        
        # Track all nodes and their best scores
        node_scores: Dict[str, Tuple[float, Node]] = {}
        
        # Add seed nodes
        for score, node in seed_results:
            node_scores[node.id] = (score, node)
        
        # Step 2: Graph expansion - follow edges
        current_frontier = [node for _, node in seed_results]
        visited = set(node.id for node in current_frontier)
        
        for hop_num in range(hop):
            next_frontier = []
            decay = neighbor_boost ** (hop_num + 1)  # Score decays with distance
            
            for node in current_frontier:
                # Get connected neighbors via edges
                neighbors = self.find_neighbors(node.id)
                
                # Also check reverse edges (target -> source)
                for edge in self.edges:
                    if edge.target == node.id:
                        source_node = self.get_node(edge.source)
                        if source_node:
                            neighbors.append(source_node)
                
                for neighbor in neighbors:
                    if neighbor.id in visited:
                        continue
                    
                    # Apply type filter
                    if node_type is not None and neighbor.type != node_type:
                        continue
                    
                    visited.add(neighbor.id)
                    
                    # Calculate score: base it on parent's score * decay
                    parent_score = node_scores.get(node.id, (0.5, node))[0]
                    neighbor_score = parent_score * decay
                    
                    # If neighbor has embedding, also consider direct similarity
                    if neighbor.embedding is not None:
                        try:
                            query_embedding = self.get_embedding(query)
                            direct_score = self.cosine_similarity(query_embedding, neighbor.embedding)
                            # Combine: weighted average favoring direct similarity
                            neighbor_score = max(neighbor_score, direct_score * decay)
                        except:
                            pass
                    
                    node_scores[neighbor.id] = (neighbor_score, neighbor)
                    next_frontier.append(neighbor)
            
            current_frontier = next_frontier
        
        # Step 3: Sort by score and return top results
        results = list(node_scores.values())
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

    # ==================== Node Merge (Phase 4) ====================

    def find_similar_nodes(self, threshold: float = 0.85) -> List[Tuple[Node, Node, float]]:
        """
        Find pairs of nodes with high embedding similarity.
        
        Args:
            threshold: Minimum similarity threshold (0.0-1.0)
        
        Returns:
            List of (node_a, node_b, similarity) tuples
        """
        similar_pairs = []
        nodes_with_embedding = [n for n in self.nodes.values() if n.embedding]
        
        for i, node_a in enumerate(nodes_with_embedding):
            for node_b in nodes_with_embedding[i + 1:]:
                similarity = self._cosine_similarity(node_a.embedding, node_b.embedding)
                if similarity >= threshold:
                    similar_pairs.append((node_a, node_b, similarity))
        
        # Sort by similarity (highest first)
        similar_pairs.sort(key=lambda x: x[2], reverse=True)
        return similar_pairs

    def merge_nodes(self, node_a: Node, node_b: Node, 
                    merged_label: Optional[str] = None,
                    merged_content: Optional[str] = None) -> Node:
        """
        Merge two nodes into one, combining their credits and edges.
        
        Args:
            node_a: First node
            node_b: Second node (will be deleted)
            merged_label: Optional new label (defaults to node_a's label)
            merged_content: Optional merged content
        
        Returns:
            The merged node
        """
        # Create merged data
        merged_data = {**node_a.data, **node_b.data}
        if merged_content:
            merged_data['content'] = merged_content
        elif 'content' in node_a.data and 'content' in node_b.data:
            # Combine contents if both have content
            merged_data['content'] = f"{node_a.data['content']}\n---\n{node_b.data['content']}"
        
        # Keep node_a as the merged node
        node_a.label = merged_label or node_a.label
        node_a.data = merged_data
        
        # Combine credit scores (ACE integration)
        node_a.helpful_count += node_b.helpful_count
        node_a.harmful_count += node_b.harmful_count
        
        # Update last_referenced to the more recent one
        if node_b.last_referenced:
            if not node_a.last_referenced or node_b.last_referenced > node_a.last_referenced:
                node_a.last_referenced = node_b.last_referenced
        
        # Transfer edges from node_b to node_a
        edges_to_update = []
        for edge_id, edge in list(self.edges.items()):
            if edge.source == node_b.id:
                edge.source = node_a.id
                edges_to_update.append(edge)
            elif edge.target == node_b.id:
                edge.target = node_a.id
                edges_to_update.append(edge)
        
        # Remove duplicate edges (same source-target pair)
        seen_pairs = set()
        edges_to_remove = []
        for edge in self.edges.values():
            pair = (edge.source, edge.target)
            if pair in seen_pairs:
                edges_to_remove.append(edge.id)
            else:
                seen_pairs.add(pair)
        
        for edge_id in edges_to_remove:
            del self.edges[edge_id]
        
        # Delete node_b
        del self.nodes[node_b.id]
        
        # Update node_a
        self.nodes[node_a.id] = node_a
        
        # Invalidate BM25 index
        self._bm25_dirty = True
        
        # Save changes
        self._save_to_file()
        
        return node_a

    def auto_merge_similar_nodes(self, threshold: float = 0.85, 
                                  max_merges: int = 5) -> List[Dict]:
        """
        Automatically find and merge similar nodes.
        
        Args:
            threshold: Similarity threshold for merging
            max_merges: Maximum number of merges per call
        
        Returns:
            List of merge operations performed
        """
        merged_operations = []
        similar_pairs = self.find_similar_nodes(threshold)
        
        merged_ids = set()  # Track already merged nodes
        
        for node_a, node_b, similarity in similar_pairs:
            if len(merged_operations) >= max_merges:
                break
            
            # Skip if either node was already merged
            if node_a.id in merged_ids or node_b.id in merged_ids:
                continue
            
            # Perform merge (keep the one with higher quality score)
            quality_a = self.get_node_quality_score(node_a)
            quality_b = self.get_node_quality_score(node_b)
            
            if quality_b > quality_a:
                node_a, node_b = node_b, node_a  # Swap to keep higher quality
            
            merged_node = self.merge_nodes(node_a, node_b)
            
            merged_operations.append({
                'kept': node_a.id,
                'deleted': node_b.id,
                'merged_label': merged_node.label,
                'similarity': similarity,
                'new_helpful': merged_node.helpful_count,
                'new_harmful': merged_node.harmful_count
            })
            
            merged_ids.add(node_a.id)
            merged_ids.add(node_b.id)
        
        return merged_operations

    def clear(self) -> None:
        """Clear all nodes and edges (caution!)."""
        self.nodes.clear()
        self.edges.clear()
        self._embedding_cache.clear()
