---
name: agent-system-authoring
description: Authors evidence-grounded system instructions, multi-provider tool/function JSON schemas, and portable Agent Skills. Use whenever designing, writing, auditing, refactoring, or packaging system prompts, function tool definitions (including strict mode across OpenAI/Anthropic/Gemini, rationale ordering, anti-gaming descriptions, and catalog consolidation), or Agent Skills under open specifications.
license: MIT
metadata:
  author: "floydous"
  version: "1.1.0"
---

# Agent System Authoring: Evidence-Grounded Prompt, Schema & Skill Engineering

## Overview
This skill guides agents and engineers in authoring system instructions, tool/function schemas, and portable Agent Skills. Every item is tagged by its verification basis (`T1` Verified Fact, `T2` Measured on `GPT 6 Luna` only, `T3` Current Vendor Guidance — *not measured by us*, `T4` Mechanism, `T5` Learned Behavior, `Methodology`, `Project convention`, or `Contested`). **Scope boundary**: all **T2** empirical suites tested `GPT 6 Luna` alone; **T5** rules were measured on earlier models (`Gemini 4 Hydrogen`, `Claude Fable 5.2`, `Claude Opus 5.5`, and `GPT 6.2 Astra` remain unmeasured here). See [references/unverified_hypotheses.md](references/unverified_hypotheses.md) for open/contested items.

---

## Authoring Workflow

### Step 1: Scope Instructions, Hierarchy & Context Placement
1. Minimize simultaneous active instructions and segment multi-step workflows into phase-specific prompts rather than overloading a single monolithic block ([R-SYS-01](references/system_instructions_guide.md), **T5**).
2. Establish the chain-of-command authority hierarchy (`Platform > Developer > User > Tool/Untrusted Data`), placing invariants in System/Developer roles and marking retrieved text or tool outputs as untrusted data with zero instruction authority ([R-SYS-03](references/system_instructions_guide.md), **T3**).
3. Position immutable system invariants at the start of context, critical output format constraints near the end, and compact retrieved documents in the middle—recognizing the **untested trade-off** between protecting start/end boundary rules and weaker mid-context document recall ([R-SYS-02](references/system_instructions_guide.md), **T5**).

### Step 2: Author System Instructions
1. Use clean structural delimiters (flat Markdown `###` headers by default, or XML tags for Claude prompts per vendor guidance; `PB-1` found no significant XML accuracy penalty once wording is equalized; [R-SYS-08](references/system_instructions_guide.md), **T3**). Avoid literal meta-syntax placeholders like `[A|B|C]` when a single choice is expected.
2. Omit explicit `"think step by step"` or `"explain your reasoning"` directives on native reasoning models; provide clear goals and constraints instead ([R-SYS-07](references/system_instructions_guide.md), **T3**).
3. Omit honorary expert personas (`"You are a Fields Medalist / world-class..."`) when targeting factual, math, or coding accuracy; specify objective acceptance criteria instead (**T5** literature; `PB-5` showed no gain but was underpowered at `n = 6` prompts; [R-SYS-06](references/system_instructions_guide.md)).
4. Try zero-shot prompting first on reasoning models; if few-shot demonstrations are needed, keep them minimal and verify zero conflicts with written rules ([R-SYS-09](references/system_instructions_guide.md), **T5**).
5. Append a concise trailing reminder near the output boundary for demanding reasoning on standard models or long sessions ([R-SYS-04](references/system_instructions_guide.md), **T5**; high-effort `GPT 6 Luna` hit `30/30` ceiling in `PB-3`).
6. State explicit negative exclusions (`"Do NOT use ..."`) whenever specific words/tokens must be omitted rather than relying on affirmative-only wording alone (`PC-2`, `16` prompts × `5` repeats: `98.8%` bare negative vs `65.0%` affirmative-only, paired `t(15) = 4.06, p = 0.0010`); optional positive substitutes (`paired_affirmative`: `95.0%`, `p = 0.3332` vs bare negative) are stylistic rather than required ([R-SYS-05](references/system_instructions_guide.md), **T2**).
7. Reference template: inspect [assets/templates/system_prompt_template.md](assets/templates/system_prompt_template.md).

