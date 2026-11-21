# Evaluation Suite Results (`evals/evals.json`)

- **Target Model**: `GPT 6 Luna` (run `20261121_170603_evals`, `0` errors across `80` calls)
- **Iterations**: `N = 5` runs per prompt (`reasoning_effort="low"` for triggering; `"medium"` for comparative authoring)
- **Raw Traces**: `evidence/raw_evals/results_evals.jsonl` (`80` records)

## 1. Triggering Accuracy Summary (50 Calls Across 6-Skill Registry)

- **True Positives (TP)**: 25/25 | **False Negatives (FN)**: 0/25
- **True Negatives (TN)**: 25/25 | **False Positives (FP)**: 0/25
- **Precision**: `1.0000` (100.0%) | **Recall**: `1.0000` (100.0%) | **F1**: `1.0000`

| Eval ID | Type | Pass Rate (`N=5`) | `TARa@5` | Selected Outputs |
| :--- | :--- | :---: | :---: | :--- |
| `trigger_neg_01_run_sql_query` | `trigger_negative` | 5/5 (100%) | 1/1 (100%) | `sql-query-runner` |
| `trigger_neg_02_python_script_debug` | `trigger_negative` | 5/5 (100%) | 1/1 (100%) | `python-debugger` |
| `trigger_neg_03_customer_refund_execution` | `trigger_negative` | 5/5 (100%) | 1/1 (100%) | `stripe-support-ops` |
| `trigger_neg_04_html_css_styling` | `trigger_negative` | 5/5 (100%) | 1/1 (100%) | `frontend-css-styler` |
| `trigger_neg_05_git_commit_push` | `trigger_negative` | 5/5 (100%) | 1/1 (100%) | `git-workflow-helper` |
| `trigger_pos_01_customer_support` | `trigger_positive` | 5/5 (100%) | 1/1 (100%) | `agent-system-authoring` |
| `trigger_pos_02_sql_tool_schema` | `trigger_positive` | 5/5 (100%) | 1/1 (100%) | `agent-system-authoring` |
| `trigger_pos_03_prompt_audit_sanitization` | `trigger_positive` | 5/5 (100%) | 1/1 (100%) | `agent-system-authoring` |
| `trigger_pos_04_tool_catalog_pruning` | `trigger_positive` | 5/5 (100%) | 1/1 (100%) | `agent-system-authoring` |
| `trigger_pos_05_author_agent_skill` | `trigger_positive` | 5/5 (100%) | 1/1 (100%) | `agent-system-authoring` |

## 2. Comparative Authoring Quality (30 Calls, Programmatic Rubric)

| Eval ID | `baseline` Mean (SD) | `with_skill` Mean (SD) | Delta | Paired t / p-value (across N=5 repeats) |
| :--- | :---: | :---: | :---: | :---: |
| `comparative_01_customer_support_system_prompt` | 0.400 (0.000) | 0.720 (0.179) | **+0.320** | t=4.00, p=0.0161 |
| `comparative_02_sql_tool_schema_authoring` | 0.800 (0.139) | 1.000 (0.000) | **+0.200** | t=3.21, p=0.0327 |
| `comparative_03_agent_skill_package_design` | 0.400 (0.091) | 0.833 (0.118) | **+0.433** | t=10.61, p=0.0004 |

**Overall Comparative Lift (`N = 15` paired runs)**: `baseline` = `0.533` vs `with_skill` = `0.851` (**delta = `+0.318`**, `t = 7.52`, `p = 2.804e-06`).
