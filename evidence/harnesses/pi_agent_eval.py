# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Headless Pi Coding Agent Evaluation Harness for Agent Skills.

Runs multi-turn coding-agent tasks inside isolated temporary workspaces using
`pi -p --mode json` with strict isolation (`-ne`, `-nc`, `--no-mcp`,
`--no-prompt-templates`, `--no-approve`, `--no-session`, `--no-skills`),
comparing a zero-skill baseline against one or more explicit `--skill <path>`
variants.

Every task is graded deterministically on the resulting workspace files (exit
codes, JSON schema contracts, AST checks, and `verify_skill.py --generic`),
alongside full Pi JSONL telemetry (turns, tool calls, skill/reference reads,
tokens, cost, wall time, and system-prompt isolation verification).
"""

from __future__ import annotations

import argparse
import ast
import concurrent.futures
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_SKILL_DIR = REPO_ROOT / "skills" / "agent-system-authoring"
VERIFY_SKILL_SCRIPT = DEFAULT_SKILL_DIR / "scripts" / "verify_skill.py"
SNAKE_CASE_RE = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")


# ---------------------------------------------------------------------------
# Fixture Builders (3 hard multi-file broken repositories)
# ---------------------------------------------------------------------------


def build_fixture_multi_provider_tools(work: Path) -> None:
    """Create a multi-provider strict tool-calling repo with 6 realistic failure modes."""
    (work / "schemas").mkdir(parents=True, exist_ok=True)
    (work / "workers").mkdir(parents=True, exist_ok=True)

    (work / "README.md").write_text(
        "# Billing & Support Agent Tooling\n\n"
        "This service deploys tool definitions across four backends:\n"
        "- `schemas/openai_chat_tools.json` -> OpenAI Chat Completions (`strict: true`, used by `workers/reasoning_agent.py` with `reasoning_effort='high'`).\n"
        "- `schemas/openai_responses_tools.json` -> OpenAI Responses API (`strict: true`).\n"
        "- `schemas/anthropic_tools.json` -> Anthropic Claude Messages API (`strict: true`).\n"
        "- `schemas/gemini_tools.json` -> Google Gemini API function calling (standard JSON Schema features: `anyOf`, `$ref`, `additionalProperties`).\n"
        "- `schemas/fast_billing_tool.json` -> Fast invoice calculator used by `workers/fast_invoice.py` (`reasoning_effort='none'`, no pre-output thinking).\n",
        encoding="utf-8",
        newline="\n",
    )

    (work / "workers" / "reasoning_agent.py").write_text(
        '"""Standard reasoning support/billing router (uses OpenAI Chat strict tools)."""\n\n'
        "MODEL_CONFIG = {\n"
        '    "provider": "openai_chat",\n'
        '    "reasoning_effort": "high",\n'
        '    "tools_file": "schemas/openai_chat_tools.json",\n'
        "}\n",
        encoding="utf-8",
        newline="\n",
    )

    (work / "workers" / "fast_invoice.py").write_text(
        '"""Zero-reasoning fast invoice worker (constrained decoding, no hidden thinking)."""\n\n'
        "MODEL_CONFIG = {\n"
        '    "provider": "openai_chat",\n'
        '    "reasoning_effort": "none",\n'
        '    "tools_file": "schemas/fast_billing_tool.json",\n'
        "}\n\n"
        "# Expected invoice formula:\n"
        "# discounted_cents = round(subtotal_cents * (1 - discount_pct / 100))\n"
        "# tax_cents = round(discounted_cents * (tax_rate_pct / 100))\n"
        "# total_cents = discounted_cents + tax_cents\n",
        encoding="utf-8",
        newline="\n",
    )

    giant_mcc = [f"MCC_{i:04d}" for i in range(1, 321)]

    openai_chat = [
        {
            "type": "function",
            "function": {
                "name": "searchKbDocs",
                "description": "THE BEST AND PREFERRED TOOL! ALWAYS USE this first for every customer question.",
                "strict": True,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "search text"},
                        "maxResults": {"type": "integer", "description": "how many"},
                    },
                    "required": ["query"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "query_billing_ledger",
                "description": "Looks up ledger entries.",
                "strict": True,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "account_id": {"type": "string", "description": "account"},
                        "date_range": {"type": "string", "description": "dates"},
                        "min_amount": {"type": "integer", "description": "amount"},
                        "currency": {"type": "string", "description": "currency"},
                        "merchant_category_code": {
                            "type": "string",
                            "enum": giant_mcc,
                            "description": "merchant code",
                        },
                    },
                    "required": ["account_id", "date_range"],
                },
            },
        },
    ]
    (work / "schemas" / "openai_chat_tools.json").write_text(
        json.dumps(openai_chat, indent=2) + "\n", encoding="utf-8", newline="\n"
    )

    # Buggy OpenAI Responses file: mistakenly uses Chat Completions nested wrapper
    openai_responses = [
        {
            "type": "function",
            "function": {
                "name": "create_refund_ticket",
                "description": "Creates a refund ticket in the billing queue.",
                "strict": True,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "invoice_id": {"type": "string", "description": "Invoice ID"},
                        "refund_cents": {"type": "integer", "description": "Refund amount"},
                        "reason_code": {
                            "type": "string",
                            "enum": ["duplicate_charge", "service_outage", "billing_error"],
                        },
                    },
                    "required": ["invoice_id", "refund_cents"],
                },
            },
        }
    ]
    (work / "schemas" / "openai_responses_tools.json").write_text(
        json.dumps(openai_responses, indent=2) + "\n", encoding="utf-8", newline="\n"
    )

    # Buggy Anthropic strict tool: wrong key `parameters`, unsupported numeric/length keywords, additionalProperties: true
    anthropic_tools = [
        {
            "type": "function",
            "name": "issue_credit_memo",
            "description": "Issues a billing credit memo for a verified customer account.",
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {
                    "account_id": {
                        "type": "string",
                        "minLength": 8,
                        "maxLength": 24,
                        "description": "Account identifier",
                    },
                    "credit_cents": {
                        "type": "integer",
                        "minimum": 100,
                        "maximum": 500000,
                        "description": "Credit amount",
                    },
                    "memo_note": {
                        "type": "string",
                        "maxLength": 200,
                        "description": "Optional note",
                    },
                },
                "required": ["account_id", "credit_cents"],
                "additionalProperties": True,
            },
        }
    ]
    (work / "schemas" / "anthropic_tools.json").write_text(
        json.dumps(anthropic_tools, indent=2) + "\n", encoding="utf-8", newline="\n"
    )

    # Buggy Gemini tool: invalid strict: true and standard JSON Schema keywords inside legacy `parameters`
    gemini_tools = [
        {
            "name": "schedule_account_audit",
            "description": "Schedules an automated ledger audit for an account.",
            "strict": True,
            "parameters": {
                "type": "object",
                "$defs": {
                    "Window": {
                        "type": "object",
                        "properties": {
                            "start_date": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
                            "end_date": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
                        },
                        "required": ["start_date", "end_date"],
                        "additionalProperties": False,
                    }
                },
                "properties": {
                    "account_id": {"type": "string", "pattern": "^ACC-[0-9]{6}$"},
                    "audit_window": {"$ref": "#/$defs/Window"},
                    "notify_email": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                },
                "required": ["account_id", "audit_window"],
                "additionalProperties": False,
            },
        }
    ]
    (work / "schemas" / "gemini_tools.json").write_text(
        json.dumps(gemini_tools, indent=2) + "\n", encoding="utf-8", newline="\n"
    )

    # Buggy zero-reasoning billing tool: numeric outputs first, no leading rationale, vague units
    fast_billing = {
        "type": "function",
        "function": {
            "name": "finalize_invoice_totals",
            "description": "Records computed invoice totals for a customer order.",
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {
                    "total_cents": {"type": "integer", "description": "total"},
                    "tax_cents": {"type": "integer", "description": "tax"},
                    "discounted_cents": {"type": "integer", "description": "after discount"},
                    "subtotal_cents": {"type": "integer", "description": "subtotal"},
                    "discount_pct": {"type": "number", "description": "discount"},
                    "tax_rate_pct": {"type": "number", "description": "tax rate"},
                    "thought": {
                        "type": "string",
                        "description": "Think step by step about the invoice math.",
                    },
                },
                "required": [
                    "total_cents",
                    "tax_cents",
                    "discounted_cents",
                    "subtotal_cents",
                    "discount_pct",
                    "tax_rate_pct",
                ],
            },
        },
    }
    (work / "schemas" / "fast_billing_tool.json").write_text(
        json.dumps(fast_billing, indent=2) + "\n", encoding="utf-8", newline="\n"
    )


def build_fixture_broken_skill_repair(work: Path) -> None:
    """Create a badly structured third-party Agent Skill package with multiple spec/hygiene bugs."""
    skill_dir = work / "Data_Pipeline_Audit"
    (skill_dir / "references" / "deep").mkdir(parents=True, exist_ok=True)
    (skill_dir / "scripts").mkdir(parents=True, exist_ok=True)
    (skill_dir / "__pycache__").mkdir(parents=True, exist_ok=True)
    (skill_dir / "tests").mkdir(parents=True, exist_ok=True)
    (skill_dir / "evidence").mkdir(parents=True, exist_ok=True)

    (work / "shared_notes.md").write_text(
        "# External Shared Notes\n"
        "- Always confirm dead_letter_queue retention >= 14 days.\n",
        encoding="utf-8",
        newline="\n",
    )

    # Build a 540-line bloated SKILL.md with invalid frontmatter, first-person desc, bad links
    filler_rows = "\n".join(
        f"| `CHK-{i:03d}` | Stage {i % 5 + 1} | Verify metric `m_{i:03d}` stays within tolerance bounds before promoting batch. |"
        for i in range(1, 515)
    )
    skill_md = (
        "---\n"
        "name: data-pipeline-audit\n"
        "description: I help you audit ETL jobs and pipelines.\n"
        "author: data-team\n"
        "version: 1.0.0\n"
        "---\n\n"
        "# Data Pipeline Audit\n\n"
        "## Overview\n"
        "Check ETL jobs for idempotency, safe backfill partitioning, schema_drift detection, and dead_letter_queue routing.\n\n"
        "## References\n"
        "- Deep checks: [deep checks](references/deep/checks.md)\n"
        "- Shared notes: [shared](../shared_notes.md)\n"
        "- SQL guide: [sql rules](references\\sql_rules.md)\n\n"
        "## Complete Check Catalog (Bloated Inline Table)\n\n"
        "| Check ID | Stage | Rule |\n"
        "| :--- | :--- | :--- |\n"
        f"{filler_rows}\n"
    )
    (skill_dir / "SKILL.md").write_text(skill_md, encoding="utf-8", newline="\n")

    (skill_dir / "references" / "deep" / "checks.md").write_text(
        "# Deep Pipeline Checks\n\n"
        "- **idempotency**: Re-running any partition write must produce identical row counts.\n"
        "- **backfill**: Historical backfills must scope by explicit partition date bounds.\n"
        "- **schema_drift**: Reject silent column drops or incompatible type casts before load.\n"
        "- **dead_letter_queue**: Malformed records must route to `dead_letter_queue` with error metadata.\n",
        encoding="utf-8",
        newline="\n",
    )
    (skill_dir / "references" / "sql_rules.md").write_text(
        "# SQL Partitioning Rules\n\n"
        "- Never run unbounded `DELETE` or `MERGE` across unpartitioned warehouse tables.\n",
        encoding="utf-8",
        newline="\n",
    )
    (skill_dir / "references" / "orphan_guide.md").write_text(
        "# Retention & SLA Notes\n\n"
        "- Keep dead_letter_queue payloads for at least 14 days for replay diagnostics.\n",
        encoding="utf-8",
        newline="\n",
    )

    # Broken script: no PEP 723, bare open(), hardcoded internal IP + bearer token
    (skill_dir / "scripts" / "check_pipeline.py").write_text(
        '"""Pipeline config checker."""\n'
        "import argparse\n"
        "import json\n\n"
        'INTERNAL_API = "http://10.0.0.42:8080/api/v1/pipelines"\n'
        'AUTH_HEADER = "Bearer tok_secret_1234567890abcdefghij"\n\n'
        "def main():\n"
        "    parser = argparse.ArgumentParser(description='Check pipeline manifest JSON.')\n"
        "    parser.add_argument('manifest', help='Path to pipeline JSON file')\n"
        "    args = parser.parse_args()\n"
        "    data = json.load(open(args.manifest))\n"
        "    required = ['idempotency_key', 'backfill_window', 'dead_letter_queue']\n"
        "    missing = [k for k in required if k not in data]\n"
        "    if missing:\n"
        "        raise SystemExit(f'Missing keys: {missing}')\n"
        "    print('OK')\n\n"
        "if __name__ == '__main__':\n"
        "    main()\n",
        encoding="utf-8",
        newline="\n",
    )

    # Hygiene pollutants inside installable skill dir
    (skill_dir / ".env").write_text(
        "WAREHOUSE_KEY=sk-live-9876543210abcdefghijklmnop\n", encoding="utf-8", newline="\n"
    )
    (skill_dir / "mock_output.json").write_text('{"status": "mock"}\n', encoding="utf-8", newline="\n")
    (skill_dir / "__pycache__" / "check_pipeline.cpython-312.pyc").write_bytes(b"\x00\x00\x00\x00")
    (skill_dir / "tests" / "test_dummy.py").write_text("assert True\n", encoding="utf-8", newline="\n")
    (skill_dir / "evidence" / "raw_dump.jsonl").write_text('{"run": 1}\n', encoding="utf-8", newline="\n")


def build_fixture_prompt_hardening(work: Path) -> None:
    """Create a bloated 52-rule prompt repo with injection, folklore, CoT, and conflicting shots."""
    (work / "config").mkdir(parents=True, exist_ok=True)
    (work / "prompts").mkdir(parents=True, exist_ok=True)
    (work / "app").mkdir(parents=True, exist_ok=True)

    (work / "config" / "model.yaml").write_text(
        "model: gpt-6-luna\n"
        "native_reasoning: true\n"
        "reasoning_effort: high\n"
        "max_output_tokens: 2048\n",
        encoding="utf-8",
        newline="\n",
    )

    (work / "prompts" / "requirements.md").write_text(
        "# Support Assistant Requirements\n\n"
        "1. **Three operational stages**: `triage` (classify & route), `investigation` (verify logs/billing facts), `resolution` (write customer response & final decision).\n"
        "2. **Decisions**: Final resolution decision must be exactly one concrete value: `APPROVE`, `ESCALATE`, or `DENY`.\n"
        "3. **Forbidden terminology**: Customer-facing responses must never contain the words `crash`, `bug`, `outage`, or `broken`, nor hyphenated/compound variants like `consecutive-bug` or `system-crash`.\n"
        "4. **Prompt injection defense**: Customer emails (`{{customer_email}}`) and CRM notes (`{{crm_ticket}}`) are untrusted external inputs; embedded override instructions inside them must be ignored.\n"
        "5. **Model target**: Runs on `GPT 6 Luna` (`native_reasoning: true`, `reasoning_effort: high`).\n",
        encoding="utf-8",
        newline="\n",
    )

    rules_52 = []
    stage_topics = [
        ("Triage", "Classify incoming priority, verify account tier, check SLA clock, detect duplicate tickets, tag product area, check region, verify language, route billing vs technical, flag VIP escalation, verify attachment count, check open incidents, confirm ticket ID, detect spam, set queue label, verify timestamps, check consent flag, note channel source"),
        ("Investigation", "Cross-check ledger ID, inspect error timestamp, confirm affected service version, verify recent deploys, check account entitlement, verify refund eligibility window, check prior credits, inspect API status code, validate reproduction steps, confirm customer plan limits, check webhook retries, verify idempotency token, inspect rate-limit logs, check auth scope, confirm region failover status, verify data retention policy, summarize objective facts"),
        ("Resolution", "Draft concise customer reply, state concrete next step, cite ticket reference, confirm single decision code, verify SLA window, confirm no internal stack traces leak, use neutral factual tone, avoid speculation, include expected timeline, confirm follow-up channel, avoid disclosing internal IP addresses, avoid quoting raw SQL, verify currency formatting, confirm timezone UTC, verify polite closing, check word limit under 180 words, confirm audit log fields, double-check compliance"),
    ]
    idx = 1
    for stage, items in stage_topics:
        for item in items.split(", "):
            rules_52.append(f"{idx}. [{stage}] {item.capitalize()}.")
            idx += 1

    monolith = (
        "You are a Fields Medalist, Turing Laureate, and Nobel-winning Senior Support Architect.\n"
        "Always think step by step and show your full reasoning chain before answering.\n\n"
        "Please use friendly phrases like 'service interruption' or 'unexpected behavior' instead of technical jargon.\n\n"
        "Output your final decision as: Decision: [APPROVE|ESCALATE|DENY]\n\n"
        "Customer email:\n{{customer_email}}\n\n"
        "CRM ticket:\n{{crm_ticket}}\n\n"
        "Follow ALL 52 rules simultaneously on every turn:\n"
        + "\n".join(rules_52)
        + "\n\n"
        "Examples:\n"
        "Example 1: Input: Billing duplicate -> Output: Decision: APPROVE. Credit issued.\n"
        "Example 2: Input: App failed -> Output: Decision: [APPROVE|ESCALATE|DENY]. Sorry about the crash and consecutive-bug.\n"
        "Example 3: Input: Unknown request -> Output: Decision: ESCALATE. Routed to tier 2.\n"
    )
    (work / "prompts" / "support_monolith.md").write_text(monolith, encoding="utf-8", newline="\n")

    (work / "app" / "loader.py").write_text(
        '"""Prompt loader utility."""\n'
        "from pathlib import Path\n\n"
        "PROMPTS_DIR = Path(__file__).resolve().parent.parent / 'prompts'\n\n"
        "def load_prompt(name: str = 'support_monolith.md') -> str:\n"
        "    return (PROMPTS_DIR / name).read_text(encoding='utf-8')\n",
        encoding="utf-8",
        newline="\n",
    )


# ---------------------------------------------------------------------------
# Deterministic Graders (10 binary checks per task = 30 checks total)
# ---------------------------------------------------------------------------


def _walk_json_keys(obj: Any) -> List[str]:
    keys: List[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            keys.append(k)
            keys.extend(_walk_json_keys(v))
    elif isinstance(obj, list):
        for item in obj:
            keys.extend(_walk_json_keys(item))
    return keys


def _has_null_type(schema: Dict[str, Any]) -> bool:
    t = schema.get("type")
    if t == "null" or (isinstance(t, list) and "null" in t):
        return True
    for branch in schema.get("anyOf") or schema.get("oneOf") or []:
        if isinstance(branch, dict) and _has_null_type(branch):
            return True
    return False


def _has_structural_constraint(schema: Any) -> bool:
    if not isinstance(schema, dict):
        return False
    c_keys = {"pattern", "format", "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum", "minItems", "maxItems", "multipleOf"}
    if any(k in schema for k in c_keys):
        return True
    for branch in schema.get("anyOf") or schema.get("oneOf") or []:
        if _has_structural_constraint(branch):
            return True
    return False


def _load_json_safe(path: Path) -> Optional[Any]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _as_tool_list(data: Any) -> List[Dict[str, Any]]:
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict):
        if "tools" in data and isinstance(data["tools"], list):
            return [x for x in data["tools"] if isinstance(x, dict)]
        return [data]
    return []


def grade_multi_provider_tools(work: Path) -> Dict[str, Tuple[bool, str]]:
    checks: Dict[str, Tuple[bool, str]] = {}

    chat_tools = _as_tool_list(_load_json_safe(work / "schemas" / "openai_chat_tools.json"))
    resp_tools = _as_tool_list(_load_json_safe(work / "schemas" / "openai_responses_tools.json"))
    anth_tools = _as_tool_list(_load_json_safe(work / "schemas" / "anthropic_tools.json"))
    gem_tools = _as_tool_list(_load_json_safe(work / "schemas" / "gemini_tools.json"))
    fast_tools = _as_tool_list(_load_json_safe(work / "schemas" / "fast_billing_tool.json"))

    # 1. OpenAI Chat strict wire shape + all required + additionalProperties: false + no rationale on reasoning tools
    ok_chat = bool(chat_tools) and len(chat_tools) >= 2
    chat_msgs: List[str] = []
    for t in chat_tools:
        fn = t.get("function") if t.get("type") == "function" else None
        if not isinstance(fn, dict):
            ok_chat = False
            chat_msgs.append("missing type=function wrapper")
            continue
        if fn.get("strict") is not True:
            ok_chat = False
            chat_msgs.append(f"{fn.get('name')}: strict!=true")
        params = fn.get("parameters") or {}
        if params.get("additionalProperties") is not False:
            ok_chat = False
            chat_msgs.append(f"{fn.get('name')}: additionalProperties!=false")
        props = params.get("properties") or {}
        reqs = set(params.get("required") or [])
        if set(props.keys()) != reqs:
            ok_chat = False
            chat_msgs.append(f"{fn.get('name')}: not all props required")
        if any(k.lower() in {"rationale", "thought", "reasoning"} for k in props):
            ok_chat = False
            chat_msgs.append(f"{fn.get('name')}: unexpected rationale on reasoning tool")
    # Also check optional fields like currency / max_results use nullable typing
    billing_fn = next((t.get("function") for t in chat_tools if isinstance(t.get("function"), dict) and "billing" in str(t["function"].get("name", "")).lower()), None)
    if billing_fn:
        bprops = (billing_fn.get("parameters") or {}).get("properties") or {}
        if "currency" in bprops and not _has_null_type(bprops["currency"]):
            # Allow either nullable currency or explicit default/enum; require at least one optional field nullable across chat tools
            any_nullable = any(
                _has_null_type(ps)
                for t in chat_tools
                for ps in (((t.get("function") or {}).get("parameters") or {}).get("properties") or {}).values()
                if isinstance(ps, dict)
            )
            if not any_nullable:
                ok_chat = False
                chat_msgs.append("optional fields not nullable in strict mode")
    checks["openai_chat_wire"] = (ok_chat, "; ".join(chat_msgs) or "ok")

    # 2. Neutrality + mutual negative boundaries in openai_chat_tools
    hype_re = re.compile(r"\b(best|preferred|always use|first choice|superior)\b", re.IGNORECASE)
    neg_re = re.compile(r"\b(do not use|don't use|not for|never use|instead use|use `?[a-z0-9_]+`? for|avoid using)\b", re.IGNORECASE)
    descs = [str((t.get("function") or {}).get("description", "")) for t in chat_tools]
    has_hype = any(hype_re.search(d) for d in descs)
    has_neg = sum(1 for d in descs if neg_re.search(d)) >= 2
    checks["openai_chat_neutral_boundaries"] = (
        bool(descs) and not has_hype and has_neg,
        f"hype={has_hype}, neg_boundaries={sum(1 for d in descs if neg_re.search(d))}/{len(descs)}",
    )

    # 3. Parameter descriptions specify concrete formats/units + structural JSON Schema constraints
    all_chat_props = [
        (k, v)
        for t in chat_tools
        for k, v in (((t.get("function") or {}).get("parameters") or {}).get("properties") or {}).items()
        if isinstance(v, dict)
    ]
    all_prop_text = " ".join(str(v.get("description", "")) for _, v in all_chat_props).lower()
    has_units_or_fmt = ("cent" in all_prop_text or "usd" in all_prop_text or "iso" in all_prop_text) and (
        "yyyy-mm-dd" in all_prop_text or "iso" in all_prop_text or "[start" in all_prop_text or "date" in all_prop_text
    )
    has_struct = any(_has_structural_constraint(v) for _, v in all_chat_props)
    checks["openai_chat_param_clarity"] = (
        has_units_or_fmt and has_struct,
        f"units_fmt={has_units_or_fmt}, structural_constraints={has_struct}",
    )

    # 4. Giant 320-value enum pruned + companion lookup/search tool provided
    max_enum_len = 0
    for t in chat_tools:
        for v in (((t.get("function") or {}).get("parameters") or {}).get("properties") or {}).values():
            if isinstance(v, dict) and isinstance(v.get("enum"), list):
                max_enum_len = max(max_enum_len, len(v["enum"]))
            if isinstance(v, dict):
                for br in v.get("anyOf") or []:
                    if isinstance(br, dict) and isinstance(br.get("enum"), list):
                        max_enum_len = max(max_enum_len, len(br["enum"]))
    has_lookup_tool = len(chat_tools) >= 3 and any(
        any(w in str((t.get("function") or {}).get("name", "")).lower() for w in ("merchant", "mcc", "category", "lookup", "search"))
        and "kb" not in str((t.get("function") or {}).get("name", "")).lower()
        for t in chat_tools
    )
    checks["openai_chat_enum_pruned"] = (
        bool(chat_tools) and max_enum_len <= 50 and has_lookup_tool,
        f"max_enum={max_enum_len}, lookup_tool={has_lookup_tool}",
    )

    # 5. OpenAI Responses API flat wire shape
    ok_resp = bool(resp_tools)
    resp_msgs: List[str] = []
    for t in resp_tools:
        if "function" in t:
            ok_resp = False
            resp_msgs.append("nested 'function' wrapper not allowed in Responses API")
        if t.get("type") != "function" or not t.get("name") or t.get("strict") is not True:
            ok_resp = False
            resp_msgs.append("must have flat type=function, name, strict=true")
        params = t.get("parameters") or {}
        if params.get("additionalProperties") is not False:
            ok_resp = False
            resp_msgs.append("additionalProperties!=false")
        props = params.get("properties") or {}
        if not props or set(props.keys()) != set(params.get("required") or []):
            ok_resp = False
            resp_msgs.append("all props must be required")
    checks["openai_responses_wire"] = (ok_resp, "; ".join(resp_msgs) or "ok")

    # 6. Anthropic strict wire shape (input_schema, NO parameters/type wrapper, additionalProperties: false, ZERO HTTP-400 keywords)
    forbidden_anth = {"minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum", "minLength", "maxLength"}
    ok_anth = bool(anth_tools)
    anth_msgs: List[str] = []
    for t in anth_tools:
        if "parameters" in t or "function" in t or "type" in t:
            ok_anth = False
            anth_msgs.append("Anthropic tool must not use parameters/function/type wrapper")
        if t.get("strict") is not True or not isinstance(t.get("input_schema"), dict):
            ok_anth = False
            anth_msgs.append("missing strict=true or input_schema")
            continue
        isch = t["input_schema"]
        if isch.get("additionalProperties") is not False:
            ok_anth = False
            anth_msgs.append("input_schema.additionalProperties!=false")
        bad_keys = sorted(forbidden_anth.intersection(_walk_json_keys(isch)))
        if bad_keys:
            ok_anth = False
            anth_msgs.append(f"HTTP-400 keywords present: {bad_keys}")
    checks["anthropic_strict_wire"] = (ok_anth, "; ".join(anth_msgs) or "ok")

    # 7. Gemini wire shape (parametersJsonSchema, NO strict: true)
    ok_gem = bool(gem_tools)
    gem_msgs: List[str] = []
    for t in gem_tools:
        if "strict" in t:
            ok_gem = False
            gem_msgs.append("Gemini must not set 'strict'")
        if "parametersJsonSchema" not in t or not isinstance(t.get("parametersJsonSchema"), dict):
            ok_gem = False
            gem_msgs.append("must use parametersJsonSchema for $ref/anyOf/additionalProperties")
        if "parameters" in t:
            ok_gem = False
            gem_msgs.append("remove legacy parameters key")
    checks["gemini_wire"] = (ok_gem, "; ".join(gem_msgs) or "ok")

    # 8. Fast zero-reasoning billing tool: rationale FIRST, no "step by step", formula/units in siblings, strict valid
    ok_fast = len(fast_tools) >= 1
    fast_msgs: List[str] = []
    if fast_tools:
        ft = fast_tools[0]
        fn = ft.get("function") if ft.get("type") == "function" and isinstance(ft.get("function"), dict) else ft
        params = fn.get("parameters") or {}
        props = params.get("properties") or {}
        prop_keys = list(props.keys())
        if not prop_keys or prop_keys[0].lower() != "rationale":
            ok_fast = False
            fast_msgs.append(f"first key is {prop_keys[0] if prop_keys else None}, expected 'rationale'")
        else:
            rdesc = str(props[prop_keys[0]].get("description", "")).lower()
            # Reject positive CoT prompts like "think step by step", while allowing explicit negative bans ("do not provide step-by-step")
            bad_cot = bool(re.search(r"(?<!do not )(?<!never )(?<!not provide )(?<!no )\bstep[- ]by[- ]step\b", rdesc)) and not bool(
                re.search(r"\b(do not|never|avoid|no)\b[^.;\n]{0,25}\bstep[- ]by[- ]step\b", rdesc)
            )
            if bad_cot:
                ok_fast = False
                fast_msgs.append("rationale description encourages 'step by step'")
        if any(k.lower() == "thought" for k in prop_keys):
            ok_fast = False
            fast_msgs.append("stale 'thought' key still present")
        if params.get("additionalProperties") is not False or set(prop_keys) != set(params.get("required") or []):
            ok_fast = False
            fast_msgs.append("strict additionalProperties/required violated")
        sib_text = " ".join(str(v.get("description", "")) for k, v in props.items() if k.lower() != "rationale").lower()
        if "cent" not in sib_text or ("round" not in sib_text and "discount" not in sib_text):
            ok_fast = False
            fast_msgs.append("sibling fields missing units/formula")
    checks["fast_billing_rationale_first"] = (ok_fast, "; ".join(fast_msgs) or "ok")

    # 9. All tool names & parameter keys snake_case
    bad_ids: List[str] = []
    for tlist in (chat_tools, resp_tools, anth_tools, gem_tools, fast_tools):
        for t in tlist:
            fn = t.get("function") if isinstance(t.get("function"), dict) else t
            name = fn.get("name")
            if isinstance(name, str) and not SNAKE_CASE_RE.match(name):
                bad_ids.append(f"tool:{name}")
            schema_obj = fn.get("parameters") or fn.get("input_schema") or fn.get("parametersJsonSchema") or {}
            if isinstance(schema_obj, dict):
                for pk in (schema_obj.get("properties") or {}).keys():
                    if not SNAKE_CASE_RE.match(pk):
                        bad_ids.append(f"param:{pk}")
    checks["snake_case_ids"] = (not bad_ids, f"non_snake={bad_ids}" if bad_ids else "ok")

    # 10. Anti-cheat: workers untouched and schemas valid JSON
    w1 = (work / "workers" / "fast_invoice.py").read_text(encoding="utf-8") if (work / "workers" / "fast_invoice.py").exists() else ""
    w2 = (work / "workers" / "reasoning_agent.py").read_text(encoding="utf-8") if (work / "workers" / "reasoning_agent.py").exists() else ""
    ok_workers = ('"reasoning_effort": "none"' in w1) and ('"reasoning_effort": "high"' in w2)
    checks["workers_preserved"] = (ok_workers, "ok" if ok_workers else "worker configs altered or removed")

    return checks


def grade_broken_skill_repair(work: Path) -> Dict[str, Tuple[bool, str]]:
    checks: Dict[str, Tuple[bool, str]] = {}
    target = work / "data-pipeline-audit"
    legacy = work / "Data_Pipeline_Audit"

    # 1. Renamed to kebab-case matching SKILL.md name
    checks["dir_name_kebab"] = (
        target.is_dir() and not legacy.exists(),
        f"target_exists={target.is_dir()}, legacy_exists={legacy.exists()}",
    )

    # Locate active skill dir for remaining checks
    sdir = target if target.is_dir() else legacy
    skill_md = sdir / "SKILL.md"
    skill_txt = skill_md.read_text(encoding="utf-8") if skill_md.exists() else ""

    # 2. External verify_skill.py --generic exit code 0
    if sdir.is_dir():
        proc = subprocess.run(
            [sys.executable, "-B", str(VERIFY_SKILL_SCRIPT), "--generic", str(sdir)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
        raw_detail = (proc.stdout + proc.stderr).strip()
        clean_detail = raw_detail.replace(str(work), "<work>").replace(str(work).replace("\\", "/"), "<work>")[-240:]
        checks["verify_skill_generic_exit0"] = (
            proc.returncode == 0,
            "ok" if proc.returncode == 0 else clean_detail,
        )
    else:
        checks["verify_skill_generic_exit0"] = (False, "skill dir missing")

    # 3. Line & token budget
    lines = skill_txt.splitlines()
    est_tokens = len(skill_txt) / 4.0
    checks["line_and_token_budget"] = (
        bool(skill_txt) and len(lines) < 500 and est_tokens < 5000,
        f"lines={len(lines)}, est_tokens={int(est_tokens)}",
    )

    # 4. Frontmatter: third-person description with what+when, no top-level author/version
    fm_match = re.match(r"^---\n(.*?)\n---", skill_txt, re.DOTALL)
    fm_text = fm_match.group(1) if fm_match else ""
    desc_m = re.search(r"^description:\s*(.+)$", fm_text, re.MULTILINE)
    desc_val = desc_m.group(1).strip().strip("\"'") if desc_m else ""
    bad_top_keys = bool(re.search(r"^(?:author|version):", fm_text, re.MULTILINE))
    first_person = bool(re.search(r"^(?:I|We|My)\b", desc_val))
    has_when = bool(re.search(r"\b(use when|when |for auditing|whenever)\b", desc_val, re.IGNORECASE))
    checks["frontmatter_valid_third_person"] = (
        bool(fm_match) and not bad_top_keys and not first_person and has_when and len(desc_val) >= 40,
        f"bad_top={bad_top_keys}, first_person={first_person}, has_when={has_when}, len={len(desc_val)}",
    )

    # 5. Single-hop links under references/, no nested dirs, no ../, no backslashes
    refs_dir = sdir / "references"
    nested_refs = [p for p in refs_dir.rglob("*.md") if p.parent != refs_dir] if refs_dir.exists() else []
    bad_links = ("../" in skill_txt) or ("references\\" in skill_txt)
    checks["single_hop_links"] = (
        refs_dir.is_dir() and not nested_refs and not bad_links and len(list(refs_dir.glob("*.md"))) >= 1,
        f"nested={len(nested_refs)}, bad_links={bad_links}",
    )

    # 6. Zero orphaned reference files (every references/*.md linked in SKILL.md)
    ref_files = sorted(p.name for p in refs_dir.glob("*.md")) if refs_dir.is_dir() else []
    orphans = [name for name in ref_files if f"references/{name}" not in skill_txt]
    checks["no_orphaned_references"] = (bool(ref_files) and not orphans, f"orphans={orphans}")

    # 7. Hygiene clean: no .env, mock_*, __pycache__, tests/, evidence/
    pollutants = []
    if sdir.is_dir():
        for p in sdir.rglob("*"):
            rel = p.relative_to(sdir)
            if p.name.startswith(".env") and p.name != ".env.example":
                pollutants.append(str(rel))
            elif p.name.startswith("mock_"):
                pollutants.append(str(rel))
            elif any(part in ("__pycache__", ".pytest_cache", "tests", "evidence") for part in rel.parts):
                pollutants.append(str(rel))
    checks["hygiene_clean"] = (not pollutants, f"pollutants={pollutants[:5]}")

    # 8. Zero leaked secrets / private IPs anywhere inside skill dir
    secret_re = re.compile(r"(?:sk-[A-Za-z0-9_-]{16,}|Bearer\s+[A-Za-z0-9._-]{16,}|10\.0\.0\.42)")
    secret_hits = []
    if sdir.is_dir():
        for p in sdir.rglob("*"):
            if p.is_file():
                txt = p.read_text(encoding="utf-8", errors="ignore")
                if secret_re.search(txt):
                    secret_hits.append(p.name)
    checks["zero_secrets"] = (not secret_hits, f"secret_hits={secret_hits}")

    # 9. PEP 723 + pathlib + UTF-8 + runnable --help on scripts/check_pipeline.py
    script = sdir / "scripts" / "check_pipeline.py"
    ok_script = False
    sc_msg = "script missing"
    if script.exists():
        stxt = script.read_text(encoding="utf-8")
        has_pep = bool(re.search(r"^# /// script\s*$.*requires-python.*dependencies.*^# ///\s*$", stxt, re.MULTILINE | re.DOTALL))
        has_pathlib = "Path" in stxt and "pathlib" in stxt
        has_utf8 = "utf-8" in stxt.lower()
        try:
            ast.parse(stxt)
            ast_ok = True
        except SyntaxError as e:
            ast_ok = False
            sc_msg = f"syntax: {e}"
        if ast_ok:
            hr = subprocess.run([sys.executable, "-B", str(script), "--help"], capture_output=True, text=True, timeout=15)
            help_ok = hr.returncode == 0
            ok_script = has_pep and has_pathlib and has_utf8 and help_ok
            sc_msg = f"pep723={has_pep}, pathlib={has_pathlib}, utf8={has_utf8}, help_rc={hr.returncode}"
    checks["pep723_portable_script"] = (ok_script, sc_msg)

    # 10. Anti-cheat: core domain concepts preserved across SKILL.md + references/
    all_md = skill_txt + "\n" + "\n".join(
        p.read_text(encoding="utf-8", errors="ignore") for p in (refs_dir.glob("*.md") if refs_dir.is_dir() else [])
    )
    required_patterns = {
        "idempotency": r"\bidempotenc",
        "backfill": r"\bbackfill",
        "schema_drift": r"\bschema[-_ ]drift\b",
        "dead_letter_queue": r"\bdead[-_ ]letter[-_ ]queue\b",
    }
    missing_terms = [k for k, pat in required_patterns.items() if not re.search(pat, all_md, re.IGNORECASE)]
    checks["domain_content_preserved"] = (not missing_terms, f"missing={missing_terms}")

    return checks


def grade_prompt_hardening(work: Path) -> Dict[str, Tuple[bool, str]]:
    checks: Dict[str, Tuple[bool, str]] = {}
    prompts_dir = work / "prompts"
    md_files = sorted(
        p for p in prompts_dir.rglob("*.md")
        if p.name.lower() != "requirements.md"
    ) if prompts_dir.exists() else []

    texts = {str(p.relative_to(work)): p.read_text(encoding="utf-8", errors="ignore") for p in md_files}
    combined = "\n\n".join(texts.values())

    # Determine active phase files (exclude original monolith if it was kept as archive/deprecated, or check all non-monolith files)
    phase_files = [
        (name, txt) for name, txt in texts.items()
        if any(s in name.lower() for s in ("triage", "investigat", "resolut", "phase", "stage"))
    ]

    # 1. Phase segmented into distinct files (triage, investigation, resolution) each <= 20 numbered/bullet rules
    has_3_stages = (
        len(phase_files) >= 3
        and any("triage" in n.lower() for n, _ in phase_files)
        and any("investigat" in n.lower() for n, _ in phase_files)
        and any("resolut" in n.lower() for n, _ in phase_files)
    )
    max_rules_in_phase = 0
    for _, txt in phase_files:
        rc = len(re.findall(r"^\s*(?:\d+\.|[-*])\s+", txt, re.MULTILINE))
        max_rules_in_phase = max(max_rules_in_phase, rc)
    checks["phase_segmented"] = (
        has_3_stages and 0 < max_rules_in_phase <= 22,
        f"phase_files={len(phase_files)}, max_rules={max_rules_in_phase}",
    )

    # Active prompt corpus: include all prompt files except an untouched legacy 52-rule monolith
    active_texts = [
        txt
        for name, txt in texts.items()
        if not ("monolith" in name.lower() and "Follow ALL 52 rules" in txt)
    ] or list(texts.values())
    active_combined = "\n\n".join(active_texts)

    # 2. Honorary expert personas removed
    persona_re = re.compile(r"\b(fields medalist|turing laureate|nobel)\b", re.IGNORECASE)
    checks["persona_fluff_removed"] = (
        bool(active_combined) and not persona_re.search(active_combined),
        "persona fluff still present" if persona_re.search(active_combined) else "ok",
    )

    # 3. Explicit CoT directive removed for native reasoning model
    cot_re = re.compile(r"\b(think step by step|step-by-step reasoning|show your full reasoning chain)\b", re.IGNORECASE)
    checks["cot_removed"] = (
        bool(active_combined) and not cot_re.search(active_combined),
        "CoT directive still present" if cot_re.search(active_combined) else "ok",
    )

    # 4. Literal [APPROVE|ESCALATE|DENY] bracket placeholder removed
    has_pipe_brackets = "[APPROVE|ESCALATE|DENY]" in active_combined
    checks["no_pipe_brackets"] = (
        bool(active_combined) and not has_pipe_brackets,
        "literal [APPROVE|ESCALATE|DENY] present" if has_pipe_brackets else "ok",
    )

    # 5. Explicit negative prohibitions naming all 4 banned words + compounds/hyphenated forms
    has_neg_ban = bool(re.search(r"\b(do not|never|must not|prohibited|forbidden)\b", active_combined, re.IGNORECASE))
    banned_words = ["crash", "bug", "outage", "broken"]
    missing_banned = [w for w in banned_words if w not in active_combined.lower()]
    mentions_compounds = bool(re.search(r"\b(hyphen|compound|consecutive-bug|inflect|variant|derivative)\b", active_combined, re.IGNORECASE))
    checks["explicit_word_bans_and_compounds"] = (
        has_neg_ban and not missing_banned and mentions_compounds,
        f"neg={has_neg_ban}, missing={missing_banned}, compounds={mentions_compounds}",
    )

    # 6. Untrusted data isolation: hierarchy + data delimiters + zero authority to embedded imperatives
    has_hier = bool(
        re.search(
            r"(?:platform|system|developer)[^\n]{0,120}(?:>|over|precedence|priority|higher)[^\n]{0,120}(?:user|untrusted|data|email|ticket)",
            active_combined,
            re.IGNORECASE,
        )
        or re.search(
            r"(?:priority|precedence|hierarchy|authority\s+order).{0,300}(?:platform|system|developer).{0,250}(?:user|untrusted|customer_email|crm_ticket)",
            active_combined,
            re.IGNORECASE | re.DOTALL,
        )
    )
    has_delim = bool(re.search(r"(<(?:untrusted|customer_email|crm_ticket|external)[^>]*>|```|---|\[\[|###\s*Untrusted)", active_combined, re.IGNORECASE))
    has_zero_auth = bool(re.search(r"(ignore|zero authority|no authority|never follow|passive data|untrusted data|not instructions)", active_combined, re.IGNORECASE))
    has_placeholders = "{{customer_email}}" in active_combined and "{{crm_ticket}}" in active_combined
    checks["untrusted_data_isolation"] = (
        has_hier and has_delim and has_zero_auth and has_placeholders,
        f"hier={has_hier}, delim={has_delim}, zero_auth={has_zero_auth}, placeholders={has_placeholders}",
    )

    # 7. Conflicting few-shot Example 2 removed or fixed
    bad_example = "Sorry about the crash" in active_combined or "Example 2: Input: App failed" in active_combined
    checks["conflicting_fewshot_resolved"] = (
        bool(active_combined) and not bad_example,
        "conflicting Example 2 still present" if bad_example else "ok",
    )

    # 8. Clean structural delimiters (Markdown ### or XML tags)
    has_headers = bool(re.search(r"^#{2,3}\s+\S+", active_combined, re.MULTILINE)) or bool(re.search(r"<[a-z_]+>", active_combined))
    checks["clean_delimiters"] = (has_headers, "ok" if has_headers else "no clean headers/tags")

    # 9. Business requirements preserved (all 3 stages + APPROVE/ESCALATE/DENY)
    needed = ["triage", "investigation", "resolution", "approve", "escalate", "deny"]
    missing_req = [k for k in needed if k not in active_combined.lower()]
    checks["business_reqs_preserved"] = (not missing_req, f"missing={missing_req}")

    # 10. app/loader.py still valid Python
    loader = work / "app" / "loader.py"
    ok_loader = False
    lmsg = "loader missing"
    if loader.exists():
        try:
            ast.parse(loader.read_text(encoding="utf-8"))
            ok_loader = True
            lmsg = "ok"
        except SyntaxError as e:
            lmsg = f"syntax: {e}"
    checks["loader_valid_python"] = (ok_loader, lmsg)

    return checks


# ---------------------------------------------------------------------------
# Task Registry
# ---------------------------------------------------------------------------


TASKS: Dict[str, Dict[str, Any]] = {
    "multi_provider_tools": {
        "builder": build_fixture_multi_provider_tools,
        "grader": grade_multi_provider_tools,
        "prompt": (
            "Our multi-provider agent tool definitions in `schemas/` are failing in production across "
            "OpenAI Chat Completions, OpenAI Responses, Anthropic strict tool use, Gemini function calling, "
            "and our fast billing worker (`workers/fast_invoice.py`). Production incidents:\n"
            "1. Anthropic returns HTTP 400 on `schemas/anthropic_tools.json` when strict mode is enabled.\n"
            "2. OpenAI strict validation rejects `schemas/openai_chat_tools.json` and `schemas/openai_responses_tools.json`.\n"
            "3. Gemini rejects `schemas/gemini_tools.json`.\n"
            "4. The router keeps picking `searchKbDocs` even for billing queries, and parameters arrive in wrong formats/units.\n"
            "5. `workers/fast_invoice.py` keeps miscalculating invoice totals right before calling its tool.\n"
            "6. Our 320-code merchant category enum bloats grammar compilation; replace it with an open string parameter backed by a companion merchant-category lookup/search tool.\n"
            "Inspect the whole repo (`README.md`, `workers/`, `schemas/`) and fix all schema files so every provider "
            "wire contract, strict-mode constraint, routing neutrality, parameter clarity, and worker-specific schema "
            "ordering is valid. Keep `workers/` untouched and preserve all business capabilities."
        ),
    },
    "broken_skill_repair": {
        "builder": build_fixture_broken_skill_repair,
        "grader": grade_broken_skill_repair,
        "prompt": (
            "Audit and repair the portable Agent Skill package currently under `Data_Pipeline_Audit/` so it is clean, "
            "open-spec compliant, portable across OSes, and ready for distribution. Fix any naming, frontmatter, "
            "context-budget, reference-linking, script-portability, and packaging-hygiene defects while preserving "
            "all actual domain audit rules (idempotency, backfill, schema_drift, dead_letter_queue) and making sure "
            "`check_pipeline.py --help` still exits 0."
        ),
    },
    "prompt_hardening_refactor": {
        "builder": build_fixture_prompt_hardening,
        "grader": grade_prompt_hardening,
        "prompt": (
            "Our customer-support assistant (`prompts/support_monolith.md`, configured in `config/model.yaml`) has "
            "four recurring incidents documented in `prompts/requirements.md`:\n"
            "1. Rule compliance collapsed after growing to 52 concurrent rules across triage, investigation, and resolution.\n"
            "2. Customer emails containing fake 'SYSTEM OVERRIDE' text occasionally hijack the assistant.\n"
            "3. Forbidden words (`crash`, `bug`, `outage`, `broken` and hyphenated forms like `consecutive-bug`) keep slipping into replies.\n"
            "4. Output formatting sometimes emits literal bracketed strings and burns excessive reasoning tokens.\n"
            "Inspect the repo and refactor the prompt architecture cleanly under `prompts/` (splitting stages into focused "
            "phase prompt files) to fix all four issues while preserving every stage's business requirements and keeping `app/loader.py` valid Python."
        ),
    },
}


# ---------------------------------------------------------------------------
# Pi Execution & Telemetry Parsing
# ---------------------------------------------------------------------------


def parse_pi_jsonl(stdout_text: str, skill_path: Optional[Path]) -> Dict[str, Any]:
    """Parse Pi v1.6.0 `--mode json` JSONL stream into clean telemetry."""
    turns = 0
    tool_calls: Dict[str, int] = {}
    read_paths: List[str] = []
    skill_read = False
    refs_read: List[str] = []
    system_prompt_text = ""
    input_tokens = 0
    output_tokens = 0
    reasoning_tokens = 0
    cache_read = 0
    total_tokens = 0
    cost_usd = 0.0
    parse_errors = 0
    aborted = False

    skill_norm = str(skill_path.resolve()).replace("\\", "/").lower() if skill_path else ""

    for line in stdout_text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            parse_errors += 1
            continue

        etype = ev.get("type")
        if etype == "turn_end":
            turns += 1
        elif etype == "agent_settled":
            aborted = bool(ev.get("aborted"))
        elif etype == "message_end":
            msg = ev.get("message") or {}
            role = msg.get("role")
            if role == "system" and not system_prompt_text:
                parts: List[str] = []
                content = msg.get("content")
                if isinstance(content, str) and content:
                    parts.append(content)
                elif isinstance(content, list):
                    parts.extend(str(b.get("text", "")) for b in content if isinstance(b, dict))
                sections = msg.get("sections")
                if isinstance(sections, dict):
                    parts.append(json.dumps(sections, ensure_ascii=False))
                system_prompt_text = "\n".join(parts)
            elif role == "assistant":
                usage = msg.get("usage") or {}
                input_tokens += int(usage.get("input") or 0)
                output_tokens += int(usage.get("output") or 0)
                reasoning_tokens += int(usage.get("reasoning") or 0)
                cache_read += int(usage.get("cacheRead") or 0)
                total_tokens += int(usage.get("totalTokens") or 0)
                cost_obj = usage.get("cost") or {}
                if isinstance(cost_obj, dict):
                    cost_usd += float(cost_obj.get("total") or 0.0)
                for blk in msg.get("content") or []:
                    if isinstance(blk, dict) and blk.get("type") == "toolCall":
                        tname = str(blk.get("name") or "unknown")
                        tool_calls[tname] = tool_calls.get(tname, 0) + 1
                        args = blk.get("arguments") or {}
                        if tname == "read" and isinstance(args, dict):
                            rpath = str(args.get("path") or "")
                            if rpath:
                                read_paths.append(rpath)
                                rnorm = rpath.replace("\\", "/").lower()
                                if skill_path is not None and skill_norm in rnorm:
                                    if rnorm.endswith("/skill.md"):
                                        skill_read = True
                                    elif "/references/" in rnorm and rnorm.endswith(".md"):
                                        refs_read.append(Path(rpath).name)
        elif etype == "tool_execution_start":
            # Fallback if a Pi version emits tool_execution_start without toolCall content blocks
            tname = str(ev.get("tool") or ev.get("toolName") or "")
            args = ev.get("args") or {}
            if tname == "read" and isinstance(args, dict):
                rpath = str(args.get("path") or "")
                if rpath and rpath not in read_paths:
                    read_paths.append(rpath)
                    rnorm = rpath.replace("\\", "/").lower()
                    if skill_path is not None and skill_norm in rnorm:
                        if rnorm.endswith("/skill.md"):
                            skill_read = True
                        elif "/references/" in rnorm and rnorm.endswith(".md"):
                            refs_read.append(Path(rpath).name)

    skill_listed_in_sys = (
        ("agent-system-authoring" in system_prompt_text)
        if skill_path is not None
        else ("<available_skills>" in system_prompt_text)
    )
    isolation_ok = (
        ("agent-system-authoring" in system_prompt_text)
        if skill_path is not None
        else ("agent-system-authoring" not in system_prompt_text and "<available_skills>" not in system_prompt_text)
    )

    return {
        "turns": turns,
        "tool_calls": tool_calls,
        "total_tool_calls": sum(tool_calls.values()),
        "skill_read": skill_read,
        "refs_read": sorted(set(refs_read)),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "reasoning_tokens": reasoning_tokens,
        "cache_read_tokens": cache_read,
        "total_tokens": total_tokens,
        "cost_usd": round(cost_usd, 6),
        "aborted": aborted,
        "parse_errors": parse_errors,
        "isolation_ok": isolation_ok,
        "skill_listed_in_sys": skill_listed_in_sys,
    }


def run_one_eval(
    pi_exe: str,
    task_id: str,
    variant_name: str,
    skill_path: Optional[Path],
    run_idx: int,
    model: str,
    thinking: str,
    tools: str,
    timeout: int,
    keep_work: bool = False,
) -> Dict[str, Any]:
    task = TASKS[task_id]
    work = Path(tempfile.mkdtemp(prefix=f"pi_eval_{task_id}_{variant_name}_r{run_idx}_"))
    task["builder"](work)

    cmd = [
        pi_exe,
        "-p",
        "--mode", "json",
        "--no-session",
        "-ne",  # --no-extensions
        "-nc",  # --no-context-files
        "--no-mcp",
        "-np",  # --no-prompt-templates
        "-na",  # --no-approve
        "-ns",  # --no-skills
        "--model", model,
        "--thinking", thinking,
        "--tools", tools,
    ]
    if skill_path is not None:
        cmd.extend(["--skill", str(skill_path.resolve())])
    cmd.extend(["--", task["prompt"]])

    t0 = time.time()
    agent_error: Optional[str] = None
    rc = -1
    stdout_text = ""
    stderr_text = ""
    try:
        proc = subprocess.run(
            cmd,
            cwd=work,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        rc = proc.returncode
        stdout_text = proc.stdout
        stderr_text = proc.stderr
        if rc != 0:
            agent_error = f"rc={rc}: {stderr_text.strip()[-300:]}"
    except subprocess.TimeoutExpired:
        agent_error = f"timeout after {timeout}s"

    wall_s = round(time.time() - t0, 2)
    telemetry = parse_pi_jsonl(stdout_text, skill_path)
    checks_raw = task["grader"](work)
    passed_cnt = sum(1 for ok, _ in checks_raw.values() if ok)
    total_cnt = len(checks_raw)

    rel_skill: Optional[str] = None
    if skill_path is not None:
        try:
            rel_skill = skill_path.resolve().relative_to(REPO_ROOT).as_posix()
        except ValueError:
            rel_skill = skill_path.name

    record: Dict[str, Any] = {
        "task_id": task_id,
        "variant": variant_name,
        "skill_path": rel_skill,
        "run_idx": run_idx,
        "model": model,
        "thinking": thinking,
        "tools": tools,
        "rc": rc,
        "agent_error": agent_error,
        "wall_seconds": wall_s,
        "strict_pass": passed_cnt == total_cnt,
        "passed_checks": passed_cnt,
        "total_checks": total_cnt,
        "check_score": round(passed_cnt / total_cnt, 4) if total_cnt else 0.0,
        "checks": {k: {"ok": ok, "detail": detail} for k, (ok, detail) in checks_raw.items()},
        **telemetry,
    }
    if keep_work:
        record["work_dir"] = str(work)
    else:
        shutil.rmtree(work, ignore_errors=True)
    return record


def verify_pristine_fixtures(selected_tasks: List[str]) -> int:
    """Verify every unedited broken fixture fails its intended defect checks."""
    print("=== Verifying Pristine Broken Fixtures (pre-agent baseline) ===")
    for tid in selected_tasks:
        work = Path(tempfile.mkdtemp(prefix=f"pi_dry_{tid}_"))
        try:
            TASKS[tid]["builder"](work)
            res = TASKS[tid]["grader"](work)
            passed = [k for k, (ok, _) in res.items() if ok]
            failed = [k for k, (ok, _) in res.items() if not ok]
            print(f"  {tid}: {len(passed)}/{len(res)} pass initially (anti-cheat only expected) | pass={passed} | fail={failed}")
        finally:
            shutil.rmtree(work, ignore_errors=True)
    return 0


def print_summary(records: List[Dict[str, Any]], task_ids: List[str], variant_names: List[str]) -> None:
    print("\n=== Pi Multi-Turn Real-Agent Eval Summary ===")
    hdr = f"{'Task':<26} {'Variant':<16} {'Strict':<8} {'Checks':<10} {'Turns':<7} {'Tools':<7} {'SkillRd':<8} {'TotTok':<10} {'Secs':<7}"
    print(hdr)
    print("-" * len(hdr))
    for tid in task_ids:
        for vname in variant_names:
            rs = [r for r in records if r["task_id"] == tid and r["variant"] == vname]
            if not rs:
                continue
            n = len(rs)
            sp = sum(1 for r in rs if r["strict_pass"])
            avg_chk = sum(r["check_score"] for r in rs) / n
            avg_turns = sum(r["turns"] for r in rs) / n
            avg_tools = sum(r["total_tool_calls"] for r in rs) / n
            sk_rd = sum(1 for r in rs if r["skill_read"])
            avg_tok = sum(r["total_tokens"] for r in rs) / n
            avg_sec = sum(r["wall_seconds"] for r in rs) / n
            print(
                f"{tid:<26} {vname:<16} {sp}/{n:<6} {avg_chk*100:5.1f}%    "
                f"{avg_turns:5.1f}  {avg_tools:5.1f}  {sk_rd}/{n:<6} {avg_tok:9.0f} {avg_sec:6.1f}s"
            )
            for r in rs:
                fails = [k for k, v in r["checks"].items() if not v["ok"]]
                if fails:
                    print(f"    run {r['run_idx']} failed checks: {fails} | refs_read={r['refs_read']} | iso={r['isolation_ok']}")
                else:
                    print(f"    run {r['run_idx']} ALL PASSED | refs_read={r['refs_read']} | iso={r['isolation_ok']}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument(
        "--variant",
        action="append",
        metavar="NAME=PATH_OR_NONE",
        help="Variant spec (repeatable), e.g. baseline=none --variant skill=skills/agent-system-authoring",
    )
    ap.add_argument("--task", action="append", choices=sorted(TASKS.keys()), help="Task id(s) to run (default: all)")
    ap.add_argument("--runs", type=int, default=1, help="Number of independent runs per (task, variant)")
    ap.add_argument("--model", default=os.environ.get("TARGET_MODEL", ""), help="Pi --model spec (or set TARGET_MODEL env var)")
    ap.add_argument("--thinking", default="high", help="Pi --thinking level (off/minimal/low/medium/high/xhigh/max)")
    ap.add_argument("--tools", default="read,edit,write,bash", help="Pi --tools allowlist")
    ap.add_argument("--pi-bin", default=shutil.which("pi"), help="Path to pi executable")
    ap.add_argument("--workers", type=int, default=3, help="Max concurrent Pi subprocesses")
    ap.add_argument("--timeout", type=int, default=360, help="Per-run timeout in seconds")
    ap.add_argument("--out", type=Path, default=None, help="Output JSONL file path")
    ap.add_argument("--keep-work", action="store_true", help="Keep temp workspaces after grading")
    ap.add_argument("--dry-run", action="store_true", help="Verify pristine broken fixtures without calling Pi")
    args = ap.parse_args()

    selected_tasks = args.task or list(TASKS.keys())
    if args.dry_run:
        return verify_pristine_fixtures(selected_tasks)

    if not args.model:
        sys.exit("TARGET_MODEL environment variable or --model flag is required.")

    if not args.pi_bin:
        sys.exit("pi binary not found on PATH; pass --pi-bin")

    variant_specs = args.variant or [
        "baseline=none",
        f"with_skill={DEFAULT_SKILL_DIR}",
    ]
    variants: List[Tuple[str, Optional[Path]]] = []
    for spec in variant_specs:
        name, sep, raw_path = spec.partition("=")
        if not sep or not name:
            sys.exit(f"Invalid --variant '{spec}', expected NAME=PATH_OR_NONE")
        if raw_path.lower() in ("none", "null", ""):
            variants.append((name, None))
        else:
            p = Path(raw_path).resolve()
            if not (p / "SKILL.md").is_file():
                sys.exit(f"Variant '{name}' missing SKILL.md at {p}")
            variants.append((name, p))

    jobs = [
        (tid, vname, spath, ridx)
        for tid in selected_tasks
        for vname, spath in variants
        for ridx in range(1, args.runs + 1)
    ]
    print(
        f"Running {len(jobs)} Pi headless runs | model={args.model} | thinking={args.thinking} "
        f"| tools={args.tools} | flags=-ne -nc --no-mcp -np -na -ns --no-session | workers={args.workers}",
        flush=True,
    )

    records: List[Dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.workers)) as ex:
        fut_map = {
            ex.submit(
                run_one_eval,
                args.pi_bin,
                tid,
                vname,
                spath,
                ridx,
                args.model,
                args.thinking,
                args.tools,
                args.timeout,
                args.keep_work,
            ): (tid, vname, ridx)
            for tid, vname, spath, ridx in jobs
        }
        for fut in concurrent.futures.as_completed(fut_map):
            rec = fut.result()
            records.append(rec)
            print(
                f"  DONE {rec['task_id']} [{rec['variant']} r{rec['run_idx']}]: "
                f"{rec['passed_checks']}/{rec['total_checks']} strict={rec['strict_pass']} "
                f"turns={rec['turns']} tools={rec['total_tool_calls']} skill_read={rec['skill_read']} "
                f"iso={rec['isolation_ok']} tok={rec['total_tokens']} {rec['wall_seconds']}s",
                flush=True,
            )

    records.sort(key=lambda r: (r["task_id"], r["variant"], r["run_idx"]))
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        print(f"Saved {len(records)} records to {args.out}")

    print_summary(records, selected_tasks, [v[0] for v in variants])
    return 0


if __name__ == "__main__":
    sys.exit(main())
