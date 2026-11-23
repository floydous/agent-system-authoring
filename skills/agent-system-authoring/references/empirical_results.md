# Empirical Results: Phase A (`228`), Phase B (`480`) & Phase C (`480`) on `GPT 6 Luna`

## 1. Executive Summary
This report documents all `1,188` live benchmark completions recorded against `GPT 6 Luna` across three experimental phases, adhering strictly to **prompt-level unit-of-analysis hygiene** (zero pooled-repeat Fisher p-values):
- **Phase A (`228` records, `N = 1` run/prompt)**: Initial exploration (`SP-1`–`SP-4`, `TS-1`–`TS-3`) under [`evidence/experiment_harness.py`](https://github.com/floydous/agent-system-authoring/blob/main/evidence/experiment_harness.py). Exposed a prompt-wording bug in `SP-4`, confounds in `TS-1`, and ceiling effects in `SP-1`, `SP-3`, and `TS-3`.
- **Phase B (`480` records, `N = 5` runs/prompt × `6` prompts/suite, `0` errors)**: Deconfounded, non-ceiling suites (`PB-1`–`PB-6`) under [`evidence/phase_b_harness.py`](https://github.com/floydous/agent-system-authoring/blob/main/evidence/phase_b_harness.py), across `xhigh`, `low`, and `none` (`reasoning_tokens = 0`) effort levels.
- **Phase C (`480` records, `N = 5` runs/prompt × `16` prompts/suite, `high` effort, `0` errors)**: Higher-powered, strictly counterbalanced tool-gaming (`PC-1`) and 4-domain lexical-prohibition (`PC-2`) replications under [`evidence/phase_c_harness.py`](https://github.com/floydous/agent-system-authoring/blob/main/evidence/phase_c_harness.py).

All statistics below match [`evidence/stats_recomputed.md`](https://github.com/floydous/agent-system-authoring/blob/main/evidence/stats_recomputed.md) (generated offline by `python evidence/recompute_stats.py`). **Scope Boundary**: Only `GPT 6 Luna` was tested; `Gemini 4 Hydrogen`, `Claude Fable 5.2`, `Claude Opus 5.5`, and `GPT 6.2 Astra` remain unmeasured here.

---

## 2. Phase C Summary Table (`N = 5` Runs/Prompt × `16` Prompts/Suite, `high` Effort)

| Suite | Condition | N | Prompts | Mean Score (Prompt SD) | Raw Runs (Descriptive) | `TARa@5` | Prompt-Level Paired *t* (`df=15`) | Prompt-Level Exact Sign Test | Mean RTok | Result Summary |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- | :--- | :---: | :--- |
| **PC-1** | `neutral` | 80 | 16 | `0.000` (`0.000`) | `0/80` exclusive `second` (`67/80` both) | `100%` | Baseline | Baseline | `6.7` | `13/80` pos-0, `67/80` parallel-both |
| **PC-1** | `assertive_on_second` | 80 | 16 | **`1.000`** (`0.000`) | **`80/80`** (`40` east + `40` west) | `100%` | `+1.000` (`sd_diff=0`) | **`16+/0- (p=3.052e-05)`** | `0.0` | **T2 confirmed (`R-TOOL-04`)** |
| **PC-1** | `example_on_second` | 80 | 16 | `0.000` (`0.000`) | `0/80` exclusive (`75/80` both) | `100%` | `0.000` (no diff) | `0+/0- (p=1.0000)` | `0.9` | Neutral example: zero hijack |
| **PC-2** | `affirmative_only` | 80 | 16 | `0.650` (`0.354`) | `52/80` (`65.0%`, `38` hits) | `44%` | Baseline | Baseline | `133.9` | Weak without explicit `Do NOT` |
| **PC-2** | `bare_negative` | 80 | 16 | **`0.988`** (`0.050`) | **`79/80`** (`98.8%`, `1` hit) | `94%` | **`+0.338, t(15)=4.06, p=0.0010`** | **`11+/0- (p=0.0010)`** | `219.6` | **T2 confirmed (`R-SYS-05`)** |
| **PC-2** | `paired_affirmative` | 80 | 16 | **`0.950`** (`0.200`) | **`76/80`** (`95.0%`, `4` hits) | `94%` | **`+0.300, t(15)=3.87, p=0.0015`** | **`11+/0- (p=0.0010)`** | `247.8` | Beats affirmative; `p=0.3332` vs bare |

---

## 3. Phase B Summary Table (`N = 5` Runs/Prompt × `6` Prompts/Suite, Prompt-Level Inference)

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

## 4. Key Discoveries Across Phases A, B & C

1. **`PC-1` Counterbalanced Symmetric Tool Gaming (`R-TOOL-04` -> T2)**:
   - Eliminated Phase B `PB-2`'s array-position/name confound by swapping `records_lookup_east` and `records_lookup_west` 50/50 across `16` prompts (`80` runs/arm).
   - Under `neutral` and `example_on_second`, the model preferred parallel dual calls (`67/80` and `75/80`, plausible under `east`/`west` shard naming) or Position 0 (`13/80` and `5/80`), choosing `second_tool` exclusively `0/80` times. Appending assertive promotional superlatives flipped exclusive selection of `second_tool` on **`16/16` prompts (`80/80` runs: `40` east + `40` west, exact prompt sign `p = 3.052e-05`)**.
2. **`PC-2` Named Lexical Exclusions vs Affirmative Suggestions & Resolution of `C-01` (`R-SYS-05` -> T2)**:
   - Prompt-level stats in Phase B (`PB-4`, `n = 6` prompts) showed significance for `paired_affirmative` vs `affirmative_only` (`t(5) = 4.00, p = 0.0103`), while `bare_negative` vs `affirmative_only` was underpowered (`t(5) = 2.38, p = 0.0631`).
   - Expanding to `16` prompts across 4 domain clusters in `PC-2` (`N = 80`/arm) confirmed `bare_negative` (`0.988`, `t(15) = 4.06, p = 0.0010`) and `paired_affirmative` (`0.950`, `t(15) = 3.87, p = 0.0015`) decisively outperform `affirmative_only` (`0.650`, `38` forbidden hits). Crucially, `paired_affirmative` showed no accuracy edge over `bare_negative` (`delta = -0.038, t(15) = -1.00, p = 0.3332`).
   - *Design & trace caveats*: `affirmative_only` suggested preferred terms (`"such as..."`) without disclosing the 4-word blacklist (testing constraint specificity + polarity rather than symmetric wording of the same ban), and all 5 negative-arm misses in `PC-2` (`consecutive-failure` on `PC2_04`) were hyphenated compounds matching `\b...\b`.
3. **`PB-1` vs Phase A `SP-4` XML Wording Bug (`R-SYS-08`)**:
   - Phase A's apparent XML penalty was traced to `[P0|P1|P2|P3]` vs `"without brackets"` phrasing (`4/12` vs `12/12` on `c5_severity`). With identical wording in `PB-1`, `flat_markdown` (`0.972`), `flat_xml` (`0.983`, `p = 0.3632`), and `nested_xml` (`0.994`, `p = 0.1019`) showed no XML disadvantage (`c5 = 30/30` in all arms).
4. **`PB-6` `rationale`-First Constrained Decoding (`R-TOOL-11` -> T2 + T4)**:
   - At `reasoning_effort = "none"` (`0` reasoning tokens, simulating constrained generation without pre-emission thinking on a reasoning model), `rationale_first` reached `1.000` (`30/30`) vs `0.367` (`11/30`) for `no_rationale` and `rationale_last` (prompt-level parametric **`t(5) = 3.12, p = 0.0261`** across `n = 6` prompts; non-parametric sign `4+/0-, p = 0.1250`). Neutral under `xhigh` (`TS-3`: `15/15`).
5. **`TS-2` Unstated Parameter Format Failure (`R-TOOL-05` -> T2 Narrowed, `N = 1`)** & **`PB-3`/`PB-5` Nulls**:
   - In Phase A `TS-2` (`15` matched prompts, `N = 1` run/prompt), universal ISO timestamps (`15/15`), currencies (`12/15`, sign `p = 0.2500`), and decimal coordinates (`15/15`, e.g. `"37.7793, -122.4192"`) were inferred, whereas omitting descriptions failed `0/15` vs `15/15` purely on the unstated no-space `"lat,lon"` convention (matched-pair exact sign / McNemar `p = 6.104e-05`).
   - `PB-3` (`30/30` vs `30/30`) was an uninformative ceiling on `xhigh`; `PB-5` (`29/30` vs `27/30`, `t(5) = -1.00, p = 0.3632`, sign `1+/3-, p = 0.6250`) was an underpowered null showing lower `TARa@5` (`50%` vs `83%`).
