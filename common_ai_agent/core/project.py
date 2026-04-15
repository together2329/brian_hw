"""
core/project.py — Project model with converge config loading

Project dataclass: module name, converge config (parsed YAML dict),
runtime state (current stage, iteration counters, variables dict).
Method load_converge_config() reads <workspace>/converge.yaml.

No EDA-specific logic — pure config holder and runtime state tracker.
The converge engine (core/converge.py) uses this as its state container.

Persistence: .session/<project>/loop_state.json
"""

import os
import sys
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

# Ensure import paths
_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_script_dir)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# YAML support — optional, falls back to JSON-only
try:
    import yaml
except ImportError:
    yaml = None


# ============================================================
# YAML Loader
# ============================================================

def load_yaml_file(path: Path) -> Optional[Dict]:
    """
    Load a YAML (or JSON) file and return parsed dict.
    Returns None if file doesn't exist. Raises on parse errors.
    """
    if not path.exists():
        return None

    text = path.read_text(encoding="utf-8")

    # Try YAML first (supports JSON as subset)
    if yaml is not None:
        return yaml.safe_load(text) or {}

    # Fallback: if it looks like JSON, parse it
    stripped = text.strip()
    if stripped.startswith("{") or stripped.startswith("["):
        return json.loads(stripped)

    # Last resort: simple key: value parser (not full YAML)
    result = {}
    for line in stripped.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, _, val = line.partition(":")
            result[key.strip()] = val.strip()
    return result


# ============================================================
# Converge Config (parsed from converge.yaml)
# ============================================================

@dataclass
class StageConfig:
    """Single pipeline stage definition (from converge.yaml stages[])."""
    id: str
    workspace: str = ""
    agent: str = "execute"
    prompt: str = ""
    depends_on: List[str] = field(default_factory=list)
    produces: List[str] = field(default_factory=list)
    max_retries: int = 3
    extra: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict) -> "StageConfig":
        return cls(
            id=data.get("id", ""),
            workspace=data.get("workspace", ""),
            agent=data.get("agent", "execute"),
            prompt=data.get("prompt", ""),
            depends_on=data.get("depends_on", []),
            produces=data.get("produces", []),
            max_retries=data.get("max_retries", 3),
            extra={k: v for k, v in data.items()
                   if k not in ("id", "workspace", "agent", "prompt",
                                "depends_on", "produces", "max_retries")},
        )


@dataclass
class FeedbackEdge:
    """Single edge in the feedback graph (from converge.yaml feedback_graph[])."""
    # Trigger
    trigger_stage: str
    trigger_condition: str = ""
    trigger_classifier: str = ""  # classifier label to match

    # Fix
    fix_workspace: str = ""
    fix_agent: str = "execute"
    fix_prompt: str = ""
    retry_from: str = ""          # stage to go back to after fix
    max_retries: int = 3

    @classmethod
    def from_dict(cls, data: Dict) -> "FeedbackEdge":
        trigger = data.get("trigger", {})
        fix = data.get("fix", {})
        return cls(
            trigger_stage=trigger.get("stage", ""),
            trigger_condition=trigger.get("condition", ""),
            trigger_classifier=trigger.get("classifier", ""),
            fix_workspace=fix.get("workspace", ""),
            fix_agent=fix.get("agent", "execute"),
            fix_prompt=fix.get("prompt", ""),
            retry_from=fix.get("retry_from", ""),
            max_retries=fix.get("max_retries", 3),
        )


@dataclass
class ClassifierRule:
    """Single classifier rule (from converge.yaml classifiers[])."""
    id: str
    patterns: List[str] = field(default_factory=list)
    condition: str = ""     # optional condition expression (e.g., "sim.iterations < 3")
    label: str = ""         # classification label when matched

    @classmethod
    def from_dict(cls, data: Dict) -> "ClassifierRule":
        return cls(
            id=data.get("id", ""),
            patterns=data.get("patterns", []),
            condition=data.get("condition", ""),
            label=data.get("label", data.get("id", "")),
        )


