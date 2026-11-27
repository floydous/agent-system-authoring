# Engineering Guide: Tool Schemas & Function Calling

## Overview
This guide documents rules for designing tool and function schemas (JSON Schema, OpenAI Structured Outputs, Anthropic Tool Use, and Gemini Function Calling), tagged by evidence tier (`T1` Verified Fact, `T2` Measured Empirically across `GPT 6 Luna`, `Particle-1`, `Nemotron 3.5 Lightning`, and/or `Ling 3.2 Flash`, `T3` Current Vendor Guidance, `T4` Mechanism, `T5` Learned Behavior).

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
  Anthropic states: *"Provide extremely detailed descriptions. This is by far the most important factor in tool performance."* Descriptions should cover (1) what the tool does, (2) when it should be used and when it should **not** be used (mutual negative boundaries cross-referencing sister tools, formerly `R-TOOL-09`), (3) what each parameter means and how it affects behavior, and (4) caveats or data it does not return — aiming for **at least 3–4 sentences**, more if complex. Guo et al. demonstrated across `150+` candidate tools on StableToolBench that structured description rewriting reduces scaling degradation by `29.23%` and boosts query success by `60.89%`. In counterbalanced `PD-3` on `GPT 6 Luna` (`16` prompts × `5`, `effort="none"`, wording equalized), plain prose (`0.950`), bullets (`0.950`, `p = 1.0000`), and `###` Markdown headers (`0.975`, `t(15) = 1.00, p = 0.3332`) showed no significant routing difference, while `###` headers added `+43.4` prompt tokens (`+13.6%`, `p = 1.692e-20`).
- **Schema Directive**:
  - Write at least `3–4` sentences of clear plain prose (more for complex tools) covering purpose, positive triggers, explicit negative boundaries referencing adjacent tools by name, parameter behavior, and caveats.

---

