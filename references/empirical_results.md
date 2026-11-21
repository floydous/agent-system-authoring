# Empirical Results: Phase A (`N = 1`) & Phase B (`N = 5`) on `GPT 6 Luna`

## 1. Executive Summary
This report documents all `708` live empirical completions recorded against `GPT 6 Luna` across two phases:
- **Phase A (`228` records, `N = 1` run/prompt)**: Initial exploration (`SP-1`–`SP-4`, `TS-1`–`TS-3`) under [`evidence/experiment_harness.py`](../evidence/experiment_harness.py). Inspection exposed a prompt-wording bug in `SP-4`, four confounds in `TS-1`, and ceiling effects in `SP-1`, `SP-3`, and `TS-3`.
- **Phase B (`480` records, `N = 5` runs/prompt, `0` errors)**: Deconfounded, non-ceiling replications (`PB-1`–`PB-6`) under [`evidence/phase_b_harness.py`](../evidence/phase_b_harness.py), testing `xhigh`, `low`, and `none` (`reasoning_tokens = 0`) effort levels.

All statistics below are computed directly from raw JSONL files via `python evidence/recompute_stats.py` and saved in [`evidence/stats_recomputed.md`](../evidence/stats_recomputed.md). **Scope Boundary**: Only `GPT 6 Luna` was available; `Gemini 4 Hydrogen`, `Claude Fable 5.2`, `Claude Opus 5.5`, and `GPT 6.2 Astra` were not executed.

---

## 2. Phase B Summary Table (`N = 5` Runs/Prompt, `480` Records)

| Suite | Condition | N | Prompts | Runs/Prompt | Mean Score | Std Dev | TARa@5 | Score vs Baseline (Paired t / p) | Binary Fisher Exact p | Mean Reasoning Tok | Result Summary |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **PB-1** (`xhigh`) | `flat_markdown` | 30 | 6 | 5 | 0.972 | 0.063 | 17% | Baseline | Baseline | 1813.4 | Baseline (`c5=30/30`) |
| **PB-1** (`xhigh`) | `flat_xml` | 30 | 6 | 5 | 0.983 | 0.051 | 67% | `+0.011` (`t=1.00, p=0.3632`) | non-binary | 1862.6 | Not significant |
| **PB-1** (`xhigh`) | `nested_xml` | 30 | 6 | 5 | 0.994 | 0.030 | 83% | `+0.022` (`t=2.00, p=0.1019`) | non-binary | 1824.1 | Not significant |
| **PB-2** (`xhigh`) | `neutral_ab` | 30 | 6 | 5 | 0.000 | 0.000 | 100% | Baseline | Baseline | 8.9 | `beta` chosen `0/30` |
| **PB-2** (`xhigh`) | `assertive_on_beta` | 30 | 6 | 5 | 1.000 | 0.000 | 100% | `+1.000` | **`30/30` vs `0/30` (`p=1.691e-17`)** | 0.4 | **T2 confirmed (`R-TOOL-04`)** |
| **PB-2** (`xhigh`) | `example_on_beta` | 30 | 6 | 5 | 0.000 | 0.000 | 100% | `0.000` (no diff) | `0/30` vs `0/30` (`p=1.0000`) | 8.5 | Example alone: zero hijack |
| **PB-3** (`xhigh`) | `system_only` | 30 | 6 | 5 | 1.000 | 0.000 | 100% | Baseline | Baseline | 189.2 | Ceiling |
| **PB-3** (`xhigh`) | `sandwich_reminder` | 30 | 6 | 5 | 1.000 | 0.000 | 100% | `0.000` (no diff) | `30/30` vs `30/30` (`p=1.0000`) | 189.9 | Uninformative ceiling |
| **PB-4** (`xhigh`) | `bare_negative` | 30 | 6 | 5 | 0.900 | 0.305 | 83% | Baseline | Baseline | 578.5 | `27/30` clean |
| **PB-4** (`xhigh`) | `affirmative_only` | 30 | 6 | 5 | 0.467 | 0.507 | 17% | `-0.433` (`t=-2.38, p=0.0631`) | **`14/30` vs `27/30` (`p=0.0006`)** | 669.6 | Affirmative-only underperforms |
| **PB-4** (`xhigh`) | `paired_affirmative` | 30 | 6 | 5 | 1.000 | 0.000 | 100% | `+0.100` (`t=1.00, p=0.3632`) | `30/30` vs `27/30` (`p=0.2373`) | 582.7 | `30/30` vs `14/30` **`p=1.944e-06`** |
| **PB-5** (`low`) | `neutral_objective` | 30 | 6 | 5 | 0.967 | 0.183 | 83% | Baseline | Baseline | 81.1 | `29/30` correct |
| **PB-5** (`low`) | `expert_persona` | 30 | 6 | 5 | 0.900 | 0.305 | 50% | `-0.067` (`t=-1.00, p=0.3632`) | `27/30` vs `29/30` (`p=0.6120`) | 82.9 | Zero benefit; lower stability |
| **PB-6** (`none`) | `no_rationale` | 30 | 6 | 5 | 0.367 | 0.490 | 83% | Baseline | Baseline | 0.0 | `11/30` (`rtok=0`) |
| **PB-6** (`none`) | `rationale_first` | 30 | 6 | 5 | 1.000 | 0.000 | 100% | **`+0.633` (`t=3.12, p=0.0261`)** | **`30/30` vs `11/30` (`p=5.343e-08`)** | 0.0 | **T2 confirmed (`R-TOOL-11`)** |
| **PB-6** (`none`) | `rationale_last` | 30 | 6 | 5 | 0.367 | 0.490 | 83% | `0.000` (no diff) | `11/30` vs `11/30` (`p=1.0000`) | 0.0 | Zero benefit after action fields |

