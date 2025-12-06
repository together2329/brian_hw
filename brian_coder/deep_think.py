"""
Deep Think Engine for Brian Coder

Implements hypothesis branching, parallel reasoning, scoring, and convergence.
Inspired by Gemini's Deep Think mode and parallel reasoning research.

Pipeline:
1. BRANCHING: Generate multiple hypotheses/strategies
2. PARALLEL REASONING: Simulate each hypothesis (run first_action)
3. SCORING: Multi-dimensional evaluation (experience, knowledge, coherence)
4. CONVERGENCE: Select best hypothesis

Zero-dependency (stdlib only + concurrent.futures for parallelism).
"""

import json
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError

import config


# ============================================================
# Data Classes
# ============================================================

@dataclass
class Hypothesis:
    """
    Single hypothesis/strategy for solving a task.

    Attributes:
        id: Unique identifier
        strategy_name: Short name (e.g., "modular", "incremental", "debug-first")
        description: Brief description of the approach
        first_action: First tool call to execute (e.g., "read_file(path='main.py')")
        reasoning: Why this approach might work
        confidence: Initial confidence score (0.0-1.0)
        scores: Dictionary of dimensional scores
        final_score: Weighted final score
        simulation_result: Result of running first_action (if simulation enabled)
    """
    id: str
    strategy_name: str
    description: str
    first_action: str
    reasoning: str
    confidence: float = 0.5
    scores: Dict[str, float] = field(default_factory=dict)
    final_score: float = 0.0
    simulation_result: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class DeepThinkResult:
    """
    Result of Deep Think pipeline execution.

    Attributes:
        selected_hypothesis: The chosen hypothesis
        all_hypotheses: All generated hypotheses with scores
        reasoning_log: Log of the reasoning process
        total_time_ms: Total execution time in milliseconds
        referenced_node_ids: ACE-style credit - node IDs used during scoring (NEW)
    """
    selected_hypothesis: Hypothesis
    all_hypotheses: List[Hypothesis]
    reasoning_log: List[str]
    total_time_ms: int
    referenced_node_ids: List[str] = field(default_factory=list)  # ACE Credit Assignment


# ============================================================
# Hypothesis Brancher
# ============================================================

class HypothesisBrancher:
    """
    Generates multiple hypotheses/strategies for a given task.
    Uses LLM to propose diverse approaches.
    """

    def __init__(self, llm_call_func: Callable = None):
        """
        Args:
            llm_call_func: Function to call LLM (signature: func(prompt, temperature=0.7) -> str)
        """
        self.llm_call_func = llm_call_func

    def branch(self, task: str, context: str, num_hypotheses: int = 3) -> List[Hypothesis]:
        """
        Generate multiple hypotheses for solving the task.

        Args:
            task: User's task description
            context: Current context (file list, recent conversation, etc.)
            num_hypotheses: Number of hypotheses to generate

        Returns:
            List of Hypothesis objects
        """
        if not self.llm_call_func:
            return [self._create_default_hypothesis()]

        prompt = f"""You are analyzing a coding task. Generate {num_hypotheses} DIFFERENT approaches to solve it.

TASK: {task}

CONTEXT:
{context[:1000]}

For each approach, provide a JSON object with:
- strategy_name: Short identifier (e.g., "modular", "incremental", "debug-first", "rewrite")
- description: 1-2 sentence description
- first_action: The EXACT first tool call (e.g., "read_file(path='main.py')" or "grep_file(pattern='error', path='.')")
- reasoning: Why this approach might work

IMPORTANT:
- Make approaches DIVERSE (different starting points, different tools)
- first_action must be a valid tool call syntax
- Available tools: read_file, write_file, grep_file, list_dir, run_command, find_files

Return ONLY a JSON array:
[{{"strategy_name": "...", "description": "...", "first_action": "...", "reasoning": "..."}}]

Different approaches (JSON only):"""

        try:
            response = self.llm_call_func(prompt, temperature=config.DEEP_THINK_TEMPERATURE)

            # Parse JSON from response
            start_idx = response.find('[')
            end_idx = response.rfind(']') + 1

            if start_idx != -1 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                approaches = json.loads(json_str)

                hypotheses = []
                for i, approach in enumerate(approaches[:num_hypotheses]):
                    hyp = Hypothesis(
                        id=f"hyp_{i}_{datetime.now().strftime('%H%M%S')}",
                        strategy_name=approach.get("strategy_name", f"approach_{i}"),
                        description=approach.get("description", ""),
                        first_action=approach.get("first_action", ""),
                        reasoning=approach.get("reasoning", ""),
                        confidence=0.5 + (0.1 * (num_hypotheses - i) / num_hypotheses)  # Slight ordering preference
                    )
                    hypotheses.append(hyp)

                return hypotheses if hypotheses else [self._create_default_hypothesis()]

        except Exception as e:
            print(f"[Deep Think] Branching failed: {e}")

        return [self._create_default_hypothesis()]

    def _create_default_hypothesis(self) -> Hypothesis:
        """Create a fallback hypothesis when branching fails."""
        return Hypothesis(
            id="hyp_fallback",
            strategy_name="default",
            description="Standard sequential approach",
            first_action="list_dir(path='.')",
            reasoning="Fallback to exploring current directory",
            confidence=0.3
        )


