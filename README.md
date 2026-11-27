<h1 align="center">agent-system-authoring</h1>

<p align="center">
  <strong>Evidence-backed rules for writing LLM system prompts, tool schemas, and portable Agent Skills.</strong>
</p>

<p align="center">
  <a href="https://github.com/floydous/agent-system-authoring/actions/workflows/verify.yml"><img src="https://github.com/floydous/agent-system-authoring/actions/workflows/verify.yml/badge.svg" alt="Verify Skill & Recompute Evidence"></a>
  <a href="https://agentskills.io/specification"><img src="https://img.shields.io/badge/Agent%20Skills-spec%20compliant-2a78d6" alt="Agent Skills Spec"></a>
  <a href="skills/agent-system-authoring/SKILL.md"><img src="https://img.shields.io/badge/version-v2.0.0-4c1" alt="Version v2.0.0"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue" alt="MIT License"></a>
</p>

<p align="center">
  <a href="#quickstart">Quickstart</a> ·
  <a href="#whats-included">What's Included</a> ·
  <a href="#what-held-up">What Held Up</a> ·
  <a href="#verify-locally">Verify Locally</a> ·
  <a href="evidence/README.md">Evidence Archive</a>
</p>

<table align="center">
  <tr>
    <td align="center" width="190"><h3>8,028</h3><b>Benchmark runs</b><br><sub>4 model families, 3 architectures</sub></td>
    <td align="center" width="190"><h3>28</h3><b>Tagged rules</b><br><sub>every rule linked to its proof</sub></td>
    <td align="center" width="190"><h3>3</h3><b>API providers</b><br><sub>OpenAI, Anthropic, Gemini</sub></td>
    <td align="center" width="190"><h3>115.5 KB</h3><b>Skill install</b><br><sub>55-line SKILL.md, 11 files</sub></td>
  </tr>
</table>

---

## Quickstart

