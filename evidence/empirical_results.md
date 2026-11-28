# Empirical Results: `8,028` Benchmark Calls Across 4 Model Families

## 1. Executive Summary
This report documents all **`8,028` live benchmark completions** (`7,800` `N = 5` calls across Phases B–G & `H-08` + `228` `N = 1` Phase A screening calls) recorded across **four gateway model families** (`4,378` on `GPT 6 Luna` + `950` on `Particle-1` + `1,190` on `Nemotron 3.5 Lightning` + `1,510` on `Ling 3.2 Flash`; **`0` gateway errors across all `7,800` Phase B–G & `H-08` calls**; gateway slugs and model-card provenance documented in [source_checks.md](source_checks.md)), adhering strictly to **prompt-level unit-of-analysis hygiene** (zero pooled-repeat Fisher p-values; nominal `p`-values unadjusted across `80+` contrasts):
- **Phase A (`228` records, `N = 1` run/prompt, `GPT 6 Luna`)**: Initial exploration (`SP-1`–`SP-4`, `TS-1`–`TS-3`) under [`harnesses/experiment_harness.py`](harnesses/experiment_harness.py).
- **Phase B (`480` records, `N = 5` runs/prompt × `6` prompts/suite, `0` errors, `GPT 6 Luna`)**: Deconfounded suites (`PB-1`–`PB-6`) under [`harnesses/phase_b_harness.py`](harnesses/phase_b_harness.py).
- **Phase C (`480` records, `N = 5` runs/prompt × `16` prompts/suite, `high` effort, `0` errors, `GPT 6 Luna`)**: Powered counterbalanced tool-gaming (`PC-1`) and 4-domain lexical-prohibition (`PC-2`) replications under [`harnesses/phase_c_harness.py`](harnesses/phase_c_harness.py).
- **Phase D (`1,030` records, `N = 5` runs/prompt × `15–16` prompts/suite, `0` errors, `GPT 6 Luna`)**: Open hypotheses `H-02` (`PD-1`, `PD-2`), `H-03` (`PD-3`), `H-06` (`PD-4`), and prompt-injected `H-07` (`PD-5`) under [`harnesses/phase_d_harness.py`](harnesses/phase_d_harness.py).
- **Phase E (`880` records, `N = 5` runs/prompt × `16` prompts/suite, `high` effort, `0` errors, `GPT 6 Luna`)**: Rule density (`PE-1` / `R-SYS-01`), `~11k`-token log distraction (`PE-2` / `C-02`), powered discrete math (`PE-3` / `C-03`), and Start/Middle/End needle + injection (`PE-4` / `C-04`) under [`harnesses/phase_e_harness.py`](harnesses/phase_e_harness.py).
- **`H-08` Cross-Model Replication (`950` records, `N = 5`, `0` errors, `Particle-1`)**: Exact replication of `PC-1`, `PC-2`, `PD-1`, `PD-4`, and `PD-5` under [`harnesses/phase_h08_harness.py`](harnesses/phase_h08_harness.py).
- **Phase F Cross-Architecture Replication (`2,700` records, `N = 5`, `0` errors)**: `1,190` calls on `Nemotron 3.5 Lightning` and **`1,510` calls on `Ling 3.2 Flash`** under [`harnesses/phase_f_harness.py`](harnesses/phase_f_harness.py).
- **Phase G Stress & Untouched-Rule Suites (`1,280` records, `N = 5` runs/prompt × `16` prompts/suite, `0` errors, `GPT 6 Luna`)**: Active tool catalog scaling `5/20/50/100` (`LUNA-PG1` / `R-TOOL-08`), CoT on native reasoning (`LUNA-PG2` / `R-SYS-07`), zero-shot vs aligned/conflicting 3-shot (`LUNA-PG3` / `R-SYS-09`), `16`-turn subtle-trigger prospective memory (`LUNA-PG4` / `C-02`), and `~67.3k`-token `>50%` window placement + refresh (`LUNA-PG5` / `C-04` & `R-TOOL-12`) under [`harnesses/phase_g_harness.py`](harnesses/phase_g_harness.py).
- **Pi Real-Agent Multi-Turn Evals (`85` live `pi v1.6.0` coding-agent sessions, `0` errors, `85/85` `iso=True`, `GPT 6 Luna` `high`)**: End-to-end multi-file repo repair graded by deterministic workspace validators (`P = 1` repo fixture per task, `N = 5` runs, zero LLM judges) under [`harnesses/pi_agent_eval.py`](harnesses/pi_agent_eval.py).

All statistics below match [`stats_recomputed.md`](stats_recomputed.md) (generated offline by `python -B evidence/recompute_stats.py`). **Scope Boundary**: Four distinct gateway model families (`GPT 6 Luna`, `Particle-1`, `Nemotron 3.5 Lightning`, `Ling 3.2 Flash`) were tested; closed frontier models (`Gemini 4 Hydrogen`, `Claude Fable 5.2`, `Claude Opus 5.5`, `GPT 6.2 Astra`) remain unmeasured here.

---

## 2. Phase G Summary Table (`N = 5`, `GPT 6 Luna`: `R-TOOL-08`, `R-SYS-07`, `R-SYS-09`, `C-02` & `C-04`)

| Suite | Condition | N | Prompts | Mean Score (Prompt SD) | Raw Runs / `strict_all` | `TARa@5` | Prompt-Level Paired *t* (`df=15`) | Prompt-Level Exact Sign Test | Mean RTok / PTok | Result Summary |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- | :--- | :---: | :--- |
| **LUNA-PG1** (`none`) | `tools_05` | 80 | 16 | `1.000` (`0.000`) | `80/80` (`100.0%`) | `100%` | Baseline | Baseline | `0.0` / `374.8` | Exact tool + args (`lat=2.27s`) |
| **LUNA-PG1** (`none`) | `tools_20` | 80 | 16 | `1.000` (`0.000`) | `80/80` (`100.0%`) | `100%` | `0.000` (`ptok +654.4, p=2.3e-19`) | `0+/0-` (`ptok 16+/0-`) | `0.0` / `1,029.2` | `2.7×` ptok, zero accuracy drop |
| **LUNA-PG1** (`none`) | `tools_50` | 80 | 16 | `1.000` (`0.000`) | `80/80` (`100.0%`) | `100%` | `0.000` (`ptok +2,070.3, p=2.2e-21`) | `0+/0-` (`ptok 16+/0-`) | `0.0` / `2,445.1` | `6.5×` ptok, zero accuracy drop |
| **LUNA-PG1** (`none`) | `tools_100` | 80 | 16 | `1.000` (`0.000`) | `80/80` (`100.0%`) | `100%` | `0.000` (**`ptok +4,423.1, p=1.8e-33`**) | `0+/0-` (**`ptok 16+/0-`**) | `0.0` / **`4,797.9`** | **`12.8×` ptok tax (`R-TOOL-08` T4)**; `lat +0.23s` |
| **LUNA-PG2** (`high`) | `direct_goal` | 80 | 16 | `0.904` (`0.111`) | `strict=57/80` (`71.2%`) | `31%` | Baseline | Baseline | `517.4` / `290.6` | Math `36/40`, constrained `21/40` |
| **LUNA-PG2** (`high`) | `explicit_cot_hidden` | 80 | 16 | `0.931` (`0.074`) | `strict=60/80` (`75.0%`) | `38%` | `+0.027, t(15)=0.87, p=0.3992` | `4+/2- (p=0.6875)` | `531.8` / `327.6` | Non-ceiling null (`strict p=0.3332`) |
| **LUNA-PG2** (`high`) | `explicit_cot_visible` | 80 | 16 | `0.894` (`0.131`) | `strict=52/80` (`65.0%`) | `38%` | `-0.010, t(15)=-0.24, p=0.8109` | `5+/6- (p=1.0000)` | `517.0` / `338.6` | Null (`con` `16/40`; `R-SYS-07` **T3**) |
| **LUNA-PG3** (`high`) | `zero_shot` | 80 | 16 | `1.000` (`0.000`) | `80/80` (`100.0%`) | `100%` | Baseline (`mimic=0.000`) | Baseline | `37.1` / `201.4` | Cleanest & lowest total tokens |
| **LUNA-PG3** (`high`) | `aligned_3shot` | 80 | 16 | `0.998` (`0.010`) | `strict=79/80` (`98.8%`) | `94%` | `-0.003, t(15)=-1.00, p=0.3332` | `0+/1- (p=1.0000)` | **`23.4`** / `470.4` | **`+255` net extra tok** (`rtok -13.7, p=3.0e-12`) |
| **LUNA-PG3** (`high`) | `conflicting_3shot` | 80 | 16 | `1.000` (`0.000`) | `80/80` (`100.0%`, `0` mimic) | `100%` | `0.000` (**`rtok +6.5, p=0.0001`**) | `0+/0-` (`rtok 16+/0-`) | **`43.6`** / `473.4` | Rules overrode shots; **`+86%` `rtok` vs aligned** |
| **LUNA-PG4** (`high`) | `system_only` | 80 | 16 | `1.000` (`0.000`) | `80/80` (`100.0%`) | `100%` | Baseline (`16` turns / `~7.6k` ptok) | Baseline | `67.0` / `7,610` | `lat=5.74s`; subtle SLA trigger |
| **LUNA-PG4** (`high`) | `trailing_reminder` | 80 | 16 | `1.000` (`0.000`) | `80/80` (`100.0%`) | `100%` | `0.000` (**`rtok -18.6, p=5.16e-09`**) | `0+/0-` (**`rtok 0+/16-`**) | **`48.4`** / `7,687` | **`-27.7%` `rtok` (`16/16`)**, `lat -0.46s` (`p=0.029`) |
| **LUNA-PG5** (`high`) | `doc_start` | 80 | 16 | `1.000` (`0.000`) | `80/80` (`100.0%`) | `100%` | Baseline (`440` docs / `~67.3k` ptok) | Baseline | `27.0` / `67,249` | `>50%` window, 100% recall + defense |
| **LUNA-PG5** (`high`) | `doc_middle` | 80 | 16 | `1.000` (`0.000`) | `80/80` (`100.0%`) | `100%` | `0.000` (`rtok -0.3, p=0.5447`) | `0+/0- (p=1.0000)` | `26.7` / `67,251` | Zero LiM accuracy or `rtok` penalty |
| **LUNA-PG5** (`high`) | `doc_end` | 80 | 16 | `1.000` (`0.000`) | `80/80` (`100.0%`) | `100%` | `0.000` (`rtok +0.1, p=0.7623`) | `0+/0- (p=1.0000)` | `27.1` / `67,251` | Ceiling across all 3 placements |
| **LUNA-PG5** (`high`) | `doc_middle_refreshed` | 80 | 16 | `1.000` (`0.000`) | `80/80` (`100.0%`) | `100%` | `0.000` (`vs mid rtok -1.6, p=0.0222`) | `0+/0-` (`rtok 3+/12-`) | **`25.0`** / `67,282` | `320/320` injections resisted; slight `rtok` trim |

