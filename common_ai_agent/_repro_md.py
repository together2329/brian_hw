import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib.textual_ui import _fix_md

cases = {}

# 1) Single UNPAIRED lone backtick in prose (the reported bug)
cases["unpaired_lone_backtick"] = (
    "어떤 mental model이야:\n`\n즉, 이 시스템은:\n\n"
    "# 3. 소유권 규칙\n\n| Artifact | Owner |\n|-|-|\n| x | y |\n"
)

# 2) PAIRED lone backticks intended as a fence around code (must still work)
cases["paired_lone_backticks"] = (
    "예시 코드:\n`\ndef foo():\n    return 1\n`\n다음 문장.\n"
)

# 3) Three lone backticks (one pair + one straggler)
cases["three_lone_backticks"] = (
    "a\n`\ncode\n`\nb\n`\nc\n\n# Heading\n"
)

# 4) Real triple fence unaffected
cases["real_triple_fence"] = (
    "```python\nprint(1)\n```\n\n# Heading\n| a | b |\n|-|-|\n"
)

for name, raw in cases.items():
    fixed = _fix_md(raw)
    nf = sum(1 for l in fixed.splitlines() if l.strip().startswith("```"))
    bad = any(l.strip() in ("# Heading", "# 3. 소유권 규칙") for l in fixed.splitlines())
    print("=" * 64)
    print(f"CASE: {name}  | fence-markers={nf} ({'BALANCED' if nf%2==0 else 'ODD!!'})")
    for ln in fixed.splitlines():
        print("   ", repr(ln))
