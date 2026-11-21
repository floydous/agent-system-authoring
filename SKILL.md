---
name: agent-system-authoring
description: Authors evidence-grounded system instructions, tool/function JSON schemas, and portable Agent Skills. Use whenever designing, writing, auditing, or packaging system prompts, tool definitions, or Agent Skills under open specifications (including progressive disclosure, trigger descriptions, flat structural delimiters, strict schemas, and packaging hygiene), or when auditing prompt adherence and tool-selection designs.
license: MIT
metadata:
  author: "floydous"
  version: "1.0.0"
---

# Agent System Authoring: Evidence-Grounded Prompt, Schema & Skill Engineering

## Overview
This skill guides agents and engineers in authoring system instructions, tool/function schemas, and portable Agent Skills. Every item below is explicitly tagged by its verification basis (`T1` Verified Fact, `T2` Measured on `cx/gpt-6-luna`, `T3` Current Vendor Guidance — *not measured by us*, `T4` Mechanism, `T5` Learned Behavior, `Methodology`, `Project convention`, or `Contested`). T5 rules were measured on earlier models; transfer to current models (`Gemini 4 Hydrogen`, `Claude Fable 5.2`, `Claude Opus 5.5`, `GPT 6.2 Astra`) is plausible but not re-measured. Contested and unsupported items: see [references/unverified_hypotheses.md](references/unverified_hypotheses.md).

---

## Authoring Workflow

### Step 1: Scope Instructions, Hierarchy & Context Placement
1. Minimize simultaneous active instructions and segment multi-step workflows into phase-specific prompts rather than overloading a single monolithic block ([R-SYS-01](references/system_instructions_guide.md), **T5**).
2. Establish the chain-of-command authority hierarchy (`Platform > Developer > User > Tool/Untrusted Data`) and isolate retrieved context or tool outputs as untrusted data ([R-SYS-03](references/system_instructions_guide.md), **T3**).
3. Position immutable system invariants at the start of context, bulky retrieved data in the middle, and critical output format constraints near the end ([R-SYS-02](references/system_instructions_guide.md), **T5**).

### Step 2: Author System Instructions
1. Use clean structural delimiters (flat Markdown headers `###` by default, or XML tags for Claude prompts per vendor guidance; Phase B `PB-1` found no significant XML accuracy penalty once wording is equalized; [R-SYS-08](references/system_instructions_guide.md), **T3**). Avoid literal meta-syntax placeholders like `[A|B|C]` when a single choice is expected.
2. Omit explicit `"think step by step"` or `"explain your reasoning"` directives on native reasoning models; provide clear goals and constraints instead ([R-SYS-07](references/system_instructions_guide.md), **T3**).
3. Omit honorary expert personas (`"You are a Fields Medalist / world-class..."`) when targeting factual, math, or coding accuracy; specify objective acceptance criteria instead ([R-SYS-06](references/system_instructions_guide.md), **T5**).
4. Try zero-shot prompting first on reasoning models; if few-shot demonstrations are needed, keep them minimal and verify zero conflicts with written rules ([R-SYS-09](references/system_instructions_guide.md), **T5**).
5. Append a concise trailing reminder near the output boundary for demanding reasoning on standard models or long sessions ([R-SYS-04](references/system_instructions_guide.md), **T5**).
6. State explicit negative exclusions (`"Do NOT use ..."`) whenever specific tokens or words must be omitted—never replace a hard exclusion with affirmative-only wording alone (`PB-4`: `46.7%` vs `90%–100%`), optionally pairing with positive substitutes ([R-SYS-05](references/system_instructions_guide.md), **T2**).
7. Reference template: inspect [assets/templates/system_prompt_template.md](assets/templates/system_prompt_template.md).

### Step 3: Author Tool & Function Schemas
1. Use descriptive semantic tool names instead of opaque identifiers ([R-TOOL-02](references/tool_schema_guide.md), **T5**), following `[verb]_[noun]` **Project convention** and `snake_case` naming across tools and parameters grounded in subword tokenization sensitivity ([R-TOOL-01](references/tool_schema_guide.md), **T4**).
2. Write detailed plain-prose descriptions — aim for **at least 3–4 sentences** (more if complex) — covering what the tool does, when to use it and when **not** to use it (including mutual negative boundaries naming sister tools, incorporating merged `R-TOOL-09`), parameter semantics, and caveats ([R-TOOL-03](references/tool_schema_guide.md), **T3**).
3. Keep tool descriptions neutral and factual; omit promotional superlatives (`"best"`, `"preferred"`, `"invoke whenever possible"`), which drove `100%` selection hijacking in `PB-2` ([R-TOOL-04](references/tool_schema_guide.md), **T2**).
4. Always provide explicit parameter `description`s specifying exact formats, spacing rules, units, and constraints for any non-universal convention ([R-TOOL-05](references/tool_schema_guide.md), **T2**).
5. Use JSON Schema `enum` arrays to constrain closed discrete parameter sets ([R-TOOL-06](references/tool_schema_guide.md), **T1**). For high-cardinality catalogs approaching provider schema limits, avoid oversized `enum`s and pair an open `string` parameter with a search/lookup tool ([R-TOOL-07](references/tool_schema_guide.md), **T3**).
6. Keep active in-context tool sets compact via dynamic retrieval or consolidated multi-action tools ([R-TOOL-08](references/tool_schema_guide.md), **T4**). In long sessions exceeding 50% context utilization, re-anchor critical tool constraints near the active turn ([R-TOOL-12](references/tool_schema_guide.md), **T5**).
7. Enable strict schema conformance (`"strict": true`, `"additionalProperties": false`, all property keys in `"required"`, nullable union types for optional fields) ([R-TOOL-10](references/tool_schema_guide.md), **T1**).
8. When targeting **non-reasoning models** or `reasoning_effort="none"` under constrained JSON decoding, place a concise `"rationale"` / explanation parameter first in `properties` (`PB-6`: `100%` vs `36.7%`; optional on high-effort native reasoning models; avoid asking for `"step-by-step thinking"`) ([R-TOOL-11](references/tool_schema_guide.md), **T2**).
9. Reference template: inspect [assets/templates/tool_schema_template.json](assets/templates/tool_schema_template.json).

