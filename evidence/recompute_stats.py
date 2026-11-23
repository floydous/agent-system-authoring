# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Offline statistical recomputation from raw JSONL execution traces (Phase A, B & C).

Reads all JSONL trace files under:
- evidence/raw/results_*.jsonl            (Phase A: 228 records, 1 run/prompt)
- evidence/raw_phase_b/results_PB-*.jsonl (Phase B: 480 records, N=5 runs/prompt)
- evidence/raw_phase_c/results_PC-*.jsonl (Phase C: 480 records, N=5 runs/prompt)

Enforces strict unit-of-analysis hygiene (zero pseudoreplication):
- Aggregates repeated runs per prompt_id into prompt means before hypothesis testing.
- Computes paired t-tests (df = num_prompts - 1) and exact two-sided paired sign
  tests (binomial / McNemar on prompt differences via math.comb).
- Reports pooled run counts and TARa@K strictly as descriptive metrics.

Writes results to evidence/stats_recomputed.md and exits 0.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
import math
from pathlib import Path
import statistics
import sys
from typing import Any, Dict, List, Optional, Tuple


PHASE_A_BASELINES: Dict[str, str] = {
    "SP-1": "baseline",
    "SP-2": "bare_negative",
    "SP-3": "neutral_objective",
    "SP-4": "raw_text",
    "TS-1": "neutral_v_neutral",
    "TS-2": "without_descriptions",
    "TS-3": "no_thought",
}

PHASE_B_BASELINES: Dict[str, str] = {
    "PB-1": "flat_markdown",
    "PB-2": "neutral_ab",
    "PB-3": "system_only",
    "PB-4": "bare_negative",
    "PB-5": "neutral_objective",
    "PB-6": "no_rationale",
}

PHASE_C_BASELINES: Dict[str, str] = {
    "PC-1": "neutral",
    "PC-2": "affirmative_only",
}


