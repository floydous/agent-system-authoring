# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Phase B Empirical Test Harness for agent-system-authoring.

Executes controlled, deconfounded, multi-iteration (N = 5 runs per prompt)
experiments across 6 test suites (PB-1 through PB-6) against an OpenAI-compatible
chat completions endpoint configured solely via environment variables:
  - GATEWAY_URL
  - API_KEY
  - TARGET_MODEL (provenance traces ran on GPT 6 Luna)

Provenance script: writes raw records (excluding auth headers and gateway URLs)
to evidence/raw_phase_b/results_<SUITE>.jsonl.
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


@dataclass
class RunConfig:
    gateway_url: str
    api_key: str
    model: str = DEFAULT_MODEL
    iterations: int = DEFAULT_ITERATIONS
    concurrency: int = DEFAULT_CONCURRENCY
    max_retries: int = 4
    timeout: float = 90.0


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
# PB-1 (SP-4 Deconfounded): Flat Markdown vs Flat XML vs Nested XML
# ------------------------------------------------------------------------------

class PB1_StructuralDelimiters:
    id = "PB-1"
    TOPICS = [
        {"id": "PB1_01", "topic": "Database Connection Pool Exhaustion under Black Friday Traffic"},
        {"id": "PB1_02", "topic": "Distributed Cache Stampede in Redis Cluster during Node Restart"},
        {"id": "PB1_03", "topic": "BGP Route Flapping Causing Cross-Region Packet Loss"},
        {"id": "PB1_04", "topic": "Kafka Consumer Group Rebalance Storm during Rolling Deployment"},
        {"id": "PB1_05", "topic": "Kubernetes API Server ETCD Compaction Latency Spike"},
        {"id": "PB1_06", "topic": "TLS Certificate Expiration on Edge Load Balancer Fleet"},
    ]

    CONSTRAINTS = [
        ("C1", "length", "Total response word count must be strictly between 160 and 190 words inclusive."),
        ("C2", "keywords", "Include all three technical terms: latency, throughput, and failover."),
        ("C3", "forbidden", "Exclude these two buzzwords completely: seamless and game-changer."),
        ("C4", "headers", "Organize the body using these exact three Markdown section headers: ### Overview, ### Root Cause, and ### Mitigation."),
        ("C5", "severity", "Include one severity line formatted as 'SEVERITY: P0', 'SEVERITY: P1', 'SEVERITY: P2', or 'SEVERITY: P3' (choose a single level, without square brackets)."),
        ("C6", "terminal", "End the response with the exact final non-empty line: STATUS: DOCUMENTED"),
    ]

    @classmethod
    def build_prompts(cls, cond: str, topic: str) -> Tuple[str, str]:
        role = "Enterprise technical documentation assistant generating concise incident postmortems."
        out_rule = "Output only the incident report matching every constraint above."

        if cond == "flat_markdown":
            rules_block = "\n".join(f"{i}. {text}" for i, (_, _, text) in enumerate(cls.CONSTRAINTS, 1))
            sys_p = f"### Role\n{role}\n\n### Constraints\n{rules_block}\n\n### Output\n{out_rule}"
            usr_p = f"### Topic\n{topic}"
        elif cond == "flat_xml":
            rules_block = "\n".join(f"{i}. {text}" for i, (_, _, text) in enumerate(cls.CONSTRAINTS, 1))
            sys_p = f"<role>\n{role}\n</role>\n<constraints>\n{rules_block}\n</constraints>\n<output>\n{out_rule}\n</output>"
            usr_p = f"<topic>{topic}</topic>"
        else:  # nested_xml
            c_lines = "\n".join(
                f'    <constraint id="{cid}" category="{cat}">{text}</constraint>'
                for cid, cat, text in cls.CONSTRAINTS
            )
            sys_p = (
                "<system_instructions>\n"
                f"  <role>{role}</role>\n"
                "  <constraints>\n"
                f"{c_lines}\n"
                "  </constraints>\n"
                f"  <output_format>{out_rule}</output_format>\n"
                "</system_instructions>"
            )
            usr_p = f"<request>\n  <topic>{topic}</topic>\n</request>"
        return sys_p, usr_p

    @classmethod
    def generate_items(cls, cfg: RunConfig) -> List[Dict[str, Any]]:
        items = []
        for it in range(1, cfg.iterations + 1):
            for t in cls.TOPICS:
                for cond in ("flat_markdown", "flat_xml", "nested_xml"):
                    sys_p, usr_p = cls.build_prompts(cond, t["topic"])
                    items.append({
                        "hypothesis_id": cls.id,
                        "prompt_id": t["id"],
                        "condition": cond,
                        "iteration": it,
                        "reasoning_effort": "xhigh",
                        "payload": {
                            "model": cfg.model,
                            "messages": [
                                {"role": "system", "content": sys_p},
                                {"role": "user", "content": usr_p},
                            ],
                            "reasoning_effort": "xhigh",
                        },
                        "meta": {},
                    })
        return items

    @classmethod
    def evaluate(cls, item: Dict[str, Any], text: str, tool_calls: List[Dict[str, Any]]) -> Dict[str, Any]:
        s = (text or "").strip()
        words = len(s.split())
        lower = s.lower()
        c1 = 1.0 if 160 <= words <= 190 else 0.0
        c2 = 1.0 if ("latency" in lower and "throughput" in lower and "failover" in lower) else 0.0
        c3 = 1.0 if ("seamless" not in lower and "game-changer" not in lower and "game changer" not in lower) else 0.0
        c4 = 1.0 if ("### overview" in lower and "### root cause" in lower and "### mitigation" in lower) else 0.0
        c5 = 1.0 if re.search(r"(?m)^\s*SEVERITY:\s*P[0-3]\s*$", s) else 0.0
        lines = [ln.strip() for ln in s.splitlines() if ln.strip()]
        c6 = 1.0 if (lines and lines[-1].rstrip(".*_`") == "STATUS: DOCUMENTED") else 0.0
        score = (c1 + c2 + c3 + c4 + c5 + c6) / 6.0
        return {
            "word_count": words,
            "c1_length": c1,
            "c2_keywords": c2,
            "c3_negative": c3,
            "c4_headers": c4,
            "c5_severity": c5,
            "c6_terminal": c6,
            "strict_pass": 1.0 if score == 1.0 else 0.0,
            "score": score,
        }


