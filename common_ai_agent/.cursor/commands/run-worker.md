# Run ATLAS All-Workflows Worker

Start one all-workflows worker for orchestrator dispatch:

```bash
python3 src/main.py --serve --all-workflows --port 5601
```

Use with `atlas-orchestrator-dispatch` when validating pipeline worker behavior.
