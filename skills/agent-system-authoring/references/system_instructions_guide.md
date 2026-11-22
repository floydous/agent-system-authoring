# Engineering Guide: System Instructions & Prompt Architecture

## Overview
This guide documents rules for authoring LLM system instructions, tagged by evidence tier (`T2` Measured on `GPT 6 Luna`, `T3` Current Vendor Guidance, `T5` Literature — Learned Behavior, `Methodology`, and `Contested`). Current frontier models (`Gemini 4 Hydrogen`, `Claude Fable 5.2`, `Claude Opus 5.5`, `GPT 6.2 Astra`) were not evaluated in the cited academic papers and were not available on our router.

---

### R-SYS-01: Instruction Density & Phase Segmentation
- **Evidence Tier**: **T5 (Literature — Learned Behavior)** *(tested on earlier models; transfer to current models not re-measured)*
- **Primary Citations**:
  - Jaroslawicz, Whiting, Shah, & Maamari (Jul 2025), *How Many Instructions Can LLMs Follow at Once?*, [arXiv:2507.11538](https://arxiv.org/abs/2507.11538).
  - Harada, Yamazaki, Taniguchi, Marrese-Taylor, Kojima, Iwasawa, & Matsuo (Sep 2025), *When Instructions Multiply*, EMNLP Findings, [arXiv:2509.21051](https://arxiv.org/abs/2509.21051).
- **Models Tested**: IFScale: `20` models across `7` providers (incl. o3, GPT-4.1, GPT-4o, Claude Sonnet 4/Opus 4, Gemini 2.5 Pro, Llama 4 Scout). ManyIFEval/StyleMBPP: `10` LLMs.
- **Verified Finding**:
  Simultaneous instruction compliance degrades as constraint count increases. In IFScale (`10` to `500` keyword-inclusion constraints), even the strongest frontier models achieved `68%` accuracy at `500` instructions, displaying three decay patterns (threshold, linear, and exponential) alongside primacy bias toward earlier instructions. ManyIFEval (`<= 10` text constraints) and StyleMBPP (`<= 6` code constraints) likewise showed consistent accuracy drops as instructions multiplied. *(Note: no universal `<= 10` rule cap was established in these papers.)*
- **Authoring Directive**:
  - Minimize concurrent active instructions per interaction turn.
  - Segment large multi-step rulebooks into phase-specific prompts or modular on-demand skills rather than monolithic system prompts.

---

### R-SYS-02: Positional Geometry & Context-Placement Trade-Off
- **Evidence Tier**: **T5 (Literature — Learned Behavior)** *(trade-off design untested here; transfer to current models not re-measured)*
- **Primary Citations**:
  - Liu, Lin, Hewitt, Paranjape, Bevilacqua, Petroni, & Liang (Jul 2023 / TACL 2024), *Lost in the Middle: How Language Models Use Long Contexts*, [arXiv:2307.03172](https://arxiv.org/abs/2307.03172).
  - Veseli, Chibane, Toneva, & Koller (Aug 2025 / COLM 2025), *Positional Biases Shift as Inputs Approach Context Window Limits*, [arXiv:2508.07479](https://arxiv.org/abs/2508.07479).
- **Models Tested**: MPT-30B, LongChat, Claude-1.3, GPT-3.5-Turbo, LLaMA-2/3, Mistral-7B, Gemma-2-9B.
- **Verified Finding & Design Trade-Off**:
  Retrieval and reasoning accuracy is highest when target information appears near the beginning (primacy) or end (recency) of context and degrades in the middle. Veseli et al. showed this Lost-in-the-Middle pattern is strongest up to `50%` of a model's context window; beyond `50%`, primacy bias weakens while recency distance-based bias dominates. **Explicit trade-off (untested here)**: placing bulky retrieved documents in the middle protects high-priority system invariants (start) and terminal output constraints (end), at the potential cost of weaker mid-context document recall—so keep retrieved excerpts compact and filtered when middle-document fidelity matters.
- **Authoring Directive**:
  - Place immutable system invariants at the start of context (System/Developer message).
  - Place critical output schema constraints and terminal action directives near the end of context.
  - Keep retrieved documents compact; when balancing rule integrity against reference payloads, place retrieved data in the middle as a deliberate trade-off protecting boundary rules.

---

### R-SYS-03: Instruction Hierarchy & Untrusted Data Separation
- **Evidence Tier**: **T3 (Current Vendor Guidance — not measured by us)**
- **Primary Citations**:
  - OpenAI Model Spec (`2025-02-12`), [https://model-spec.openai.com/](https://model-spec.openai.com/).
  - Wallace, Xiao, Leike, Weng, Heidecke, & Beutel (Apr 2024), *The Instruction Hierarchy: Training LLMs to Prioritize Privileged Instructions*, [arXiv:2404.13208](https://arxiv.org/abs/2404.13208) *(tested on GPT-3.5)*.
- **Verified Guidance**:
  The OpenAI Model Spec defines a strict authority chain (`Platform > Developer > User > Tool/Untrusted Data`): *"Ignore untrusted data by default, all other content (e.g., untrusted_text, quoted text, images, or tool outputs) should be ignored unless an applicable higher-level instruction explicitly delegates authority to it."* Wallace et al. showed on GPT-3.5 that instruction-hierarchy training drastically increases robustness against unseen prompt-injection attacks with minimal standard capability loss.
- **Authoring Directive**:
  - Place non-negotiable behavioral guardrails in Developer/System messages rather than User messages.
  - Isolate retrieved text, web pages, and tool outputs in clearly labeled data blocks and state explicitly that embedded imperatives inside retrieved data carry zero authority.

---

### R-SYS-04: Prospective Memory & Trailing Reminders
- **Evidence Tier**: **T5 (Literature — Learned Behavior)** *(tested on 3 model families; `GPT 6 Luna (xhigh)` hit ceiling in `SP-1` and `PB-3`)*
- **Primary Citations**:
  - Mittal (Mar 2026 / ACL Anthology), *Did You Forget What I Asked? Prospective Memory Failures in Large Language Models*, [arXiv:2603.23530](https://arxiv.org/abs/2603.23530).
  - `SP-1` and `PB-3` in [empirical_results.md](empirical_results.md).
- **Models Tested**: 3 model families (>8,000 prompts); `GPT 6 Luna (thinking level: xhigh)` (`SP-1`, `PB-3`).
- **Verified Finding**:
  Across over `8,000` prompts and `3` model families, concurrent reasoning dropped formatting compliance by `2%–21%`, with terminal boundary constraints degrading up to `50%` (and GSM8K task accuracy dropping from `93%` to `27%` in one model). Salience-enhanced framing plus a trailing reminder restored compliance to `90%–100%` in many settings.
- **`GPT 6 Luna` Observation (`SP-1` & `PB-3`)**:
  Ceiling / uninformative: even under ~1,200 words of noisy log distractors and strict JSON + sentinel constraints (`PB-3`, `n = 6` prompts × `5` repeats = `30`/arm), both `system_only` and `sandwich_reminder` scored `30/30` (`1.000`, prompt-level `delta = 0.000`, sign `0+/0-, p = 1.0000`). High-effort reasoning maintains prospective memory across moderate noisy inputs; trailing reminders remain recommended for standard or long-session models.
- **Authoring Directive**:
  - Under demanding reasoning tasks on standard models or long multi-step sessions, append a concise trailing reminder summarizing terminal output invariants adjacent to the generation boundary.

---

### R-SYS-05: Explicit Prohibitions Over Affirmative-Only Phrasing
- **Evidence Tier**: **T2 (Measured on `GPT 6 Luna`, `PC-2` & `PB-4`)**
- **Primary Citations**:
  - `PC-2` (`16` prompts × `5` repeats) & `PB-4` ([stats_recomputed.md](https://github.com/floydous/agent-system-authoring/blob/main/evidence/stats_recomputed.md)) & `SP-2` in [empirical_results.md](empirical_results.md).
  - Jang, Ye, & Seo (Sep 2022), *Can Large Language Models Truly Understand Prompts? A Case Study with Negated Prompts*, [arXiv:2209.12711](https://arxiv.org/abs/2209.12711) *(inverse scaling observed on `OPT 125M–175B`, `GPT-3`, `InstructGPT`)*.
- **Models Tested**: `GPT 6 Luna` (`PC-2` `high`, `PB-4`/`SP-2` `xhigh`); `OPT (125M–175B)`, `GPT-3`, `InstructGPT` (Jang et al.).
- **Verified `T2` Evidence (Prompt-Level Inference)**:
  Unlike pre-2023 models in Jang et al., `GPT 6 Luna` reliably followed explicit lexical exclusions:
  - In `PB-4` (`n = 6` prompts × `5` repeats), `affirmative_only` dropped to `14/30` (`46.7%`) vs `paired_affirmative` `30/30` (prompt-level paired `t(5) = 4.00, p = 0.0103`; sign `5+/0-, p = 0.0625`) and `bare_negative` `27/30` (`t(5) = 2.38, p = 0.0631`, underpowered at `n = 6`).
  - In higher-powered `PC-2` (`n = 16` prompts across 4 domains × `5` repeats = `80`/arm), `bare_negative` achieved **`0.988` (`79/80` clean, `1` forbidden hit, `TARa@5 = 94%`)** and `paired_affirmative` achieved **`0.950` (`76/80` clean, `4` hits, `TARa@5 = 94%`)**, both decisively outperforming `affirmative_only` (**`0.650`**, `52/80` clean, `38` hits, `TARa@5 = 44%`): prompt-level **`t(15) = 4.06, p = 0.0010`** (sign `11+/0-, p = 0.0010`) and **`t(15) = 3.87, p = 0.0015`** (`p = 0.0010`), respectively.
  - Adding positive substitutes (`paired_affirmative`) over `bare_negative` alone showed no accuracy benefit in `PC-2` (`delta = -0.038, t(15) = -1.00, p = 0.3332`; `247.8` vs `219.6` mean reasoning tokens) and is therefore optional for style/tone rather than a compliance requirement.
- **Authoring Directive**:
  - Whenever specific tokens, words, or formats must be omitted, state the **explicit prohibition** (`"Do NOT use ..."`) rather than relying on affirmative-only phrasing alone. Optionally pair prohibitions with substitutes (`"Use X; do NOT use Y"`) when editorial guidance helps clarity.

---

### R-SYS-06: Neutral Objectives Over Expert Personas
- **Evidence Tier**: **T5 (Literature — Learned Behavior)** *(confirmed neutral/non-beneficial in non-ceiling `PB-5` on `GPT 6 Luna`)*
- **Primary Citations**:
  - Zheng, Pei, Logeswaran, Lee, & Jurgens (Nov 2023), *When "A Helpful Assistant" Is Not Really Helpful*, [arXiv:2311.10054](https://arxiv.org/abs/2311.10054).
  - Basil, Shapiro, Shapiro, Mollick, Mollick, & Meincke (Dec 2025), *Prompting Science Report 4: Playing Pretend: Expert Personas Don't Improve Factual Accuracy*, [arXiv:2512.05858](https://arxiv.org/abs/2512.05858).
  - `PB-5` & `SP-3` in [empirical_results.md](empirical_results.md).
- **Models Tested**: `4` LLM families (`162` roles, `2,410` factual questions, Zheng et al.); `6` models on GPQA Diamond & MMLU-Pro (Basil et al.); `GPT 6 Luna` (`SP-3` `xhigh`, `PB-5` `low`).
- **Verified Finding**:
  Adding personas to system prompts does not improve factual question accuracy over a no-persona baseline (Zheng et al.).
- **`GPT 6 Luna` Observation (`PB-5`, `reasoning_effort = "low"`, `n = 6` prompts × `5` repeats = `30`/arm)**:
  On non-ceiling combinatorics and number-theory puzzles, `neutral_objective` scored **`29/30` (`96.7%`, `TARa@5 = 83%`)** vs `expert_persona` **`27/30` (`90.0%`, `TARa@5 = 50%`)** (prompt-level paired `t(5) = -1.00, p = 0.3632`; sign `0+/1-, p = 1.0000`, reasoning token diff `+1.9`, `p = 0.9211`). Expert personas showed no detectable gain and lower prompt-level stability, though `n = 6` prompts is underpowered to independently prove zero difference—this rule rests primarily on **T5** literature (`Zheng et al.`, `Basil et al.`).
- **Authoring Directive**:
  - Omit honorary expert personas (`"You are a Fields Medalist / Turing Laureate..."`) when seeking factual, mathematical, or coding accuracy; specify concrete objectives and acceptance criteria instead. Use role framing only when voice, tone, or target audience style matters.

---

### R-SYS-07: Native Reasoning Models & Chain-of-Thought Prompts
- **Evidence Tier**: **T3 (Current Vendor Guidance — not measured by us)** *(supported by T5 findings on 15 models)*
- **Primary Citations**:
  - OpenAI Reasoning Best Practices, [https://developers.openai.com/api/docs/guides/reasoning-best-practices](https://developers.openai.com/api/docs/guides/reasoning-best-practices) (retrieved 2026-11-22).
  - Li, Yu, Zhang, Chen, Zhang, Zhuang, Sadagopan, & Beniwal (May 2025), *When Thinking Fails: The Pitfalls of Reasoning for Instruction-Following in LLMs*, [arXiv:2505.11423](https://arxiv.org/abs/2505.11423).
- **Models Tested**: OpenAI reasoning models (vendor docs); `15` models across `IFEval` and `ComplexBench` (Li et al.).
- **Verified Guidance**:
  OpenAI states: *"Avoid chain-of-thought prompts: Since these models perform reasoning internally, prompting them to 'think step by step' or 'explain your reasoning' is unnecessary"* and notes such phrasing *"may not enhance performance (and can sometimes hinder it)."* Independently, Li et al. observed consistent instruction-following degradation across `15` models on `IFEval` and `ComplexBench` when CoT prompting diverted attention from constraints.
- **Authoring Directive**:
  - For reasoning models, omit explicit `"think step by step"` instructions; provide clear goals and constraints instead.

---

### R-SYS-08: Structural Delimiters (Flat Markdown & XML Containers)
- **Evidence Tier**: **T3 (Current Vendor Guidance — not measured by us on Claude)** + **T5** (`He et al.`, `Liu & Chu`)
- **Primary Citations**:
  - Anthropic Prompting Best Practices (retrieved 2026-11-22), [platform.claude.com](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices).
  - OpenAI Prompt Engineering Guide (retrieved 2026-11-22), [developers.openai.com](https://developers.openai.com/api/docs/guides/prompt-engineering).
  - He, Rungta, Koleczek, Sekhon, Wang, & Hasan (Nov 2024), *Does Prompt Formatting Have Any Impact on LLM Performance?*, [arXiv:2411.10541](https://arxiv.org/abs/2411.10541) *(Plain Text, Markdown, JSON, YAML on GPT-3.5-turbo/GPT-4, up to 40% variation on code translation; XML NOT tested)*.
  - Liu & Chu (Apr 2026), *Understanding the Prompt Sensitivity*, [arXiv:2604.18389](https://arxiv.org/abs/2604.18389).
  - `PB-1` & `SP-4` in [stats_recomputed.md](https://github.com/floydous/agent-system-authoring/blob/main/evidence/stats_recomputed.md).
- **Models Tested**: Anthropic docs cover `Claude Fable 5.2` / `Claude Opus 5.5` *(not measured by us)*; `GPT-3.5-turbo` & `GPT-4` (He et al.); `GPT 6 Luna (xhigh)` (`PB-1`).
- **`GPT 6 Luna` Phase B Finding (`PB-1`, `n = 6` prompts × `5` repeats, identical wording)**:
  Phase A's apparent XML penalty in `SP-4` was caused by a `[P0|P1|P2|P3]` bracket wording bug (`XML_TEXT` omitted `"without brackets"` and scored `4/12` on `c5_severity` vs `12/12` in `RAW_TEXT`). With wording fixed and equalized in `PB-1`, **`flat_markdown` (`0.972`), `flat_xml` (`0.983`, paired `t(5) = 1.00, p = 0.3632`), and `nested_xml` (`0.994`, paired `t(5) = 2.00, p = 0.1019`) showed no statistically significant XML disadvantage** (`c5_severity = 30/30` in all three arms).
- **Vendor Guidance (`T3` — not measured by us)**:
  Anthropic recommends XML tags (`<instructions>`, `<context>`, `<input>`) for Claude, nesting tags when content has natural hierarchy (`<documents><document index="n">`); OpenAI recommends combining Markdown headers and XML tags to mark logical prompt boundaries.
- **Authoring Directive**:
  - Use clean, unambiguous structural delimiters (flat Markdown `###` headers by default in [system_prompt_template.md](../assets/templates/system_prompt_template.md), or XML tags for Claude prompts), keeping wording identical and avoiding literal meta-syntax placeholders like `[A|B|C]` when a single concrete value is required.

---

### R-SYS-09: Few-Shot Discipline & Instruction Alignment
- **Evidence Tier**: **T5 (Literature — Learned Behavior)** *(tested on earlier models; transfer not re-measured)* + **T3 (OpenAI Reasoning Guide)**
- **Primary Citations**:
  - Tang, Tuncel, Koerner, & Runkler (Sep 2025), *The Few-shot Dilemma: Over-prompting Large Language Models*, [arXiv:2509.13196](https://arxiv.org/abs/2509.13196).
  - Camassa & Shiller (2026-05-19), *Do as I Say, Not as I Do: Instruction-Induction Conflict in LLMs*, [arXiv:2605.20382](https://arxiv.org/abs/2605.20382).
  - OpenAI Reasoning Best Practices (retrieved 2026-11-22), [developers.openai.com](https://developers.openai.com/api/docs/guides/reasoning-best-practices).
- **Models Tested**: GPT-4o, GPT-3.5-turbo, DeepSeek-V3, Gemma-3, LLaMA-3.1/3.2, Mistral (Tang et al.); `13` models across `16` instructions (Camassa & Shiller).
- **Verified Finding**:
  Adding excessive domain examples degrades accuracy in some LLMs (Tang et al.). When hardcoded examples conflict with written rules, instruction-following drops sharply (`27%` fixed-output / `43%` task-based grand mean across 13 models, Camassa & Shiller). OpenAI advises: *"Try zero shot first, then few shot if needed... ensure that the examples align very closely with your prompt instructions."*
- **Authoring Directive**:
  - Start zero-shot on reasoning models; add only minimal, clean examples when output format or edge-case disambiguation requires them, ensuring zero rule contradictions.

---

### R-SYS-10: Repeated Evaluation & Distributional Reporting
- **Evidence Tier**: **Methodology** *(grounded in T4 hardware/kernel non-determinism)*
- **Primary Citations**:
  - Yuan, Li, Ding, et al. (Jun 2025), *Understanding and Mitigating Numerical Sources of Nondeterminism in LLM Inference*, [arXiv:2506.09501](https://arxiv.org/abs/2506.09501).
  - Atil, Aykent, Chittams, et al. (Aug 2024), *Non-Determinism of "Deterministic" LLM Settings*, Eval4NLP, [arXiv:2408.04667](https://arxiv.org/abs/2408.04667).
- **Models Tested**: `DeepSeek-R1-Distill-Qwen-7B` (Yuan et al.); `5` LLMs over `8` tasks × `10` runs (Atil et al.).
- **Verified Principle**:
  Even under greedy decoding (`temperature = 0`), FP16/BF16 non-associativity and dynamic server batching create accuracy variance up to `9%` (`9,000` token swings, Yuan et al.) and up to `15%` accuracy variation / `70%` best-worst gaps across repeated runs (Atil et al., defining `TARr@N` and `TARa@N`).
- **Evaluation Directive**:
  - Run prompt and skill evaluations over repeated iterations (`N >= 5` runs per prompt across adequate prompt counts, ideally `n >= 15`), aggregate repeated runs into prompt means before applying paired *t* or exact sign tests (never pool repeats as independent samples), and report dispersion alongside `TARa@N`.
  - **Phase B & C Confirmation**: Multi-run `GPT 6 Luna` repeats (`N = 5`) recorded prompt-level non-determinism (`TARa@5 = 17%` in `PB-1 flat_markdown` and `PB-4 affirmative_only`; `44%` in `PC-2 affirmative_only`; `50%` in `PB-5 expert_persona`), confirming single-run evaluation is insufficient even at fixed settings. *(Note: Phase A `raw/` remains `N = 1` per prompt for historical traceability.)*
