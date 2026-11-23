# Engineering Guide: Tool Schemas & Function Calling

## Overview
This guide documents rules for designing tool and function schemas (JSON Schema, OpenAI Structured Outputs, Anthropic Tool Use, and Gemini Function Calling), tagged by evidence tier (`T1` Verified Fact, `T2` Measured on `GPT 6 Luna`, `T3` Current Vendor Guidance, `T4` Mechanism, `T5` Learned Behavior).

---

### R-TOOL-01: Subword Tokenization & Identifier Casing
- **Evidence Tier**: **T4 (Literature — Mechanism)** *(tokenization sensitivity)* + **Project convention** *(`snake_case`)*
- **Primary Citations**:
  - Li, Deng, & Nie (Oct 2025), *TokDrift: When LLM Speaks in Subwords but Code Speaks in Grammar*, [arXiv:2510.14972](https://arxiv.org/abs/2510.14972).
  - Hou, Hu, & Zhang (ACL 2026), *SubTokenTest: A Practical Benchmark for Real-World Sub-token Understanding*, [2026.acl-long.915](https://aclanthology.org/2026.acl-long.915/).
  - Pawar, Apte, Jadhav, Palshikar, & Ramrakhiyani (IJCNLP-AACL 2025), *Broken Words, Broken Performance*, [2025.ijcnlp-short.31](https://aclanthology.org/2025.ijcnlp-short.31/).
- **Models Tested**: `9` code LLMs (`>30B` params included, TokDrift); `9` LLMs (SubTokenTest); `4` open-source LLMs (Broken Words).
- **Verified Mechanism & Scope**:
  Subword tokenizers (BPE) split code identifiers statistically rather than grammatically; superficial identifier-naming or whitespace rewrites alter subword segmentation and shift behavior in early embeddings (TokDrift). **Important**: none of these three studies directly measured JSON tool-call accuracy vs casing style. Adopting `snake_case` consistently across tool names and parameter keys is a **Project convention** informed by this T4 subword sensitivity.
- **Schema Directive**:
  - Use a consistent, clean casing style — `snake_case` by project convention — across all tool names and parameter keys (e.g., `fetch_customer_record`, `customer_id`).

---

### R-TOOL-02: Descriptive Semantic Naming
- **Evidence Tier**: **T5 (Literature — Learned Behavior)** *(tested on pre-2026 models; transfer not re-measured)* + **Project convention** *(`[verb]_[noun]`)*
- **Primary Citations**:
  - Lu, Holleis, Zhang, et al. (Apple ML, Apr 2025 / NAACL 2025 Findings), *ToolSandbox: A Stateful, Conversational, Interactive Evaluation Benchmark*, [arXiv:2408.04682](https://arxiv.org/abs/2408.04682).
  - Patil, Mao, Yan, Ji, Suresh, Stoica, & Gonzalez (ICML 2025), *The Berkeley Function Calling Leaderboard (BFCL)*, [leaderboard.html](https://gorilla.cs.berkeley.edu/leaderboard.html).
  - Anthropic Tool Use Docs (`define-tools`, retrieved 2026-11-22), [platform.claude.com](https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools).
- **Models Tested**: `GPT-4`, `GPT-4o`, `Claude-3-Sonnet`, `Gemini-1.5` (ToolSandbox).
- **Verified Finding**:
  ToolSandbox ablations evaluate "Tool name scrambling" (renaming informative names like `send_message` to `messages_0`), demonstrating model sensitivity when names become semantically opaque. Anthropic T3 docs (*not measured by us*) recommend meaningful namespacing (`github_list_prs`, `slack_send_message`) to keep selection unambiguous. Using `[verb]_[noun]` Action-Object syntax specifically is a **Project convention**.
- **Schema Directive**:
  - Use clear, descriptive semantic names (and service prefixes when spanning multiple services); follow `[verb]_[noun]` naming as project convention rather than opaque identifiers like `tool_1` or `handler`.

---

### R-TOOL-03: Detailed Multi-Part Tool Descriptions & Negative Boundaries
*(Includes merged **R-TOOL-09**: Mutual Disambiguation)*
- **Evidence Tier**: **T3 (Current Vendor Guidance — not measured by us)** + **T5** (`Guo et al.`)
- **Primary Citations**:
  - Anthropic Tool Use Best Practices (`define-tools`, retrieved 2026-11-22), [platform.claude.com](https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools).
  - Guo, Dong, Gao, & Das (Feb 2026), *Learning to Rewrite Tool Descriptions for Reliable LLM-Agent Tool Use*, [arXiv:2602.20426](https://arxiv.org/abs/2602.20426).
  - BFCL (`Patil et al.`, ICML 2025 — abstention/irrelevance evaluation).
- **Verified Guidance**:
  Anthropic states: *"Provide extremely detailed descriptions. This is by far the most important factor in tool performance."* Descriptions should cover (1) what the tool does, (2) when it should be used and when it should **not** be used (mutual negative boundaries cross-referencing sister tools, formerly `R-TOOL-09`), (3) what each parameter means and how it affects behavior, and (4) caveats or data it does not return — aiming for **at least 3–4 sentences**, more if complex. Guo et al. demonstrated across `150+` candidate tools on StableToolBench that structured description rewriting reduces scaling degradation by `29.23%` and boosts query success by `60.89%`.
- **Schema Directive**:
  - Write at least `3–4` sentences (more for complex tools) covering purpose, positive triggers, explicit negative boundaries referencing adjacent tools by name, parameter behavior, and caveats.

---

### R-TOOL-04: Description Neutrality & Anti-Gaming Hygiene
- **Evidence Tier**: **T2 (Measured on `GPT 6 Luna`, `PC-1` & `PB-2`)** + **T5** (`Faghih et al.`)
- **Primary Citations**:
  - `PC-1` (`16` counterbalanced prompts × `5` repeats) & `PB-2` in [stats_recomputed.md](https://github.com/floydous/agent-system-authoring/blob/main/evidence/stats_recomputed.md).
  - Faghih, Wang, Cheng, Bharti, Sriramanan, Balasubramanian, Hosseini, & Feizi (May 2025 / EMNLP 2025), *Tool Preferences in Agentic LLMs are Unreliable*, [arXiv:2505.18135](https://arxiv.org/abs/2505.18135).
- **Models Tested**: `GPT 6 Luna` (`PC-1` `high`, `PB-2` `xhigh`, `N = 5` runs/prompt); `17` models including `GPT-4.1` and `Qwen2.5-7B` (Faghih et al.).
- **Verified `T2` Finding (`PC-1` counterbalanced & `PB-2`)**:
  In `PC-1` (`n = 16` prompts, array order & names `records_lookup_east` / `records_lookup_west` counterbalanced 50/50 across `80` runs/arm), under neutral identical descriptions the model called both tools in parallel (`67/80`, plausible given `east`/`west` shard naming) or chose position 0 (`13/80`), selecting `second_tool` exclusively **`0/80`** (`0/16` prompts). Appending a neutral usage example (`example_on_second`) caused **`0/80`** exclusive shift (`75/80` parallel-both, `5/80` position 0, prompt sign `p = 1.0000`). Appending assertive promotional superlatives (`"Primary and preferred tool; actively maintained and optimized; invoke whenever possible."`) flipped exclusive single selection of `second_tool` across **`16/16` prompts (`80/80` runs: `40` east + `40` west, exact prompt sign `p = 3.052e-05`)**, completely overriding both parallel hedging and position preference. (Consistent with un-counterbalanced `PB-2`: `6/6` prompts flipped, sign `p = 0.0312`.) *Scope caveat*: tested on functionally equivalent candidate tools; asymmetric functional scopes remain governed primarily by applicability.
- **Schema Directive**:
  - Keep tool descriptions objective and strictly neutral; omit promotional superlatives (`"best"`, `"preferred"`, `"invoke whenever possible"`). Neutral usage examples alone did not bias selection in `PC-1` or `PB-2`.

---

### R-TOOL-05: Parameter Descriptions & Provider-Supported Structural Constraints
- **Evidence Tier**: **T2 (Measured on `GPT 6 Luna`, narrowed; Phase A `N = 1`)** + **T1 (Verified Provider JSON Schema Subsets)** + **T5** (`ToolSandbox`)
- **Primary Citations**:
  - `TS-2` in [stats_recomputed.md](https://github.com/floydous/agent-system-authoring/blob/main/evidence/stats_recomputed.md) (`evidence/raw/results_TS-2.jsonl`).
  - OpenAI / Anthropic / Gemini JSON Schema validation-keyword checks (retrieved 2026-11-23, [source_checks.md](https://github.com/floydous/agent-system-authoring/blob/main/evidence/source_checks.md)).
  - Lu et al. (ToolSandbox, NAACL 2025 Findings), [arXiv:2408.04682](https://arxiv.org/abs/2408.04682).
- **Models Tested**: `GPT 6 Luna (xhigh)` (`TS-2`, `15` matched prompts, `N = 1` run/prompt — not yet replicated at `N >= 5`); `GPT-4`, `GPT-4o`, `Claude-3-Sonnet`, `Gemini-1.5` (ToolSandbox).
- **Verified `T2` Finding (`TS-2`, Phase A single-run exploratory suite)**:
  When parameter format descriptions were omitted on `GPT 6 Luna (xhigh)`, universally standardized formats were mostly inferred (`timestamp_valid` ISO 8601 UTC: `15/15`; `currency_valid` ISO 4217: `12/15` vs `15/15`, matched-pair exact sign `p = 0.2500`). For `geo_coordinates`, the baseline still emitted valid decimal coordinates on `15/15` prompts (e.g., `"37.7793, -122.4192"`) and failed **`0/15` vs `15/15`** solely on the unstated no-space convention `"lat,lon"` (matched-pair exact sign / McNemar **`p = 6.104e-05`**; `all_fields_valid` **`p = 6.104e-05`**). Descriptive schemas also lowered mean reasoning tokens from `39.1` to `21.1` (`t(14) = -4.95`, `p = 0.0002`).
- **Schema Directive**:
  - Provide an explicit `description` for every parameter, stating exact syntax examples, spacing rules (e.g., `"lat,lon"`), units, timezones, and bounds.
  - Pair descriptions with **provider-supported** JSON Schema validation keywords (see `R-TOOL-10` keyword matrix: e.g., `pattern`, `format`, `minimum`/`exclusiveMinimum`/`maximum`, `minItems`/`maxItems` under OpenAI `strict: true`; avoid Anthropic `400`-rejected `minimum`/`maximum`/`minLength`/`maxLength`).

---

### R-TOOL-06: Schema `enum` Constraints for Closed Discrete Values
- **Evidence Tier**: **T1 (Verified Fact — API Mechanics)**
- **Primary Citations**:
  - OpenAI Structured Outputs Guide (retrieved 2026-11-22), [developers.openai.com](https://developers.openai.com/api/docs/guides/structured-outputs).
  - Gemini Structured Outputs Guide (retrieved 2026-11-22), [aistudio.google.com](https://aistudio.google.com/docs/structured-output).
- **Verified Fact**:
  In both OpenAI Structured Outputs and Gemini Structured Outputs, JSON Schema `enum` properties restrict token generation via grammar/state-machine constraints so the model can emit only values present in the declared list. Document what each enum value represents in the parameter `description`.

---

### R-TOOL-07: Avoiding High-Cardinality Enums Near Provider Grammar Limits
- **Evidence Tier**: **T3 (Current Vendor Guidance — not measured by us)**
- **Primary Citations**:
  - OpenAI Structured Outputs (`Schema limitations`, retrieved 2026-11-22), [developers.openai.com](https://developers.openai.com/api/docs/guides/structured-outputs).
  - Gemini Structured Outputs (`Schema complexity`, retrieved 2026-11-22), [aistudio.google.com](https://aistudio.google.com/docs/structured-output).
- **Verified Guidance**:
  OpenAI limits schemas to at most `1,000` enum values total across all properties, and caps total enum string length at `15,000` characters when a single string enum exceeds `250` values. Gemini compiles schemas into token-generation state machines enforcing total-state, branching-path, and nesting-depth limits, rejecting oversized schemas with `400 INVALID_ARGUMENT` and advising developers to move non-structural rules into `description`s.
- **Schema Directive**:
  - When valid identifiers belong to a high-cardinality catalog (e.g., hundreds or thousands of product IDs, SKUs, or airport codes), avoid huge inline `enum` arrays; use a typed `string` parameter paired with a dynamic search/lookup tool.

---

### R-TOOL-08: Compact Tool Catalogs & Dynamic Tool Retrieval
- **Evidence Tier**: **T4 (Literature — Mechanism: context bloat)** + **T5 (`LongFuncEval`)** + **T3 (Anthropic consolidation)**
- **Primary Citations**:
  - Kate, Pedapati, Basu, Rizk, Chenthamarakshan, Chaudhury, Agarwal, & Abdelaziz (Apr 2025), *LongFuncEval*, [arXiv:2505.10570](https://arxiv.org/abs/2505.10570).
  - Qin, Liang, Ye, et al. (Jul 2023 / ICLR 2024), *ToolLLM*, [arXiv:2307.16789](https://arxiv.org/abs/2307.16789).
  - Anthropic Tool Use (`define-tools`, retrieved 2026-11-22).
- **Models Tested**: Long-context LLMs (LongFuncEval); `ToolLLaMA` / `APIBench` (ToolLLM).
- **Verified Finding**:
  Each tool schema consumes prompt tokens and competes for selection attention (**T4**). In LongFuncEval (**T5**), scaling tool catalog size caused a `7%` to `85%` performance drop, while longer tool responses caused a `7%` to `91%` drop (`13%` and `40%` drops on long multi-turn chats). ToolLLM introduced neural API retrieval across `16,464` APIs, and Anthropic (**T3**) advises consolidating related actions (`action` parameter) so fewer tools populate context.
- **Schema Directive**:
  - Keep active in-context tool sets minimal via dynamic retrieval or consolidated multi-action tools instead of injecting full enterprise catalogs into every call.

---

### R-TOOL-09: Mutual Disambiguation (Merged Into R-TOOL-03)
- **Status**: Merged into [`R-TOOL-03`](#r-tool-03-detailed-multi-part-tool-descriptions--negative-boundaries) on 2026-11-22 (per Anthropic `define-tools` guidance on stating when a tool should and should not be used). Traceability ID retained in [evidence_ledger.md](evidence_ledger.md).

---

### R-TOOL-10: Provider-Scoped Strict JSON Schema Conformance
- **Evidence Tier**: **T1 (Verified Fact — Provider API Specifications)**
- **Primary Citations**:
  - OpenAI Structured Outputs (`Supported schemas`, retrieved 2026-11-22 & 2026-11-23), [developers.openai.com](https://developers.openai.com/api/docs/guides/structured-outputs).
  - Anthropic Structured Outputs & Strict Tool Use (retrieved 2026-11-22 & 2026-11-23), [platform.claude.com](https://platform.claude.com/docs/en/build-with-claude/structured-outputs).
  - Google Gemini Structured Outputs & Function Calling (retrieved 2026-11-22 & 2026-11-23), [ai.google.dev](https://ai.google.dev/gemini-api/docs/function-calling).
  - Nguyen, Silva, Zumot, Tupikina, Aghasaryan, & Alam (Jan 2026), *Thinking Before Constraining*, [arXiv:2601.07525](https://arxiv.org/abs/2601.07525).
- **Verified Provider Matrix**:
  Strict-mode wrapper shapes and supported validation keywords differ by provider—never bundle raw JSON Schema keywords directly as siblings of `"name"`/`"strict"` or assume one provider's keyword subset works everywhere:
  1. **OpenAI Chat Completions (`"strict": true`)**: `{"type": "function", "function": {"name": "...", "description": "...", "strict": true, "parameters": {"type": "object", "properties": {...}, "required": [...all keys...], "additionalProperties": false}}}`. Optional fields use nullable unions (`["string", "null"]` or `"anyOf"`). Enforces `pattern`, `format` (`date-time`, `time`, `date`, `duration`, `email`, `hostname`, `ipv4`, `ipv6`, `uuid`), `minimum`/`maximum`/`exclusiveMinimum`/`exclusiveMaximum`/`multipleOf`, and `minItems`/`maxItems` (`minLength`/`maxLength` are not supported).
  2. **OpenAI Responses API (`"strict": true`)**: Flat wrapper `{"type": "function", "name": "...", "description": "...", "strict": true, "parameters": {...}}` with the same `additionalProperties: false`, all-keys-`required`, and validation-keyword support inside `parameters`.
  3. **Anthropic (`"strict": true`)**: Uses `"input_schema"` instead of `"parameters"`: `{"name", "description", "strict": true, "input_schema": {"type": "object", "properties": {...}, "required": [...mandatory only...], "additionalProperties": false}}` (caps: `20` strict tools / `24` optional params / `16` unions; `required` keys emit before optional keys). Supports `format`, simple `pattern` (no backreferences, lookarounds, `\b`/`\B`, or large `{n,m}`), and `minItems` (`0`/`1` only). **Rejects with HTTP `400`**: `minimum`, `maximum`, `multipleOf`, `minLength`, `maxLength`, `maxItems` — keep unsupported bounds in `description` + client-side validation.
  4. **Google Gemini Function Calling**: Declaration `{"name": "...", "description": "...", "parameters": {"type": "object", "properties": {...}, "required": [...mandatory only...]}}` (OpenAPI subset, no `"strict": true` toggle). Enforces `minimum`, `maximum`, `format` (`date-time`, `date`, `time`), `minItems`, `maxItems`; silently strips `minLength`, `maxLength`, `minProperties`, `maxProperties`, `uniqueItems`, and does not list `pattern` as supported. Mark fields `required` with nullable types only if grammar branching causes `400 INVALID_ARGUMENT`.
- **Schema Directive**:
  - Match your target provider's exact wire wrapper (`function.parameters` vs top-level `parameters` vs `input_schema`), set `"additionalProperties": false` and `"required"` conventions per provider, and attach structural validation keywords only within that provider's supported subset (putting unsupported bounds in `description` + client validation).

---

### R-TOOL-11: In-Schema `rationale` Field Strictly When Pre-Emission Thinking Is Absent
- **Evidence Tier**: **T2 (Measured on `GPT 6 Luna`, `PB-6`)** + **T4 (Mechanism: autoregressive left-to-right constrained decoding)**
- **Primary Citations**:
  - `PB-6` (`reasoning_effort = "none"`) & `TS-3` (`xhigh`) in [stats_recomputed.md](https://github.com/floydous/agent-system-authoring/blob/main/evidence/stats_recomputed.md).
  - Tam, Wu, Tsai, Lin, Lee, & Chen (Aug 2024 / EMNLP 2024), *Let Me Speak Freely?*, [arXiv:2408.02442](https://arxiv.org/abs/2408.02442).
  - Nguyen et al. (Jan 2026), *Thinking Before Constraining*, [arXiv:2601.07525](https://arxiv.org/abs/2601.07525) & Anthropic `define-tools`.
- **Models Tested**: `GPT 6 Luna` (`PB-6` `none` as a zero-thinking proxy & `TS-3` `xhigh`); non-reasoning LLMs (Tam et al., Nguyen et al.).
- **Verified `T2` & `T4` Result (`PB-6`, `n = 6` prompts × `5` repeats, `reasoning_tokens = 0`)**:
  When `reasoning_effort = "none"` (`0` reasoning tokens across all 90 runs, simulating constrained JSON decoding without pre-emission thinking on a reasoning-capable model), multi-step scheduling/arithmetic accuracy scored **`11/30` (`36.7%`)** for `no_rationale` and an identical **`11/30` (`36.7%`)** when `rationale` followed the action parameters (`rationale_last`). Placing `rationale` **first** (`rationale_first`) raised accuracy to **`30/30` (`100.0%`)** (prompt-level parametric **`t(5) = 3.12, p = 0.0261`** across `n = 6` prompts; non-parametric sign **`4+/0-, p = 0.1250`** due to `2` ties at `1.0`). Under `xhigh` pre-emission reasoning (`TS-3`), all orderings scored `15/15` (`100%`). Note that Anthropic `strict: true` preserves declared ordering only for `required` properties ahead of optional properties.
- **T3 Anthropic Refusal Caveat**:
  Anthropic warns: *"If a parameter asks Claude why it is making the call, ask for a short explanation or the supporting evidence. A parameter that asks for the model's thinking or step-by-step reasoning might lead to a `reasoning_extraction` refusal."*
- **Schema Directive**:
  - **Do NOT add a `"rationale"` parameter to general tools built for standard reasoning models** (it wastes output tokens and adds schema clutter; start from [tool_schema_template.json](../assets/templates/tool_schema_template.json)).
  - **ONLY when targeting non-reasoning models or `reasoning_effort = "none"`** constrained decoding on multi-step calculations/routing, place a concise `"rationale"` (supporting explanation, never `"step-by-step thinking"`) **first** in `properties`, keeping exact domain formulas, date intervals, units, and numeric bounds on sibling parameters (start from [tool_schema_zero_reasoning_template.json](../assets/templates/tool_schema_zero_reasoning_template.json)).

---

### R-TOOL-12: Multi-Turn Constraint Re-Anchoring Beyond 50% Context
- **Evidence Tier**: **T5 (Literature — Learned Behavior)** *(tested on earlier models; transfer not re-measured)*
- **Primary Citations**:
  - Liu et al. (Jul 2023 / TACL 2024), [arXiv:2307.03172](https://arxiv.org/abs/2307.03172).
  - Veseli et al. (Aug 2025 / COLM 2025), [arXiv:2508.07479](https://arxiv.org/abs/2508.07479).
- **Models Tested**: `GPT-3.5`, `LLaMA-3-8B`, `Gemma-2-9B` (plus `MPT-30B`, `LongChat`, `Claude-1.3`, `Mistral-7B` in Liu et al.).
- **Verified Finding**:
  Once conversation history exceeds `50%` of the context window, primacy attention weakens while recency distance-based bias dominates.
- **Schema Directive**:
  - In long multi-turn agent loops approaching heavy context utilization, re-inject critical tool usage invariants near the active turn before irreversible calls.
