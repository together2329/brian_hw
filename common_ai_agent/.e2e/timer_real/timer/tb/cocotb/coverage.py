import json
from pathlib import Path

class TimerCoverage:
    def __init__(self, root='.'):
        self.root = Path(root)
        self.bins = {}

    def sample(self, scenario_id, refs=None):
        self.bins[scenario_id] = self.bins.get(scenario_id, 0) + 1
        for r in refs or []:
            self.bins[str(r)] = self.bins.get(str(r), 0) + 1

    def write(self):
        p = self.root / 'timer' / 'cov' / 'coverage_functional.json'
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open('w') as f:
            json.dump({'functional_bins': self.bins}, f, indent=2)
