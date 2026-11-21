# agent-system-authoring

An [Agent Skills specification](https://agentskills.io/specification)-compliant skill for designing, writing, auditing, and packaging LLM system instructions, tool/function JSON schemas, and portable Agent Skills. Every rule is tagged by its verification basis (`T1`–`T5`, `Methodology`, or `Project convention`) and backed by primary source checks and reproducible execution traces on `GPT 6 Luna`.

## What This Skill Teaches

1. **System Instructions & Prompt Architecture** ([references/system_instructions_guide.md](references/system_instructions_guide.md))
   - Enforces authority separation (`Platform > Developer > User > Tool/Untrusted Data`), positional placement (invariants at start, bulky retrieved data in the middle, format rules near the end), phase segmentation, and trailing reminders.
   - Uses clean structural delimiters (flat Markdown headers or XML tags per vendor guidance), states explicit prohibitions whenever specific tokens/words must be excluded, and omits honorary expert personas and redundant reasoning-model `"think step by step"` directives.
2. **Tool & Function JSON Schemas** ([references/tool_schema_guide.md](references/tool_schema_guide.md))
   - Enforces OpenAI `strict: true` schemas (`additionalProperties: false`, every property in `required`, nullable optional unions), descriptive `snake_case` naming, neutral detailed descriptions (aiming for at least `3–4` sentences covering purpose, positive triggers, negative boundaries naming sister tools, parameter semantics, and caveats), explicit format conventions for non-universal parameters, and `rationale`-first ordering when targeting non-reasoning or zero-reasoning constrained decoding.
3. **Portable Agent Skills** ([references/skill_design_guide.md](references/skill_design_guide.md))
   - Structures skills around root [SKILL.md](SKILL.md) (`< 500` lines / `< 5000` recommended tokens), `what + when` YAML frontmatter, one-level-deep links into `references/`, PEP 723 inline Python script metadata, starter templates in [assets/templates/](assets/templates/skill_template.md), and clean packaging hygiene.
4. **Epistemic Rigor & Folklore Audits** ([references/debunked_folklore.md](references/debunked_folklore.md), [references/unverified_hypotheses.md](references/unverified_hypotheses.md))
   - Separates verified facts from refuted folklore and unmeasured claims, requiring multi-iteration evaluation (`N >= 5`, `TARa@N`, paired/exact tests).

## Evidence Tier Policy

Every rule in [references/evidence_ledger.md](references/evidence_ledger.md) carries exactly one primary tier:

| Tier | Meaning |
| :--- | :--- |
| **T1** | Verified specification or API schema mechanic checked directly against retrieved docs ([evidence/source_checks.md](evidence/source_checks.md)). |
| **T2** | Statistically significant behavior recomputed offline from bundled execution traces on `GPT 6 Luna` ([evidence/stats_recomputed.md](evidence/stats_recomputed.md)). |
| **T3** | Current official vendor guidance (Anthropic / OpenAI / Google) retrieved verbatim (*not measured by us*). |
| **T4** | Peer-reviewed finding rooted in invariant architectural mechanics (BPE tokenization, left-to-right constrained decoding, context-token cost, FP16/BF16 non-determinism). |
| **T5** | Peer-reviewed learned-behavior finding measured on earlier model families (*transfer to current models plausible, not re-measured*). |
| **Methodology / Project convention** | Statistical evaluation principles (`R-SYS-10`) or engineering conventions (`R-SKILL-05`). |

## Empirical Summary (`GPT 6 Luna`)

Across `708` benchmark completions (`228` Phase A runs at `N = 1`, `480` Phase B runs at `N = 5`, `0` errors in Phase B) and `80` `evals/evals.json` executions (`0` errors):

| Suite / Benchmark | Conditions & Sample (`GPT 6 Luna`) | Verified Result (`evidence/stats_recomputed.md` & `evidence/evals_results.md`) |
| :--- | :--- | :--- |
| **`PB-2` (Tool Gaming)** | Symmetric tools (`alpha` vs `beta`), `N = 30`/arm, `xhigh` | Assertive claims flipped selection from `0/30` (`0.0%`) to **`30/30` (`100.0%`, Fisher `p = 1.691e-17`)**; neutral usage examples alone caused `0/30` shift (`p = 1.0000`). Supports `R-TOOL-04` (**T2**). |
| **`PB-6` (`rationale` Ordering)** | `reasoning_effort = "none"` (`reasoning_tokens = 0`), `N = 30`/arm | `rationale_first` reached **`30/30` (`100.0%`)** vs **`11/30` (`36.7%`)** for both `no_rationale` and `rationale_last` (paired `t = 3.12, p = 0.0261`; Fisher `p = 5.343e-08`). Neutral (`15/15`) at `xhigh` (`TS-3`). Supports `R-TOOL-11` (**T2**). |
| **`PB-4` (Negation vs Affirmative-Only)** | 4 excluded terms, `N = 30`/arm, `xhigh` | Explicit exclusions (`bare_negative` `27/30` = `90.0%`, `paired_affirmative` `30/30` = `100.0%`) beat `affirmative_only` (`14/30` = `46.7%`; Fisher `p = 0.0006` and `p = 1.944e-06`). Supports `R-SYS-05` (**T2**). |
| **`TS-2` (Parameter Descriptions)** | With vs without descriptions (`N = 15`/arm, `xhigh`) | Universal ISO timestamps (`15/15`) and ISO currencies (`12/15`, `p = 0.2241`) were mostly inferred, whereas unstated no-space `"lat,lon"` geo syntax failed **`0/15` vs `15/15` (`p = 1.289e-08`)**. Supports `R-TOOL-05` (**T2**). |
| **`PB-1` (Delimiters)** | Identical wording across `flat_markdown` / `flat_xml` / `nested_xml`, `N = 30`/arm | `0.972` vs `0.983` (`p = 0.3632`) vs `0.994` (`p = 0.1019`) — resolved an earlier Phase A `SP-4` bracket-syntax prompt bug. Supports `R-SYS-08` (**T3**). |
| **`PB-5` (Expert Persona)** | Combinatorics puzzles at `reasoning_effort = "low"`, `N = 30`/arm | `neutral_objective` (`29/30` = `96.7%`, `TARa@5 = 83%`) vs `expert_persona` (`27/30` = `90.0%`, `TARa@5 = 50%`, `p = 0.6120`). Zero benefit (`R-SYS-06`, **T5**). |
| **Triggering Eval (`evals.json`)** | `50` calls across 6-skill registry (`N = 5`/prompt, `low`) | **Precision `1.0000` (`25/25` TP, `0/25` FP), Recall `1.0000`, F1 `1.0000`**, `TARa@5 = 100%` across all 10 trigger cases. |
| **Comparative Eval (`evals.json`)** | `baseline` vs `with_skill`, `N = 15` pairs (`3` tasks × `5` runs, `medium`) | Overall rubric score improved from **`0.533` to `0.851` (`+0.318`, paired `t = 7.52, p = 2.804e-06`)**. |

> **Scope Boundary**: Live experiments and evaluations tested `GPT 6 Luna` only. Direct cross-model testing on `Gemini 4 Hydrogen`, `Claude Fable 5.2`, `Claude Opus 5.5`, and `GPT 6.2 Astra` has not yet been executed in this repository.

## Installation & Offline Verification

Place or clone this directory into your agent's skills root (e.g., `~/.pi/agent/skills/agent-system-authoring` or your harness skills directory):

```bash
git clone git@github.com:floydous/agent-system-authoring.git
cd agent-system-authoring
```

Run the standalone, offline Python verification and statistical recomputation checks (standard library only):

```bash
python scripts/verify_skill.py .
python evidence/recompute_stats.py
```

Both commands exit `0` when all directory layout, YAML frontmatter, single-hop link, ledger tier, template, PEP 723, and statistical trace checks succeed.

## Repository Layout

```text
agent-system-authoring/
├── SKILL.md                         # Skill entrypoint loaded upon activation (< 100 lines)
├── README.md                        # Repository overview, verified empirical summary & setup
├── LICENSE                          # MIT License
├── assets/templates/                # Starter system prompt (.md), skill (.md), and tool schema (.json)
├── evals/evals.json                 # Dual-axis triggering and comparative authoring test suite
├── evidence/
│   ├── README.md                    # Provenance index and Phase A/B/eval methodological notes
│   ├── recompute_stats.py           # Offline statistical recomputation script (Phase A & Phase B)
│   ├── stats_recomputed.md          # Recomputed tables, paired t-tests, Fisher exact p & TARa@5
│   ├── evals_results.md             # Executed evals.json trigger & comparative evaluation report
│   ├── source_checks.md             # Primary-source quotes and retrieval verification log
│   ├── experiment_harness.py        # Phase A provenance harness
│   ├── phase_b_harness.py           # Phase B provenance harness
│   ├── run_evals.py                 # evals.json execution and deterministic rubric scorer
│   ├── raw/                         # Phase A JSONL completion logs (228 records)
│   ├── raw_phase_b/                 # Phase B JSONL completion logs (480 records)
│   └── raw_evals/                   # Executed evals JSONL logs (80 records)
├── references/                      # Domain authoring guides, evidence ledger & folklore catalog
└── scripts/verify_skill.py          # Offline package conformance & hygiene linter
```

## License

Released under the [MIT License](LICENSE).