# ============================================================
# Parallel Reasoner
# ============================================================

class ParallelReasoner:
    """
    Runs simulation for each hypothesis by executing its first_action.
    Uses ThreadPoolExecutor for parallel execution.
    """

    # Read-only tools that are safe to run in parallel
    SAFE_PARALLEL_TOOLS = {
        'read_file', 'read_lines', 'grep_file', 'list_dir',
        'find_files', 'git_status', 'git_diff', 'get_plan',
        'rag_search', 'rag_status'
    }

    def __init__(self, execute_tool_func: Callable = None):
        """
        Args:
            execute_tool_func: Function to execute tools (signature: func(tool_name, args_str) -> str)
        """
        self.execute_tool_func = execute_tool_func

    def simulate(self, hypothesis: Hypothesis) -> str:
        """
        Run simulation for a single hypothesis.

        Args:
            hypothesis: Hypothesis to simulate

        Returns:
            Simulation result string
        """
        if not self.execute_tool_func or not hypothesis.first_action:
            return "No simulation (no tool function or action)"

        # Parse tool name from first_action
        tool_name = self._extract_tool_name(hypothesis.first_action)

        if not tool_name:
            return "Invalid action format"

        # Check if tool is safe for parallel execution
        if tool_name not in self.SAFE_PARALLEL_TOOLS:
            return f"Skipped (write tool: {tool_name})"

        try:
            # Parse the action to extract tool name and args
            match = re.match(r'(\w+)\((.*)\)$', hypothesis.first_action, re.DOTALL)
            if match:
                tool_name = match.group(1)
                args_str = match.group(2)

                result = self.execute_tool_func(tool_name, args_str)

                # Truncate long results
                if len(result) > 500:
                    result = result[:500] + "... (truncated)"

                return f"SUCCESS: {result}"
            else:
                return "Invalid action syntax"

        except Exception as e:
            return f"ERROR: {str(e)[:200]}"

    def _extract_tool_name(self, action: str) -> Optional[str]:
        """Extract tool name from action string."""
        match = re.match(r'(\w+)\(', action)
        return match.group(1) if match else None

    def run_all_parallel(self, hypotheses: List[Hypothesis], timeout: int = None) -> List[Hypothesis]:
        """
        Run simulation for all hypotheses in parallel.

        Args:
            hypotheses: List of hypotheses to simulate
            timeout: Timeout per hypothesis in seconds

        Returns:
            List of hypotheses with simulation_result filled
        """
        if not self.execute_tool_func:
            for h in hypotheses:
                h.simulation_result = "Simulation disabled (no execute function)"
            return hypotheses

        timeout = timeout or config.DEEP_THINK_TOOL_TIMEOUT

        with ThreadPoolExecutor(max_workers=len(hypotheses)) as executor:
            future_to_hyp = {
                executor.submit(self.simulate, h): h
                for h in hypotheses
            }

            for future in as_completed(future_to_hyp, timeout=timeout * 2):
                hypothesis = future_to_hyp[future]
                try:
                    hypothesis.simulation_result = future.result(timeout=timeout)
                except TimeoutError:
                    hypothesis.simulation_result = "TIMEOUT"
                except Exception as e:
                    hypothesis.simulation_result = f"ERROR: {str(e)[:100]}"

        return hypotheses


# ============================================================
# Hypothesis Scorer
# ============================================================