@dataclass
class ParserConfig:
    """Output parser definition (from converge.yaml parsers.<stage>)."""
    parser_type: str = "count_patterns"  # count_patterns | structured | regex_groups
    fields: Dict[str, Any] = field(default_factory=dict)
    patterns: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict) -> "ParserConfig":
        return cls(
            parser_type=data.get("type", "count_patterns"),
            fields=data.get("fields", {}),
            patterns=data.get("patterns", {}),
        )


@dataclass
class ConvergeConfig:
    """
    Fully parsed converge.yaml — domain-agnostic loop definition.

    Loaded by Project.load_converge_config(). Contains all stages,
    criteria, score function, feedback graph, classifiers, and parsers.
    """
    name: str = ""
    description: str = ""

    # Pipeline stages (ordered list)
    stages: List[StageConfig] = field(default_factory=list)

    # Convergence criteria
    criteria_hard_stop: List[Dict[str, Any]] = field(default_factory=list)
    criteria_score_threshold: float = 10.0
    criteria_max_total_iterations: int = 15
    criteria_no_improve_limit: int = 3

    # Score function weights
    score_weights: Dict[str, float] = field(default_factory=dict)

    # Feedback graph
    feedback_graph: List[FeedbackEdge] = field(default_factory=list)

    # Classifiers
    classifiers: List[ClassifierRule] = field(default_factory=list)

    # Output parsers per stage
    parsers: Dict[str, ParserConfig] = field(default_factory=dict)

    # Rollback config
    rollback_enabled: bool = True
    rollback_paths: List[str] = field(default_factory=list)
    rollback_on: str = "regressed"  # regressed | stalled | never

    # Raw YAML (for any custom extensions)
    raw: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict) -> "ConvergeConfig":
        """Parse a full converge YAML dict into structured config."""
        criteria = data.get("criteria", {})
        score_fn = data.get("score_function", {})
        weights = score_fn.get("weights", {})
        rollback = data.get("rollback", {})

        # Parse stages
        stages = [StageConfig.from_dict(s) for s in data.get("stages", [])]

        # Parse feedback graph
        fb_graph = [FeedbackEdge.from_dict(e) for e in data.get("feedback_graph", [])]

        # Parse classifiers
        classifiers = [ClassifierRule.from_dict(c) for c in data.get("classifiers", [])]

        # Parse output parsers
        parsers = {}
        for stage_id, parser_data in data.get("parsers", {}).items():
            parsers[stage_id] = ParserConfig.from_dict(parser_data)

        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            stages=stages,
            criteria_hard_stop=criteria.get("hard_stop", []),
            criteria_score_threshold=float(criteria.get("score_threshold", 10.0)),
            criteria_max_total_iterations=int(criteria.get("max_total_iterations", 15)),
            criteria_no_improve_limit=int(criteria.get("no_improve_limit", 3)),
            score_weights=weights,
            feedback_graph=fb_graph,
            classifiers=classifiers,
            parsers=parsers,
            rollback_enabled=rollback.get("enabled", True),
            rollback_paths=rollback.get("paths", []),
            rollback_on=rollback.get("on", "regressed"),
            raw=data,
        )


# ============================================================
# Project Model
# ============================================================