Install the skill with [vercel-labs/skills](https://github.com/vercel-labs/skills) (`Node.js >= 22.20`):

```bash
npx skills add floydous/agent-system-authoring
```

Only `skills/agent-system-authoring/` gets installed into your project. Raw benchmark logs, provenance harnesses, and unit tests stay out of your workspace.

<details>
<summary><strong>More install options (preview, global, pinned version)</strong></summary>

```bash
# Inspect discovered skills before installing
npx skills add floydous/agent-system-authoring --list

# Install globally across projects
npx skills add floydous/agent-system-authoring -g

# Pin to the v2.0.0 release tag
npx skills add floydous/agent-system-authoring@v2.0.0
```

</details>

## Why this exists

Most prompting advice circulates as folklore. A trick from an older model gets copied into production prompts, and nobody checks whether it still helps or just burns tokens.

This skill gives coding agents a short, tested playbook for authoring system prompts, tool schemas, and portable Agent Skills. Every rule states how we know it works: checked directly against provider API docs, measured across repeated model runs, or labeled clearly as vendor guidance or an open question.

## What's included

<table width="100%">
  <tr>
    <td width="50%" valign="top">
      <h4><a href="skills/agent-system-authoring/references/system_instructions_guide.md">System prompts</a></h4>
      <p>Instruction hierarchy, keeping active rule counts small, explicit word bans, clean delimiters, and skipping filler personas.</p>
      <br/>
    </td>
    <td width="50%" valign="top">
      <h4><a href="skills/agent-system-authoring/references/tool_schema_guide.md">Multi-provider tool schemas</a></h4>
      <p>Exact strict-mode JSON shapes for OpenAI, Anthropic, and Gemini, neutral tool descriptions, and parameter format rules.</p>
      <br/>
    </td>
  </tr>
  <tr>
    <td width="50%" valign="top">
      <h4><a href="skills/agent-system-authoring/references/skill_design_guide.md">Portable Agent Skills</a></h4>
      <p>Spec-compliant <code>SKILL.md</code> structure, progressive disclosure, one-hop references, PEP 723 scripts, and a standalone linter.</p>
      <br/>
    </td>
    <td width="50%" valign="top">
      <h4><a href="evidence/evidence_ledger.md">Evidence and templates</a></h4>
      <p>All 28 rules with verification tiers, a list of refuted myths, open hypotheses, and ready-to-edit starter templates.</p>
      <br/>
    </td>
  </tr>
</table>

*Starter files:* [SKILL.md](skills/agent-system-authoring/SKILL.md) · [System Prompt Template](skills/agent-system-authoring/assets/templates/system_prompt_template.md) · [Tool Schema Template](skills/agent-system-authoring/assets/templates/tool_schema_template.json) · [Zero-Reasoning Tool Template](skills/agent-system-authoring/assets/templates/tool_schema_zero_reasoning_template.json) · [Debunked Folklore](skills/agent-system-authoring/references/debunked_folklore.md)

## What held up

We ran `8,028` benchmark calls across four model families (`GPT 6 Luna`, `Particle-1`, `Nemotron 3.5 Lightning` Mamba-2 SSM, and `Ling 3.2 Flash` Hybrid-Linear MoE) plus `490` skill-eval calls. Repeated runs (`N = 5` per prompt) are averaged at the prompt level before statistical testing to avoid inflated sample counts.

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="evidence/charts/what_held_up_dark.png">
    <source media="(prefers-color-scheme: light)" srcset="evidence/charts/what_held_up_light.png">
    <img alt="Benchmark summary chart comparing baseline and intervention pass rates, prompt token savings, and thinking token savings across 4 model families and 3 architectures" src="evidence/charts/what_held_up_light.png" width="100%">
  </picture>
</p>

**Key rules to apply:** spell out exact parameter formats and units (cuts thinking tokens across all 4 families too), keep tool descriptions factual and neutral, prune bloated tool catalogs, name banned words explicitly, break large rule sets into compact phases, put `rationale` first only when pre-output thinking is off, use TypeScript interfaces inside prose prompts (keep JSON Schema for tool APIs), and drop CoT directives, superfluous few-shot examples, honorary expert personas, and `###` tool headers.

**Skill evals:** `1.000` precision and recall on the 9-skill trigger suite (`160` calls), `50/50` solo-skill precision, and `39/40` vs `38/40` on objective authoring probes ([evals_results.md](evidence/evals_results.md)). On real multi-turn coding-agent tasks (`55` isolated `pi v1.6.0` sessions on `GPT 6 Luna`, deterministic workspace grading), the skill lifted multi-provider tool repair **`42% → 78%`** (`p = 0.0079`, `-33%` turns, `-25%` tokens, `-34%` wall time) and skill-package repair **`58% → 76%`** (`p = 0.0317`), with an A/B-verified Step-3 fix lifting strict `10/10` pass rate **`0/5 → 5/5`** (`p = 0.0079`, `-11%` tokens) and post-slim verification (`115.5 KB`) holding `96%` (`4/5` strict, `p = 1.00`) and `90%` (`p = 0.72`) while trimming tokens across all 3 tasks.

> [!NOTE]
> Live runs tested four model families across three architectures: `GPT 6 Luna`, `Particle-1` (DeepSeek V4.1 Flash lineage), `Nemotron 3.5 Lightning` (`30B-A3B` Mamba-2 SSM hybrid), and `Ling 3.2 Flash` (`~560B-A25B` Hybrid-Linear KDA+MLA MoE). Closed frontier models (`Claude Opus 5.5`, `Claude Fable 5.2`, `Gemini 4 Hydrogen`, `GPT 6.2 Astra`) remain open in [unverified_hypotheses.md](evidence/unverified_hypotheses.md).

<details>
<summary><strong>Evidence tiers (T1 to T5)</strong></summary>

Every rule in [evidence_ledger.md](evidence/evidence_ledger.md) carries one primary verification tag:

| Tier | Meaning |
| :--- | :--- |
| **T1** | Specification or provider API rule checked directly against official docs ([source_checks.md](evidence/source_checks.md)). |
| **T2** | Statistically significant prompt-level effect recomputed offline from bundled traces ([stats_recomputed.md](evidence/stats_recomputed.md)). |
| **T3** | Current official vendor guidance (Anthropic, OpenAI, Google), not measured by our harness. |
| **T4** | Peer-reviewed finding rooted in fixed mechanics (BPE tokenization, constrained decoding, context cost, FP non-determinism). |
| **T5** | Peer-reviewed learned behavior from earlier models; transfer to newer models is plausible but not re-measured. |
| **Methodology / Convention** | Evaluation design principles (`R-SYS-10`) or repo engineering standards (`R-SKILL-05`). |

</details>

<details>
<summary><strong>Full benchmark archive (8,028 benchmark calls + 490 eval calls + 55 real-agent Pi sessions)</strong></summary>

| Suite | Model | Calls | Focus | Full report |
| :--- | :--- | :---: | :--- | :--- |
| **Phase A** | `GPT 6 Luna` | 228 | Initial screening across 7 prompt and schema suites | [stats_recomputed.md](evidence/stats_recomputed.md) |
| **Phase B** | `GPT 6 Luna` | 480 | Equalized delimiters, personas, `rationale` ordering (`N = 5`) | [stats_recomputed.md](evidence/stats_recomputed.md) |
| **Phase C** | `GPT 6 Luna` | 480 | Counterbalanced tool gaming (`PC-1`) and explicit bans (`PC-2`) | [stats_recomputed.md](evidence/stats_recomputed.md) |
| **Phase D** | `GPT 6 Luna` | 1,030 | Param descriptions, verbosity ceiling, headers, digits, TS vs JSON | [stats_recomputed.md](evidence/stats_recomputed.md) |
| **Phase E** | `GPT 6 Luna` (`high`) | 880 | Rule density (`5` to `50`), long-context reminders, hard math personas | [stats_recomputed.md](evidence/stats_recomputed.md) |
| **`H-08` Replication** | `Particle-1` (DeepSeek V4.1 Flash) | 950 | Cross-model replication of `PC-1`, `PC-2`, `PD-1`, `PD-4`, `PD-5` | [stats_recomputed.md](evidence/stats_recomputed.md) |
| **Phase F Cross-Arch (Nemotron)** | `Nemotron 3.5 Lightning` (Mamba-2 SSM) | 1,190 | Cross-architecture replication of `PB-6`, `PC-1`, `PC-2`, `PD-1`, `PD-4`, `PE-2` | [stats_recomputed.md](evidence/stats_recomputed.md) |
| **Phase F Cross-Arch (Ling)** | `Ling 3.2 Flash` (Hybrid-Linear MoE) | 1,510 | Cross-architecture replication of `PB-6`, `PE-1`, `PC-1`, `PC-2`, `PD-1`, `PD-4`, `PD-5` | [stats_recomputed.md](evidence/stats_recomputed.md) |
| **Phase G Stress & Untouched Rules** | `GPT 6 Luna` | 1,280 | Tool catalog scaling (`PG-1`), CoT on reasoning (`PG-2`), conflicting few-shots (`PG-3`), 16-turn memory (`PG-4`), 67k context (`PG-5`) | [stats_recomputed.md](evidence/stats_recomputed.md) |
| **Eval Suite v4** | `GPT 6 Luna` | 490 | 9-skill triggering, solo precision, objective probes, dual-order judge | [evals_results.md](evidence/evals_results.md) |
| **Pi Real-Agent Evals** | `GPT 6 Luna` (`pi v1.6.0`) | 55 sessions | Multi-turn broken-repo repair (`N = 5` × 3 repos), paired A/B Step-3 fix, post-slim verification | [stats_recomputed.md](evidence/stats_recomputed.md) |

All `7,800` Phase B to G and `H-08` runs, all `490` Eval v4 runs, and all `55` real-agent Pi sessions completed with `0` errors. Narrative synthesis lives in [empirical_results.md](evidence/empirical_results.md).

</details>

## Verify locally

All packaging checks, unit tests, and statistical tables reproduce offline using Python's standard library alone (no API keys or extra packages required):

```bash
python -B skills/agent-system-authoring/scripts/verify_skill.py skills/agent-system-authoring
python -B skills/agent-system-authoring/scripts/verify_skill.py --generic skills/agent-system-authoring
python -B evidence/recompute_stats.py --check
python -B evidence/run_evals.py --rescore-only --check
python -B -m unittest discover -s tests -v
```

These same checks run automatically on Ubuntu and Windows in [.github/workflows/verify.yml](.github/workflows/verify.yml). Pass `--generic` to `verify_skill.py` to lint any external Agent Skill folder.

## Repository layout

| Path | Contents |
| :--- | :--- |
| [`skills/agent-system-authoring/`](skills/agent-system-authoring/SKILL.md) | Installable skill package: `SKILL.md`, authoring guides, starter templates, eval suite, and stdlib linter. |
| [`evidence/`](evidence/README.md) | Raw JSONL completion traces, provenance harnesses, primary-source check log, and offline stats scripts. |
| [`tests/`](tests/) | Standard-library unit tests covering `verify_skill.py` and evidence utilities. |
| [`.github/workflows/verify.yml`](.github/workflows/verify.yml) | Cross-OS GitHub Actions workflow enforcing skill conformance and stats reproducibility. |

## License

Released under the [MIT License](LICENSE).