### Step 3: Author Tool & Function Schemas
1. Use descriptive semantic tool names instead of opaque identifiers ([R-TOOL-02](references/tool_schema_guide.md), **T5**), following `[verb]_[noun]` **Project convention** and `snake_case` naming grounded in subword tokenization sensitivity ([R-TOOL-01](references/tool_schema_guide.md), **T4**).
2. Write detailed plain-prose descriptions — aim for **at least 3–4 sentences** (more if complex) — covering what the tool does, when to use it and when **not** to use it (mutual negative boundaries naming sister tools, incl. merged `R-TOOL-09`), parameter semantics, and caveats ([R-TOOL-03](references/tool_schema_guide.md), **T3**).
3. Keep tool descriptions neutral and factual; omit promotional superlatives (`"best"`, `"preferred"`, `"invoke whenever possible"`), which overrode neutral parallel/first-position defaults between functionally identical tools across `16/16` counterbalanced prompts in `PC-1` (sign `p = 3.052e-05`; [R-TOOL-04](references/tool_schema_guide.md), **T2**).
4. Provide explicit parameter `description`s specifying exact formats, spacing rules, units, and constraints—essential for non-universal conventions where unstated syntax failed (`TS-2`: `0/15` -> `15/15` on unstated no-space `"lat,lon"`, sign `p = 6.104e-05`; [R-TOOL-05](references/tool_schema_guide.md), **T2**).
5. Use JSON Schema `enum` arrays for closed discrete parameter sets ([R-TOOL-06](references/tool_schema_guide.md), **T1**). For high-cardinality catalogs near provider grammar limits, replace huge inline `enum`s with an open `string` parameter plus a search/lookup tool ([R-TOOL-07](references/tool_schema_guide.md), **T3**).
6. Keep active in-context tool sets compact via dynamic retrieval or consolidated multi-action tools ([R-TOOL-08](references/tool_schema_guide.md), **T4**). In long sessions exceeding 50% context utilization, re-anchor critical tool invariants near the active turn ([R-TOOL-12](references/tool_schema_guide.md), **T5**).
7. Apply provider-scoped strict schema conformance ([R-TOOL-10](references/tool_schema_guide.md), **T1**):
   - **OpenAI (`"strict": true`)**: set `"additionalProperties": false`, include **all** keys in `"required"`, and use nullable unions (`["string", "null"]`) for optionals.
   - **Anthropic (`"strict": true`)**: set `"additionalProperties": false` (max `20` strict tools, `24` optional params, `16` unions/request); optionals may stay outside `"required"`, though required fields emit first.
   - **Gemini**: omit `"strict": true` (OpenAPI subset `parameters`); keep optionals outside `"required"` unless simplifying grammar branching.
8. When targeting **non-reasoning models** (proxied in `PB-6` via `reasoning_effort="none"`, `reasoning_tokens = 0`) under constrained JSON decoding on multi-step computations, place a concise `"rationale"` / explanation field first in `properties` (`PB-6`, `n = 6` prompts: `100.0%` vs `36.7%`, paired `t(5) = 3.12, p = 0.0261`; neutral at `xhigh` in `TS-3`; avoid requesting `"step-by-step thinking"` to prevent Anthropic `reasoning_extraction` refusals) ([R-TOOL-11](references/tool_schema_guide.md), **T2** + **T4**).
9. Reference starter (OpenAI strict format): [assets/templates/tool_schema_template.json](assets/templates/tool_schema_template.json).

