---
name: agent-system-authoring
description: Authors and audits LLM system prompts, AI agent function-calling tool definitions (OpenAI, Anthropic, Gemini), and portable Agent Skill packages. Use when writing, refactoring, evaluating, or troubleshooting bot behavioral rules, prompt-injection boundaries, word exclusions, LLM tool-calling arguments or descriptions, or reusable Agent Skill folders—even in plain language without jargon. Do not use for general HTTP/REST API specs, app-config schemas, or application code.
license: MIT
metadata:
  author: "floydous"
  version: "2.0.0"
---

# Agent System Authoring

## Overview
Follow these directives to author production system prompts, multi-provider tool definitions, and portable Agent Skills (`T1` Verified Spec, `T2` Measured Empirically across multiple model architectures, `T3` Vendor Guidance, `T4` Mechanism, `T5` Pre-2026 Literature, `Methodology`, `Project convention`). Full evidence ledger, tested model scope, and statistical tables live in [evidence/evidence_ledger.md](https://github.com/floydous/agent-system-authoring/blob/main/evidence/evidence_ledger.md) and [evidence/empirical_results.md](https://github.com/floydous/agent-system-authoring/blob/main/evidence/empirical_results.md).

## Authoring Workflow
Route directly to **Step 1** (system prompts), **Step 2** (tool schemas), **Step 3** (Agent Skills), or **Audit** (read existing artifacts and check [references/debunked_folklore.md](references/debunked_folklore.md) first). Before editing multi-file or multi-provider targets, open the matching reference guide below (`system_instructions_guide.md`, `tool_schema_guide.md`, or `skill_design_guide.md`) for exact wire shapes, keyword limits, and checklists. If target **provider(s)** (`OpenAI`/`Anthropic`/`Gemini`), **`strict: true`** support, or **reasoning vs. zero-reasoning mode** are not evident from workspace files, confirm them before authoring (`R-TOOL-10`/`R-TOOL-11` wire shapes are mutually incompatible).

### Step 1: Structure System Prompts & Boundaries
1. **Minimize active rules (`R-SYS-01`, T2 + T5)**: Split multi-step workflows into focused phases rather than one overloaded rule dump; high concurrent rule counts degrade strict compliance and inflate reasoning tokens.
2. **Isolate untrusted data (`R-SYS-03`, T3)**: Enforce `Platform > Developer > User > Tool/Untrusted Data`; wrap CRM tickets, PDFs, or web text in data delimiters and deny authority to imperatives inside them.
3. **Place boundaries purposefully (`R-SYS-02`, T5)**: Put core invariants first, strict output rules near the end, and compact retrieved data in the middle (explicit boundary-vs-recall trade-off).
4. **Use clean delimiters (`R-SYS-08`, T3)**: Default to flat Markdown `###` headers (or XML tags for Claude); never use literal `[A|B|C]` brackets when a single concrete value is expected.
5. **Drop CoT & persona fluff (`R-SYS-07` T3, `R-SYS-06` T5)**: Omit `"think step by step"` on reasoning models and omit expert personas (`"Fields Medalist..."`) on accuracy tasks; specify objective criteria instead.
6. **Start zero-shot (`R-SYS-09`, T5)**: Add minimal examples only when formatting needs them, aligned with all rules. Append a brief trailing reminder for demanding standard-model reasoning (`R-SYS-04`, T5).
7. **State exclusions explicitly (`R-SYS-05`, T2)**: Write explicit `Do NOT use ...` bans (specifying whether plurals or hyphenated compounds like `consecutive-failure` are banned); never assume affirmative `"use X instead"` phrasing blocks unnamed words.
8. For concrete hardening patterns and examples, read [references/system_instructions_guide.md](references/system_instructions_guide.md); starter: [assets/templates/system_prompt_template.md](assets/templates/system_prompt_template.md).

### Step 2: Author Multi-Provider Tool & Function Schemas
1. **Name semantically in `snake_case` (`R-TOOL-01` T4, `R-TOOL-02` T5)**: Use clear `[verb]_[noun]` names (service-prefixed if multi-service), never opaque IDs.
2. **Write neutral 3–4+ sentence descriptions (`R-TOOL-03` T3, `R-TOOL-04` T2)**: State purpose, positive triggers, sister-tool negative boundaries, parameters, and caveats; omit promotional superlatives (`"best"`, `"preferred"`).
3. **Pair descriptions with provider-supported structural constraints (`R-TOOL-05` T2, `R-TOOL-10` T1)**: Put exact syntax examples, no-space separators (e.g., `"lat,lon"`), units (`cents`, `ms`), date-interval conventions (`[start, end)`), formulas, and bounds in parameter `description`s, AND add structural JSON Schema keywords where supported:
   - **OpenAI (`strict: true`)**: Encode `pattern`, `format`, `minimum`/`exclusiveMinimum`/`maximum`, and `minItems`/`maxItems`.
   - **Anthropic (`strict: true`)**: Use only simple `pattern`, `format`, and `minItems` (`0`/`1`); move `minimum`/`maximum`/`minLength`/`maxLength` to `description` + client validation (those trigger HTTP `400`).
   - **Gemini**: Use `parametersJsonSchema` for standard JSON Schema (`pattern`, `additionalProperties`, `$ref`, `anyOf`, `type: "null"`, numeric bounds), or legacy OpenAPI-subset `parameters` (`minimum`, `maximum`, `format`, `minItems`/`maxItems`).
4. **Constrain closed sets & prune catalogs (`R-TOOL-06` T1, `R-TOOL-07` T3, `R-TOOL-08` T4)**: Use `enum` for small closed sets; replace giant enums near grammar caps with a `string` + companion search/lookup tool; consolidate actions and re-anchor invariants past 50% context (`R-TOOL-12`, T5).
5. **Match exact provider wire shapes (`R-TOOL-10`, T1)** (never mix `"name"`/`"strict"` directly alongside `"$schema"`/`"properties"`):
   - **OpenAI Chat (`strict: true`)**: `{"type": "function", "function": {"name", "description", "strict": true, "parameters": {"type": "object", "properties", "required": [<all keys>], "additionalProperties": false}}}` (nullable unions for optionals).
   - **OpenAI Responses (`strict: true`)**: Flat wrapper `{"type": "function", "name", "description", "strict": true, "parameters": {...}}` (`additionalProperties: false`, all keys `required`).
   - **Anthropic (`strict: true`)**: `{"name", "description", "strict": true, "input_schema": {"type": "object", "properties", "required": [<mandatory only>], "additionalProperties": false}}` (caps: `20` strict tools / `24` optionals / `16` unions; required emit first).
   - **Gemini**: `{"name", "description", "parametersJsonSchema": {"type": "object", "properties", "required": [<mandatory only>], "additionalProperties": false}}` (preferred standard JSON Schema) or legacy OpenAPI-subset `"parameters"` (no `"strict": true`).
6. **Reserve `rationale`-first strictly for zero/non-reasoning constrained decoding (`R-TOOL-11`, T2 + T4)**:
   - **Omit `"rationale"` on standard reasoning-model tools**; start from [assets/templates/tool_schema_template.json](assets/templates/tool_schema_template.json).
   - **Add `"rationale"` FIRST** (concise supporting explanation, never `"step-by-step thinking"`) ONLY when pre-emission thinking is absent or `reasoning_effort="none"`, keeping exact domain formulas and bounds on sibling fields; start from [assets/templates/tool_schema_zero_reasoning_template.json](assets/templates/tool_schema_zero_reasoning_template.json).
   - For the full provider keyword matrix and wire-shape examples, read [references/tool_schema_guide.md](references/tool_schema_guide.md).

### Step 3: Design, Verify & Evaluate Agent Skills
1. **Follow open-spec layout (`R-SKILL-01`–`04`, T1)**: Root `SKILL.md` (`< 500` lines, `< 5000` tokens), optional lowercase `scripts/`, `references/`, `assets/` with one-hop links from `SKILL.md` (no `../` from `SKILL.md`, never escaping skill root), kebab-case `name` **matching its parent folder name**, and third-person `description` stating both what it does and when to use it. Starter: [assets/templates/skill_template.md](assets/templates/skill_template.md); operational workflow patterns (stop gates, stall breakers, CLI-drift & isolated agent A/B evals) live in [references/skill_design_guide.md](references/skill_design_guide.md).
2. **Keep runtime packages concrete & clean (`R-SKILL-05` convention, `R-SKILL-06` T1)**: Tailor workflows, checklists, and helper scripts concretely to the target domain (avoid copying repo-specific meta-harness boilerplate). Omit secrets, `.env*`, private keys, `__pycache__/`, `.pytest_cache/`, `tests/`, `mock_*`, and heavy `evidence/` traces from installable skill dirs; use PEP 723 (`# /// script` declaring `requires-python` and `dependencies = []` before `# ///`) stdlib `pathlib.Path` UTF-8 scripts, and run Python checks with `python -B` so `__pycache__/` is not recreated.
3. **Audit & verify (`R-SYS-10`, Methodology)**: Check [references/debunked_folklore.md](references/debunked_folklore.md), run `python -B <this-skill-dir>/scripts/verify_skill.py --generic <target-skill-dir>` until exit code `0` (omit `--generic` only for `agent-system-authoring` itself), and test over `N >= 5` repeats aggregated to prompt means before paired *t* / exact sign tests.

## References
- [references/system_instructions_guide.md](references/system_instructions_guide.md) — System prompt directives (`R-SYS-01`–`10`) & concrete examples.
- [references/tool_schema_guide.md](references/tool_schema_guide.md) — Exact provider wire shapes, keyword matrix & tool directives (`R-TOOL-01`–`12`).
- [references/skill_design_guide.md](references/skill_design_guide.md) — Agent Skills spec (`R-SKILL-01`–`06`), operational patterns & eval design.
- [references/debunked_folklore.md](references/debunked_folklore.md) — Audit checklist of refuted prompting & schema myths.
- [scripts/verify_skill.py](scripts/verify_skill.py) & [evals/evals.json](evals/evals.json) — Offline validator & Eval Suite v4 definitions.
