# MCP 서버 (rtl-db) — 설정과 트러블슈팅

`.cursor/mcp.json`이 `rtl-db` 서버를 등록한다. **Cursor가 직접 띄운다** — 당신이
powershell이나 터미널로 따로 실행할 필요 없다. Cursor가 mcp.json을 읽고
`atlas_mcp_server.py`를 자식 프로세스로 spawn해 stdin/stdout(JSON-RPC)으로 대화한다.

## 원리

```
Cursor (MCP 클라이언트 + 런처) ──stdio JSON-RPC──► atlas_mcp_server.py (서버)
```

Cursor 자체가 MCP 클라이언트라 **별도 어댑터 불필요**. stdio 방식이므로 서버는
상주 데몬이 아니라 Cursor에 붙은 프로세스다 (Cursor 켜지면 뜨고 꺼지면 닫힘).

## 제공 툴

| tool | env 필요? | 기능 |
|---|---|---|
| `rtl_db_query` | ✅ `ATLAS_RTL_DB_QUERY` | 외부 RTL 설계 DB 그래프 워크 |
| `rtl_db_wiki` | ✅ `ATLAS_RTL_DB_WIKI` | 외부 RTL DB wiki 코퍼스 |
| `ontology_query` | ❌ | `ontology/platform.db` SELECT |
| `wiki_search` | ❌ | doc/wiki + `<ip>/wiki` 검색 |

## 안 될 때 — 체크리스트 (실측 빈발 원인)

1. **Windows 네이티브: `command: "python3"` 실패** — Windows엔 `python3`가 보통
   없다(있는 건 `python` 또는 `py`). mcp.json의 command를 환경에 맞게 바꿔라:
   - Windows 네이티브: `"command": "python"` (또는 `"py"`, args 앞에 `"-3"`)
   - **권장: WSL2** — 거기선 `python3`가 정상이고 iverilog/cocotb도 잘 돈다 (SETUP.md)
2. **`rtl_db_query`가 "not configured"** — `env`의 `ATLAS_RTL_DB_QUERY` /
   `ATLAS_RTL_DB_WIKI`를 당신의 RTL DB 경로/명령으로 채워라. 비어 있으면 그 두 툴은
   에러를 반환한다. (`ontology_query`/`wiki_search`는 env 없이도 동작 → 먼저 이걸로
   서버가 살아있는지 확인)
3. **빨간불/연결 실패** — Cursor Settings → MCP에서 서버 상태와 stderr 로그 확인.
   대개 ①(명령 못 찾음)이다.
4. **상대경로 안 풀림** — Cursor는 보통 cwd=프로젝트 루트로 spawn하므로
   `.cursor/scripts/...`가 풀린다. 안 풀리면 args를 절대경로로 바꿔라.

## 서버 단독 점검 (Cursor 없이)

```bash
printf '%s\n%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18"}}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' \
  | python3 .cursor/scripts/atlas_mcp_server.py
```
`serverInfo`와 4개 tool이 JSON으로 나오면 서버는 정상. 그다음 문제는 mcp.json의
command(②/①) 또는 env(②) 설정이다.
