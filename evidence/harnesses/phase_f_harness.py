# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Phase F (H-08 Cross-Architecture) Empirical Harness for agent-system-authoring.

Extends empirical validation beyond Transformer-only baselines (GPT 6 Luna & Particle-1)
to two architecturally distinct open-weight / hybrid families via OpenRouter:
  1. Ling 3.2 Flash (inclusionAI / Ant Group, ~560B-A25B Hybrid-Linear KDA+MLA MoE)
  2. Nemotron 3.5 Lightning (NVIDIA, 30B-A3B Mamba-2 SSM + MoE Hybrid)

Suites supported (all N = 5 runs/prompt, prompt-level paired inference):
  - PB6_16 (R-TOOL-11, thinking OFF, rtok=0): Powered 16-prompt expansion of PB-6
    (no_rationale vs rationale_first vs rationale_last; 16 x 3 x 5 = 240 calls)
  - PE1    (R-SYS-01, thinking OFF, rtok=0): Nested 5/10/20/50 behavioral rules
    (16 x 4 x 5 = 320 calls)
  - PE2    (C-02 / R-SYS-04, thinking OFF, rtok=0): ~13.6k noisy log distraction
    prospective memory (system_only vs sandwich_reminder; 16 x 2 x 5 = 160 calls)
  - PC1    (R-TOOL-04, default reasoning): Counterbalanced tool gaming (240 calls)
  - PC2    (R-SYS-05 & C-01): Explicit bans vs affirmative-only & paired (240 calls;
    default reasoning on Ling, thinking OFF on Nemotron to avoid >2k CoT truncation)
  - PD1    (R-TOOL-05, default reasoning): Parameter descriptions N=5 (150 calls)
  - PD4    (H-06, thinking OFF, rtok=0): Arabic digits vs spelled numbers (160 calls)
  - PD5    (H-07, thinking OFF, rtok=0): Prompt JSON Schema vs TypeScript (160 calls)

Configured solely via environment variables:
  - GATEWAY_URL
  - API_KEY
  - TARGET_MODEL

Writes sanitized JSONL records (stripped of auth headers & gateway URLs) to:
  - evidence/raw/phase_f_<prefix>/results_<PREFIX>-<SUITE>.jsonl
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import random
import sys
import threading
import time
from typing import Any, Dict, List, Optional, Tuple
import urllib.error
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase_b_harness as pb  # noqa: E402
import phase_c_harness as pc  # noqa: E402
import phase_d_harness as pd  # noqa: E402
import phase_e_harness as pe  # noqa: E402


DEFAULT_ITERATIONS = 5
DEFAULT_CONCURRENCY = 5


@dataclass
class RunConfig:
    gateway_url: str
    api_key: str
    model: str
    prefix: str
    iterations: int = DEFAULT_ITERATIONS
    concurrency: int = DEFAULT_CONCURRENCY
    max_retries: int = 8
    timeout: float = 120.0
    limit_prompts: Optional[int] = None


