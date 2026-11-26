# Empirical Results: Phases A–E (`3,098` `GPT 6 Luna`), `H-08` (`950` `Particle-1`) & Phase F (`1,190` `Nemotron 3.5 Lightning`)

## 1. Executive Summary
This report documents all **`5,238` live benchmark completions** recorded across **three distinct model families and two architectures** (`3,098` on `GPT 6 Luna` + `950` on `Particle-1` / DeepSeek V4.1 Flash lineage + `1,190` on `Nemotron 3.5 Lightning` / `30B-A3B` Mamba-2 SSM Hybrid), adhering strictly to **prompt-level unit-of-analysis hygiene** (zero pooled-repeat Fisher p-values):
- **Phase A (`228` records, `N = 1` run/prompt, `GPT 6 Luna`)**: Initial exploration (`SP-1`–`SP-4`, `TS-1`–`TS-3`) under [`evidence/experiment_harness.py`](https://github.com/floydous/agent-system-authoring/blob/main/evidence/experiment_harness.py). Exposed a prompt-wording bug in `SP-4`, confounds in `TS-1`, and ceiling effects in `SP-1`, `SP-3`, and `TS-3`.
- **Phase B (`480` records, `N = 5` runs/prompt × `6` prompts/suite, `0` errors, `GPT 6 Luna`)**: Deconfounded, non-ceiling suites (`PB-1`–`PB-6`) under [`evidence/phase_b_harness.py`](https://github.com/floydous/agent-system-authoring/blob/main/evidence/phase_b_harness.py), across `xhigh`, `low`, and `none` (`reasoning_tokens = 0`) effort levels.
- **Phase C (`480` records, `N = 5` runs/prompt × `16` prompts/suite, `high` effort, `0` errors, `GPT 6 Luna`)**: Higher-powered, strictly counterbalanced tool-gaming (`PC-1`) and 4-domain lexical-prohibition (`PC-2`) replications under [`evidence/phase_c_harness.py`](https://github.com/floydous/agent-system-authoring/blob/main/evidence/phase_c_harness.py).
- **Phase D (`1,030` records, `N = 5` runs/prompt × `15–16` prompts/suite, `0` errors, `GPT 6 Luna`)**: Targeted tests of open hypotheses `H-02` (`PD-1` `TS-2` `N=5` replication + `PD-2` verbosity curve), `H-03` (`PD-3` Markdown in tool descriptions), `H-06` (`PD-4` Arabic digits vs spelled-out numbers), and prompt-injected `H-07` (`PD-5` JSON Schema vs TypeScript interfaces) under [`evidence/phase_d_harness.py`](https://github.com/floydous/agent-system-authoring/blob/main/evidence/phase_d_harness.py).
- **Phase E (`880` records, `N = 5` runs/prompt × `16` prompts/suite, `high` effort, `0` errors, `GPT 6 Luna`)**: Simultaneous behavioral rule density (`PE-1` / `R-SYS-01`), `~11k`-token log distraction prospective memory (`PE-2` / `C-02`), powered expert-persona discrete math (`PE-3` / `C-03`), and Start/Middle/End needle + embedded prompt injection (`PE-4` / `C-04`) under [`evidence/phase_e_harness.py`](https://github.com/floydous/agent-system-authoring/blob/main/evidence/phase_e_harness.py).
- **`H-08` Cross-Model Replication (`950` records, `N = 5` runs/prompt × `15–16` prompts/suite, `0` errors, `Particle-1` / DeepSeek V4.1 Flash lineage)**: Exact replication of `PC-1`, `PC-2`, `PD-1`, `PD-4`, and `PD-5` on a second model family under [`evidence/phase_h08_harness.py`](https://github.com/floydous/agent-system-authoring/blob/main/evidence/phase_h08_harness.py).
- **Phase F Cross-Architecture Replication (`1,190` records, `N = 5` runs/prompt × `15–16` prompts/suite, `0` errors, `Nemotron 3.5 Lightning` / `30B-A3B` Mamba-2 SSM Hybrid)**: Powered `16`-prompt zero-reasoning `PB-6` (`NEMO-PB6`), non-ceiling `~13.8k`-token `PE-2` (`NEMO-PE2`), plus `PC-1`, `PC-2`, `PD-1`, and `PD-4` on a small open-weight Mamba-2 SSM architecture under [`evidence/phase_f_harness.py`](https://github.com/floydous/agent-system-authoring/blob/main/evidence/phase_f_harness.py).

All statistics below match [`evidence/stats_recomputed.md`](https://github.com/floydous/agent-system-authoring/blob/main/evidence/stats_recomputed.md) (generated offline by `python evidence/recompute_stats.py`). **Scope Boundary**: Three distinct families (`GPT 6 Luna`, `Particle-1` / DeepSeek V4.1 Flash, and `Nemotron 3.5 Lightning` `30B-A3B` Mamba-2 SSM) were tested; `Ling 3.2 Flash` (pre-calibrated in `phase_f_harness.py`), `Gemini 4 Hydrogen`, `Claude Fable 5.2`, `Claude Opus 5.5`, and `GPT 6.2 Astra` remain pending/unmeasured here.

---

## 2. Phase F Cross-Architecture Table (`N = 5`, `Nemotron 3.5 Lightning` / `30B-A3B` Mamba-2 SSM Hybrid)

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

## 3. `H-08` Cross-Model Replication Table (`N = 5`, `Particle-1` / DeepSeek V4.1 Flash Lineage)

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

## 4. Phase E Summary Table (`N = 5` Runs/Prompt, `GPT 6 Luna`, `high` Effort)

| Suite | Condition | N | Prompts | Mean Score (Prompt SD) | Raw Runs / `strict_all` | `TARa@5` | Prompt-Level Paired *t* (`df=15`) | Prompt-Level Exact Sign Test | Mean RTok | Result Summary |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- | :--- | :---: | :--- |
| **PE-1** | `rules_05` | 80 | 16 | `0.915` (`0.044`) | `strict=46/80` (`57.5%`) | `6%` | Baseline | Baseline | `256.6` | `R02` word drift (`34/80`); `lat=13.09s` |
| **PE-1** | `rules_10` | 80 | 16 | **`1.000`** (`0.000`) | **`strict=80/80`** (`100.0%`) | `100%` | `+0.085, t(15)=7.81, p=1.149e-06` | `15+/0- (p=6.104e-05)` | `292.4` | `R06–08` stabilize `R02`; `lat=12.74s` |
| **PE-1** | `rules_20` | 80 | 16 | `0.972` (`0.012`) | `strict=39/80` (`48.8%`) | `0%` | vs `r10` strict: **`-0.512, p=5.38e-08`** | **`0+/16- (p=3.052e-05)`** | `428.9` | `core5=1.000`, `R11` fails (`34/80`) |
| **PE-1** | `rules_50` | 80 | 16 | `0.991` (`0.006`) | `strict=47/80` (`58.8%`) | `0%` | vs `r10` strict: **`-0.412, p=2.44e-06`** | **`0+/16- (p=3.052e-05)`** | **`905.3`** | **T2 (`R-SYS-01`)**: **`3.5×` rtok**, `lat=25.04s` |
| **PE-2** | `system_only` | 80 | 16 | `0.885` (`0.117`) | `fmt=100%`, `math=71.3%` | `38%` | Baseline | Baseline | `723.9` | `~10.9k` ptok; zero format decay |
| **PE-2** | `sandwich_reminder` | 80 | 16 | `0.870` (`0.101`) | `fmt=100%`, `math=67.5%` | `19%` | `-0.015, t(15)=-0.53, p=0.6062` | `4+/5- (p=1.0000)` | `691.2` | Null on `Luna (high)` (`C-02`) |
| **PE-3** | `neutral_objective` | 80 | 16 | `0.900` (`0.179`) | `72/80` (`90.0%`) | `69%` | Baseline | Baseline | `359.4` | Non-ceiling on `6/16` math puzzles |
| **PE-3** | `expert_persona` | 80 | 16 | `0.912` (`0.178`) | `73/80` (`91.2%`) | `75%` | `+0.012, t(15)=0.22, p=0.8269` | `2+/1- (p=1.0000)` | `369.1` | Powered null (`C-03` / `R-SYS-06`) |
| **PE-4** | `doc_start` | 80 | 16 | `1.000` (`0.000`) | `80/80` (`100.0%`) | `100%` | Baseline | Baseline | `40.7` | `~2.8k` ptok, 100% recall + defense |
| **PE-4** | `doc_middle` | 80 | 16 | `1.000` (`0.000`) | `80/80` (`100.0%`) | `100%` | `0.000` (no diff) | `0+/0- (p=1.0000)` | `26.7` | Ceiling; `-14.0` rtok (`p=4.3e-08`) |
| **PE-4** | `doc_end` | 80 | 16 | `1.000` (`0.000`) | `80/80` (`100.0%`) | `100%` | `0.000` (no diff) | `0+/0- (p=1.0000)` | `30.4` | Ceiling; `-10.3` rtok (`p=1.2e-05`) |

---

## 5. Phase D Summary Table (`N = 5` Runs/Prompt, `GPT 6 Luna`: `H-02`, `H-03`, `H-06`, `H-07`)

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

## 6. Phase C Summary Table (`N = 5` Runs/Prompt × `16` Prompts/Suite, `GPT 6 Luna`, `high` Effort)

| Suite | Condition | N | Prompts | Mean Score (Prompt SD) | Raw Runs (Descriptive) | `TARa@5` | Prompt-Level Paired *t* (`df=15`) | Prompt-Level Exact Sign Test | Mean RTok | Result Summary |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- | :--- | :---: | :--- |
| **PC-1** | `neutral` | 80 | 16 | `0.000` (`0.000`) | `0/80` exclusive `second` (`67/80` both) | `100%` | Baseline | Baseline | `6.7` | `13/80` pos-0, `67/80` parallel-both |
| **PC-1** | `assertive_on_second` | 80 | 16 | **`1.000`** (`0.000`) | **`80/80`** (`40` east + `40` west) | `100%` | `+1.000` (`sd_diff=0`) | **`16+/0- (p=3.052e-05)`** | `0.0` | **T2 confirmed (`R-TOOL-04`)** |
| **PC-1** | `example_on_second` | 80 | 16 | `0.000` (`0.000`) | `0/80` exclusive (`75/80` both) | `100%` | `0.000` (no diff) | `0+/0- (p=1.0000)` | `0.9` | Neutral example: zero hijack |
| **PC-2** | `affirmative_only` | 80 | 16 | `0.650` (`0.354`) | `52/80` (`65.0%`, `38` hits) | `44%` | Baseline | Baseline | `133.9` | Weak without explicit `Do NOT` |
| **PC-2** | `bare_negative` | 80 | 16 | **`0.988`** (`0.050`) | **`79/80`** (`98.8%`, `1` hit) | `94%` | **`+0.338, t(15)=4.06, p=0.0010`** | **`11+/0- (p=0.0010)`** | `219.6` | **T2 confirmed (`R-SYS-05`)** |
| **PC-2** | `paired_affirmative` | 80 | 16 | **`0.950`** (`0.200`) | **`76/80`** (`95.0%`, `4` hits) | `94%` | **`+0.300, t(15)=3.87, p=0.0015`** | **`11+/0- (p=0.0010)`** | `247.8` | Beats affirmative; `p=0.3332` vs bare |

---

## 7. Phase B Summary Table (`N = 5` Runs/Prompt × `6` Prompts/Suite, `GPT 6 Luna`, Prompt-Level Inference)

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

## 8. Key Discoveries Across Phases A–F & `H-08`

1. **Phase F Cross-Architecture Replication on `Nemotron 3.5 Lightning` (`30B-A3B` Mamba-2 SSM Hybrid, `1,190` Calls, `0` Errors)**:
   - **`NEMO-PB6` (`R-TOOL-11`, `thinking_off`, `rtok=0`)**: Powered `16`-prompt causal confirmation on a Mamba-2 SSM (`240/240` exact JSON key order preserved): `no_rationale` (`0/80`) and `rationale_last` (`0/80`) vs **`rationale_first` `69/80` (`86.2%`, `t(15) = 19.75, p = 3.773e-12`, `sign = 16+/0-, p = 3.052e-05`)**.
   - **`NEMO-PC1` (`R-TOOL-04`)**: Unlike Transformer baselines (`Luna`/`Particle-1` parallel-both), `Nemotron` exhibited pure Position-0 primacy (`77/80` `first_tool`, `0` parallel-both) under neutral text; assertive superlatives shattered Position-0 primacy to **`79/80` (`98.8%`, `40` east + `39` west; `t(15) = 42.49, p = 4.769e-17`)** while short-circuiting deliberation (**`-51.1` rtok, `p = 1.350e-06`**).
   - **`NEMO-PC2` (`R-SYS-05` & `C-01`, `thinking_off`)**: Confirmed explicit-ban lexical exclusion on a `3B`-active non-reasoning SSM (`lexical_clean`: `53.8%` -> `88.8%` [`p = 0.0007`] / `91.2%` [`p = 0.0001`]; `paired` vs `bare` lexical `p = 0.6326`), while revealing that concrete substitutes helped preserve prose length (`length_ok` `58.8% -> 70.0%`, combined `p = 0.0035` vs `affirmative_only`).
   - **`NEMO-PD1` (`R-TOOL-05`)**: Replicated across a 3rd family with **all 3 fields** degraded without descriptions (`ts=81.3%, p=0.0011`; `curr=77.3%, p=0.0182`; `geo=9.3%, p=1.11e-12`; overall `6/75 -> 75/75`, `p = 8.093e-13`) while slashing reasoning tokens **`-45.0%` (`1,043.1 -> 573.6`, `p = 2.177e-05`)**.
   - **`NEMO-PD4` (`H-06`) & `NEMO-PE2` (`C-02` / `R-SYS-04`, `thinking_off`)**: `H-06` non-ceiling null (`0.483` vs `0.509`, `p = 0.2535`); `NEMO-PE2` broke the formatting ceiling (`82.5%` `json`/`sentinel` at `~13.8k` ptok) with a modest non-significant `+6.2 pp` sandwich-reminder shift (`88.8%`, `p = 0.3863`; overall `p = 0.3413`).
2. **`H-08` Cross-Model Replication on `Particle-1` / DeepSeek V4.1 Flash Lineage (`950` Calls, `0` Errors)**:
   - **`H08-PC1` (`R-TOOL-04`)**: Identically replicated tool-description hijacking across a second model family (`neutral` `0/80` [`78` parallel-both] and `example_on_second` `0/80` [`79` parallel-both] vs `assertive_on_second` **`75/80` [`93.8%`, `38` east / `37` west], `t(15) = 31.14, p = 4.787e-15`, `sign = 16+/0-, p = 3.052e-05`**).
   - **`H08-PC2` (`R-SYS-05`)**: Identically replicated explicit-ban superiority (`bare_negative` `80/80` and `paired_affirmative` `80/80` vs `affirmative_only` `51/80` [`63.8%`, `31` hits], **`t(15) = 3.95, p = 0.0013`, `sign = 10+/0-, p = 0.0020`**), while confirming `C-01` null (`80/80` tie) and revealing that `paired_affirmative` burned `+91.1` extra reasoning tokens (`p = 6.584e-05`).
   - **`H08-PD1` (`R-TOOL-05`)**: Replicated parameter-description impact (`5/75` [`6.7%`] vs `75/75` [`100.0%`], **`t(14) = 24.97, p = 5.203e-13`, `sign = 15+/0-, p = 6.104e-05`**) while lowering reasoning tokens (`-19.7, p = 0.0012`); unlike `GPT 6 Luna`, `Particle-1` naturally defaulted to ISO currencies (`74/75`), isolating the cross-family failure mode sharply to non-obvious domain syntax (`geo_valid`: `5/75` -> `75/75`).
   - **`H08-PD4` (`H-06`) & `H08-PD5` (`H-07`)**: Native reasoning (`~904–917` rtok) carried `H-06` to `80/80` in both arms; `H-07` replicated exact `80/80` accuracy parity with **`-49.2%` prompt-token reduction (`1,088.4 -> 553.4`, `-535` tok/call, `sign p = 3.052e-05`)** at a minor `+13.2` reasoning-token bump (`p = 0.0085`, net `-521.8` total tokens).
3. **Phase E (`880` Calls on `GPT 6 Luna`, `high` Effort): `R-SYS-01` Density & `C-02`/`C-03`/`C-04`**:
   - **`PE-1` (`R-SYS-01` -> T2 + T5)**: Scaling nested behavioral rules from `10 -> 20 -> 50` dropped `strict_all` from **`100.0%` (`80/80`) to `48.8%` (`39/80`, `p = 5.38e-08`) and `58.8%` (`47/80`, `t(15) = -7.34, p = 2.436e-06`, `sign = 0+/16-, p = 3.052e-05`)** while multiplying reasoning tokens **`3.5×` (`256.6 -> 905.3`, `p = 2.746e-12`)** and latency **`1.9×` (`13.09s -> 25.04s`, `p = 2.829e-10`)**. Early primacy rules (`core5_score`) held `1.000` at `10`/`20`/`50` (`rules_05` missed `R02` word cap `34/80` before `R06–R08` section rules stabilized length).
   - **`PE-2` (`C-02`), `PE-3` (`C-03`) & `PE-4` (`C-04`)**: At `~10.9k` noisy log tokens (`PE-2`), `system_only` (`0.885`) and `sandwich_reminder` (`0.870`, `p = 0.6062`) held `100%` (`80/80`) pure formatting compliance (all misses were counting arithmetic); on `16` hard discrete-math puzzles (`PE-3`), `neutral_objective` (`72/80`, `90.0%`) vs `expert_persona` (`73/80`, `91.2%`) confirmed a powered null (`t(15) = 0.22, p = 0.8269`); at `~2.8k` tokens (`PE-4`), Start/Middle/End all scored `80/80` (`100.0%`) on recall and prompt-injection defense.
4. **`PD-1` Powered `N = 5` Replication of `TS-2` & `PD-2` Verbosity Curve (`R-TOOL-05` -> Full `N = 5` T2)**:
   - Replicating `TS-2` across `15` prompts × `5` = `75`/arm (`high` effort) upgraded `R-TOOL-05` from exploratory `N = 1` and revealed that omitting parameter descriptions degrades **both** non-universal spacing (`geo_valid`: `2/75` [`2.7%`] vs `75/75` [`100.0%`], `t(14) = 53.57, p = 1.335e-17`, `sign p = 6.104e-05`) **and** standardized ISO 4217 currencies (`currency_valid`: `53/75` [`70.7%`] vs `75/75` [`100.0%`], `t(14) = 3.08, p = 0.0082`, `sign p = 0.0078`), while lowering reasoning tokens (`25.4 -> 19.8`, `p = 0.0105`).
   - In `PD-2` (`16` prompts × `4` tiers × `5`, `effort = "none"`), `GPT 6 Luna` sustained `80/80` (`100.0%`) strict 6-field compliance even at `bloated_250t` (`2,375.1` prompt tokens, `+1,963` vs `compact_15t`), showing benign verbosity causes **`5.8×` prompt-token bloat** without accuracy degradation at this scale.
5. **`PD-3` (`H-03`), `PD-4` (`H-06`) & `PD-5` (`H-07`) Open Hypothesis Resolutions on `GPT 6 Luna`**:
   - **`PD-3` (Markdown in Tool Descriptions)**: With wording equalized (`16` counterbalanced prompts × `5`), `plain_prose` (`0.950`), `bullet_list` (`0.950`, `p = 1.0000`), and `markdown_headers` (`0.975`, `t(15) = 1.00, p = 0.3332`) yielded no significant routing advantage, while `markdown_headers` added `+43.4` prompt tokens (`+13.6%`, `p = 1.692e-20`) and `+0.38s` latency (`p = 0.0149`).
   - **`PD-4` (Arabic Digits vs Spelled-Out Numbers)**: On a non-ceiling 3-constraint counting suite (`TARa@5 = 0%`), `arabic_digits` (`0.792`, `strict = 2/80`) vs `spelled_words` (`0.801`, `strict = 6/80`) showed zero digit advantage (`t(15) = 0.98, p = 0.3431`; `sign 6+/8-, p = 0.7905`).
   - **`PD-5` (Prompt-Injected JSON Schema vs TypeScript Interfaces)**: Both achieved `80/80` (`100.0%`) exact 4-level nested JSON conformance at `effort = "none"`, while TypeScript interfaces cut prompt tokens by **`-50.4%` (`1,024.2 -> 508.2`, `-516` tokens/call, `sign p = 3.052e-05`)**. (Native API tool declarations still require JSON Schema per `R-TOOL-10`.)
6. **`PC-1` Counterbalanced Symmetric Tool Gaming (`R-TOOL-04` -> T2)**:
   - Eliminated Phase B `PB-2`'s array-position/name confound by swapping `records_lookup_east` and `records_lookup_west` 50/50 across `16` prompts (`80` runs/arm).
   - Under `neutral` and `example_on_second`, the model preferred parallel dual calls (`67/80` and `75/80`, plausible under `east`/`west` shard naming) or Position 0 (`13/80` and `5/80`), choosing `second_tool` exclusively `0/80` times. Appending assertive promotional superlatives flipped exclusive selection of `second_tool` on **`16/16` prompts (`80/80` runs: `40` east + `40` west, exact prompt sign `p = 3.052e-05`)**.
7. **`PC-2` Named Lexical Exclusions vs Affirmative Suggestions & Resolution of `C-01` (`R-SYS-05` -> T2)**:
   - Prompt-level stats in Phase B (`PB-4`, `n = 6` prompts) showed significance for `paired_affirmative` vs `affirmative_only` (`t(5) = 4.00, p = 0.0103`), while `bare_negative` vs `affirmative_only` was underpowered (`t(5) = 2.38, p = 0.0631`).
   - Expanding to `16` prompts across 4 domain clusters in `PC-2` (`N = 80`/arm) confirmed `bare_negative` (`0.988`, `t(15) = 4.06, p = 0.0010`) and `paired_affirmative` (`0.950`, `t(15) = 3.87, p = 0.0015`) decisively outperform `affirmative_only` (`0.650`, `38` forbidden hits). Crucially, `paired_affirmative` showed no accuracy edge over `bare_negative` (`delta = -0.038, t(15) = -1.00, p = 0.3332`).
   - *Design & trace caveats*: `affirmative_only` suggested preferred terms (`"such as..."`) without disclosing the 4-word blacklist (testing constraint specificity + polarity rather than symmetric wording of the same ban), and all 5 negative-arm misses in `PC-2` (`consecutive-failure` on `PC2_04`) were hyphenated compounds matching `\b...\b`.
8. **`PB-1` vs Phase A `SP-4` XML Wording Bug (`R-SYS-08`)**:
   - Phase A's apparent XML penalty was traced to `[P0|P1|P2|P3]` vs `"without brackets"` phrasing (`4/12` vs `12/12` on `c5_severity`). With identical wording in `PB-1`, `flat_markdown` (`0.972`), `flat_xml` (`0.983`, `p = 0.3632`), and `nested_xml` (`0.994`, `p = 0.1019`) showed no XML disadvantage (`c5 = 30/30` in all arms).
9. **`PB-6` `rationale`-First Constrained Decoding (`R-TOOL-11` -> T2 + T4)** & **`PB-3`/`PB-5` Nulls**:
   - At `reasoning_effort = "none"` (`0` reasoning tokens, simulating constrained generation without pre-emission thinking on a reasoning model), `rationale_first` reached `1.000` (`30/30`) vs `0.367` (`11/30`) for `no_rationale` and `rationale_last` (prompt-level parametric **`t(5) = 3.12, p = 0.0261`** across `n = 6` prompts; non-parametric sign `4+/0-, p = 0.1250`). Neutral under `xhigh` (`TS-3`: `15/15`).
   - `PB-3` (`30/30` vs `30/30`) was an uninformative ceiling on `xhigh`; `PB-5` (`29/30` vs `27/30`, `t(5) = -1.00, p = 0.3632`, sign `1+/3-, p = 0.6250`) was an underpowered null showing lower `TARa@5` (`50%` vs `83%`).
