# Tool Schema & Function Calling Guide

Concise runtime directives (`R-TOOL-01`–`R-TOOL-12`) and exact provider wire contracts for OpenAI, Anthropic, and Google Gemini. Full citations, tested models, and statistical tables live in [evidence/evidence_ledger.md](https://github.com/floydous/agent-system-authoring/blob/main/evidence/evidence_ledger.md).

---

### R-TOOL-01 & R-TOOL-02: Semantic `snake_case` Naming (`T4` + `T5` + `Project convention`)
- **Why**: Opaque names (`tool_1`, `handler`) hurt tool routing, and inconsistent casing alters BPE subword segmentation.
- **Directive**:
  - Use descriptive `[verb]_[noun]` names in `snake_case` across all tool names and parameter keys (prefix with service name when spanning multiple services, e.g., `billing_query_ledger`, `github_list_prs`).

### R-TOOL-03: Detailed Multi-Part Descriptions & Sister-Tool Boundaries (`T3`, absorbs `R-TOOL-09`)
- **Why**: Tool descriptions are the primary signal for routing; Markdown `###` headers inside descriptions burn extra prompt tokens without improving selection over plain prose.
- **Directive**:
  - Write `3–4+` sentences of plain prose covering: (1) what the tool does, (2) when to use it, (3) explicit negative boundaries naming adjacent sister tools (`"Do NOT use for billing disputes; use query_billing_ledger instead"`), (4) key parameter behavior, and (5) caveats/limitations.

### R-TOOL-04: Description Neutrality (`T2`)
- **Why**: Promotional superlatives (`"best"`, `"preferred"`, `"always use first"`) reliably hijack tool routing across architectures, overriding legitimate sister tools.
- **Directive**:
  - Keep descriptions strictly factual and neutral; remove all promotional superlatives. Neutral usage examples are safe.

### R-TOOL-05: Concise Parameter Descriptions & Structural Constraints (`T2` + `T1`)
- **Why**: Omitting parameter descriptions collapses formatting validity on non-obvious syntax/units and increases model thinking tokens; bloated multi-paragraph descriptions waste prompt tokens with no accuracy gain.
- **Directive**:
  - Write a concise `description` (`~15–50` tokens) on every parameter stating exact syntax examples, no-space separators (e.g., `"lat,lon"`), units (`cents`, `ms`, `USD`), ISO formats (`YYYY-MM-DD`, ISO 4217), date-interval inclusivity (`[start, end)`), formulas, and bounds.
  - Pair descriptions with **provider-supported** JSON Schema validation keywords (see `R-TOOL-10` below).

### R-TOOL-06 & R-TOOL-07: Closed Enums vs. High-Cardinality Catalogs (`T1` + `T3`)
- **Why**: Small `enum` arrays guarantee valid values at decode time, but giant enums hit provider grammar limits (OpenAI caps `1,000` enum values / `15,000` chars when > `250` values; Gemini rejects oversized state machines with `400 INVALID_ARGUMENT`).
- **Directive**:
  - Use `enum` for small closed sets (document each value's meaning in `description`; avoid case-only distinctions).
  - Replace high-cardinality catalogs (hundreds of SKUs, merchant codes, airport codes) with a plain `string` parameter plus a companion lookup/search tool.

### R-TOOL-08: Compact Active Tool Catalogs (`T4` + `T3`)
- **Why**: Every in-context tool schema multiplies prompt token cost on every turn and degrades routing on weaker/longer-context models.
- **Directive**:
  - Keep active in-context tool catalogs small via dynamic retrieval or consolidated multi-action tools instead of dumping entire enterprise catalogs into every call.

---

### R-TOOL-10: Exact Provider Wire Shapes & Keyword Matrix (`T1`)
Never mix top-level `"name"`/`"strict"` directly alongside `"$schema"`/`"properties"`, and never assume one provider's strict keywords work on another.

#### 1. OpenAI Chat Completions (`strict: true`)
```json
{
  "type": "function",
  "function": {
    "name": "query_billing_ledger",
    "description": "Searches posted customer ledger entries by account and date window...",
    "strict": true,
    "parameters": {
      "type": "object",
      "properties": {
        "account_id": { "type": "string", "pattern": "^ACC-[0-9]{6}$", "description": "Account ID, e.g. ACC-004219." },
        "currency": { "type": ["string", "null"], "description": "Optional ISO 4217 currency code (e.g. USD), or null for all." }
      },
      "required": ["account_id", "currency"],
      "additionalProperties": false
    }
  }
}
```
- **Rules**: `additionalProperties: false` on every object; **all** property keys must be in `required` (encode optional fields as nullable `["string", "null"]` or `anyOf` with `{"type": "null"}`).
- **Supported keywords**: `pattern`, `format` (`date-time`, `time`, `date`, `duration`, `email`, `hostname`, `ipv4`, `ipv6`, `uuid`), `minimum`/`maximum`/`exclusiveMinimum`/`exclusiveMaximum`/`multipleOf`, `minItems`/`maxItems` (`minLength`/`maxLength` are not supported).

#### 2. OpenAI Responses API (`strict: true`)
```json
{
  "type": "function",
  "name": "create_refund_ticket",
  "description": "Creates a refund ticket in the billing queue...",
  "strict": true,
  "parameters": {
    "type": "object",
    "properties": { "...": {} },
    "required": ["...all keys..."],
    "additionalProperties": false
  }
}
```
- **Rules**: **Flat** top-level wrapper (NO nested `"function": {...}` object). Same `additionalProperties: false`, all-keys-`required`, and keyword rules inside `parameters`.

#### 3. Anthropic Messages API (`strict: true`)
```json
{
  "name": "issue_credit_memo",
  "description": "Issues a billing credit memo for a verified account...",
  "strict": true,
  "input_schema": {
    "type": "object",
    "properties": {
      "account_id": { "type": "string", "pattern": "^ACC-[0-9]{6}$", "description": "Account ID (8-24 chars)." },
      "credit_cents": { "type": "integer", "description": "Integer cents between 100 and 500000 inclusive." },
      "memo_note": { "type": "string", "description": "Optional note (max 200 chars)." }
    },
    "required": ["account_id", "credit_cents"],
    "additionalProperties": false
  }
}
```
- **Rules**: Uses `"input_schema"` (never `"parameters"` or `"type": "function"`). Optional fields stay **outside** `required`; `additionalProperties: false` required. Caps: `20` strict tools / `24` optional params / `16` unions; `required` keys emit before optional keys.
- **Supported keywords**: `format`, simple `pattern` (no lookarounds, backreferences, `\b`/`\B`, or large `{n,m}`), `minItems` (`0` or `1` only).
- **Triggers HTTP `400` (MUST OMIT from schema)**: `minimum`, `maximum`, `multipleOf`, `minLength`, `maxLength`, `maxItems` — put those bounds in `description` + client-side validation.

#### 4. Google Gemini Function Calling (No `"strict": true`)
```json
{
  "name": "schedule_account_audit",
  "description": "Schedules an automated ledger audit for an account...",
  "parametersJsonSchema": {
    "type": "object",
    "properties": { "...": {} },
    "required": ["account_id"],
    "additionalProperties": false
  }
}
```
- **Rules**: Never include `"strict": true`.
  - **`parametersJsonSchema`** (`parameters_json_schema` in Python SDK — **preferred**): Standard JSON Schema supporting `pattern`, `format`, `minimum`, `maximum`, `anyOf`, `$ref`, `type: "null"`, and `additionalProperties`. Keep regex patterns simple to avoid `400 INVALID_ARGUMENT`.
  - **`parameters`** (legacy OpenAPI 3.0 subset): Supports `minimum`, `maximum`, `format` (`date-time`, `date`, `time`), `minItems`, `maxItems`; silently strips `minLength`/`maxLength`/`uniqueItems` and omits `$ref`/`anyOf`/`pattern`.

---

### R-TOOL-11: In-Schema `rationale` Ordering (`T2` + `T4`)
- **Why**: Under autoregressive constrained JSON decoding **without** pre-emission thinking (`reasoning_effort="none"` or non-reasoning models), forcing a numeric answer before any scratchpad tokens collapses calculation accuracy; on native reasoning models, an extra `rationale` field just wastes tokens. Asking for `"step-by-step reasoning"` can also trigger Anthropic `reasoning_extraction` refusals.
- **Directive**:
  - **Omit `"rationale"`** on standard reasoning-model tools (starter: [tool_schema_template.json](../assets/templates/tool_schema_template.json)).
  - **Place `"rationale"` FIRST** in `properties` **only** when pre-emission thinking is absent or `reasoning_effort="none"` on multi-step calculations/routing (starter: [tool_schema_zero_reasoning_template.json](../assets/templates/tool_schema_zero_reasoning_template.json)). Ask for a concise supporting calculation/evidence summary — never `"think step by step"` — and put exact formulas, units, and bounds on sibling fields.

### R-TOOL-12: Multi-Turn Constraint Re-Anchoring (`T5`)
- **Why**: Beyond ~50% of a model's context window, primacy weakens relative to recency on smaller/older models.
- **Directive**:
  - In long multi-turn agent loops approaching heavy context utilization, re-anchor critical tool invariants near the active turn before irreversible tool calls.
