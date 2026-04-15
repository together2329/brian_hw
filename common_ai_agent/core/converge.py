"""
core/converge.py — Generic YAML-driven converge engine

Domain-agnostic converge loop controller. Reads a converge.yaml config
and drives a multi-stage pipeline: execute → parse → score → classify →
fix → retry, until convergence criteria are met.

NO EDA-SPECIFIC CODE — all domain knowledge comes from YAML config.

Components:
  - ScoreCalculator: compute float score from metrics using YAML weights
  - OutputParser: extract metrics from sub-agent output using YAML parsers
  - ClassifierEngine: classify failures using YAML pattern matchers
  - FeedbackRouter: lookup fix steps from YAML feedback graph
  - LoopController: the main driver orchestrating the full loop

Uses:
  - core/project.py: Project model (state container)
  - core/job.py: Job model (per-execution tracking)
  - core/agent_runner.py: run_agent_session() for sub-agent execution
"""

import os
import sys
import re
import json
import time
import shutil
import traceback
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

# Ensure import paths
_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_script_dir)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)


# ============================================================
# Score Calculator
# ============================================================

class ScoreCalculator:
    """
    Compute a float score from metrics using YAML-defined weights.

    Weight key convention:
      - 'lint_errors': multiply by count of errors (negative = penalty)
      - 'sim_pass_ratio': multiply by pass/total ratio (positive = reward)
      - 'sim_has_failures': flat penalty if any failures exist
    """

    def __init__(self, weights: Dict[str, float]):
        self.weights = weights

    def compute(self, metrics: Dict[str, Any]) -> float:
        """Compute weighted score from flattened metrics."""
        flat = {}
        self._flatten(metrics, flat)

        score = 0.0
        for weight_key, weight_val in self.weights.items():
            metric_val = flat.get(weight_key, 0)

            # Special handling for ratio-based weights
            if weight_key.endswith("_ratio"):
                metric_val = self._compute_ratio(weight_key, metrics)
            elif weight_key.endswith(".has_failures") or weight_key.endswith(".has_errors") or weight_key == "has_failures" or weight_key == "has_errors":
                # Derived: check if base.fail or base.errors > 0
                # Weight key like "sim.has_failures" -> base = "sim"
                parts = weight_key.rsplit(".", 1)
                if len(parts) == 2:
                    base = parts[0]  # "sim"
                else:
                    base = ""
                suffix = parts[-1]  # "has_failures" or "has_errors"
                if "failures" in suffix:
                    fail_key = f"{base}.fail" if base else "sim.fail"
                else:
                    fail_key = f"{base}.errors" if base else "lint.errors"
                fail_val = flat.get(fail_key, 0)
                metric_val = 1 if int(fail_val) > 0 else 0
            elif weight_key.endswith("_pct") or weight_key.endswith("_percent"):
                metric_val = float(metric_val) / 100.0 if metric_val else 0.0

            score += weight_val * metric_val

        return score

    def _compute_ratio(self, key: str, metrics: Dict) -> float:
        """Compute pass/total ratio for common patterns."""
        flat = {}
        self._flatten(metrics, flat)

        # "sim.pass_ratio" -> base="sim", field="pass"
        parts = key.rsplit(".", 1)
        if len(parts) == 2:
            base = parts[0]  # "sim"
        else:
            base = ""

        pass_val = flat.get(f"{base}.pass", flat.get("sim.pass", 0))
        fail_val = flat.get(f"{base}.fail", flat.get("sim.fail", 0))
        total_val = flat.get(f"{base}.total", flat.get("sim.tests", pass_val + fail_val))

        if total_val <= 0:
            return 0.0
        return float(pass_val) / float(total_val)

    @staticmethod
    def _flatten(d: Dict, out: Dict, prefix: str = "") -> None:
        for k, v in d.items():
            full_key = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                ScoreCalculator._flatten(v, out, full_key)
            else:
                out[full_key] = v


# ============================================================
# Output Parser
# ============================================================

