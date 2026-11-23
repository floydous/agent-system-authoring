# Evaluation Suite v4 Results (`evals/evals.json`)

- **Target Model**: `GPT 6 Luna` (run `20261123_040036_evals_v4`, `0` errors across `490` trace records)
- **Iterations**: `N = 5` runs per prompt
- **Unit-of-Analysis Hygiene**: All hypothesis tests operate strictly on prompt/task-level means (`df = num_tasks - 1`).
- **Context Disclosure**: Part B `with_skill` runs simulate progressive disclosure by supplying `SKILL.md` plus the single task-matched reference guide and default starter template.
- **Raw Traces**: `evidence/raw_evals/results_evals_v4.jsonl` (`490` records including `model`, sanitized `request_payload`, `reasoning_tokens`, and `total_tokens`)

## 1. Hard Triggering Accuracy (9-Skill Registry & Solo-Skill Stress Test, Reason-First Routing)

### 1.1 9-Skill Registry (`32` Prompts × `5` = `160` Calls, Generic Distractors)
- **Positive Triggers (6 plain-English + 6 technical)**: `TP = 60/60`, `FN = 0/60`
- **Distractor Negatives (`10` prompts)**: `50/50` rejected (`FP = 0`)
- **Unmatched `'none'` Negatives (`10` overlapping prompts)**: `50/50` rejected (`FP = 0`, selected `'none'` cleanly: 47/50)
- **Overall Precision**: `1.0000` | **Recall**: `1.0000` | **F1**: `1.0000`

### 1.2 Solo-Skill Precision Stress Test (`10` `'none'` Prompts × `5` = `50` Calls, No Distractors)
- **Result**: `50/50` (`100.0%`) correctly stayed at `'none'` (`FP = 0`).

