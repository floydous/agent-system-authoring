# Evaluation Suite v3 Results (`evals/evals.json`)

- **Target Model**: `GPT 6 Luna` (run `20261123_032542_evals_v3`, `0` errors across `440` trace records)
- **Iterations**: `N = 5` runs per prompt
- **Unit-of-Analysis Hygiene**: All hypothesis tests operate strictly on prompt/task-level means (`df = num_tasks - 1`).
- **Context Disclosure**: Part B `with_skill` runs simulate progressive disclosure by supplying `SKILL.md` plus the single task-matched reference guide and starter template.
- **Raw Traces**: `evidence/raw_evals/results_evals_v3.jsonl` (`440` records including `model`, sanitized `request_payload`, `reasoning_tokens`, and `total_tokens`)

## 1. Hard Triggering Accuracy (9-Skill Registry & Solo-Skill Stress Test)

### 1.1 9-Skill Registry (`32` Prompts × `5` = `160` Calls, Generic Distractors)
- **Positive Triggers (6 plain-English + 6 technical)**: `TP = 60/60`, `FN = 0/60`
- **Distractor Negatives (`10` prompts)**: `50/50` rejected (`FP = 0`)
- **Unmatched `'none'` Negatives (`10` overlapping prompts)**: `45/50` rejected (`FP = 5`, selected `'none'` cleanly: 42/50)
- **Overall Precision**: `0.9231` | **Recall**: `1.0000` | **F1**: `0.9600`

### 1.2 Solo-Skill Precision Stress Test (`10` `'none'` Prompts × `5` = `50` Calls, No Distractors)
- **Result**: `49/50` (`98.0%`) correctly stayed at `'none'` (`FP = 1`).

| Eval ID | Type | Registry Pass (`N=5`) | `TARa@5` | Registry Selections |
| :--- | :--- | :---: | :---: | :--- |
| `trigger_neg_01_postgres_select` | `trigger_negative` | 5/5 (100%) | 1/1 (100%) | `postgres-sql` |
| `trigger_neg_02_postgres_ddl` | `trigger_negative` | 5/5 (100%) | 1/1 (100%) | `postgres-sql` |
| `trigger_neg_03_python_keyerror` | `trigger_negative` | 5/5 (100%) | 1/1 (100%) | `python-debugging` |
| `trigger_neg_04_live_stripe_refund` | `trigger_negative` | 5/5 (100%) | 1/1 (100%) | `stripe-billing` |
| `trigger_neg_05_react_drawer_ui` | `trigger_negative` | 5/5 (100%) | 1/1 (100%) | `react-frontend` |
| `trigger_neg_06_git_squash_tag` | `trigger_negative` | 5/5 (100%) | 1/1 (100%) | `git-ops` |
| `trigger_neg_07_repo_readme` | `trigger_negative` | 5/5 (100%) | 1/1 (100%) | `docs-readme` |
| `trigger_neg_08_github_actions_pytest` | `trigger_negative` | 5/5 (100%) | 1/1 (100%) | `ci-cd-pipelines` |
| `trigger_neg_09_dbt_incremental` | `trigger_negative` | 5/5 (100%) | 1/1 (100%) | `dbt-analytics` |
| `trigger_neg_10_python_unicode_error` | `trigger_negative` | 5/5 (100%) | 1/1 (100%) | `python-debugging` |
| `trigger_none_01_app_config_json_schema` | `trigger_negative_none` | 5/5 (100%) | 1/1 (100%) | `none` |
| `trigger_none_02_pydantic_csv_model` | `trigger_negative_none` | 5/5 (100%) | 0/1 (0%) | `none, python-debugging` |
| `trigger_none_03_openapi_rest_spec` | `trigger_negative_none` | 0/5 (0%) | 1/1 (100%) | `agent-system-authoring` |
| `trigger_none_04_qdrant_rag_tuning` | `trigger_negative_none` | 5/5 (100%) | 1/1 (100%) | `none` |
| `trigger_none_05_summarize_paper` | `trigger_negative_none` | 5/5 (100%) | 1/1 (100%) | `none` |
| `trigger_none_06_employee_handbook` | `trigger_negative_none` | 5/5 (100%) | 0/1 (0%) | `docs-readme, none` |
| `trigger_none_07_cover_letter_edit` | `trigger_negative_none` | 5/5 (100%) | 1/1 (100%) | `none` |
| `trigger_none_08_api_pricing_sheet` | `trigger_negative_none` | 5/5 (100%) | 1/1 (100%) | `none` |
| `trigger_none_09_graphql_schema` | `trigger_negative_none` | 5/5 (100%) | 1/1 (100%) | `none` |
| `trigger_none_10_k8s_network_policy` | `trigger_negative_none` | 5/5 (100%) | 1/1 (100%) | `none` |
| `trigger_pos_01_plain_injection_guard` | `trigger_positive` | 5/5 (100%) | 1/1 (100%) | `agent-system-authoring` |
| `trigger_pos_02_plain_tool_blurb_hijack` | `trigger_positive` | 5/5 (100%) | 1/1 (100%) | `agent-system-authoring` |
| `trigger_pos_03_plain_fast_model_math_params` | `trigger_positive` | 5/5 (100%) | 1/1 (100%) | `agent-system-authoring` |
| `trigger_pos_04_plain_word_ban_rules` | `trigger_positive` | 5/5 (100%) | 1/1 (100%) | `agent-system-authoring` |
| `trigger_pos_05_plain_multi_provider_funcs` | `trigger_positive` | 5/5 (100%) | 1/1 (100%) | `agent-system-authoring` |
| `trigger_pos_06_plain_reusable_skill_folder` | `trigger_positive` | 5/5 (100%) | 1/1 (100%) | `agent-system-authoring` |
| `trigger_pos_07_tech_strict_sql_schema` | `trigger_positive` | 5/5 (100%) | 1/1 (100%) | `agent-system-authoring` |
| `trigger_pos_08_tech_legacy_prompt_audit` | `trigger_positive` | 5/5 (100%) | 1/1 (100%) | `agent-system-authoring` |
| `trigger_pos_09_tech_catalog_enum_scaling` | `trigger_positive` | 5/5 (100%) | 1/1 (100%) | `agent-system-authoring` |
| `trigger_pos_10_tech_skill_md_refactor` | `trigger_positive` | 5/5 (100%) | 1/1 (100%) | `agent-system-authoring` |
| `trigger_pos_11_tech_prompt_eval_design` | `trigger_positive` | 5/5 (100%) | 1/1 (100%) | `agent-system-authoring` |
| `trigger_pos_12_tech_legal_prompt_boundaries` | `trigger_positive` | 5/5 (100%) | 1/1 (100%) | `agent-system-authoring` |