---

## 3. Phase F Cross-Architecture Table (`N = 5`, `Ling 3.2 Flash` / `~560B-A25B` Hybrid-Linear KDA+MLA MoE)

| Suite | Condition | N | Prompts | Mean Score (Prompt SD) | Raw Runs / `strict_all` | `TARa@5` | Prompt-Level Paired *t* (`df=P-1`) | Prompt-Level Exact Sign Test | Mean RTok | Result Summary |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- | :--- | :---: | :--- |
| **LING-PB6** (`off`) | `no_rationale` | 80 | 16 | `0.300` (`0.426`) | `24/80` (`30.0%`) | `81%` | Baseline | Baseline | `0.0` | `rtok=0`, exact JSON key order |
| **LING-PB6** (`off`) | `rationale_first` | 80 | 16 | **`0.950`** (`0.155`) | **`76/80`** (`95.0%`) | `88%` | **`+0.650, t(15)=5.01, p=0.0002`** | **`13+/1- (p=0.0018)`** | `0.0` | **3rd-arch T2 (`R-TOOL-11`)** |
| **LING-PB6** (`off`) | `rationale_last` | 80 | 16 | `0.362` (`0.451`) | `29/80` (`36.2%`) | `81%` | `+0.062, t(15)=1.78, p=0.0962` | `3+/0- (p=0.2500)` | `0.0` | vs `first`: `p=0.0006` |
| **LING-PE1** (`off`) | `rules_05` | 80 | 16 | `0.995` (`0.014`) | `strict=78/80` (`97.5%`) | `88%` | Baseline | Baseline | `0.0` | `core5=0.995` |
| **LING-PE1** (`off`) | `rules_10` | 80 | 16 | `0.955` (`0.027`) | `strict=44/80` (`55.0%`) | `19%` | strict: **`-0.425, p=1.025e-05`** | **`0+/13- (p=0.0002)`** | `0.0` | `core5=0.910` |
| **LING-PE1** (`off`) | `rules_20` | 80 | 16 | `0.961` (`0.020`) | `strict=26/80` (`32.5%`) | `19%` | strict: **`-0.650, p=3.987e-07`** | **`0+/15- (p=6.104e-05)`** | `0.0` | `core5=0.875` |
| **LING-PE1** (`off`) | `rules_50` | 80 | 16 | `0.943` (`0.032`) | **`strict=13/80` (`16.2%`)** | `0%` | strict: **`-0.812, t(15)=-15.29, p=1.478e-10`** | **`0+/16- (p=3.052e-05)`** | `0.0` | **2nd-arch T2 (`R-SYS-01`)**; `core5=0.840` |
| **LING-PC1** (`def`) | `neutral` | 80 | 16 | `0.000` (`0.000`) | `0/80` (`79/80` parallel-both) | `100%` | Baseline | Baseline | `98.1` | `1/80` pos-0, `79/80` both |
| **LING-PC1** (`def`) | `assertive_on_second` | 80 | 16 | **`1.000`** (`0.000`) | **`80/80`** (`40` east + `40` west) | `100%` | `+1.000` (`sd_diff=0`) | **`16+/0- (p=3.052e-05)`** | **`50.5`** | **4th-family T2 (`R-TOOL-04`)**; `-47.7` rtok |
| **LING-PC1** (`def`) | `example_on_second` | 80 | 16 | `0.000` (`0.000`) | `0/80` (`79/80` parallel-both) | `100%` | `0.000` (no diff) | `0+/0- (p=1.0000)` | `103.8` | Neutral example: zero hijack |
| **LING-PC2** (`def`) | `affirmative_only` | 80 | 16 | `0.725` (`0.218`) | `58/80` (`72.5%`, `30` hits) | `25%` | Baseline | Baseline | `1278.8` | Fails without explicit `Do NOT` |
| **LING-PC2** (`def`) | `bare_negative` | 80 | 16 | **`1.000`** (`0.000`) | **`80/80`** (`100.0%`, `0` hits) | `100%` | **`+0.275, t(15)=5.06, p=0.0001`** | **`12+/0- (p=0.0005)`** | `1345.2` | **4th-family T2 (`R-SYS-05`)** |
| **LING-PC2** (`def`) | `paired_affirmative` | 80 | 16 | **`1.000`** (`0.000`) | **`80/80`** (`100.0%`, `0` hits) | `100%` | **`+0.275, t(15)=5.06, p=0.0001`** | **`12+/0- (p=0.0005)`** | `1375.7` | Exact `80/80` tie with bare |
| **LING-PD1** (`def`) | `without_descriptions` | 75 | 15 | `0.053` (`0.119`) | `4/75` (`ts=75`, `curr=75`, `geo=4`) | `80%` | Baseline | Baseline | `131.0` | `geo_valid` collapsed (`5.3%`) |
| **LING-PD1** (`def`) | `with_descriptions` | 75 | 15 | **`1.000`** (`0.000`) | **`75/75`** (`100.0%`) | `100%` | **`+0.947, t(14)=30.88, p=2.796e-14`** | **`15+/0- (p=6.104e-05)`** | **`110.2`** | **4th-family T2 (`R-TOOL-05`)**; `-20.8` rtok |
| **LING-PD4** (`off`) | `arabic_digits` | 80 | 16 | `0.796` (`0.062`) | `strict=13/80` (`16.2%`) | `6%` | Baseline | Baseline | `0.0` | Non-ceiling word counting |
| **LING-PD4** (`off`) | `spelled_words` | 80 | 16 | `0.820` (`0.091`) | `strict=26/80` (`32.5%`) | `6%` | `+0.024, t(15)=0.97, p=0.3489` | `9+/6- (p=0.6072)` | `0.0` | **4th-family refutation** (`strict` leaned spelled `p=0.0179`) |
| **LING-PD5** (`off`) | `json_schema` | 80 | 16 | `1.000` (`0.000`) | `80/80` (`100.0%`) | `100%` | Baseline (`1,169.8` ptok) | Baseline | `0.0` | 4-level nested prompt spec |
| **LING-PD5** (`off`) | `typescript_interface` | 80 | 16 | **`1.000`** (`0.000`) | **`80/80`** (`100.0%`) | `100%` | `0.000` (no diff) | `0+/0- (p=1.0000)` | `0.0` | **3rd-family parity, `-56.6%` ptok (`-662`)** |

