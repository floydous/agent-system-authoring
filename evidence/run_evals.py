# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Live Evaluation Runner for evals/evals.json against an OpenAI-compatible endpoint.

Executes:
- Part A (Triggering Suite): 10 cases (5 positive, 5 near-miss negative) x N iterations
  using a realistic 6-skill registry router (reasoning_effort: low).
- Part B (Comparative Authoring Suite): 3 comparative tasks x 2 arms (baseline vs with_skill)
  x N iterations (reasoning_effort: medium) with deterministic programmatic rubric scoring.

Configured solely via environment variables:
  - GATEWAY_URL
  - API_KEY
  - TARGET_MODEL (provenance evals ran on GPT 6 Luna)

Writes raw JSONL traces (stripped of URLs and auth headers) to
evidence/raw_evals/results_evals.jsonl and renders evidence/evals_results.md.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import re
import statistics
import sys
import threading
import time
from typing import Any, Dict, List, Optional, Tuple
import urllib.error
import urllib.request


DEFAULT_MODEL = os.environ.get("TARGET_MODEL", "")
DEFAULT_ITERATIONS = 5
DEFAULT_CONCURRENCY = 8

DISTRACTOR_SKILLS = [
    {
        "name": "sql-query-runner",
        "description": "Executes read-only SQL SELECT queries directly against PostgreSQL or analytics tables and formats tabular results. Use when running ad-hoc SQL queries against existing schemas, not when authoring JSON tool definitions.",
    },
    {
        "name": "python-debugger",
        "description": "Diagnoses runtime tracebacks, IndexErrors, type mismatches, and failing Python application modules. Use when debugging or patching Python source code.",
    },
    {
        "name": "stripe-support-ops",
        "description": "Processes end-user Stripe refunds, subscription cancellations, and customer receipt emails using billing operations tools. Use when handling live support tickets.",
    },
    {
        "name": "frontend-css-styler",
        "description": "Refactors HTML, CSS, flexbox, grid layouts, and color-contrast themes for responsive web UI components. Use when modifying frontend stylesheets.",
    },
    {
        "name": "git-workflow-helper",
        "description": "Stages files, composes commit messages, manages branches, and pushes commits to Git remotes. Use when performing git version-control actions.",
    },
]


def betacf(a: float, b: float, x: float) -> float:
    max_iter = 200
    eps = 3.0e-12
    fpmin = 1.0e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
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
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    bt = math.exp(
        math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log(1.0 - x)
    )
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * betacf(a, b, x) / a
    return 1.0 - bt * betacf(b, a, 1.0 - x) / b


def student_t_p(t_stat: float, df: int) -> float:
    if df <= 0 or t_stat == 0.0:
        return 1.0
    return min(1.0, max(0.0, betainc(0.5 * df, 0.5, df / (df + t_stat * t_stat))))


def extract_skill_metadata_and_body(skill_md: Path) -> Tuple[str, str, str]:
    """Return (name, description, full_body) from SKILL.md."""
    raw = skill_md.read_text(encoding="utf-8")
    lines = raw.splitlines()
    end_idx = lines.index("---", 1)
    fm_lines = lines[1:end_idx]
    name = ""
    desc = ""
    for line in fm_lines:
        if line.startswith("name:"):
            name = line.split(":", 1)[1].strip().strip("'\"")
        elif line.startswith("description:"):
            desc = line.split(":", 1)[1].strip().strip("'\"")
    body = "\n".join(lines[end_idx + 1 :]).strip()
    return name, desc, body


def post_chat(gateway_url: str, api_key: str, payload: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], float, Optional[str]]:
    endpoint = gateway_url.rstrip("/")
    if not endpoint.endswith("/chat/completions"):
        endpoint += "/chat/completions"
    data = json.dumps(payload).encode("utf-8")
    last_err: Optional[str] = None
    for attempt in range(1, 5):
        t0 = time.time()
        req = urllib.request.Request(
            endpoint,
            data=data,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=90.0) as resp:
                return json.loads(resp.read().decode("utf-8")), time.time() - t0, None
        except urllib.error.HTTPError as e:
            last_err = f"HTTP {e.code}: {e.read().decode('utf-8', errors='replace')[:250]}"
            if e.code in (400, 401, 403, 404):
                return None, time.time() - t0, last_err
        except Exception as e:
            last_err = f"{type(e).__name__}: {e}"
        time.sleep(min(2.0 ** attempt, 12.0))
    return None, 0.0, last_err


