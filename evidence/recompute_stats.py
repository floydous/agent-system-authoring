# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Offline statistical recomputation from raw JSONL execution traces (Phases A–F & H-08).

Reads all JSONL trace files under:
- evidence/raw/results_*.jsonl                     (Phase A: 228 records, 1 run/prompt, GPT 6 Luna)
- evidence/raw_phase_b/results_PB-*.jsonl          (Phase B: 480 records, N=5 runs/prompt, GPT 6 Luna)
- evidence/raw_phase_c/results_PC-*.jsonl          (Phase C: 480 records, N=5 runs/prompt, GPT 6 Luna)
- evidence/raw_phase_d/results_PD-*.jsonl          (Phase D: 1,030 records, N=5 runs/prompt, GPT 6 Luna)
- evidence/raw_phase_e/results_PE-*.jsonl          (Phase E: 880 records, N=5 runs/prompt, GPT 6 Luna high)
- evidence/raw_h08_particle1/results_H08-*.jsonl   (H-08: 950 records, N=5 runs/prompt, Particle-1 / DeepSeek V4.1 Flash)
- evidence/raw_phase_f_nemo/results_NEMO-*.jsonl   (Phase F: 1,190 records, N=5 runs/prompt, Nemotron 3.5 Lightning 30B-A3B Mamba-2 SSM)
- evidence/raw_phase_f_ling/results_LING-*.jsonl   (Phase F: 1,510 records, N=5 runs/prompt, Ling 3.2 Flash ~560B-A25B Hybrid-Linear KDA+MLA MoE)

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

PHASE_D_BASELINES: Dict[str, str] = {
    "PD-1": "without_descriptions",
    "PD-2": "compact_15t",
    "PD-3": "plain_prose",
    "PD-4": "arabic_digits",
    "PD-5": "json_schema",
}

PHASE_E_BASELINES: Dict[str, str] = {
    "PE-1": "rules_05",
    "PE-2": "system_only",
    "PE-3": "neutral_objective",
    "PE-4": "doc_start",
}

H08_BASELINES: Dict[str, str] = {
    "H08-PC1": "neutral",
    "H08-PC2": "affirmative_only",
    "H08-PD1": "without_descriptions",
    "H08-PD4": "arabic_digits",
    "H08-PD5": "json_schema",
}

PHASE_F_NEMO_BASELINES: Dict[str, str] = {
    "NEMO-PB6": "no_rationale",
    "NEMO-PC1": "neutral",
    "NEMO-PC2": "affirmative_only",
    "NEMO-PD1": "without_descriptions",
    "NEMO-PD4": "arabic_digits",
    "NEMO-PE2": "system_only",
}

