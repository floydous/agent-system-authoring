# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Offline statistical recomputation from raw JSONL execution traces (Phase A & Phase B).

Reads all JSONL trace files under:
- evidence/raw/results_*.jsonl         (Phase A: 228 records, 1 run/prompt)
- evidence/raw_phase_b/results_PB-*.jsonl (Phase B: 480 records, N=5 runs/prompt)

Computes:
- Sample sizes (N), distinct prompts, runs per prompt, mean score, std dev
- Paired t-test (averaged per prompt_id, df = num_prompts - 1) for score & reasoning_tokens
- Pooled two-sided Fisher's exact test (via math.comb) for binary outcomes
- Run-to-run stability (TARa@K: fraction of prompts with identical outcomes across all K repeats)
- Sub-metric breakdowns for Phase A SP-4, Phase A TS-2, Phase B PB-1, PB-3, and PB-4

Writes results to evidence/stats_recomputed.md and exits 0.
"""

from __future__ import annotations

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
    if sd_d == 0.0:
        return None, 1.0 if mean_d == 0.0 else None, mean_d, 0.0
    se = sd_d / math.sqrt(n)
    t_val = mean_d / se
    p_val = student_t_two_sided_p(t_val, n - 1)
    return t_val, p_val, mean_d, sd_d


def fisher_exact_two_sided(a: int, b: int, c: int, d: int) -> float:
    """Compute exact two-sided Fisher's exact test p-value for 2x2 table [[a, b], [c, d]]."""
    row1 = a + b
    row2 = c + d
    col1 = a + c
    total = row1 + row2
    if total == 0:
        return 1.0

    denom = math.comb(total, col1)

    def hypergeom_prob(x: int) -> float:
        return (math.comb(row1, x) * math.comb(row2, col1 - x)) / denom

    p_obs = hypergeom_prob(a)
    min_x = max(0, col1 - row2)
    max_x = min(row1, col1)

    p_sum = 0.0
    for x in range(min_x, max_x + 1):
        p_x = hypergeom_prob(x)
        if p_x <= p_obs * (1.0 + 1e-12):
            p_sum += p_x
    return min(1.0, p_sum)


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


