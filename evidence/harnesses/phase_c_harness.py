# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Phase C Empirical Test Harness for agent-system-authoring.

Executes deconfounded, higher-powered (N = 16 prompts x 5 repeats = 80/arm)
experiments on GPT 6 Luna across two suites:
- PC-1 (R-TOOL-04): Counterbalanced symmetric tool gaming (16 prompts, 50/50 order)
- PC-2 (R-SYS-05 / C-01): Powered lexical prohibition vs affirmative-only vs paired

Configured solely via environment variables:
  - GATEWAY_URL
  - API_KEY
  - TARGET_MODEL (provenance traces ran on GPT 6 Luna)

Writes raw records (stripped of auth headers and gateway URLs) to
evidence/raw/phase_c/results_<SUITE>.jsonl.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sys
import threading
import time
from typing import Any, Dict, List, Optional, Tuple
import urllib.error
import urllib.request


DEFAULT_MODEL = os.environ.get("TARGET_MODEL", "")
DEFAULT_ITERATIONS = 5
DEFAULT_CONCURRENCY = 8
DEFAULT_EFFORT = "high"


@dataclass
class RunConfig:
    gateway_url: str
    api_key: str
    model: str = DEFAULT_MODEL
    iterations: int = DEFAULT_ITERATIONS
    concurrency: int = DEFAULT_CONCURRENCY
    reasoning_effort: str = DEFAULT_EFFORT
    max_retries: int = 5
    timeout: float = 120.0


def post_chat_completion(
    cfg: RunConfig, payload: Dict[str, Any]
) -> Tuple[Optional[Dict[str, Any]], float, Optional[str]]:
    """Send POST /chat/completions with exponential backoff retry."""
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
        time.sleep(min(2.0 ** attempt, 12.0))
    return None, 0.0, last_err


def extract_fields(resp: Optional[Dict[str, Any]]) -> Tuple[str, List[Dict[str, Any]], int, int]:
    """Extract assistant content, tool_calls, reasoning_tokens, and total_tokens."""
    if not resp:
        return "", [], 0, 0
    choices = resp.get("choices") or []
    msg = choices[0].get("message", {}) if choices else {}
    content = msg.get("content") or ""
    tool_calls = msg.get("tool_calls") or []
    usage = resp.get("usage") or {}
    details = usage.get("completion_tokens_details") or {}
    r_tok = int(details.get("reasoning_tokens") or 0)
    tot_tok = int(usage.get("total_tokens") or 0)
    return content, tool_calls, r_tok, tot_tok


# ------------------------------------------------------------------------------
# PC-1: Counterbalanced Symmetric Tool Gaming (R-TOOL-04)
# ------------------------------------------------------------------------------