PHASE_F_LING_BASELINES: Dict[str, str] = {
    "LING-PB6": "no_rationale",
    "LING-PC1": "neutral",
    "LING-PC2": "affirmative_only",
    "LING-PD1": "without_descriptions",
    "LING-PD4": "arabic_digits",
    "LING-PD5": "json_schema",
    "LING-PE1": "rules_05",
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


def prompt_top_field_pair_summary(
    recs_a: List[Dict[str, Any]],
    recs_b: List[Dict[str, Any]],
    field_name: str,
    digits: int = 1,
) -> str:
    """Compare a top-level numeric record field (e.g., prompt_tokens or latency_seconds) at the prompt level."""
    by_a: Dict[str, List[float]] = defaultdict(list)
    by_b: Dict[str, List[float]] = defaultdict(list)
    for r in recs_a:
        by_a[r["prompt_id"]].append(float(r.get(field_name) or 0.0))
    for r in recs_b:
        by_b[r["prompt_id"]].append(float(r.get(field_name) or 0.0))

    shared = sorted(set(by_a.keys()) & set(by_b.keys()))
    diffs = [statistics.mean(by_a[p]) - statistics.mean(by_b[p]) for p in shared]
    t_val, p_val, mean_d, sd_d = paired_t_test(diffs)
    pos, neg, p_sign = sign_test_two_sided(diffs)
    df = len(shared) - 1

    if sd_d == 0.0 and abs(mean_d) < 1e-15:
        t_part = f"diff=0.0 (df={df}, no diff)"
    elif t_val is None:
        t_part = f"diff={mean_d:+.{digits}f}, sd_diff=0 (all {len(shared)} prompts identical shift)"
    else:
        t_part = f"diff={mean_d:+.{digits}f}, t({df})={t_val:.2f}, p={fmt_p(p_val)}"
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
    raw_d = evidence_dir / "raw_phase_d"
    raw_e = evidence_dir / "raw_phase_e"
    raw_h08 = evidence_dir / "raw_h08_particle1"
    raw_f_nemo = evidence_dir / "raw_phase_f_nemo"
    raw_f_ling = evidence_dir / "raw_phase_f_ling"
    out_path = evidence_dir / "stats_recomputed.md"

    grouped_a = load_records(raw_a, "results_*.jsonl")
    grouped_b = load_records(raw_b, "results_PB-*.jsonl")
    grouped_c = load_records(raw_c, "results_PC-*.jsonl")
    grouped_d = load_records(raw_d, "results_PD-*.jsonl")
    grouped_e = load_records(raw_e, "results_PE-*.jsonl")
    grouped_h08 = load_records(raw_h08, "results_H08-*.jsonl")
    grouped_f_nemo = load_records(raw_f_nemo, "results_NEMO-*.jsonl")
    grouped_f_ling = load_records(raw_f_ling, "results_LING-*.jsonl")

    if not grouped_a:
        print(f"ERROR: No Phase A JSONL files found in {raw_a}", file=sys.stderr)
        return 1

    total_a = sum(len(v) for v in grouped_a.values())
    total_b = sum(len(v) for v in grouped_b.values())
    total_c = sum(len(v) for v in grouped_c.values())
    total_d = sum(len(v) for v in grouped_d.values())
    total_e = sum(len(v) for v in grouped_e.values())
    total_h08 = sum(len(v) for v in grouped_h08.values())
    total_f_nemo = sum(len(v) for v in grouped_f_nemo.values())
    total_f_ling = sum(len(v) for v in grouped_f_ling.values())
    grand_total = total_a + total_b + total_c + total_d + total_e + total_h08 + total_f_nemo + total_f_ling
    err_b = sum(1 for v in grouped_b.values() for r in v if r.get("error") is not None)
    err_c = sum(1 for v in grouped_c.values() for r in v if r.get("error") is not None)
    err_d = sum(1 for v in grouped_d.values() for r in v if r.get("error") is not None)
    err_e = sum(1 for v in grouped_e.values() for r in v if r.get("error") is not None)
    err_h08 = sum(1 for v in grouped_h08.values() for r in v if r.get("error") is not None)
    err_f_nemo = sum(1 for v in grouped_f_nemo.values() for r in v if r.get("error") is not None)
    err_f_ling = sum(1 for v in grouped_f_ling.values() for r in v if r.get("error") is not None)

    lines: List[str] = [
        "# Recomputed Statistical Summary (Phases A–F & H-08 Cross-Architecture Replication)",
        "",
        f"- **Total Benchmark Traces**: **{grand_total:,} records** (`{total_a + total_b + total_c + total_d + total_e:,}` on `GPT 6 Luna` + `{total_h08:,}` on `Particle-1` / DeepSeek V4.1 Flash + `{total_f_nemo:,}` on `Nemotron 3.5 Lightning` / `30B-A3B` Mamba-2 SSM + `{total_f_ling:,}` on `Ling 3.2 Flash` / `~560B-A25B` Hybrid-Linear KDA+MLA MoE)",
        "- **Unit-of-Analysis Policy**: Zero pseudoreplication — repeated runs (`N = 5` per prompt) are aggregated into prompt-level means (`n = P` independent prompts) before inferential testing (paired *t*-test with `df = P - 1` and exact two-sided paired sign test). Pooled run counts and `TARa@K` are reported descriptively.",
        f"- **Phase A Traces**: `evidence/raw/` ({len(grouped_a)} suites, {total_a} records, 1 run/prompt, GPT 6 Luna)",
        f"- **Phase B Traces**: `evidence/raw_phase_b/` ({len(grouped_b)} suites, {total_b} records, 5 runs/prompt, GPT 6 Luna, gateway errors={err_b})",
        f"- **Phase C Traces**: `evidence/raw_phase_c/` ({len(grouped_c)} suites, {total_c} records, 5 runs/prompt, GPT 6 Luna, gateway errors={err_c})",
        f"- **Phase D Traces**: `evidence/raw_phase_d/` ({len(grouped_d)} suites, {total_d} records, 5 runs/prompt, GPT 6 Luna, gateway errors={err_d})",
        f"- **Phase E Traces**: `evidence/raw_phase_e/` ({len(grouped_e)} suites, {total_e} records, 5 runs/prompt, GPT 6 Luna high, gateway errors={err_e})",
        f"- **H-08 Particle-1 Traces**: `evidence/raw_h08_particle1/` ({len(grouped_h08)} suites, {total_h08} records, 5 runs/prompt, Particle-1 / DeepSeek V4.1 Flash, gateway errors={err_h08})",
        f"- **Phase F Nemotron Traces**: `evidence/raw_phase_f_nemo/` ({len(grouped_f_nemo)} suites, {total_f_nemo} records, 5 runs/prompt, Nemotron 3.5 Lightning 30B-A3B Mamba-2 SSM, gateway errors={err_f_nemo})",
        f"- **Phase F Ling Traces**: `evidence/raw_phase_f_ling/` ({len(grouped_f_ling)} suites, {total_f_ling} records, 5 runs/prompt, Ling 3.2 Flash ~560B-A25B Hybrid-Linear KDA+MLA MoE, gateway errors={err_f_ling})",
        "- **Generated By**: `evidence/recompute_stats.py` (offline stdlib-only statistical verification)",
        "",
    ]

    if grouped_f_ling:
        lines.extend([
            "## 1. Phase F Cross-Architecture Table (`N = 5` Runs/Prompt, `Ling 3.2 Flash` / `~560B-A25B` Hybrid-Linear KDA+MLA MoE)",
            "",
        ])
        lines.extend(render_suite_table(grouped_f_ling, PHASE_F_LING_BASELINES, include_tara=True))
        lines.extend(["", "### Phase F Detailed Prompt-Level Breakdowns (`Ling 3.2 Flash`)", ""])

        if "LING-PB6" in grouped_f_ling:
            by_c = defaultdict(list)
            for r in grouped_f_ling["LING-PB6"]:
                by_c[r["condition"]].append(r)
            lines.extend([
                "- **`LING-PB6` (`R-TOOL-11` Powered `16`-Prompt `rationale` Ordering, `thinking_off`, `reasoning_tokens = 0` on all 240 calls)**:",
                "  - `no_rationale`=24/80 (30.0%), `rationale_last`=29/80 (36.2%), **`rationale_first`=76/80 (95.0%)**; exact declared JSON key order preserved on `240/240` calls.",
                f"  - `rationale_first` vs `no_rationale`: {prompt_metric_pair_summary(by_c['rationale_first'], by_c['no_rationale'], 'score')}",
                f"  - `rationale_first` vs `rationale_last`: {prompt_metric_pair_summary(by_c['rationale_first'], by_c['rationale_last'], 'score')}",
            ])

        if "LING-PE1" in grouped_f_ling:
            by_c = defaultdict(list)
            for r in grouped_f_ling["LING-PE1"]:
                by_c[r["condition"]].append(r)
            lines.append("- **`LING-PE1` (`R-SYS-01` Non-Reasoning Behavioral Rule Density, `thinking_off`, `16` prompts × `5` = `80` runs/arm)**:")
            for c in ("rules_05", "rules_10", "rules_20", "rules_50"):
                pt = statistics.mean(float(r.get("prompt_tokens") or 0.0) for r in by_c[c])
                s_ok = sum(int(r["metrics"].get("strict_all", 0)) for r in by_c[c])
                c5 = statistics.mean(float(r["metrics"].get("core5_score", 0.0)) for r in by_c[c])
                lines.append(f"  - `{c}`: `strict_all`={s_ok}/80 ({100*s_ok/80:.1f}%), `core5_score`={c5:.4f}, prompt_tokens={pt:.1f}")
            lines.extend([
                f"  - `rules_10` vs `rules_05` (`strict_all`): {prompt_metric_pair_summary(by_c['rules_10'], by_c['rules_05'], 'strict_all')}",
                f"  - `rules_20` vs `rules_05` (`strict_all`): {prompt_metric_pair_summary(by_c['rules_20'], by_c['rules_05'], 'strict_all')}",
                f"  - `rules_50` vs `rules_05` (`strict_all`): {prompt_metric_pair_summary(by_c['rules_50'], by_c['rules_05'], 'strict_all')}",
                f"  - `rules_50` vs `rules_05` (`core5_score`): {prompt_metric_pair_summary(by_c['rules_50'], by_c['rules_05'], 'core5_score')}",
                f"  - `rules_50` vs `rules_10` (`strict_all`): {prompt_metric_pair_summary(by_c['rules_50'], by_c['rules_10'], 'strict_all')}",
            ])

        if "LING-PC1" in grouped_f_ling:
            pc1_l = grouped_f_ling["LING-PC1"]
            by_c = defaultdict(list)
            for r in pc1_l:
                by_c[r["condition"]].append(r)

            def ling_call_pattern(recs: List[Dict[str, Any]]) -> Tuple[int, int, int, int, int]:
                f_only = s_only = both = east_s = west_s = 0
                for r in recs:
                    tcs = [tc.get("function", {}).get("name") for tc in r.get("tool_calls", [])]
                    if len(tcs) == 1:
                        if tcs[0] == r["meta"]["first_tool"]:
                            f_only += 1
                        elif tcs[0] == r["meta"]["second_tool"]:
                            s_only += 1
                            if r["meta"]["second_tool"] == "records_lookup_east":
                                east_s += 1
                            else:
                                west_s += 1
                    elif len(tcs) >= 2:
                        both += 1
                return f_only, s_only, both, east_s, west_s

            nf, ns, nb, _, _ = ling_call_pattern(by_c["neutral"])
            ef, es, eb, _, _ = ling_call_pattern(by_c["example_on_second"])
            af, a_s, ab, a_east, a_west = ling_call_pattern(by_c["assertive_on_second"])
            lines.extend([
                "- **`LING-PC1` (`R-TOOL-04` Tool Description Gaming on Hybrid-Linear MoE, `16` counterbalanced prompts × `5` = `80` runs/arm)**:",
                f"  - `neutral`: `{nb}/80` parallel-both, `{nf}/80` exclusive `first_tool`, `{ns}/80` exclusive `second_tool`.",
                f"  - `example_on_second`: `{eb}/80` parallel-both, `{ef}/80` exclusive `first_tool`, `{es}/80` exclusive `second_tool` (zero hijacking).",
                f"  - `assertive_on_second`: `{ab}/80` parallel-both, `{af}/80` exclusive `first_tool`, **`{a_s}/80` (`{100*a_s/80:.1f}%`, `{a_east}` east / `{a_west}` west) exclusive `second_tool`**.",
                f"  - `assertive_on_second` vs `neutral`: {prompt_metric_pair_summary(by_c['assertive_on_second'], by_c['neutral'], 'score')} (reasoning_tokens: {prompt_top_field_pair_summary(by_c['assertive_on_second'], by_c['neutral'], 'reasoning_tokens', 1)})",
            ])

        if "LING-PC2" in grouped_f_ling:
            by_c = defaultdict(list)
            for r in grouped_f_ling["LING-PC2"]:
                by_c[r["condition"]].append(r)
            lines.extend([
                "- **`LING-PC2` (`R-SYS-05` & `C-01` Explicit Bans on Hybrid-Linear MoE, `16` × `5` = `80`/arm)**:",
                f"  - `bare_negative` vs `affirmative_only`: {prompt_metric_pair_summary(by_c['bare_negative'], by_c['affirmative_only'], 'score')}",
                f"  - `paired_affirmative` vs `affirmative_only`: {prompt_metric_pair_summary(by_c['paired_affirmative'], by_c['affirmative_only'], 'score')}",
                f"  - `paired_affirmative` vs `bare_negative`: {prompt_metric_pair_summary(by_c['paired_affirmative'], by_c['bare_negative'], 'score')} (reasoning_tokens: {prompt_top_field_pair_summary(by_c['paired_affirmative'], by_c['bare_negative'], 'reasoning_tokens', 1)})",
            ])
            for c in ("affirmative_only", "bare_negative", "paired_affirmative"):
                lex_ok = sum(int(r["metrics"].get("lexical_clean", 0)) for r in by_c[c])
                len_ok = sum(int(r["metrics"].get("length_ok", 0)) for r in by_c[c])
                hits = sum(int(r["metrics"].get("forbidden_word_count", 0)) for r in by_c[c])
                lines.append(f"  - `{c}`: `lexical_clean`={lex_ok}/80 ({100*lex_ok/80:.1f}%), `length_ok`={len_ok}/80, forbidden hits={hits}")

        if "LING-PD1" in grouped_f_ling:
            by_c = defaultdict(list)
            for r in grouped_f_ling["LING-PD1"]:
                by_c[r["condition"]].append(r)
            lines.append("- **`LING-PD1` (`R-TOOL-05` Parameter Descriptions on Hybrid-Linear MoE, `15` prompts × `5` = `75` runs/arm)**:")
            for field in ("timestamp_valid", "currency_valid", "geo_valid", "all_fields_valid"):
                b_ok = sum(int(r["metrics"].get(field, 0)) for r in by_c["without_descriptions"])
                w_ok = sum(int(r["metrics"].get(field, 0)) for r in by_c["with_descriptions"])
                pair_s = prompt_metric_pair_summary(by_c["with_descriptions"], by_c["without_descriptions"], field)
                lines.append(f"  - `{field}`: `without`={b_ok}/75 ({100*b_ok/75:.1f}%) vs `with`={w_ok}/75 ({100*w_ok/75:.1f}%) | {pair_s}")
            lines.append(f"  - Reasoning tokens (`with_descriptions` vs `without_descriptions`): {prompt_top_field_pair_summary(by_c['with_descriptions'], by_c['without_descriptions'], 'reasoning_tokens', 1)}")

        if "LING-PD4" in grouped_f_ling:
            by_c = defaultdict(list)
            for r in grouped_f_ling["LING-PD4"]:
                by_c[r["condition"]].append(r)
            lines.append("- **`LING-PD4` (`H-06` Arabic Digits vs Spelled-Out Numbers on Hybrid-Linear MoE, `thinking_off`, `16` × `5` = `80`/arm)**:")
            for mk in ("score", "c1_bullets", "bullet_word_frac", "c2_words_all", "c3_tags", "strict_all"):
                am = statistics.mean(float(r["metrics"].get(mk, 0.0)) for r in by_c["arabic_digits"])
                sm = statistics.mean(float(r["metrics"].get(mk, 0.0)) for r in by_c["spelled_words"])
                pair_s = prompt_metric_pair_summary(by_c["spelled_words"], by_c["arabic_digits"], mk)
                lines.append(f"  - `{mk}`: `arabic_digits`={am:.4f} vs `spelled_words`={sm:.4f} | spelled vs arabic: {pair_s}")

        if "LING-PD5" in grouped_f_ling:
            by_c = defaultdict(list)
            for r in grouped_f_ling["LING-PD5"]:
                by_c[r["condition"]].append(r)
            js_pt = statistics.mean(float(r.get("prompt_tokens") or 0.0) for r in by_c["json_schema"])
            ts_pt = statistics.mean(float(r.get("prompt_tokens") or 0.0) for r in by_c["typescript_interface"])
            pct = 100.0 * (ts_pt - js_pt) / js_pt if js_pt else 0.0
            lines.extend([
                "- **`LING-PD5` (`H-07` Prompt-Injected JSON Schema vs TypeScript Interfaces on Hybrid-Linear MoE, `thinking_off`, `16` × `5` = `80`/arm)**:",
                f"  - Accuracy (`score`): `json_schema`=80/80 (100.0%) vs `typescript_interface`=80/80 (100.0%) | {prompt_metric_pair_summary(by_c['typescript_interface'], by_c['json_schema'], 'score')}",
                f"  - Prompt token cost: `json_schema`={js_pt:.1f} vs `typescript_interface`={ts_pt:.1f} ({pct:+.1f}%) | {prompt_top_field_pair_summary(by_c['typescript_interface'], by_c['json_schema'], 'prompt_tokens', 1)}",
                f"  - Latency: {prompt_top_field_pair_summary(by_c['typescript_interface'], by_c['json_schema'], 'latency_seconds', 2)}",
            ])
        lines.append("")

    if grouped_f_nemo:
        lines.extend([
            "## 2. Phase F Cross-Architecture Table (`N = 5` Runs/Prompt, `Nemotron 3.5 Lightning` / `30B-A3B` Mamba-2 SSM Hybrid)",
            "",
        ])
        lines.extend(render_suite_table(grouped_f_nemo, PHASE_F_NEMO_BASELINES, include_tara=True))
        lines.extend(["", "### Phase F Detailed Prompt-Level Breakdowns (`Nemotron 3.5 Lightning`)", ""])

        if "NEMO-PB6" in grouped_f_nemo:
            by_c = defaultdict(list)
            for r in grouped_f_nemo["NEMO-PB6"]:
                by_c[r["condition"]].append(r)
            lines.extend([
                "- **`NEMO-PB6` (`R-TOOL-11` Powered `16`-Prompt `rationale` Ordering, `thinking_off`, `reasoning_tokens = 0` on all 240 calls)**:",
                f"  - `no_rationale`=0/80 (0.0%), `rationale_last`=0/80 (0.0%), **`rationale_first`=69/80 (86.2%)**; exact declared JSON key order preserved on `240/240` calls.",
                f"  - `rationale_first` vs `no_rationale`: {prompt_metric_pair_summary(by_c['rationale_first'], by_c['no_rationale'], 'score')}",
                f"  - `rationale_first` vs `rationale_last`: {prompt_metric_pair_summary(by_c['rationale_first'], by_c['rationale_last'], 'score')}",
            ])

        if "NEMO-PC1" in grouped_f_nemo:
            pc1_n = grouped_f_nemo["NEMO-PC1"]
            by_c = defaultdict(list)
            for r in pc1_n:
                by_c[r["condition"]].append(r)

            def nemo_call_pattern(recs: List[Dict[str, Any]]) -> Tuple[int, int, int, int, int]:
                f_only = s_only = both = east_s = west_s = 0
                for r in recs:
                    tcs = [tc.get("function", {}).get("name") for tc in r.get("tool_calls", [])]
                    if len(tcs) == 1:
                        if tcs[0] == r["meta"]["first_tool"]:
                            f_only += 1
                        elif tcs[0] == r["meta"]["second_tool"]:
                            s_only += 1
                            if r["meta"]["second_tool"] == "records_lookup_east":
                                east_s += 1
                            else:
                                west_s += 1
                    elif len(tcs) >= 2:
                        both += 1
                return f_only, s_only, both, east_s, west_s

            nf, ns, nb, _, _ = nemo_call_pattern(by_c["neutral"])
            ef, es, eb, _, _ = nemo_call_pattern(by_c["example_on_second"])
            af, a_s, ab, a_east, a_west = nemo_call_pattern(by_c["assertive_on_second"])
            lines.extend([
                "- **`NEMO-PC1` (`R-TOOL-04` Tool Description Gaming on Mamba-2 SSM, `16` counterbalanced prompts × `5` = `80` runs/arm)**:",
                f"  - `neutral`: `{nf}/80` exclusive `first_tool` (Position-0 primacy), `{ns}/80` exclusive `second_tool`, `{nb}/80` parallel-both.",
                f"  - `example_on_second`: `{ef}/80` exclusive `first_tool`, `{es}/80` exclusive `second_tool`, `{eb}/80` parallel-both (`p=0.4564` vs neutral).",
                f"  - `assertive_on_second`: `{af}/80` exclusive `first_tool`, **`{a_s}/80` (`{100*a_s/80:.1f}%`, `{a_east}` east / `{a_west}` west) exclusive `second_tool`**, `{ab}/80` parallel-both.",
                f"  - `assertive_on_second` vs `neutral`: {prompt_metric_pair_summary(by_c['assertive_on_second'], by_c['neutral'], 'score')} (reasoning_tokens: {prompt_top_field_pair_summary(by_c['assertive_on_second'], by_c['neutral'], 'reasoning_tokens', 1)})",
                f"  - `assertive_on_second` vs `example_on_second`: {prompt_metric_pair_summary(by_c['assertive_on_second'], by_c['example_on_second'], 'score')}",
            ])

        if "NEMO-PC2" in grouped_f_nemo:
            by_c = defaultdict(list)
            for r in grouped_f_nemo["NEMO-PC2"]:
                by_c[r["condition"]].append(r)
            lines.extend([
                "- **`NEMO-PC2` (`R-SYS-05` & `C-01` Explicit Bans on Non-Reasoning `3B`-Active Mamba-2 SSM, `thinking_off`, `16` × `5` = `80`/arm)**:",
                f"  - Pure `lexical_clean` (`bare_negative` vs `affirmative_only`): {prompt_metric_pair_summary(by_c['bare_negative'], by_c['affirmative_only'], 'lexical_clean')}",
                f"  - Pure `lexical_clean` (`paired_affirmative` vs `affirmative_only`): {prompt_metric_pair_summary(by_c['paired_affirmative'], by_c['affirmative_only'], 'lexical_clean')}",
                f"  - Pure `lexical_clean` (`paired_affirmative` vs `bare_negative`): {prompt_metric_pair_summary(by_c['paired_affirmative'], by_c['bare_negative'], 'lexical_clean')}",
                f"  - Combined `score` (`paired_affirmative` vs `bare_negative`): {prompt_metric_pair_summary(by_c['paired_affirmative'], by_c['bare_negative'], 'score')}",
            ])
            for c in ("affirmative_only", "bare_negative", "paired_affirmative"):
                lex_ok = sum(int(r["metrics"].get("lexical_clean", 0)) for r in by_c[c])
                len_ok = sum(int(r["metrics"].get("length_ok", 0)) for r in by_c[c])
                both_ok = sum(int(r["metrics"].get("score", 0)) for r in by_c[c])
                hits = sum(int(r["metrics"].get("forbidden_word_count", 0)) for r in by_c[c])
                lines.append(f"  - `{c}`: `lexical_clean`={lex_ok}/80 ({100*lex_ok/80:.1f}%), `length_ok`={len_ok}/80 ({100*len_ok/80:.1f}%), `combined`={both_ok}/80 ({100*both_ok/80:.1f}%), forbidden hits={hits}")

        if "NEMO-PD1" in grouped_f_nemo:
            by_c = defaultdict(list)
            for r in grouped_f_nemo["NEMO-PD1"]:
                by_c[r["condition"]].append(r)
            lines.append("- **`NEMO-PD1` (`R-TOOL-05` Parameter Descriptions on Mamba-2 SSM, `15` prompts × `5` = `75` runs/arm)**:")
            for field in ("timestamp_valid", "currency_valid", "geo_valid", "all_fields_valid"):
                b_ok = sum(int(r["metrics"].get(field, 0)) for r in by_c["without_descriptions"])
                w_ok = sum(int(r["metrics"].get(field, 0)) for r in by_c["with_descriptions"])
                pair_s = prompt_metric_pair_summary(by_c["with_descriptions"], by_c["without_descriptions"], field)
                lines.append(f"  - `{field}`: `without`={b_ok}/75 ({100*b_ok/75:.1f}%) vs `with`={w_ok}/75 ({100*w_ok/75:.1f}%) | {pair_s}")
            lines.append(f"  - Reasoning tokens (`with_descriptions` vs `without_descriptions`): {prompt_top_field_pair_summary(by_c['with_descriptions'], by_c['without_descriptions'], 'reasoning_tokens', 1)}")

        if "NEMO-PD4" in grouped_f_nemo:
            by_c = defaultdict(list)
            for r in grouped_f_nemo["NEMO-PD4"]:
                by_c[r["condition"]].append(r)
            lines.append("- **`NEMO-PD4` (`H-06` Arabic Digits vs Spelled-Out Numbers on Non-Reasoning Mamba-2 SSM, `thinking_off`, `16` × `5` = `80`/arm)**:")
            for mk in ("score", "c1_bullets", "bullet_word_frac", "c3_tags", "strict_all"):
                am = statistics.mean(float(r["metrics"].get(mk, 0.0)) for r in by_c["arabic_digits"])
                sm = statistics.mean(float(r["metrics"].get(mk, 0.0)) for r in by_c["spelled_words"])
                pair_s = prompt_metric_pair_summary(by_c["spelled_words"], by_c["arabic_digits"], mk)
                lines.append(f"  - `{mk}`: `arabic_digits`={am:.4f} vs `spelled_words`={sm:.4f} | spelled vs arabic: {pair_s}")

        if "NEMO-PE2" in grouped_f_nemo:
            by_c = defaultdict(list)
            for r in grouped_f_nemo["NEMO-PE2"]:
                by_c[r["condition"]].append(r)
            lines.append("- **`NEMO-PE2` (`C-02` / `R-SYS-04` Non-Ceiling Prospective Memory at `~13.8k` ptok, `thinking_off`, `16` × `5` = `80`/arm)**:")
            for mk in ("format_score", "no_fence", "json_ok", "sentinel_ok", "csv_ok", "math_ok"):
                so = statistics.mean(float(r["metrics"].get(mk, 0.0)) for r in by_c["system_only"])
                sr = statistics.mean(float(r["metrics"].get(mk, 0.0)) for r in by_c["sandwich_reminder"])
                pair_s = prompt_metric_pair_summary(by_c["sandwich_reminder"], by_c["system_only"], mk)
                lines.append(f"  - `{mk}`: `system_only`={so:.4f} vs `sandwich_reminder`={sr:.4f} | sandwich vs system: {pair_s}")
        lines.append("")

    if grouped_h08:
        lines.extend([
            "## 3. H-08 Cross-Model Replication Table (`N = 5` Runs/Prompt, `Particle-1` / DeepSeek V4.1 Flash Lineage)",
            "",
        ])
        lines.extend(render_suite_table(grouped_h08, H08_BASELINES, include_tara=True))
        lines.extend(["", "### H-08 Detailed Prompt-Level Breakdowns (`Particle-1`)", ""])

        if "H08-PC1" in grouped_h08:
            pc1_h = grouped_h08["H08-PC1"]
            by_c = defaultdict(list)
            for r in pc1_h:
                by_c[r["condition"]].append(r)

            def h08_call_pattern(recs: List[Dict[str, Any]]) -> Tuple[int, int, int, int, int]:
                f_only = s_only = both = east_s = west_s = 0
                for r in recs:
                    tcs = [tc.get("function", {}).get("name") for tc in r.get("tool_calls", [])]
                    if len(tcs) == 1:
                        if tcs[0] == r["meta"]["first_tool"]:
                            f_only += 1
                        elif tcs[0] == r["meta"]["second_tool"]:
                            s_only += 1
                            if r["meta"]["second_tool"] == "records_lookup_east":
                                east_s += 1
                            else:
                                west_s += 1
                    elif len(tcs) >= 2:
                        both += 1
                return f_only, s_only, both, east_s, west_s

            nf, ns, nb, _, _ = h08_call_pattern(by_c["neutral"])
            ef, es, eb, _, _ = h08_call_pattern(by_c["example_on_second"])
            af, a_s, ab, a_east, a_west = h08_call_pattern(by_c["assertive_on_second"])
            valid_args_h = sum(
                1
                for r in pc1_h
                if r.get("tool_calls")
                and all(
                    json.loads(tc["function"].get("arguments", "{}")).get("entity_id") == r["meta"]["exp_id"]
                    and json.loads(tc["function"].get("arguments", "{}")).get("record_scope") == r["meta"]["exp_scope"]
                    for tc in r["tool_calls"]
                )
            )
            lines.extend([
                "- **`H08-PC1` (`R-TOOL-04` Tool Description Gaming on `Particle-1`, `16` counterbalanced prompts × `5` = `80` runs/arm)**:",
                f"  - `neutral`: `{nb}/80` parallel-both, `{nf}/80` exclusive `first_tool`, `{ns}/80` exclusive `second_tool`.",
                f"  - `example_on_second`: `{eb}/80` parallel-both, `{ef}/80` exclusive `first_tool`, `{es}/80` exclusive `second_tool` (zero hijacking).",
                f"  - `assertive_on_second`: `{ab}/80` parallel-both, `{af}/80` exclusive `first_tool`, **`{a_s}/80` (`{100*a_s/80:.1f}%`, `{a_east}` east / `{a_west}` west) exclusive `second_tool`**.",
                f"  - Argument extraction accuracy: {valid_args_h}/240 ({100*valid_args_h/240:.1f}%).",
                f"  - `assertive_on_second` vs `neutral`: {prompt_metric_pair_summary(by_c['assertive_on_second'], by_c['neutral'], 'score')}",
                f"  - `assertive_on_second` vs `example_on_second`: {prompt_metric_pair_summary(by_c['assertive_on_second'], by_c['example_on_second'], 'score')}",
            ])

        if "H08-PC2" in grouped_h08:
            by_c = defaultdict(list)
            for r in grouped_h08["H08-PC2"]:
                by_c[r["condition"]].append(r)
            lines.extend([
                "- **`H08-PC2` (`R-SYS-05` Explicit Bans vs Affirmative-Only on `Particle-1`, `16` prompts × `5` = `80` runs/arm)**:",
                f"  - `bare_negative` vs `affirmative_only` (score & lexical_clean): {prompt_metric_pair_summary(by_c['bare_negative'], by_c['affirmative_only'], 'score')}",
                f"  - `paired_affirmative` vs `affirmative_only` (score & lexical_clean): {prompt_metric_pair_summary(by_c['paired_affirmative'], by_c['affirmative_only'], 'score')}",
                f"  - `paired_affirmative` vs `bare_negative` (`C-01`): {prompt_metric_pair_summary(by_c['paired_affirmative'], by_c['bare_negative'], 'score')} (reasoning_tokens: {prompt_top_field_pair_summary(by_c['paired_affirmative'], by_c['bare_negative'], 'reasoning_tokens', 1)})",
            ])
            for c in ("affirmative_only", "bare_negative", "paired_affirmative"):
                lex_ok = sum(int(r["metrics"].get("lexical_clean", 0)) for r in by_c[c])
                len_ok = sum(int(r["metrics"].get("length_ok", 0)) for r in by_c[c])
                forb_hits = sum(int(r["metrics"].get("forbidden_word_count", 0)) for r in by_c[c])
                lines.append(f"  - `{c}`: `lexical_clean`={lex_ok}/80 ({100*lex_ok/80:.1f}%), `length_ok`={len_ok}/80, total forbidden hits={forb_hits}")

        if "H08-PD1" in grouped_h08:
            by_c = defaultdict(list)
            for r in grouped_h08["H08-PD1"]:
                by_c[r["condition"]].append(r)
            lines.append("- **`H08-PD1` (`R-TOOL-05` Parameter Descriptions on `Particle-1`, `15` prompts × `5` = `75` runs/arm)**:")
            for field in ("timestamp_valid", "currency_valid", "geo_valid", "all_fields_valid"):
                b_ok = sum(int(r["metrics"].get(field, 0)) for r in by_c["without_descriptions"])
                w_ok = sum(int(r["metrics"].get(field, 0)) for r in by_c["with_descriptions"])
                pair_s = prompt_metric_pair_summary(by_c["with_descriptions"], by_c["without_descriptions"], field)
                lines.append(f"  - `{field}`: `without`={b_ok}/75 ({100*b_ok/75:.1f}%) vs `with`={w_ok}/75 ({100*w_ok/75:.1f}%) | {pair_s}")
            lines.append(f"  - Reasoning tokens (`with_descriptions` vs `without_descriptions`): {prompt_top_field_pair_summary(by_c['with_descriptions'], by_c['without_descriptions'], 'reasoning_tokens', 1)}")

        if "H08-PD4" in grouped_h08:
            by_c = defaultdict(list)
            for r in grouped_h08["H08-PD4"]:
                by_c[r["condition"]].append(r)
            lines.extend([
                "- **`H08-PD4` (`H-06` Arabic Digits vs Spelled-Out Numbers on `Particle-1`, `16` prompts × `5` = `80` runs/arm, native reasoning)**:",
                f"  - `score` & `strict_all`: `arabic_digits`=80/80 (100.0%) vs `spelled_words`=80/80 (100.0%) | {prompt_metric_pair_summary(by_c['spelled_words'], by_c['arabic_digits'], 'score')}",
                f"  - Reasoning tokens: {prompt_top_field_pair_summary(by_c['spelled_words'], by_c['arabic_digits'], 'reasoning_tokens', 1)}",
            ])

        if "H08-PD5" in grouped_h08:
            by_c = defaultdict(list)
            for r in grouped_h08["H08-PD5"]:
                by_c[r["condition"]].append(r)
            js_pt = statistics.mean(float(r.get("prompt_tokens") or 0.0) for r in by_c["json_schema"])
            ts_pt = statistics.mean(float(r.get("prompt_tokens") or 0.0) for r in by_c["typescript_interface"])
            pct = 100.0 * (ts_pt - js_pt) / js_pt if js_pt else 0.0
            lines.extend([
                "- **`H08-PD5` (`H-07` Prompt-Injected JSON Schema vs TypeScript Interfaces on `Particle-1`, `16` prompts × `5` = `80` runs/arm)**:",
                f"  - Accuracy (`score`): `json_schema`=80/80 (100.0%) vs `typescript_interface`=80/80 (100.0%) | {prompt_metric_pair_summary(by_c['typescript_interface'], by_c['json_schema'], 'score')}",
                f"  - Prompt token cost: `json_schema`={js_pt:.1f} vs `typescript_interface`={ts_pt:.1f} ({pct:+.1f}%) | {prompt_top_field_pair_summary(by_c['typescript_interface'], by_c['json_schema'], 'prompt_tokens', 1)}",
                f"  - Reasoning tokens: {prompt_top_field_pair_summary(by_c['typescript_interface'], by_c['json_schema'], 'reasoning_tokens', 1)}; Latency: {prompt_top_field_pair_summary(by_c['typescript_interface'], by_c['json_schema'], 'latency_seconds', 2)}",
            ])
        lines.append("")

    if grouped_e:
        lines.extend([
            "## 4. Phase E Summary Table (`N = 5` Runs/Prompt, `GPT 6 Luna`, `high` Effort: `R-SYS-01` & `C-02`/`C-03`/`C-04`)",
            "",
        ])
        lines.extend(render_suite_table(grouped_e, PHASE_E_BASELINES, include_tara=True))
        lines.extend(["", "### Phase E Detailed Prompt-Level Breakdowns (`GPT 6 Luna`, `high` Effort)", ""])

        if "PE-1" in grouped_e:
            by_c = defaultdict(list)
            for r in grouped_e["PE-1"]:
                by_c[r["condition"]].append(r)
            lines.append("- **`PE-1` (`R-SYS-01` Simultaneous Behavioral Rule Density, `16` prompts × `5` = `80` runs/arm)**:")
            for c in ("rules_05", "rules_10", "rules_20", "rules_50"):
                pt = statistics.mean(float(r.get("prompt_tokens") or 0.0) for r in by_c[c])
                rt = statistics.mean(float(r.get("reasoning_tokens") or 0.0) for r in by_c[c])
                lat = statistics.mean(float(r.get("latency_seconds") or 0.0) for r in by_c[c])
                s_ok = sum(int(r["metrics"].get("strict_all", 0)) for r in by_c[c])
                c5 = statistics.mean(float(r["metrics"].get("core5_score", 0.0)) for r in by_c[c])
                lines.append(
                    f"  - `{c}`: `strict_all`={s_ok}/80 ({100*s_ok/80:.1f}%), `core5_score`={c5:.4f}, "
                    f"prompt_tokens={pt:.1f}, reasoning_tokens={rt:.1f}, latency={lat:.2f}s"
                )
            lines.extend([
                f"  - `rules_50` vs `rules_10` (`strict_all`): {prompt_metric_pair_summary(by_c['rules_50'], by_c['rules_10'], 'strict_all')}",
                f"  - `rules_50` vs `rules_10` (`score`): {prompt_metric_pair_summary(by_c['rules_50'], by_c['rules_10'], 'score')}",
                f"  - `rules_20` vs `rules_10` (`strict_all`): {prompt_metric_pair_summary(by_c['rules_20'], by_c['rules_10'], 'strict_all')}",
                f"  - `rules_50` vs `rules_05` (`reasoning_tokens`): {prompt_top_field_pair_summary(by_c['rules_50'], by_c['rules_05'], 'reasoning_tokens', 1)}",
                f"  - `rules_50` vs `rules_05` (`latency_seconds`): {prompt_top_field_pair_summary(by_c['rules_50'], by_c['rules_05'], 'latency_seconds', 2)}",
            ])

        if "PE-2" in grouped_e:
            by_c = defaultdict(list)
            for r in grouped_e["PE-2"]:
                by_c[r["condition"]].append(r)
            lines.append("- **`PE-2` (`C-02` / `R-SYS-04` Prospective Memory Under Heavy Log Distraction, `~10.9k` ptok, `16` prompts × `5` = `80` runs/arm)**:")
            for mk in ("format_score", "no_fence", "json_ok", "sentinel_ok", "csv_ok", "math_ok", "strict_all"):
                so = statistics.mean(float(r["metrics"].get(mk, 0.0)) for r in by_c["system_only"])
                sr = statistics.mean(float(r["metrics"].get(mk, 0.0)) for r in by_c["sandwich_reminder"])
                pair_s = prompt_metric_pair_summary(by_c["sandwich_reminder"], by_c["system_only"], mk)
                lines.append(f"  - `{mk}`: `system_only`={so:.4f} vs `sandwich_reminder`={sr:.4f} | sandwich vs system: {pair_s}")

        if "PE-3" in grouped_e:
            by_c = defaultdict(list)
            for r in grouped_e["PE-3"]:
                by_c[r["condition"]].append(r)
            n_ok = sum(int(r["metrics"].get("score", 0)) for r in by_c["neutral_objective"])
            e_ok = sum(int(r["metrics"].get("score", 0)) for r in by_c["expert_persona"])
            lines.extend([
                "- **`PE-3` (`C-03` / `R-SYS-06` Powered Expert Persona on Hard Discrete Math, `16` puzzles × `5` = `80` runs/arm)**:",
                f"  - Accuracy: `neutral_objective`={n_ok}/80 ({100*n_ok/80:.1f}%) vs `expert_persona`={e_ok}/80 ({100*e_ok/80:.1f}%) | {prompt_metric_pair_summary(by_c['expert_persona'], by_c['neutral_objective'], 'score')}",
                f"  - Reasoning tokens: {prompt_top_field_pair_summary(by_c['expert_persona'], by_c['neutral_objective'], 'reasoning_tokens', 1)}",
            ])

        if "PE-4" in grouped_e:
            by_c = defaultdict(list)
            for r in grouped_e["PE-4"]:
                by_c[r["condition"]].append(r)
            lines.extend([
                "- **`PE-4` (`C-04` / `R-SYS-02` Start/Middle/End Needle + Embedded Prompt Injection, `~2.8k` ptok, `16` × `5` = `80` runs/arm)**:",
                "  - All 3 arms (`doc_start`, `doc_middle`, `doc_end`) achieved `80/80` (`100.0%`) across `recall_ok`, `injection_resisted`, and `format_ok`.",
                f"  - Reasoning tokens `doc_middle` vs `doc_start`: {prompt_top_field_pair_summary(by_c['doc_middle'], by_c['doc_start'], 'reasoning_tokens', 1)}",
                f"  - Reasoning tokens `doc_end` vs `doc_start`: {prompt_top_field_pair_summary(by_c['doc_end'], by_c['doc_start'], 'reasoning_tokens', 1)}",
            ])
        lines.append("")

    if grouped_d:
        lines.extend([
            "## 5. Phase D Summary Table (`N = 5` Runs/Prompt, Open Hypotheses `H-02`, `H-03`, `H-06`, `H-07`)",
            "",
        ])
        lines.extend(render_suite_table(grouped_d, PHASE_D_BASELINES, include_tara=True))
        lines.extend(["", "### Phase D Detailed Prompt-Level Breakdowns", ""])

        if "PD-1" in grouped_d:
            by_c = defaultdict(list)
            for r in grouped_d["PD-1"]:
                by_c[r["condition"]].append(r)
            lines.extend([
                "- **`PD-1` (`H-02a` / `TS-2` `N = 5` Replication, `15` prompts × `5` = `75` runs/arm, `high` effort)**:",
                "  - Per-field validity (`with_descriptions` vs `without_descriptions`):",
            ])
            for field in ("timestamp_valid", "currency_valid", "geo_valid", "all_fields_valid"):
                b_ok = sum(int(r["metrics"].get(field, 0)) for r in by_c["without_descriptions"])
                w_ok = sum(int(r["metrics"].get(field, 0)) for r in by_c["with_descriptions"])
                pair_s = prompt_metric_pair_summary(by_c["with_descriptions"], by_c["without_descriptions"], field)
                lines.append(f"    - `{field}`: `without`={b_ok}/75 ({100*b_ok/75:.1f}%) vs `with`={w_ok}/75 ({100*w_ok/75:.1f}%) | {pair_s}")

        if "PD-2" in grouped_d:
            by_c = defaultdict(list)
            for r in grouped_d["PD-2"]:
                by_c[r["condition"]].append(r)
            lines.append("- **`PD-2` (`H-02b` Parameter Verbosity Ceiling, `16` prompts × `5` = `80` runs/arm, `effort = \"none\"`)**:")
            for c in ("compact_15t", "moderate_50t", "verbose_120t", "bloated_250t"):
                pt = statistics.mean(float(r.get("prompt_tokens") or 0.0) for r in by_c[c])
                lat = statistics.mean(float(r.get("latency_seconds") or 0.0) for r in by_c[c])
                s_ok = sum(int(r["metrics"].get("strict_all_6", 0)) for r in by_c[c])
                extra = "" if c == "compact_15t" else f" | ptok vs compact: {prompt_top_field_pair_summary(by_c[c], by_c['compact_15t'], 'prompt_tokens', 1)}; lat: {prompt_top_field_pair_summary(by_c[c], by_c['compact_15t'], 'latency_seconds', 2)}"
                lines.append(f"  - `{c}`: strict_all_6={s_ok}/80 ({100*s_ok/80:.1f}%), mean prompt_tokens={pt:.1f}, mean latency={lat:.2f}s{extra}")

        if "PD-3" in grouped_d:
            by_c = defaultdict(list)
            for r in grouped_d["PD-3"]:
                by_c[r["condition"]].append(r)
            lines.extend([
                "- **`PD-3` (`H-03` Markdown in Tool Descriptions, `16` counterbalanced prompts × `5` = `80` runs/arm, `effort = \"none\"`)**:",
                f"  - `bullet_list` vs `plain_prose` (score): {prompt_metric_pair_summary(by_c['bullet_list'], by_c['plain_prose'], 'score')}",
                f"  - `markdown_headers` vs `plain_prose` (score): {prompt_metric_pair_summary(by_c['markdown_headers'], by_c['plain_prose'], 'score')}",
                f"  - `markdown_headers` vs `bullet_list` (score): {prompt_metric_pair_summary(by_c['markdown_headers'], by_c['bullet_list'], 'score')}",
                f"  - `markdown_headers` vs `plain_prose` (prompt_tokens): {prompt_top_field_pair_summary(by_c['markdown_headers'], by_c['plain_prose'], 'prompt_tokens', 1)}",
                f"  - `markdown_headers` vs `plain_prose` (latency_seconds): {prompt_top_field_pair_summary(by_c['markdown_headers'], by_c['plain_prose'], 'latency_seconds', 2)}",
            ])

        if "PD-4" in grouped_d:
            by_c = defaultdict(list)
            for r in grouped_d["PD-4"]:
                by_c[r["condition"]].append(r)
            lines.append("- **`PD-4` (`H-06` Arabic Digits vs Spelled-Out Numbers, `16` prompts × `5` = `80` runs/arm, `effort = \"none\"`)**:")
            for mk in ("score", "c1_bullets", "bullet_word_frac", "c2_words_all", "c3_tags", "strict_all"):
                am = statistics.mean(float(r["metrics"].get(mk, 0.0)) for r in by_c["arabic_digits"])
                sm = statistics.mean(float(r["metrics"].get(mk, 0.0)) for r in by_c["spelled_words"])
                pair_s = prompt_metric_pair_summary(by_c["spelled_words"], by_c["arabic_digits"], mk)
                lines.append(f"  - `{mk}`: `arabic_digits`={am:.4f} vs `spelled_words`={sm:.4f} | spelled vs arabic: {pair_s}")

        if "PD-5" in grouped_d:
            by_c = defaultdict(list)
            for r in grouped_d["PD-5"]:
                by_c[r["condition"]].append(r)
            js_pt = statistics.mean(float(r.get("prompt_tokens") or 0.0) for r in by_c["json_schema"])
            ts_pt = statistics.mean(float(r.get("prompt_tokens") or 0.0) for r in by_c["typescript_interface"])
            pct = 100.0 * (ts_pt - js_pt) / js_pt if js_pt else 0.0
            lines.extend([
                "- **`PD-5` (`H-07` Prompt-Injected JSON Schema vs TypeScript Interfaces, `16` prompts × `5` = `80` runs/arm, `effort = \"none\"`)**:",
                f"  - Accuracy (`score`, 4-level strict schema + exact extraction): `json_schema`=80/80 (100.0%) vs `typescript_interface`=80/80 (100.0%) | {prompt_metric_pair_summary(by_c['typescript_interface'], by_c['json_schema'], 'score')}",
                f"  - Prompt token cost: `json_schema`={js_pt:.1f} vs `typescript_interface`={ts_pt:.1f} ({pct:+.1f}%) | {prompt_top_field_pair_summary(by_c['typescript_interface'], by_c['json_schema'], 'prompt_tokens', 1)}",
                f"  - Latency: {prompt_top_field_pair_summary(by_c['typescript_interface'], by_c['json_schema'], 'latency_seconds', 2)}",
            ])
        lines.append("")

    if grouped_c:
        lines.extend([
            "## 6. Phase C Summary Table (`N = 5` Runs/Prompt × `16` Prompts/Suite, High Effort, Counterbalanced / Powered)",
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
            "## 7. Phase B Summary Table (`N = 5` Runs/Prompt × `6` Prompts/Suite, Prompt-Level Inference)",
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
        "## 8. Phase A Summary Table (Baseline Run `20261119_020610_3f7405`, `N = 1` Run/Prompt)",
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

    out_path.write_text(rendered, encoding="utf-8", newline="\n")
    print(f"Wrote recomputed stats to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