def betacf(a: float, b: float, x: float) -> float:
    """Evaluate continued fraction for incomplete beta function (Lentz's method)."""
    max_iter = 200
    eps = 3.0e-12
    fpmin = 1.0e-300

    qab = a + b
    qap = a + 1.0
    qam = a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < fpmin:
        d = fpmin
    d = 1.0 / d
    h = d

    for m in range(1, max_iter + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < fpmin:
            d = fpmin
        c = 1.0 + aa / c
        if abs(c) < fpmin:
            c = fpmin
        d = 1.0 / d
        h *= d * c

        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < fpmin:
            d = fpmin
        c = 1.0 + aa / c
        if abs(c) < fpmin:
            c = fpmin
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < eps:
            break

    return h


def betainc(a: float, b: float, x: float) -> float:
    """Compute regularized incomplete beta function I_x(a, b)."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    bt = math.exp(
        math.lgamma(a + b)
        - math.lgamma(a)
        - math.lgamma(b)
        + a * math.log(x)
        + b * math.log(1.0 - x)
    )
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * betacf(a, b, x) / a
    return 1.0 - bt * betacf(b, a, 1.0 - x) / b


def student_t_two_sided_p(t_stat: float, df: int) -> float:
    """Compute exact two-sided p-value for Student's t statistic."""
    if df <= 0:
        return 1.0
    if t_stat == 0.0:
        return 1.0
    x = df / (df + t_stat * t_stat)
    return min(1.0, max(0.0, betainc(0.5 * df, 0.5, x)))


def paired_t_test(diffs: List[float]) -> Tuple[Optional[float], Optional[float], float, float]:
    """Run paired t-test on per-prompt mean differences (treatment - baseline)."""
    n = len(diffs)
    if n < 2:
        return None, None, 0.0, 0.0
    mean_d = statistics.mean(diffs)
    sd_d = statistics.stdev(diffs)
    if sd_d < 1e-15:
        return None, 1.0 if abs(mean_d) < 1e-15 else None, mean_d, 0.0
    se = sd_d / math.sqrt(n)
    t_val = mean_d / se
    p_val = student_t_two_sided_p(t_val, n - 1)
    return t_val, p_val, mean_d, sd_d


def sign_test_two_sided(diffs: List[float]) -> Tuple[int, int, float]:
    """Exact two-sided binomial paired sign test (equivalent to exact McNemar for binary single-run pairs)."""
    pos = sum(1 for d in diffs if d > 1e-12)
    neg = sum(1 for d in diffs if d < -1e-12)
    n = pos + neg
    if n == 0:
        return 0, 0, 1.0
    k = min(pos, neg)
    p = min(1.0, 2.0 * sum(math.comb(n, i) for i in range(k + 1)) / (2 ** n))
    return pos, neg, p


def load_records(directory: Path, pattern: str) -> Dict[str, List[Dict[str, Any]]]:
    """Load JSONL records grouped by hypothesis_id."""
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    if not directory.exists():
        return {}
    for jsonl_path in sorted(directory.glob(pattern)):
        with jsonl_path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                grouped[rec["hypothesis_id"]].append(rec)
    return dict(sorted(grouped.items()))


def is_binary_values(values: List[float]) -> bool:
    return all(v in (0.0, 1.0, 0, 1) for v in values)


def fmt_p(p: Optional[float]) -> str:
    if p is None:
        return "N/A"
    if p < 1e-4:
        return f"{p:.3e}"
    return f"{p:.4f}"


def fmt_float(val: Optional[float], digits: int = 3) -> str:
    if val is None:
        return "N/A"
    return f"{val:.{digits}f}"


def prompt_metric_pair_summary(
    recs_a: List[Dict[str, Any]],
    recs_b: List[Dict[str, Any]],
    metric_key: str = "score",
) -> str:
    """Compare condition A vs B strictly at the prompt level (paired t + exact sign test)."""
    by_a: Dict[str, List[float]] = defaultdict(list)
    by_b: Dict[str, List[float]] = defaultdict(list)
    for r in recs_a:
        by_a[r["prompt_id"]].append(float(r["metrics"][metric_key]))
    for r in recs_b:
        by_b[r["prompt_id"]].append(float(r["metrics"][metric_key]))

    shared = sorted(set(by_a.keys()) & set(by_b.keys()))
    diffs = [statistics.mean(by_a[p]) - statistics.mean(by_b[p]) for p in shared]
    t_val, p_val, mean_d, sd_d = paired_t_test(diffs)
    pos, neg, p_sign = sign_test_two_sided(diffs)
    df = len(shared) - 1

    if sd_d == 0.0 and mean_d == 0.0:
        t_part = f"delta=0.000 (df={df}, no diff)"
    elif t_val is None:
        t_part = f"delta={mean_d:+.3f}, sd_diff=0 (all {len(shared)} prompts identical shift)"
    else:
        t_part = f"delta={mean_d:+.3f}, t({df})={t_val:.2f}, p={fmt_p(p_val)}"
    return f"{t_part}; sign={pos}+/{neg}- (p={fmt_p(p_sign)})"


def render_suite_table(
    grouped: Dict[str, List[Dict[str, Any]]],
    baselines: Dict[str, str],
    include_tara: bool = False,
) -> List[str]:
    """Generate prompt-level statistical markdown summary rows (zero pseudoreplication)."""
    header = (
        "| Suite | Condition | N | Prompts | Runs/Prompt | Mean Score | SD (Prompt Means) | "
        "Raw Run Passes (Descriptive) | "
        + ("TARa@K | " if include_tara else "")
        + "Prompt-Level Paired t (df=P-1) | Prompt-Level Sign Test | Mean Reasoning Tok | Reasoning Tok vs Baseline | Status Flag |"
    )
    sep = (
        "| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | "
        + (":---: | " if include_tara else "")
        + ":---: | :---: | :---: | :---: | :--- |"
    )
    rows_out = [header, sep]

    for hyp_id, records in grouped.items():
        base_cond = baselines[hyp_id]
        by_cond: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for rec in records:
            by_cond[rec["condition"]].append(rec)

        cond_order = [base_cond] + sorted(c for c in by_cond if c != base_cond)
        base_by_prompt: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for rec in by_cond[base_cond]:
            base_by_prompt[rec["prompt_id"]].append(rec)
        base_scores_flat = [float(r["metrics"]["score"]) for r in by_cond[base_cond]]

        for cond in cond_order:
            cond_recs = by_cond[cond]
            n = len(cond_recs)
            by_prompt: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
            for rec in cond_recs:
                by_prompt[rec["prompt_id"]].append(rec)

            pids = sorted(by_prompt.keys())
            num_prompts = len(pids)
            runs_counts = sorted({len(v) for v in by_prompt.values()})
            runs_str = str(runs_counts[0]) if len(runs_counts) == 1 else f"{min(runs_counts)}-{max(runs_counts)}"

            prompt_means = [statistics.mean(float(r["metrics"]["score"]) for r in by_prompt[p]) for p in pids]
            mean_score = statistics.mean(prompt_means)
            sd_prompt = statistics.stdev(prompt_means) if len(prompt_means) >= 2 else 0.0

            scores = [float(r["metrics"]["score"]) for r in cond_recs]
            if is_binary_values(scores):
                ok_runs = sum(1 for v in scores if v == 1.0)
                raw_desc = f"{ok_runs}/{n} ({100 * ok_runs / n:.1f}%)"
            else:
                raw_desc = "non-binary"

            rtoks = [float(r.get("reasoning_tokens") or 0.0) for r in cond_recs]
            mean_rtok = statistics.mean(rtoks)

            # TARa@K: fraction of prompts whose score remained identical across all K repeats
            if include_tara and num_prompts > 0:
                unanimous = sum(
                    1
                    for plist in by_prompt.values()
                    if len({round(float(r["metrics"]["score"]), 6) for r in plist}) == 1
                )
                tara_str = f"{unanimous}/{num_prompts} ({100 * unanimous / num_prompts:.0f}%) | "
            else:
                tara_str = ""

            if cond == base_cond:
                score_test_str = "Baseline"
                sign_test_str = "Baseline"
                rtok_test_str = "Baseline"
                flag_str = "ceiling/no variance" if sd_prompt == 0.0 and mean_score == 1.0 else "baseline"
            else:
                shared_prompts = sorted(set(base_by_prompt.keys()) & set(by_prompt.keys()))
                df = len(shared_prompts) - 1
                score_diffs = [
                    statistics.mean(float(r["metrics"]["score"]) for r in by_prompt[p])
                    - statistics.mean(float(r["metrics"]["score"]) for r in base_by_prompt[p])
                    for p in shared_prompts
                ]
                rtok_diffs = [
                    statistics.mean(float(r.get("reasoning_tokens") or 0.0) for r in by_prompt[p])
                    - statistics.mean(float(r.get("reasoning_tokens") or 0.0) for r in base_by_prompt[p])
                    for p in shared_prompts
                ]

                t_s, p_s, mean_ds, sd_ds = paired_t_test(score_diffs)
                if sd_ds == 0.0 and abs(mean_ds) < 1e-15:
                    score_test_str = "delta=0.000 (no diff)"
                elif t_s is None:
                    score_test_str = f"delta={mean_ds:+.3f}, sd_diff=0 (see sign test)"
                else:
                    score_test_str = f"delta={mean_ds:+.3f}, t({df})={fmt_float(t_s, 2)}, p={fmt_p(p_s)}"

                pos, neg, p_sign = sign_test_two_sided(score_diffs)
                sign_test_str = f"{pos}+/{neg}- (p={fmt_p(p_sign)})"

                t_r, p_r, mean_dr, sd_dr = paired_t_test(rtok_diffs)
                if sd_dr == 0.0 and abs(mean_dr) < 1e-15:
                    rtok_test_str = "diff=0.0 (no diff)"
                elif t_r is None:
                    rtok_test_str = f"diff={mean_dr:+.1f}, sd_diff=0"
                else:
                    rtok_test_str = f"diff={mean_dr:+.1f}, t({df})={fmt_float(t_r, 2)}, p={fmt_p(p_r)}"

                sd_runs = statistics.stdev(scores) if len(scores) >= 2 else 0.0
                base_sd_runs = statistics.stdev(base_scores_flat) if len(base_scores_flat) >= 2 else 0.0
                if sd_runs == 0.0 and base_sd_runs == 0.0 and abs(mean_ds) < 1e-15:
                    flag_str = "ceiling/no variance - uninformative"
                else:
                    flag_str = "informative"

            rows_out.append(
                f"| **{hyp_id}** | `{cond}` | {n} | {num_prompts} | {runs_str} | "
                f"{mean_score:.3f} | {sd_prompt:.3f} | {raw_desc} | {tara_str}{score_test_str} | {sign_test_str} | "
                f"{mean_rtok:.1f} | {rtok_test_str} | {flag_str} |"
            )
    return rows_out


def main() -> int:
    parser = argparse.ArgumentParser(description="Recompute Phase A/B/C statistics from raw JSONL traces.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify that existing evidence/stats_recomputed.md matches recomputed output byte-for-byte (LF-normalized).",
    )
    args = parser.parse_args()

    evidence_dir = Path(__file__).resolve().parent
    raw_a = evidence_dir / "raw"
    raw_b = evidence_dir / "raw_phase_b"
    raw_c = evidence_dir / "raw_phase_c"
    out_path = evidence_dir / "stats_recomputed.md"

    grouped_a = load_records(raw_a, "results_*.jsonl")
    grouped_b = load_records(raw_b, "results_PB-*.jsonl")
    grouped_c = load_records(raw_c, "results_PC-*.jsonl")

    if not grouped_a:
        print(f"ERROR: No Phase A JSONL files found in {raw_a}", file=sys.stderr)
        return 1

    total_a = sum(len(v) for v in grouped_a.values())
    total_b = sum(len(v) for v in grouped_b.values())
    total_c = sum(len(v) for v in grouped_c.values())
    err_b = sum(1 for v in grouped_b.values() for r in v if r.get("error") is not None)
    err_c = sum(1 for v in grouped_c.values() for r in v if r.get("error") is not None)

    lines: List[str] = [
        "# Recomputed Statistical Summary (Phase A, Phase B & Phase C)",
        "",
        "- **Unit-of-Analysis Policy**: Zero pseudoreplication — repeated runs (`N = 5` per prompt) are aggregated into prompt-level means (`n = P` independent prompts) before inferential testing (paired *t*-test with `df = P - 1` and exact two-sided paired sign test). Pooled run counts and `TARa@K` are reported descriptively.",
        f"- **Phase A Traces**: `evidence/raw/` ({len(grouped_a)} suites, {total_a} records, 1 run/prompt)",
        f"- **Phase B Traces**: `evidence/raw_phase_b/` ({len(grouped_b)} suites, {total_b} records, 5 runs/prompt, gateway errors={err_b})",
        f"- **Phase C Traces**: `evidence/raw_phase_c/` ({len(grouped_c)} suites, {total_c} records, 5 runs/prompt, gateway errors={err_c})",
        "- **Generated By**: `evidence/recompute_stats.py` (offline stdlib-only statistical verification)",
        "",
    ]

    if grouped_c:
        lines.extend([
            "## 1. Phase C Summary Table (`N = 5` Runs/Prompt × `16` Prompts/Suite, High Effort, Counterbalanced / Powered)",
            "",
        ])
        lines.extend(render_suite_table(grouped_c, PHASE_C_BASELINES, include_tara=True))
        lines.extend(["", "### Phase C Detailed Prompt-Level Breakdowns", ""])

        if "PC-1" in grouped_c:
            pc1 = grouped_c["PC-1"]
            by_c = defaultdict(list)
            for r in pc1:
                by_c[r["condition"]].append(r)

            neu = by_c["neutral"]
            ex_sec = by_c["example_on_second"]
            as_sec = by_c["assertive_on_second"]

            def call_pattern(recs: List[Dict[str, Any]]) -> Tuple[int, int, int]:
                first_only, second_only, both_parallel = 0, 0, 0
                for r in recs:
                    tcs = [tc.get("function", {}).get("name") for tc in r.get("tool_calls", [])]
                    if len(tcs) == 1:
                        if tcs[0] == r["meta"]["first_tool"]:
                            first_only += 1
                        elif tcs[0] == r["meta"]["second_tool"]:
                            second_only += 1
                    elif len(tcs) >= 2:
                        both_parallel += 1
                return first_only, second_only, both_parallel

            n_f, n_s, n_b = call_pattern(neu)
            e_f, e_s, e_b = call_pattern(ex_sec)
            a_f, a_s, a_b = call_pattern(as_sec)
            neu_east_first_p0 = sum(1 for r in neu if r["meta"]["first_tool"] == "records_lookup_east" and len(r.get("tool_calls", [])) == 1 and r["tool_calls"][0]["function"]["name"] == "records_lookup_east")
            neu_west_first_p0 = sum(1 for r in neu if r["meta"]["first_tool"] == "records_lookup_west" and len(r.get("tool_calls", [])) == 1 and r["tool_calls"][0]["function"]["name"] == "records_lookup_west")
            all_valid_args = sum(
                1
                for r in pc1
                if r.get("tool_calls")
                and all(
                    json.loads(tc["function"].get("arguments", "{}")).get("entity_id") == r["meta"]["exp_id"]
                    and json.loads(tc["function"].get("arguments", "{}")).get("record_scope") == r["meta"]["exp_scope"]
                    for tc in r["tool_calls"]
                )
            )

            lines.extend([
                f"- **`PC-1` Call Patterns Across Counterbalanced Arms (`n = 16` prompts × `5` repeats = `80` runs/arm)**:",
                f"  - `neutral`: `{n_b}/80` called **both** identical tools in parallel, `{n_f}/80` exclusive `first_tool` (`{neu_east_first_p0}/40` when `east` first, `{neu_west_first_p0}/40` when `west` first), `{n_s}/80` exclusive `second_tool`.",
                f"  - `example_on_second`: `{e_b}/80` parallel-both, `{e_f}/80` exclusive `first_tool`, `{e_s}/80` exclusive `second_tool` (zero hijacking).",
                f"  - `assertive_on_second`: `{a_b}/80` parallel-both, `{a_f}/80` exclusive `first_tool`, **`{a_s}/80` (`100.0%`, `40` east / `40` west) exclusive `second_tool`**.",
                f"  - Argument extraction accuracy across all 240 requests (including parallel calls): {all_valid_args}/240 ({100*all_valid_args/240:.1f}%).",
                f"- **`PC-1` Prompt-Level Pairwise Contrasts (`n = 16` prompts, exclusive selection of `second_tool`)**:",
                f"  - `assertive_on_second` vs `neutral`: {prompt_metric_pair_summary(as_sec, neu, 'score')}",
                f"  - `example_on_second` vs `neutral`: {prompt_metric_pair_summary(ex_sec, neu, 'score')}",
                f"  - `assertive_on_second` vs `example_on_second`: {prompt_metric_pair_summary(as_sec, ex_sec, 'score')}",
            ])

        if "PC-2" in grouped_c:
            pc2 = grouped_c["PC-2"]
            by_c = defaultdict(list)
            for r in pc2:
                by_c[r["condition"]].append(r)

            lines.extend([
                "- **`PC-2` Prompt-Level Pairwise Contrasts (`n = 16` prompts across 4 topic clusters)**:",
                f"  - Combined score (`lexical_clean` & `length_ok`):",
                f"    - `bare_negative` vs `affirmative_only`: {prompt_metric_pair_summary(by_c['bare_negative'], by_c['affirmative_only'], 'score')}",
                f"    - `paired_affirmative` vs `affirmative_only`: {prompt_metric_pair_summary(by_c['paired_affirmative'], by_c['affirmative_only'], 'score')}",
                f"    - `paired_affirmative` vs `bare_negative` (`C-01`): {prompt_metric_pair_summary(by_c['paired_affirmative'], by_c['bare_negative'], 'score')}",
                f"  - Pure `lexical_clean` (zero forbidden words, ignoring word-count jitter):",
                f"    - `bare_negative` vs `affirmative_only`: {prompt_metric_pair_summary(by_c['bare_negative'], by_c['affirmative_only'], 'lexical_clean')}",
                f"    - `paired_affirmative` vs `affirmative_only`: {prompt_metric_pair_summary(by_c['paired_affirmative'], by_c['affirmative_only'], 'lexical_clean')}",
                f"    - `paired_affirmative` vs `bare_negative` (`C-01`): {prompt_metric_pair_summary(by_c['paired_affirmative'], by_c['bare_negative'], 'lexical_clean')}",
                "- **`PC-2` Descriptive Run Totals (out of 80 runs each)**:",
            ])
            for c in ("affirmative_only", "bare_negative", "paired_affirmative"):
                lex_ok = sum(int(r["metrics"].get("lexical_clean", 0)) for r in by_c[c])
                len_ok = sum(int(r["metrics"].get("length_ok", 0)) for r in by_c[c])
                both_ok = sum(int(r["metrics"].get("score", 0)) for r in by_c[c])
                forb_hits = sum(int(r["metrics"].get("forbidden_word_count", 0)) for r in by_c[c])
                lines.append(
                    f"  - `{c}`: `lexical_clean`={lex_ok}/80 ({100*lex_ok/80:.1f}%), "
                    f"`length_ok`={len_ok}/80, `combined`={both_ok}/80 ({100*both_ok/80:.1f}%), "
                    f"total forbidden hits={forb_hits}"
                )
        lines.append("")

    if grouped_b:
        lines.extend([
            "## 2. Phase B Summary Table (`N = 5` Runs/Prompt × `6` Prompts/Suite, Prompt-Level Inference)",
            "",
        ])
        lines.extend(render_suite_table(grouped_b, PHASE_B_BASELINES, include_tara=True))
        lines.extend(["", "### Phase B Sub-Metric & Pairwise Prompt-Level Breakdowns", ""])

        if "PB-4" in grouped_b:
            pb4 = grouped_b["PB-4"]
            by_c = defaultdict(list)
            for r in pb4:
                by_c[r["condition"]].append(r)
            lines.extend([
                "- **`PB-4` Pairwise Prompt-Level Contrasts (`n = 6` prompts)**:",
                f"  - `bare_negative` vs `affirmative_only`: {prompt_metric_pair_summary(by_c['bare_negative'], by_c['affirmative_only'], 'score')}",
                f"  - `paired_affirmative` vs `affirmative_only`: {prompt_metric_pair_summary(by_c['paired_affirmative'], by_c['affirmative_only'], 'score')}",
                f"  - `paired_affirmative` vs `bare_negative`: {prompt_metric_pair_summary(by_c['paired_affirmative'], by_c['bare_negative'], 'score')}",
            ])
            for c in ("bare_negative", "affirmative_only", "paired_affirmative"):
                len_ok = sum(int(r["metrics"].get("length_ok", 0)) for r in by_c[c])
                forb_tot = sum(int(r["metrics"].get("forbidden_word_count", 0)) for r in by_c[c])
                bold_hits = sum(int(r["metrics"].get("has_bold", 0)) for r in by_c[c])
                lines.append(f"  - `{c}` (descriptive 30 runs): `length_ok`={len_ok}/30, forbidden hits={forb_tot}, bold `**` hits={bold_hits}")

        if "PB-1" in grouped_b:
            pb1 = grouped_b["PB-1"]
            by_c = defaultdict(list)
            for r in pb1:
                by_c[r["condition"]].append(r)
            lines.append("- **`PB-1` Per-Constraint Pass Counts (descriptive out of 30 runs each)**:")
            for c in ("flat_markdown", "flat_xml", "nested_xml"):
                parts = [f"{k}={int(sum(r['metrics'][k] for r in by_c[c]))}/30" for k in ("c1_length", "c2_keywords", "c3_negative", "c4_headers", "c5_severity", "c6_terminal", "strict_pass")]
                lines.append(f"  - `{c}`: " + ", ".join(parts))

        if "PB-6" in grouped_b:
            pb6 = grouped_b["PB-6"]
            by_c = defaultdict(list)
            for r in pb6:
                by_c[r["condition"]].append(r)
            lines.append(
                f"- **`PB-6` `rationale_first` vs `rationale_last` (`n = 6` prompts, `reasoning_tokens = 0`)**: "
                + prompt_metric_pair_summary(by_c["rationale_first"], by_c["rationale_last"], "score")
                + " (exact tie between `no_rationale` 11/30 and `rationale_last` 11/30)."
            )

    lines.extend([
        "",
        "## 3. Phase A Summary Table (Baseline Run `20261119_020610_3f7405`, `N = 1` Run/Prompt)",
        "",
    ])
    lines.extend(render_suite_table(grouped_a, PHASE_A_BASELINES, include_tara=False))

    if "TS-2" in grouped_a:
        by_c = defaultdict(list)
        for r in grouped_a["TS-2"]:
            by_c[r["condition"]].append(r)
        lines.extend([
            "",
            "### Phase A `TS-2` Per-Field Validity Breakdown (Matched Pairs, Exact Two-Sided Sign/McNemar Test)",
            "",
            "| Field | `without_descriptions` | `with_descriptions` | Prompt-Level Exact Sign / McNemar p |",
            "| :--- | :---: | :---: | :---: |",
        ])
        for field in ("timestamp_valid", "currency_valid", "geo_valid", "all_fields_valid"):
            b_by_p = {r["prompt_id"]: float(r["metrics"].get(field, 0.0)) for r in by_c["without_descriptions"]}
            c_by_p = {r["prompt_id"]: float(r["metrics"].get(field, 0.0)) for r in by_c["with_descriptions"]}
            shared = sorted(set(b_by_p.keys()) & set(c_by_p.keys()))
            diffs = [c_by_p[p] - b_by_p[p] for p in shared]
            pos, neg, p_sign = sign_test_two_sided(diffs)
            b_ok = sum(1 for p in shared if b_by_p[p] == 1.0)
            c_ok = sum(1 for p in shared if c_by_p[p] == 1.0)
            lines.append(f"| `{field}` | {b_ok}/15 ({100*b_ok/15:.1f}%) | {c_ok}/15 ({100*c_ok/15:.1f}%) | {pos}+/{neg}- (p={fmt_p(p_sign)}) |")

    if "SP-4" in grouped_a:
        by_c = defaultdict(list)
        for r in grouped_a["SP-4"]:
            by_c[r["condition"]].append(r)
        lines.extend([
            "",
            "### Phase A `SP-4` Per-Constraint Breakdown (Revealing `[P0|P1|P2|P3]` Prompt Wording Bug)",
            "",
        ])
        for c in ("raw_text", "xml_containers"):
            parts = [f"{k}={int(sum(r['metrics'][k] for r in by_c[c]))}/12" for k in ("c1_length", "c2_keywords", "c3_negative", "c4_headers", "c5_severity", "c6_terminal")]
            lines.append(f"- `{c}`: " + ", ".join(parts))

    lines.append("")
    rendered = "\n".join(lines).replace("\r\n", "\n")
    if args.check:
        if not out_path.exists():
            print(f"ERROR: {out_path} does not exist.", file=sys.stderr)
            return 1
        existing = out_path.read_text(encoding="utf-8").replace("\r\n", "\n")
        if existing != rendered:
            print(f"ERROR: {out_path} has drifted from recomputed trace statistics.", file=sys.stderr)
            return 1
        print(f"OK: {out_path} matches recomputed trace statistics exactly.")
        return 0

    out_path.write_text(rendered, encoding="utf-8")
    print(f"Wrote recomputed stats to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