## 2. Objective Downstream Functional & Structural Execution (`8` Tasks × `2` Arms × `5` Runs)

| Task ID | Probe Description | `baseline` Pass Rate | `with_skill` Pass Rate | Task Delta |
| :--- | :--- | :---: | :---: | :---: |
| `comp_01_support_injection_system_prompt` | CRM injection resistance + `STATUS: READY` | 5/5 (100%) | 4/5 (80%) | **-0.20** |
| `comp_03_code_review_json_prohibition` | Raw JSON dict + zero forbidden words | 5/5 (100%) | 5/5 (100%) | **+0.00** |
| `comp_04_legal_pdf_injection_prompt` | Vendor PDF injection + 3 clauses | 5/5 (100%) | 5/5 (100%) | **+0.00** |
| `comp_05_disambiguate_two_support_tools` | OpenAI wire shape + SQL vs policy KB routing | 5/5 (100%) | 5/5 (100%) | **+0.00** |
| `comp_06_logistics_custom_format_tool` | OpenAI strict wire + exact no-space `lat,lon` call | 5/5 (100%) | 5/5 (100%) | **+0.00** |
| `comp_07_non_reasoning_refund_tool` | Zero-reasoning arithmetic (`4650c`, `17d`, valid dates) | 4/5 (80%) | 5/5 (100%) | **+0.20** |
| `comp_08_fix_gamed_search_tools` | OpenAI wire shape + rebalanced PDF vs wiki routing | 5/5 (100%) | 5/5 (100%) | **+0.00** |
| `comp_09_skill_package_data_auditing` | Deterministic `agentskills.io` spec & hygiene audit | 1/5 (20%) | 5/5 (100%) | **+0.80** |

**Task-Level Downstream Functional Summary (`n = 8` tasks, `df = 7`)**: `baseline` = `0.875` vs `with_skill` = `0.975` (delta=+0.100, t(7)=0.94, p=0.3807; sign=2+/1- (p=1.0000)).

## 3. Counterbalanced 50/50 Blinded Pairwise Judge (`10` Tasks × `5` Pairs = `50` Judgments)

- **Position Balance**: `with_skill` in Position A `25/50`, `baseline` in Position A `25/50` (`25/25` exact counterbalance).
- **Position & Internal Consistency Audit**: Score-derived Position A wins `31/50` vs Position B `17/50`; raw-winner vs score-winner disagreements `2/50` (resolved strictly to dimension-score winner). *Caveat: same-family judge (`GPT 6 Luna`).*

| Task ID | `baseline` Mean Score | `with_skill` Mean Score | Delta | Score-Derived Wins (`skill` / `base` / `tie`) |
| :--- | :---: | :---: | :---: | :---: |
| `comp_01_support_injection_system_prompt` | 0.870 | 0.890 | **+0.020** | 3 / 2 / 0 |
| `comp_02_refactor_legacy_finance_prompt` | 0.820 | 0.940 | **+0.120** | 5 / 0 / 0 |
| `comp_03_code_review_json_prohibition` | 0.780 | 0.920 | **+0.140** | 5 / 0 / 0 |
| `comp_04_legal_pdf_injection_prompt` | 0.930 | 0.930 | **+0.000** | 2 / 2 / 1 |
| `comp_05_disambiguate_two_support_tools` | 0.830 | 0.670 | **-0.160** | 0 / 5 / 0 |
| `comp_06_logistics_custom_format_tool` | 0.810 | 0.710 | **-0.100** | 2 / 3 / 0 |
| `comp_07_non_reasoning_refund_tool` | 0.790 | 0.740 | **-0.050** | 2 / 3 / 0 |
| `comp_08_fix_gamed_search_tools` | 0.870 | 0.910 | **+0.040** | 4 / 1 / 0 |
| `comp_09_skill_package_data_auditing` | 0.870 | 0.780 | **-0.090** | 0 / 4 / 1 |
| `comp_10_skill_package_postmortem_review` | 0.860 | 0.780 | **-0.080** | 1 / 4 / 0 |

**Task-Level Blinded Judge Summary (`n = 10` tasks, `df = 9`)**: `baseline` = `0.843` vs `with_skill` = `0.827` (delta=-0.016, t(9)=-0.52, p=0.6173; sign=4+/5- (p=1.0000); score-derived judgments `24` with_skill / `24` baseline / `2` tie).
