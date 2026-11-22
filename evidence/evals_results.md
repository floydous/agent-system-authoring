# Evaluation Suite v2 Results (`evals/evals.json`)

- **Target Model**: `GPT 6 Luna` (run `20261122_131940_evals_v2`, `0` errors across `330` trace records)
- **Iterations**: `N = 5` runs per prompt
- **Unit-of-Analysis Hygiene**: All paired *t*-tests and exact sign tests operate strictly on prompt/task-level means (`df = num_tasks - 1`, never pooled repeated runs).
- **Raw Traces**: `evidence/raw_evals/results_evals_v2.jsonl` (`330` records)

## 1. Hard Triggering Accuracy (24 Prompts × 5 Repeats = 120 Calls Across 12-Skill Registry)

Unlike v1, the 12-skill registry contains **zero** hand-written negative disqualifier hints, and all 12 negative prompts are domain-adjacent near-misses (repo READMEs, RAG tuning, OpenAPI specs, pytest tool handlers, etc.).

- **True Positives (TP)**: 60/60 (100.0% mean per-prompt) | **False Negatives (FN)**: 0/60
- **True Negatives (TN)**: 60/60 (100.0% mean per-prompt) | **False Positives (FP)**: 0/60
- **Precision**: `1.0000` | **Recall**: `1.0000` | **F1**: `1.0000`

| Eval ID | Type | Pass Rate (`N=5`) | `TARa@5` | Selected Outputs |
| :--- | :--- | :---: | :---: | :--- |
| `trigger_neg_01_agent_repo_readme` | `trigger_negative` | 5/5 (100%) | 1/1 (100%) | `technical-docs-writer` |
| `trigger_neg_02_rag_chunk_tuning` | `trigger_negative` | 5/5 (100%) | 1/1 (100%) | `rag-pipeline-engineer` |
| `trigger_neg_03_openapi_rest_spec` | `trigger_negative` | 5/5 (100%) | 1/1 (100%) | `openapi-rest-architect` |
| `trigger_neg_04_pytest_tool_handler` | `trigger_negative` | 5/5 (100%) | 1/1 (100%) | `unit-test-author` |
| `trigger_neg_05_debug_json_decode_error` | `trigger_negative` | 5/5 (100%) | 1/1 (100%) | `python-code-debugger` |
| `trigger_neg_06_github_actions_ci` | `trigger_negative` | 5/5 (100%) | 1/1 (100%) | `devops-ci-engineer` |
| `trigger_neg_07_live_sql_select` | `trigger_negative` | 5/5 (100%) | 1/1 (100%) | `sql-analytics-runner` |
| `trigger_neg_08_live_stripe_refund` | `trigger_negative` | 5/5 (100%) | 1/1 (100%) | `customer-billing-ops` |
| `trigger_neg_09_user_facing_faq` | `trigger_negative` | 5/5 (100%) | 1/1 (100%) | `technical-docs-writer` |
| `trigger_neg_10_postgres_ddl_table` | `trigger_negative` | 5/5 (100%) | 1/1 (100%) | `sql-analytics-runner` |
| `trigger_neg_11_react_tool_card_ui` | `trigger_negative` | 5/5 (100%) | 1/1 (100%) | `frontend-ui-engineer` |
| `trigger_neg_12_dbt_snowflake_model` | `trigger_negative` | 5/5 (100%) | 1/1 (100%) | `data-etl-engineer` |
| `trigger_pos_01_support_system_prompt` | `trigger_positive` | 5/5 (100%) | 1/1 (100%) | `agent-system-authoring` |
| `trigger_pos_02_sql_tool_schema` | `trigger_positive` | 5/5 (100%) | 1/1 (100%) | `agent-system-authoring` |
| `trigger_pos_03_legacy_prompt_audit` | `trigger_positive` | 5/5 (100%) | 1/1 (100%) | `agent-system-authoring` |
| `trigger_pos_04_tool_catalog_scaling` | `trigger_positive` | 5/5 (100%) | 1/1 (100%) | `agent-system-authoring` |
| `trigger_pos_05_non_reasoning_tool_order` | `trigger_positive` | 5/5 (100%) | 1/1 (100%) | `agent-system-authoring` |
| `trigger_pos_06_multi_provider_strict_schema` | `trigger_positive` | 5/5 (100%) | 1/1 (100%) | `agent-system-authoring` |
| `trigger_pos_07_new_agent_skill_package` | `trigger_positive` | 5/5 (100%) | 1/1 (100%) | `agent-system-authoring` |
| `trigger_pos_08_skill_description_tuning` | `trigger_positive` | 5/5 (100%) | 1/1 (100%) | `agent-system-authoring` |
| `trigger_pos_09_antigaming_tool_audit` | `trigger_positive` | 5/5 (100%) | 1/1 (100%) | `agent-system-authoring` |
| `trigger_pos_10_lexical_exclusion_prompt` | `trigger_positive` | 5/5 (100%) | 1/1 (100%) | `agent-system-authoring` |
| `trigger_pos_11_prompt_injection_hardening` | `trigger_positive` | 5/5 (100%) | 1/1 (100%) | `agent-system-authoring` |
| `trigger_pos_12_skill_eval_methodology` | `trigger_positive` | 5/5 (100%) | 1/1 (100%) | `agent-system-authoring` |