def score_comparative_01(text: str) -> Dict[str, Any]:
    s = text or ""
    low = s.lower()
    headers = re.findall(r"^###\s+.+$", s, re.MULTILINE)
    has_nested_constraint = "<constraint" in low
    flat_delimiters = 1.0 if (len(headers) >= 3 and not has_nested_constraint) else 0.0

    bullets = re.findall(r"^\s*(?:\d+\.|-|\*)\s+.+$", s, re.MULTILINE)
    has_phases = bool(re.search(r"(?:phase|step|stage)\s*[1-9]|###", low))
    constraint_segmentation = 1.0 if (has_phases and 2 <= len(bullets) <= 24) else 0.0

    privilege_hierarchy = 1.0 if (
        ("untrusted" in low or "hierarchy" in low or "developer > user" in low or "tool data" in low or "retrieved" in low)
        and ("ignore" in low or "never follow" in low or "passive data" in low or "no authority" in low or "treat" in low)
    ) else 0.0

    tail = "\n".join(s.splitlines()[-15:]).lower()
    sandwich_reminder = 1.0 if ("reminder" in low or "trailing" in low or "output" in tail or "format" in tail) and len(headers) >= 3 else 0.0

    anti_personas = ["world-class", "award-winning", "fields medalist", "turing", "25 years of experience"]
    anti_cot = ["think step-by-step", "think step by step", "step-by-step reasoning"]
    anti_pattern_detection = 1.0 if (not any(p in low for p in anti_personas + anti_cot)) else 0.0

    checks = {
        "flat_delimiters": flat_delimiters,
        "constraint_segmentation": constraint_segmentation,
        "privilege_hierarchy": privilege_hierarchy,
        "sandwich_reminder": sandwich_reminder,
        "anti_pattern_detection": anti_pattern_detection,
    }
    checks["score"] = sum(checks.values()) / len(checks)
    return checks


def _extract_json_objects(text: str) -> List[Dict[str, Any]]:
    objs: List[Dict[str, Any]] = []
    dec = json.JSONDecoder()
    s = text or ""
    i = 0
    while i < len(s):
        idx = s.find("{", i)
        if idx < 0:
            break
        try:
            obj, end = dec.raw_decode(s, idx)
            if isinstance(obj, dict):
                objs.append(obj)
            i = end
        except Exception:
            i = idx + 1
    return objs


def score_comparative_02(text: str) -> Dict[str, Any]:
    s = text or ""
    low = s.lower()
    objs = _extract_json_objects(s)
    schema: Dict[str, Any] = {}
    for o in objs:
        if "properties" in o or "parameters" in o or ("function" in o and isinstance(o["function"], dict)):
            schema = o
            break

    fn_node = schema.get("function", schema) if isinstance(schema, dict) else {}
    params = fn_node.get("parameters", fn_node) if isinstance(fn_node, dict) else {}
    props = params.get("properties", {}) if isinstance(params, dict) else {}
    prop_names = list(props.keys()) if isinstance(props, dict) else []

    snake_re = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")
    fn_name = str(fn_node.get("name", "")) if isinstance(fn_node, dict) else ""
    naming = 1.0 if (bool(prop_names) and (not fn_name or snake_re.match(fn_name)) and all(snake_re.match(k) for k in prop_names)) else 0.0

    desc = str(fn_node.get("description", "")) if isinstance(fn_node, dict) else ""
    sentences = [x for x in re.split(r"[.!?]+(?:\s+|$)", desc.strip()) if x.strip()]
    neg_markers = ["do not", "don't", "never use", "instead", "not for"]
    detailed_description = 1.0 if (len(sentences) >= 3 and any(m in desc.lower() for m in neg_markers)) else 0.0

    first_prop = prop_names[0].lower() if prop_names else ""
    rationale_ok_name = first_prop in {"rationale", "explanation", "reason", "justification"}
    asks_thinking = "step-by-step thinking" in low or "step by step thinking" in low
    rationale_ordering = 1.0 if (rationale_ok_name and not asks_thinking) else 0.0

    parameter_descriptions = 1.0 if (
        bool(props)
        and all(isinstance(v, dict) and len(str(v.get("description", "")).strip()) >= 12 for v in props.values())
    ) else 0.0

    reqs = params.get("required", []) if isinstance(params, dict) else []
    add_props = params.get("additionalProperties", True) if isinstance(params, dict) else True
    is_strict = fn_node.get("strict") is True or params.get("strict") is True or schema.get("strict") is True
    strict_schema = 1.0 if (
        bool(prop_names) and add_props is False and set(prop_names) == set(reqs) and is_strict
    ) else 0.0

    gaming_terms = ["best tool", "preferred tool", "invoke whenever possible", "always use this", "fastest sql"]
    anti_pattern_detection = 1.0 if not any(g in desc.lower() for g in gaming_terms) else 0.0

    checks = {
        "naming": naming,
        "detailed_description": detailed_description,
        "rationale_ordering": rationale_ordering,
        "parameter_descriptions": parameter_descriptions,
        "strict_schema": strict_schema,
        "anti_pattern_detection": anti_pattern_detection,
    }
    checks["score"] = sum(checks.values()) / len(checks)
    return checks