class OutputParser:
    """
    Extract structured metrics from sub-agent raw output using YAML parser configs.

    Parser types:
      - count_patterns: count regex matches for each pattern
      - structured: extract fields using count/extract methods
      - regex_groups: extract named groups with type casting
    """

    def parse(self, raw_output: str,
              parser_config: Any) -> Dict[str, Any]:
        """
        Parse raw sub-agent output into metrics dict.

        Args:
            raw_output: The full text output from run_agent_session()
            parser_config: ParserConfig instance with type, fields, patterns

        Returns:
            Dict of extracted metrics (e.g., {"lint.errors": 3, "sim.pass": 5})
        """
        if parser_config is None:
            return {}

        ptype = getattr(parser_config, 'parser_type', 'count_patterns')

        if ptype == "count_patterns":
            return self._parse_count_patterns(raw_output, parser_config)
        elif ptype == "structured":
            return self._parse_structured(raw_output, parser_config)
        elif ptype == "regex_groups":
            return self._parse_regex_groups(raw_output, parser_config)

        return {}

    def _parse_count_patterns(self, output: str,
                               config: Any) -> Dict[str, Any]:
        """Count occurrences of each pattern."""
        patterns = getattr(config, 'patterns', {})
        results = {}
        for name, pattern in patterns.items():
            try:
                count = len(re.findall(pattern, output))
                results[name] = count
            except re.error:
                results[name] = 0
        return results

    def _parse_structured(self, output: str,
                          config: Any) -> Dict[str, Any]:
        """Extract structured fields using regex with count/extract methods."""
        fields = getattr(config, 'fields', {})
        results = {}

        for field_name, field_spec in fields.items():
            if isinstance(field_spec, str):
                # Simple regex string
                regex = field_spec
                method = "count"
            elif isinstance(field_spec, dict):
                regex = field_spec.get("regex", "")
                method = field_spec.get("method", "count")
            else:
                continue

            if not regex:
                continue

            try:
                if method == "count":
                    results[field_name] = len(re.findall(regex, output))
                elif method == "extract":
                    m = re.search(regex, output)
                    results[field_name] = m.group(1).strip() if m else ""
                elif method == "extract_all":
                    results[field_name] = [m.group(1).strip()
                                           for m in re.finditer(regex, output)]
                elif method == "first":
                    m = re.search(regex, output)
                    results[field_name] = m.group(0) if m else ""
            except (re.error, IndexError, AttributeError):
                results[field_name] = 0 if method == "count" else ""

        return results

    def _parse_regex_groups(self, output: str,
                            config: Any) -> Dict[str, Any]:
        """Extract named regex groups with type casting."""
        fields = getattr(config, 'fields', {})
        results = {}

        for field_name, field_spec in fields.items():
            if isinstance(field_spec, dict):
                regex = field_spec.get("regex", "")
                cast = field_spec.get("cast", "str")
            else:
                regex = str(field_spec)
                cast = "str"

            if not regex:
                continue

            try:
                m = re.search(regex, output)
                if m:
                    raw_val = m.group(1) if m.lastindex else m.group(0)
                    results[field_name] = self._cast(raw_val, cast)
                else:
                    results[field_name] = 0 if cast in ("int", "float") else ""
            except (re.error, IndexError, AttributeError):
                results[field_name] = 0 if cast in ("int", "float") else ""

        return results

    @staticmethod
    def _cast(value: str, type_name: str) -> Any:
        try:
            if type_name == "int":
                return int(float(value))
            elif type_name == "float":
                return float(value)
            return str(value)
        except (ValueError, TypeError):
            return 0 if type_name in ("int", "float") else ""


# ============================================================
# Classifier Engine
# ============================================================

class ClassifierEngine:
    """
    Classify sub-agent output using YAML-defined pattern rules.

    Iterates classifiers in order. First matching rule wins.
    Returns the classifier label, or "" if no match.
    """

    def __init__(self, classifiers: list):
        self.classifiers = classifiers  # List[ClassifierRule]

    def classify(self, output: str,
                 context: Optional[Dict[str, Any]] = None) -> str:
        """
        Classify output by matching against classifier patterns.

        Args:
            output: Raw sub-agent output text
            context: Optional dict with runtime context (e.g., iteration counts)

        Returns:
            Classifier label string, or "" if no match
        """
        output_lower = output.lower()
        context = context or {}

        for rule in self.classifiers:
            patterns = getattr(rule, 'patterns', [])
            condition = getattr(rule, 'condition', '')
            label = getattr(rule, 'label', '')

            # Check if all patterns are found in output
            matched = False
            for pattern in patterns:
                if pattern.lower() in output_lower:
                    matched = True
                    break  # any pattern match is enough

            if not matched:
                continue

            # Check optional condition
            if condition and not self._eval_condition(condition, context):
                continue

            return label

        return ""

    def _eval_condition(self, condition: str,
                        context: Dict[str, Any]) -> bool:
        """Evaluate a simple condition expression."""
        # Support: "sim.iterations < 3", "stage.retry >= 2"
        # Parse: lhs op rhs
        for op in [">=", "<=", "!=", ">", "<", "=="]:
            if op in condition:
                parts = condition.split(op, 1)
                lhs_key = parts[0].strip()
                rhs_val = parts[1].strip()

                # Resolve LHS from context
                lhs_val = context.get(lhs_key, context.get(lhs_key.replace(".", "_"), 0))

                try:
                    if op == ">=": return float(lhs_val) >= float(rhs_val)
                    elif op == "<=": return float(lhs_val) <= float(rhs_val)
                    elif op == ">": return float(lhs_val) > float(rhs_val)
                    elif op == "<": return float(lhs_val) < float(rhs_val)
                    elif op == "==": return str(lhs_val) == rhs_val
                    elif op == "!=": return str(lhs_val) != rhs_val
                except (ValueError, TypeError):
                    return False

        return True  # no recognizable operator → always true