class HypothesisScorer:
    """
    Scores hypotheses using multiple dimensions:
    1. Experience (ProceduralMemory)
    2. Knowledge (GraphLite)
    3. Coherence (LLM judgment)
    4. Simulation result
    5. Initial confidence
    """

    def __init__(self,
                 procedural_memory=None,
                 graph_lite=None,
                 llm_call_func: Callable = None):
        """
        Args:
            procedural_memory: ProceduralMemory instance for experience-based scoring
            graph_lite: GraphLite instance for knowledge-based scoring
            llm_call_func: LLM function for coherence scoring
        """
        self.procedural_memory = procedural_memory
        self.graph_lite = graph_lite
        self.llm_call_func = llm_call_func

    def score_experience(self, hypothesis: Hypothesis, task: str) -> float:
        """
        Score based on past similar experiences.

        Returns:
            float: Experience score (0.0-1.0)
        """
        if not self.procedural_memory:
            return 0.5  # Neutral score when no memory available

        try:
            # Search for similar past trajectories
            search_query = f"{task} {hypothesis.strategy_name}"
            similar_trajs = self.procedural_memory.retrieve(search_query, limit=3)

            if not similar_trajs:
                return 0.5

            # Weighted average of success rates
            total_weight = 0
            weighted_success = 0

            for similarity, traj in similar_trajs:
                weight = similarity
                weighted_success += weight * traj.success_rate
                total_weight += weight

            if total_weight == 0:
                return 0.5

            return weighted_success / total_weight

        except Exception as e:
            return 0.5

    def score_knowledge(self, hypothesis: Hypothesis) -> Tuple[float, List[str]]:
        """
        Score based on related knowledge in the graph.

        Returns:
            Tuple[float, List[str]]: (Knowledge score 0.0-1.0, List of referenced node IDs)
        """
        if not self.graph_lite:
            return 0.5, []

        try:
            # Search knowledge graph
            query = f"{hypothesis.strategy_name} {hypothesis.description}"
            results = self.graph_lite.search(query, limit=5)

            if not results:
                return 0.5, []

            # ACE Credit Assignment: Track referenced node IDs
            referenced_ids = [node.id for score, node in results[:5]]

            # Average similarity of top results
            scores = [score for score, _ in results[:5]]
            return sum(scores) / len(scores), referenced_ids

        except Exception as e:
            return 0.5, []

    def score_coherence(self, hypothesis: Hypothesis, task: str) -> float:
        """
        Score logical coherence using LLM.

        Returns:
            float: Coherence score (0.0-1.0)
        """
        if not self.llm_call_func:
            return 0.5

        prompt = f"""Rate the logical coherence of this approach (0.0-1.0):

TASK: {task}

APPROACH: {hypothesis.strategy_name}
DESCRIPTION: {hypothesis.description}
FIRST ACTION: {hypothesis.first_action}
REASONING: {hypothesis.reasoning}

Consider:
1. Does the approach directly address the task?
2. Is the first action appropriate for this strategy?
3. Is the reasoning sound?

Return ONLY a decimal number between 0.0 and 1.0:"""

        try:
            response = self.llm_call_func(prompt, temperature=0.1)

            # Extract number from response
            match = re.search(r'(0?\.\d+|1\.0|0|1)', response.strip())
            if match:
                score = float(match.group(1))
                return min(1.0, max(0.0, score))

        except Exception as e:
            pass

        return 0.5

    def score_simulation(self, hypothesis: Hypothesis) -> float:
        """
        Score based on simulation result.

        Returns:
            float: Simulation score (0.0-1.0)
        """
        if not hypothesis.simulation_result:
            return 0.5

        result = hypothesis.simulation_result.lower()

        # Keyword-based scoring
        if result.startswith("success"):
            return 0.8
        elif "timeout" in result:
            return 0.3
        elif result.startswith("error"):
            return 0.2
        elif "skipped" in result:
            return 0.5  # Neutral for skipped write tools

        return 0.5

    def score_all(self, hypotheses: List[Hypothesis], task: str) -> Tuple[List[Hypothesis], List[str]]:
        """
        Calculate all dimension scores and final weighted score.

        Returns:
            Tuple[List[Hypothesis], List[str]]: (Hypotheses with scores, All referenced node IDs)
        """
        all_referenced_ids = []  # ACE Credit Assignment

        for h in hypotheses:
            # Calculate each dimension
            h.scores['experience'] = self.score_experience(h, task)

            # ACE: score_knowledge now returns (score, node_ids)
            knowledge_score, node_ids = self.score_knowledge(h)
            h.scores['knowledge'] = knowledge_score
            all_referenced_ids.extend(node_ids)

            h.scores['coherence'] = self.score_coherence(h, task)
            h.scores['simulation'] = self.score_simulation(h)
            h.scores['confidence'] = h.confidence

            # Calculate weighted final score
            h.final_score = (
                config.DEEP_THINK_WEIGHT_EXPERIENCE * h.scores['experience'] +
                config.DEEP_THINK_WEIGHT_KNOWLEDGE * h.scores['knowledge'] +
                config.DEEP_THINK_WEIGHT_COHERENCE * h.scores['coherence'] +
                config.DEEP_THINK_WEIGHT_SIMULATION * h.scores['simulation'] +
                config.DEEP_THINK_WEIGHT_CONFIDENCE * h.scores['confidence']
            )

        # Remove duplicates while preserving order
        seen = set()
        unique_ids = [x for x in all_referenced_ids if not (x in seen or seen.add(x))]

        return hypotheses, unique_ids


