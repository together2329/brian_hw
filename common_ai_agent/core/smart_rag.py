"""
Smart RAG Decision Module

2-stage RAG decision strategy:
- Stage 1: Always perform RAG search (fast and cheap)
- Stage 2: Decide to use results based on score threshold

Score-based decision:
- score >= HIGH_THRESHOLD: Use directly
- LOW_THRESHOLD < score < HIGH_THRESHOLD: Ask LLM to judge relevance
- score < LOW_THRESHOLD: Ignore
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Optional, Tuple, List, Any


class SmartRAGDecision:
    """
    Smart RAG decision maker that automatically determines
    whether to include RAG context based on relevance scores.
    """
    
    def __init__(
        self,
        high_threshold: float = 0.8,
        low_threshold: float = 0.5,
        top_k: int = 3,
        debug: bool = False
    ):
        """
        Initialize Smart RAG Decision.
        
        Args:
            high_threshold: Score above this -> use directly
            low_threshold: Score below this -> ignore
            top_k: Number of results to consider
            debug: Enable debug output
        """
        self.high_threshold = high_threshold
        self.low_threshold = low_threshold
        self.top_k = top_k
        self.debug = debug
    
    def decide(
        self,
        query: str,
        rag_search_func: callable,
        llm_judge_func: Optional[callable] = None
    ) -> Tuple[bool, List[Any]]:
        """
        Decide whether to use RAG results for the given query.
        
        Args:
            query: User query to search for
            rag_search_func: Function to perform RAG search
            llm_judge_func: Optional LLM function for mid-score judgment
            
        Returns:
            Tuple of (should_use: bool, results: list)
        """
        if not query or not query.strip():
            return False, []
        
        # Stage 1: Always perform RAG search
        try:
            results = rag_search_func(query, limit=self.top_k)
        except Exception as e:
            if self.debug:
                print(f"[SmartRAG] Search error: {e}")
            return False, []
        
        if not results:
            if self.debug:
                print(f"[SmartRAG] No results for query: {query[:50]}...")
            return False, []
        
        # Get top score
        # Results format: [(score, chunk), ...] from rag_db
        if isinstance(results[0], tuple):
            top_score = results[0][0]
        else:
            # Fallback for different result formats
            top_score = getattr(results[0], 'score', 0.0)
        
        if self.debug:
            print(f"[SmartRAG] Query: {query[:50]}... | Top score: {top_score:.3f}")
        
        # Stage 2: Score-based decision
        if top_score >= self.high_threshold:
            if self.debug:
                print(f"[SmartRAG] HIGH score ({top_score:.3f} >= {self.high_threshold}) -> Using RAG context")
            return True, results
        
        if top_score < self.low_threshold:
            if self.debug:
                print(f"[SmartRAG] LOW score ({top_score:.3f} < {self.low_threshold}) -> Ignoring RAG")
            return False, []
        
        # Mid-score: Ask LLM to judge if function provided
        if llm_judge_func:
            if self.debug:
                print(f"[SmartRAG] MID score ({top_score:.3f}) -> Asking LLM to judge relevance")
            
            should_use = self._llm_judge_relevance(query, results, llm_judge_func)
            
            if self.debug:
                decision = "Using" if should_use else "Ignoring"
                print(f"[SmartRAG] LLM decision: {decision} RAG context")
            
            return should_use, results if should_use else []
        
        # No LLM judge available, use conservative approach
        if self.debug:
            print(f"[SmartRAG] MID score, no LLM judge -> Using RAG context (conservative)")
        return True, results
    
    def _llm_judge_relevance(
        self,
        query: str,
        results: List[Any],
        llm_func: callable
    ) -> bool:
        """
        Ask LLM to judge if RAG results are relevant to the query.
        
        Args:
            query: Original user query
            results: RAG search results
            llm_func: LLM function to call
            
        Returns:
            True if relevant, False otherwise
        """
        # Format results for LLM
        results_summary = []
        for i, item in enumerate(results[:3], 1):
            if isinstance(item, tuple):
                score, chunk = item
                source = getattr(chunk, 'source_file', 'unknown')
                preview = getattr(chunk, 'content', '')[:100]
            else:
                score = getattr(item, 'score', 0.0)
                source = getattr(item, 'source_file', 'unknown')
                preview = getattr(item, 'content', '')[:100]
            
            results_summary.append(f"{i}. [{os.path.basename(source)}] (score: {score:.2f})\n   {preview}...")
        
        prompt = f"""다음 검색 결과가 사용자 질문에 도움이 되는지 판단하세요.

질문: {query}

검색 결과:
{''.join(results_summary)}

이 검색 결과가 질문에 답하는 데 관련이 있습니까?
관련 있으면 "YES", 관련 없으면 "NO"만 응답하세요."""

        try:
            response = llm_func(prompt)
            return "YES" in response.upper()
        except Exception as e:
            if self.debug:
                print(f"[SmartRAG] LLM judge error: {e}")
            # On error, conservatively include results
            return True
    
    def format_context(self, results: List[Any], max_chars: int = 2000) -> str:
        """
        Format RAG results as context string for system prompt.
        
        Args:
            results: RAG search results
            max_chars: Maximum characters for context
            
        Returns:
            Formatted context string
        """
        if not results:
            return ""
        
        context_parts = ["=== RELEVANT CODE/SPEC CONTEXT ===\n"]
        total_chars = 0
        
        for item in results:
            if isinstance(item, tuple):
                score, chunk = item
            else:
                score = getattr(item, 'score', 0.0)
                chunk = item
            
            source = getattr(chunk, 'source_file', 'unknown')
            category = getattr(chunk, 'category', 'unknown')
            start_line = getattr(chunk, 'start_line', 0)
            end_line = getattr(chunk, 'end_line', 0)
            content = getattr(chunk, 'content', '')
            
            # Truncate content if needed
            if len(content) > 500:
                content = content[:500] + "..."
            
            entry = f"\n[{category.upper()}] {os.path.basename(source)} (L{start_line}-{end_line}) | Relevance: {score:.2f}\n"
            entry += f"```\n{content}\n```\n"
            
            if total_chars + len(entry) > max_chars:
                break
            
            context_parts.append(entry)
            total_chars += len(entry)
        
        context_parts.append("\n================================\n")
        
        return "".join(context_parts)


def get_smart_rag_decision(config_module=None) -> Optional[SmartRAGDecision]:
    """
    Factory function to create SmartRAGDecision from config.
    
    Args:
        config_module: Config module (uses src.config if not provided)
        
    Returns:
        SmartRAGDecision instance or None if disabled
    """
    if config_module is None:
        try:
            import config as config_module
        except ImportError:
            return None
    
    if not getattr(config_module, 'ENABLE_SMART_RAG', False):
        return None
    
    return SmartRAGDecision(
        high_threshold=getattr(config_module, 'SMART_RAG_HIGH_THRESHOLD', 0.8),
        low_threshold=getattr(config_module, 'SMART_RAG_LOW_THRESHOLD', 0.5),
        top_k=getattr(config_module, 'SMART_RAG_TOP_K', 3),
        debug=getattr(config_module, 'DEBUG_MODE', False)
    )