# ------------------------------------------------------------------------------
# PB-2 (TS-1 Deconfounded): Symmetric Tool Gaming vs Examples
# ------------------------------------------------------------------------------

class PB2_SymmetricToolGaming:
    id = "PB-2"
    TASKS = [
        {"id": "PB2_01", "query": "Look up the profile information for customer ID 'CUST-8831' with full details.", "exp_id": "CUST-8831", "exp_scope": "full"},
        {"id": "PB2_02", "query": "Retrieve the basic account record for customer 'CUST-1049'.", "exp_id": "CUST-1049", "exp_scope": "basic"},
        {"id": "PB2_03", "query": "Fetch the audit trail record for client 'CUST-5520'.", "exp_id": "CUST-5520", "exp_scope": "audit"},
        {"id": "PB2_04", "query": "Pull up the full account profile for 'CUST-9014'.", "exp_id": "CUST-9014", "exp_scope": "full"},
        {"id": "PB2_05", "query": "Get the basic overview profile for customer 'CUST-6190'.", "exp_id": "CUST-6190", "exp_scope": "basic"},
        {"id": "PB2_06", "query": "Check audit-level profile details for client 'CUST-4819'.", "exp_id": "CUST-4819", "exp_scope": "audit"},
    ]
    SCHEMA = {
        "type": "object",
        "properties": {
            "customer_id": {"type": "string", "description": "Unique customer ID (e.g., 'CUST-1042')."},
            "record_scope": {"type": "string", "enum": ["basic", "full", "audit"], "description": "Detail scope to return."},
        },
        "required": ["customer_id", "record_scope"],
        "additionalProperties": False,
    }
    BASE_DESC = "Retrieves customer account and profile records from the database given a customer ID and record scope."

    @classmethod
    def _tools(cls, cond: str) -> List[Dict[str, Any]]:
        desc_alpha = cls.BASE_DESC
        if cond == "neutral_ab":
            desc_beta = cls.BASE_DESC
        elif cond == "assertive_on_beta":
            desc_beta = cls.BASE_DESC + " Primary and preferred tool; actively maintained and optimized; invoke whenever possible."
        else:  # example_on_beta
            desc_beta = cls.BASE_DESC + " Example: records_provider_beta(customer_id='CUST-1042', record_scope='basic')."
        return [
            {"type": "function", "function": {"name": "records_provider_alpha", "description": desc_alpha, "strict": True, "parameters": cls.SCHEMA}},
            {"type": "function", "function": {"name": "records_provider_beta", "description": desc_beta, "strict": True, "parameters": cls.SCHEMA}},
        ]

    @classmethod
    def generate_items(cls, cfg: RunConfig) -> List[Dict[str, Any]]:
        items = []
        for it in range(1, cfg.iterations + 1):
            for t in cls.TASKS:
                for cond in ("neutral_ab", "assertive_on_beta", "example_on_beta"):
                    items.append({
                        "hypothesis_id": cls.id,
                        "prompt_id": t["id"],
                        "condition": cond,
                        "iteration": it,
                        "reasoning_effort": "xhigh",
                        "payload": {
                            "model": cfg.model,
                            "messages": [{"role": "user", "content": t["query"]}],
                            "tools": cls._tools(cond),
                            "tool_choice": "auto",
                            "reasoning_effort": "xhigh",
                        },
                        "meta": {"exp_id": t["exp_id"], "exp_scope": t["exp_scope"]},
                    })
        return items

    @classmethod
    def evaluate(cls, item: Dict[str, Any], text: str, tool_calls: List[Dict[str, Any]]) -> Dict[str, Any]:
        if len(tool_calls) != 1:
            return {"valid_call": False, "selected_tool": None, "beta_selected": 0.0, "arg_accuracy": 0.0, "score": 0.0}
        fn = tool_calls[0].get("function", {})
        name = fn.get("name")
        try:
            args = json.loads(fn.get("arguments", "{}"))
        except Exception:
            args = {}
        arg_ok = (args.get("customer_id") == item["meta"]["exp_id"] and args.get("record_scope") == item["meta"]["exp_scope"])
        beta = 1.0 if name == "records_provider_beta" else 0.0
        return {
            "valid_call": True,
            "selected_tool": name,
            "beta_selected": beta,
            "arg_accuracy": 1.0 if arg_ok else 0.0,
            "score": beta,
        }


