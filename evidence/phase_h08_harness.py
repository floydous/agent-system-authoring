# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""H-08 Cross-Model Generalization Harness for agent-system-authoring.

Replicates the five highest-signal empirical suites identically across a second
model family (provenance run targets Particle-1 / DeepSeek V4.1 Flash lineage
via OpenRouter) using the exact same tasks, schemas, and evaluators as Phases C & D:
- H08-PC1 (R-TOOL-04): Counterbalanced tool description gaming (16 x 3 x 5 = 240 calls)
- H08-PC2 (R-SYS-05): Explicit bans vs affirmative-only & paired (16 x 3 x 5 = 240 calls)
- H08-PD1 (R-TOOL-05): Parameter descriptions N=5 replication (15 x 2 x 5 = 150 calls)
- H08-PD4 (H-06): Arabic digits vs spelled-out numbers (16 x 2 x 5 = 160 calls)
- H08-PD5 (H-07): Prompt-injected JSON Schema vs TypeScript interfaces (16 x 2 x 5 = 160 calls)

Configured solely via environment variables:
  - GATEWAY_URL
  - API_KEY
  - TARGET_MODEL (e.g., openrouter/particle-ai/particle-1:free)

Writes raw records (stripped of auth headers and gateway URLs) to
evidence/raw_h08_particle1/results_<SUITE>.jsonl (or --out-dir).
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

# Reuse exact canonical suite definitions and evaluators from Phase C and Phase D
sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase_c_harness as pc  # noqa: E402
import phase_d_harness as pd  # noqa: E402


DEFAULT_MODEL = os.environ.get("TARGET_MODEL", "")
DEFAULT_ITERATIONS = 5
DEFAULT_CONCURRENCY = 4


@dataclass
class RunConfig:
    gateway_url: str
    api_key: str
    model: str = DEFAULT_MODEL
    iterations: int = DEFAULT_ITERATIONS
    concurrency: int = DEFAULT_CONCURRENCY
    include_reasoning_effort: bool = False
    reasoning_effort: str = "default"
    max_retries: int = 7
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
        backoff = min(2.0 ** attempt, 25.0) + random.uniform(0.2, 1.5)
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


REPLICATION_SUITES: Dict[str, Any] = {
    "H08-PC1": pc.PC1_CounterbalancedToolGaming,
    "H08-PC2": pc.PC2_PoweredNegationVsAffirmative,
    "H08-PD1": pd.PD1_TS2Replication,
    "H08-PD4": pd.PD4_ArabicVsSpelledNumbers,
    "H08-PD5": pd.PD5_JsonSchemaVsTypeScript,
}


def build_items_for_suite(h08_id: str, cfg: RunConfig) -> List[Dict[str, Any]]:
    """Generate identical items from Phase C / Phase D suites, stripping OpenAI-only reasoning_effort unless requested."""
    suite_cls = REPLICATION_SUITES[h08_id]
    if h08_id in ("H08-PC1", "H08-PC2"):
        sub_cfg = pc.RunConfig(
            gateway_url=cfg.gateway_url,
            api_key=cfg.api_key,
            model=cfg.model,
            iterations=cfg.iterations,
            concurrency=cfg.concurrency,
            reasoning_effort=cfg.reasoning_effort,
        )
        raw_items = suite_cls.generate_items(sub_cfg)
        if cfg.limit_prompts:
            keep_ids = sorted({it["prompt_id"] for it in raw_items})[: cfg.limit_prompts]
            raw_items = [it for it in raw_items if it["prompt_id"] in keep_ids]
    else:
        sub_cfg = pd.RunConfig(
            gateway_url=cfg.gateway_url,
            api_key=cfg.api_key,
            model=cfg.model,
            iterations=cfg.iterations,
            concurrency=cfg.concurrency,
            limit_prompts=cfg.limit_prompts,
        )
        raw_items = suite_cls.generate_items(sub_cfg)

    cleaned: List[Dict[str, Any]] = []
    for it in raw_items:
        payload = dict(it["payload"])
        if not cfg.include_reasoning_effort:
            payload.pop("reasoning_effort", None)
        cleaned.append({
            "hypothesis_id": h08_id,
            "source_suite": suite_cls.id,
            "prompt_id": it["prompt_id"],
            "condition": it["condition"],
            "iteration": it["iteration"],
            "reasoning_effort": cfg.reasoning_effort if cfg.include_reasoning_effort else "native_default",
            "payload": payload,
            "meta": it["meta"],
        })
    return cleaned


def run_suite(cfg: RunConfig, h08_id: str, out_dir: Path, run_id: str) -> Tuple[int, int]:
    suite_cls = REPLICATION_SUITES[h08_id]
    items = build_items_for_suite(h08_id, cfg)
    out_path = out_dir / f"results_{h08_id}.jsonl"
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
    print(f"[{h08_id}] completed {len(records)} records (errors={errs}) [{cond_summary}] -> {out_path}")
    return len(records), errs


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute H-08 cross-model replication suites (PC-1, PC-2, PD-1, PD-4, PD-5).")
    parser.add_argument("--suites", nargs="+", default=list(REPLICATION_SUITES.keys()), choices=list(REPLICATION_SUITES.keys()))
    parser.add_argument("--iterations", type=int, default=DEFAULT_ITERATIONS)
    parser.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--include-reasoning-effort", action="store_true")
    parser.add_argument("--effort", default="high")
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

    cfg = RunConfig(
        gateway_url=gw,
        api_key=key,
        model=args.model,
        iterations=args.iterations,
        concurrency=args.concurrency,
        include_reasoning_effort=args.include_reasoning_effort,
        reasoning_effort=args.effort,
        limit_prompts=args.limit_prompts,
    )
    out_dir = Path(args.out_dir).resolve() if args.out_dir else (Path(__file__).resolve().parent / "raw_h08_particle1")
    out_dir.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_h08")

    tot_n, tot_e = 0, 0
    for sid in args.suites:
        n, e = run_suite(cfg, sid, out_dir, run_id)
        tot_n += n
        tot_e += e
    print(f"H-08 total: {tot_n} records, {tot_e} errors.")
    return 0 if tot_e == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