def post_chat_completion(
    cfg: RunConfig, payload: Dict[str, Any]
) -> Tuple[Optional[Dict[str, Any]], float, Optional[str]]:
    """Send POST /chat/completions with jittered exponential backoff for free/shared endpoints."""
    endpoint = cfg.gateway_url.rstrip("/")
    if not endpoint.endswith("/chat/completions"):
        endpoint += "/chat/completions"

    raw_bytes = json.dumps(payload).encode("utf-8")
    last_err: Optional[str] = None
    for attempt in range(1, cfg.max_retries + 1):
        t0 = time.time()
        req = urllib.request.Request(
            endpoint,
            data=raw_bytes,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {cfg.api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=cfg.timeout) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                return body, time.time() - t0, None
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")[:300]
            last_err = f"HTTP {e.code}: {err_body}"
            if e.code in (400, 401, 403, 404):
                return None, time.time() - t0, last_err
        except Exception as e:
            last_err = f"{type(e).__name__}: {e}"
        backoff = min(2.0 ** attempt, 30.0) + random.uniform(0.3, 1.8)
        time.sleep(backoff)
    return None, 0.0, last_err


def extract_fields(resp: Optional[Dict[str, Any]]) -> Tuple[str, List[Dict[str, Any]], int, int, int, int]:
    """Extract content, tool_calls, prompt_tokens, completion_tokens, reasoning_tokens, total_tokens."""
    if not resp:
        return "", [], 0, 0, 0, 0
    choices = resp.get("choices") or []
    msg = choices[0].get("message", {}) if choices else {}
    content = msg.get("content") or ""
    tool_calls = msg.get("tool_calls") or []
    usage = resp.get("usage") or {}
    details = usage.get("completion_tokens_details") or {}
    p_tok = int(usage.get("prompt_tokens") or 0)
    c_tok = int(usage.get("completion_tokens") or 0)
    r_tok = int(details.get("reasoning_tokens") or 0)
    tot_tok = int(usage.get("total_tokens") or 0)
    return content, tool_calls, p_tok, c_tok, r_tok, tot_tok


# ------------------------------------------------------------------------------
# Powered 16-Prompt PB-6 (R-TOOL-11): In-Schema rationale Ordering (thinking OFF)
# ------------------------------------------------------------------------------

class PB6_Powered16:
    """Extends Phase B's 6-prompt PB-6 suite to 16 brute-force-verified arithmetic scheduling tasks."""

    id = "PB6"
    PROBLEMS: List[Dict[str, Any]] = list(pb.PB6_InSchemaRationaleNoneEffort.PROBLEMS) + [
        {
            "id": "PB6_07",
            "prompt": (
                "Schedule compute job JOB-107. Two phases: Phase 1 is 35 minutes at 60 cents/min, "
                "Phase 2 is 45 minutes at 40 cents/min, plus a 600-cent cluster fee, followed by a 15% "
                "discount on the combined subtotal. Window starts at hour 16 and advances by 13 hours modulo 24. "
                "Buffer equals (total_minutes // 5) + 3."
            ),
            "exp_cost": 3825,  # (35*60 + 45*40 + 600) * 0.85 = (2100 + 1800 + 600) * 0.85 = 4500 * 0.85 = 3825
            "exp_hour": 5,     # (16 + 13) % 24 = 5
            "exp_buf": 19,     # (80 // 5) + 3 = 19
        },
        {
            "id": "PB6_08",
            "prompt": (
                "Schedule compute job JOB-108. Run 4 equal workers for 30 minutes each at 55 cents/worker-min, "
                "plus a 1,400-cent coordinator fee, then apply a 25% enterprise discount to the full subtotal. "
                "Start hour is 23 and advances by 9 hours modulo 24. Buffer is (30 * 4) // 6 + 5."
            ),
            "exp_cost": 6000,  # (4*30*55 + 1400) * 0.75 = (6600 + 1400) * 0.75 = 8000 * 0.75 = 6000
            "exp_hour": 8,     # (23 + 9) % 24 = 8
            "exp_buf": 25,     # 120 // 6 + 5 = 25
        },
        {
            "id": "PB6_09",
            "prompt": (
                "Schedule compute job JOB-109. Job runs 95 minutes: first 60 minutes cost 50 cents/min, "
                "remaining 35 minutes cost 80 cents/min, plus a 700-cent I/O surcharge, minus a 10% credit "
                "on the combined total. Start hour is 18 and advances by 15 hours modulo 24. "
                "Buffer equals (95 // 5) - 4."
            ),
            "exp_cost": 5850,  # (3000 + 2800 + 700) * 0.90 = 6500 * 0.90 = 5850
            "exp_hour": 9,     # (18 + 15) % 24 = 9
            "exp_buf": 15,     # 19 - 4 = 15
        },
        {
            "id": "PB6_10",
            "prompt": (
                "Schedule compute job JOB-110. Stage A takes 55 minutes at 40 cents/min, Stage B takes "
                "25 minutes at 90 cents/min, plus a 550-cent queue reservation fee, then a 20% discount "
                "on the whole sum. Start hour is 15 and advances by 17 hours modulo 24. "
                "Buffer equals (55 + 25) // 4 + 2."
            ),
            "exp_cost": 4000,  # (2200 + 2250 + 550) * 0.80 = 5000 * 0.80 = 4000
            "exp_hour": 8,     # (15 + 17) % 24 = 8
            "exp_buf": 22,     # 80 // 4 + 2 = 22
        },
        {
            "id": "PB6_11",
            "prompt": (
                "Schedule compute job JOB-111. 70 minutes at 65 cents/min plus a 450-cent snapshot fee, "
                "followed by a 12% discount on the combined subtotal. Window starts at hour 22 and advances "
                "by 14 hours modulo 24. Buffer is (70 // 2) - 11."
            ),
            "exp_cost": 4400,  # (4550 + 450) * 0.88 = 5000 * 0.88 = 4400
            "exp_hour": 12,    # (22 + 14) % 24 = 12
            "exp_buf": 24,     # 35 - 11 = 24
        },
        {
            "id": "PB6_12",
            "prompt": (
                "Schedule compute job JOB-112. Five shards run 20 minutes each at 75 cents/shard-min, "
                "plus a 900-cent network egress fee, minus a 15% volume rebate on the total. "
                "Start hour is 19 and advances by 19 hours modulo 24. Buffer is (5 * 20) // 4 - 3."
            ),
            "exp_cost": 7140,  # (7500 + 900) * 0.85 = 8400 * 0.85 = 7140
            "exp_hour": 14,    # (19 + 19) % 24 = 14
            "exp_buf": 22,     # 25 - 3 = 22
        },
        {
            "id": "PB6_13",
            "prompt": (
                "Schedule compute job JOB-113. First 40 minutes at 70 cents/min, next 50 minutes at 50 cents/min, "
                "plus a 700-cent checkpoint fee, with a 25% discount applied to the whole sum. "
                "Start hour is 21 and advances by 16 hours modulo 24. Buffer equals (90 // 3) - 7."
            ),
            "exp_cost": 4500,  # (2800 + 2500 + 700) * 0.75 = 6000 * 0.75 = 4500
            "exp_hour": 13,    # (21 + 16) % 24 = 13
            "exp_buf": 23,     # 30 - 7 = 23
        },
        {
            "id": "PB6_14",
            "prompt": (
                "Schedule compute job JOB-114. Stage A is 65 minutes at 40 cents/min, Stage B is 35 minutes "
                "at 80 cents/min, plus a 600-cent priority lock fee, then a 10% rebate on the entire subtotal. "
                "Start hour is 13 and advances by 20 hours modulo 24. Buffer equals (65 + 35) // 5 + 6."
            ),
            "exp_cost": 5400,  # (2600 + 2800 + 600) * 0.90 = 6000 * 0.90 = 5400
            "exp_hour": 9,     # (13 + 20) % 24 = 9
            "exp_buf": 26,     # 20 + 6 = 26
        },
        {
            "id": "PB6_15",
            "prompt": (
                "Schedule compute job JOB-115. Three parallel nodes run 40 minutes each at 45 cents/node-min, "
                "plus a 1,100-cent storage fee, followed by a 20% credit on the combined subtotal. "
                "Window starts at hour 17 and advances by 21 hours modulo 24. Buffer is (3 * 40) // 8 + 4."
            ),
            "exp_cost": 5200,  # (5400 + 1100) * 0.80 = 6500 * 0.80 = 5200
            "exp_hour": 14,    # (17 + 21) % 24 = 14
            "exp_buf": 19,     # 15 + 4 = 19
        },
        {
            "id": "PB6_16",
            "prompt": (
                "Schedule compute job JOB-116. Job runs 110 minutes: first 70 minutes at 60 cents/min, "
                "remaining 40 minutes at 45 cents/min, plus a 1,000-cent compliance audit fee, "
                "minus a 15% discount on the combined subtotal. Window starts at hour 20 and advances "
                "by 18 hours modulo 24. Buffer equals (110 // 5) - 5."
            ),
            "exp_cost": 5950,  # (4200 + 1800 + 1000) * 0.85 = 7000 * 0.85 = 5950
            "exp_hour": 14,    # (20 + 18) % 24 = 14
            "exp_buf": 17,     # 22 - 5 = 17
        },
    ]

    @classmethod
    def generate_items(cls, cfg: RunConfig) -> List[Dict[str, Any]]:
        probs = cls.PROBLEMS[: cfg.limit_prompts] if cfg.limit_prompts else cls.PROBLEMS
        items: List[Dict[str, Any]] = []
        for it in range(1, cfg.iterations + 1):
            for p in probs:
                for cond in ("no_rationale", "rationale_first", "rationale_last"):
                    items.append({
                        "hypothesis_id": f"{cfg.prefix}-PB6",
                        "source_suite": "PB-6-16",
                        "prompt_id": p["id"],
                        "condition": cond,
                        "iteration": it,
                        "reasoning_effort": "thinking_off",
                        "payload": {
                            "model": cfg.model,
                            "messages": [
                                {
                                    "role": "system",
                                    "content": (
                                        "You are a job scheduler. Compute exact integer values and invoke "
                                        "schedule_compute_job immediately with the exact calculated arguments."
                                    ),
                                },
                                {"role": "user", "content": p["prompt"]},
                            ],
                            "tools": pb.PB6_InSchemaRationaleNoneEffort._tools(cond),
                            "tool_choice": {"type": "function", "function": {"name": "schedule_compute_job"}},
                            "reasoning": {"enabled": False},
                            "max_tokens": 1024,
                        },
                        "meta": {
                            "exp_cost": p["exp_cost"],
                            "exp_hour": p["exp_hour"],
                            "exp_buf": p["exp_buf"],
                        },
                    })
        return items

    @classmethod
    def evaluate(cls, item: Dict[str, Any], text: str, tool_calls: List[Dict[str, Any]]) -> Dict[str, Any]:
        ev = pb.PB6_InSchemaRationaleNoneEffort.evaluate(item, text, tool_calls)
        # Also record raw JSON key order to verify no server-side alphabetical key reordering occurred
        keys: List[str] = []
        if tool_calls:
            try:
                keys = list(json.loads(tool_calls[0].get("function", {}).get("arguments") or "{}").keys())
            except Exception:
                keys = []
        ev["emitted_keys"] = keys
        return ev


# Suite registry mapping short suite names to (source_cls, default_thinking_off, default_max_tokens)
SUITE_SPECS: Dict[str, Tuple[Any, bool, int]] = {
    "PB6": (PB6_Powered16, True, 1024),
    "PE1": (pe.PE1_RuleDensityScaling, True, 2048),
    "PE2": (pe.PE2_HeavyProspectiveMemory, True, 1024),
    "PC1": (pc.PC1_CounterbalancedToolGaming, False, 4096),
    "PC2": (pc.PC2_PoweredNegationVsAffirmative, False, 8192),
    "PD1": (pd.PD1_TS2Replication, False, 4096),
    "PD4": (pd.PD4_ArabicVsSpelledNumbers, True, 1024),
    "PD5": (pd.PD5_JsonSchemaVsTypeScript, True, 2048),
}

MODEL_PRESETS: Dict[str, Dict[str, Any]] = {
    "LING": {
        "suites": ["PB6", "PE1", "PC1", "PC2", "PD1", "PD4", "PD5"],
        "thinking_off_overrides": {},  # PC1/PC2/PD1 use default thinking ON; PB6/PE1/PD4/PD5 use thinking OFF
    },
    "NEMO": {
        "suites": ["PB6", "PE2", "PC1", "PC2", "PD1", "PD4"],
        "thinking_off_overrides": {"PC2": True},  # Nemotron default CoT exceeds 2k tok on PC2; run thinking OFF
    },
}


def build_items_for_suite(
    cfg: RunConfig, suite_key: str, thinking_off_override: Optional[bool] = None
) -> Tuple[Any, List[Dict[str, Any]]]:
    suite_cls, default_off, max_tok = SUITE_SPECS[suite_key]
    think_off = default_off if thinking_off_override is None else thinking_off_override
    hyp_id = f"{cfg.prefix}-{suite_key}"

    if suite_key == "PB6":
        return suite_cls, suite_cls.generate_items(cfg)

    if suite_key in ("PC1", "PC2"):
        sub_cfg = pc.RunConfig(
            gateway_url=cfg.gateway_url,
            api_key=cfg.api_key,
            model=cfg.model,
            iterations=cfg.iterations,
            concurrency=cfg.concurrency,
            reasoning_effort="default",
        )
        raw_items = suite_cls.generate_items(sub_cfg)
        if cfg.limit_prompts:
            keep = sorted({it["prompt_id"] for it in raw_items})[: cfg.limit_prompts]
            raw_items = [it for it in raw_items if it["prompt_id"] in keep]
    elif suite_key in ("PD1", "PD4", "PD5"):
        sub_cfg = pd.RunConfig(
            gateway_url=cfg.gateway_url,
            api_key=cfg.api_key,
            model=cfg.model,
            iterations=cfg.iterations,
            concurrency=cfg.concurrency,
            limit_prompts=cfg.limit_prompts,
        )
        raw_items = suite_cls.generate_items(sub_cfg)
    else:  # PE1, PE2
        sub_cfg = pe.RunConfig(
            gateway_url=cfg.gateway_url,
            api_key=cfg.api_key,
            model=cfg.model,
            iterations=cfg.iterations,
            concurrency=cfg.concurrency,
            reasoning_effort="default",
            limit_prompts=cfg.limit_prompts,
        )
        raw_items = suite_cls.generate_items(sub_cfg)

    cleaned: List[Dict[str, Any]] = []
    for it in raw_items:
        payload = dict(it["payload"])
        payload.pop("reasoning_effort", None)
        if think_off:
            payload["reasoning"] = {"enabled": False}
            effort_tag = "thinking_off"
        else:
            payload.pop("reasoning", None)
            effort_tag = "native_default"
        payload["max_tokens"] = max_tok
        cleaned.append({
            "hypothesis_id": hyp_id,
            "source_suite": suite_cls.id,
            "prompt_id": it["prompt_id"],
            "condition": it["condition"],
            "iteration": it["iteration"],
            "reasoning_effort": effort_tag,
            "payload": payload,
            "meta": it["meta"],
        })
    return suite_cls, cleaned


def run_suite(
    cfg: RunConfig,
    suite_key: str,
    out_dir: Path,
    run_id: str,
    thinking_off_override: Optional[bool] = None,
) -> Tuple[int, int]:
    suite_cls, items = build_items_for_suite(cfg, suite_key, thinking_off_override)
    hyp_id = f"{cfg.prefix}-{suite_key}"
    out_path = out_dir / f"results_{hyp_id}.jsonl"
    lock = threading.Lock()
    records: List[Dict[str, Any]] = []

    def worker(item: Dict[str, Any]) -> Dict[str, Any]:
        resp, dt, err = post_chat_completion(cfg, item["payload"])
        text, tool_calls, p_tok, c_tok, r_tok, tot_tok = extract_fields(resp)
        metrics = suite_cls.evaluate(item, text, tool_calls) if err is None else {"score": 0.0}
        return {
            "run_id": run_id,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "hypothesis_id": item["hypothesis_id"],
            "source_suite": item["source_suite"],
            "prompt_id": item["prompt_id"],
            "condition": item["condition"],
            "iteration": item["iteration"],
            "model": cfg.model,
            "reasoning_effort": item["reasoning_effort"],
            "latency_seconds": round(dt, 3),
            "prompt_tokens": p_tok,
            "completion_tokens": c_tok,
            "reasoning_tokens": r_tok,
            "total_tokens": tot_tok,
            "error": err,
            "response_id": resp.get("id") if resp else None,
            "request_payload": item["payload"],
            "response_text": text,
            "tool_calls": tool_calls,
            "meta": item["meta"],
            "metrics": metrics,
        }

    with out_path.open("w", encoding="utf-8", newline="\n") as fh:
        with ThreadPoolExecutor(max_workers=cfg.concurrency) as pool:
            futs = [pool.submit(worker, it) for it in items]
            for fut in as_completed(futs):
                rec = fut.result()
                with lock:
                    records.append(rec)
                    fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    fh.flush()

    errs = sum(1 for r in records if r["error"] is not None)
    by_c: Dict[str, List[float]] = {}
    for r in records:
        by_c.setdefault(r["condition"], []).append(float(r["metrics"].get("score", 0.0)))
    cond_summary = ", ".join(f"{c}={sum(v)/len(v):.3f}" for c, v in sorted(by_c.items()))
    print(f"[{hyp_id}] completed {len(records)} records (errors={errs}) [{cond_summary}] -> {out_path}", flush=True)
    return len(records), errs


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute Phase F cross-architecture suites (Ling 3.2 Flash & Nemotron 3.5 Lightning).")
    parser.add_argument("--prefix", required=True, choices=["LING", "NEMO"], help="Model suite prefix (LING or NEMO).")
    parser.add_argument("--suites", nargs="+", default=None, choices=list(SUITE_SPECS.keys()))
    parser.add_argument("--iterations", type=int, default=DEFAULT_ITERATIONS)
    parser.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY)
    parser.add_argument("--model", default=os.environ.get("TARGET_MODEL", ""))
    parser.add_argument("--limit-prompts", type=int, default=None)
    parser.add_argument("--out-dir", default=None)
    args = parser.parse_args()

    gw = os.environ.get("GATEWAY_URL", "").strip()
    key = os.environ.get("API_KEY", "").strip()
    if not gw or not key:
        print("ERROR: GATEWAY_URL and API_KEY environment variables are required.", file=sys.stderr)
        return 1
    if not args.model:
        print("ERROR: TARGET_MODEL environment variable or --model flag is required.", file=sys.stderr)
        return 1

    preset = MODEL_PRESETS[args.prefix]
    suites = args.suites if args.suites else preset["suites"]
    overrides = preset["thinking_off_overrides"]

    cfg = RunConfig(
        gateway_url=gw,
        api_key=key,
        model=args.model,
        prefix=args.prefix,
        iterations=args.iterations,
        concurrency=args.concurrency,
        limit_prompts=args.limit_prompts,
    )
    default_dir = Path(__file__).resolve().parent.parent / "raw" / f"phase_f_{args.prefix.lower()}"
    out_dir = Path(args.out_dir).resolve() if args.out_dir else default_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime(f"%Y%m%d_%H%M%S_{args.prefix.lower()}")

    tot_n, tot_e = 0, 0
    for sk in suites:
        n, e = run_suite(cfg, sk, out_dir, run_id, thinking_off_override=overrides.get(sk))
        tot_n += n
        tot_e += e
    print(f"Phase F ({args.prefix}) total: {tot_n} records, {tot_e} errors.", flush=True)
    return 0 if tot_e == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