class PC1_CounterbalancedToolGaming:
    id = "PC-1"
    TASKS = [
        {"id": "PC1_01", "query": "Look up full entity records for identifier 'ENT-8831'.", "exp_id": "ENT-8831", "exp_scope": "full"},
        {"id": "PC1_02", "query": "Retrieve the basic account snapshot for entity 'ENT-1049'.", "exp_id": "ENT-1049", "exp_scope": "basic"},
        {"id": "PC1_03", "query": "Fetch the audit trail record for account 'ENT-5520'.", "exp_id": "ENT-5520", "exp_scope": "audit"},
        {"id": "PC1_04", "query": "Pull up full directory profile details for 'ENT-9014'.", "exp_id": "ENT-9014", "exp_scope": "full"},
        {"id": "PC1_05", "query": "Get the basic overview profile for entity 'ENT-6190'.", "exp_id": "ENT-6190", "exp_scope": "basic"},
        {"id": "PC1_06", "query": "Check audit-level compliance history for 'ENT-4819'.", "exp_id": "ENT-4819", "exp_scope": "audit"},
        {"id": "PC1_07", "query": "Obtain full entity profile data for 'ENT-2374'.", "exp_id": "ENT-2374", "exp_scope": "full"},
        {"id": "PC1_08", "query": "Query basic registration record for 'ENT-7742'.", "exp_id": "ENT-7742", "exp_scope": "basic"},
        {"id": "PC1_09", "query": "Look up full profile details for entity 'ENT-3195'.", "exp_id": "ENT-3195", "exp_scope": "full"},
        {"id": "PC1_10", "query": "Retrieve basic account metadata for 'ENT-6608'.", "exp_id": "ENT-6608", "exp_scope": "basic"},
        {"id": "PC1_11", "query": "Fetch the audit event log for entity 'ENT-9412'.", "exp_id": "ENT-9412", "exp_scope": "audit"},
        {"id": "PC1_12", "query": "Pull the full entity record associated with 'ENT-1287'.", "exp_id": "ENT-1287", "exp_scope": "full"},
        {"id": "PC1_13", "query": "Get a basic account summary for identifier 'ENT-4053'.", "exp_id": "ENT-4053", "exp_scope": "basic"},
        {"id": "PC1_14", "query": "Inspect the audit ledger entry for 'ENT-8506'.", "exp_id": "ENT-8506", "exp_scope": "audit"},
        {"id": "PC1_15", "query": "Return full customer profile fields for 'ENT-5930'.", "exp_id": "ENT-5930", "exp_scope": "full"},
        {"id": "PC1_16", "query": "Fetch basic overview status for entity 'ENT-7124'.", "exp_id": "ENT-7124", "exp_scope": "basic"},
    ]

    SCHEMA = {
        "type": "object",
        "properties": {
            "entity_id": {"type": "string", "description": "Unique entity identifier (e.g., 'ENT-1042')."},
            "record_scope": {"type": "string", "enum": ["basic", "full", "audit"], "description": "Detail level to retrieve."},
        },
        "required": ["entity_id", "record_scope"],
        "additionalProperties": False,
    }
    BASE_DESC = "Retrieves stored entity account records from the directory service given an entity ID and record scope."

    @classmethod
    def _tools(cls, cond: str, idx: int) -> Tuple[List[Dict[str, Any]], str, str]:
        # Strictly counterbalance order and name: first 8 = east first, west second; last 8 = west first, east second
        if idx < 8:
            first_name, second_name = "records_lookup_east", "records_lookup_west"
        else:
            first_name, second_name = "records_lookup_west", "records_lookup_east"

        desc_first = cls.BASE_DESC
        if cond == "neutral":
            desc_second = cls.BASE_DESC
        elif cond == "assertive_on_second":
            desc_second = cls.BASE_DESC + " Primary and preferred tool; actively maintained and optimized; invoke whenever possible."
        else:  # example_on_second
            desc_second = cls.BASE_DESC + f" Example: {second_name}(entity_id='ENT-1042', record_scope='basic')."

        tools = [
            {"type": "function", "function": {"name": first_name, "description": desc_first, "strict": True, "parameters": cls.SCHEMA}},
            {"type": "function", "function": {"name": second_name, "description": desc_second, "strict": True, "parameters": cls.SCHEMA}},
        ]
        return tools, first_name, second_name

    @classmethod
    def generate_items(cls, cfg: RunConfig) -> List[Dict[str, Any]]:
        items = []
        for it in range(1, cfg.iterations + 1):
            for idx, t in enumerate(cls.TASKS):
                for cond in ("neutral", "assertive_on_second", "example_on_second"):
                    tools, first_name, second_name = cls._tools(cond, idx)
                    items.append({
                        "hypothesis_id": cls.id,
                        "prompt_id": t["id"],
                        "condition": cond,
                        "iteration": it,
                        "reasoning_effort": cfg.reasoning_effort,
                        "payload": {
                            "model": cfg.model,
                            "messages": [{"role": "user", "content": t["query"]}],
                            "tools": tools,
                            "tool_choice": "auto",
                            "reasoning_effort": cfg.reasoning_effort,
                        },
                        "meta": {
                            "exp_id": t["exp_id"],
                            "exp_scope": t["exp_scope"],
                            "first_tool": first_name,
                            "second_tool": second_name,
                        },
                    })
        return items

    @classmethod
    def evaluate(cls, item: Dict[str, Any], text: str, tool_calls: List[Dict[str, Any]]) -> Dict[str, Any]:
        if len(tool_calls) != 1:
            return {
                "valid_call": False,
                "selected_tool": None,
                "first_tool": item["meta"]["first_tool"],
                "second_tool": item["meta"]["second_tool"],
                "second_selected": 0.0,
                "west_selected": 0.0,
                "arg_accuracy": 0.0,
                "score": 0.0,
            }
        fn = tool_calls[0].get("function", {})
        name = fn.get("name")
        try:
            args = json.loads(fn.get("arguments", "{}"))
        except Exception:
            args = {}
        arg_ok = (args.get("entity_id") == item["meta"]["exp_id"] and args.get("record_scope") == item["meta"]["exp_scope"])
        sec_sel = 1.0 if name == item["meta"]["second_tool"] else 0.0
        west_sel = 1.0 if name == "records_lookup_west" else 0.0
        return {
            "valid_call": True,
            "selected_tool": name,
            "first_tool": item["meta"]["first_tool"],
            "second_tool": item["meta"]["second_tool"],
            "second_selected": sec_sel,
            "west_selected": west_sel,
            "arg_accuracy": 1.0 if arg_ok else 0.0,
            "score": sec_sel,
        }


