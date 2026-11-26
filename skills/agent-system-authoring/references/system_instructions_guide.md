# Engineering Guide: System Instructions & Prompt Architecture

## Overview
This guide documents rules for authoring LLM system instructions, tagged by evidence tier (`T2` Measured Empirically across `GPT 6 Luna`, `Particle-1`, and/or `Nemotron 3.5 Lightning`, `T3` Current Vendor Guidance, `T5` Literature — Learned Behavior, `Methodology`, and `Contested`). Current closed frontier models (`Gemini 4 Hydrogen`, `Claude Fable 5.2`, `Claude Opus 5.5`, `GPT 6.2 Astra`) were not evaluated in the cited academic papers and were not available on our router.

---

### R-SYS-01: Instruction Density & Phase Segmentation
- **Evidence Tier**: **T2 (Measured on `GPT 6 Luna`, `PE-1`)** + **T5 (Literature — Learned Behavior)**
- **Primary Citations**:
  - `PE-1` (`16` prompts × `4` densities × `5` = `320` calls) in [stats_recomputed.md](https://github.com/floydous/agent-system-authoring/blob/main/evidence/stats_recomputed.md).
  - Jaroslawicz, Whiting, Shah, & Maamari (Jul 2025), *How Many Instructions Can LLMs Follow at Once?*, [arXiv:2507.11538](https://arxiv.org/abs/2507.11538).
  - Harada, Yamazaki, Taniguchi, Marrese-Taylor, Kojima, Iwasawa, & Matsuo (Sep 2025), *When Instructions Multiply*, EMNLP Findings, [arXiv:2509.21051](https://arxiv.org/abs/2509.21051).
- **Models Tested**: `GPT 6 Luna` (`PE-1`, `high` effort); IFScale: `20` models across `7` providers (incl. o3, GPT-4.1, GPT-4o, Claude Sonnet 4/Opus 4, Gemini 2.5 Pro, Llama 4 Scout); ManyIFEval/StyleMBPP: `10` LLMs.
- **Verified Finding**:
  Simultaneous instruction compliance degrades as constraint count increases. In IFScale (`10` to `500` keyword-inclusion constraints), even the strongest frontier models achieved `68%` accuracy at `500` instructions, displaying threshold/linear/exponential decay alongside primacy bias. In Phase E **`PE-1`** on `GPT 6 Luna (high)` using nested mutually satisfiable non-keyword behavioral rules, `rules_10` hit **`80/80` (`100.0%`)** strict all-rule compliance (`rules_05` scored `46/80` solely from unconstrained `R02` word-count drift before `R06–R08` section structure entered), whereas scaling to `rules_20` and `rules_50` cut `strict_all` to **`39/80` (`48.8%`, `t(15) = -9.94, p = 5.380e-08`)** and **`47/80` (`58.8%`, `t(15) = -7.34, p = 2.436e-06`, `sign = 0+/16-, p = 3.052e-05`)** while multiplying reasoning tokens **`3.5×` (`256.6 -> 905.3`, `p = 2.746e-12`)** and latency **`1.9×` (`13.09s -> 25.04s`, `p = 2.829e-10`)** (`core5_score` primacy rules stayed `100%`). *(No universal `<= 10` cliff is claimed.)*
- **Authoring Directive**:
  - Minimize concurrent active instructions per interaction turn.
  - Segment large multi-step rulebooks into phase-specific prompts or modular on-demand skills rather than monolithic system prompts.

---

### R-SYS-02: Positional Geometry & Context-Placement Trade-Off
- **Evidence Tier**: **T5 (Literature — Learned Behavior)** *(ceiling at `~2.8k` tokens in `PE-4` on `GPT 6 Luna (high)`; near-limit trade-off not re-measured)*
- **Primary Citations**:
  - Liu, Lin, Hewitt, Paranjape, Bevilacqua, Petroni, & Liang (Jul 2023 / TACL 2024), *Lost in the Middle: How Language Models Use Long Contexts*, [arXiv:2307.03172](https://arxiv.org/abs/2307.03172).
  - Veseli, Chibane, Toneva, & Koller (Aug 2025 / COLM 2025), *Positional Biases Shift as Inputs Approach Context Window Limits*, [arXiv:2508.07479](https://arxiv.org/abs/2508.07479).
  - `PE-4` in [empirical_results.md](empirical_results.md).
- **Models Tested**: `GPT 6 Luna` (`PE-4`, `high`, `~2.8k` tokens); MPT-30B, LongChat, Claude-1.3, GPT-3.5-Turbo, LLaMA-2/3, Mistral-7B, Gemma-2-9B.
- **Verified Finding & Design Trade-Off**:
  Retrieval and reasoning accuracy is highest when target information appears near the beginning (primacy) or end (recency) of context and degrades in the middle. Veseli et al. showed this Lost-in-the-Middle pattern is strongest up to `50%` of a model's context window; beyond `50%`, primacy bias weakens while recency distance-based bias dominates. In Phase E **`PE-4`** (`18` docs / `~2.8k` prompt tokens with embedded prompt injection, `16 × 5 = 80`/arm), `GPT 6 Luna (high)` hit **`80/80` (`100.0%`)** across Start, Middle, and End on recall, injection defense, and format (`rtok` modestly lower for `doc_middle` `-14.0, p = 4.287e-08`), showing no short-context penalty; **near-limit (>50% context) trade-offs remain T5**: placing bulky retrieved documents in the middle protects high-priority system invariants (start) and terminal output constraints (end), at the potential cost of weaker mid-context document recall.
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
- **Evidence Tier**: **T5 (Literature — Learned Behavior)** *(tested on 3 model families; `GPT 6 Luna (high/xhigh)` showed zero formatting decay in `PB-3` & `PE-2`)*
- **Primary Citations**:
  - Mittal (Mar 2026 / ACL Anthology), *Did You Forget What I Asked? Prospective Memory Failures in Large Language Models*, [arXiv:2603.23530](https://arxiv.org/abs/2603.23530).
  - `PE-2`, `PB-3`, and `SP-1` in [empirical_results.md](empirical_results.md).
- **Models Tested**: 3 model families (>8,000 prompts); `GPT 6 Luna` (`SP-1`/`PB-3` `xhigh`, `PE-2` `high`).
- **Verified Finding**:
  Across over `8,000` prompts and `3` model families, concurrent reasoning dropped formatting compliance by `2%–21%`, with terminal boundary constraints degrading up to `50%` (and GSM8K task accuracy dropping from `93%` to `27%` in one model). Salience-enhanced framing plus a trailing reminder restored compliance to `90%–100%` in many settings.
- **Empirical Observations (`PB-3`, `PE-2`, `NEMO-PE2`)**:
  On `GPT 6 Luna (high)` at `~10,917` prompt tokens (`PE-2`, `16 × 5`), `system_only` (`0.885`) vs `sandwich_reminder` (`0.870`, `p = 0.6062`) held `80/80` (`100.0%`) pure formatting in both arms (all misses were counting arithmetic). On small non-reasoning **`Nemotron 3.5 Lightning` (`30B-A3B` Mamba-2 SSM, `thinking_off`, `~13,778` ptok, `NEMO-PE2`)**, pure formatting broke below ceiling (`json_ok` and `sentinel_ok`: `82.5%` vs `88.8%`, `+6.2 pp`, `t(15) = 0.89, p = 0.3863`; overall `0.530` vs `0.558`, `p = 0.3413`) with a modest, non-significant reminder shift. Trailing reminders remain recommended (**T5**) for standard models under heavy reasoning load or long multi-turn sessions.
- **Authoring Directive**:
  - Under demanding reasoning tasks on standard models or long multi-step sessions, append a concise trailing reminder summarizing terminal output invariants adjacent to the generation boundary.

---

### R-SYS-05: Explicit Prohibitions Over Affirmative-Only Phrasing
- **Evidence Tier**: **T2 (Measured across 3 model families & 2 architectures: `GPT 6 Luna` `PC-2`, `Particle-1` `H08-PC2`, `Nemotron 3.5 Lightning` `NEMO-PC2`)**
- **Primary Citations**:
  - `PC-2`, `H08-PC2`, `NEMO-PC2` (`16` prompts × `5` repeats) & `PB-4` ([stats_recomputed.md](https://github.com/floydous/agent-system-authoring/blob/main/evidence/stats_recomputed.md)) & `SP-2` in [empirical_results.md](empirical_results.md).
  - Jang, Ye, & Seo (Sep 2022), *Can Large Language Models Truly Understand Prompts? A Case Study with Negated Prompts*, [arXiv:2209.12711](https://arxiv.org/abs/2209.12711) *(inverse scaling observed on `OPT 125M–175B`, `GPT-3`, `InstructGPT`)*.
- **Models Tested**: `GPT 6 Luna` (`PC-2` `high`, `PB-4`/`SP-2` `xhigh`); `Particle-1` / DeepSeek V4.1 Flash (`H08-PC2`); `Nemotron 3.5 Lightning` `30B-A3B` Mamba-2 SSM (`NEMO-PC2`, `thinking_off`); `OPT (125M–175B)`, `GPT-3`, `InstructGPT` (Jang et al.).
- **Verified `T2` Evidence & Scope Boundaries (Prompt-Level Inference)**:
  Unlike pre-2023 models in Jang et al., all three tested modern families reliably followed explicit lexical exclusions:
  - **`GPT 6 Luna` (`PC-2`, `16 × 5`)**: `bare_negative` **`0.988` (`79/80`)** and `paired_affirmative` **`0.950` (`76/80`)** beat `affirmative_only` (**`0.650`**, `52/80`, `38` hits): **`t(15) = 4.06, p = 0.0010`** and **`t(15) = 3.87, p = 0.0015`**.
  - **`Particle-1` / DeepSeek V4.1 Flash (`H08-PC2`, `16 × 5`)**: `bare_negative` (**`80/80`**) and `paired_affirmative` (**`80/80`**) beat `affirmative_only` (**`51/80`**, `63.8%`, `31` hits): **`t(15) = 3.95, p = 0.0013`**, while `paired_affirmative` burned **`+91.1` extra reasoning tokens** (`p = 6.584e-05`).
  - **`Nemotron 3.5 Lightning` (`NEMO-PC2`, `30B-A3B` Mamba-2 SSM, `thinking_off`, `16 × 5`)**: On pure `lexical_clean`, `bare_negative` (**`71/80`, `88.8%`**, `t(15) = 4.23, p = 0.0007`) and `paired_affirmative` (**`73/80`, `91.2%`**, `t(15) = 5.16, p = 0.0001`) decisively beat `affirmative_only` (**`43/80`, `53.8%`**, `45` hits; `paired` vs `bare` lexical `p = 0.6326`). On small non-reasoning models, concrete substitutes also aided prose length (`length_ok` `58.8% -> 70.0%`, combined `0.613` vs `0.412`, `p = 0.0035`).
  - **Design & Construct Boundary (`PC-2` / `H08-PC2` / `NEMO-PC2`)**: `affirmative_only` suggested preferred terms (`"such as..."`) without disclosing the 4-word blacklist. Across all 3 families, (a) omitting named bans fails often (`53.8%–65.0%`), (b) explicit `Do NOT` prohibitions work reliably (`88.8%–100.0%`), and (c) substitutes add zero lexical-exclusion gain (`p >= 0.33`), though they can support fluency on small (`3B`-active) non-reasoning models.
  - **Hyphenated-Compound Edge Case**: Every lexical failure under explicit prohibitions on `GPT 6 Luna` (`5` hits in `PC-2`: `consecutive-failure`; `3` hits in `PB-4`: `operating-system`) was a **hyphenated compound** matching `\b<word>\b` (`Particle-1` had `0` misses).
- **Authoring Directive**:
  - Whenever specific words or tokens must be omitted, state an **explicit `Do NOT use ...` exclusion** rather than hoping affirmative `"use X instead"` framing suppresses them implicitly. Specify explicitly whether inflected, plural, or hyphenated compound forms (e.g., `consecutive-failure`) are also excluded. Pair prohibitions with concrete substitutes when targeting editorial tone or small non-reasoning models.

---

### R-SYS-06: Neutral Objectives Over Expert Personas
- **Evidence Tier**: **T5 (Literature — Learned Behavior)** *(confirmed powered null in non-ceiling `PE-3` and `PB-5` on `GPT 6 Luna`)*
- **Primary Citations**:
  - Zheng, Pei, Logeswaran, Lee, & Jurgens (Nov 2023), *When "A Helpful Assistant" Is Not Really Helpful*, [arXiv:2311.10054](https://arxiv.org/abs/2311.10054).
  - Basil, Shapiro, Shapiro, Mollick, Mollick, & Meincke (Dec 2025), *Prompting Science Report 4: Playing Pretend: Expert Personas Don't Improve Factual Accuracy*, [arXiv:2512.05858](https://arxiv.org/abs/2512.05858).
  - `PE-3`, `PB-5` & `SP-3` in [empirical_results.md](empirical_results.md).
- **Models Tested**: `4` LLM families (`162` roles, `2,410` factual questions, Zheng et al.); `6` models on GPQA Diamond & MMLU-Pro (Basil et al.); `GPT 6 Luna` (`PE-3` `high`, `PB-5` `low`, `SP-3` `xhigh`).
- **Verified Finding**:
  Adding personas to system prompts does not improve factual question accuracy over a no-persona baseline (Zheng et al.).
- **`GPT 6 Luna` Observations (`PE-3` powered & `PB-5`)**:
  In powered **`PE-3`** (`16` competition discrete-math puzzles × `5` = `80`/arm, `high` effort, non-ceiling across `6/16` puzzles), `neutral_objective` scored **`72/80` (`90.0%`, `TARa@5 = 69%`)** vs `expert_persona` **`73/80` (`91.2%`, `TARa@5 = 75%`)** — prompt-level **`delta = +0.012, t(15) = 0.22, p = 0.8269; sign = 2+/1- (p = 1.0000)`** (`rtok diff = +9.7, p = 0.7390`). Consistent with `PB-5` (`low` effort, `n = 6` × `5`: `0.967` vs `0.900`, `t(5) = -1.00, p = 0.3632`) and **T5** literature (`Zheng et al.`, `Basil et al.`).
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