### Step 4: Design and Package Portable Agent Skills
1. Package as a standalone directory with `SKILL.md` at root and optional lowercase `scripts/`, `references/`, and `assets/` subdirectories (`evals/` and `evidence/` are **Project conventions**) ([R-SKILL-01](references/skill_design_guide.md), **T1**).
2. Configure YAML frontmatter: `name` (`1–64` chars, `[a-z0-9-]`, matching parent directory name) and `description` (`1–1024` chars stating what the skill does and when to use it; Anthropic T3 advises third person) ([R-SKILL-03](references/skill_design_guide.md), **T1**).
3. Keep `SKILL.md` under `500` lines and `< 5000` recommended tokens ([R-SKILL-02](references/skill_design_guide.md), **T1**), keeping file links one level deep from `SKILL.md` without nested reference chains or `../` traversal ([R-SKILL-04](references/skill_design_guide.md), **T1**).
4. Enforce packaging hygiene: omit private credentials, `__pycache__/`, `.pytest_cache/`, internal `tests/` runners, and synthetic/mock dumps; keep reproducibility traces only under `evidence/` ([R-SKILL-05](references/skill_design_guide.md), **Project convention**).
5. Declare Python script dependencies inline using PEP 723 metadata (`# /// script ... # ///`) and write cross-platform UTF-8 `pathlib.Path` code ([R-SKILL-06](references/skill_design_guide.md), **T1**).
6. Reference template: inspect [assets/templates/skill_template.md](assets/templates/skill_template.md).

### Step 5: Audit, Verify & Evaluate
1. Review drafts against [references/debunked_folklore.md](references/debunked_folklore.md) and [references/unverified_hypotheses.md](references/unverified_hypotheses.md).
2. Run offline structural verification and verify trace statistics:
   ```bash
   python scripts/verify_skill.py .
   python evidence/recompute_stats.py
   ```
3. Run evaluations (`evals/evals.json`) across `N >= 5` iterations per prompt, reporting dispersion and exact/paired tests to account for GPU/batching non-determinism ([R-SYS-10](references/system_instructions_guide.md), **Methodology**). On `cx/gpt-6-luna` (`80` calls, `N = 5`), triggering scored Precision `1.0` / Recall `1.0` / F1 `1.0` and comparative rubric quality improved from `0.533` to `0.851` (`+0.318`, `p = 2.804e-06`; see [evidence/evals_results.md](evidence/evals_results.md)).

---

## References & Files

| File | Purpose |
| :--- | :--- |
| [references/system_instructions_guide.md](references/system_instructions_guide.md) | System instruction rules (`R-SYS-01`–`R-SYS-10`) with tiers, citations, and model boundaries. |
| [references/tool_schema_guide.md](references/tool_schema_guide.md) | Tool schema rules (`R-TOOL-01`–`R-TOOL-12`, `R-TOOL-09` merged into `R-TOOL-03`). |
| [references/skill_design_guide.md](references/skill_design_guide.md) | Agent Skill packaging specification and conventions (`R-SKILL-01`–`R-SKILL-06`). |
| [references/evidence_ledger.md](references/evidence_ledger.md) | Master ledger indexing all 28 rule IDs to tiers, models tested, and verified quotes. |
| [references/debunked_folklore.md](references/debunked_folklore.md) | Verified refutations and conditionally bounded comparisons across Phase A & Phase B. |
| [references/unverified_hypotheses.md](references/unverified_hypotheses.md) | Unsupported numbers removed from rules, inconclusive contrasts, and open hypotheses. |
| [references/empirical_results.md](references/empirical_results.md) | Recomputed Phase A (228 runs) and Phase B (480 runs, N=5/prompt) analysis on `cx/gpt-6-luna`. |
| [evidence/README.md](evidence/README.md) | Provenance index, raw JSONL traces, `recompute_stats.py`, and source verification log. |
| [assets/templates/system_prompt_template.md](assets/templates/system_prompt_template.md) | Flat Markdown-header system prompt starter template. |
| [assets/templates/tool_schema_template.json](assets/templates/tool_schema_template.json) | Strict JSON tool schema template (`strict: true`, rationale scoped to non-reasoning models). |
| [assets/templates/skill_template.md](assets/templates/skill_template.md) | Starter `SKILL.md` template conforming to the Agent Skills specification. |
| [scripts/verify_skill.py](scripts/verify_skill.py) | Offline validator checking structure, frontmatter, links, templates, evals, and hygiene. |
| [evals/evals.json](evals/evals.json) | Triggering and comparative evaluation test specification (executed on `cx/gpt-6-luna` in [evidence/evals_results.md](evidence/evals_results.md)). |