| Eval ID | Type | Target Match / Rejected (`N=5`) | Exact `'none'` | `TARa@5` | Registry Selections |
| :--- | :--- | :---: | :---: | :---: | :--- |
| `trigger_neg_01_postgres_select` | `trigger_negative` | 5/5 (100%) | — | 1/1 (100%) | `postgres-sql` |
| `trigger_neg_02_postgres_ddl` | `trigger_negative` | 5/5 (100%) | — | 1/1 (100%) | `postgres-sql` |
| `trigger_neg_03_python_keyerror` | `trigger_negative` | 5/5 (100%) | — | 1/1 (100%) | `python-debugging` |
| `trigger_neg_04_live_stripe_refund` | `trigger_negative` | 5/5 (100%) | — | 1/1 (100%) | `stripe-billing` |
| `trigger_neg_05_react_drawer_ui` | `trigger_negative` | 5/5 (100%) | — | 1/1 (100%) | `react-frontend` |
| `trigger_neg_06_git_squash_tag` | `trigger_negative` | 5/5 (100%) | — | 1/1 (100%) | `git-ops` |
| `trigger_neg_07_repo_readme` | `trigger_negative` | 5/5 (100%) | — | 1/1 (100%) | `docs-readme` |
| `trigger_neg_08_github_actions_pytest` | `trigger_negative` | 5/5 (100%) | — | 1/1 (100%) | `ci-cd-pipelines` |
| `trigger_neg_09_dbt_incremental` | `trigger_negative` | 5/5 (100%) | — | 1/1 (100%) | `dbt-analytics` |
| `trigger_neg_10_python_unicode_error` | `trigger_negative` | 5/5 (100%) | — | 1/1 (100%) | `python-debugging` |
| `trigger_none_01_app_config_json_schema` | `trigger_negative_none` | 5/5 (100%) | 5/5 (100%) | 1/1 (100%) | `none` |
| `trigger_none_02_pydantic_csv_model` | `trigger_negative_none` | 5/5 (100%) | 5/5 (100%) | 1/1 (100%) | `none` |
| `trigger_none_03_openapi_rest_spec` | `trigger_negative_none` | 5/5 (100%) | 5/5 (100%) | 1/1 (100%) | `none` |
| `trigger_none_04_qdrant_rag_tuning` | `trigger_negative_none` | 5/5 (100%) | 5/5 (100%) | 1/1 (100%) | `none` |
| `trigger_none_05_summarize_paper` | `trigger_negative_none` | 5/5 (100%) | 5/5 (100%) | 1/1 (100%) | `none` |
| `trigger_none_06_employee_handbook` | `trigger_negative_none` | 5/5 (100%) | 2/5 (40%) | 0/1 (0%) | `docs-readme, none` |
| `trigger_none_07_cover_letter_edit` | `trigger_negative_none` | 5/5 (100%) | 5/5 (100%) | 1/1 (100%) | `none` |
| `trigger_none_08_api_pricing_sheet` | `trigger_negative_none` | 5/5 (100%) | 5/5 (100%) | 1/1 (100%) | `none` |
| `trigger_none_09_graphql_schema` | `trigger_negative_none` | 5/5 (100%) | 5/5 (100%) | 1/1 (100%) | `none` |
| `trigger_none_10_k8s_network_policy` | `trigger_negative_none` | 5/5 (100%) | 5/5 (100%) | 1/1 (100%) | `none` |
| `trigger_pos_01_plain_injection_guard` | `trigger_positive` | 5/5 (100%) | — | 1/1 (100%) | `agent-system-authoring` |
| `trigger_pos_02_plain_tool_blurb_hijack` | `trigger_positive` | 5/5 (100%) | — | 1/1 (100%) | `agent-system-authoring` |
| `trigger_pos_03_plain_fast_model_math_params` | `trigger_positive` | 5/5 (100%) | — | 1/1 (100%) | `agent-system-authoring` |
| `trigger_pos_04_plain_word_ban_rules` | `trigger_positive` | 5/5 (100%) | — | 1/1 (100%) | `agent-system-authoring` |
| `trigger_pos_05_plain_multi_provider_funcs` | `trigger_positive` | 5/5 (100%) | — | 1/1 (100%) | `agent-system-authoring` |
| `trigger_pos_06_plain_reusable_skill_folder` | `trigger_positive` | 5/5 (100%) | — | 1/1 (100%) | `agent-system-authoring` |
| `trigger_pos_07_tech_strict_sql_schema` | `trigger_positive` | 5/5 (100%) | — | 1/1 (100%) | `agent-system-authoring` |
| `trigger_pos_08_tech_legacy_prompt_audit` | `trigger_positive` | 5/5 (100%) | — | 1/1 (100%) | `agent-system-authoring` |
| `trigger_pos_09_tech_catalog_enum_scaling` | `trigger_positive` | 5/5 (100%) | — | 1/1 (100%) | `agent-system-authoring` |
| `trigger_pos_10_tech_skill_md_refactor` | `trigger_positive` | 5/5 (100%) | — | 1/1 (100%) | `agent-system-authoring` |
| `trigger_pos_11_tech_prompt_eval_design` | `trigger_positive` | 5/5 (100%) | — | 1/1 (100%) | `agent-system-authoring` |
| `trigger_pos_12_tech_legal_prompt_boundaries` | `trigger_positive` | 5/5 (100%) | — | 1/1 (100%) | `agent-system-authoring` |

## 2. Objective Downstream Functional & Structural Execution (`8` Tasks × `2` Arms × `5` Runs)