# ------------------------------------------------------------------------------
# PB-3 (SP-1 Non-Ceiling): Prospective Memory Under Long Distractor Log
# ------------------------------------------------------------------------------

class PB3_ProspectiveMemoryDistractor:
    id = "PB-3"
    SERVICES = ["auth", "billing", "catalog", "dispatch", "ledger"]

    @classmethod
    def _build_log(cls, seed: int, peak_svc: str) -> Tuple[str, int, str, str]:
        rng = random.Random(seed)
        lines: List[str] = []
        err_counts = {s: 0 for s in cls.SERVICES}
        # ~90 log lines (~1,200 words) mixing INFO, WARN, decoy JSON, and ERROR events
        for idx in range(90):
            ts = f"2026-11-21T12:{idx // 6:02d}:{(idx % 6) * 10:02d}Z"
            svc = cls.SERVICES[rng.randrange(len(cls.SERVICES))]
            r = rng.random()
            if svc == peak_svc and r < 0.42:
                lvl = "ERROR"
            elif svc != peak_svc and r < 0.10:
                lvl = "ERROR"
            elif r < 0.45:
                lvl = "WARN"
            else:
                lvl = "INFO"

            if lvl == "ERROR":
                err_counts[svc] += 1
                code = rng.choice([502, 503, 504, 429])
                lines.append(f"{ts} [ERROR] service={svc} code={code} msg=\"upstream socket timeout during shard sync attempt retry={rng.randint(1,5)} err_ref={rng.randint(100,999)}\"")
            else:
                decoy = rng.choice([
                    f"heartbeat ack latency_ms={rng.randint(8,95)} active_workers={rng.randint(4,32)} ignored_err_budget=0",
                    f"cache refresh complete hit_ratio=0.{rng.randint(85,99)} sample_payload={{\"errors\": {rng.randint(10,99)}, \"ok\": true}}",
                    f"rebalance checkpoint partition={rng.randint(0,15)} queued_jobs={rng.randint(1,40)} status=nominal",
                ])
                lines.append(f"{ts} [{lvl}] service={svc} {decoy}")

        # Guarantee strict unique peak_svc
        max_other = max(v for k, v in err_counts.items() if k != peak_svc)
        while err_counts[peak_svc] <= max_other + 2:
            err_counts[peak_svc] += 1
            lines.insert(rng.randint(10, len(lines) - 5), f"2026-11-21T12:14:55Z [ERROR] service={peak_svc} code=503 msg=\"connection pool saturated during burst\"")

        tot = sum(err_counts.values())
        checksum = f"{peak_svc[:3].upper()}-{tot}"
        return "\n".join(lines), tot, peak_svc, checksum

    @classmethod
    def generate_items(cls, cfg: RunConfig) -> List[Dict[str, Any]]:
        sys_prompt = (
            "You are a log-auditing engine. Given timestamped production log lines, compute:\n"
            "1. total_errors: exact count of lines containing '[ERROR]'. (Ignore '[INFO]' and '[WARN]' decoy numbers.)\n"
            "2. peak_service: the service name with the highest number of '[ERROR]' lines.\n"
            "3. checksum: first 3 characters of peak_service in UPPERCASE, followed by '-' and total_errors.\n\n"
            "Formatting requirements (all mandatory):\n"
            "- Line 1 must be ONLY valid raw JSON matching: {\"total_errors\": <int>, \"peak_service\": <str>, \"checksum\": <str>}\n"
            "- Do NOT use markdown code fences or backticks anywhere.\n"
            "- Line 2 (final line) must be the exact string: END_REPORT_VERIFIED"
        )
        peaks = ["billing", "dispatch", "ledger", "auth", "catalog", "billing"]
        items = []
        for it in range(1, cfg.iterations + 1):
            for idx, peak in enumerate(peaks):
                pid = f"PB3_{idx + 1:02d}"
                log_txt, tot, p_svc, chksum = cls._build_log(1000 + idx, peak)
                for cond in ("system_only", "sandwich_reminder"):
                    tail = (
                        "Analyze the logs above and output the report."
                        if cond == "system_only"
                        else "Analyze the logs above and output the report. Reminder: output raw JSON only with keys total_errors, peak_service, checksum (zero markdown fences), immediately followed on line 2 by END_REPORT_VERIFIED."
                    )
                    usr_p = f"Audit log stream:\n\n{log_txt}\n\n{tail}"
                    items.append({
                        "hypothesis_id": cls.id,
                        "prompt_id": pid,
                        "condition": cond,
                        "iteration": it,
                        "reasoning_effort": "xhigh",
                        "payload": {
                            "model": cfg.model,
                            "messages": [
                                {"role": "system", "content": sys_prompt},
                                {"role": "user", "content": usr_p},
                            ],
                            "reasoning_effort": "xhigh",
                        },
                        "meta": {"total_errors": tot, "peak_service": p_svc, "checksum": chksum},
                    })
        return items

    @classmethod
    def evaluate(cls, item: Dict[str, Any], text: str, tool_calls: List[Dict[str, Any]]) -> Dict[str, Any]:
        s = (text or "").strip()
        no_fence = 1.0 if "```" not in s and "`" not in s else 0.0
        lines = [ln.strip() for ln in s.splitlines() if ln.strip()]
        sentinel_ok = 1.0 if (len(lines) >= 2 and lines[-1] == "END_REPORT_VERIFIED") else 0.0

        json_ok = 0.0
        math_ok = 0.0
        if lines:
            try:
                obj = json.loads(lines[0])
                if isinstance(obj, dict) and set(obj.keys()) == {"total_errors", "peak_service", "checksum"}:
                    json_ok = 1.0
                    if (
                        obj.get("total_errors") == item["meta"]["total_errors"]
                        and str(obj.get("peak_service", "")).lower() == item["meta"]["peak_service"]
                        and obj.get("checksum") == item["meta"]["checksum"]
                    ):
                        math_ok = 1.0
            except Exception:
                pass
        score = (no_fence + sentinel_ok + json_ok + math_ok) / 4.0
        all_pass = 1.0 if score == 1.0 else 0.0
        return {
            "no_fence": no_fence,
            "sentinel_ok": sentinel_ok,
            "json_ok": json_ok,
            "math_ok": math_ok,
            "all_pass": all_pass,
            "score": score,
        }


