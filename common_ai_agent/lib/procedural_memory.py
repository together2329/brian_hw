"""
Procedural Memory System (Memp-inspired)

Enables Brian Coder to learn from past experiences and improve over time.
Stores "how-to" knowledge as trajectories: task → actions → outcome.

Key features:
- Build: Store experiences as trajectories
- Retrieve: Find similar past experiences for new tasks
- Update: Reflect on failures and improve strategies
- Zero-dependency (stdlib + urllib only)
"""
import json
import math
import os
import tempfile
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import re


@dataclass
class Action:
    """
    Single action in a trajectory.

    Attributes:
        tool: Tool name (e.g., "read_file", "run_command")
        args: Tool arguments as string
        result: Result of the action (success/failure/error)
        observation: Observation returned
        timestamp: When action was executed
    """
    tool: str
    args: str
    result: str  # "success", "failure", "error"
    observation: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Action':
        return cls(**data)


@dataclass
class Trajectory:
    """
    A complete experience: task → sequence of actions → outcome.

    Attributes:
        id: Unique identifier
        task_type: Classification of task (e.g., "compile_verilog", "debug_python")
        task_description: Original task description
        actions: Sequence of actions taken
        outcome: Final outcome ("success" or "failure")
        iterations: Number of iterations taken
        success_rate: Success rate (0.0-1.0)
        errors_encountered: List of errors encountered
        created_at: When trajectory was created
        updated_at: When trajectory was last updated
        usage_count: How many times this trajectory was retrieved
    """
    id: str
    task_type: str
    task_description: str
    actions: List[Action]
    outcome: str  # "success" or "failure"
    iterations: int
    success_rate: float = 1.0
    errors_encountered: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    usage_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['actions'] = [action.to_dict() for action in self.actions]
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Trajectory':
        actions = [Action.from_dict(a) for a in data.pop('actions')]
        return cls(actions=actions, **data)