### R-TOOL-04: Description Neutrality & Anti-Gaming Hygiene
- **Evidence Tier**: **T2 (Measured across 4 model families & 3 architectures: `GPT 6 Luna`, `Particle-1`, `Nemotron 3.5 Lightning`, `Ling 3.2 Flash`)** + **T5** (`Faghih et al.`)
- **Primary Citations**:
  - `PC-1`, `H08-PC1`, `NEMO-PC1`, `LING-PC1` (`16` counterbalanced prompts × `5`) & `PB-2` in [stats_recomputed.md](https://github.com/floydous/agent-system-authoring/blob/main/evidence/stats_recomputed.md).
  - Faghih, Wang, Cheng, Bharti, Sriramanan, Balasubramanian, Hosseini, & Feizi (May 2025 / EMNLP 2025), *Tool Preferences in Agentic LLMs are Unreliable*, [arXiv:2505.18135](https://arxiv.org/abs/2505.18135).
- **Models Tested**: `GPT 6 Luna` (`PC-1`); `Particle-1` (`H08-PC1`); `Nemotron 3.5 Lightning` Mamba-2 SSM (`NEMO-PC1`); `Ling 3.2 Flash` Hybrid-Linear MoE (`LING-PC1`); `17` models (Faghih et al.).
- **Verified `T2` Finding (Counterbalanced `50/50` Across 4 Families & 3 Architectures)**:
  Under neutral and `example_on_second` descriptions, models either hedged via parallel dual calls (`Luna`, `Particle-1`, `Ling`: `67–79/80` parallel-both) or picked Position 0 (`Nemotron`: `77/80` first-only), with zero significant hijacking from neutral examples (`0/80` on `Luna`/`Particle-1`/`Ling`, `6/80` `p = 0.4564` on `Nemotron`). Appending assertive promotional superlatives flipped exclusive `second_tool` selection across **`16/16` prompts on all four families**: **`80/80` (`100%`) on `Luna` and `Ling`**, **`75/80` (`93.8%`, `p = 4.79e-15`) on `Particle-1`**, and **`79/80` (`98.8%`, `p = 4.77e-17`) on `Nemotron`** — while also short-circuiting deliberation on both `Nemotron` (`-51.1` rtok, `p = 1.35e-06`) and `Ling` (`-47.7` rtok, `p = 2.48e-07`).
- **Schema Directive**:
  - Keep tool descriptions objective and strictly neutral; omit promotional superlatives (`"best"`, `"preferred"`, `"invoke whenever possible"`). Neutral usage examples alone did not bias selection across any tested architecture.

---

### R-TOOL-05: Parameter Descriptions & Provider-Supported Structural Constraints
- **Evidence Tier**: **T2 (Measured across 4 model families & 3 architectures: `GPT 6 Luna`, `Particle-1`, `Nemotron 3.5 Lightning`, `Ling 3.2 Flash`)** + **T1** + **T5** (`ToolSandbox`)
- **Primary Citations**:
  - `PD-1`, `H08-PD1`, `NEMO-PD1`, `LING-PD1`, `PD-2` & `TS-2` in [stats_recomputed.md](https://github.com/floydous/agent-system-authoring/blob/main/evidence/stats_recomputed.md).
  - OpenAI / Anthropic / Gemini JSON Schema validation-keyword checks ([source_checks.md](https://github.com/floydous/agent-system-authoring/blob/main/evidence/source_checks.md)).
  - Lu et al. (ToolSandbox, NAACL 2025 Findings), [arXiv:2408.04682](https://arxiv.org/abs/2408.04682).
- **Models Tested**: `GPT 6 Luna` (`PD-1`/`PD-2`); `Particle-1` (`H08-PD1`); `Nemotron 3.5 Lightning` Mamba-2 SSM (`NEMO-PD1`); `Ling 3.2 Flash` Hybrid-Linear MoE (`LING-PD1`); ToolSandbox models.
- **Verified `T2` Findings (Prompt-Level `N = 5` Across 4 Families & 3 Architectures)**:
  - **Cross-Architecture `N = 5` Replication (`75` runs/arm)**: Omitting parameter descriptions collapsed overall validity to **`2.7%` (`2/75`, Luna)**, **`6.7%` (`5/75`, `Particle-1`)**, **`8.0%` (`6/75`, `Nemotron`)**, and **`5.3%` (`4/75`, `Ling`, `p = 2.796e-14`)** vs **`100.0%` (`75/75`)** with descriptions on all four families. Explicit descriptions also **reduced reasoning tokens on all four families** (`-5.6` Luna, `-19.7` `Particle-1`, **`-469.5` [`-45.0%`] `Nemotron`**, `-20.8` `Ling` `p = 0.0005`).
  - **Verbosity Curve (`PD-2`, `320` calls, `GPT 6 Luna`, `effort="none"`)**: `compact_15t` (`412.1` prompt tok) through `bloated_250t` (`2,375.1`) all achieved **`80/80` (`100.0%`)** — confirming compact descriptions (`~15–50` tokens/param) avoid `5.8×` prompt-token bloat (`+1,963` tok/call) with zero accuracy sacrifice.
- **Schema Directive**:
  - Provide a concise, explicit `description` (`~15–50` tokens) for every parameter stating exact syntax examples, spacing rules (e.g., `"lat,lon"`), ISO code requirements, units, timezones, and bounds; avoid bloated multi-paragraph prose.
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
  4. **Google Gemini Function Calling**: Supports two declaration fields (no `"strict": true` toggle; optional fields omitted from `required` by default):
     - **`parametersJsonSchema`** (SDK: `parameters_json_schema`, preferred for modern Gemini API): Standard JSON Schema object (`{"name", "description", "parametersJsonSchema": {"type": "object", "properties": {...}, "required": [...mandatory only...], "additionalProperties": false}}`), supporting `pattern`, `format`, `minimum`, `maximum`, `anyOf`, `$ref`, `type: "null"`, and `additionalProperties`. Keep regex patterns simple to avoid `400 INVALID_ARGUMENT` state-machine complexity errors.
     - **`parameters`** (legacy OpenAPI 3.0 subset): Declaration `{"name": "...", "description": "...", "parameters": {"type": "object", "properties": {...}, "required": [...mandatory only...]}}`; enforces `minimum`, `maximum`, `format` (`date-time`, `date`, `time`), `minItems`, `maxItems`, silently strips `minLength`, `maxLength`, `minProperties`, `maxProperties`, `uniqueItems`, and does not list `pattern` in the OpenAPI subset. Mark fields `required` with nullable types only if grammar branching causes `400 INVALID_ARGUMENT`.
- **Schema Directive**:
  - Match your target provider's exact wire wrapper (`function.parameters` vs top-level `parameters` vs `input_schema` vs Gemini `parametersJsonSchema`/`parameters`), set `"additionalProperties": false` and `"required"` conventions per provider, and attach structural validation keywords only within that provider's supported subset (putting unsupported bounds in `description` + client validation).

---

### R-TOOL-11: In-Schema `rationale` Field Strictly When Pre-Emission Thinking Is Absent
- **Evidence Tier**: **T2 (Measured across 3 architectures: `GPT 6 Luna` `PB-6`, `Nemotron 3.5 Lightning` Mamba-2 SSM `NEMO-PB6`, `Ling 3.2 Flash` KDA+MLA MoE `LING-PB6`)** + **T4 (Mechanism: autoregressive left-to-right constrained decoding)**
- **Primary Citations**:
  - `LING-PB6`, `NEMO-PB6` (`16` prompts × `5`, `thinking_off`, `rtok = 0`), `PB-6` (`reasoning_effort = "none"`) & `TS-3` (`xhigh`) in [stats_recomputed.md](https://github.com/floydous/agent-system-authoring/blob/main/evidence/stats_recomputed.md).
  - Tam, Wu, Tsai, Lin, Lee, & Chen (Aug 2024 / EMNLP 2024), *Let Me Speak Freely?*, [arXiv:2408.02442](https://arxiv.org/abs/2408.02442).
  - Nguyen et al. (Jan 2026), *Thinking Before Constraining*, [arXiv:2601.07525](https://arxiv.org/abs/2601.07525) & Anthropic `define-tools`.
- **Models Tested**: `GPT 6 Luna` (`PB-6`, `TS-3`); `Nemotron 3.5 Lightning` Mamba-2 SSM (`NEMO-PB6`); `Ling 3.2 Flash` Hybrid-Linear KDA+MLA MoE (`LING-PB6`); non-reasoning LLMs (Tam et al., Nguyen et al.).
- **Verified `T2` & `T4` Result Across 3 Distinct Architectures (`reasoning_tokens = 0`)**:
  - **`Ling 3.2 Flash` (`LING-PB6`, KDA+MLA MoE, `16 × 5`, `240/240` exact key order)**: `no_rationale` **`24/80` (`30.0%`)** and `rationale_last` **`29/80` (`36.2%`, `p = 0.0962`)** vs **`rationale_first` `76/80` (`95.0%`, `t(15) = 5.01, p = 0.0002`, `sign 13+/1-, p = 0.0018`)**.
  - **`Nemotron 3.5 Lightning` (`NEMO-PB6`, Mamba-2 SSM, `16 × 5`, `240/240` exact key order)**: `no_rationale` and `rationale_last` both **`0/80` (`0.0%`)** vs **`rationale_first` `69/80` (`86.2%`, `t(15) = 19.75, p = 3.773e-12`, `sign 16+/0-, p = 3.052e-05`)**.
  - **`GPT 6 Luna` (`PB-6`, `6 × 5`)**: `no_rationale` and `rationale_last` both **`11/30` (`36.7%`)** vs **`rationale_first` `30/30` (`100.0%`, `t(5) = 3.12, p = 0.0261`)**. Under `xhigh` pre-emission reasoning (`TS-3`), all orderings scored `15/15` (`100%`). Note that Anthropic `strict: true` preserves declared ordering only for `required` properties ahead of optional properties.
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