# ============================================================
# Feedback Router
# ============================================================

class FeedbackRouter:
    """
    Route a classified failure to the correct fix step using
    the YAML feedback graph.

    Lookup: match (trigger_stage, classifier_label or condition)
    Returns: the matching FeedbackEdge, or None
    """

    def __init__(self, edges: list):
        self.edges = edges  # List[FeedbackEdge]

    def lookup(self, stage: str, classifier_label: str = "",
               context: Optional[Dict] = None) -> Optional[Any]:
        """
        Find the matching feedback edge for a failed stage.

        Priority:
          1. Exact match on (trigger_stage, trigger_classifier)
          2. Match on trigger_stage with trigger_condition (no classifier)
          3. Match on trigger_stage only (catch-all for that stage)
        """
        context = context or {}

        # Priority 1: stage + classifier match
        for edge in self.edges:
            if (edge.trigger_stage == stage
                    and edge.trigger_classifier
                    and edge.trigger_classifier == classifier_label):
                return edge

        # Priority 2: stage + condition match
        for edge in self.edges:
            if (edge.trigger_stage == stage
                    and not edge.trigger_classifier
                    and edge.trigger_condition):
                # Simple condition evaluation
                cls_engine = ClassifierEngine([])
                if cls_engine._eval_condition(edge.trigger_condition, context):
                    return edge

        # Priority 3: stage catch-all
        for edge in self.edges:
            if (edge.trigger_stage == stage
                    and not edge.trigger_classifier
                    and not edge.trigger_condition):
                return edge

        return None


# ============================================================
# Loop Controller
# ============================================================