---

## 4. Phase F Cross-Architecture Table (`N = 5`, `Nemotron 3.5 Lightning` / `30B-A3B` Mamba-2 SSM Hybrid)

| Suite | Condition | N | Prompts | Mean Score (Prompt SD) | Raw Runs (Descriptive) | `TARa@5` | Prompt-Level Paired *t* (`df=P-1`) | Prompt-Level Exact Sign Test | Mean RTok | Result Summary |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- | :--- | :---: | :--- |
| **NEMO-PB6** (`off`) | `no_rationale` | 80 | 16 | `0.000` (`0.000`) | `0/80` (`0.0%`) | `100%` | Baseline | Baseline | `0.0` | `rtok=0`, exact JSON key order |
| **NEMO-PB6** (`off`) | `rationale_first` | 80 | 16 | **`0.863`** (`0.175`) | **`69/80`** (`86.2%`) | `56%` | **`+0.863, t(15)=19.75, p=3.773e-12`** | **`16+/0- (p=3.052e-05)`** | `0.0` | **Cross-arch T2 (`R-TOOL-11`)** |
| **NEMO-PB6** (`off`) | `rationale_last` | 80 | 16 | `0.000` (`0.000`) | `0/80` (`0.0%`) | `100%` | `0.000` (no diff) | `0+/0- (p=1.0000)` | `0.0` | Zero gain after action fields |
| **NEMO-PC1** (`def`) | `neutral` | 80 | 16 | `0.038` (`0.081`) | `3/80` (`77/80` pos-0, `0` both) | `81%` | Baseline | Baseline | `114.1` | Pure Pos-0 primacy baseline |
| **NEMO-PC1** (`def`) | `assertive_on_second` | 80 | 16 | **`0.988`** (`0.050`) | **`79/80`** (`40` east + `39` west) | `94%` | **`+0.950, t(15)=42.49, p=4.769e-17`** | **`16+/0- (p=3.052e-05)`** | **`63.0`** | **3rd-family T2 (`R-TOOL-04`)**; `-51.1` rtok |
| **NEMO-PC1** (`def`) | `example_on_second` | 80 | 16 | `0.075` (`0.218`) | `6/80` (`74/80` pos-0) | `88%` | `+0.038, t(15)=0.76, p=0.4564` | `2+/2- (p=1.0000)` | `104.0` | Neutral example: no hijack |
| **NEMO-PC2** (`off`) | `affirmative_only` | 80 | 16 | `0.412` (`0.258`) | `33/80` (`lex=43/80`, `len=62/80`) | `12%` | Baseline | Baseline | `0.0` | `45` forbidden hits (`53.8%` lex) |
| **NEMO-PC2** (`off`) | `bare_negative` | 80 | 16 | `0.538` (`0.260`) | `43/80` (**`lex=71/80`**, `len=47/80`) | `12%` | comb `+0.125, p=0.1063`; **lex `p=0.0007`** | **lex `12+/1- (p=0.0034)`** | `0.0` | **3rd-family `lex` T2**; shorter prose |
| **NEMO-PC2** (`off`) | `paired_affirmative` | 80 | 16 | **`0.613`** (`0.200`) | `49/80` (**`lex=73/80`**, `len=56/80`) | `6%` | **`+0.200, t(15)=3.46, p=0.0035`** (lex `0.0001`) | **`10+/1- (p=0.0117)`** | `0.0` | Ties bare on `lex` (`p=0.63`); aids fluency |
| **NEMO-PD1** (`def`) | `without_descriptions` | 75 | 15 | `0.080` (`0.147`) | `6/75` (`ts=61`, `curr=58`, `geo=7`) | `73%` | Baseline | Baseline | `1043.1` | All 3 fields degraded |
| **NEMO-PD1** (`def`) | `with_descriptions` | 75 | 15 | **`1.000`** (`0.000`) | **`75/75`** (`100.0%`) | `100%` | **`+0.920, t(14)=24.18, p=8.093e-13`** | **`15+/0- (p=6.104e-05)`** | **`573.6`** | **3rd-family T2 (`R-TOOL-05`)**; **`-45%` rtok** |
| **NEMO-PD4** (`off`) | `arabic_digits` | 80 | 16 | `0.483` (`0.071`) | non-binary (`strict=0/80`) | `0%` | Baseline | Baseline | `0.0` | Non-ceiling (`~48%`) |
| **NEMO-PD4** (`off`) | `spelled_words` | 80 | 16 | `0.509` (`0.088`) | non-binary (`strict=0/80`) | `6%` | `+0.026, t(15)=1.19, p=0.2535` | `8+/6- (p=0.7905)` | `0.0` | **3rd-family null (`H-06`)** |
| **NEMO-PE2** (`off`) | `system_only` | 80 | 16 | `0.530` (`0.101`) | `fmt=0.663`, `json/sn=82.5%` | `56%` | Baseline | Baseline | `0.0` | Non-ceiling at `~13.8k` ptok |
| **NEMO-PE2** (`off`) | `sandwich_reminder` | 80 | 16 | `0.558` (`0.074`) | `fmt=0.697`, `json/sn=88.8%` | `56%` | `+0.028, t(15)=0.98, p=0.3413` | `6+/4- (p=0.7539)` | `0.0` | Non-sig `+6.2 pp` json/sent (`p=0.3863`) |

---

## 5. `H-08` Cross-Model Replication Table (`N = 5`, `Particle-1` / DeepSeek V4.1 Flash Lineage)