def score_comparative_03(text: str) -> Dict[str, Any]:
    s = text or ""
    low = s.lower()
    directory_layout = 1.0 if ("skill.md" in low and "references/" in low and ("scripts/" in low or "assets/" in low)) else 0.0
    frontmatter = 1.0 if ("name: data-pipeline-auditing" in low and "description:" in low and ("use when" in low or "when " in low)) else 0.0
    progressive_disclosure = 1.0 if ("500" in low and ("5000" in low or "5,000" in low) and "references/" in low) else 0.0
    shallow_linking = 1.0 if (("one level" in low or "single-hop" in low or "single hop" in low) and ("../" in low or "chain" in low)) else 0.0
    packaging_hygiene = 1.0 if (
        ("__pycache__" in low or "cache" in low)
        and ("credential" in low or "api key" in low or "secret" in low)
        and ("tests/" in low or "mock" in low)
    ) else 0.0
    script_portability = 1.0 if (("# /// script" in low or "pep 723" in low) and "verify_skill.py" in low) else 0.0

    checks = {
        "directory_layout": directory_layout,
        "frontmatter": frontmatter,
        "progressive_disclosure": progressive_disclosure,
        "shallow_linking": shallow_linking,
        "packaging_hygiene": packaging_hygiene,
        "script_portability": script_portability,
    }
    checks["score"] = sum(checks.values()) / len(checks)
    return checks