@dataclass
class Project:
    """
    Project model — the top-level state container for a converge loop run.

    Holds:
      - Identity: module name, project root
      - Converge config: parsed from workspace converge.yaml
      - Runtime variables: {module}, {rtl_path}, etc. for prompt templating
      - Runtime state: current stage, iteration counters, metrics, score history
      - Job tracking: list of job IDs created during this run

    Persistence: .session/<project_name>/loop_state.json
    """

    # ── Identity ──────────────────────────────
    module: str = ""
    project_root: Path = field(default_factory=Path.cwd)
    project_name: str = "default"

    # ── Converge Config ───────────────────────
    converge_yaml_path: Optional[Path] = None
    converge_config: Optional[ConvergeConfig] = None

    # ── Runtime Variables (template resolution) ──
    variables: Dict[str, str] = field(default_factory=dict)

    # ── Runtime State ─────────────────────────
    current_stage: str = ""           # stage id
    status: str = "idle"              # idle | running | converged | stalled | failed | timeout
    phase: str = "idle"               # idle | running | paused | done
    iteration: int = 0                # total iterations across all stages
    stage_iterations: Dict[str, int] = field(default_factory=dict)  # per-stage retry count

    # ── Metrics ───────────────────────────────
    metrics: Dict[str, Any] = field(default_factory=dict)   # {"lint.errors": 3, "sim.pass": 5, ...}
    score: float = -999.0
    best_score: float = -999.0
    no_improve_count: int = 0

    # ── History ───────────────────────────────
    history: List[Dict[str, Any]] = field(default_factory=list)
    jobs: List[str] = field(default_factory=list)            # ["job5", "job6", ...]

    # ── Orchestrator Inbox ────────────────────
    inbox: List[Dict[str, Any]] = field(default_factory=list)  # [{type, message, ...}]

    # ── Convergence Result ────────────────────
    convergence_reason: str = ""
    report: Dict[str, Any] = field(default_factory=dict)

    # ── No-op Stage Tracking ──────────────────
    # Stages where the sub-agent made 0 tool calls.
    # Metrics from these stages are excluded from convergence checks.
    noop_stages: set = field(default_factory=set)

    # ── Session directory ─────────────────────
    session_dir: Optional[Path] = None

    # ============================================================
    # Config Loading
    # ============================================================

    def load_converge_config(self, yaml_path: Optional[Path] = None) -> None:
        """
        Load converge.yaml from the given path or discover from workspace.

        Discovery order:
          1. Explicit yaml_path parameter
          2. self.converge_yaml_path (if previously set)
          3. ACTIVE_WORKSPACE env var → workflow/<ws>/converge.yaml
          4. Fallback: workflow/eda/converge.yaml

        Raises FileNotFoundError if no config found.
        """
        search_paths = []

        if yaml_path:
            search_paths.append(Path(yaml_path))
        if self.converge_yaml_path:
            search_paths.append(Path(self.converge_yaml_path))

        # From active workspace env var
        active_ws = os.getenv("ACTIVE_WORKSPACE", "")
        if active_ws:
            search_paths.append(self.project_root / "workflow" / active_ws / "converge.yaml")

        # Default EDA workspace
        search_paths.append(self.project_root / "workflow" / "eda" / "converge.yaml")

        for path in search_paths:
            data = load_yaml_file(path)
            if data is not None:
                self.converge_yaml_path = path
                self.converge_config = ConvergeConfig.from_dict(data)
                # Initialize per-stage iteration counters
                for stage in self.converge_config.stages:
                    if stage.id not in self.stage_iterations:
                        self.stage_iterations[stage.id] = 0
                return

        searched = "\n  ".join(str(p) for p in search_paths)
        raise FileNotFoundError(
            f"converge.yaml not found. Searched:\n  {searched}"
        )

    # ============================================================
    # Variable Management
    # ============================================================

    def set_variable(self, key: str, value: str) -> None:
        """Set a template variable (e.g., 'module', 'rtl_path')."""
        self.variables[key] = value

    def get_variable(self, key: str, default: str = "") -> str:
        """Get a template variable, with {key} default for unresolved."""
        return self.variables.get(key, default)

    def resolve_template(self, template: str) -> str:
        """
        Resolve {variable} placeholders in a prompt template string.

        Uses self.variables dict. Unknown {key}s are left as-is.
        """
        result = template
        for key, value in self.variables.items():
            result = result.replace(f"{{{key}}}", str(value))
        return result

    def update_variables_from_stage_output(self, stage_id: str,
                                            output: str,
                                            produces: List[str]) -> None:
        """
        After a stage runs, extract produced variables from its output.

        Convention: if a stage produces ["rtl_path"], the converge engine
        should set project.variables["rtl_path"] based on parsed output.
        This method just records which variables are expected.
        """
        pass  # Actual extraction done by converge engine per-domain parsers

    # ============================================================
    # State Transitions
    # ============================================================

    def advance_to_stage(self, stage_id: str) -> None:
        """Move to a new pipeline stage."""
        self.current_stage = stage_id

    def record_iteration(self, action: str, metrics: Dict[str, Any],
                         score: float) -> None:
        """Record a single iteration in the history."""
        self.iteration += 1
        self.metrics.update(metrics)
        self.score = score

        is_best = score > self.best_score
        if is_best:
            self.best_score = score
            self.no_improve_count = 0
        elif score == self.best_score:
            self.no_improve_count += 1
        else:
            self.no_improve_count += 1

        self.history.append({
            "iteration": self.iteration,
            "stage": self.current_stage,
            "action": action,
            "score": score,
            "metrics": dict(metrics),
            "is_best": is_best,
        })

    def increment_stage_retry(self, stage_id: str) -> int:
        """Increment retry counter for a stage, return new count."""
        count = self.stage_iterations.get(stage_id, 0) + 1
        self.stage_iterations[stage_id] = count
        return count

    def get_stage_retry_count(self, stage_id: str) -> int:
        """Get current retry count for a stage."""
        return self.stage_iterations.get(stage_id, 0)

    def mark_stage_noop(self, stage_id: str) -> None:
        """Mark a stage as a no-op (sub-agent made 0 tool calls).

        Metrics from no-op stages are excluded from convergence checks
        because the sub-agent just wrote text instead of running tools.
        """
        self.noop_stages.add(stage_id)

    def add_job(self, job_id: str) -> None:
        """Track a job created during this converge run."""
        self.jobs.append(job_id)

    # ============================================================
    # Inbox (orchestrator → sub-agent communication)
    # ============================================================

    def send_to_inbox(self, msg_type: str, message: str,
                      **kwargs) -> None:
        """Add a message to the project inbox for the loop controller."""
        self.inbox.append({
            "type": msg_type,
            "message": message,
            **kwargs,
        })

    def drain_inbox(self) -> List[Dict[str, Any]]:
        """Return and clear all inbox messages."""
        msgs = list(self.inbox)
        self.inbox.clear()
        return msgs

    def has_inbox_messages(self) -> bool:
        return len(self.inbox) > 0

    # ============================================================
    # Persistence
    # ============================================================

    def save_state(self) -> None:
        """Save current project state to loop_state.json."""
        if not self.session_dir:
            return

        self.session_dir.mkdir(parents=True, exist_ok=True)
        state_path = self.session_dir / "loop_state.json"

        data = {
            "module": self.module,
            "project_name": self.project_name,
            "current_stage": self.current_stage,
            "status": self.status,
            "phase": self.phase,
            "iteration": self.iteration,
            "stage_iterations": dict(self.stage_iterations),
            "metrics": dict(self.metrics),
            "score": self.score,
            "best_score": self.best_score,
            "no_improve_count": self.no_improve_count,
            "variables": dict(self.variables),
            "history": list(self.history),
            "jobs": list(self.jobs),
            "inbox": list(self.inbox),
            "convergence_reason": self.convergence_reason,
            "converge_yaml_path": str(self.converge_yaml_path) if self.converge_yaml_path else None,
            "noop_stages": list(self.noop_stages),
        }

        state_path.write_text(
            json.dumps(data, indent=2, default=str, ensure_ascii=False),
            encoding="utf-8",
        )

    def load_state(self) -> bool:
        """
        Load project state from loop_state.json.
        Returns True if state was loaded, False if no saved state exists.
        """
        if not self.session_dir:
            return False

        state_path = self.session_dir / "loop_state.json"
        if not state_path.exists():
            return False

        try:
            data = json.loads(state_path.read_text(encoding="utf-8"))
            self.module = data.get("module", self.module)
            self.project_name = data.get("project_name", self.project_name)
            self.current_stage = data.get("current_stage", "")
            self.status = data.get("status", "idle")
            self.phase = data.get("phase", "idle")
            self.iteration = data.get("iteration", 0)
            self.stage_iterations = data.get("stage_iterations", {})
            self.metrics = data.get("metrics", {})
            self.score = data.get("score", -999.0)
            self.best_score = data.get("best_score", -999.0)
            self.no_improve_count = data.get("no_improve_count", 0)
            self.variables = data.get("variables", {})
            self.history = data.get("history", [])
            self.jobs = data.get("jobs", [])
            self.inbox = data.get("inbox", [])
            self.convergence_reason = data.get("convergence_reason", "")
            self.noop_stages = set(data.get("noop_stages", []))
            yaml_path_str = data.get("converge_yaml_path")
            if yaml_path_str:
                self.converge_yaml_path = Path(yaml_path_str)
            return True
        except (json.JSONDecodeError, KeyError, TypeError):
            return False

    # ============================================================
    # Convergence Check Helpers
    # ============================================================

    def check_hard_stop_criteria(self) -> Dict[str, bool]:
        """
        Evaluate all hard_stop criteria from converge config.

        Returns dict mapping criterion description → pass/fail.
        Example: {"lint.errors == 0": True, "sim.fail == 0": False}

        Metrics from no-op stages (where sub-agent made 0 tool calls)
        are treated as _METRIC_MISSING, preventing false convergence.
        """
        if not self.converge_config:
            return {}

        results = {}
        for criterion in self.converge_config.criteria_hard_stop:
            metric_path = criterion.get("metric", "")
            operator = criterion.get("operator", "==")
            target = criterion.get("value", 0)

            # Check if this metric's stage was a no-op
            # metric_path is like "lint.errors" → stage prefix is "lint"
            stage_prefix = metric_path.split(".")[0] if "." in metric_path else ""
            if stage_prefix in self.noop_stages:
                # This metric came from a no-op stage — treat as not measured
                actual = self._METRIC_MISSING
            else:
                actual = self._resolve_metric_path(metric_path)
            passed = self._compare(actual, operator, target)

            actual_display = actual if actual is not self._METRIC_MISSING else "(not measured)"
            desc = f"{metric_path} {operator} {target} (actual: {actual_display})"
            results[desc] = passed

        return results

    def is_converged(self) -> bool:
        """Check if ALL hard_stop criteria are met."""
        results = self.check_hard_stop_criteria()
        return all(results.values()) if results else False

    def is_stalled(self) -> bool:
        """Check if we've hit the no-improve limit."""
        if not self.converge_config:
            return False
        return self.no_improve_count >= self.converge_config.criteria_no_improve_limit

    def is_exhausted(self) -> bool:
        """Check if we've hit the max total iterations."""
        if not self.converge_config:
            return False
        return self.iteration >= self.converge_config.criteria_max_total_iterations

    # ============================================================
    # Display Helpers
    # ============================================================

    def format_status(self) -> str:
        """Format current project status for REPL display."""
        lines = [
            f"=== Converge Loop: {self.module} ===",
            f"Status: {self.status} | Phase: {self.phase}",
            f"Stage: {self.current_stage} | Iteration: {self.iteration}",
            f"Score: {self.score:.1f} | Best: {self.best_score:.1f} | No-improve: {self.no_improve_count}",
        ]

        if self.metrics:
            lines.append("Metrics:")
            for k, v in sorted(self.metrics.items()):
                lines.append(f"  {k}: {v}")

        criteria = self.check_hard_stop_criteria()
        if criteria:
            lines.append("Criteria:")
            for desc, passed in criteria.items():
                icon = "✅" if passed else "❌"
                lines.append(f"  {icon} {desc}")

        if self.convergence_reason:
            lines.append(f"Reason: {self.convergence_reason}")

        return "\n".join(lines)

    def format_history(self) -> str:
        """Format score history table for REPL display."""
        if not self.history:
            return "No iterations recorded yet."

        lines = [
            f"=== Converge History: {self.module} ===",
            f"{'Iter':>4}  {'Stage':<12} {'Action':<20} {'Score':>8}  {'Best':>5}",
            "-" * 60,
        ]
        for h in self.history:
            best_mark = " ★" if h.get("is_best") else ""
            lines.append(
                f"{h['iteration']:>4}  {h['stage']:<12} {h['action']:<20} "
                f"{h['score']:>8.1f}  {best_mark}"
            )

        lines.append(f"\nTotal: {len(self.history)} iterations | Best score: {self.best_score:.1f}")
        return "\n".join(lines)

    # ============================================================
    # Internal Helpers
    # ============================================================

    # Sentinel for "metric never measured"
    _METRIC_MISSING = object()

    def _resolve_metric_path(self, path: str) -> Any:
        """
        Resolve a dotted metric path like 'lint.errors' from self.metrics.

        Supports both:
          - Flat keys: metrics["lint.errors"] = 0
          - Nested dicts: metrics["lint"]["errors"] = 0

        Returns _METRIC_MISSING if path not found in metrics dict.
        This distinguishes "metric = 0" from "metric never measured".
        """
        # Try flat key first (common case in converge loop)
        if path in self.metrics:
            return self.metrics[path]

        # Try nested dict walk
        parts = path.split(".")
        current = self.metrics
        for part in parts:
            if isinstance(current, dict):
                if part not in current:
                    return self._METRIC_MISSING
                current = current[part]
            else:
                return self._METRIC_MISSING
        return current

    @staticmethod
    def _compare(actual: Any, operator: str, target: Any) -> bool:
        """Compare actual value to target using the given operator.

        If actual is _METRIC_MISSING (never measured), always returns False.
        """
        # If the metric was never measured, criterion is NOT met
        if actual is Project._METRIC_MISSING:
            return False
        try:
            if operator == "==":
                return actual == target
            elif operator == "!=":
                return actual != target
            elif operator == ">=":
                return float(actual) >= float(target)
            elif operator == "<=":
                return float(actual) <= float(target)
            elif operator == ">":
                return float(actual) > float(target)
            elif operator == "<":
                return float(actual) < float(target)
        except (ValueError, TypeError):
            pass
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Serialize project state to dict (for report generation)."""
        return {
            "module": self.module,
            "project_name": self.project_name,
            "status": self.status,
            "phase": self.phase,
            "iteration": self.iteration,
            "score": self.score,
            "best_score": self.best_score,
            "metrics": dict(self.metrics),
            "variables": dict(self.variables),
            "stage_iterations": dict(self.stage_iterations),
            "history": list(self.history),
            "jobs": list(self.jobs),
            "convergence_reason": self.convergence_reason,
        }


# ============================================================
# Factory Functions
# ============================================================

def create_project(
    module: str,
    project_root: Optional[Path] = None,
    converge_yaml: Optional[Path] = None,
    session_name: Optional[str] = None,
) -> Project:
    """
    Create and initialize a Project for a converge loop run.

    Args:
        module: Module name (e.g., "counter")
        project_root: Root directory of the project (default: cwd)
        converge_yaml: Explicit path to converge.yaml (default: auto-discover)
        session_name: Session name for .session/ directory (default: module name)

    Returns:
        Initialized Project with converge config loaded.
    """
    root = project_root or Path.cwd()
    name = session_name or module

    project = Project(
        module=module,
        project_root=root,
        project_name=name,
        session_dir=root / ".session" / name,
        variables={
            "module": module,
        },
    )

    # Load converge config
    project.load_converge_config(yaml_path=converge_yaml)

    # Set initial stage
    if project.converge_config and project.converge_config.stages:
        project.current_stage = project.converge_config.stages[0].id

    return project


def restore_project(session_dir: Path,
                    project_root: Optional[Path] = None) -> Optional[Project]:
    """
    Restore a Project from a saved loop_state.json.

    Returns None if no saved state exists.
    """
    state_path = session_dir / "loop_state.json"
    if not state_path.exists():
        return None

    root = project_root or session_dir.parent.parent

    project = Project(
        project_root=root,
        session_dir=session_dir,
    )

    if project.load_state():
        # Reload converge config from saved path
        if project.converge_yaml_path:
            try:
                project.load_converge_config()
            except FileNotFoundError:
                pass  # Config may have moved; keep previously loaded state
        return project

    return None
