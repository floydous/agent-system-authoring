<h1 align="center">agent-system-authoring</h1>

<p align="center">
  <strong>Evidence-backed rules for writing LLM system prompts, tool schemas, and portable Agent Skills.</strong>
</p>

<p align="center">
  <a href="https://github.com/floydous/agent-system-authoring/actions/workflows/verify.yml"><img src="https://github.com/floydous/agent-system-authoring/actions/workflows/verify.yml/badge.svg" alt="Verify Skill & Recompute Evidence"></a>
  <a href="https://agentskills.io/specification"><img src="https://img.shields.io/badge/Agent%20Skills-spec%20compliant-2a78d6" alt="Agent Skills Spec"></a>
  <a href="skills/agent-system-authoring/SKILL.md"><img src="https://img.shields.io/badge/version-v1.4.0-4c1" alt="Version v1.4.0"></a>
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
    <td align="center" width="190"><h3>5,238</h3><b>Benchmark runs</b><br><sub>3 model families, 2 architectures</sub></td>
    <td align="center" width="190"><h3>28</h3><b>Tagged rules</b><br><sub>every rule linked to its proof</sub></td>
    <td align="center" width="190"><h3>3</h3><b>API providers</b><br><sub>OpenAI, Anthropic, Gemini</sub></td>
    <td align="center" width="190"><h3>214.6 KB</h3><b>Skill install</b><br><sub>55-line SKILL.md, 14 files</sub></td>
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

# Pin to the v1.4.0 release tag
npx skills add floydous/agent-system-authoring@v1.4.0
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
      <h4><a href="skills/agent-system-authoring/references/evidence_ledger.md">Evidence and templates</a></h4>
      <p>All 28 rules with verification tiers, a list of refuted myths, open hypotheses, and ready-to-edit starter templates.</p>
      <br/>
    </td>
  </tr>
</table>

*Starter files:* [SKILL.md](skills/agent-system-authoring/SKILL.md) · [System Prompt Template](skills/agent-system-authoring/assets/templates/system_prompt_template.md) · [Tool Schema Template](skills/agent-system-authoring/assets/templates/tool_schema_template.json) · [Zero-Reasoning Tool Template](skills/agent-system-authoring/assets/templates/tool_schema_zero_reasoning_template.json) · [Debunked Folklore](skills/agent-system-authoring/references/debunked_folklore.md)

## What held up

We ran `5,238` benchmark calls across three model families (`GPT 6 Luna`, `Particle-1`, and `Nemotron 3.5 Lightning` Mamba-2 SSM) plus `490` skill-eval calls. Repeated runs (`N = 5` per prompt) are averaged at the prompt level before statistical testing to avoid inflated sample counts.

| What we tested | Measured result | Practical rule |
| :--- | :--- | :--- |
| **Parameter descriptions** | `3%` to `8%` -> **`100%`** valid (`3/3` models) | Spell out exact formats, spacing, and units; also cut thinking tokens up to `45%`. |
| **Assertive tool hype** (`"best"`, `"always use"`) | `0%` to `4%` -> **`94%` to `100%`** hijack (`3/3` models) | Promotional superlatives skew tool routing; keep descriptions factual and neutral. |
| **Explicit word bans** vs polite hints | `54%` to `65%` -> **`89%` to `100%`** clean (`3/3` models) | Name forbidden words directly (plus compound rules) instead of relying on suggestions. |
| **Rule count scaling** (`10` vs `20` to `50` rules) | `100%` -> **`49%` to `59%`** strict pass (`3.5x` thinking) | Keep active rule lists compact and break large instruction sets into phases. |
| **In-schema `rationale` field** (thinking off) | `0%` to `37%` -> **`86%` to `100%`** (`2/2` architectures) | Put `rationale` first only when pre-output thinking is off; omit it on reasoning models. |
| **TypeScript vs JSON Schema in prompts** | **`100%`** accuracy parity, **`~50%`** fewer prompt tokens | Use TypeScript interfaces inside prose prompts; keep JSON Schema for tool APIs. |
| **Expert personas, spelled digits, `###` headers** | **No accuracy lift** (statistically flat) | Drop honorary expert personas, keep normal numbers, and write plain prose tool docs. |

**Skill evals:** `1.000` precision and recall on the 9-skill trigger suite (`160` calls), `50/50` solo-skill precision, and `39/40` vs `38/40` on objective authoring probes ([evals_results.md](evidence/evals_results.md)).

> [!NOTE]
> Live runs tested `GPT 6 Luna`, `Particle-1` (DeepSeek V4.1 Flash lineage), and `Nemotron 3.5 Lightning` (`30B-A3B` Mamba-2 SSM). A `Ling 3.2 Flash` harness preset is ready in `evidence/phase_f_harness.py`, while closed frontier models (`Claude Opus 5.5`, `Claude Fable 5.2`, `Gemini 4 Hydrogen`, `GPT 6.2 Astra`) remain open in [unverified_hypotheses.md](skills/agent-system-authoring/references/unverified_hypotheses.md).

<details>
<summary><strong>Evidence tiers (T1 to T5)</strong></summary>

Every rule in [evidence_ledger.md](skills/agent-system-authoring/references/evidence_ledger.md) carries one primary verification tag:

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
<summary><strong>Full benchmark archive (5,238 benchmark calls + 490 eval calls)</strong></summary>

| Suite | Model | Calls | Focus | Full report |
| :--- | :--- | :---: | :--- | :--- |
| **Phase A** | `GPT 6 Luna` | 228 | Initial screening across 7 prompt and schema suites | [stats_recomputed.md](evidence/stats_recomputed.md) |
| **Phase B** | `GPT 6 Luna` | 480 | Equalized delimiters, personas, `rationale` ordering (`N = 5`) | [stats_recomputed.md](evidence/stats_recomputed.md) |
| **Phase C** | `GPT 6 Luna` | 480 | Counterbalanced tool gaming (`PC-1`) and explicit bans (`PC-2`) | [stats_recomputed.md](evidence/stats_recomputed.md) |
| **Phase D** | `GPT 6 Luna` | 1,030 | Param descriptions, verbosity ceiling, headers, digits, TS vs JSON | [stats_recomputed.md](evidence/stats_recomputed.md) |
| **Phase E** | `GPT 6 Luna` (`high`) | 880 | Rule density (`5` to `50`), long-context reminders, hard math personas | [stats_recomputed.md](evidence/stats_recomputed.md) |
| **`H-08` Replication** | `Particle-1` (DeepSeek V4.1 Flash) | 950 | Cross-model replication of `PC-1`, `PC-2`, `PD-1`, `PD-4`, `PD-5` | [stats_recomputed.md](evidence/stats_recomputed.md) |
| **Phase F Cross-Arch** | `Nemotron 3.5 Lightning` (Mamba-2 SSM) | 1,190 | Cross-architecture replication of `PB-6`, `PC-1`, `PC-2`, `PD-1`, `PD-4`, `PE-2` | [stats_recomputed.md](evidence/stats_recomputed.md) |
| **Eval Suite v4** | `GPT 6 Luna` | 490 | 9-skill triggering, solo precision, objective probes, dual-order judge | [evals_results.md](evidence/evals_results.md) |

All `5,010` Phase B to F and `H-08` runs and all `490` Eval v4 runs completed with `0` gateway errors. Narrative synthesis lives in [empirical_results.md](skills/agent-system-authoring/references/empirical_results.md).

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
