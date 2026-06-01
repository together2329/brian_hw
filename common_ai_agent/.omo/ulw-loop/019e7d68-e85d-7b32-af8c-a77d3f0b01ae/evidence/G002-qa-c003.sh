set -euo pipefail
REPO="/Users/brian/Desktop/Project/brian_hw/common_ai_agent"
ANDES="/Users/brian/Desktop/andes"
cd "$REPO"
ATLAS_PROJECT_ROOT="$REPO" COMMON_AI_AGENT_HOME="$REPO" ATLAS_RTL_DB_WIKI="$ANDES/wiki" ATLAS_RTL_DB_NO_REBUILD=1 python3 - <<'PY'
import importlib
queries = [
    ("uart", "atcuart"),
    ("spi", "atcspi"),
    ("dma", "atcdmac"),
    ("ae210 design coverage module", "rtlroot-platform-ae210p-20161118-ae210p-andes-ip-ae210-top"),
    ("i2c verification coverage module", "rtlroot-platform-ae210p-20161118-ae210p-andes-vip-models-i2c"),
    ("fpu macro coverage module", "rtlroot-platform-ncefpu100-20161118-test-ncefpu100-andes-ip-cop-fpu-macro"),
]
wiki_query = importlib.import_module("core.tools").wiki_query
for topic, expected in queries:
    out = wiki_query(ip="rtl-db", topic=topic, depth=3, max_nodes=8)
    print("QUERY", topic)
    print(out)
    assert expected.lower() in out.lower(), (topic, expected, out)
PY
python3 -m pytest tests/test_wiki_query_tool.py tests/test_andes_rtl_db_wiki_builder.py -q
python3 - <<'PY'
import json
from pathlib import Path
graph = json.loads(Path("/Users/brian/Desktop/andes/wiki/_graph.json").read_text())
print("graph", graph["node_count"], graph["edge_count"])
PY
echo "PASS C003 query regression"