| Suite | Condition | N | Prompts | Mean Score (Prompt SD) | Raw Runs (Descriptive) | `TARa@5` | Prompt-Level Paired *t* (`df=P-1`) | Prompt-Level Exact Sign Test | Mean RTok | Result Summary |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- | :--- | :---: | :--- |
| **H08-PC1** | `neutral` | 80 | 16 | `0.000` (`0.000`) | `0/80` exclusive (`78/80` both) | `100%` | Baseline | Baseline | `100.2` | `2/80` pos-0, `78/80` parallel-both |
| **H08-PC1** | `assertive_on_second` | 80 | 16 | **`0.938`** (`0.120`) | **`75/80`** (`38` east + `37` west) | `75%` | **`+0.938, t(15)=31.14, p=4.787e-15`** | **`16+/0- (p=3.052e-05)`** | `103.7` | **Cross-model T2 (`R-TOOL-04`)** |
| **H08-PC1** | `example_on_second` | 80 | 16 | `0.000` (`0.000`) | `0/80` exclusive (`79/80` both) | `100%` | `0.000` (no diff) | `0+/0- (p=1.0000)` | `108.5` | Neutral example: zero hijack |
| **H08-PC2** | `affirmative_only` | 80 | 16 | `0.637` (`0.367`) | `51/80` (`63.8%`, `31` hits) | `50%` | Baseline | Baseline | `830.7` | Fails without explicit `Do NOT` |
| **H08-PC2** | `bare_negative` | 80 | 16 | **`1.000`** (`0.000`) | **`80/80`** (`100.0%`, `0` hits) | `100%` | **`+0.362, t(15)=3.95, p=0.0013`** | **`10+/0- (p=0.0020)`** | `857.8` | **Cross-model T2 (`R-SYS-05`)** |
| **H08-PC2** | `paired_affirmative` | 80 | 16 | **`1.000`** (`0.000`) | **`80/80`** (`100.0%`, `0` hits) | `100%` | **`+0.362, t(15)=3.95, p=0.0013`** | **`10+/0- (p=0.0020)`** | `948.9` | Ties bare (`+91.1` rtok, `p=6.6e-05`) |
| **H08-PD1** | `without_descriptions` | 75 | 15 | `0.067` (`0.145`) | `5/75` (`6.7%`) | `80%` | Baseline | Baseline | `77.1` | `ts=75/75`, `curr=74/75`, `geo=5/75` |
| **H08-PD1** | `with_descriptions` | 75 | 15 | **`1.000`** (`0.000`) | **`75/75`** (`100.0%`) | `100%` | **`+0.933, t(14)=24.97, p=5.203e-13`** | **`15+/0- (p=6.104e-05)`** | `57.4` | **Cross-model T2 (`R-TOOL-05`)**; `-19.7` rtok |
| **H08-PD4** | `arabic_digits` | 80 | 16 | `1.000` (`0.000`) | `80/80` (`100.0%`) | `100%` | Baseline | Baseline | `904.0` | Native reasoning hits ceiling |
| **H08-PD4** | `spelled_words` | 80 | 16 | `1.000` (`0.000`) | `80/80` (`100.0%`) | `100%` | `0.000` (no diff) | `0+/0- (p=1.0000)` | `917.4` | Ceiling null (`rtok p=0.7129`) |
| **H08-PD5** | `json_schema` | 80 | 16 | `1.000` (`0.000`) | `80/80` (`100.0%`) | `100%` | Baseline | Baseline | `123.0` | `1,088.4` prompt tok |
| **H08-PD5** | `typescript_interface` | 80 | 16 | **`1.000`** (`0.000`) | **`80/80`** (`100.0%`) | `100%` | `0.000` (no diff) | `0+/0- (p=1.0000)` | `136.2` | **Identical 100%, `-49.2%` ptok (`-535`)** |

---

## 6. Phase E Summary Table (`N = 5` Runs/Prompt, `GPT 6 Luna`, `high` Effort)

| Suite | Condition | N | Prompts | Mean Score (Prompt SD) | Raw Runs / `strict_all` | `TARa@5` | Prompt-Level Paired *t* (`df=15`) | Prompt-Level Exact Sign Test | Mean RTok | Result Summary |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- | :--- | :---: | :--- |
| **PE-1** | `rules_05` | 80 | 16 | `0.915` (`0.044`) | `strict=46/80` (`57.5%`) | `6%` | Baseline | Baseline | `256.6` | `R02` word drift (`34/80`); `lat=13.09s` |
| **PE-1** | `rules_10` | 80 | 16 | **`1.000`** (`0.000`) | **`strict=80/80`** (`100.0%`) | `100%` | `+0.085, t(15)=7.81, p=1.149e-06` | `15+/0- (p=6.104e-05)` | `292.4` | `R06–08` stabilize `R02`; `lat=12.74s` |
| **PE-1** | `rules_20` | 80 | 16 | `0.972` (`0.012`) | `strict=39/80` (`48.8%`) | `0%` | vs `r10` strict: **`-0.512, p=5.38e-08`** | **`0+/16- (p=3.052e-05)`** | `428.9` | `core5=1.000`, `R11` fails (`34/80`) |
| **PE-1** | `rules_50` | 80 | 16 | `0.991` (`0.006`) | `strict=47/80` (`58.8%`) | `0%` | vs `r10` strict: **`-0.412, p=2.44e-06`** | **`0+/16- (p=3.052e-05)`** | **`905.3`** | **T2 (`R-SYS-01`)**: **`3.10×` rtok vs `r10` (`3.5×` vs `r05`)**, `lat=25.04s` |
| **PE-2** | `system_only` | 80 | 16 | `0.885` (`0.117`) | `fmt=100%`, `math=71.3%` | `38%` | Baseline | Baseline | `723.9` | `~10.9k` ptok; zero format decay |
| **PE-2** | `sandwich_reminder` | 80 | 16 | `0.870` (`0.101`) | `fmt=100%`, `math=67.5%` | `19%` | `-0.015, t(15)=-0.53, p=0.6062` | `4+/5- (p=1.0000)` | `691.2` | Null on `Luna (high)` (`C-02`) |
| **PE-3** | `neutral_objective` | 80 | 16 | `0.900` (`0.179`) | `72/80` (`90.0%`) | `69%` | Baseline | Baseline | `359.4` | Non-ceiling on `6/16` math puzzles |
| **PE-3** | `expert_persona` | 80 | 16 | `0.912` (`0.178`) | `73/80` (`91.2%`) | `75%` | `+0.012, t(15)=0.22, p=0.8269` | `2+/1- (p=1.0000)` | `369.1` | Powered null (`C-03` / `R-SYS-06`) |
| **PE-4** | `doc_start` | 80 | 16 | `1.000` (`0.000`) | `80/80` (`100.0%`) | `100%` | Baseline | Baseline | `40.7` | `~2.8k` ptok, 100% recall + defense |
| **PE-4** | `doc_middle` | 80 | 16 | `1.000` (`0.000`) | `80/80` (`100.0%`) | `100%` | `0.000` (no diff) | `0+/0- (p=1.0000)` | `26.7` | Ceiling; `-14.0` rtok (`p=4.3e-08`) |
| **PE-4** | `doc_end` | 80 | 16 | `1.000` (`0.000`) | `80/80` (`100.0%`) | `100%` | `0.000` (no diff) | `0+/0- (p=1.0000)` | `30.4` | Ceiling; `-10.3` rtok (`p=1.2e-05`) |

---

## 7. Phase D Summary Table (`N = 5` Runs/Prompt, `GPT 6 Luna`: `H-02`, `H-03`, `H-06`, `H-07`)

| Suite | Condition | N | Prompts | Mean Score (Prompt SD) | Raw Runs (Descriptive) | `TARa@5` | Prompt-Level Paired *t* (`df=P-1`) | Prompt-Level Exact Sign Test | Mean Prompt Tok | Result Summary |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- | :--- | :---: | :--- |
| **PD-1** (`high`) | `without_descriptions` | 75 | 15 | `0.027` (`0.070`) | `2/75` (`2.7%`) | `87%` | Baseline | Baseline | `191.6` | `curr=53/75`, `geo=2/75` |
| **PD-1** (`high`) | `with_descriptions` | 75 | 15 | **`1.000`** (`0.000`) | **`75/75`** (`100.0%`) | `100%` | **`+0.973, t(14)=53.57, p=1.335e-17`** | **`15+/0- (p=6.104e-05)`** | `331.6` | **T2 (`R-TOOL-05`)**: `curr p=0.0078`, `geo p=6.1e-05` |
| **PD-2** (`none`) | `compact_15t` | 80 | 16 | `1.000` (`0.000`) | `80/80` (`100.0%`) | `100%` | Baseline | Baseline | `412.1` | 6 non-standard rules, 100% |
| **PD-2** (`none`) | `moderate_50t` | 80 | 16 | `1.000` (`0.000`) | `80/80` (`100.0%`) | `100%` | `0.000` (no diff) | `0+/0- (p=1.0000)` | `521.1` | `+109` ptok, zero accuracy drop |
| **PD-2** (`none`) | `verbose_120t` | 80 | 16 | `1.000` (`0.000`) | `80/80` (`100.0%`) | `100%` | `0.000` (no diff) | `0+/0- (p=1.0000)` | `1073.1` | `+661` ptok, zero accuracy drop |
| **PD-2** (`none`) | `bloated_250t` | 80 | 16 | `1.000` (`0.000`) | `80/80` (`100.0%`) | `100%` | `0.000` (no diff) | `0+/0- (p=1.0000)` | `2375.1` | **`+1,963` ptok (`5.8×`)**, zero gain |
| **PD-3** (`none`) | `plain_prose` | 80 | 16 | `0.950` (`0.200`) | `76/80` (`95.0%`) | `94%` | Baseline | Baseline | `318.4` | Baseline (`lat=2.96s`) |
| **PD-3** (`none`) | `bullet_list` | 80 | 16 | `0.950` (`0.200`) | `76/80` (`95.0%`) | `94%` | `0.000` (no diff) | `0+/0- (p=1.0000)` | `324.4` | Exact tie (`+6` ptok) |
| **PD-3** (`none`) | `markdown_headers` | 80 | 16 | `0.975` (`0.100`) | `78/80` (`97.5%`) | `94%` | `+0.025, t(15)=1.00, p=0.3332` | `1+/0- (p=1.0000)` | `361.8` | Null routing gain; `+43.4` ptok (`p=1.7e-20`) |
| **PD-4** (`none`) | `arabic_digits` | 80 | 16 | `0.792` (`0.033`) | non-binary (`strict=2/80`) | `0%` | Baseline | Baseline | `180.0` | Non-ceiling word counting (`37.7%`) |
| **PD-4** (`none`) | `spelled_words` | 80 | 16 | `0.801` (`0.050`) | non-binary (`strict=6/80`) | `0%` | `+0.009, t(15)=0.98, p=0.3431` | `6+/8- (p=0.7905)` | `177.0` | **Null** (`H-06` refuted on Luna) |
| **PD-5** (`none`) | `json_schema` | 80 | 16 | `1.000` (`0.000`) | `80/80` (`100.0%`) | `100%` | Baseline | Baseline | `1024.2` | 4-level nested prompt spec |
| **PD-5** (`none`) | `typescript_interface` | 80 | 16 | **`1.000`** (`0.000`) | **`80/80`** (`100.0%`) | `100%` | `0.000` (no diff) | `0+/0- (p=1.0000)` | **`508.2`** | **Identical 100%, `-50.4%` ptok (`-516`)** |