# ============================================================
# Hypothesis Selector
# ============================================================

class HypothesisSelector:
    """
    Selects the best hypothesis based on scores.
    """

    def __init__(self, llm_call_func: Callable = None):
        self.llm_call_func = llm_call_func

    def select_best(self, hypotheses: List[Hypothesis]) -> Hypothesis:
        """
        Select hypothesis with highest final score.

        Args:
            hypotheses: List of scored hypotheses

        Returns:
            Best hypothesis
        """
        if not hypotheses:
            raise ValueError("No hypotheses to select from")

        # Sort by final score (descending)
        sorted_hypotheses = sorted(hypotheses, key=lambda h: h.final_score, reverse=True)
        return sorted_hypotheses[0]

    def select_top_k(self, hypotheses: List[Hypothesis], k: int = 2) -> List[Hypothesis]:
        """
        Select top k hypotheses.

        Args:
            hypotheses: List of scored hypotheses
            k: Number of top hypotheses to return

        Returns:
            Top k hypotheses
        """
        sorted_hypotheses = sorted(hypotheses, key=lambda h: h.final_score, reverse=True)
        return sorted_hypotheses[:k]


# ============================================================
# Deep Think Engine
# ============================================================

class DeepThinkEngine:
    """
    Main engine that orchestrates the 4-stage Deep Think pipeline.

    Pipeline:
    1. BRANCHING → Generate hypotheses
    2. SIMULATION → Run first_action for each (parallel)
    3. SCORING → Multi-dimensional evaluation
    4. SELECTION → Choose best hypothesis
    """

    def __init__(self,
                 procedural_memory=None,
                 graph_lite=None,
                 llm_call_func: Callable = None,
                 execute_tool_func: Callable = None):
        """
        Args:
            procedural_memory: ProceduralMemory instance
            graph_lite: GraphLite instance
            llm_call_func: LLM call function
            execute_tool_func: Tool execution function
        """
        self.brancher = HypothesisBrancher(llm_call_func)
        self.reasoner = ParallelReasoner(execute_tool_func)
        self.scorer = HypothesisScorer(procedural_memory, graph_lite, llm_call_func)
        self.selector = HypothesisSelector(llm_call_func)
        self.llm_call_func = llm_call_func

    def think(self, task: str, context: str = "",
              num_hypotheses: int = None,
              enable_simulation: bool = None) -> DeepThinkResult:
        """
        Execute the full Deep Think pipeline.

        Args:
            task: User's task description
            context: Current context
            num_hypotheses: Number of hypotheses (default from config)
            enable_simulation: Whether to run simulation (default from config)

        Returns:
            DeepThinkResult with selected hypothesis and reasoning log
        """
        start_time = time.time()
        reasoning_log = []

        num_hypotheses = num_hypotheses or config.DEEP_THINK_NUM_HYPOTHESES
        enable_simulation = enable_simulation if enable_simulation is not None else config.DEEP_THINK_ENABLE_SIMULATION

        # ========== PHASE 1: BRANCHING ==========
        reasoning_log.append("[Phase 1] Generating hypotheses...")
        hypotheses = self.brancher.branch(task, context, num_hypotheses)
        reasoning_log.append(f"  Generated {len(hypotheses)} hypotheses:")

        for h in hypotheses:
            reasoning_log.append(f"  - {h.strategy_name}: {h.description[:60]}...")

        # ========== PHASE 2: SIMULATION ==========
        if enable_simulation:
            reasoning_log.append("\n[Phase 2] Running simulations (parallel)...")
            hypotheses = self.reasoner.run_all_parallel(hypotheses)

            for h in hypotheses:
                result_preview = (h.simulation_result or "None")[:80]
                reasoning_log.append(f"  - {h.strategy_name}: {result_preview}")
        else:
            reasoning_log.append("\n[Phase 2] Simulation disabled")

        # ========== PHASE 3: SCORING ==========
        reasoning_log.append("\n[Phase 3] Scoring hypotheses...")
        # ACE Credit Assignment: score_all now returns (hypotheses, referenced_node_ids)
        hypotheses, referenced_node_ids = self.scorer.score_all(hypotheses, task)

        for h in hypotheses:
            scores_str = ", ".join([f"{k}={v:.2f}" for k, v in h.scores.items()])
            reasoning_log.append(f"  - {h.strategy_name}: final={h.final_score:.3f} ({scores_str})")

        # Log referenced nodes for credit assignment
        if referenced_node_ids:
            reasoning_log.append(f"  [ACE] Referenced {len(referenced_node_ids)} knowledge nodes")

        # ========== PHASE 4: SELECTION ==========
        reasoning_log.append("\n[Phase 4] Selecting best hypothesis...")
        selected = self.selector.select_best(hypotheses)
        reasoning_log.append(f"  Selected: {selected.strategy_name} (score: {selected.final_score:.3f})")

        # Calculate total time
        elapsed_ms = int((time.time() - start_time) * 1000)
        reasoning_log.append(f"\n[Complete] Total time: {elapsed_ms}ms")

        return DeepThinkResult(
            selected_hypothesis=selected,
            all_hypotheses=hypotheses,
            reasoning_log=reasoning_log,
            total_time_ms=elapsed_ms,
            referenced_node_ids=referenced_node_ids  # ACE Credit Assignment
        )

    def format_strategy_guidance(self, result: DeepThinkResult) -> str:
        """
        Format the selected strategy as guidance for the ReAct loop.

        Args:
            result: DeepThinkResult from think()

        Returns:
            Formatted guidance string to inject into messages
        """
        h = result.selected_hypothesis

        # Build alternatives summary
        alternatives = []
        for hyp in result.all_hypotheses:
            if hyp.id != h.id:
                alternatives.append(f"  - {hyp.strategy_name}: {hyp.final_score:.2f}")

        guidance = f"""
=== DEEP THINK ANALYSIS ===
Selected Strategy: {h.strategy_name}
Score: {h.final_score:.3f}
Description: {h.description}
Reasoning: {h.reasoning}

Recommended First Action: {h.first_action}

Alternative Approaches (not selected):
{chr(10).join(alternatives) if alternatives else "  None"}

Follow the selected strategy. If it fails, consider alternatives.
===========================
"""
        return guidance


