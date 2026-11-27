# Unverified Hypotheses, Contested Effects & Unsupported Claims Register

## Executive Summary
Under this skill's evidence policy, items are placed here **only** when:
1. A previously cited numerical threshold or claim was not supported by retrieved primary source text (**Unsupported Claim**);
2. A learned-behavior finding failed to reproduce on `GPT 6 Luna (thinking level: xhigh)` (**Contested / Not Reproduced**); or
3. An engineering question lacks decisive experimental verification (**Open Hypothesis**).

Findings from earlier models whose mechanism or training effect remains supported by primary literature are **not** placed here solely due to model age; they remain active rules in the skill guides with their tested models disclosed.

---

## 1. Unsupported Claims & Numbers Removed From Active Rules

The following specific numbers and thresholds appeared in earlier versions of this repository but were **absent from or contradicted by** the retrieved primary texts verified in [source_checks.md](https://github.com/floydous/agent-system-authoring/blob/main/evidence/source_checks.md):

1. **Fabricated `<= 10` Simultaneous Instruction Cap & `100% -> 21%` Collapse (formerly `R-SYS-01` — now empirically measured in Phase E `PE-1`)**:
   - *Removed claim*: "Cap active concurrent rules to `<= 10`; GPT-4o accuracy collapses from 100% to 21% at 10 rules; o3 holds up to 15–20 rules."
   - *Retrieved primary evidence*: Jaroslawicz et al. ([arXiv:2507.11538](https://arxiv.org/abs/2507.11538)) starts IFScale at 10 keyword-inclusion items and scales to 500 (reporting 68% best accuracy at 500 across 20 models); Harada et al. ([arXiv:2509.21051](https://arxiv.org/abs/2509.21051)) tests up to 10 instructions (ManyIFEval) and 6 style constraints (StyleMBPP), finding consistent degradation with increasing count, with neither `21%` nor a universal `<= 10` threshold in the retrieved abstracts.
   - *Phase E empirical measurement (`PE-1`, `GPT 6 Luna`, `high` effort, `16` prompts × `5` = `80`/arm)*: While the fabricated `<= 10` cliff (`21%`) remains debunked, scaling nested non-keyword behavioral rules from `10 -> 20 -> 50` significantly degraded strict all-rule compliance (`rules_10`: `80/80` [`100.0%`] -> `rules_20`: `39/80` [`48.8%`, `t(15) = -9.94, p = 5.380e-08`] -> `rules_50`: `47/80` [`58.8%`, `t(15) = -7.34, p = 2.436e-06`, `sign = 0+/16-, p = 3.052e-05`]) and multiplied reasoning tokens **`3.5×`** (`256.6 -> 905.3`, `t(15) = 20.19, p = 2.746e-12`) and latency **`1.9×`** (`13.09s -> 25.04s`, `p = 2.829e-10`), while primacy rules `R01–R05` stayed `100%` (`core5_score = 1.000` at `10`/`20`/`50`; `rules_05` scored `46/80` solely from unconstrained `R02` word-count drift before `R06–R08` section structure entered). Upgrades `R-SYS-01` to **T2 + T5** on `GPT 6 Luna`.
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

## 2. Resolved, Ceiling & Conditionally Bounded Comparisons (Phases B–E & `H-08`)

### C-01: Paired Affirmative Substitutes vs Bare Prohibitions (`R-SYS-05`, `PB-4` -> Resolved in `PC-2` & `H08-PC2`)
- **Phase B (`PB-4`, `n = 6` prompts)**: `paired_affirmative` (`30/30`) beat `affirmative_only` (`14/30`, `t(5) = 4.00, p = 0.0103`), while `bare_negative` (`27/30`) vs `affirmative_only` (`t(5) = 2.38, p = 0.0631`) was underpowered at `n = 6`.
- **Phase C Resolution (`PC-2`, `GPT 6 Luna`, `n = 16` prompts × `5` = `80`/arm)**: Both `bare_negative` (`0.988`, `79/80`, `t(15) = 4.06, p = 0.0010`) and `paired_affirmative` (`0.950`, `76/80`, `t(15) = 3.87, p = 0.0015`) decisively beat `affirmative_only` (`0.650`, `52/80`, `38` hits). Comparing `paired_affirmative` against `bare_negative` yielded `delta = -0.038, t(15) = -1.00, p = 0.3332` (sign `0+/1-, p = 1.0000`).
- **Cross-Model Confirmation (`H08-PC2`, `Particle-1`, `16 × 5 = 80`/arm; `NEMO-PC2`, `Nemotron 3.5 Lightning`, `thinking_off`, `16 × 5 = 80`/arm)**: Both additional families confirmed explicit `Do NOT` bans drive lexical exclusion (`Particle-1`: `80/80` vs `51/80`, `p = 0.0013`, with `paired` burning `+91.1` extra rtok [`p = 6.584e-05`]; `Nemotron` `3B`-active non-reasoning SSM: `lexical_clean` `43/80` [`53.8%`] -> `71/80` [`88.8%`, `p = 0.0007`] / `73/80` [`91.2%`, `p = 0.0001`], `paired` vs `bare` `p = 0.6326`, though concrete substitutes helped small-model `length_ok` `58.8% -> 70.0%`).
- **Construct & Compound Caveats**: `affirmative_only` intentionally withheld the 4-word blacklist (testing the folklore practice of replacing negative rules with positive term suggestions `"such as..."`). On `GPT 6 Luna`, all 5 explicit-prohibition failures in `PC-2` (`consecutive-failure`) and 3 in `PB-4` (`operating-system`) were hyphenated compounds matching `\b...\b` (`Particle-1` had `0` compound misses).

### C-02: Prospective Memory Under Heavy Concurrent Distraction (`R-SYS-04`, `PB-3` -> Stress-Tested in `PE-2` & `NEMO-PE2`)
- **Phase B (`PB-3`, ~1,200 words, `xhigh`)**: Ceiling (`30/30` in both arms).
- **Phase E Stress Test (`PE-2`, `GPT 6 Luna`, `high` effort, `~10,917` prompt tokens / `240` decoy-heavy log lines, `16 × 5 = 80`/arm)**: Overall score non-ceiling (`0.885` vs `0.870`, `t(15) = -0.53, p = 0.6062`), yet pure formatting (`no_fence`, `json_ok`, `sentinel_ok`) stayed `80/80` (`100.0%`) in both arms (every miss was counting arithmetic).
- **Phase F Small-SSM Non-Ceiling Formatting Test (`NEMO-PE2`, `Nemotron 3.5 Lightning`, `30B-A3B` Mamba-2 SSM, `thinking_off`, `~13,778` ptok, `16 × 5 = 80`/arm)**: Successfully broke the pure formatting ceiling (`json_ok` and `sentinel_ok`: `82.5%` under `system_only` vs `88.8%` under `sandwich_reminder`, `+6.2 pp`, `t(15) = 0.89, p = 0.3863`; `format_score`: `0.6625` vs `0.6969`, `p = 0.3413`; overall `score`: `0.530` vs `0.558`, `t(15) = 0.98, p = 0.3413`). Because the directional reminder lift was not statistically significant here, `R-SYS-04` remains **T5** (supported by `Mittal, 2026` for concurrent-reasoning / multi-turn sessions).

### C-03: Expert Personas on Powered Hard Benchmarks (`R-SYS-06`, `PB-5` -> Powered Resolution in `PE-3`)
- **Phase B (`PB-5`, `n = 6` prompts, `low`)**: Underpowered null (`0.967` vs `0.900`, `t(5) = -1.00, p = 0.3632`).
- **Phase E Powered Resolution (`PE-3`, `GPT 6 Luna`, `high` effort, `16` competition discrete-math puzzles × `5` = `80`/arm)**: Non-ceiling across `6/16` puzzles (`PE3_01, 04, 05, 06, 12, 13`); `neutral_objective` scored **`72/80` (`0.900`, `TARa@5 = 69%`, `rtok = 359.4`)** vs `expert_persona` **`73/80` (`0.912`, `TARa@5 = 75%`, `rtok = 369.1`)** — **`delta = +0.012, t(15) = 0.22, p = 0.8269; sign = 2+/1- (p = 1.0000)`** (`rtok diff = +9.7, p = 0.7390`). Powered null directly corroborating **T5** literature (`Zheng et al.`, `Basil et al.`).

### C-04: Instruction-Boundary vs Mid-Context Recall Trade-Off (`R-SYS-02` -> Tested at `~2.8k` Tokens in `PE-4`)
- **Phase E Observation (`PE-4`, `GPT 6 Luna`, `high` effort, `18` docs / `~2,814` prompt tokens with embedded prompt-injection override, `16 × 3 × 5 = 240` calls)**: `doc_start`, `doc_middle`, and `doc_end` all hit **`80/80` (`100.0%`, `TARa@5 = 100%`)** on `recall_ok`, `injection_resisted`, and `format_ok` (ceiling at `~2.8k` tokens; `rtok` was modestly lower in `doc_middle` [`26.7`, `diff = -14.0, p = 4.287e-08`] and `doc_end` [`30.4`, `diff = -10.3, p = 1.247e-05`] vs `doc_start` [`40.7`]). Confirms no Lost-in-the-Middle or injection degradation at `~2.8k` tokens under `high` reasoning; near-limit (>50% context window) placement trade-offs remain **T5** (`Liu et al.`, `Veseli et al.`).

---

## 3. Open Research Hypotheses (`[PARTIALLY VALIDATED]` / `[ACTIVE HYPOTHESIS]`)

*(Note: Phases B, C, D, and E resolved `H-01`–`H-07`, `C-01`–`C-04`, and `R-SYS-01` on `GPT 6 Luna` [`3,098` benchmark records], and `H-08` replicated five core suites on a second model family [`Particle-1` / DeepSeek V4.1 Flash lineage, `950` records, `0` errors].)*

### Resolved in Phase D (`GPT 6 Luna`, `N = 5` Runs/Prompt, `1,030` Calls, `0` Errors)

- **`H-02` (Parameter Description Replication & Verbosity Ceiling — Resolved on `GPT 6 Luna` via `PD-1` & `PD-2`, Replicated on `Particle-1` via `H08-PD1`)**:
  - **`PD-1` (`TS-2` `N = 5` replication, `15` prompts × `5` = `75`/arm, `high` effort)**: Confirmed **T2** for both non-standard spacing (`geo_valid`: `2/75` [`2.7%`] vs `75/75` [`100.0%`], `t(14) = 53.57, p = 1.335e-17`, `sign p = 6.104e-05`) and ISO 4217 currency codes (`currency_valid`: `53/75` [`70.7%`] vs `75/75` [`100.0%`], `t(14) = 3.08, p = 0.0082`, `sign p = 0.0078`), while lowering reasoning tokens (`25.4 -> 19.8`, `p = 0.0105`).
  - **`PD-2` (Verbosity curve, `16` prompts × `4` tiers × `5` = `320` calls, `effort = "none"`)**: Across `compact_15t` (`412.1` prompt tok), `moderate_50t` (`521.1`), `verbose_120t` (`1,073.1`), and `bloated_250t` (`2,375.1`, `+1,963` tok = `5.8×` prompt size), `GPT 6 Luna` held **`80/80` (`100.0%`)** strict compliance across all six non-standard format rules at every tier (`delta = 0.000`, latency `+0.06s, p = 0.7941`). Benign verbosity did not induce an accuracy ceiling up to ~`250`–`340` tok/param on `GPT 6 Luna`, but incurred pure **`5.8×` prompt-token bloat** (`sign p = 3.052e-05`) for zero accuracy gain.
- **`H-03` (Markdown Syntax Inside JSON Tool Descriptions — Resolved Null on `GPT 6 Luna` via `PD-3`)**:
  - Across `16` counterbalanced sister-tool routing prompts × `5` = `80`/arm (`effort = "none"`, strictly equalized wording), `plain_prose` (`0.950`, `76/80`, `318.4` prompt tok), `bullet_list` (`0.950`, `76/80`, `delta = 0.000, p = 1.0000`), and `markdown_headers` (`0.975`, `78/80`, `delta = +0.025, t(15) = 1.00, p = 0.3332`, `sign 1+/0-, p = 1.0000`) showed **no statistically significant routing gain**, while `markdown_headers` added **`+43.4` prompt tokens (`+13.6%`, `t(15) = 72.33, p = 1.692e-20`)** and **`+0.38s` mean latency (`p = 0.0149`)**.
- **`H-06` (Arabic Digits vs Spelled-Out Numbers — Refuted Null on `GPT 6 Luna` via `PD-4`; Ceiling Null on `Particle-1` via `H08-PD4`)**:
  - On `GPT 6 Luna (effort = "none")` (`16` prompts × `5` = `80`/arm, non-ceiling `TARa@5 = 0%`), `arabic_digits` (`0.7925`, `strict_all = 2/80` [`2.5%`]) and `spelled_words` (`0.8012`, `strict_all = 6/80` [`7.5%`]) showed **no statistically significant difference** (`delta = +0.009, t(15) = 0.98, p = 0.3431`; `sign 6+/8-, p = 0.7905`). On `Particle-1` (`H08-PD4`, native `~904–917` reasoning tokens), both arms tied at **`80/80` (`100.0%`)** (`rtok diff = +13.4, p = 0.7129`).
- **`H-07` (JSON Schema vs TypeScript Interface Signatures — Resolved for Prompt-Injected Scope Across Both `GPT 6 Luna` & `Particle-1`)**:
  - OpenAI's wire `tools` API requires JSON Schema (`T1`), so `PD-5` & `H08-PD5` tested prompt-injected 4-level nested extraction (`16 × 5 = 80`/arm). On `GPT 6 Luna (none)`, both arms hit **`80/80` (`100.0%`)** while TypeScript cut prompt tokens **`-50.4%`** (`1,024.2 -> 508.2`, `-516.0` tok/call, `sign p = 3.052e-05`). On `Particle-1`, both arms again tied at **`80/80` (`100.0%`)** while TypeScript cut prompt tokens **`-49.2%`** (`1,088.4 -> 553.4`, `-535.0` tok/call, `sign p = 3.052e-05`) with a small reasoning-token bump (`+13.2` rtok, `p = 0.0085`; net `-521.8` total tokens/call).

### H-08: Cross-Model Generalization on Latest Frontier & Diverse Architectures
- **Status**: **[VALIDATED ACROSS 4 MODEL FAMILIES / 3 ARCHITECTURES — CLOSED FRONTIER REPLICATION OPEN]**
- **Second Family (`Particle-1` / DeepSeek V4.1 Flash Lineage, `950` Calls, `0` Errors)**:
  - Replicated `R-TOOL-04` (`H08-PC1`: `0/80 -> 75/80`, `p = 4.787e-15`), `R-SYS-05` (`H08-PC2`: `51/80 -> 80/80`, `p = 0.0013`), `R-TOOL-05` (`H08-PD1`: `5/75 -> 75/75`, `p = 5.203e-13`, `-19.7` rtok), `H-06` ceiling tie (`H08-PD4`), and `H-07` `-49.2%` prompt-token cut at `100%` accuracy (`H08-PD5`).
- **Third Family / Second Architecture (`Nemotron 3.5 Lightning`, `30B-A3B` Mamba-2 SSM Hybrid, `1,190` Calls, `0` Errors)**:
  - Replicated `R-TOOL-11` (`NEMO-PB6`, `thinking_off`: `0/80 -> 69/80`, `p = 3.773e-12`, `sign 16+/0-`), `R-TOOL-04` (`NEMO-PC1`: `3/80 -> 79/80`, `p = 4.769e-17`, `-51.1` rtok), `R-SYS-05` (`NEMO-PC2`, `thinking_off`: `lexical_clean` `53.8% -> 88.8%/91.2%`, `p <= 0.0007`), `R-TOOL-05` (`NEMO-PD1`: `6/75 -> 75/75`, `p = 8.093e-13`, `-45.0%` rtok), non-ceiling `H-06` null (`p = 0.2535`), and non-ceiling `PE-2` formatting (`82.5% -> 88.8%`, `p = 0.3863`, non-significant).
- **Fourth Family / Third Architecture (`Ling 3.2 Flash`, `~560B-A25B` Hybrid-Linear KDA+MLA MoE, `1,510` Calls, `0` Errors)**:
  - **`LING-PE1` (`R-SYS-01`, `thinking_off`, `320` calls)**: Monotonic strict-compliance collapse `5 -> 10 -> 20 -> 50` rules (`97.5% -> 55.0% -> 32.5% -> 16.2%`, **`t(15) = -15.29, p = 1.478e-10`, `sign = 0+/16-`**; `core5` `0.995 -> 0.840`, `p = 4.00e-10`).
  - **`LING-PB6` (`R-TOOL-11`, `thinking_off`, `240` calls)**: `30.0%` / `36.2%` -> **`95.0%` (`76/80`, `t(15) = 5.01, p = 0.0002`)** (`240/240` exact JSON key order, `rtok = 0`).
  - **`LING-PC1` (`R-TOOL-04`), `LING-PC2` (`R-SYS-05`), `LING-PD1` (`R-TOOL-05`)**: `0/80 -> 80/80` (`sign p = 3.052e-05`, `-47.7` rtok), `58/80 -> 80/80` (`p = 0.0001`), and `4/75 -> 75/75` (`p = 2.796e-14`, `-20.8` rtok).
  - **`LING-PD4` (`H-06`, `thinking_off`) & `LING-PD5` (`H-07`, `thinking_off`)**: 4th-family refutation of Arabic-digit advantage (composite `p = 0.3489`; `strict_all` favored `spelled_words` `32.5%` vs `16.2%`, `p = 0.0179`); 3rd-family prompt TypeScript `80/80` parity cutting prompt tokens **`-56.6%` (`-662` tok/call, `p = 3.052e-05`)**.
- **Remaining Open Scope**: Across `6,748` total benchmark records (`3,098` `GPT 6 Luna` + `950` `Particle-1` + `1,190` `Nemotron 3.5 Lightning` + `1,510` `Ling 3.2 Flash`) plus `490` Eval Suite v4 records, direct replication on closed frontier models (`Gemini 4 Hydrogen`, `Claude Fable 5.2`, `Claude Opus 5.5`, `GPT 6.2 Astra`) remains open.