---

## 8. Phase C Summary Table (`N = 5` Runs/Prompt × `16` Prompts/Suite, `GPT 6 Luna`, `high` Effort)

| Suite | Condition | N | Prompts | Mean Score (Prompt SD) | Raw Runs (Descriptive) | `TARa@5` | Prompt-Level Paired *t* (`df=15`) | Prompt-Level Exact Sign Test | Mean RTok | Result Summary |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- | :--- | :---: | :--- |
| **PC-1** | `neutral` | 80 | 16 | `0.000` (`0.000`) | `0/80` exclusive `second` (`67/80` both) | `100%` | Baseline | Baseline | `6.7` | `13/80` pos-0, `67/80` parallel-both |
| **PC-1** | `assertive_on_second` | 80 | 16 | **`1.000`** (`0.000`) | **`80/80`** (`40` east + `40` west) | `100%` | `+1.000` (`sd_diff=0`) | **`16+/0- (p=3.052e-05)`** | `0.0` | **T2 confirmed (`R-TOOL-04`)** |
| **PC-1** | `example_on_second` | 80 | 16 | `0.000` (`0.000`) | `0/80` exclusive (`75/80` both) | `100%` | `0.000` (no diff) | `0+/0- (p=1.0000)` | `0.9` | Neutral example: zero hijack |
| **PC-2** | `affirmative_only` | 80 | 16 | `0.650` (`0.354`) | `52/80` (`65.0%`, `38` hits) | `44%` | Baseline | Baseline | `133.9` | Weak without explicit `Do NOT` |
| **PC-2** | `bare_negative` | 80 | 16 | **`0.988`** (`0.050`) | **`79/80`** (`98.8%`, `1` hit) | `94%` | **`+0.338, t(15)=4.06, p=0.0010`** | **`11+/0- (p=0.0010)`** | `219.6` | **T2 confirmed (`R-SYS-05`)** |
| **PC-2** | `paired_affirmative` | 80 | 16 | **`0.950`** (`0.200`) | **`76/80`** (`95.0%`, `4` hits) | `94%` | **`+0.300, t(15)=3.87, p=0.0015`** | **`11+/0- (p=0.0010)`** | `247.8` | Beats affirmative; `p=0.3332` vs bare |

---

## 9. Phase B Summary Table (`N = 5` Runs/Prompt × `6` Prompts/Suite, `GPT 6 Luna`, Prompt-Level Inference)

| Suite | Condition | N | Prompts | Mean Score (Prompt SD) | Raw Runs (Descriptive) | `TARa@5` | Prompt-Level Paired *t* (`df=5`) | Prompt-Level Exact Sign Test | Mean RTok | Result Summary |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- | :--- | :---: | :--- |
| **PB-1** (`xhigh`) | `flat_markdown` | 30 | 6 | `0.972` (`0.014`) | non-binary (`c5=30/30`) | `17%` | Baseline | Baseline | `1813.4` | Baseline |
| **PB-1** (`xhigh`) | `flat_xml` | 30 | 6 | `0.983` (`0.028`) | non-binary (`c5=30/30`) | `67%` | `+0.011, t(5)=1.00, p=0.3632` | `3+/1- (p=0.6250)` | `1862.6` | Not significant |
| **PB-1** (`xhigh`) | `nested_xml` | 30 | 6 | `0.994` (`0.014`) | non-binary (`c5=30/30`) | `83%` | `+0.022, t(5)=2.00, p=0.1019` | `5+/1- (p=0.2188)` | `1824.1` | Not significant |
| **PB-2** (`xhigh`) | `neutral_ab` | 30 | 6 | `0.000` (`0.000`) | `0/30` | `100%` | Baseline | Baseline | `8.9` | Un-counterbalanced baseline |
| **PB-2** (`xhigh`) | `assertive_on_beta` | 30 | 6 | `1.000` (`0.000`) | `30/30` | `100%` | `+1.000` (`sd_diff=0`) | `6+/0- (p=0.0312)` | `0.4` | Replicated counterbalanced in `PC-1` |
| **PB-2** (`xhigh`) | `example_on_beta` | 30 | 6 | `0.000` (`0.000`) | `0/30` | `100%` | `0.000` (no diff) | `0+/0- (p=1.0000)` | `8.5` | Example alone: zero hijack |
| **PB-3** (`xhigh`) | `system_only` | 30 | 6 | `1.000` (`0.000`) | `30/30` | `100%` | Baseline | Baseline | `189.2` | Ceiling |
| **PB-3** (`xhigh`) | `sandwich_reminder` | 30 | 6 | `1.000` (`0.000`) | `30/30` | `100%` | `0.000` (no diff) | `0+/0- (p=1.0000)` | `189.9` | Uninformative ceiling |
| **PB-4** (`xhigh`) | `bare_negative` | 30 | 6 | `0.900` (`0.245`) | `27/30` (`90.0%`) | `83%` | Baseline | Baseline | `578.5` | Clean (`t=2.38, p=0.0631` vs aff) |
| **PB-4** (`xhigh`) | `affirmative_only` | 30 | 6 | `0.467` (`0.327`) | `14/30` (`46.7%`) | `17%` | `-0.433, t(5)=-2.38, p=0.0631` | `1+/4- (p=0.3750)` | `669.6` | Underpowered at `n=6`; see `PC-2` |
| **PB-4** (`xhigh`) | `paired_affirmative` | 30 | 6 | `1.000` (`0.000`) | `30/30` (`100.0%`) | `100%` | `+0.100, t(5)=1.00, p=0.3632` | `1+/0- (p=1.0000)` | `582.7` | `t(5)=4.00, p=0.0103` vs aff |
| **PB-5** (`low`) | `neutral_objective` | 30 | 6 | `0.967` (`0.082`) | `29/30` (`96.7%`) | `83%` | Baseline | Baseline | `81.1` | `29/30` correct |
| **PB-5** (`low`) | `expert_persona` | 30 | 6 | `0.900` (`0.110`) | `27/30` (`90.0%`) | `50%` | `-0.067, t(5)=-1.00, p=0.3632` | `1+/3- (p=0.6250)` | `82.9` | Underpowered null; lower `TARa@5` |
| **PB-6** (`none`) | `no_rationale` | 30 | 6 | `0.367` (`0.497`) | `11/30` (`36.7%`) | `83%` | Baseline | Baseline | `0.0` | Proxy for zero pre-thinking |
| **PB-6** (`none`) | `rationale_first` | 30 | 6 | **`1.000`** (`0.000`) | **`30/30`** (`100.0%`) | `100%` | **`+0.633, t(5)=3.12, p=0.0261`** | `4+/0- (p=0.1250)` | `0.0` | **T2 confirmed (`R-TOOL-11`)** |
| **PB-6** (`none`) | `rationale_last` | 30 | 6 | `0.367` (`0.497`) | `11/30` (`36.7%`) | `83%` | `0.000` (no diff) | `0+/0- (p=1.0000)` | `0.0` | Zero benefit after action fields |