# ============================================================
# Utility Functions
# ============================================================

def format_deep_think_output(result: DeepThinkResult, verbose: bool = False) -> str:
    """
    Format Deep Think result for console output.

    Args:
        result: DeepThinkResult
        verbose: Include full reasoning log

    Returns:
        Formatted string for display
    """
    output = []
    output.append("\n" + "="*60)
    output.append("DEEP THINK ANALYSIS")
    output.append("="*60)

    # Selected hypothesis
    h = result.selected_hypothesis
    output.append(f"\nSelected Strategy: {h.strategy_name}")
    output.append(f"  Score: {h.final_score:.3f}")
    output.append(f"  Description: {h.description}")
    output.append(f"  First Action: {h.first_action}")

    # All hypotheses scores
    output.append(f"\nAll Hypotheses ({len(result.all_hypotheses)}):")
    for hyp in sorted(result.all_hypotheses, key=lambda x: x.final_score, reverse=True):
        marker = "→" if hyp.id == h.id else " "
        output.append(f"  {marker} {hyp.strategy_name}: {hyp.final_score:.3f}")

    # Timing
    output.append(f"\nTotal Time: {result.total_time_ms}ms")

    if verbose:
        output.append("\n" + "-"*40)
        output.append("REASONING LOG:")
        output.append("-"*40)
        output.extend(result.reasoning_log)

    output.append("="*60 + "\n")

    return "\n".join(output)