COMPARATIVE_SCORERS = {
    "comparative_01_customer_support_system_prompt": score_comparative_01,
    "comparative_02_sql_tool_schema_authoring": score_comparative_02,
    "comparative_03_agent_skill_package_design": score_comparative_03,
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute evals/evals.json against gateway model.")
    parser.add_argument("--iterations", type=int, default=DEFAULT_ITERATIONS)
    parser.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--rescore-only", action="store_true", help="Recompute scores/report from existing JSONL traces.")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    out_dir = root / "evidence" / "raw_evals"
    out_jsonl = out_dir / "results_evals.jsonl"

    if args.rescore_only:
        records = [json.loads(ln) for ln in out_jsonl.read_text(encoding="utf-8").splitlines() if ln.strip()]
        for r in records:
            if r["kind"] == "comparative" and r.get("error") is None:
                r["metrics"] = COMPARATIVE_SCORERS[r["eval_id"]](r.get("response_text", ""))
        out_jsonl.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n", encoding="utf-8")
        run_id = records[0]["run_id"]
        errors = sum(1 for r in records if r.get("error") is not None)
    else:
        gw = os.environ.get("GATEWAY_URL", "").strip()
        key = os.environ.get("API_KEY", "").strip()
        if not gw or not key:
            print("ERROR: GATEWAY_URL and API_KEY must be set in environment.", file=sys.stderr)
            return 1

        skill_name, skill_desc, skill_body = extract_skill_metadata_and_body(root / "SKILL.md")
        evals_data = json.loads((root / "evals" / "evals.json").read_text(encoding="utf-8"))["evals"]

        registry = [{"name": skill_name, "description": skill_desc}] + DISTRACTOR_SKILLS
        registry_text = "\n".join(f"- {s['name']}: {s['description']}" for s in registry)
        allowed_choices = [s["name"] for s in registry] + ["none"]

        router_schema = {
            "type": "json_schema",
            "json_schema": {
                "name": "skill_routing_decision",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "selected_skill": {"type": "string", "enum": allowed_choices},
                        "reason": {"type": "string"},
                    },
                    "required": ["selected_skill", "reason"],
                    "additionalProperties": False,
                },
            },
        }

        router_sys = (
            "You are an agent skill router. Given the user's request and the installed skill registry below, "
            "activate the single matching skill ONLY if the user's request falls squarely within its scope; "
            "otherwise select 'none'.\n\nInstalled Skills:\n" + registry_text
        )

        jobs: List[Dict[str, Any]] = []
        for it in range(1, args.iterations + 1):
            for ev in evals_data:
                if ev["type"] in ("trigger_positive", "trigger_negative"):
                    jobs.append({
                        "kind": ev["type"],
                        "id": ev["id"],
                        "condition": "trigger",
                        "iteration": it,
                        "should_trigger": bool(ev["should_trigger"]),
                        "payload": {
                            "model": args.model,
                            "messages": [
                                {"role": "system", "content": router_sys},
                                {"role": "user", "content": ev["prompt"]},
                            ],
                            "response_format": router_schema,
                            "reasoning_effort": "low",
                        },
                    })
                elif ev["type"] == "comparative":
                    for cond in ("baseline", "with_skill"):
                        sys_msg = (
                            "You are a helpful AI assistant."
                            if cond == "baseline"
                            else f"Follow the agent-system-authoring skill specification rigorously to satisfy the user's request.\n\n{skill_body}"
                        )
                        jobs.append({
                            "kind": "comparative",
                            "id": ev["id"],
                            "condition": cond,
                            "iteration": it,
                            "should_trigger": None,
                            "payload": {
                                "model": args.model,
                                "messages": [
                                    {"role": "system", "content": sys_msg},
                                    {"role": "user", "content": ev["prompt"]},
                                ],
                                "reasoning_effort": "medium",
                            },
                        })

        out_dir.mkdir(parents=True, exist_ok=True)
        run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_evals")
        lock = threading.Lock()
        records: List[Dict[str, Any]] = []

        def worker(job: Dict[str, Any]) -> Dict[str, Any]:
            resp, dt, err = post_chat(gw, key, job["payload"])
            text = ""
            r_tok = 0
            tot_tok = 0
            resp_id = None
            if resp:
                resp_id = resp.get("id")
                choices = resp.get("choices") or []
                if choices:
                    text = (choices[0].get("message") or {}).get("content") or ""
                usage = resp.get("usage") or {}
                r_tok = int((usage.get("completion_tokens_details") or {}).get("reasoning_tokens") or 0)
                tot_tok = int(usage.get("total_tokens") or 0)

            if job["kind"] in ("trigger_positive", "trigger_negative"):
                selected = None
                try:
                    selected = json.loads(text).get("selected_skill")
                except Exception:
                    pass
                activated = (selected == skill_name)
                passed = 1.0 if (activated == job["should_trigger"]) else 0.0
                metrics = {"selected_skill": selected, "activated": activated, "score": passed}
            else:
                metrics = COMPARATIVE_SCORERS[job["id"]](text) if err is None else {"score": 0.0}

            return {
                "run_id": run_id,
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "eval_id": job["id"],
                "kind": job["kind"],
                "condition": job["condition"],
                "iteration": job["iteration"],
                "model": args.model,
                "reasoning_effort": job["payload"]["reasoning_effort"],
                "latency_seconds": round(dt, 3),
                "reasoning_tokens": r_tok,
                "total_tokens": tot_tok,
                "error": err,
                "response_id": resp_id,
                "response_text": text,
                "metrics": metrics,
            }

        with out_jsonl.open("w", encoding="utf-8") as fh:
            with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
                futs = [pool.submit(worker, j) for j in jobs]
                for fut in as_completed(futs):
                    rec = fut.result()
                    with lock:
                        records.append(rec)
                        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                        fh.flush()

        errors = sum(1 for r in records if r["error"] is not None)
        print(f"Executed {len(records)} eval calls (errors={errors}).")

    # Compute summary report
    trig_pos = [r for r in records if r["kind"] == "trigger_positive"]
    trig_neg = [r for r in records if r["kind"] == "trigger_negative"]
    tp = sum(1 for r in trig_pos if r["metrics"]["activated"])
    fn = len(trig_pos) - tp
    fp = sum(1 for r in trig_neg if r["metrics"]["activated"])
    tn = len(trig_neg) - fp
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec_rate = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * prec * rec_rate / (prec + rec_rate)) if (prec + rec_rate) else 0.0

    by_trig_id = defaultdict(list)
    for r in trig_pos + trig_neg:
        by_trig_id[r["eval_id"]].append(r)

    comp = [r for r in records if r["kind"] == "comparative"]
    by_comp = defaultdict(lambda: defaultdict(list))
    for r in comp:
        by_comp[r["eval_id"]][r["condition"]].append(r)

    md: List[str] = [
        "# Evaluation Suite Results (`evals/evals.json`)",
        "",
        f"- **Target Model**: `{args.model}` (run `{run_id}`, `0` errors across `{len(records)}` calls)" if errors == 0 else f"- **Target Model**: `{args.model}` (run `{run_id}`, `{errors}` errors)",
        f"- **Iterations**: `N = {args.iterations}` runs per prompt (`reasoning_effort=\"low\"` for triggering; `\"medium\"` for comparative authoring)",
        f"- **Raw Traces**: `evidence/raw_evals/results_evals.jsonl` (`{len(records)}` records)",
        "",
        "## 1. Triggering Accuracy Summary (50 Calls Across 6-Skill Registry)",
        "",
        f"- **True Positives (TP)**: {tp}/{len(trig_pos)} | **False Negatives (FN)**: {fn}/{len(trig_pos)}",
        f"- **True Negatives (TN)**: {tn}/{len(trig_neg)} | **False Positives (FP)**: {fp}/{len(trig_neg)}",
        f"- **Precision**: `{prec:.4f}` ({100*prec:.1f}%) | **Recall**: `{rec_rate:.4f}` ({100*rec_rate:.1f}%) | **F1**: `{f1:.4f}`",
        "",
        "| Eval ID | Type | Pass Rate (`N=5`) | `TARa@5` | Selected Outputs |",
        "| :--- | :--- | :---: | :---: | :--- |",
    ]
    for eid in sorted(by_trig_id.keys()):
        rs = by_trig_id[eid]
        ok = sum(1 for r in rs if r["metrics"]["score"] == 1.0)
        uniq = sorted({str(r["metrics"]["selected_skill"]) for r in rs})
        tara = "1/1 (100%)" if len(uniq) == 1 else "0/1 (0%)"
        md.append(f"| `{eid}` | `{rs[0]['kind']}` | {ok}/{len(rs)} ({100*ok/len(rs):.0f}%) | {tara} | `{', '.join(uniq)}` |")

    md.extend([
        "",
        "## 2. Comparative Authoring Quality (30 Calls, Programmatic Rubric)",
        "",
        "| Eval ID | `baseline` Mean (SD) | `with_skill` Mean (SD) | Delta | Paired t / p-value (across N=5 repeats) |",
        "| :--- | :---: | :---: | :---: | :---: |",
    ])
    all_base_scores: List[float] = []
    all_skill_scores: List[float] = []
    for eid in sorted(by_comp.keys()):
        bs = sorted(by_comp[eid]["baseline"], key=lambda x: x["iteration"])
        ws = sorted(by_comp[eid]["with_skill"], key=lambda x: x["iteration"])
        b_sc = [float(r["metrics"]["score"]) for r in bs]
        w_sc = [float(r["metrics"]["score"]) for r in ws]
        all_base_scores.extend(b_sc)
        all_skill_scores.extend(w_sc)
        diffs = [w - b for w, b in zip(w_sc, b_sc)]
        m_d = statistics.mean(diffs)
        sd_d = statistics.stdev(diffs) if len(diffs) >= 2 else 0.0
        if sd_d > 0:
            t_v = m_d / (sd_d / math.sqrt(len(diffs)))
            p_v = student_t_p(t_v, len(diffs) - 1)
            stat_s = f"t={t_v:.2f}, p={p_v:.4f}"
        else:
            stat_s = "no diff" if m_d == 0 else f"delta={m_d:+.3f}, sd_diff=0"
        md.append(
            f"| `{eid}` | {statistics.mean(b_sc):.3f} ({statistics.stdev(b_sc):.3f}) | "
            f"{statistics.mean(w_sc):.3f} ({statistics.stdev(w_sc):.3f}) | **{m_d:+.3f}** | {stat_s} |"
        )

    tot_diffs = [w - b for w, b in zip(all_skill_scores, all_base_scores)]
    overall_m = statistics.mean(tot_diffs)
    overall_sd = statistics.stdev(tot_diffs)
    overall_t = overall_m / (overall_sd / math.sqrt(len(tot_diffs))) if overall_sd > 0 else 0.0
    overall_p = student_t_p(overall_t, len(tot_diffs) - 1) if overall_sd > 0 else 1.0
    md.extend([
        "",
        f"**Overall Comparative Lift (`N = {len(tot_diffs)}` paired runs)**: `baseline` = `{statistics.mean(all_base_scores):.3f}` vs `with_skill` = `{statistics.mean(all_skill_scores):.3f}` (**delta = `{overall_m:+.3f}`**, `t = {overall_t:.2f}`, `p = {overall_p:.3e}`).",
        "",
    ])

    report_path = root / "evidence" / "evals_results.md"
    report_path.write_text("\n".join(md), encoding="utf-8")
    print(f"Wrote eval report to {report_path}")
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