# ------------------------------------------------------------------------------
# PB-4 (SP-2 Clean): Bare Negative vs Affirmative-Only vs Paired
# ------------------------------------------------------------------------------

class PB4_CleanNegationVsAffirmative:
    id = "PB-4"
    TOPICS = [
        {"id": "PB4_01", "topic": "Why replica lag spikes happen during large batch migrations and how backpressure helps"},
        {"id": "PB4_02", "topic": "How health-check timeouts trigger cascading restarts behind a load balancer"},
        {"id": "PB4_03", "topic": "Why corrupt checkpoint serialization causes crash loops in stateful microservices"},
        {"id": "PB4_04", "topic": "How retry storms amplify partial upstream outages and why jittered backoff stabilizes queues"},
        {"id": "PB4_05", "topic": "Why stale DNS caches route requests to terminated compute nodes during failover"},
        {"id": "PB4_06", "topic": "How schema validation mismatches break downstream stream consumers silently"},
    ]
    FORBIDDEN_RE = re.compile(r"\b(?:server|system|error|data)\b", re.IGNORECASE)

    PROMPTS = {
        "bare_negative": (
            "Write a 100-140 word technical summary of the topic. "
            "Do NOT use the words 'server', 'system', 'error', or 'data'. "
            "Do NOT use markdown bold (**)."
        ),
        "affirmative_only": (
            "Write a 100-140 word technical summary of the topic in plain unstyled prose paragraphs. "
            "Express concepts exclusively with concrete terms such as node, platform, fault, incident, payload, and telemetry."
        ),
        "paired_affirmative": (
            "Write a 100-140 word technical summary of the topic in plain unstyled prose using concrete terms such as "
            "node, platform, fault, incident, payload, and telemetry; "
            "do NOT use the words 'server', 'system', 'error', or 'data', or markdown bold (**)."
        ),
    }

    @classmethod
    def generate_items(cls, cfg: RunConfig) -> List[Dict[str, Any]]:
        items = []
        for it in range(1, cfg.iterations + 1):
            for t in cls.TOPICS:
                for cond in ("bare_negative", "affirmative_only", "paired_affirmative"):
                    items.append({
                        "hypothesis_id": cls.id,
                        "prompt_id": t["id"],
                        "condition": cond,
                        "iteration": it,
                        "reasoning_effort": "xhigh",
                        "payload": {
                            "model": cfg.model,
                            "messages": [
                                {"role": "system", "content": cls.PROMPTS[cond]},
                                {"role": "user", "content": f"Topic: {t['topic']}"},
                            ],
                            "reasoning_effort": "xhigh",
                        },
                        "meta": {},
                    })
        return items

    @classmethod
    def evaluate(cls, item: Dict[str, Any], text: str, tool_calls: List[Dict[str, Any]]) -> Dict[str, Any]:
        s = (text or "").strip()
        words = len(s.split())
        matches = cls.FORBIDDEN_RE.findall(s)
        has_bold = "**" in s
        length_ok = 1.0 if 100 <= words <= 140 else 0.0
        constraint_pass = 1.0 if (len(matches) == 0 and not has_bold) else 0.0
        return {
            "word_count": words,
            "forbidden_word_count": len(matches),
            "forbidden_found": matches,
            "has_bold": 1.0 if has_bold else 0.0,
            "length_ok": length_ok,
            "constraint_pass": constraint_pass,
            "score": constraint_pass,
        }