---

## 3. Phase B Key Findings & Revisions to Phase A

### 3.1 `PB-1` vs Phase A `SP-4`: Resolving the XML Prompt-Wording Bug (`R-SYS-08`)
- **Phase A Defect Discovered**: Per-constraint audit of Phase A `SP-4` traces showed `raw_text` scored `12/12` on `c5_severity` (`"SEVERITY: [LEVEL] where LEVEL is one of P0, P1, P2, or P3"`), whereas `xml_containers` scored only **`4/12`** because `XML_TEXT` literally wrote `"Include the line: SEVERITY: [P0|P1|P2|P3]"`—causing 8/12 completions to echo literal brackets (`SEVERITY: [P0|P1|P2|P3]`). That single wording discrepancy accounted for virtually the entire `-0.139` Phase A gap.
- **Phase B (`PB-1`) Result**: Using identical constraint wording across all three structural formats (`c5_severity = 30/30` everywhere), `flat_markdown` (`0.972`), `flat_xml` (`0.983`, `p = 0.3632`), and `nested_xml` (`0.994`, `p = 0.1019`) showed **no statistically significant penalty for XML containers** on `GPT 6 Luna (xhigh)`.

### 3.2 `PB-2` vs Phase A `TS-1`: Isolating Assertive Tool Gaming (`R-TOOL-04` -> **T2**)
- Phase B eliminated Phase A's confounds by pairing symmetric tools (`records_provider_alpha` vs `records_provider_beta`) with identical neutral baselines (`beta` selected `0/30` at baseline).
- Adding a neutral usage example alone (`example_on_beta`) produced `0/30` shifts (`p = 1.0000`). Adding assertive promotional phrasing (`assertive_on_beta`) caused **`30/30` (`100.0%`) preference hijacking** (`p = 1.691e-17`), confirming `R-TOOL-04` at **T2** on `GPT 6 Luna`.

### 3.3 `PB-4` vs Phase A `SP-2`: Prohibitions Beat Affirmative-Only Phrasing (`R-SYS-05` -> **T2** Narrowed)
- Asking `GPT 6 Luna (xhigh)` to avoid four high-frequency domain words using **only affirmative substitutes** (`affirmative_only`, no `Do NOT`) resulted in `14/30` (`46.7%`) pass rate (`19` forbidden-word violations).
- Explicit negative rules succeeded cleanly: `bare_negative` achieved `27/30` (`90.0%`, `p = 0.0006` vs `affirmative_only`) and `paired_affirmative` achieved `30/30` (`100.0%`, `p = 1.944e-06` vs `affirmative_only`). Note that `paired_affirmative` (`30/30`) vs `bare_negative` (`27/30`, `p = 0.2373`) is directionally higher but not significant at `alpha = 0.05`.

### 3.4 `PB-6` vs Phase A `TS-3`: Proving Left-to-Right `rationale`-First Decoding (`R-TOOL-11` -> **T2**)
- At `reasoning_effort = "none"` (`0` pre-emission reasoning tokens across all 90 runs), strict JSON tool calls without an upfront explanation scored **`11/30` (`36.7%`)** for both `no_rationale` and `rationale_last`.
- Moving `rationale` to the first schema property (`rationale_first`) raised exact multi-step calculation accuracy to **`30/30` (`100.0%`)** (paired `t = 3.12, p = 0.0261`; Fisher exact **`p = 5.343e-08`** vs both alternatives). Together with Phase A `TS-3` (`15/15` at `xhigh`), this directly confirms both halves of `R-TOOL-11`: parameter ordering is critical when pre-emission thinking is absent, and neutral when extended test-time thinking runs first.

### 3.5 `PB-3` & `PB-5`: Prospective Memory Ceiling & Non-Ceiling Persona Test
- **`PB-3` (`SP-1`)**: Even with ~1,200 words of noisy log distractors and strict formatting invariants, `GPT 6 Luna (xhigh)` scored `30/30` in both `system_only` and `sandwich_reminder` (ceiling/uninformative).
- **`PB-5` (`SP-3`)**: Running tricky combinatorics/modular puzzles at `reasoning_effort = "low"` eliminated the ceiling: `neutral_objective` scored `29/30` (`96.7%`, `TARa@5 = 83%`) vs `expert_persona` `27/30` (`90.0%`, `TARa@5 = 50%`, Fisher `p = 0.6120`, reasoning tokens `p = 0.9211`). Expert personas conferred zero accuracy benefit.

---

## 4. Phase A Summary Reference (`228` Records, `N = 1` Run/Prompt)

Retained in full inside [`evidence/stats_recomputed.md`](../evidence/stats_recomputed.md):
- **`TS-2` (`R-TOOL-05`, **T2**)**: Without parameter descriptions, `GPT 6 Luna` inferred ISO timestamps (`15/15`) and ISO 4217 currencies (`12/15`, `p = 0.2241`), while failing `0/15` vs `15/15` (`p = 1.289e-08`) on the unstated no-space `"lat,lon"` format rule.
- **`SP-1` (`12/12`), `SP-2` (`11/12`, token `p = 0.0574`), `SP-3` (`12/12`, token `p = 0.4124`), `TS-1` (`12/15 -> 15/15`, `p = 0.2241`), `TS-3` (`15/15`)**, and buggy **`SP-4` (`c5_severity = 4/12`)** are preserved untouched under `evidence/raw/` for full reproducibility.