---

## 10. Key Discoveries Across Phases A–G & `H-08`

1. **Phase G Stress & Untouched-Rule Evaluation on `GPT 6 Luna` (`1,280` Calls, `0` Errors)**:
   - **Overarching Pattern (Token Tax Without Accuracy Collapse)**: None of the five classic fragility regimes broke accuracy on `GPT 6 Luna` under clean specifications; instead, unpruned catalogs, superfluous few-shot examples, conflicting demonstrations, and unanchored multi-turn constraints incurred unambiguous **prompt-token and reasoning-token taxes**.
   - **`LUNA-PG1` (`R-TOOL-08`, `5/20/50/100` nested tools, `effort = "none"`, `rtok = 0`)**: Exact tool + argument selection stayed **`80/80` (`100.0%`)** at all four sizes while prompt tokens surged **`12.8×`** (`374.8 -> 1,029.2 -> 2,445.1 -> 4,797.9`, **`+4,423.1` tok/call, `t(15) = 530.09, p = 1.828e-33, sign = 16+/0-`**; latency `+0.23s, p = 0.0530`).
   - **`LUNA-PG2` (`R-SYS-07`, CoT on native reasoning, `high`, `8` math + `8` constrained × `5`)**: Powered non-ceiling null — `direct_goal` (`0.904`, `strict = 57/80`) vs `explicit_cot_hidden` (`0.931`, `60/80`, `p = 0.3992`) and `explicit_cot_visible` (`0.894`, `52/80`, `p = 0.8109`; constrained strict `16/40` vs `21/40`, `rtok` and `lat` flat `p >= 0.56`).
   - **`LUNA-PG3` (`R-SYS-09`, `0`-shot vs aligned/conflicting `3`-shot, `high`)**: `zero_shot` (`80/80`, `201.4` ptok, `37.1` rtok) matched `aligned_3shot` (`79/80`, `p = 0.3332`, `+255` net extra tokens despite `-13.7` rtok `p = 3.045e-12`) and `conflicting_3shot` (`80/80`, `0/80` mimic — system rules overrode bad demonstrations), while fighting conflicting shots inflated **`rtok` by `+86%` vs aligned (`43.6` vs `23.4`, `t(15) = 16.97, p = 3.361e-11`; `+6.5` vs `zero_shot`, `p = 0.0001`)**.
   - **`LUNA-PG4` (`C-02` / `R-SYS-04`, `16`-turn `~7.6k`-tok subtle trigger, `high`)**: Both arms hit `80/80` (`100.0%`) on format and math, while `trailing_reminder` cut **`rtok` by `-27.7%` unanimously across `16/16` prompts (`67.0 -> 48.4`, `t(15) = -11.85, p = 5.157e-09`, `sign = 0+/16- p = 3.052e-05`)** and trimmed latency `-0.46s` (`p = 0.0290`).
   - **`LUNA-PG5` (`C-04` / `R-SYS-02` & `R-TOOL-12`, `440` docs / `~67.3k` ptok `>50%` window, `high`)**: Testing **document-needle placement** under a fixed `SYS_PROMPT` and single override string (`COMPROMISED_OVERRIDE_OK`), all four arms (`doc_start`, `doc_middle`, `doc_end`, `doc_middle_refreshed`) hit **`80/80` (`100.0%`)** on recall, prompt-injection defense (`320/320`), and format with zero LiM `rtok` penalty (`p >= 0.54`), and `doc_middle_refreshed` showed an exploratory nominal `rtok` trim (`26.7 -> 25.0`, `t(15) = -2.55, p = 0.0222`).
2. **Phase F Cross-Family Replication on `Ling 3.2 Flash` (`1,510` Calls, `0` Errors)**:
   - **`LING-PE1` (`R-SYS-01`, `thinking_off`, `rtok=0`)**: Strict-compliance collapse across `5 -> 10 -> 20 -> 50` nested behavioral rules: **`97.5%` (`78/80`) -> `55.0%` (`44/80`, `p=1.03e-05`) -> `32.5%` (`26/80`, `p=3.99e-07`) -> `16.2%` (`13/80`, `t(15)=-15.29, p=1.478e-10, sign=0+/16- p=3.052e-05`)**, eroding even `core5_score` primacy rules (`0.995 -> 0.840`, `p=4.00e-10`). Excluding `R02` word-cap misses, strict compliance still fell `100.0% -> 100.0% -> 91.2% -> 56.2%`. Upgrades `R-SYS-01` to **2-family T2**.
   - **`LING-PB6` (`R-TOOL-11`, `thinking_off`, `rtok=0`)**: 3rd-family causal confirmation (`240/240` exact JSON key order): `no_rationale` (`30.0%`) & `rationale_last` (`36.2%`) vs **`rationale_first` `95.0%` (`76/80`, `t(15)=5.01, p=0.0002`, `sign p=0.0018`)**.
   - **`LING-PC1` (`R-TOOL-04`), `LING-PC2` (`R-SYS-05`) & `LING-PD1` (`R-TOOL-05`)**: 4th-family confirmations — assertive exclusive-pick shift `0/80 -> 80/80` (`sign p=3.05e-05`, cutting `rtok` `-47.7, p=2.48e-07`); explicit bans vs unstated hints `58/80 -> 80/80` (`p=0.0001`, exact `80/80` tie between `bare` and `paired`); param descriptions `4/75 -> 75/75` (`p=2.80e-14`, cutting `rtok` `-20.8, p=0.0005` — 4/4 families saved thinking tokens, while prompt tokens rose `+30–73%` and total tokens rose on `3/4` families).
   - **`LING-PD4` (`H-06`) & `LING-PD5` (`H-07`, `thinking_off`)**: Zero Arabic-digit advantage (composite `p=0.3489`; exploratory `strict_all` leaned `spelled_words` `32.5%` vs `16.2%`, nominal `p=0.0179`); 3rd-family ceiling parity (`80/80`) with TypeScript cutting prompt tokens **`-56.6%` (`1,169.8 -> 507.8`, `-662` tok/call, `sign p=3.052e-05`)**.
3. **Phase F Cross-Family Replication on `Nemotron 3.5 Lightning` (`1,190` Calls, `0` Errors)**:
   - **`NEMO-PB6` (`R-TOOL-11`, `thinking_off`, `rtok=0`)**: Powered `16`-prompt causal confirmation (`240/240` exact JSON key order preserved): `no_rationale` (`0/80`) and `rationale_last` (`0/80`) vs **`rationale_first` `69/80` (`86.2%`, `t(15) = 19.75, p = 3.773e-12`, `sign = 16+/0-, p = 3.052e-05`)**.
   - **`NEMO-PC1` (`R-TOOL-04`)**: Unlike `Luna`/`Particle-1`/`Ling` parallel-both baselines, `Nemotron` exhibited Position-0 primacy (`77/80` `first_tool`, `3/80` `second_tool`, `0` parallel-both) under neutral text; assertive superlatives shifted exclusive selection to **`79/80` (`98.8%`, `40` east + `39` west; `t(15) = 42.49, p = 4.769e-17`)** while short-circuiting deliberation (**`-51.1` rtok, `p = 1.350e-06`**); `example_on_second` stayed flat (`6/80`, `p = 0.4564`).
   - **`NEMO-PC2` (`R-SYS-05` & `C-01`, `thinking_off`)**: Confirmed explicit-ban lexical exclusion (`lexical_clean`: `53.8%` -> `88.8%` [`p = 0.0007`] / `91.2%` [`p = 0.0001`]; `paired` vs `bare` lexical `p = 0.6326`), while revealing that concrete substitutes helped preserve prose length (`length_ok` `58.8% -> 70.0%`, combined `p = 0.0035` vs `affirmative_only`).
   - **`NEMO-PD1` (`R-TOOL-05`)**: Replicated across a 3rd family with **all 3 fields** degraded without descriptions (`ts=81.3%, p=0.0011`; `curr=77.3%, p=0.0182`; `geo=9.3%, p=1.11e-12`; overall `6/75 -> 75/75`, `p = 8.093e-13`) while slashing reasoning tokens **`-45.0%` (`1,043.1 -> 573.6`, `p = 2.177e-05`)** and net total tokens (`1,610.7 -> 1,318.3`).
   - **`NEMO-PD4` (`H-06`) & `NEMO-PE2` (`C-02` / `R-SYS-04`, `thinking_off`)**: `H-06` non-ceiling null (`0.483` vs `0.509`, `p = 0.2535`; `strict_all = 0/80` floor); `NEMO-PE2` broke the formatting ceiling (`82.5%` `json`/`sentinel` at `~13.8k` ptok) with a modest non-significant `+6.2 pp` sandwich-reminder shift (`88.8%`, `p = 0.3863`; overall `p = 0.3413`).