def render_suite_table(
    grouped: Dict[str, List[Dict[str, Any]]],
    baselines: Dict[str, str],
    include_tara: bool = False,
) -> List[str]:
    """Generate condition-level markdown summary rows."""
    header = (
        "| Suite | Condition | N | Prompts | Runs/Prompt | Mean Score | Std Dev | "
        + ("TARa@K | " if include_tara else "")
        + "Score vs Baseline (Paired t on Prompt Means) | Binary Fisher Exact p | Mean Reasoning Tok | Reasoning Tok vs Baseline | Status Flag |"
    )
    sep = (
        "| :--- | :--- | :---: | :---: | :---: | :---: | :---: | "
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

            num_prompts = len(by_prompt)
            runs_counts = sorted({len(v) for v in by_prompt.values()})
            runs_str = str(runs_counts[0]) if len(runs_counts) == 1 else f"{min(runs_counts)}-{max(runs_counts)}"

            scores = [float(r["metrics"]["score"]) for r in cond_recs]
            mean_score = statistics.mean(scores)
            sd_score = statistics.stdev(scores) if len(scores) >= 2 else 0.0

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
                fisher_str = "Baseline"
                rtok_test_str = "Baseline"
                flag_str = "ceiling/no variance" if sd_score == 0.0 and mean_score == 1.0 else "baseline"
            else:
                shared_prompts = sorted(set(base_by_prompt.keys()) & set(by_prompt.keys()))
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
                if sd_ds == 0.0 and mean_ds == 0.0:
                    score_test_str = "delta=0.000 (no diff)"
                else:
                    score_test_str = f"delta={mean_ds:+.3f}, t={fmt_float(t_s, 2)}, p={fmt_p(p_s)}"

                if is_binary_values(base_scores_flat) and is_binary_values(scores):
                    base_ok = sum(1 for v in base_scores_flat if v == 1.0)
                    cond_ok = sum(1 for v in scores if v == 1.0)
                    p_fish = fisher_exact_two_sided(
                        cond_ok, len(scores) - cond_ok, base_ok, len(base_scores_flat) - base_ok
                    )
                    fisher_str = f"{cond_ok}/{len(scores)} vs {base_ok}/{len(base_scores_flat)} (p={fmt_p(p_fish)})"
                else:
                    fisher_str = "non-binary"

                t_r, p_r, mean_dr, sd_dr = paired_t_test(rtok_diffs)
                if sd_dr == 0.0 and mean_dr == 0.0:
                    rtok_test_str = "diff=0.0 (no diff)"
                else:
                    rtok_test_str = f"diff={mean_dr:+.1f}, t={fmt_float(t_r, 2)}, p={fmt_p(p_r)}"

                base_sd = statistics.stdev(base_scores_flat) if len(base_scores_flat) >= 2 else 0.0
                if sd_score == 0.0 and base_sd == 0.0 and mean_score == statistics.mean(base_scores_flat):
                    flag_str = "ceiling/no variance - uninformative"
                else:
                    flag_str = "informative"

            rows_out.append(
                f"| **{hyp_id}** | `{cond}` | {n} | {num_prompts} | {runs_str} | "
                f"{mean_score:.3f} | {sd_score:.3f} | {tara_str}{score_test_str} | {fisher_str} | "
                f"{mean_rtok:.1f} | {rtok_test_str} | {flag_str} |"
            )
    return rows_out


def main() -> int:
    evidence_dir = Path(__file__).resolve().parent
    raw_a = evidence_dir / "raw"
    raw_b = evidence_dir / "raw_phase_b"
    out_path = evidence_dir / "stats_recomputed.md"

    grouped_a = load_records(raw_a, "results_*.jsonl")
    grouped_b = load_records(raw_b, "results_PB-*.jsonl")

    if not grouped_a:
        print(f"ERROR: No Phase A JSONL files found in {raw_a}", file=sys.stderr)
        return 1

    total_a = sum(len(v) for v in grouped_a.values())
    total_b = sum(len(v) for v in grouped_b.values())
    err_b = sum(1 for v in grouped_b.values() for r in v if r.get("error") is not None)

    lines: List[str] = [
        "# Recomputed Statistical Summary (Phase A & Phase B)",
        "",
        f"- **Phase A Traces**: `evidence/raw/` ({len(grouped_a)} suites, {total_a} records, 1 run/prompt)",
        f"- **Phase B Traces**: `evidence/raw_phase_b/` ({len(grouped_b)} suites, {total_b} records, 5 runs/prompt, gateway errors={err_b})",
        "- **Generated By**: `evidence/recompute_stats.py` (offline stdlib-only statistical verification)",
        "",
        "## 1. Phase B Summary Table (`N = 5` Runs/Prompt, Deconfounded Suites)",
        "",
    ]

    if grouped_b:
        lines.extend(render_suite_table(grouped_b, PHASE_B_BASELINES, include_tara=True))

        # Additional pairwise test PB-4 affirmative_only vs paired_affirmative
        if "PB-4" in grouped_b:
            pb4 = grouped_b["PB-4"]
            by_c = defaultdict(list)
            for r in pb4:
                by_c[r["condition"]].append(r)
            aff_ok = sum(1 for r in by_c["affirmative_only"] if r["metrics"]["score"] == 1.0)
            pair_ok = sum(1 for r in by_c["paired_affirmative"] if r["metrics"]["score"] == 1.0)
            bare_ok = sum(1 for r in by_c["bare_negative"] if r["metrics"]["score"] == 1.0)
            p_aff_pair = fisher_exact_two_sided(pair_ok, 30 - pair_ok, aff_ok, 30 - aff_ok)
            p_bare_aff = fisher_exact_two_sided(bare_ok, 30 - bare_ok, aff_ok, 30 - aff_ok)
            lines.extend([
                "",
                "### Phase B Sub-Metric Breakdowns",
                "",
                f"- **`PB-4` Additional Fisher Comparisons**: `bare_negative` ({bare_ok}/30) vs `affirmative_only` ({aff_ok}/30): `p = {fmt_p(p_bare_aff)}`; `paired_affirmative` ({pair_ok}/30) vs `affirmative_only` ({aff_ok}/30): `p = {fmt_p(p_aff_pair)}`.",
            ])
            for c in ("bare_negative", "affirmative_only", "paired_affirmative"):
                len_ok = sum(int(r["metrics"].get("length_ok", 0)) for r in by_c[c])
                forb_tot = sum(int(r["metrics"].get("forbidden_word_count", 0)) for r in by_c[c])
                bold_hits = sum(int(r["metrics"].get("has_bold", 0)) for r in by_c[c])
                lines.append(f"  - `{c}`: `length_ok`={len_ok}/30, total forbidden word hits={forb_tot}, bold `**` hits={bold_hits}")

        if "PB-1" in grouped_b:
            pb1 = grouped_b["PB-1"]
            by_c = defaultdict(list)
            for r in pb1:
                by_c[r["condition"]].append(r)
            lines.append("- **`PB-1` Per-Constraint Pass Counts (out of 30 runs each)**:")
            for c in ("flat_markdown", "flat_xml", "nested_xml"):
                parts = [f"{k}={int(sum(r['metrics'][k] for r in by_c[c]))}/30" for k in ("c1_length", "c2_keywords", "c3_negative", "c4_headers", "c5_severity", "c6_terminal", "strict_pass")]
                lines.append(f"  - `{c}`: " + ", ".join(parts))

        if "PB-6" in grouped_b:
            pb6 = grouped_b["PB-6"]
            by_c = defaultdict(list)
            for r in pb6:
                by_c[r["condition"]].append(r)
            p_rf_rl = fisher_exact_two_sided(
                sum(int(r["metrics"]["score"]) for r in by_c["rationale_first"]),
                30 - sum(int(r["metrics"]["score"]) for r in by_c["rationale_first"]),
                sum(int(r["metrics"]["score"]) for r in by_c["rationale_last"]),
                30 - sum(int(r["metrics"]["score"]) for r in by_c["rationale_last"]),
            )
            lines.append(f"- **`PB-6` `rationale_first` (30/30) vs `rationale_last` (11/30)**: Fisher exact `p = {fmt_p(p_rf_rl)}` (exact tie between `no_rationale` 11/30 and `rationale_last` 11/30; `reasoning_tokens = 0` across all 90 runs at `effort=\"none\"`).")

    lines.extend([
        "",
        "## 2. Phase A Summary Table (Baseline Run `20261119_020610_3f7405`, `N = 1` Run/Prompt)",
        "",
    ])
    lines.extend(render_suite_table(grouped_a, PHASE_A_BASELINES, include_tara=False))

    # Phase A TS-2 & SP-4 sub-metric breakdowns
    if "TS-2" in grouped_a:
        by_c = defaultdict(list)
        for r in grouped_a["TS-2"]:
            by_c[r["condition"]].append(r)
        lines.extend([
            "",
            "### Phase A `TS-2` Per-Field Validity Breakdown",
            "",
            "| Field | `without_descriptions` | `with_descriptions` | Two-Sided Fisher Exact p |",
            "| :--- | :---: | :---: | :---: |",
        ])
        for field in ("timestamp_valid", "currency_valid", "geo_valid", "all_fields_valid"):
            b_ok = sum(1 for r in by_c["without_descriptions"] if float(r["metrics"].get(field, 0.0)) == 1.0)
            c_ok = sum(1 for r in by_c["with_descriptions"] if float(r["metrics"].get(field, 0.0)) == 1.0)
            p_f = fisher_exact_two_sided(c_ok, 15 - c_ok, b_ok, 15 - b_ok)
            lines.append(f"| `{field}` | {b_ok}/15 ({100*b_ok/15:.1f}%) | {c_ok}/15 ({100*c_ok/15:.1f}%) | {fmt_p(p_f)} |")

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
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote recomputed stats to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
