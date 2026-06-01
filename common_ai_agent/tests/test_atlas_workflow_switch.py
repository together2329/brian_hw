from pathlib import Path

import src.atlas_workflow_switch as workflow_switch


def test_schedule_workflow_checkpoint_starts_background_thread(tmp_path, monkeypatch):
    ip_dir = tmp_path / "demo_ip"
    (ip_dir / ".git").mkdir(parents=True)
    started = []

    class FakeThread:
        def __init__(self, *, target, args, name, daemon):
            self.target = target
            self.args = args
            self.name = name
            self.daemon = daemon

        def start(self):
            started.append(self)

    monkeypatch.setattr(workflow_switch.threading, "Thread", FakeThread)

    status = workflow_switch.schedule_workflow_checkpoint(
        workflow_switch.WorkflowCheckpointRequest(
            ip_dir=ip_dir,
            previous_workflow="rtl-gen",
            next_workflow="coverage",
        )
    )

    assert status.scheduled is True
    assert started
    assert started[0].target is workflow_switch._commit_workflow_checkpoint
    assert started[0].args[0].ip_dir == ip_dir
    assert started[0].daemon is True


def test_schedule_workflow_checkpoint_skips_non_git_ip(tmp_path: Path):
    status = workflow_switch.schedule_workflow_checkpoint(
        workflow_switch.WorkflowCheckpointRequest(
            ip_dir=tmp_path / "demo_ip",
            previous_workflow="rtl-gen",
            next_workflow="coverage",
        )
    )

    assert status.scheduled is False
    assert status.reason == "not_a_git_repo"
