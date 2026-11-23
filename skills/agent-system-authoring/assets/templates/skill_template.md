---
name: specialized-skill-name
description: Authors and audits specialized domain workflows in clear third-person prose. Use when designing, writing, verifying, or troubleshooting domain artifacts, even when the user does not mention the skill name directly.
compatibility: Python 3.10+, standard POSIX/Windows shell (optional)
metadata:
  version: "1.0.0"
  author: "[author-or-team]"
---

# Specialized Skill Name: Procedural Runbook

## Overview
Concise summary of the domain capability, boundaries, and verification rules. Keep `SKILL.md` under `500` lines and `< 5000` tokens, delegating detailed reference catalogs and evidence matrices into `references/` via single-hop relative links.

---

## Procedural Workflow

### Step 1: Scope Requirements and Input Invariants
1. Validate input parameters, types, and operational guardrails before executing actions.
2. Keep concurrent instructions minimal and split complex workflows into sequential phases ([references/workflow_guide.md](references/workflow_guide.md)).
3. Separate trusted system instructions from untrusted external inputs ([references/workflow_guide.md](references/workflow_guide.md)).

### Step 2: Load Domain References On Demand
1. Load only the specific files from `references/` required for the current task step using direct one-level links.
2. Use flat Markdown section headers for general instructions, keeping any Claude-targeted XML tags flat unless hierarchy is inherent.

### Step 3: Execute Operations
1. Apply domain transformations cleanly without promotional or vague directives.
2. Invoke bundled utilities from `scripts/` via standard CLI flags and exit codes:
   ```bash
   python scripts/run_task.py --input <input_path> --output <output_path>
   ```

### Step 4: Verify Quality and Package Hygiene
1. Validate outputs against explicit schema and boundary constraints (`N >= 5` evaluation runs where benchmarking quality).
2. Run any domain-specific validation script you ship under `scripts/` before delivery (example pattern):
   ```bash
   python scripts/validate_package.py .
   ```
3. Enforce clean packaging: remove private credentials, `__pycache__/`, `.pytest_cache/`, development `tests/` suites, and mock/synthetic dumps. Keep heavy empirical traces or provenance archives outside the installable skill directory (for example, in a repo-root `evidence/` folder).

---

## References & Files

| File | Purpose |
| :--- | :--- |
| [references/workflow_guide.md](references/workflow_guide.md) | Detailed procedural rules and domain edge cases. |
| [references/evidence_ledger.md](references/evidence_ledger.md) | Traceability table linking rules to sources and tiers. |
| [evals/evals.json](evals/evals.json) | Triggering and comparative evaluation test cases. |