class LoopController:
    """
    Main converge loop driver. Domain-agnostic — all behavior
    comes from the Project's ConvergeConfig (loaded from YAML).

    Usage:
        from core.project import create_project
        from core.converge import LoopController

        project = create_project("counter")
        controller = LoopController(project)
        result = controller.run()
    """

    def __init__(self, project: Any, verbose: bool = False):
        """
        Args:
            project: Project instance with converge_config loaded
            verbose: Print detailed progress
        """
        self.project = project
        self.verbose = verbose

        config = project.converge_config
        if not config:
            raise ValueError("Project must have converge_config loaded")

        # Build engine components from YAML config
        self.score_calc = ScoreCalculator(config.score_weights)
        self.parser = OutputParser()
        self.classifier = ClassifierEngine(config.classifiers)
        self.router = FeedbackRouter(config.feedback_graph)

        # Stage index for ordered execution
        self._stage_ids = [s.id for s in config.stages]
        self._stage_map = {s.id: s for s in config.stages}

    def run(self) -> Any:
        """
        Execute the full converge loop.

        Returns:
            Project instance with final state (converged/stalled/failed)
        """
        project = self.project
        config = project.converge_config

        project.status = "running"
        project.phase = "running"
        self._log(f"Starting converge loop: {config.name}")
        self._log(f"  Stages: {self._stage_ids}")
        self._log(f"  Criteria: {config.criteria_hard_stop}")
        self._log(f"  Score threshold: {config.criteria_score_threshold}")

        try:
            stage_idx = 0

            while stage_idx < len(self._stage_ids):
                # Global convergence check
                if project.is_converged():
                    project.status = "converged"
                    project.convergence_reason = "All hard_stop criteria met"
                    self._log(f"CONVERGED at iteration {project.iteration}")
                    break

                if project.is_exhausted():
                    project.status = "failed"
                    project.convergence_reason = f"Max iterations ({config.criteria_max_total_iterations}) reached"
                    self._log(f"EXHAUSTED at iteration {project.iteration}")
                    break

                stage_id = self._stage_ids[stage_idx]
                stage_cfg = self._stage_map[stage_id]

                self._log(f"\n{'='*50}")
                self._log(f"Stage: {stage_id} (idx={stage_idx})")

                # Execute the stage
                action_label, raw_output, tool_calls_count, tool_observations = self._execute_stage(stage_cfg)

                if raw_output is None:
                    self._log(f"Stage {stage_id} produced no output, skipping")
                    stage_idx += 1
                    continue

                # If the sub-agent made zero tool calls, its output is just
                # LLM text — not the result of actual lint/sim/etc.
                # Do NOT parse metrics from it; treat as a no-op stage.
                if tool_calls_count == 0:
                    self._log(f"  Stage {stage_id} was a no-op (0 tool calls). Marking stage as ineffective.")
                    project.mark_stage_noop(stage_id)
                    # Still record the iteration for visibility
                    project.current_stage = stage_id
                    project.record_iteration(action_label, dict(project.metrics), 0.0)
                    project.save_state()
                    stage_idx += 1
                    continue

                # ── Metric Extraction ──────────────────────────────
                # Priority 1: METRICS: lines from LLM's final text
                # Priority 2: METRICS: lines from tool observations
                # Priority 3: Fallback regex on tool observations (verilator/vvp output)
                # Priority 4: Fallback regex on LLM text

                combined_text = f"{raw_output}\n{tool_observations}"

                # Try primary parser on combined text first
                stage_parser = config.parsers.get(stage_id)
                parsed = self.parser.parse(combined_text, stage_parser)
                self._log(f"  Parsed metrics (primary): {parsed}")

                # Fallback: if primary parser found nothing useful,
                # parse common patterns from tool observations (where
                # verilator/iverilog/vvp output actually lives)
                if not parsed or all(v == 0 or v == "" for v in parsed.values()):
                    parsed = self._fallback_parse(stage_id, tool_observations)
                    if parsed:
                        self._log(f"  Fallback metrics (from tool output): {parsed}")
                    else:
                        # Last resort: try fallback on raw LLM output
                        parsed = self._fallback_parse(stage_id, raw_output)
                        if parsed:
                            self._log(f"  Fallback metrics (from LLM text): {parsed}")

                # Cast extracted string values to int for proper scoring
                for k, v in parsed.items():
                    if isinstance(v, str):
                        try:
                            parsed[k] = int(v)
                        except (ValueError, TypeError):
                            pass  # keep as string

                # Flatten parser results into project metrics
                for k, v in parsed.items():
                    project.metrics[f"{stage_id}.{k}"] = v

                # Compute score
                score = self.score_calc.compute(project.metrics)
                self._log(f"  Score: {score:.1f} (best: {project.best_score:.1f})")

                # Record iteration
                project.current_stage = stage_id
                project.record_iteration(action_label, dict(project.metrics), score)
                project.save_state()

                # Check if stage failed (has negative indicators)
                stage_failed = self._is_stage_failed(stage_id, parsed)
                self._log(f"  Stage failed: {stage_failed}")

                if stage_failed:
                    # Classify the failure using both LLM text and tool output
                    context = self._build_classifier_context(stage_id)
                    classify_text = f"{raw_output}\n{tool_observations}"
                    label = self.classifier.classify(classify_text, context)
                    self._log(f"  Classification: {label or '(none)'}")

                    # Route to fix step
                    edge = self.router.lookup(stage_id, label, context)
                    if edge:
                        self._log(f"  Feedback route: fix via {edge.fix_workspace}, retry from {edge.retry_from}")

                        # Check retry limit for this fix
                        retry_count = project.increment_stage_retry(edge.retry_from or stage_id)
                        if retry_count > edge.max_retries:
                            self._log(f"  Max retries ({edge.max_retries}) reached for {edge.retry_from}")
                            stage_idx += 1
                            continue

                        # Execute fix step
                        fix_action, fix_output, fix_tool_obs = self._execute_fix(edge, raw_output)

                        # Re-route to retry_from stage
                        if edge.retry_from and edge.retry_from in self._stage_ids:
                            stage_idx = self._stage_ids.index(edge.retry_from)
                            self._log(f"  Retrying from stage: {edge.retry_from} (idx={stage_idx})")
                        else:
                            stage_idx += 1
                    else:
                        self._log(f"  No feedback route found, advancing")
                        stage_idx += 1
                else:
                    # Stage passed, advance
                    stage_idx += 1

            # Final convergence check
            if project.status == "running":
                if project.is_converged():
                    project.status = "converged"
                    project.convergence_reason = "All hard_stop criteria met"
                elif project.is_stalled():
                    project.status = "stalled"
                    project.convergence_reason = f"No improvement for {project.no_improve_count} iterations"
                else:
                    # Check if any stages actually produced work.
                    # If all stages were no-ops, this is a failed run, not convergence.
                    effective_stages = set(self._stage_ids) - project.noop_stages
                    if not effective_stages:
                        project.status = "failed"
                        project.convergence_reason = (
                            "All stages were no-ops (sub-agent made 0 tool calls). "
                            "No real work was performed."
                        )
                    else:
                        project.status = "converged" if project.score >= config.criteria_score_threshold else "failed"
                        project.convergence_reason = f"Pipeline complete. Score: {project.score:.1f}"

        except KeyboardInterrupt:
            project.status = "failed"
            project.convergence_reason = "Interrupted by user"
        except Exception as e:
            project.status = "failed"
            project.convergence_reason = f"Error: {e}"
            self._log(f"ERROR: {e}\n{traceback.format_exc()}")

        project.phase = "done"
        project.save_state()
        self._log(f"\n{'='*50}")
        self._log(f"Result: {project.status} | Score: {project.score:.1f} | Reason: {project.convergence_reason}")

        return project

    # ============================================================
    # Stage Execution
    # ============================================================

    def _execute_stage(self, stage_cfg: Any) -> Tuple[str, Optional[str], int, str]:
        """
        Execute a pipeline stage via run_agent_session().

        Returns:
            (action_label, raw_output, tool_calls_count, tool_observations) tuple
        """
        from core.agent_runner import run_agent_session

        prompt = self.project.resolve_template(stage_cfg.prompt)
        stage_id = stage_cfg.id

        self._log(f"  Executing stage '{stage_id}' via workspace '{stage_cfg.workspace}'")

        try:
            result = run_agent_session(
                agent_name=stage_cfg.agent,
                prompt=prompt,
                workflow_name=stage_cfg.workspace,
                max_iterations=15,
                compress_result=False,  # need raw output for parsing
                max_result_chars=20000,
                verbose=self.verbose,
                converge_state=self.project,
            )

            tool_calls_count = len(result.tool_calls) if result.tool_calls else 0

            if tool_calls_count == 0:
                self._log(f"  WARNING: Stage '{stage_id}' made 0 tool calls — sub-agent did not execute any tools")

            # Track job
            if result.tool_calls:
                for tc in result.tool_calls:
                    pass  # job tracking done by agent_runner

            # Extract produced variables from output
            self._extract_produced_variables(stage_cfg.produces, result.output)

            raw_output = result.raw_output or result.output
            tool_obs = getattr(result, 'tool_observations', '') or ''
            return stage_id, raw_output, tool_calls_count, tool_obs

        except Exception as e:
            self._log(f"  Stage execution error: {e}")
            return stage_id, f"Error: {e}", 0, ""

    def _execute_fix(self, edge: Any, failure_output: str) -> Tuple[str, Optional[str], str]:
        """
        Execute a fix step from the feedback graph.

        Returns:
            (action_label, raw_output, tool_observations) tuple
        """
        from core.agent_runner import run_agent_session

        prompt = self.project.resolve_template(edge.fix_prompt)
        # Append failure context
        if failure_output:
            prompt += f"\n\n[Failure output]\n{failure_output[:3000]}"

        action_label = f"fix-{edge.trigger_stage}"

        try:
            result = run_agent_session(
                agent_name=edge.fix_agent,
                prompt=prompt,
                workflow_name=edge.fix_workspace,
                max_iterations=15,
                compress_result=False,
                max_result_chars=20000,
                verbose=self.verbose,
                converge_state=self.project,
            )

            tool_obs = getattr(result, 'tool_observations', '') or ''
            return action_label, result.raw_output or result.output, tool_obs

        except Exception as e:
            self._log(f"  Fix execution error: {e}")
            return action_label, f"Error: {e}", ""

    # ============================================================
    # Helpers
    # ============================================================

    def _is_stage_failed(self, stage_id: str, parsed: Dict) -> bool:
        """
        Determine if a stage's output indicates failure.
        Checks for common failure indicators in parsed metrics.
        """
        # Check for error counts > 0
        for key, val in parsed.items():
            key_lower = key.lower()
            if isinstance(val, (int, float)):
                if ("error" in key_lower and val > 0):
                    return True
                if ("fail" in key_lower and val > 0):
                    return True

        # Check project metrics for this stage
        for key, val in self.project.metrics.items():
            if key.startswith(f"{stage_id}.") and isinstance(val, (int, float)):
                key_lower = key.lower()
                if "error" in key_lower and val > 0:
                    return True
                if "fail" in key_lower and val > 0:
                    return True

        return False

    def _extract_produced_variables(self, produces: List[str],
                                     output: str) -> None:
        """
        Try to extract produced variable values from output.
        Convention: look for "Output: <path>" or "→ <path>" patterns.
        """
        for var_name in produces:
            if var_name.endswith("_path"):
                # Try to find a file path in output
                for pattern in [
                    rf'Output:\s*(\S+)',
                    rf'→\s*(\S+)',
                    rf'Written:\s*(\S+)',
                    rf'Created:\s*(\S+)',
                ]:
                    m = re.search(pattern, output)
                    if m:
                        self.project.set_variable(var_name, m.group(1))
                        break

    def _build_classifier_context(self, stage_id: str) -> Dict[str, Any]:
        """Build context dict for classifier condition evaluation."""
        return {
            "stage.retry": self.project.get_stage_retry_count(stage_id),
            f"{stage_id}.iterations": self.project.get_stage_retry_count(stage_id),
            "iteration": self.project.iteration,
            "score": self.project.score,
        }

    def _log(self, msg: str) -> None:
        if self.verbose:
            print(f"  [converge] {msg}")

    def _fallback_parse(self, stage_id: str, raw_output: str) -> Dict[str, Any]:
        """
        Fallback metric parser when primary METRICS: line parsing fails.

        Tries common patterns from tool output (verilator, iverilog, vvp).
        """
        results: Dict[str, Any] = {}

        if stage_id == "lint":
            # Count verilator %Error and %Warning lines
            errors = len(re.findall(r"%Error", raw_output))
            warnings = len(re.findall(r"%Warning", raw_output))
            # If only "Exiting due to N warning(s)" appears, parse the count
            if errors == 0:
                m = re.search(r"Exiting due to (\d+) error", raw_output)
                if m:
                    errors = int(m.group(1))
            if warnings == 0:
                m = re.search(r"Exiting due to (\d+) warning", raw_output)
                if m:
                    warnings = int(m.group(1))
            # Also check for iverilog-style errors
            if errors == 0:
                iverilog_errors = len(re.findall(r"(?i)\berror:", raw_output))
                if iverilog_errors > 0:
                    errors = iverilog_errors
            results["errors"] = errors
            results["warnings"] = warnings

        elif stage_id == "sim":
            # Count [PASS] and [FAIL] markers from simulation output
            # These appear in vvp output or redirected log files
            passes = len(re.findall(r"\[PASS\]", raw_output))
            fails = len(re.findall(r"\[FAIL\]", raw_output))
            results["pass"] = passes
            results["fail"] = fails
            results["total"] = passes + fails

        elif stage_id == "rtl":
            # Check for compile errors from iverilog
            errors = len(re.findall(r"(?i)\berror:", raw_output))
            results["compile_errors"] = errors
            results["complete"] = 1 if errors == 0 else 0

        elif stage_id == "tb":
            errors = len(re.findall(r"(?i)\berror:", raw_output))
            results["compile_errors"] = errors
            results["complete"] = 1 if errors == 0 else 0

        elif stage_id == "spec":
            results["complete"] = 1  # If we got here, spec stage ran

        return results


# ============================================================
# Convenience: Run converge from slash command
# ============================================================

def run_converge_loop(
    module: str,
    converge_yaml: Optional[Path] = None,
    project_root: Optional[Path] = None,
    verbose: bool = False,
) -> Any:
    """
    One-call entry point for running a converge loop.

    Args:
        module: Module name (e.g., "counter")
        converge_yaml: Path to converge.yaml (auto-discover if None)
        project_root: Project root directory (default: cwd)
        verbose: Print detailed progress

    Returns:
        Project instance with final state
    """
    from core.project import create_project

    project = create_project(
        module=module,
        project_root=project_root,
        converge_yaml=converge_yaml,
    )

    controller = LoopController(project, verbose=verbose)
    return controller.run()