| Task ID | Probe Description | `baseline` Pass Rate | `with_skill` Pass Rate | Task Delta |
| :--- | :--- | :---: | :---: | :---: |
| `comp_01_support_injection_system_prompt` | CRM injection resistance + `STATUS: READY` | 3/5 (60%) | 5/5 (100%) | **+0.40** |
| `comp_03_code_review_json_prohibition` | Raw JSON dict + zero forbidden words | 5/5 (100%) | 4/5 (80%) | **-0.20** |
| `comp_04_legal_pdf_injection_prompt` | Vendor PDF injection + 3 clauses | 5/5 (100%) | 5/5 (100%) | **+0.00** |
| `comp_05_disambiguate_two_support_tools` | OpenAI wire shape + SQL vs policy KB routing | 5/5 (100%) | 5/5 (100%) | **+0.00** |
| `comp_06_logistics_custom_format_tool` | OpenAI strict wire + exact no-space `lat,lon` call | 5/5 (100%) | 5/5 (100%) | **+0.00** |
| `comp_07_non_reasoning_refund_tool` | Zero-reasoning arithmetic (`4650c`, `17d`, valid dates) | 5/5 (100%) | 5/5 (100%) | **+0.00** |
| `comp_08_fix_gamed_search_tools` | OpenAI wire shape + rebalanced PDF vs wiki routing | 5/5 (100%) | 5/5 (100%) | **+0.00** |
| `comp_09_skill_package_data_auditing` | T1 `agentskills.io` + PEP 723 + general hygiene | 5/5 (100%) | 5/5 (100%) | **+0.00** |

- **`comp_09` Decomposition (`T1` Spec vs Packaging Hygiene)**: `T1 agentskills.io + PEP 723` (`baseline` `5/5` vs `with_skill` `5/5`); `general packaging hygiene` (`baseline` `5/5` vs `with_skill` `5/5`).
- **Task-Level Downstream Functional Summary (`n = 8` tasks, `df = 7`)**: `baseline` = `0.950` vs `with_skill` = `0.975` (delta=+0.025, t(7)=0.42, p=0.6845; sign=1+/1- (p=1.0000)).

## 3. Dual-Order `(A,B) + (B,A)` Swap-Consistent Blinded Judge (`10` Tasks × `5` Pairs × `2` Orders = `100` Judgments)

- **Position & Swap-Consistency Audit**: Raw Position A wins `54/100`, Position B `30/100`, Ties `16/100`; exact A↔B position flips `12/50`; raw-winner vs score-winner disagreements `17/100` (resolved strictly to dimension-score winner). *Caveat: same-family judge (`GPT 6 Luna`).*

| Task ID | `baseline` Mean Score | `with_skill` Mean Score | Delta | Swap-Consistent (`skill` / `base` / `flip_or_tie`) |
| :--- | :---: | :---: | :---: | :---: |
| `comp_01_support_injection_system_prompt` | 0.890 | 0.885 | **-0.005** | 0 / 1 / 4 |
| `comp_02_refactor_legacy_finance_prompt` | 0.840 | 0.930 | **+0.090** | 4 / 0 / 1 |
| `comp_03_code_review_json_prohibition` | 0.815 | 0.805 | **-0.010** | 2 / 2 / 1 |
| `comp_04_legal_pdf_injection_prompt` | 0.895 | 0.915 | **+0.020** | 0 / 1 / 4 |
| `comp_05_disambiguate_two_support_tools` | 0.765 | 0.810 | **+0.045** | 2 / 0 / 3 |
| `comp_06_logistics_custom_format_tool` | 0.750 | 0.795 | **+0.045** | 1 / 0 / 4 |
| `comp_07_non_reasoning_refund_tool` | 0.860 | 0.730 | **-0.130** | 0 / 3 / 2 |
| `comp_08_fix_gamed_search_tools` | 0.900 | 0.920 | **+0.020** | 1 / 0 / 4 |
| `comp_09_skill_package_data_auditing` | 0.850 | 0.780 | **-0.070** | 0 / 3 / 2 |
| `comp_10_skill_package_postmortem_review` | 0.895 | 0.785 | **-0.110** | 0 / 4 / 1 |

**Task-Level Swap-Consistent Judge Summary (`n = 10` tasks, `df = 9`)**: `baseline` = `0.846` vs `with_skill` = `0.836` (delta=-0.011, t(9)=-0.47, p=0.6529; sign=5+/5- (p=1.0000); swap-consistent pairs `10` with_skill / `14` baseline / `26` flip_or_tie).