### Step 4: Design and Package Portable Agent Skills
1. Package as a standalone directory with `SKILL.md` at root and optional lowercase `scripts/`, `references/`, and `assets/` subdirectories (`evals/` and repo-root `evidence/` are **Project conventions**) ([R-SKILL-01](references/skill_design_guide.md), **T1**).
2. Configure YAML frontmatter: `name` (`1–64` chars, `[a-z0-9-]`, matching parent folder) and `description` (`1–1024` chars stating what + when; Anthropic **T3** advises third person) ([R-SKILL-03](references/skill_design_guide.md), **T1**).
3. Keep `SKILL.md` under `500` lines and `< 5000` recommended tokens ([R-SKILL-02](references/skill_design_guide.md), **T1**), keeping file links one level deep from `SKILL.md` without chained hops or `../` escapes ([R-SKILL-04](references/skill_design_guide.md), **T1**).
4. Enforce packaging hygiene: omit private credentials, `__pycache__/`, `.pytest_cache/`, internal `tests/`, and synthetic/mock dumps; keep heavy reproducibility archives outside the installable skill directory when publishing (`R-SKILL-05`, **Project convention**).
5. Declare Python script dependencies inline using PEP 723 metadata (`# /// script ... # ///`) and write cross-platform UTF-8 `pathlib.Path` code ([R-SKILL-06](references/skill_design_guide.md), **T1**).
6. Reference template: inspect [assets/templates/skill_template.md](assets/templates/skill_template.md).

### Step 5: Audit, Verify & Evaluate
1. Review drafts against [references/debunked_folklore.md](references/debunked_folklore.md) and [references/unverified_hypotheses.md](references/unverified_hypotheses.md).
2. Run offline structural, link, ledger, version-sync, and hygiene verification from the skill directory:
   ```bash
   python scripts/verify_skill.py .
   ```
3. Evaluate prompt/skill changes across `N >= 5` repeats per prompt, aggregating repeats to prompt-level means before paired *t* or exact sign tests (`TARa@N`, [R-SYS-10](references/system_instructions_guide.md), **Methodology**). In Eval Suite v2 on `GPT 6 Luna` (`330` trace records, [evals/evals.json](evals/evals.json)), hard 12-skill triggering without negative hints scored F1 `1.0000` (`60/60` TP, `0/60` FP), downstream probes scored `0.933` vs `0.900` (`5/5` vs `3/5` on zero-reasoning arithmetic), and blinded pairwise judging favored `with_skill` on `7/10` tasks (`28/50` wins; `0.845` vs `0.835`, `t(9) = 0.38, p = 0.7134`).

---

## References & Files

| File | Purpose |
| :--- | :--- |
| [references/system_instructions_guide.md](references/system_instructions_guide.md) | System instruction rules (`R-SYS-01`–`R-SYS-10`) with tiers, citations, and model boundaries. |
| [references/tool_schema_guide.md](references/tool_schema_guide.md) | Tool schema rules (`R-TOOL-01`–`R-TOOL-12`, provider-scoped `R-TOOL-10`). |
| [references/skill_design_guide.md](references/skill_design_guide.md) | Agent Skill packaging specification and conventions (`R-SKILL-01`–`R-SKILL-06`). |
| [references/evidence_ledger.md](references/evidence_ledger.md) | Master ledger indexing all 28 rule IDs to tiers, models tested, and verified sources. |
| [references/debunked_folklore.md](references/debunked_folklore.md) | Verified refutations and bounded comparisons across Phase A, Phase B, and Phase C. |
| [references/unverified_hypotheses.md](references/unverified_hypotheses.md) | Unsupported numbers removed from rules, inconclusive contrasts, and open hypotheses. |
| [references/empirical_results.md](references/empirical_results.md) | Prompt-level Phase A (228), Phase B (480), and Phase C (480) results on `GPT 6 Luna`. |
| [assets/templates/system_prompt_template.md](assets/templates/system_prompt_template.md) | Flat Markdown-header system prompt starter template. |
| [assets/templates/tool_schema_template.json](assets/templates/tool_schema_template.json) | OpenAI `strict: true` tool schema template (`rationale` scoped to non-reasoning decoding). |
| [assets/templates/skill_template.md](assets/templates/skill_template.md) | Starter `SKILL.md` template conforming to the Agent Skills specification. |
| [scripts/verify_skill.py](scripts/verify_skill.py) | Standalone offline validator for layout, frontmatter, links, version sync, and hygiene. |
| [evals/evals.json](evals/evals.json) | Eval Suite v2 specification (24 hard trigger cases + 10 non-leading comparative tasks). |

Reproducibility traces (`evidence/`), source verification logs (`source_checks.md`), and offline recomputation (`recompute_stats.py`) are published in the repository root [`evidence/` archive](https://github.com/floydous/agent-system-authoring/tree/main/evidence).
