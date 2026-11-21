# Unverified Hypotheses, Contested Effects & Unsupported Claims Register

## Executive Summary
Under this skill's evidence policy, items are placed here **only** when:
1. A previously cited numerical threshold or claim was not supported by retrieved primary source text (**Unsupported Claim**);
2. A learned-behavior finding failed to reproduce on `cx/gpt-6-luna (thinking level: xhigh)` (**Contested / Not Reproduced**); or
3. An engineering question lacks decisive experimental verification (**Open Hypothesis**).

Findings from earlier models whose mechanism or training effect remains supported by primary literature are **not** placed here solely due to model age; they remain active rules in the skill guides with their tested models disclosed.

---

## 1. Unsupported Claims & Numbers Removed From Active Rules

The following specific numbers and thresholds appeared in earlier versions of this repository but were **absent from or contradicted by** the retrieved primary texts verified in [source_checks.md](../evidence/source_checks.md):

1. **Fabricated `<= 10` Simultaneous Instruction Cap & `100% -> 21%` Collapse (formerly `R-SYS-01`)**:
   - *Removed claim*: "Cap active concurrent rules to `<= 10`; GPT-4o accuracy collapses from 100% to 21% at 10 rules; o3 holds up to 15–20 rules."
   - *Retrieved primary evidence*: Jaroslawicz et al. ([arXiv:2507.11538](https://arxiv.org/abs/2507.11538)) starts IFScale at 10 keyword-inclusion items and scales to 500 (reporting 68% best accuracy at 500 across 20 models); Harada et al. ([arXiv:2509.21051](https://arxiv.org/abs/2509.21051)) tests up to 10 instructions (ManyIFEval) and 6 style constraints (StyleMBPP), finding consistent degradation with increasing count, with neither `21%` nor a universal `<= 10` threshold in the retrieved abstracts.
   - *Verification needed*: Test behavioral system-rule compliance across 5, 10, 20, and 50 concurrent non-keyword constraints with `N >= 5` iterations per prompt.
2. **Misstated Two-to-Four Concise Sentences Tool Description Rule (formerly `R-TOOL-03`)**:
   - *Removed claim*: Restricting tool descriptions to at most four short sentences attributed to Anthropic.
   - *Retrieved primary evidence*: Anthropic's retrieved guide ([define-tools](https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools)) actually states: `"Aim for at least 3–4 sentences for each tool description, more if the tool is complex."`
3. **Invented Enum Cardinality Cutoffs (`<= 20`, `20–50`, `+15–25 pp`, `>30%`, `10%–25%`) (formerly `R-TOOL-06`, `R-TOOL-07`)**:
   - *Removed claim*: Fixed `<= 20` and `>20–50` boundaries and unverified accuracy deltas.
   - *Retrieved primary evidence*: OpenAI Structured Outputs documents `1,000` max enum values across a schema and `15,000` chars when a single string enum exceeds `250` values; Google Gemini Structured Outputs documents state-machine `400 INVALID_ARGUMENT` limits without a fixed integer cutoff.
4. **Invented Tool Catalog Cap (`<= 10–20` tools, `Top-3 to Top-5`, `8K–120K`, `85.5%`) (formerly `R-TOOL-08`)**:
   - *Removed claim*: Specific `<= 10–20` active tool limit and `Top-3 to Top-5` RAG cutoff.
   - *Retrieved primary evidence*: Kate et al. (`LongFuncEval`, [arXiv:2505.10570](https://arxiv.org/abs/2505.10570)) reports `7%` to `85%` (not `85.5%`) drop as tool count increases without specifying `<= 10–20`.
5. **Invented Few-Shot Numbers (`k in [2, 4]`, `>85%` override) & Misapplied Citation (formerly `R-SYS-09`)**:
   - *Removed claim*: Optimal shot range `[2, 4]` and `>85%` written-rule override attributed to Tang et al. and Pecher et al.
   - *Retrieved primary evidence*: Tang et al. ([arXiv:2509.13196](https://arxiv.org/abs/2509.13196)) does not claim `k in [2, 4]` in its abstract; Pecher et al. ([arXiv:2602.04297](https://arxiv.org/abs/2602.04297)) studies prompt underspecification rather than conflicting demonstrations. (Replaced conflicting-example citation with Camassa & Shiller, [arXiv:2605.20382](https://arxiv.org/abs/2605.20382), reporting 27%/43% grand-mean rule compliance across 13 models.)
6. **Unsupported `63%` Prompt-Injection Metric & GPT-4 Claim (formerly `R-SYS-03`)**:
   - *Removed claim*: "Up to 63% attack reduction" across GPT-4/4o in Wallace et al. ([arXiv:2404.13208](https://arxiv.org/abs/2404.13208)).
   - *Retrieved primary evidence*: Abstract states qualitative `"drastically increases robustness"` applied to `GPT-3.5`.
7. **Other Unsupported Numbers Removed**:
   - `R-SYS-02` / `R-TOOL-12`: Removed `>20% to 40%` (not in Liu et al. abstract) and `>20% degradation avoided`.
   - `R-SYS-05`: Removed `~50%` flatline figure (not in Jang et al. abstract).
   - `R-SYS-07`: Removed `13 of 14 models` and `-16.2 pp` (not in Li et al. abstract) and `"officially deprecates"`.
   - `R-TOOL-01`: Removed `15%–40% fertility` (not in TokDrift abstract).
   - `R-TOOL-02`: Removed `>30% delta` (not in ToolSandbox/BFCL abstracts).
   - `R-TOOL-09`: Removed `40% false-positive invocations`.

---

## 2. Statistically Inconclusive / Ceiling Comparisons After Phase B

### C-01: Paired Affirmative Substitutes vs Bare Prohibitions (`R-SYS-05`, `PB-4`)
- **Resolved in Phase B**: `affirmative_only` (without explicit prohibitions) dropped to `14/30` (`46.7%`), losing significantly to `bare_negative` (`27/30` = `90.0%`, `p = 0.0006`) and `paired_affirmative` (`30/30` = `100.0%`, `p = 1.944e-06`).
- **Remaining Inconclusive Contrast**: `paired_affirmative` (`30/30`, `TARa@5 = 100%`) vs `bare_negative` (`27/30`, `TARa@5 = 83%`, Fisher `p = 0.2373`, paired `t = 1.00`, `p = 0.3632`) is directionally consistent across 30 runs but does not reach `alpha = 0.05`. Testing across a larger prompt set (`N >= 15` prompts × `5` repeats) is needed to resolve whether adding positive substitutes yields a reliable ~10 pp gain over bare prohibitions alone.

### C-02: Prospective Memory Under High Reasoning Effort (`R-SYS-04`, `PB-3`)
- **Phase B Observation**: Even under ~1,200 words of noisy log distractors, `cx/gpt-6-luna (xhigh)` scored `30/30` (`1.000`) in both `system_only` and `sandwich_reminder` (ceiling/uninformative). Multi-turn sessions exceeding 50% context utilization remain untested here.

---

## 3. Open Research Hypotheses (`[NO EVIDENCE YET]` / `[ACTIVE HYPOTHESIS]`)

*(Note: Phase B resolved former `H-01` via `PB-6` [`36.7%` -> `100.0%` at `effort="none"`, `p = 5.343e-08`], former `H-04` via `PB-2` [`0/30` -> `30/30` on assertive text, `p = 1.691e-17`], and former `H-05` via `PB-1` [no significant XML penalty once `[P0|P1|P2|P3]` wording bug was fixed].)*

### H-02: Parameter Description Verbosity Ceiling & Attention Dilution
- **Status**: **[NO EVIDENCE YET]**
- **Context**: `TS-2` showed `cx/gpt-6-luna` fails on unstated custom formats (`geo_coordinates` no-space rule) while inferring standard ISO formats. The upper bound where verbose parameter descriptions bloat context or degrade sibling parameter accuracy remains unmeasured.
- **Test Design**: Vary description length (`10`, `30`, `60`, `120`, `250` tokens per parameter) across multi-argument tools with non-obvious format rules (`N >= 5` iterations).

### H-03: Markdown Syntax Inside JSON Tool Descriptions
- **Status**: **[ACTIVE HYPOTHESIS]**
- **Context**: Developers frequently embed Markdown headers or bullet lists inside tool descriptions rather than plain prose paragraphs (`R-TOOL-03`). Whether Markdown formatting inside JSON tool descriptions improves or degrades tool routing accuracy is unmeasured.
- **Test Design**: Compare plain prose descriptions (at least 3–4 sentences) against bulleted and Markdown-header descriptions across ambiguous adjacent-tool queries (`N >= 5` runs/prompt).

### H-06: Arabic Digits vs Spelled-Out Numbers in Constraint Phrasing
- **Status**: **[NO EVIDENCE YET]**
- **Context**: Untested hypothesis whether Arabic numerals (`3`) yield higher exact-count compliance than spelled-out numbers (`three`) under tokenization differences.
- **Test Design**: Compare digit vs word constraints on length-bounded outputs across `N >= 5` runs per prompt.

### H-07: JSON Schema vs TypeScript Interface Signatures for Tool Definitions
- **Status**: **[NO EVIDENCE YET]**
- **Context**: Untested hypothesis comparing JSON Schema tool declarations against TypeScript interface definitions on deeply nested inputs.
- **Test Design**: Measure argument validity rate and token cost on nested object-array schemas across `N >= 5` runs per prompt.

### H-08: Cross-Model Generalization on Latest Frontier Families
- **Status**: **[NO EVIDENCE YET ON OUR ROUTER]**
- **Context**: Empirical Phase A and Phase B runs (`708` total records) evaluated `cx/gpt-6-luna`. Direct empirical transfer to `Gemini 4 Hydrogen`, `Claude Fable 5.2`, `Claude Opus 5.5`, and `GPT 6.2 Astra` awaits multi-model gateway access.
