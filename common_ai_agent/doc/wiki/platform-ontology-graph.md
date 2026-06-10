---
title: Platform Ontology Graph (auto-generated)
category: architecture
tags: [ontology, traceability, generated]
status: spine 12/17 closed — 재생성: python3 scripts/platform_ontology.py graph > doc/wiki/platform-ontology-graph.md
---

# Platform Ontology Graph

`ontology/platform_*.yaml` 실데이터에서 자동 생성. 손으로 고치지 말 것.

```mermaid
flowchart LR
  classDef closed fill:#d4edda,stroke:#28a745,color:#155724
  classDef refuted fill:#f8d7da,stroke:#dc3545,color:#721c24
  classDef stale fill:#fff3cd,stroke:#ffc107,color:#856404
  classDef open fill:#e2e3e5,stroke:#6c757d,color:#383d41
  classDef unit fill:#cce5ff,stroke:#004085,color:#004085
  classDef req fill:#ffffff,stroke:#333,color:#111
  classDef ev fill:#f8f9fa,stroke:#adb5bd,color:#495057
  subgraph SG_REQ_PLAT_TENANT_ISOLATION_001["REQ_PLAT_TENANT_ISOLATION_001"]
    REQ_PLAT_TENANT_ISOLATION_001["한 사용자는 다른 사용자의 세션/파일/이력을 읽거나 쓸 수 없다 (fail-clos…"]:::req
    OBL_SESS_READ_CROSS_USER_404["✅ OBL_SESS_READ_CROSS_USER_404<br/>(behavior)"]:::closed
    REQ_PLAT_TENANT_ISOLATION_001 --> OBL_SESS_READ_CROSS_USER_404
    OBL_SESS_WRITE_CROSS_USER_404["✅ OBL_SESS_WRITE_CROSS_USER_404<br/>(behavior)"]:::closed
    REQ_PLAT_TENANT_ISOLATION_001 --> OBL_SESS_WRITE_CROSS_USER_404
    OBL_SESS_HISTORY_STATE_CROSS_USER_DENIED["✅ OBL_SESS_HISTORY_STATE_CROSS_USER_DENIED<br/>(behavior)"]:::closed
    REQ_PLAT_TENANT_ISOLATION_001 --> OBL_SESS_HISTORY_STATE_CROSS_USER_DENIED
    OBL_FS_AUTHZ_FAIL_CLOSED["✅ OBL_FS_AUTHZ_FAIL_CLOSED<br/>(behavior)"]:::closed
    REQ_PLAT_TENANT_ISOLATION_001 --> OBL_FS_AUTHZ_FAIL_CLOSED
    OBL_PATH_TRAVERSAL_DENIED["✅ OBL_PATH_TRAVERSAL_DENIED<br/>(behavior)"]:::closed
    REQ_PLAT_TENANT_ISOLATION_001 --> OBL_PATH_TRAVERSAL_DENIED
    OBL_SESS_AUTHORIZE_NO_FAIL_OPEN["❌ OBL_SESS_AUTHORIZE_NO_FAIL_OPEN<br/>(concurrent)"]:::refuted
    REQ_PLAT_TENANT_ISOLATION_001 --> OBL_SESS_AUTHORIZE_NO_FAIL_OPEN
    OBL_ACTIVATE_ENV_NO_CROSS_LEAK["❌ OBL_ACTIVATE_ENV_NO_CROSS_LEAK<br/>(behavior)"]:::refuted
    REQ_PLAT_TENANT_ISOLATION_001 --> OBL_ACTIVATE_ENV_NO_CROSS_LEAK
  end
  subgraph SG_REQ_PLAT_MEMORY_DURABILITY_001["REQ_PLAT_MEMORY_DURABILITY_001"]
    REQ_PLAT_MEMORY_DURABILITY_001["에이전트 메모리는 재시작·파손에도 보존/복구되고 사용자별로 격리된다…"]:::req
    OBL_MEM_PREF_PERSIST_RELOAD["✅ OBL_MEM_PREF_PERSIST_RELOAD<br/>(content)"]:::closed
    REQ_PLAT_MEMORY_DURABILITY_001 --> OBL_MEM_PREF_PERSIST_RELOAD
    OBL_MEM_CORRUPT_STORE_RECOVERY["✅ OBL_MEM_CORRUPT_STORE_RECOVERY<br/>(behavior)"]:::closed
    REQ_PLAT_MEMORY_DURABILITY_001 --> OBL_MEM_CORRUPT_STORE_RECOVERY
    OBL_MEM_USER_ISOLATION["✅ OBL_MEM_USER_ISOLATION<br/>(content)"]:::closed
    REQ_PLAT_MEMORY_DURABILITY_001 --> OBL_MEM_USER_ISOLATION
    OBL_MEM_EXPORT_IMPORT_ROUNDTRIP["✅ OBL_MEM_EXPORT_IMPORT_ROUNDTRIP<br/>(content)"]:::closed
    REQ_PLAT_MEMORY_DURABILITY_001 --> OBL_MEM_EXPORT_IMPORT_ROUNDTRIP
    OBL_MEM_ABS_PATH_RESPECTED["❌ OBL_MEM_ABS_PATH_RESPECTED<br/>(structural)"]:::refuted
    REQ_PLAT_MEMORY_DURABILITY_001 --> OBL_MEM_ABS_PATH_RESPECTED
  end
  subgraph SG_REQ_PLAT_LLM_FAILURE_VISIBILITY_001["REQ_PLAT_LLM_FAILURE_VISIBILITY_001"]
    REQ_PLAT_LLM_FAILURE_VISIBILITY_001["LLM 호출 실패는 절대 정상 결과로 둔갑하지 않는다 (green-while-bro…"]:::req
    OBL_MEM_EXTRACT_LLM_FAIL_DISTINGUISHABLE["❌ OBL_MEM_EXTRACT_LLM_FAIL_DISTINGUISHABLE<br/>(behavior)"]:::refuted
    REQ_PLAT_LLM_FAILURE_VISIBILITY_001 --> OBL_MEM_EXTRACT_LLM_FAIL_DISTINGUISHABLE
    OBL_COMPRESS_LLM_FAIL_SURFACED["❌ OBL_COMPRESS_LLM_FAIL_SURFACED<br/>(behavior)"]:::refuted
    REQ_PLAT_LLM_FAILURE_VISIBILITY_001 --> OBL_COMPRESS_LLM_FAIL_SURFACED
  end
  subgraph SG_REQ_PLAT_DEV_TRACEABILITY_001["REQ_PLAT_DEV_TRACEABILITY_001"]
    REQ_PLAT_DEV_TRACEABILITY_001["플랫폼의 모든 개발 약속은 기계 추적 가능하다 (선언→증거→판정)…"]:::req
    OBL_ONTOLOGY_DECLARED_PATHS_REAL["✅ OBL_ONTOLOGY_DECLARED_PATHS_REAL<br/>(structural)"]:::closed
    REQ_PLAT_DEV_TRACEABILITY_001 --> OBL_ONTOLOGY_DECLARED_PATHS_REAL
    OBL_NEW_MODULE_REGISTERED["✅ OBL_NEW_MODULE_REGISTERED<br/>(structural)"]:::closed
    REQ_PLAT_DEV_TRACEABILITY_001 --> OBL_NEW_MODULE_REGISTERED
    OBL_SPINE_INTEGRITY_ENFORCED["✅ OBL_SPINE_INTEGRITY_ENFORCED<br/>(structural)"]:::closed
    REQ_PLAT_DEV_TRACEABILITY_001 --> OBL_SPINE_INTEGRITY_ENFORCED
  end
  U_agent_compression["agent.compression<br/>L3 E2E"]:::unit
  U_agent_memory["agent.memory<br/>L2 내용검증"]:::unit
  U_api_sessions["api.sessions<br/>L2 내용검증"]:::unit
  U_platform_ontology["platform.ontology<br/>L2 내용검증"]:::unit
  U_runtime_authz["runtime.authz<br/>L2 내용검증"]:::unit
  OBL_SESS_READ_CROSS_USER_404 --> U_api_sessions
  OBL_SESS_READ_CROSS_USER_404 -.-> E_0
  OBL_SESS_WRITE_CROSS_USER_404 --> U_api_sessions
  OBL_SESS_WRITE_CROSS_USER_404 -.-> E_0
  OBL_SESS_WRITE_CROSS_USER_404 -.-> E_0
  OBL_SESS_HISTORY_STATE_CROSS_USER_DENIED --> U_api_sessions
  OBL_SESS_HISTORY_STATE_CROSS_USER_DENIED -.-> E_0
  OBL_SESS_HISTORY_STATE_CROSS_USER_DENIED -.-> E_0
  OBL_FS_AUTHZ_FAIL_CLOSED --> U_runtime_authz
  OBL_FS_AUTHZ_FAIL_CLOSED -.-> E_1
  OBL_FS_AUTHZ_FAIL_CLOSED -.-> E_1
  OBL_PATH_TRAVERSAL_DENIED --> U_runtime_authz
  OBL_PATH_TRAVERSAL_DENIED -.-> E_1
  OBL_PATH_TRAVERSAL_DENIED -.-> E_0
  OBL_SESS_AUTHORIZE_NO_FAIL_OPEN --> U_api_sessions
  OBL_ACTIVATE_ENV_NO_CROSS_LEAK --> U_api_sessions
  OBL_MEM_PREF_PERSIST_RELOAD --> U_agent_memory
  OBL_MEM_PREF_PERSIST_RELOAD -.-> E_2
  OBL_MEM_CORRUPT_STORE_RECOVERY --> U_agent_memory
  OBL_MEM_CORRUPT_STORE_RECOVERY -.-> E_2
  OBL_MEM_CORRUPT_STORE_RECOVERY -.-> E_2
  OBL_MEM_USER_ISOLATION --> U_agent_memory
  OBL_MEM_USER_ISOLATION -.-> E_2
  OBL_MEM_EXPORT_IMPORT_ROUNDTRIP --> U_agent_memory
  OBL_MEM_EXPORT_IMPORT_ROUNDTRIP -.-> E_2
  OBL_MEM_ABS_PATH_RESPECTED --> U_agent_memory
  OBL_MEM_EXTRACT_LLM_FAIL_DISTINGUISHABLE --> U_agent_memory
  OBL_COMPRESS_LLM_FAIL_SURFACED --> U_agent_compression
  OBL_ONTOLOGY_DECLARED_PATHS_REAL --> U_platform_ontology
  OBL_ONTOLOGY_DECLARED_PATHS_REAL -.-> E_3
  OBL_NEW_MODULE_REGISTERED --> U_platform_ontology
  OBL_NEW_MODULE_REGISTERED -.-> E_3
  OBL_SPINE_INTEGRITY_ENFORCED --> U_platform_ontology
  OBL_SPINE_INTEGRITY_ENFORCED -.-> E_3
  OBL_SPINE_INTEGRITY_ENFORCED -.-> E_3
  E_0["test_api_sessions_content.py"]:::ev
  E_1["test_fs_authz.py"]:::ev
  E_2["test_agent_memory_content.py"]:::ev
  E_3["test_platform_ontology.py"]:::ev
```

## DevUnit 성숙도 (전체 19 units)

```mermaid
flowchart TB
  subgraph L3["L3 E2E (2)"]
    M_agent_compression["agent.compression"]
    M_engine_stage["engine.stage"]
  end
  subgraph L2["L2 내용검증 (6)"]
    M_agent_tools["agent.tools"]
    M_runtime_authz["runtime.authz"]
    M_api_sessions["api.sessions"]
    M_task_todo_tracker["task.todo-tracker"]
    M_agent_memory["agent.memory"]
    M_platform_ontology["platform.ontology"]
  end
  subgraph L1["L1 단위테스트 (10)"]
    M_agent_react_loop["agent.react-loop"]
    M_agent_llm["agent.llm"]
    M_agent_slash["agent.slash"]
    M_runtime_session_worker["runtime.session-worker"]
    M_runtime_multiuser["runtime.multiuser"]
    M_runtime_server["runtime.server"]
    M_data_db["data.db"]
    M_api_jobs["api.jobs"]
    M_ui_tui["ui.tui"]
    M_platform_config["platform.config"]
  end
  subgraph L0["L0 존재 (1)"]
    M_ui_workspace["ui.workspace"]
  end
```