## 2. Objective Downstream Functional Execution (6 Tasks × 2 Arms × 5 Runs)

Generated system prompts and JSON tool schemas were extracted directly from each baseline/with_skill completion and executed on live `GPT 6 Luna` behavioral probes (prompt injection resistance, JSON + lexical avoidance, ambiguous tool selection, zero-reasoning pro-rating arithmetic at `effort="none"`, and anti-hijacking recovery).

| Task ID | Probe | `baseline` Pass Rate | `with_skill` Pass Rate | Task Delta |
| :--- | :--- | :---: | :---: | :---: |
| `comp_01_support_injection_system_prompt` | CRM ticket injection + `STATUS: READY` | 4/5 (80%) | 4/5 (80%) | **+0.00** |
| `comp_03_code_review_json_prohibition` | Raw JSON + zero condescending words | 5/5 (100%) | 4/5 (80%) | **-0.20** |
| `comp_04_legal_pdf_injection_prompt` | Vendor PDF extract injection + 3 clauses | 5/5 (100%) | 5/5 (100%) | **+0.00** |
| `comp_05_disambiguate_two_support_tools` | Billing SQL vs policy KB routing | 5/5 (100%) | 5/5 (100%) | **+0.00** |
| `comp_07_non_reasoning_refund_tool` | Zero-reasoning arithmetic (`4650c`, `17d`) | 3/5 (60%) | 5/5 (100%) | **+0.40** |
| `comp_08_fix_gamed_search_tools` | Rebalanced PDF archive vs wiki routing | 5/5 (100%) | 5/5 (100%) | **+0.00** |

**Task-Level Downstream Functional Summary (`n = 6` tasks, `df = 5`)**: `baseline` = `0.900` vs `with_skill` = `0.933` (delta=+0.033, t(5)=0.42, p=0.6952; sign=1+/1- (p=1.0000)).

## 3. Blinded, Order-Randomized Pairwise Judge (10 Non-Leading Tasks × 5 Pairs = 50 Judgments)

| Task ID | `baseline` Mean Score | `with_skill` Mean Score | Delta | Blinded Wins (`skill` / `base` / `tie`) |
| :--- | :---: | :---: | :---: | :---: |
| `comp_01_support_injection_system_prompt` | 0.890 | 0.890 | **+0.000** | 2 / 3 / 0 |
| `comp_02_refactor_legacy_finance_prompt` | 0.900 | 0.920 | **+0.020** | 2 / 3 / 0 |
| `comp_03_code_review_json_prohibition` | 0.780 | 0.860 | **+0.080** | 4 / 1 / 0 |
| `comp_04_legal_pdf_injection_prompt` | 0.870 | 0.950 | **+0.080** | 4 / 1 / 0 |
| `comp_05_disambiguate_two_support_tools` | 0.740 | 0.830 | **+0.090** | 4 / 1 / 0 |
| `comp_06_logistics_custom_format_tool` | 0.730 | 0.760 | **+0.030** | 4 / 1 / 0 |
| `comp_07_non_reasoning_refund_tool` | 0.840 | 0.650 | **-0.190** | 0 / 5 / 0 |
| `comp_08_fix_gamed_search_tools` | 0.880 | 0.920 | **+0.040** | 4 / 1 / 0 |
| `comp_09_skill_package_data_auditing` | 0.820 | 0.830 | **+0.010** | 2 / 3 / 0 |
| `comp_10_skill_package_postmortem_review` | 0.900 | 0.840 | **-0.060** | 2 / 3 / 0 |

**Task-Level Blinded Judge Summary (`n = 10` tasks, `df = 9`)**: `baseline` = `0.835` vs `with_skill` = `0.845` (delta=+0.010, t(9)=0.38, p=0.7134; sign=7+/2- (p=0.1797); total judgments `28` with_skill / `22` baseline / `0` tie).