# ------------------------------------------------------------------------------
# PB-5 (SP-3 Non-Ceiling): Neutral Objective vs Expert Persona (reasoning=low)
# ------------------------------------------------------------------------------

class PB5_ExpertPersonaNonCeiling:
    id = "PB-5"
    PUZZLES = [
        {"id": "PB5_01", "q": "How many subsets of {1, 2, 3, 4, 5, 6, 7, 8, 9, 10} (including the empty subset) have element sum divisible by 5?", "ans": 208},
        {"id": "PB5_02", "q": "How many strings of length 7 over the alphabet {A, B, C} contain NO two consecutive 'A' characters ('AA')?", "ans": 1224},
        {"id": "PB5_03", "q": "Compute the exact remainder when 3^2026 is divided by 100.", "ans": 29},
        {"id": "PB5_04", "q": "How many permutations (derangements) of {1, 2, 3, 4, 5, 6, 7} leave NO element in its original position?", "ans": 1854},
        {"id": "PB5_05", "q": "How many lattice paths go from (0, 0) to (6, 5) taking only +1 Right or +1 Up steps, while strictly avoiding BOTH blocked cells (3, 2) and (4, 3)?", "ans": 172},
        {"id": "PB5_06", "q": "How many integers n with 1 <= n <= 1000 are coprime to 30 (i.e., gcd(n, 30) = 1)?", "ans": 266},
    ]

    SYS = {
        "neutral_objective": "Solve the combinatorial or number-theory problem accurately. End with the exact final line: ANSWER: <integer>",
        "expert_persona": (
            "You are a Fields Medalist, ACM Turing Award winner, and world-leading principal algorithms researcher "
            "with 25 years of experience in competitive mathematics and discrete optimization. "
            "Solve the combinatorial or number-theory problem accurately. End with the exact final line: ANSWER: <integer>"
        ),
    }

    @classmethod
    def generate_items(cls, cfg: RunConfig) -> List[Dict[str, Any]]:
        items = []
        for it in range(1, cfg.iterations + 1):
            for p in cls.PUZZLES:
                for cond in ("neutral_objective", "expert_persona"):
                    items.append({
                        "hypothesis_id": cls.id,
                        "prompt_id": p["id"],
                        "condition": cond,
                        "iteration": it,
                        "reasoning_effort": "low",
                        "payload": {
                            "model": cfg.model,
                            "messages": [
                                {"role": "system", "content": cls.SYS[cond]},
                                {"role": "user", "content": p["q"]},
                            ],
                            "reasoning_effort": "low",
                        },
                        "meta": {"expected": p["ans"]},
                    })
        return items

    @classmethod
    def evaluate(cls, item: Dict[str, Any], text: str, tool_calls: List[Dict[str, Any]]) -> Dict[str, Any]:
        s = (text or "").strip()
        m = re.findall(r"ANSWER:\s*(-?\d+)", s)
        parsed = int(m[-1]) if m else None
        ok = 1.0 if parsed == item["meta"]["expected"] else 0.0
        return {"parsed_answer": parsed, "expected": item["meta"]["expected"], "score": ok}