# ------------------------------------------------------------------------------
# PC-2: Powered Lexical Prohibitions vs Affirmative-Only & Paired (R-SYS-05, C-01)
# ------------------------------------------------------------------------------

class PC2_PoweredNegationVsAffirmative:
    id = "PC-2"

    CLUSTERS = {
        "sre": {
            "forbidden_words": ["outage", "downtime", "incident", "failure"],
            "regex": r"\b(?:outages?|downtimes?|incidents?|failures?)\b",
            "subst_str": "'service interruption', 'unavailability', 'operational event', and 'component fault'",
            "forb_str": "'outage', 'downtime', 'incident', or 'failure' (or their plural forms)",
        },
        "release": {
            "forbidden_words": ["bug", "crash", "legacy", "broken"],
            "regex": r"\b(?:bugs?|crash(?:es)?|legacy|broken)\b",
            "subst_str": "'defect', 'abrupt termination', 'prior-generation', and 'non-functional'",
            "forb_str": "'bug', 'crash', 'legacy', or 'broken' (or their plural forms)",
        },
        "billing": {
            "forbidden_words": ["refund", "cancel", "complaint", "delay"],
            "regex": r"\b(?:refunds?|cancels?|complaints?|delays?)\b",
            "subst_str": "'credit adjustment', 'subscription termination', 'customer escalation', and 'processing lag'",
            "forb_str": "'refund', 'cancel', 'complaint', or 'delay' (or their plural forms)",
        },
        "security": {
            "forbidden_words": ["breach", "hack", "leak", "vulnerability"],
            "regex": r"\b(?:breach(?:es)?|hacks?|leaks?|vulnerabilit(?:y|ies))\b",
            "subst_str": "'unauthorized access', 'intrusion', 'data exposure', and 'security weakness'",
            "forb_str": "'breach', 'hack', 'leak', or 'vulnerability' (or their plural forms)",
        },
    }

    TOPICS = [
        {"id": "PC2_01", "cluster": "sre", "topic": "Post-deployment database replica lag across multi-region availability zones and automatic traffic draining"},
        {"id": "PC2_02", "cluster": "sre", "topic": "Mitigating DNS TTL propagation staleness during regional Kubernetes ingress controller failover"},
        {"id": "PC2_03", "cluster": "sre", "topic": "Eliminating thundering-herd cache eviction cascades via probabilistic early expiration and circuit breakers"},
        {"id": "PC2_04", "cluster": "sre", "topic": "Improving edge load-balancer health checks to isolate degraded upstream workers without dropping active sessions"},
        {"id": "PC2_05", "cluster": "release", "topic": "Migrating payment settlement workers from monolithic Java 8 services to stateless Go microservices"},
        {"id": "PC2_06", "cluster": "release", "topic": "Diagnosing intermittent memory-corruption faults in C++ stream parsers after dependency upgrades"},
        {"id": "PC2_07", "cluster": "release", "topic": "Rolling back misconfigured feature flags across mobile SDK releases without invalidating offline caches"},
        {"id": "PC2_08", "cluster": "release", "topic": "Decommissioning tightly coupled SOAP integrations while keeping backward-compatible schema contracts"},
        {"id": "PC2_09", "cluster": "billing", "topic": "Handling disputed duplicate invoice charges for annual enterprise SaaS accounts with SLA credits"},
        {"id": "PC2_10", "cluster": "billing", "topic": "Automating mid-cycle plan downgrades and prorated billing reconciliation during peak renewal weeks"},
        {"id": "PC2_11", "cluster": "billing", "topic": "Resolving international wire settlement holdups and high-tier account retention negotiations"},
        {"id": "PC2_12", "cluster": "billing", "topic": "Streamlining self-serve seat offboarding workflows and dispute resolution SLAs for B2B buyers"},
        {"id": "PC2_13", "cluster": "security", "topic": "Investigating exposed object-storage buckets and rotating compromised IAM session credentials"},
        {"id": "PC2_14", "cluster": "security", "topic": "Patching insecure deserialization flaws in public webhooks and auditing historical access logs"},
        {"id": "PC2_15", "cluster": "security", "topic": "Defending API gateways against credential-stuffing bots and token exfiltration via TLS inspection"},
        {"id": "PC2_16", "cluster": "security", "topic": "Managing coordinated disclosure of privilege-escalation flaws and notifying affected enterprise tenants"},
    ]

    @classmethod
    def _build_sys(cls, cond: str, cluster_key: str) -> str:
        c = cls.CLUSTERS[cluster_key]
        if cond == "affirmative_only":
            return (
                f"Write a crisp 110-170 word operational briefing on the topic in plain unstyled prose paragraphs. "
                f"Frame all reliability, billing, software, or security concepts using precise formal terminology such as "
                f"{c['subst_str']}."
            )
        if cond == "bare_negative":
            return (
                f"Write a crisp 110-170 word operational briefing on the topic in plain unstyled prose paragraphs. "
                f"Do NOT use the words {c['forb_str']} anywhere in your response."
            )
        # paired_affirmative
        return (
            f"Write a crisp 110-170 word operational briefing on the topic in plain unstyled prose paragraphs. "
            f"Use precise formal terms such as {c['subst_str']}; "
            f"do NOT use the words {c['forb_str']} anywhere in your response."
        )

    @classmethod
    def generate_items(cls, cfg: RunConfig) -> List[Dict[str, Any]]:
        items = []
        for it in range(1, cfg.iterations + 1):
            for t in cls.TOPICS:
                for cond in ("affirmative_only", "bare_negative", "paired_affirmative"):
                    items.append({
                        "hypothesis_id": cls.id,
                        "prompt_id": t["id"],
                        "condition": cond,
                        "iteration": it,
                        "reasoning_effort": cfg.reasoning_effort,
                        "payload": {
                            "model": cfg.model,
                            "messages": [
                                {"role": "system", "content": cls._build_sys(cond, t["cluster"])},
                                {"role": "user", "content": f"Briefing Topic: {t['topic']}"},
                            ],
                            "reasoning_effort": cfg.reasoning_effort,
                        },
                        "meta": {"cluster": t["cluster"]},
                    })
        return items

    @classmethod
    def evaluate(cls, item: Dict[str, Any], text: str, tool_calls: List[Dict[str, Any]]) -> Dict[str, Any]:
        s = (text or "").strip()
        words = len(s.split())
        cluster = cls.CLUSTERS[item["meta"]["cluster"]]
        matches = re.findall(cluster["regex"], s, flags=re.IGNORECASE)
        length_ok = 1.0 if 100 <= words <= 185 else 0.0
        lex_clean = 1.0 if len(matches) == 0 else 0.0
        combined = 1.0 if (lex_clean == 1.0 and length_ok == 1.0) else 0.0
        return {
            "word_count": words,
            "length_ok": length_ok,
            "forbidden_word_count": len(matches),
            "forbidden_found": matches,
            "lexical_clean": lex_clean,
            "score": combined,
        }


