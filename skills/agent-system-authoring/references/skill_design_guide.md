# Agent Skill Architecture & Design Guide

## Overview
An **Agent Skill** is a self-contained directory containing a `SKILL.md` entrypoint plus optional reference manuals, scripts, and templates that agents discover from frontmatter metadata and load on demand via progressive disclosure. This guide reflects the [Agent Skills open specification](https://agentskills.io/specification) verified on 2026-11-22, clearly distinguishing **T1** spec facts, **T3** vendor recommendations, and **Project conventions**.

---

### R-SKILL-01: Package Directory Layout (`T1` + `Project convention`)
- **Evidence Tier**: **T1 (Verified Fact)** — [agentskills.io/specification](https://agentskills.io/specification)
- **Specification Facts**:
  A skill directory requires only `SKILL.md` at its root. The specification defines three optional subdirectories:
  - `scripts/`: Executable code agents can run.
  - `references/`: Additional documentation loaded when needed.
  - `assets/`: Static templates, schemas, images, or data files.
- **Project Conventions**:
  For skills authored with this repository's workflow, `evals/` (`evals.json` trigger/comparative test cases) and repo-root `evidence/` (raw empirical traces and provenance scripts, kept outside `skills/<name>/` so user installs remain lightweight) are adopted as **Project conventions** rather than open-spec mandates. Keep subdirectory names lowercase and limit nesting depth cleanly (e.g., `<= 3` levels). Tailor each skill's workflow, reference checklists, and helper scripts concretely to its target domain rather than copying repo-specific statistical harness boilerplate.

---

### R-SKILL-02: Progressive Disclosure & Context Budget (`T1`)
- **Evidence Tier**: **T1 (Verified Fact)** — [agentskills.io/specification](https://agentskills.io/specification)
- **Specification Guidance**:
  Skill loading occurs in three stages:
  1. **Metadata** (`~100` tokens): Only `name` and `description` load at startup for all skills.
  2. **Instructions** (`< 5000` tokens recommended): The full `SKILL.md` body loads only when activated; keep `SKILL.md` under **`500` lines** and move detailed reference material into separate files.
  3. **Resources** (on demand): Files in `scripts/`, `references/`, and `assets/` load only when referenced and needed.

---

### R-SKILL-03: YAML Frontmatter & Discovery Description (`T1` + `T3`)
- **Evidence Tier**: **T1 (Verified Fact)** ([agentskills.io/specification](https://agentskills.io/specification)) + **T3 (Current Vendor Guidance)** ([Anthropic Skill Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices.md))
- **Verified Field Constraints (`T1`)**:

| Field | Required | Specification Constraint |
| :--- | :---: | :--- |
| `name` | Yes | `1–64` characters; lowercase alphanumeric (`a-z`, `0-9`) and hyphens (`-`) only; no leading/trailing/consecutive `-`; must match parent directory name. |
| `description` | Yes | `1–1024` characters; non-empty; describes **what** the skill does and **when** to use it. |
| `license` | No | License identifier or path to bundled license file. |
| `compatibility` | No | Max `500` characters specifying environment prerequisites. |
| `metadata` | No | Arbitrary string-to-string key-value mapping (`map[string]string`). |
| `allowed-tools` | No | Space-delimited list of pre-approved tools (experimental). |

- **Authoring Guidance (`T3` — not measured by us)**:
  Anthropic's skill authoring best practices state: *"Always write in third person. The description is injected into the system prompt, and inconsistent point-of-view can cause discovery problems."* (The `agentskills.io` optimizing-descriptions guide notes pairing clear capability triggers with near-miss keywords, even when users do not mention exact domain jargon.)

---

### R-SKILL-04: Shallow Relative Linking (`T1`)
- **Evidence Tier**: **T1 (Verified Fact)** — [agentskills.io/specification](https://agentskills.io/specification)
- **Specification Guidance**:
  - Reference bundled files using relative paths from the skill root (e.g., `references/system_instructions_guide.md`).
  - *"Keep file references one level deep from `SKILL.md`. Avoid deeply nested reference chains."*
  - Avoid parent-directory traversal (`../`) in portable skill documentation links outside self-contained internal references.

---

### R-SKILL-05: Packaging Hygiene (`Project convention`)
- **Evidence Tier**: **Project convention**
- **Convention Rules**:
  Keep distributed skill packages focused on runtime execution and concise authoring documentation rather than development residue:
  - **Omit Private Secrets**: Never bundle API keys, bearer tokens, passwords, or internal private endpoints.
  - **Omit Transient Caches**: Clean `__pycache__/`, `.pytest_cache/`, `.mypy_cache/`, `.DS_Store`, and temporary scratch artifacts before shipping.
  - **Omit Development Test Runners & Synthetic/Mock Dumps**: Keep `tests/`, `pytest.ini`, and `mock_*` files out of the skill bundle. Keep heavy empirical traces and provenance scripts isolated in a separate repo-root `evidence/` archive rather than inside the installable `skills/<skill-name>/` package.

---

### R-SKILL-06: Portable Scripting & PEP 723 (`T1`)
- **Evidence Tier**: **T1 (Verified Fact)** — [PEP 723](https://peps.python.org/pep-0723/) & [Inline Script Metadata Spec](https://packaging.python.org/en/latest/specifications/inline-script-metadata/)
- **Verified Standard**:
  When shipping Python helper scripts that declare external packages (or standalone runnable metadata), use PEP 723 inline metadata blocks:
  ```python
  # /// script
  # requires-python = ">=3.10"
  # dependencies = []
  # ///
  ```
  Prefer Python's standard library where practical (`pathlib.Path`, `encoding="utf-8"`) so scripts execute reliably across Windows, macOS, and Linux without fragile environment setup.

---

## Operational Workflow Patterns (`Project convention`)
Spec conformance (`R-SKILL-01`–`R-SKILL-06`) ensures a skill **loads cleanly**, while operational workflow patterns ensure agents **execute reliably** on real multi-step tasks. Apply only the patterns warranted by the skill's complexity (keep lightweight skills minimal):

1. **Mode Routing & Progressive Entrypoints**:
   - Place a short routing block near the top of `SKILL.md` when a skill supports distinct modes (e.g., quick single-file fix vs. full-project workflow, or scratch authoring vs. auditing).
   - Keep the common fast path inline in `SKILL.md` and send deep multi-stage workflows to a dedicated one-hop `references/<workflow>.md` guide so activation context stays within `R-SKILL-02`.
2. **Fact-Finding vs. Human Stop Gates**:
   - Explicitly separate **facts** the agent must discover via workspace inspection/tools from **decisions** the user owns (product scope, compatibility bars, destructive mutations).
   - For multi-decision tasks, interview in compact frontier rounds: number each open decision, propose a recommended default so brief confirmation accepts it, and defer dependent questions until prerequisites settle.
   - Insert hard stop gates before irreversible actions (e.g., *"Plan, then stop — wait for approval"* or *"Ask before modifying production source files"*).
3. **Anti-Shortcut & Verification-Integrity Invariants**:
   - Explicitly prohibit agents from gaming verification checks: never edit recorded test fixtures or golden outputs to force a pass, never widen numeric/matching tolerances to hide failures without user approval, never drop assertions to make a suite green, and never hardcode expected test results into runtime code.
4. **Stall / Loop Circuit Breakers**:
   - Define an explicit retry cap (e.g., `2–3` consecutive edits that yield zero progress on the same failing check). When hit, stop editing, show the exact remaining failure/diff, and escalate to the user rather than burning tokens in an open-ended loop.
5. **Cross-Session State & Correction Capture (Long-Horizon Skills)**:
   - For workflows that span multiple sessions or subagents, define lightweight pointer-not-copy artifacts in the target project (e.g., a status map, append-only architectural decisions, a session handoff, and a one-sentence learned-corrections list appended immediately whenever the user corrects behavior) so new sessions resume accurately without duplicating prose or repeating past mistakes.
6. **Objective Done Criteria & Reporting Contract**:
   - Anchor completion to a deterministic verification command (`exit code 0`) rather than agent self-report, and specify a fixed closing report (what changed, exact verification results, and remaining risks or unverified assumptions).

---

## Evaluation Design & CI Drift Checks (`Project convention`)
Combine static drift tests, single-turn trigger/quality evals, and (for tool-driving skills) end-to-end headless agent A/B tests:

### 1. Single-Turn Trigger & Comparative Suite (`evals/evals.json`)
Consistent with `agentskills.io` description-optimization guidance, pair three test types inside `evals/evals.json`:
1. **`trigger_positive`**: Realistic prompts that should activate the skill without naming it explicitly.
2. **`trigger_negative`**: Near-miss prompts sharing vocabulary with the domain (e.g., running SQL directly rather than designing a SQL tool schema) that should **not** trigger activation.
3. **`comparative`**: Multi-dimensional rubric comparisons evaluating skill-guided output against an unguided baseline across `N >= 5` iterations (`R-SYS-10`). Note: treat unexecuted `evals.json` definitions as test specifications rather than completed benchmark proof.

### 2. CLI & Command-Drift CI Checks
When a skill instructs agents to invoke bundled scripts or an external CLI, stale flags or renamed subcommands send every run down a dead end. Add an offline CI test that extracts fenced code blocks and inline backtick spans from `SKILL.md` and `references/*.md` and verifies every referenced command/flag against the actual CLI `--help` or `argparse` schema.

### 3. End-to-End Headless Agent A/B Evals
Single-turn completions measure prompt quality, not multi-turn tool execution. For workflow-heavy skills, add an A/B harness that runs two skill directories (`--variant current=...` vs. `--variant draft=...`) inside fresh temporary fixture copies using a headless coding agent:
- **Deterministic Grading**: Score each run strictly by running an objective verifier/gate (`exit code 0`) on the workspace the agent produced — not by what the agent claims in its final message.
- **Efficiency Telemetry**: Log pass rate alongside **turns**, **wall-clock seconds**, and **token / USD cost** across `N >= 5` runs (`R-SYS-10`), since wording edits often change turn count and cost even when pass rates tie.
- **Global-Install Isolation**: Before running A/B comparisons, uninstall or disable any user-level global copy of the skill (e.g., `~/.claude/skills/<name>` or global agent skill dirs) so both variants do not silently load the global install instead of the isolated workspace variant.

---

## Pre-Release Authoring Checklist
1. Verify `name` (`kebab-case`, `1–64` chars) matches parent folder name (`R-SKILL-03`, `T1`).
2. Confirm `description` (`1–1024` chars) states what + when in third person (`R-SKILL-03`, `T1`/`T3`).
3. Keep `SKILL.md` `< 500` lines and `< 5000` tokens (`R-SKILL-02`, `T1`), linking reference files directly one level deep (`R-SKILL-04`, `T1`).
4. Confirm operational clarity: mode routing (if multi-mode), inspect-first fact gathering, explicit stop gates, anti-shortcut invariants, stall circuit breaker, and objective done criteria (`Project convention`).
5. Confirm every script declares PEP 723 metadata (`R-SKILL-06`, `T1`) and uses UTF-8 / `pathlib.Path`, and verify referenced CLI flags match actual `--help` / parser definitions.
6. Remove all secrets, `__pycache__/`, `.pytest_cache/`, and `mock_*` files (`R-SKILL-05`, `Project convention`).
7. Run `python -B <skill-dir>/scripts/verify_skill.py --generic <target-skill-dir>` (exit code `0`) and confirm `evals/evals.json` validity (and isolate global skill installs before running headless agent A/B evals).