# ------------------------------------------------------------------------------
# PB-6 (TS-3 Non-Reasoning Simulation): In-Schema rationale Ordering (effort=none)
# ------------------------------------------------------------------------------

class PB6_InSchemaRationaleNoneEffort:
    id = "PB-6"
    PROBLEMS = [
        {
            "id": "PB6_01",
            "prompt": (
                "Schedule compute job JOB-101. Compute cost: 40 minutes at 45 cents/min plus a 200-cent setup fee, "
                "followed by a 10% tier discount on the combined subtotal. Start hour is 14 and advances by 4 hours modulo 24. "
                "Buffer equals duration // 4."
            ),
            "exp_cost": 1800,
            "exp_hour": 18,
            "exp_buf": 10,
        },
        {
            "id": "PB6_02",
            "prompt": "Schedule compute job JOB-102. Compute cost: 60 minutes at 35 cents/min plus 400-cent setup fee, followed by a 20% discount on the combined subtotal. Window starts at hour 21 and advances by 7 hours modulo 24. Buffer is 25% of compute minutes.",
            "exp_cost": 2000,
            "exp_hour": 4,
            "exp_buf": 15,
        },
        {
            "id": "PB6_03",
            "prompt": "Schedule compute job JOB-103. Job runs 80 minutes: first 50 minutes cost 40 cents/min, remaining 30 minutes cost 60 cents/min, plus a 300-cent priority surcharge (no discount). Window starts at hour 19 and advances by 9 hours modulo 24. Buffer is 1/5 of total minutes plus 4.",
            "exp_cost": 4100,
            "exp_hour": 4,
            "exp_buf": 20,
        },
        {
            "id": "PB6_04",
            "prompt": "Schedule compute job JOB-104. Two stages run sequentially: Stage A is 45 minutes at 80 cents/min, Stage B is 35 minutes at 60 cents/min, plus a 500-cent staging fee, then a 10% rebate on the whole total. Window starts at hour 22 and advances by (45 + 35)//10 = 8 hours modulo 24. Buffer equals (total_minutes // 4) - 2.",
            "exp_cost": 5580,
            "exp_hour": 6,
            "exp_buf": 18,
        },
        {
            "id": "PB6_05",
            "prompt": "Schedule compute job JOB-105. 90 minutes at 50 cents/min plus 1,500-cent cluster lock fee, minus a 15% credit on the combined subtotal. Start hour is 17, advancing by 11 hours modulo 24. Buffer is (90 // 3) - 6.",
            "exp_cost": 5100,
            "exp_hour": 4,
            "exp_buf": 24,
        },
        {
            "id": "PB6_06",
            "prompt": "Schedule compute job JOB-106. Three equal shards run in parallel (charged linearly): 3 shards * 25 min * 70 cents/min, plus 750-cent coordinator fee, with a 20% off discount applied to the whole sum. Start hour is 20, advancing by 13 hours modulo 24. Buffer is (25 * 3) // 5 + 3.",
            "exp_cost": 4800,
            "exp_hour": 9,
            "exp_buf": 18,
        },
    ]

    @classmethod
    def _tools(cls, cond: str) -> List[Dict[str, Any]]:
        rat_prop = (
            "rationale",
            {"type": "string", "description": "Concise arithmetic derivation computing total_cost_cents, final_slot_hour, and buffer_minutes."},
        )
        core = [
            ("total_cost_cents", {"type": "integer", "description": "Computed total job cost in integer cents after fees and discounts."}),
            ("final_slot_hour", {"type": "integer", "description": "Computed final 24-hour slot hour (0-23) modulo 24."}),
            ("buffer_minutes", {"type": "integer", "description": "Computed post-job buffer duration in integer minutes."}),
        ]
        if cond == "no_rationale":
            pairs = core
        elif cond == "rationale_first":
            pairs = [rat_prop] + core
        else:
            pairs = core + [rat_prop]
        props = dict(pairs)
        return [{
            "type": "function",
            "function": {
                "name": "schedule_compute_job",
                "description": "Schedules a compute job with computed cost, target 24h slot hour, and post-job buffer duration. Call once after computing all integer values.",
                "strict": True,
                "parameters": {
                    "type": "object",
                    "properties": props,
                    "required": list(props.keys()),
                    "additionalProperties": False,
                },
            },
        }]

    @classmethod
    def generate_items(cls, cfg: RunConfig) -> List[Dict[str, Any]]:
        items = []
        for it in range(1, cfg.iterations + 1):
            for p in cls.PROBLEMS:
                for cond in ("no_rationale", "rationale_first", "rationale_last"):
                    items.append({
                        "hypothesis_id": cls.id,
                        "prompt_id": p["id"],
                        "condition": cond,
                        "iteration": it,
                        "reasoning_effort": "none",
                        "payload": {
                            "model": cfg.model,
                            "messages": [{"role": "user", "content": p["prompt"]}],
                            "tools": cls._tools(cond),
                            "tool_choice": {"type": "function", "function": {"name": "schedule_compute_job"}},
                            "reasoning_effort": "none",
                        },
                        "meta": {"exp_cost": p["exp_cost"], "exp_hour": p["exp_hour"], "exp_buf": p["exp_buf"]},
                    })
        return items

    @classmethod
    def evaluate(cls, item: Dict[str, Any], text: str, tool_calls: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not tool_calls:
            return {"valid_call": False, "score": 0.0}
        try:
            args = json.loads(tool_calls[0].get("function", {}).get("arguments", "{}"))
        except Exception:
            args = {}
        ok = (
            args.get("total_cost_cents") == item["meta"]["exp_cost"]
            and args.get("final_slot_hour") == item["meta"]["exp_hour"]
            and args.get("buffer_minutes") == item["meta"]["exp_buf"]
        )
        return {"valid_call": True, "args": args, "score": 1.0 if ok else 0.0}


SUITES = {
    "PB-1": PB1_StructuralDelimiters,
    "PB-2": PB2_SymmetricToolGaming,
    "PB-3": PB3_ProspectiveMemoryDistractor,
    "PB-4": PB4_CleanNegationVsAffirmative,
    "PB-5": PB5_ExpertPersonaNonCeiling,
    "PB-6": PB6_InSchemaRationaleNoneEffort,
}


def run_suite(cfg: RunConfig, suite_id: str, out_dir: Path, run_id: str) -> Tuple[int, int]:
    cls = SUITES[suite_id]
    items = cls.generate_items(cfg)
    out_file = out_dir / f"results_{suite_id}.jsonl"
    lock = threading.Lock()
    records: List[Dict[str, Any]] = []
    errors = 0

    def worker(item: Dict[str, Any]) -> Dict[str, Any]:
        resp, dt, err = post_chat_completion(cfg, item["payload"])
        text, tcalls, r_tok, tot_tok = extract_fields(resp)
        metrics = cls.evaluate(item, text, tcalls) if err is None else {"score": 0.0}
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
            "request_payload": item["payload"],
            "response_id": resp.get("id") if resp else None,
            "response_text": text,
            "tool_calls": tcalls,
            "metrics": metrics,
        }

    with out_file.open("w", encoding="utf-8") as fh:
        with ThreadPoolExecutor(max_workers=cfg.concurrency) as pool:
            futs = [pool.submit(worker, it) for it in items]
            for fut in as_completed(futs):
                rec = fut.result()
                if rec["error"] is not None:
                    errors += 1
                with lock:
                    records.append(rec)
                    fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    fh.flush()

    print(f"[{suite_id}] wrote {len(records)} records (errors={errors}) to {out_file}")
    return len(records), errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Phase B empirical test suites.")
    parser.add_argument("--suites", nargs="+", default=list(SUITES.keys()), choices=list(SUITES.keys()))
    parser.add_argument("--iterations", type=int, default=DEFAULT_ITERATIONS)
    parser.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    args = parser.parse_args()

    gw = os.environ.get("GATEWAY_URL", "").strip()
    key = os.environ.get("API_KEY", "").strip()
    if not gw or not key:
        print("ERROR: GATEWAY_URL and API_KEY must be provided via environment variables.", file=sys.stderr)
        return 1

    cfg = RunConfig(gateway_url=gw, api_key=key, model=args.model, iterations=args.iterations, concurrency=args.concurrency)
    out_dir = Path(__file__).resolve().parent / "raw_phase_b"
    out_dir.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_phaseB")

    total = 0
    total_err = 0
    for sid in args.suites:
        n, e = run_suite(cfg, sid, out_dir, run_id)
        total += n
        total_err += e
    print(f"Phase B complete: {total} total records, {total_err} errors.")
    return 0 if total_err == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