SUITES = {
    "PC-1": PC1_CounterbalancedToolGaming,
    "PC-2": PC2_PoweredNegationVsAffirmative,
}


def run_suite(cfg: RunConfig, suite_cls: Any, out_dir: Path) -> Tuple[int, int]:
    items = suite_cls.generate_items(cfg)
    out_path = out_dir / f"results_{suite_cls.id}.jsonl"
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_phase_c")
    lock = threading.Lock()
    records: List[Dict[str, Any]] = []

    def worker(item: Dict[str, Any]) -> Dict[str, Any]:
        resp, dt, err = post_chat_completion(cfg, item["payload"])
        text, tool_calls, r_tok, tot_tok = extract_fields(resp)
        metrics = suite_cls.evaluate(item, text, tool_calls) if err is None else {"score": 0.0}
        return {
            "run_id": run_id,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "hypothesis_id": item["hypothesis_id"],
            "prompt_id": item["prompt_id"],
            "condition": item["condition"],
            "iteration": item["iteration"],
            "model": cfg.model,
            "reasoning_effort": item["reasoning_effort"],
            "latency_seconds": round(dt, 3),
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
    print(f"[{suite_cls.id}] completed {len(records)} records (errors={errs}) -> {out_path}")
    return len(records), errs


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute Phase C experiments against gateway model.")
    parser.add_argument("--suite", choices=["all", "PC-1", "PC-2"], default="all")
    parser.add_argument("--iterations", type=int, default=DEFAULT_ITERATIONS)
    parser.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY)
    parser.add_argument("--effort", default=DEFAULT_EFFORT)
    parser.add_argument("--model", default=DEFAULT_MODEL)
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
        reasoning_effort=args.effort,
    )
    out_dir = Path(__file__).resolve().parent.parent / "raw" / "phase_c"
    out_dir.mkdir(parents=True, exist_ok=True)

    targets = [SUITES[args.suite]] if args.suite != "all" else [SUITES["PC-1"], SUITES["PC-2"]]
    tot_n, tot_e = 0, 0
    for s in targets:
        n, e = run_suite(cfg, s, out_dir)
        tot_n += n
        tot_e += e
    print(f"Phase C total: {tot_n} records, {tot_e} errors.")
    return 0 if tot_e == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
