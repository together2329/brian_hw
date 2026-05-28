"""Diagram plan API — extracted from src/atlas_ui.py.

Hosts POST /api/diagram/plan — the lightweight planning endpoint for the
Atlas diagram editor. Was a 231-line nested route inside create_app()
before Phase 16.

Factory pattern: register_diagram_plan_routes(app, *, PROJECT_ROOT)
takes a single closure capture (PROJECT_ROOT). Stdlib imports (asyncio,
json, re) are pulled at module top.

Phase 16 of refactor/atlas-modular (backend extraction).
"""
from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path
from typing import Any

from fastapi.responses import JSONResponse


def register_diagram_plan_routes(app, *, PROJECT_ROOT) -> None:
    """Register POST /api/diagram/plan on `app` via the dep-injected root."""
    @app.post("/api/diagram/plan")
    async def api_diagram_plan(request: Request):
        """Plan diagram edits with the configured LLM.

        The model returns a narrow action JSON. The frontend owns actual
        application through existing layout/connect APIs.
        """
        try:
            body = await request.json()
        except Exception as e:
            return JSONResponse({"error": f"bad json: {e}"}, status_code=400)
        prompt = str((body or {}).get("prompt") or "").strip()
        if not prompt:
            return JSONResponse({"error": "missing prompt"}, status_code=400)
        try:
            import yaml as _yaml
        except ImportError:
            return JSONResponse({"error": "PyYAML not installed"}, status_code=500)
        soc_path = PROJECT_ROOT / "soc.ssot.yaml"
        if not soc_path.is_file():
            return JSONResponse({"error": "soc.ssot.yaml not found at project root"},
                                status_code=404)
        try:
            doc = _yaml.safe_load(soc_path.read_text(encoding="utf-8")) or {}
        except Exception as e:
            return JSONResponse({"error": f"soc parse: {e}"}, status_code=500)
        if not isinstance(doc, dict):
            doc = {}
        modules = []
        for inst in (doc.get("instances") or []):
            if not isinstance(inst, dict) or not inst.get("id"):
                continue
            mid = str(inst["id"])
            ports = []
            leaf = inst.get("ssot")
            if leaf:
                p = PROJECT_ROOT / str(leaf)
                if p.is_file():
                    try:
                        leaf_doc = _yaml.safe_load(p.read_text(encoding="utf-8")) or {}
                        for bi in (leaf_doc.get("busInterfaces") or []):
                            if isinstance(bi, dict):
                                ports.append({
                                    "name": bi.get("name"),
                                    "proto": bi.get("proto"),
                                    "role": bi.get("role"),
                                    "side": bi.get("side"),
                                })
                    except Exception:
                        pass
            modules.append({"id": mid, "name": inst.get("name") or mid,
                            "addr": inst.get("addr"),
                            "x": inst.get("top_x") or inst.get("x"),
                            "y": inst.get("top_y") or inst.get("y"),
                            "ports": ports})
        context = {
            "soc": doc.get("name") or PROJECT_ROOT.name,
            "clusters": doc.get("clusters") or [],
            "modules": modules,
            "connections": doc.get("connections") or [],
            "current_layout": (body or {}).get("layout") or {},
            "canvas": {"w": 1180, "h": 720},
        }

        def _quick_architect_plan(text: str, ctx: dict):
            """Small deterministic command layer before the LLM planner.

            This is intentionally narrow: it gives the Architect chat a
            reliable tool-call surface for common diagram edits, while the
            LLM still handles freer natural language.
            """
            raw = (text or "").strip()
            if not raw:
                return None
            low = raw.lower()
            mods = {str(m.get("id")): m for m in (ctx.get("modules") or [])}
            layout = ctx.get("current_layout") or {}

            def _ref_for(mid: str) -> str:
                for c in (ctx.get("clusters") or []):
                    if not isinstance(c, dict): continue
                    cid = c.get("id") or c.get("name") or "uncategorized"
                    for member in (c.get("members") or []):
                        if str(member) == mid:
                            return f"{cid}/{mid}"
                return f"uncategorized/{mid}"

            def _pos(mid: str):
                ref = _ref_for(mid)
                p = layout.get(f"top:{ref}") or layout.get(ref) or {}
                m = mods.get(mid) or {}
                x = p.get("x", m.get("x"))
                y = p.get("y", m.get("y"))
                try: x = float(x)
                except Exception: x = 170.0
                try: y = float(y)
                except Exception: y = 240.0
                return x, y

            def _move_action(mid: str, where: str = "", x=None, y=None):
                if mid not in mods:
                    return None
                cx, cy = _pos(mid)
                w = (where or "").lower()
                if x is None or y is None:
                    if w in ("left", "좌", "왼쪽"): x, y = 80, cy
                    elif w in ("right", "우", "오른쪽"): x, y = 850, cy
                    elif w in ("top", "up", "위", "상단"): x, y = cx, 70
                    elif w in ("bottom", "down", "아래", "하단"): x, y = cx, 540
                    elif w in ("center", "middle", "중앙", "가운데"): x, y = 470, 280
                    else: return None
                return {"type": "move_block", "id": mid, "x": x, "y": y}

            if low in ("/arch", "/arch help", "/diagram help", "help", "도움말"):
                return {
                    "summary": "Architect commands: /move <inst> <x> <y>|left|right|top|bottom|center; /connect <inst/port> <inst/port> [proto]; /add <model> [id] [cluster]; /delete <inst>; /layout",
                    "actions": [],
                }

            if re.match(r"^/(layout|auto-?layout)\b", low) or low in ("자동배치", "자동 배치"):
                return {"summary": "Reset to automatic top-level layout", "actions": [{"type": "auto_layout"}]}

            m = re.match(r"^/(?:move|mv)\s+([A-Za-z_][\w]*)\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\s*$", raw, re.I)
            if m:
                act = _move_action(m.group(1), x=float(m.group(2)), y=float(m.group(3)))
                return {"summary": f"Move {m.group(1)}", "actions": [act] if act else []}
            m = re.match(r"^/(?:move|mv)\s+([A-Za-z_][\w]*)\s+([A-Za-z가-힣]+)\s*$", raw, re.I)
            if m:
                act = _move_action(m.group(1), m.group(2))
                return {"summary": f"Move {m.group(1)} {m.group(2)}", "actions": [act] if act else []}

            for mid in mods:
                if re.search(rf"\b{re.escape(mid)}\b", raw):
                    where = None
                    if re.search(r"(left|왼쪽|좌측|좌로)", low): where = "left"
                    elif re.search(r"(right|오른쪽|우측|우로)", low): where = "right"
                    elif re.search(r"(top|up|위|상단)", low): where = "top"
                    elif re.search(r"(bottom|down|아래|하단)", low): where = "bottom"
                    elif re.search(r"(center|middle|중앙|가운데)", low): where = "center"
                    if where and re.search(r"(move|옮겨|움직|배치|놓|보내)", low):
                        act = _move_action(mid, where)
                        return {"summary": f"Move {mid} {where}", "actions": [act] if act else []}

            m = re.match(r"^/(?:connect|cn)\s+([\w.-]+/[\w.-]+)\s+([\w.-]+/[\w.-]+)(?:\s+([A-Za-z0-9_]+))?\s*$", raw, re.I)
            if m:
                proto = m.group(3) or ""
                return {"summary": f"Connect {m.group(1)} to {m.group(2)}",
                        "actions": [{"type": "connect_ports", "from": m.group(1), "to": m.group(2), "proto": proto}]}

            m = re.match(r"^/(?:add|add-instance|instantiate)\s+([A-Za-z_][\w]*)(?:\s+([A-Za-z_][\w]*))?(?:\s+([A-Za-z_][\w]*))?\s*$", raw, re.I)
            if m:
                model, inst_id, cluster = m.group(1), m.group(2), m.group(3)
                return {"summary": f"Add {model}",
                        "actions": [{"type": "add_instance", "model": model, "id": inst_id, "cluster": cluster, "x": 170, "y": 560}]}

            m = re.match(r"^/(?:delete|del|remove|rm)\s+([A-Za-z_][\w]*)\s*$", raw, re.I)
            if m:
                return {"summary": f"Delete {m.group(1)}",
                        "actions": [{"type": "delete_instance", "id": m.group(1)}]}

            return None

        quick_plan = _quick_architect_plan(prompt, context)
        if quick_plan is not None:
            return JSONResponse({"ok": True, "plan": quick_plan, "raw": "quick_architect_command"})

        try:
            arch_prompt = (PROJECT_ROOT / "workflow/architect/system_prompt.md").read_text(encoding="utf-8")[:4500]
            arch_commands = (PROJECT_ROOT / "workflow/architect/commands/architect.json").read_text(encoding="utf-8")[:2500]
        except Exception:
            arch_prompt = ""
            arch_commands = ""
        sys_prompt = (
            "You are an SoC Architect diagram planner. Convert the user request "
            "into ONLY strict JSON. No markdown. No prose. Schema: "
            "{\"summary\":\"...\",\"actions\":[...]}. "
            "Allowed actions: "
            "{\"type\":\"move_block\",\"id\":\"<module id>\",\"x\":number,\"y\":number}; "
            "{\"type\":\"connect_ports\",\"from\":\"<module>/<port>\",\"to\":\"<module>/<port>\",\"proto\":\"ACE|AXI4|APB|IRQ|...\"}; "
            "{\"type\":\"auto_layout\"}; "
            "{\"type\":\"add_instance\",\"model\":\"<catalog model>\",\"id\":\"<new instance id>\",\"cluster\":\"<cluster id>\",\"x\":number,\"y\":number}; "
            "{\"type\":\"delete_instance\",\"id\":\"<instance id>\"}. "
            "Use only module ids and ports present in context. For vague placement, choose reasonable canvas coordinates. "
            "You are attached to the workflow/architect supervisor contract below, but your output is still ONLY the diagram action JSON."
        )
        user_prompt = (
            "WORKFLOW ARCHITECT PROMPT EXCERPT:\n" + arch_prompt +
            "\n\nARCHITECT COMMANDS:\n" + arch_commands +
            "\n\nCONTEXT JSON:\n" + json.dumps(context, ensure_ascii=False, default=str) +
            "\n\nUSER REQUEST:\n" + prompt
        )
        try:
            from src.llm_client import call_llm_raw
            raw = await asyncio.to_thread(
                call_llm_raw,
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
                max_tokens=1200,
                caller_tag="atlas_diagram_plan",
            )
        except Exception as e:
            return JSONResponse({"error": f"llm: {e}"}, status_code=500)
        txt = str(raw or "").strip()
        if txt.startswith("```"):
            txt = re.sub(r"^```(?:json)?\s*", "", txt)
            txt = re.sub(r"\s*```$", "", txt)
        try:
            plan = json.loads(txt)
        except Exception:
            m = re.search(r"\{.*\}", txt, re.S)
            if not m:
                return JSONResponse({"error": "llm returned non-json", "raw": txt},
                                    status_code=500)
            try:
                plan = json.loads(m.group(0))
            except Exception as e:
                return JSONResponse({"error": f"json parse: {e}", "raw": txt},
                                    status_code=500)
        if not isinstance(plan, dict):
            return JSONResponse({"error": "plan must be object", "raw": txt},
                                status_code=500)
        actions = plan.get("actions")
        if not isinstance(actions, list):
            return JSONResponse({"error": "plan.actions must be list", "plan": plan},
                                status_code=500)
        allowed = {"move_block", "connect_ports", "auto_layout", "add_instance", "delete_instance"}
        plan["actions"] = [a for a in actions[:12]
                           if isinstance(a, dict) and a.get("type") in allowed]
        return JSONResponse({"ok": True, "plan": plan, "raw": txt})

