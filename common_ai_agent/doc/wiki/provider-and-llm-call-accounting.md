# Provider And LLM Call Accounting

## Provider Rule

GPT, DeepSeek, GLM, Kimi, Cursor CLI, and Claude CLI may all produce different
raw outputs. The workflow must normalize them into the same stage artifact
contract before writing files or updating todo state.

```text
raw provider output -> normalized artifact envelope -> workflow validator
```

Provider-specific adapters may parse response formats. They must not define
approval semantics.

## One LLM Call

Count one LLM call every time the workflow sends one prompt/request to a model
provider and receives one response.

Examples:

- `ssot-gen` prompt to `gpt-5.3-codex` = 1 LLM call.
- `rtl-gen` repair prompt to `deepseek` = 1 LLM call.
- `tb-gen` prompt to `kimi` = 1 LLM call.

Do not call these packets in user reports unless the code artifact explicitly
uses that name. Report as:

```text
SSOT LLM calls: 2
RTL LLM calls: 15
TB LLM calls: 1
Total LLM calls: 18
```

## Deterministic Stages

FL generation, CL generation, lint, sim, coverage, and audits may be
deterministic script stages. They still cost time, but they are not LLM calls
unless they explicitly invoke a provider.

Report them separately:

```text
Deterministic stages: FL PASS, CL PASS, lint PASS, sim FAIL
LLM calls: SSOT 2, RTL 15, TB 1
```

## Related

- [[golden-todo-evidence]]
- [[full-flow-pipeline]]
- [doc/ai_driven_ip_development_guide.md](../ai_driven_ip_development_guide.md)