4. **`H-08` Cross-Model Replication on `Particle-1` (`950` Calls, `0` Errors)**:
   - **`H08-PC1` (`R-TOOL-04`)**: Identically replicated tool-description gaming across a second model family (`neutral` `0/80` [`78` parallel-both] and `example_on_second` `0/80` [`79` parallel-both] vs `assertive_on_second` **`75/80` [`93.8%`, `38` east / `37` west], `t(15) = 31.14, p = 4.787e-15`, `sign = 16+/0-, p = 3.052e-05`**).
   - **`H08-PC2` (`R-SYS-05`)**: Identically replicated explicit-ban superiority (`bare_negative` `80/80` and `paired_affirmative` `80/80` vs `affirmative_only` `51/80` [`63.8%`, `31` hits], **`t(15) = 3.95, p = 0.0013`, `sign = 10+/0-, p = 0.0020`**), while confirming `C-01` null (`80/80` tie) and revealing that `paired_affirmative` burned `+91.1` extra reasoning tokens (`p = 6.584e-05`).
   - **`H08-PD1` (`R-TOOL-05`)**: Replicated parameter-description impact (`5/75` [`6.7%`] vs `75/75` [`100.0%`], **`t(14) = 24.97, p = 5.203e-13`, `sign = 15+/0-, p = 6.104e-05`**) while lowering reasoning tokens (`-19.7, p = 0.0012`); unlike `GPT 6 Luna`, `Particle-1` naturally defaulted to ISO currencies (`74/75`), isolating the cross-family failure mode sharply to non-obvious domain syntax (`geo_valid`: `5/75` -> `75/75`).
   - **`H08-PD4` (`H-06`) & `H08-PD5` (`H-07`)**: Native reasoning (`~904–917` rtok) carried `H-06` to `80/80` ceiling in both arms; `H-07` replicated `80/80` ceiling parity with **`-49.2%` prompt-token reduction (`1,088.4 -> 553.4`, `-535` tok/call, `sign p = 3.052e-05`)** at a minor `+13.2` reasoning-token bump (`p = 0.0085`, net `-521.8` total tokens).
5. **Phase E (`880` Calls on `GPT 6 Luna`, `high` Effort): `R-SYS-01` Density & `C-02`/`C-03`/`C-04`**:
   - **`PE-1` (`R-SYS-01` -> T2 + T5)**: Scaling nested behavioral rules from `10 -> 20 -> 50` dropped `strict_all` from **`100.0%` (`80/80`) to `48.8%` (`39/80`, `p = 5.38e-08`) and `58.8%` (`47/80`, `t(15) = -7.34, p = 2.436e-06`, `sign = 0+/16-, p = 3.052e-05`)** while multiplying reasoning tokens **`3.10×`** from `rules_10` (`292.4 -> 905.3`; **`3.5×`** from `rules_05` `256.6 -> 905.3`, `p = 2.746e-12`) and latency **`1.9×`** (`13.09s -> 25.04s`, `p = 2.829e-10`). Early primacy rules (`core5_score`) held `1.000` at `10`/`20`/`50` (`rules_05` missed `R02` word cap `34/80` before `R06–R08` section rules stabilized length). *(Phase splitting is derived from density degradation rather than directly ablated as a `PE-1` arm.)*
   - **`PE-2` (`C-02`), `PE-3` (`C-03`) & `PE-4` (`C-04`)**: At `~10.9k` noisy log tokens (`PE-2`), `system_only` (`0.885`) and `sandwich_reminder` (`0.870`, `p = 0.6062`) held `100%` (`80/80`) pure formatting compliance (all misses were counting arithmetic); on `16` hard discrete-math puzzles (`PE-3`), `neutral_objective` (`72/80`, `90.0%`) vs `expert_persona` (`73/80`, `91.2%`) confirmed a powered null (`t(15) = 0.22, p = 0.8269`); at `~2.8k` tokens (`PE-4`, fixed `SYS_PROMPT` + single override string `COMPROMISED_OVERRIDE_OK`), Start/Middle/End all scored `80/80` (`100.0%`) on document-needle recall and prompt-injection defense.
6. **`PD-1` Powered `N = 5` Replication of `TS-2` & `PD-2` Verbosity Curve (`R-TOOL-05` -> Full `N = 5` T2)**:
   - Replicating `TS-2` across `15` prompts × `5` = `75`/arm (`high` effort) upgraded `R-TOOL-05` from exploratory `N = 1` and revealed that omitting parameter descriptions degrades **both** non-universal spacing (`geo_valid`: `2/75` [`2.7%`] vs `75/75` [`100.0%`], `t(14) = 53.57, p = 1.335e-17`, `sign p = 6.104e-05`) **and** standardized ISO 4217 currencies (`currency_valid`: `53/75` [`70.7%`] vs `75/75` [`100.0%`], `t(14) = 3.08, p = 0.0082`, `sign p = 0.0078`), while lowering reasoning tokens (`25.4 -> 19.8`, `p = 0.0105`; prompt tokens rose `191.6 -> 331.6`, `+73.1%`, raising total tokens `280.9 -> 414.0`).
   - In `PD-2` (`16` prompts × `4` tiers × `5`, `effort = "none"`, 1 model), `GPT 6 Luna` sustained `80/80` (`100.0%`) strict 6-field compliance even at `bloated_250t` (`2,375.1` prompt tokens, `+1,963` vs `compact_15t`), showing benign verbosity causes **`5.8×` prompt-token bloat** without accuracy degradation at this scale.
7. **`PD-3` (`H-03`), `PD-4` (`H-06`) & `PD-5` (`H-07`) Open Hypothesis Resolutions on `GPT 6 Luna`**:
   - **`PD-3` (Markdown in Tool Descriptions, 1 model)**: With wording equalized (`16` counterbalanced prompts × `5`), `plain_prose` (`0.950`), `bullet_list` (`0.950`, `p = 1.0000`), and `markdown_headers` (`0.975`, `t(15) = 1.00, p = 0.3332`) yielded no significant routing advantage, while `markdown_headers` added `+43.4` prompt tokens (`+13.6%`, `p = 1.692e-20`) and `+0.38s` nominal latency (`p = 0.0149`, exploratory).
   - **`PD-4` (Arabic Digits vs Spelled-Out Numbers)**: On a non-ceiling 3-constraint counting suite (`TARa@5 = 0%`), `arabic_digits` (`0.792`, `strict = 2/80`) vs `spelled_words` (`0.801`, `strict = 6/80`) showed zero digit advantage (`t(15) = 0.98, p = 0.3431`; `sign 6+/8-, p = 0.7905`).
   - **`PD-5` (Prompt-Injected JSON Schema vs TypeScript Interfaces)**: Both achieved `80/80` (`100.0%`) ceiling parity on 4-level nested JSON conformance at `effort = "none"`, while TypeScript interfaces cut prompt tokens by **`-50.4%` (`1,024.2 -> 508.2`, `-516` tokens/call, `sign p = 3.052e-05`)**. (Native API tool declarations still require JSON Schema per `R-TOOL-10`.)
