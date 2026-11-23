# agent-system-authoring

[![Verify Skill & Recompute Evidence](https://github.com/floydous/agent-system-authoring/actions/workflows/verify.yml/badge.svg)](https://github.com/floydous/agent-system-authoring/actions/workflows/verify.yml)

An [Agent Skills specification](https://agentskills.io/specification)-compliant skill (`v1.2.0`) for designing, writing, auditing, and packaging LLM system instructions, multi-provider tool/function JSON schemas, and portable Agent Skills. Every rule is tagged by its verification basis (`T1`–`T5`, `Methodology`, or `Project convention`) and backed by primary source checks and reproducible execution traces on `GPT 6 Luna`.

The installable skill lives under [skills/agent-system-authoring/](skills/agent-system-authoring/SKILL.md) (`50` lines, `~1,566` estimated body tokens, `~159 KB` total package) so `npx skills add` installs stay lightweight and runtime-focused, while raw empirical JSONL logs, offline verification scripts, and provenance harnesses remain in the root [evidence/](evidence/README.md) archive.

## What This Skill Teaches

1. **System Instructions & Prompt Architecture** ([references/system_instructions_guide.md](skills/agent-system-authoring/references/system_instructions_guide.md))
   - Enforces chain-of-command hierarchy (`Platform > Developer > User > Tool/Untrusted Data`), phase segmentation, and context placement (invariants at start, format rules near the end, compact retrieved data in the middle as an explicit boundary-vs-recall trade-off).
   - Uses clean delimiters (flat Markdown headers or XML tags per vendor guidance), states explicit `Do NOT` prohibitions (specifying compound/inflected scope) when excluding words, and omits honorary expert personas and redundant reasoning-model `"think step by step"` directives.
2. **Multi-Provider Tool & Function JSON Schemas** ([references/tool_schema_guide.md](skills/agent-system-authoring/references/tool_schema_guide.md))
   - Enforces exact wire shapes across **OpenAI Chat Completions** (`type: function`, `function`, `strict: true`, all keys `required`, nullable optionals), **OpenAI Responses API**, **Anthropic** (`strict: true`, `input_schema`, optional fields allowed outside `required`), and **Google Gemini** (`parameters`, no `strict: true`).
   - Enforces descriptive `snake_case` naming, neutral detailed descriptions (`3–4+` sentences with sister-tool negative boundaries), explicit parameter conventions/formulas/units, and `rationale`-first ordering strictly when targeting zero/non-reasoning constrained decoding.
3. **Portable Agent Skills** ([references/skill_design_guide.md](skills/agent-system-authoring/references/skill_design_guide.md))
   - Structures skills around [SKILL.md](skills/agent-system-authoring/SKILL.md) (`< 500` lines / `< 5000` recommended tokens), `what + when` YAML frontmatter, one-hop `references/` links, PEP 723 inline script metadata, clean templates in [assets/templates/](skills/agent-system-authoring/assets/templates/skill_template.md), and packaging hygiene.
4. **Epistemic Rigor & Unit-of-Analysis Hygiene** ([references/debunked_folklore.md](skills/agent-system-authoring/references/debunked_folklore.md), [references/unverified_hypotheses.md](skills/agent-system-authoring/references/unverified_hypotheses.md))
   - Separates verified facts from refuted folklore and open hypotheses, aggregating repeated iterations (`N >= 5`) into prompt-level means (`df = P - 1`, paired *t* and exact sign tests; zero pseudoreplication).

## Evidence Tier Policy

Every rule in [references/evidence_ledger.md](skills/agent-system-authoring/references/evidence_ledger.md) carries one primary verification tier:

| Tier | Meaning |
| :--- | :--- |
| **T1** | Verified specification or multi-provider API schema mechanic checked directly against official docs ([evidence/source_checks.md](evidence/source_checks.md)). |
| **T2** | Statistically significant prompt-level effect recomputed offline from bundled traces on `GPT 6 Luna` ([evidence/stats_recomputed.md](evidence/stats_recomputed.md)). |
| **T3** | Current official vendor guidance (Anthropic / OpenAI / Google) retrieved verbatim (*not measured by us*). |
| **T4** | Peer-reviewed finding rooted in invariant architectural mechanics (BPE tokenization, left-to-right constrained decoding, context-token cost, FP16/BF16 non-determinism). |
| **T5** | Peer-reviewed learned-behavior finding measured on earlier model families (*transfer to current models plausible, not re-measured*). |
| **Methodology / Project convention** | Statistical evaluation principles (`R-SYS-10`) or engineering conventions (`R-SKILL-05`). |

## Empirical & Evaluation Summary (`GPT 6 Luna`)

Across `1,188` benchmark completions (`228` Phase A at `N = 1`, `480` Phase B at `N = 5` × `6` prompts, `480` Phase C at `N = 5` × `16` prompts, `0` errors in Phases B & C) and `440` Eval Suite v3 trace records (`0` errors), using strictly **prompt/task-level inference**:

| Suite / Benchmark | Design & Sample (`GPT 6 Luna`) | Prompt-Level Result ([stats_recomputed.md](evidence/stats_recomputed.md) & [evals_results.md](evidence/evals_results.md)) |
| :--- | :--- | :--- |
| **`PC-1` (Counterbalanced Tool Gaming)** | `n = 16` prompts (`50/50` east/west order) × `5` repeats, `high` | Under neutral/example descriptions, `GPT 6 Luna` hedged via parallel dual calls (`67/80`, `75/80`, plausible under `east`/`west` names) or position 0 (`13/80`, `5/80`), picking `second_tool` exclusively `0/80`. Assertive claims flipped exclusive selection of `second_tool` on **`16/16` prompts (`80/80`, sign `p = 3.052e-05`)**. Supports `R-TOOL-04` (**T2**). |
| **`PC-2` (Explicit Bans vs Affirmative Suggestions)** | `n = 16` prompts across 4 domains × `5` repeats, `high` | **`bare_negative` (`0.988`, `79/80`)** and **`paired_affirmative` (`0.950`, `76/80`)** decisively beat unstated-blacklist `affirmative_only` (`0.650`, `52/80`, `"such as..."`): **`t(15) = 4.06, p = 0.0010`** and **`t(15) = 3.87, p = 0.0015`** (sign `p = 0.0010`). Substitutes added no lift over bare prohibitions (`p = 0.3332`); all 5 negative-arm misses were hyphenated compounds (`consecutive-failure`). Supports `R-SYS-05` (**T2**). |
| **`PB-6` (`rationale` Ordering)** | `reasoning_effort = "none"` (`0` rtok), `n = 6` prompts × `5` | `rationale_first` reached **`1.000` (`30/30`)** vs **`0.367` (`11/30`)** for both `no_rationale` and `rationale_last` (parametric **`t(5) = 3.12, p = 0.0261`**; sign `4+/0-, p = 0.1250`). Neutral (`15/15`) at `xhigh` (`TS-3`). Supports `R-TOOL-11` (**T2**). |
| **`TS-2` (Parameter Descriptions)** | With vs without descriptions, `n = 15` matched prompts (`N = 1`, `xhigh`) | Universal ISO timestamps (`15/15`), currencies (`12/15`, sign `p = 0.2500`), and decimal coords (`15/15`) were inferred, while omitting descriptions failed **`0/15` vs `15/15`** purely on unstated no-space `"lat,lon"` syntax (**sign/McNemar `p = 6.104e-05`**). Supports `R-TOOL-05` (**T2**). |
| **`PB-1` (Delimiters)** | Equalized wording across `flat_markdown` / `flat_xml` / `nested_xml`, `n = 6` × `5` | `0.972` vs `0.983` (`t(5) = 1.00, p = 0.3632`) vs `0.994` (`t(5) = 2.00, p = 0.1019`) — resolved Phase A `SP-4` bracket-syntax bug (`c5 = 30/30` everywhere). Supports `R-SYS-08` (**T3**). |
| **`PB-5` (Expert Persona)** | Combinatorics puzzles at `reasoning_effort = "low"`, `n = 6` × `5` | `neutral_objective` (`0.967`, `TARa@5 = 83%`) vs `expert_persona` (`0.900`, `TARa@5 = 50%`, `t(5) = -1.00, p = 0.3632`, sign `1+/3-, p = 0.6250`) — underpowered null consistent with **T5** literature (`R-SYS-06`). |
| **Eval v3 Hard Triggering** | `160` 9-skill calls (`12` pos [6 plain + 6 tech], `10` generic distractors, `10` unmatched `'none'`) + `50` solo `'none'` calls | **9-Skill Registry**: Precision **`0.9231`**, Recall **`1.0000` (`60/60`)**, F1 **`0.9600`** (`50/50` distractor negatives, `45/50` unmatched `'none'` rejected with `42/50` literal `'none'`). **Solo-Skill Precision**: **`49/50` (`98.0%`)** stayed `'none'`. |
| **Eval v3 Comparative (Probes & 50/50 Blinded Judge)** | `10` non-leading tasks × `5` repeats (progressive disclosure for `with_skill`; `8` objective probes + `50` counterbalanced pairs) | **Objective Probes (`n = 8`)**: `baseline` **`0.875` (`35/40`)** vs `with_skill` **`0.975` (`39/40`)** (`+0.100`, `t(7) = 0.94, p = 0.3807`), lifting `agentskills.io` spec compliance (`comp_09`) from **`1/5` (`20%`) to `5/5` (`100%`)** and zero-reasoning arithmetic (`comp_07`) from `4/5` to `5/5`. **Blinded Judge (`25/25` counterbalance, same-family caveat)**: `baseline` `0.843` vs `with_skill` `0.827` (`t(9) = -0.52, p = 0.6173`; `24` skill / `24` base / `2` tie), winning `5/5` on legacy prompt audit (`+0.120`) and JSON exclusions (`+0.140`) while penalized on `comp_05`/`comp_06` for copying optional `rationale` from the starter. |

> **Scope Boundary**: Live experiments and evaluations tested `GPT 6 Luna` only. Direct cross-model testing on `Gemini 4 Hydrogen`, `Claude Fable 5.2`, `Claude Opus 5.5`, and `GPT 6.2 Astra` has not yet been executed in this repository.

## Installation & Offline Verification

Install the lean skill directory directly with [vercel-labs/skills](https://github.com/vercel-labs/skills) (`Node.js >= 22.20`):

```bash
# List discovered skills
npx skills add floydous/agent-system-authoring --list

# Install to current project (or add -g for global install)
npx skills add floydous/agent-system-authoring

# Pin to v1.2.0 release tag
npx skills add floydous/agent-system-authoring@v1.2.0
```

Run standalone offline verification and reproducibility checks (Python **standard library only**):

```bash
python skills/agent-system-authoring/scripts/verify_skill.py skills/agent-system-authoring
python evidence/recompute_stats.py --check
python evidence/run_evals.py --rescore-only --check
```

All three commands exit `0` (and run automatically on every push/PR in [.github/workflows/verify.yml](.github/workflows/verify.yml)). Use `--generic` on `verify_skill.py` to validate any external Agent Skill directory.

## Repository Layout

```text
agent-system-authoring/
├── .github/workflows/verify.yml               # Automated CI running verifier & exact reproducibility checks
├── README.md                                  # Repository overview, verified empirical summary & setup
├── LICENSE                                    # MIT License
├── skills/
│   └── agent-system-authoring/                # Lightweight installable Agent Skill discovered by npx skills
│       ├── SKILL.md                           # Runtime-lean skill entrypoint (50 lines, ~1,566 est tokens)
│       ├── assets/templates/                  # Starter system prompt (.md), skill (.md), and OpenAI wire schema (.json)
│       ├── evals/evals.json                   # Eval Suite v3 (32 trigger cases + 10 non-leading comparative tasks)
│       ├── references/                        # Authoring guides, evidence ledger, folklore & open hypotheses
│       └── scripts/verify_skill.py            # Stdlib-only package conformance & hygiene linter (--generic supported)
└── evidence/                                  # Reproducibility archive (excluded from skill installs)
    ├── README.md                              # Provenance index and Phase A/B/C/Eval methodological notes
    ├── recompute_stats.py                     # Stdlib-only prompt-level stats script (supports --check)
    ├── stats_recomputed.md                    # Prompt-level summary tables (paired t, sign test, TARa@5)
    ├── evals_results.md                       # Executed Eval Suite v3 triggering, probe & 50/50 judge report
    ├── source_checks.md                       # Primary-source retrieval verification log
    ├── experiment_harness.py                  # Phase A provenance harness
    ├── phase_b_harness.py                     # Phase B provenance harness
    ├── phase_c_harness.py                     # Phase C counterbalanced & powered provenance harness
    ├── run_evals.py                           # Eval Suite v3 execution, probe & 50/50 judge runner (--check)
    ├── raw/                                   # Phase A JSONL completion logs (228 records)
    ├── raw_phase_b/                           # Phase B JSONL completion logs (480 records)
    ├── raw_phase_c/                           # Phase C JSONL completion logs (480 records)
    └── raw_evals/                             # Executed Eval Suite v3 JSONL logs (440 records)
```

## License

Released under the [MIT License](LICENSE).