class ProceduralMemory:
    """
    Procedural Memory System (Memp-inspired)

    Manages "how-to" knowledge through Build-Retrieve-Update cycle.
    Enables learning from past experiences and failure reflection.
    """

    def __init__(self, memory_dir: str = ".brian_memory"):
        """
        Initialize Procedural Memory system.

        Args:
            memory_dir: Directory for storing trajectories
        """
        self.memory_dir = Path.home() / memory_dir
        self.trajectories_file = self.memory_dir / "procedural_trajectories.json"
        self.trajectories: Dict[str, Trajectory] = {}

        self._ensure_initialized()
        self._load()

    def _ensure_initialized(self):
        """Ensure memory directory and files exist."""
        self.memory_dir.mkdir(parents=True, exist_ok=True)

        if not self.trajectories_file.exists():
            # Best-effort, atomic init to avoid partial writes in concurrent setups.
            with self._file_lock(self.trajectories_file):
                if not self.trajectories_file.exists():
                    self._atomic_write_json(self.trajectories_file, {})

    # ==================== Low-level File Helpers ====================

    def _read_json_file(self, path: Path) -> Dict[str, Any]:
        """Read a JSON dict from disk, returning {} on error."""
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _atomic_write_json(self, path: Path, data: Dict[str, Any]) -> None:
        """
        Atomically write JSON to disk.
        Writes to a temp file in the same directory, then os.replace().
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode='w',
                dir=str(path.parent),
                delete=False,
                encoding='utf-8'
            ) as tmp:
                json.dump(data, tmp, indent=2, ensure_ascii=False)
                tmp.flush()
                os.fsync(tmp.fileno())
                tmp_path = Path(tmp.name)
            os.replace(str(tmp_path), str(path))
        finally:
            if tmp_path and tmp_path.exists():
                try:
                    tmp_path.unlink()
                except Exception:
                    pass

    @contextmanager
    def _file_lock(self, target_path: Path, timeout: float = 5.0, poll_interval: float = 0.05):
        """
        Cross-process lock using an adjacent lock file.
        Best-effort: blocks until acquired or timeout.
        """
        lock_path = target_path.with_suffix(target_path.suffix + ".lock")
        start = time.time()
        fd = None

        while True:
            try:
                fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_RDWR)
                break
            except FileExistsError:
                if (time.time() - start) > timeout:
                    raise TimeoutError(f"Timeout acquiring lock for {target_path}")
                time.sleep(poll_interval)

        try:
            yield
        finally:
            if fd is not None:
                try:
                    os.close(fd)
                except OSError:
                    pass
            try:
                os.unlink(str(lock_path))
            except FileNotFoundError:
                pass

    # ==================== Build ====================

    def build(self, task_description: str, actions: List[Action],
              outcome: str, iterations: int) -> str:
        """
        Build a new trajectory from an experience.

        Args:
            task_description: Description of the task
            actions: Sequence of actions taken
            outcome: Final outcome ("success" or "failure")
            iterations: Number of iterations taken

        Returns:
            Trajectory ID
        """
        # Classify task type
        task_type = self._classify_task(task_description, actions)

        # Extract errors
        errors = self._extract_errors(actions)

        # Calculate success rate
        success_rate = 1.0 if outcome == "success" else 0.0

        # Generate trajectory ID
        trajectory_id = f"traj_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_{uuid.uuid4().hex[:8]}"

        # Create trajectory
        trajectory = Trajectory(
            id=trajectory_id,
            task_type=task_type,
            task_description=task_description,
            actions=actions,
            outcome=outcome,
            iterations=iterations,
            success_rate=success_rate,
            errors_encountered=errors
        )

        # Store trajectory
        self.trajectories[trajectory_id] = trajectory

        return trajectory_id

    def _classify_task(self, task_description: str, actions: List[Action]) -> str:
        """
        Classify task type based on description and actions.

        Args:
            task_description: Task description
            actions: Actions taken

        Returns:
            Task type string
        """
        task_lower = task_description.lower()

        # Check for common patterns
        if "iverilog" in task_lower or "verilog" in task_lower:
            return "compile_verilog"
        elif "python" in task_lower or ".py" in task_lower:
            if "test" in task_lower:
                return "test_python"
            elif "run" in task_lower or "execute" in task_lower:
                return "run_python"
            else:
                return "python_task"
        elif "compile" in task_lower or "build" in task_lower:
            return "compile_code"
        elif "test" in task_lower:
            return "run_tests"
        elif "debug" in task_lower or "fix" in task_lower or "error" in task_lower:
            return "debug_task"
        elif "read" in task_lower or "analyze" in task_lower:
            return "read_task"
        elif "write" in task_lower or "create" in task_lower:
            # Check actions to see if writing code
            write_actions = [a for a in actions if a.tool == "write_file"]
            if write_actions:
                return "write_code"
            return "write_task"
        else:
            # Use most common tool as classifier
            if actions:
                tool_counts = {}
                for action in actions:
                    tool_counts[action.tool] = tool_counts.get(action.tool, 0) + 1
                most_common_tool = max(tool_counts, key=tool_counts.get)
                return f"{most_common_tool}_task"

            return "general_task"

    def _extract_errors(self, actions: List[Action]) -> List[str]:
        """
        Extract error messages from actions.

        Args:
            actions: List of actions

        Returns:
            List of unique error messages
        """
        errors = []
        error_patterns = [
            r'error:?\s+(.+)',
            r'exception:?\s+(.+)',
            r'failed:?\s+(.+)',
            r'syntax error\s+(.+)?',
        ]

        for action in actions:
            if action.result in ["failure", "error"]:
                obs_lower = action.observation.lower()

                # Try to extract specific error message
                for pattern in error_patterns:
                    match = re.search(pattern, obs_lower, re.IGNORECASE)
                    if match:
                        error_msg = match.group(0)[:100]  # First 100 chars
                        if error_msg not in errors:
                            errors.append(error_msg)
                        break

        return errors

    # ==================== Retrieve ====================

    def retrieve(self, task_description: str, limit: int = 3) -> List[Tuple[float, Trajectory]]:
        """
        Retrieve most relevant past trajectories for a new task.

        Args:
            task_description: New task description
            limit: Maximum number of trajectories to return

        Returns:
            List of (similarity_score, trajectory) tuples, sorted by score
        """
        if not self.trajectories:
            return []

        # Classify new task
        new_task_type = self._classify_task(task_description, [])

        results = []

        for trajectory in self.trajectories.values():
            # Calculate similarity score
            score = self._calculate_similarity(
                task_description,
                new_task_type,
                trajectory
            )

            results.append((score, trajectory))

        # Sort by score (descending)
        results.sort(reverse=True, key=lambda x: x[0])

        return results[:limit]

    def _calculate_similarity(self, task_description: str,
                             task_type: str, trajectory: Trajectory) -> float:
        """
        Calculate similarity between new task and trajectory.

        Uses multiple signals:
        - Task type match (most important)
        - Keyword overlap
        - Success rate (prefer successful trajectories)
        - Recency (prefer recent trajectories)
        - Usage count (prefer proven trajectories)

        Args:
            task_description: New task description
            task_type: Classified task type
            trajectory: Trajectory to compare with

        Returns:
            Similarity score (0.0-1.0)
        """
        score = 0.0

        # 1. Task type match (40% weight)
        if trajectory.task_type == task_type:
            score += 0.4
        elif self._is_related_task_type(task_type, trajectory.task_type):
            score += 0.2

        # 2. Keyword overlap (30% weight)
        keywords_new = set(self._extract_keywords(task_description))
        keywords_traj = set(self._extract_keywords(trajectory.task_description))

        if keywords_new and keywords_traj:
            overlap = len(keywords_new & keywords_traj)
            total = len(keywords_new | keywords_traj)
            keyword_score = overlap / total if total > 0 else 0
            score += 0.3 * keyword_score

        # 3. Success rate (20% weight)
        score += 0.2 * trajectory.success_rate

        # 4. Recency (5% weight)
        # More recent = higher score
        try:
            days_old = (datetime.now() - datetime.fromisoformat(trajectory.created_at)).days
            recency_score = max(0, 1 - (days_old / 30))  # Decay over 30 days
            score += 0.05 * recency_score
        except:
            pass

        # 5. Usage count (5% weight)
        # More used = more proven
        usage_score = min(1.0, trajectory.usage_count / 10)  # Cap at 10 uses
        score += 0.05 * usage_score

        return min(1.0, score)

    def _is_related_task_type(self, type1: str, type2: str) -> bool:
        """Check if two task types are related."""
        related_groups = [
            {"compile_verilog", "compile_code"},
            {"test_python", "run_python", "python_task"},
            {"debug_task", "fix_task"},
            {"read_task", "analyze_task"},
            {"write_code", "write_task"},
        ]

        for group in related_groups:
            if type1 in group and type2 in group:
                return True

        return False

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text."""
        # Remove common words
        stopwords = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
                    "of", "with", "by", "from", "up", "about", "into", "through", "during"}

        # Extract words
        words = re.findall(r'\b\w+\b', text.lower())

        # Filter stopwords and short words
        keywords = [w for w in words if w not in stopwords and len(w) > 2]

        return keywords

    # ==================== Update ====================

    def update(self, trajectory_id: str, reflection: str,
               new_success_rate: Optional[float] = None) -> bool:
        """
        Update a trajectory based on new experience or reflection.

        Args:
            trajectory_id: ID of trajectory to update
            reflection: Reflection on what went wrong/right
            new_success_rate: Updated success rate

        Returns:
            True if updated, False if trajectory not found
        """
        if trajectory_id not in self.trajectories:
            return False

        trajectory = self.trajectories[trajectory_id]

        # Update success rate if provided
        if new_success_rate is not None:
            trajectory.success_rate = new_success_rate

        # Update timestamp
        trajectory.updated_at = datetime.now().isoformat()

        # Store reflection as metadata (could be used for future improvements)
        # For now, we just update the trajectory

        return True

    def increment_usage(self, trajectory_id: str) -> bool:
        """
        Increment usage count for a trajectory.

        Args:
            trajectory_id: Trajectory ID

        Returns:
            True if incremented, False if not found
        """
        if trajectory_id not in self.trajectories:
            return False

        self.trajectories[trajectory_id].usage_count += 1
        self.trajectories[trajectory_id].updated_at = datetime.now().isoformat()
        return True

    # ==================== Persistence ====================

    def save(self) -> None:
        """Save trajectories to disk (atomic + locked + merge)."""
        try:
            with self._file_lock(self.trajectories_file):
                existing = self._read_json_file(self.trajectories_file)
                ours = {
                    traj_id: traj.to_dict()
                    for traj_id, traj in self.trajectories.items()
                }

                merged = dict(existing)
                for traj_id, ours_data in ours.items():
                    existing_data = merged.get(traj_id)
                    if not isinstance(existing_data, dict):
                        merged[traj_id] = ours_data
                        continue

                    try:
                        ours_updated = datetime.fromisoformat(ours_data.get("updated_at", ""))
                    except Exception:
                        ours_updated = None
                    try:
                        existing_updated = datetime.fromisoformat(existing_data.get("updated_at", ""))
                    except Exception:
                        existing_updated = None

                    choose_ours = False
                    if existing_updated is None and ours_updated is not None:
                        choose_ours = True
                    elif ours_updated is None and existing_updated is None:
                        choose_ours = True
                    elif ours_updated is not None and existing_updated is not None:
                        choose_ours = ours_updated >= existing_updated

                    if choose_ours:
                        merged_data = ours_data
                    else:
                        merged_data = existing_data

                    # Preserve usage_count across processes where possible.
                    try:
                        merged_data["usage_count"] = max(
                            int(existing_data.get("usage_count", 0)),
                            int(ours_data.get("usage_count", 0))
                        )
                    except Exception:
                        pass

                    merged[traj_id] = merged_data

                self._atomic_write_json(self.trajectories_file, merged)

                # Keep in-memory state in sync with what we just wrote/merged.
                self.trajectories = {
                    tid: Trajectory.from_dict(tdata)
                    for tid, tdata in merged.items()
                    if isinstance(tdata, dict)
                }
        except Exception as e:
            print(f"[Procedural Memory] Failed to save: {e}")

    def _load(self) -> None:
        """Load trajectories from disk."""
        try:
            data = self._read_json_file(self.trajectories_file)
            self.trajectories = {
                traj_id: Trajectory.from_dict(traj_data)
                for traj_id, traj_data in data.items()
                if isinstance(traj_data, dict)
            }
        except Exception:
            # Initialize empty on load failure
            self.trajectories = {}

    # ==================== Utilities ====================

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about procedural memory."""
        if not self.trajectories:
            return {
                "total_trajectories": 0,
                "task_types": {},
                "success_rate": 0.0,
                "most_used": None
            }

        task_types = {}
        total_success_rate = 0.0
        most_used = None
        max_usage = 0

        for traj in self.trajectories.values():
            task_types[traj.task_type] = task_types.get(traj.task_type, 0) + 1
            total_success_rate += traj.success_rate

            if traj.usage_count > max_usage:
                max_usage = traj.usage_count
                most_used = traj.task_type

        return {
            "total_trajectories": len(self.trajectories),
            "task_types": task_types,
            "avg_success_rate": total_success_rate / len(self.trajectories),
            "most_used": most_used
        }

    def clear(self) -> None:
        """Clear all trajectories (caution!)."""
        self.trajectories.clear()
