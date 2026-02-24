#!/usr/bin/env python3
"""
explore / plan 에이전트 LLM 설정 및 실제 호출 테스트
"""
import os
import sys

# Path setup
_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_dir, 'src'))
sys.path.insert(0, _dir)

print("=" * 60)
print("Agent LLM Config Test")
print("=" * 60)

# ── 1. agent_config 로드 확인 ──────────────────────────────
print("\n[1] agents.jsonc 로드 확인")
from core.agent_config import get_agent_config

for name in ("explore", "plan"):
    cfg = get_agent_config(name)
    if cfg and cfg.model:
        print(f"  ✅ {name:8s} → {cfg.model.provider_id}/{cfg.model.model_id}  (temp={cfg.temperature})")
    else:
        print(f"  ❌ {name:8s} → config 없음 (기본 LLM 사용)")

# ── 2. get_llm_call_func() 동작 확인 ─────────────────────
print("\n[2] get_llm_call_func() 동작 확인")
from llm_client import call_llm_raw
from agents.sub_agents.explore_agent import ExploreAgent
from agents.sub_agents.plan_agent import PlanAgent

def dummy_tool(tool_name, args):
    return f"[dummy] {tool_name}({args})"

explore_agent = ExploreAgent(name="explore", llm_call_func=call_llm_raw, execute_tool_func=dummy_tool)
plan_agent    = PlanAgent(  name="plan",    llm_call_func=call_llm_raw, execute_tool_func=dummy_tool)

explore_func = explore_agent.get_llm_call_func()
plan_func    = plan_agent.get_llm_call_func()

print(f"  explore llm func 교체됨: {explore_func is not call_llm_raw}")
print(f"  plan    llm func 교체됨: {plan_func    is not call_llm_raw}")

# ── 3. call_llm_for_agent 경유 실제 모델 확인 ─────────────
print("\n[3] call_llm_for_agent 실제 모델 확인")
from llm_client import call_llm_for_agent, get_provider_config
from core.agent_config import get_agent_config

for name in ("explore", "plan"):
    cfg = get_agent_config(name)
    if cfg and cfg.model:
        prov = get_provider_config(
            provider_id=cfg.model.provider_id,
            model_id=cfg.model.model_id
        )
        print(f"  {name:8s} → url={prov.base_url}")
        print(f"  {' ':8s}   model={prov.model_id}")
    else:
        print(f"  {name:8s} → 기본 설정 사용")

# ── 4. 실제 API 호출 테스트 ───────────────────────────────
print("\n[4] 실제 API 호출 테스트")
print("  (짧은 ping 메시지로 모델 응답 확인)\n")

test_messages = [
    {"role": "user", "content": "Reply with just: 'OK [your model name]'"}
]

for name in ("explore", "plan"):
    print(f"  --- {name} agent ---")
    try:
        resp = call_llm_for_agent(test_messages, agent_name=name)
        print(f"  응답: {resp.strip()[:200]}")
        print(f"  ✅ 성공\n")
    except Exception as e:
        print(f"  ❌ 실패: {e}\n")

print("=" * 60)
print("Done")
print("=" * 60)