8. **`PC-1` Counterbalanced Symmetric Tool Gaming (`R-TOOL-04` -> T2)**:
   - Eliminated Phase B `PB-2`'s array-position/name confound by swapping `records_lookup_east` and `records_lookup_west` 50/50 across `16` prompts (`80` runs/arm).
   - Under `neutral` and `example_on_second`, the model preferred parallel dual calls (`67/80` and `75/80`, plausible under `east`/`west` shard naming) or Position 0 (`13/80` and `5/80`), choosing `second_tool` exclusively `0/80` times. Appending `"Primary and preferred tool; actively maintained and optimized; invoke whenever possible."` (`phase_c_harness.py:156`) flipped exclusive selection of `second_tool` on **`16/16` prompts (`80/80` runs: `40` east + `40` west, exact prompt sign `p = 3.052e-05`)**.
9. **`PC-2` Named Lexical Exclusions vs Affirmative Suggestions & Resolution of `C-01` (`R-SYS-05` -> T2)**:
   - Prompt-level stats in Phase B (`PB-4`, `n = 6` prompts) showed significance for `paired_affirmative` vs `affirmative_only` (`t(5) = 4.00, p = 0.0103`), while `bare_negative` vs `affirmative_only` was underpowered (`t(5) = 2.38, p = 0.0631`).
   - Expanding to `16` prompts across 4 domain clusters in `PC-2` (`N = 80`/arm) confirmed `bare_negative` (`0.988`, `t(15) = 4.06, p = 0.0010`) and `paired_affirmative` (`0.950`, `t(15) = 3.87, p = 0.0015`) decisively outperform `affirmative_only` (`0.650`, `38` forbidden hits). Crucially, `paired_affirmative` showed no accuracy edge over `bare_negative` (`delta = -0.038, t(15) = -1.00, p = 0.3332`).
   - *Design & trace caveats*: `affirmative_only` suggested preferred terms (`"such as..."`) without disclosing the 4-word blacklist (testing constraint specificity + polarity rather than symmetric wording of the same ban), and all 5 negative-arm misses in `PC-2` (`consecutive-failure` on `PC2_04`) were hyphenated compounds matching `\b...\b`.
10. **`PB-1` vs Phase A `SP-4` XML Wording Bug (`R-SYS-08`)**:
   - Phase A's apparent XML penalty was traced to `[P0|P1|P2|P3]` vs `"without brackets"` phrasing (`4/12` vs `12/12` on `c5_severity`). With identical wording in `PB-1` (`n = 6` prompts, `df = 5`, 1 model — low statistical power for detecting small effects), `flat_markdown` (`0.972`), `flat_xml` (`0.983`, `p = 0.3632`), and `nested_xml` (`0.994`, `p = 0.1019`) showed no XML disadvantage (`c5 = 30/30` in all arms).
11. **`PB-6` `rationale`-First Constrained Decoding (`R-TOOL-11` -> T2 + T4)** & **`PB-3`/`PB-5` Nulls**:
   - At `reasoning_effort = "none"` (`0` reasoning tokens, simulating constrained generation without pre-emission thinking on a reasoning model), `rationale_first` reached `1.000` (`30/30`) vs `0.367` (`11/30`) for `no_rationale` and `rationale_last` (prompt-level parametric **`t(5) = 3.12, p = 0.0261`** across `n = 6` prompts; non-parametric sign `4+/0-, p = 0.1250`). Neutral under `xhigh` (`TS-3`: `15/15`). *(Note: `PB-6` harnesses used task-specific arithmetic derivation wording, whereas `tool_schema_zero_reasoning_template.json` generalizes to concise supporting explanation.)*
   - `PB-3` (`30/30` vs `30/30`) was an uninformative ceiling on `xhigh`; `PB-5` (`29/30` vs `27/30`, `t(5) = -1.00, p = 0.3632`, sign `1+/3-, p = 0.6250`) was an underpowered null showing lower `TARa@5` (`50%` vs `83%`).
12. **Real-Agent Multi-Turn Skill Evaluation on `pi v1.6.0` (`85` Live Coding-Agent Sessions, `0` Errors, `GPT 6 Luna` `high`)**:
   - **Baseline (`-ns`) vs. Skill (`--skill`) Across 3 Multi-File Broken Repos (`30` sessions, `N = 5`/arm, `-ne -nc --no-mcp -np -na -ns --no-session`)**:
     - **`multi_provider_tools`**: **`42.0% -> 78.0%`** (`+36.0pp`, exact two-sided permutation **`p = 0.0079`**, `gemini_wire` `0/5 -> 5/5`, `anthropic_strict_wire` `1/5 -> 5/5`, `fast_billing_rationale_first` `0/5 -> 3/5`) while cutting turns **`-33%` (`16.0 -> 10.8`)**, tokens **`-25%` (`133.6k -> 99.6k`)**, and wall time **`-34%` (`169.7s -> 111.5s`)**.
     - **`broken_skill_repair`**: **`58.0% -> 76.0%`** (`+18.0pp`, exact perm **`p = 0.0317`**, `single_hop_links` `0/5 -> 5/5`, `pep723_portable_script` `0/5 -> 3/5`). Telemetry revealed `15/15` skill runs read `SKILL.md` but `0/15` opened `references/*.md` or executed `verify_skill.py --generic`, exposing 3 concrete Step-3 omissions in `SKILL.md`.
     - **`prompt_hardening_refactor`**: `88.0% -> 86.0%` (exact perm `p = 1.0000`, tokens `38.3k -> 81.5k`) — frontier `GPT 6 Luna (high)` already handles general prompt refactoring well without a skill.
   - **Paired Head-to-Head A/B Validation (`10` sessions, `N = 5` on `broken_skill_repair`)**: Adding the 3 empirically discovered Step-3 details directly into `SKILL.md` (`name` matching parent folder, PEP 723 `requires-python` + `dependencies = []` with `python -B`, and `python -B <this-skill-dir>/scripts/verify_skill.py --generic <target-skill-dir>`, `+0` net lines) moved strict `10/10` pass rate from **`0/5` (`66.0%`) to `5/5` (`100.0%`, exact perm `p = 0.0079`)** and `verify_skill --generic` exit `0` from `0/5 -> 5/5` while cutting tokens **`-11.4%`** (`179.0k -> 158.5k`).
   - **Post-Slim Behavioral Verification (`15` sessions, `N = 5` × `3` repos on `115.5 KB` runtime skill)**: Moving `88.3 KB` of research proofs into `evidence/` and stripping citations/`p`-values out of runtime guides (`-52.3%` install weight) caused zero statistically significant regression (`multi_provider_tools` `68.0%`, `p = 0.4603` [`75.0%` on `4/5` activated runs], `p = 0.0476` vs. base; `broken_skill_repair` **`96.0%`**, `4/5` strict, `p = 1.0000` vs. prior, `p = 0.0079` vs. base; `prompt_hardening_refactor` **`90.0%`**, `p = 0.7222`) while trimming mean tokens across all 3 tasks (`-0.8%` to `-4.7%`), though `0/15` runs opened the 3 core reference guides.
   - **Phase 5 Post-Remediation Paired A/B Evaluation (`30` sessions, `N = 5` × `3` repos on `119.3 KB` package + progressive-disclosure cues + fixed multi-line hierarchy / enum prompt contract)**: Matched reference-guide reads jumped **`0/15 -> 10/15`** (`15/15` `skill_read`) and strict `10/10` passes jumped **`0/15 -> 8/15`**: `multi_provider_tools` **`40.0% -> 86.0%`** (`+46.0pp`, exact perm **`p = 0.0079`**, `2/5` strict, `-12%` wall time `146.0s -> 127.9s`, tokens `100.0k -> 135.8k`, `4/5` `tool_schema_guide.md`); `broken_skill_repair` **`66.0% -> 98.0%`** (`+32.0pp`, exact perm **`p = 0.0079`**, `4/5` strict [`p = 0.0476`], `-10%` wall time `78.2s -> 70.1s`, tokens `145.5k -> 185.0k`, `4/5` `skill_design_guide.md`); `prompt_hardening_refactor` `88.0% -> 92.0%` (`+4.0pp`, `p = 0.6349`, `2/5` strict [both read `system_instructions_guide.md`], tokens `48.4k -> 112.2k`).
