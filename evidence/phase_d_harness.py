# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Phase D Empirical Test Harness for agent-system-authoring.

Executes powered, deconfounded, multi-iteration (N = 5 runs per prompt)
experiments on GPT 6 Luna across the four core open hypotheses in
references/unverified_hypotheses.md:
- PD-1 (H-02a / R-TOOL-05): TS-2 N=5 replication (15 prompts x 2 arms x 5 = 150 calls)
- PD-2 (H-02b / Verbosity): Parameter description verbosity/dilution curve across
  15 / 50 / 120 / 250 tokens per param on 6 non-standard rules (16 x 4 x 5 = 320 calls)
- PD-3 (H-03 / Markdown): Plain prose vs bullet list vs Markdown ### headers inside
  JSON tool descriptions, counterbalanced & wording-equalized (16 x 3 x 5 = 240 calls)
- PD-4 (H-06 / Numerals): Arabic digits vs spelled-out English numbers for exact
  multi-constraint counting tasks (16 x 2 x 5 = 160 calls)
- PD-5 (H-07 / TS vs JSON Schema): Prompt-injected deeply nested JSON Schema vs
  semantically equivalent TypeScript interface signatures (16 x 2 x 5 = 160 calls)

Configured solely via environment variables:
  - GATEWAY_URL
  - API_KEY
  - TARGET_MODEL (provenance traces ran on GPT 6 Luna)

Writes raw records (stripped of auth headers and gateway URLs) to
evidence/raw_phase_d/results_<SUITE>.jsonl.
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


@dataclass
class RunConfig:
    gateway_url: str
    api_key: str
    model: str = DEFAULT_MODEL
    iterations: int = DEFAULT_ITERATIONS
    concurrency: int = DEFAULT_CONCURRENCY
    max_retries: int = 5
    timeout: float = 120.0
    limit_prompts: Optional[int] = None


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
# PD-1 (H-02a / R-TOOL-05): Powered N=5 Replication of TS-2
# ------------------------------------------------------------------------------

class PD1_TS2Replication:
    id = "PD-1"
    EFFORT = "high"

    TASKS = [
        {"id": "PD1_01", "query": "Dispatch mission 'LOG-101' scheduled for November 20, 2026 at 2:30 PM UTC. The settlement is in US dollars and the target is San Francisco City Hall (latitude 37.7793, longitude -122.4192).", "exp_ts": "2026-11-20T14:30:00Z", "exp_curr": "USD", "exp_geo": "37.7793,-122.4192"},
        {"id": "PD1_02", "query": "Set up logistics run 'LOG-102' departing on December 1st, 2026 at 09:00 AM UTC. Bill the budget in Euros (€) at the Eiffel Tower site located at 48.8584 N, 2.2945 E.", "exp_ts": "2026-12-01T09:00:00Z", "exp_curr": "EUR", "exp_geo": "48.8584,2.2945"},
        {"id": "PD1_03", "query": "Create dispatch 'LOG-103' planned for 2026-11-25 at 18:00 UTC with billing in British Pounds and drop-off coordinates at Big Ben (lat 51.5007, lon -0.1246).", "exp_ts": "2026-11-25T18:00:00Z", "exp_curr": "GBP", "exp_geo": "51.5007,-0.1246"},
        {"id": "PD1_04", "query": "Initiate transport 'LOG-104' for Jan 15, 2027 at 08:15 AM UTC. Fee currency is Japanese Yen, destination coordinates Tokyo Tower (35.6586, 139.7454).", "exp_ts": "2027-01-15T08:15:00Z", "exp_curr": "JPY", "exp_geo": "35.6586,139.7454"},
        {"id": "PD1_05", "query": "Schedule delivery 'LOG-105' for November 22, 2026 at 23:45 UTC, paid in Canadian Dollars ($CAD), situated at CN Tower (lat 43.6426, long -79.3871).", "exp_ts": "2026-11-22T23:45:00Z", "exp_curr": "CAD", "exp_geo": "43.6426,-79.3871"},
        {"id": "PD1_06", "query": "Plan dispatch 'LOG-106' for October 31, 2026 at 12:00:00 UTC with payment in Australian Dollars, location Sydney Opera House at -33.8568, 151.2153.", "exp_ts": "2026-10-31T12:00:00Z", "exp_curr": "AUD", "exp_geo": "-33.8568,151.2153"},
        {"id": "PD1_07", "query": "Dispatch logistics mission 'LOG-107' on Dec 10, 2026 at 04:00 AM UTC, currency Swiss Francs (CHF), location Zurich Central Station at 47.3782, 8.5402.", "exp_ts": "2026-12-10T04:00:00Z", "exp_curr": "CHF", "exp_geo": "47.3782,8.5402"},
        {"id": "PD1_08", "query": "Launch route 'LOG-108' on Nov 28, 2026 at 16:20 UTC with settlement in Singapore Dollars, coordinate Marina Bay Sands at 1.2834, 103.8607.", "exp_ts": "2026-11-28T16:20:00Z", "exp_curr": "SGD", "exp_geo": "1.2834,103.8607"},
        {"id": "PD1_09", "query": "Dispatch unit 'LOG-109' on Dec 5, 2026 at 10:30 UTC, funded in Hong Kong Dollars, at Victoria Peak (22.2759 lat, 114.1455 lon).", "exp_ts": "2026-12-05T10:30:00Z", "exp_curr": "HKD", "exp_geo": "22.2759,114.1455"},
        {"id": "PD1_10", "query": "Create run 'LOG-110' for Nov 19, 2026 at 20:00 UTC, currency New Zealand Dollars, at Sky Tower Auckland (-36.8485, 174.7633).", "exp_ts": "2026-11-19T20:00:00Z", "exp_curr": "NZD", "exp_geo": "-36.8485,174.7633"},
        {"id": "PD1_11", "query": "Execute mission 'LOG-111' on Jan 2, 2027 at 07:00 UTC, billed in Swedish Krona, target Stockholm City Hall (59.3275, 18.0544).", "exp_ts": "2027-01-02T07:00:00Z", "exp_curr": "SEK", "exp_geo": "59.3275,18.0544"},
        {"id": "PD1_12", "query": "Schedule cargo 'LOG-112' for Dec 15, 2026 at 15:45 UTC, payment in Norwegian Krone, location Oslo Opera House (59.9075, 10.7531).", "exp_ts": "2026-12-15T15:45:00Z", "exp_curr": "NOK", "exp_geo": "59.9075,10.7531"},
        {"id": "PD1_13", "query": "Deploy transport 'LOG-113' on Nov 24, 2026 at 11:10 UTC, settlement in Danish Krone, site Little Mermaid Copenhagen (55.6929, 12.5993).", "exp_ts": "2026-11-24T11:10:00Z", "exp_curr": "DKK", "exp_geo": "55.6929,12.5993"},
        {"id": "PD1_14", "query": "Register dispatch 'LOG-114' for Dec 22, 2026 at 13:00 UTC, currency South Korean Won, location N Seoul Tower (37.5512, 126.9882).", "exp_ts": "2026-12-22T13:00:00Z", "exp_curr": "KRW", "exp_geo": "37.5512,126.9882"},
        {"id": "PD1_15", "query": "Initiate run 'LOG-115' on Jan 10, 2027 at 01:30 UTC, billing in Mexican Pesos, location Angel of Independence Mexico City (19.4270, -99.1677).", "exp_ts": "2027-01-10T01:30:00Z", "exp_curr": "MXN", "exp_geo": "19.4270,-99.1677"},
    ]

    ISO_8601_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
    ISO_4217_RE = re.compile(r"^[A-Z]{3}$")
    GEO_RE = re.compile(r"^-?(?:90(?:\.0+)?|[1-8]?\d(?:\.\d+)?),-?(?:180(?:\.0+)?|1[0-7]\d(?:\.\d+)?|\d{1,2}(?:\.\d+)?)$")

    @classmethod
    def _tools(cls, cond: str) -> List[Dict[str, Any]]:
        if cond == "with_descriptions":
            props = {
                "mission_id": {"type": "string", "description": "The unique mission alphanumeric identifier (e.g., 'LOG-101')."},
                "schedule_timestamp": {"type": "string", "description": "ISO 8601 UTC timestamp formatted strictly as 'YYYY-MM-DDTHH:MM:SSZ' (e.g., '2026-11-20T14:30:00Z'). Do not use local timezone offsets or unformatted text."},
                "settlement_currency": {"type": "string", "description": "Three-letter uppercase ISO 4217 currency code (e.g., 'USD', 'EUR', 'GBP', 'JPY'). Do not use currency symbols like $ or €."},
                "geo_coordinates": {"type": "string", "description": "Target latitude and longitude formatted strictly as a single comma-separated string 'lat,lon' in signed decimal degrees without spaces (e.g., '37.7793,-122.4192'). Latitude must be between -90 and 90, longitude between -180 and 180."},
            }
        else:
            props = {
                "mission_id": {"type": "string", "description": "The mission identifier."},
                "schedule_timestamp": {"type": "string", "description": "The schedule timestamp."},
                "settlement_currency": {"type": "string", "description": "The settlement currency."},
                "geo_coordinates": {"type": "string", "description": "The target geo coordinates."},
            }
        return [{
            "type": "function",
            "function": {
                "name": "dispatch_logistics_mission",
                "description": "Dispatches an autonomous logistics transport mission to a target coordinate.",
                "strict": True,
                "parameters": {
                    "type": "object",
                    "properties": props,
                    "required": ["mission_id", "schedule_timestamp", "settlement_currency", "geo_coordinates"],
                    "additionalProperties": False,
                },
            },
        }]

    @classmethod
    def generate_items(cls, cfg: RunConfig) -> List[Dict[str, Any]]:
        tasks = cls.TASKS[: cfg.limit_prompts] if cfg.limit_prompts else cls.TASKS
        items = []
        for it in range(1, cfg.iterations + 1):
            for t in tasks:
                for cond in ("without_descriptions", "with_descriptions"):
                    items.append({
                        "hypothesis_id": cls.id,
                        "prompt_id": t["id"],
                        "condition": cond,
                        "iteration": it,
                        "reasoning_effort": cls.EFFORT,
                        "payload": {
                            "model": cfg.model,
                            "messages": [{"role": "user", "content": t["query"]}],
                            "tools": cls._tools(cond),
                            "tool_choice": "auto",
                            "reasoning_effort": cls.EFFORT,
                        },
                        "meta": {"exp_ts": t["exp_ts"], "exp_curr": t["exp_curr"], "exp_geo": t["exp_geo"]},
                    })
        return items

    @classmethod
    def evaluate(cls, item: Dict[str, Any], text: str, tool_calls: List[Dict[str, Any]]) -> Dict[str, Any]:
        if len(tool_calls) != 1:
            return {"valid_syntax": False, "timestamp_valid": 0.0, "currency_valid": 0.0, "geo_valid": 0.0, "all_fields_valid": 0.0, "score": 0.0}
        try:
            args = json.loads(tool_calls[0].get("function", {}).get("arguments", "{}"))
        except Exception:
            return {"valid_syntax": False, "timestamp_valid": 0.0, "currency_valid": 0.0, "geo_valid": 0.0, "all_fields_valid": 0.0, "score": 0.0}
        ts_val = str(args.get("schedule_timestamp", ""))
        curr_val = str(args.get("settlement_currency", ""))
        geo_val = str(args.get("geo_coordinates", ""))
        ts_ok = bool(cls.ISO_8601_UTC_RE.match(ts_val)) and (ts_val == item["meta"]["exp_ts"])
        curr_ok = bool(cls.ISO_4217_RE.match(curr_val)) and (curr_val == item["meta"]["exp_curr"])
        geo_ok = False
        if cls.GEO_RE.match(geo_val):
            try:
                elat, elon = map(float, geo_val.split(","))
                xlat, xlon = map(float, item["meta"]["exp_geo"].split(","))
                geo_ok = abs(elat - xlat) < 1e-3 and abs(elon - xlon) < 1e-3
            except Exception:
                geo_ok = False
        all_ok = 1.0 if (ts_ok and curr_ok and geo_ok) else 0.0
        return {
            "valid_syntax": True,
            "timestamp_valid": 1.0 if ts_ok else 0.0,
            "currency_valid": 1.0 if curr_ok else 0.0,
            "geo_valid": 1.0 if geo_ok else 0.0,
            "all_fields_valid": all_ok,
            "score": all_ok,
        }


# ------------------------------------------------------------------------------
# PD-2 (H-02b): Parameter Description Verbosity Ceiling & Attention Dilution
# ------------------------------------------------------------------------------

class PD2_ParamVerbosityCeiling:
    id = "PD-2"
    EFFORT = "none"

    TASKS = [
        {"id": "PD2_01", "query": "Record telemetry for batch 7 on March 4, 2026 at 08:15 UTC in San Francisco, US (lat 37.7749, lon -122.4194). Node readings show CPU 68% and memory 54%. Mark as urgent priority.", "exp": {"batch_ref": "BATCH_0007", "window_utc": "2026/03/04-08:15", "region_tag": "us:sfo", "metric_payload": "cpu=68;mem=54", "geo_pair": "-122.4194|37.7749", "priority_code": "PRI-1"}},
        {"id": "PD2_02", "query": "Log telemetry batch 42 captured on April 19, 2026 at 14:30 UTC in Frankfurt, Germany (lat 50.1109, lon 8.6821). Metrics: memory 71%, CPU 45%. Normal priority dispatch.", "exp": {"batch_ref": "BATCH_0042", "window_utc": "2026/04/19-14:30", "region_tag": "de:fra", "metric_payload": "cpu=45;mem=71", "geo_pair": "8.6821|50.1109", "priority_code": "PRI-2"}},
        {"id": "PD2_03", "query": "Submit telemetry batch 108 for May 2, 2026 at 23:05 UTC from Tokyo, Japan (lat 35.6762, lon 139.6503). Observed utilization is 89% CPU and 82% memory. Classify as deferred priority.", "exp": {"batch_ref": "BATCH_0108", "window_utc": "2026/05/02-23:05", "region_tag": "jp:tyo", "metric_payload": "cpu=89;mem=82", "geo_pair": "139.6503|35.6762", "priority_code": "PRI-3"}},
        {"id": "PD2_04", "query": "Upload batch 315 telemetry snapshot taken June 11, 2026 at 00:45 UTC in London, UK (lat 51.5074, lon -0.1278). Memory usage was 39% and CPU stood at 27%. Treat as normal priority.", "exp": {"batch_ref": "BATCH_0315", "window_utc": "2026/06/11-00:45", "region_tag": "gb:lon", "metric_payload": "cpu=27;mem=39", "geo_pair": "-0.1278|51.5074", "priority_code": "PRI-2"}},
        {"id": "PD2_05", "query": "Archive batch 9 telemetry for July 28, 2026 at 19:50 UTC from Singapore (country SG, city SIN; lat 1.3521, lon 103.8198). CPU 94%, mem 91%. Escalate as urgent priority.", "exp": {"batch_ref": "BATCH_0009", "window_utc": "2026/07/28-19:50", "region_tag": "sg:sin", "metric_payload": "cpu=94;mem=91", "geo_pair": "103.8198|1.3521", "priority_code": "PRI-1"}},
        {"id": "PD2_06", "query": "Send batch 520 telemetry from Sydney, Australia (AU, SYD; lat -33.8688, lon 151.2093) recorded August 15, 2026 at 06:20 UTC. Memory 63%, CPU 58%. Deferred priority queue.", "exp": {"batch_ref": "BATCH_0520", "window_utc": "2026/08/15-06:20", "region_tag": "au:syd", "metric_payload": "cpu=58;mem=63", "geo_pair": "151.2093|-33.8688", "priority_code": "PRI-3"}},
        {"id": "PD2_07", "query": "Report telemetry batch 84 on September 3, 2026 at 11:00 UTC in New York, US (NYC; lat 40.7128, lon -74.0060). Load readings: CPU 77%, memory 66%. Mark normal priority.", "exp": {"batch_ref": "BATCH_0084", "window_utc": "2026/09/03-11:00", "region_tag": "us:nyc", "metric_payload": "cpu=77;mem=66", "geo_pair": "-74.0060|40.7128", "priority_code": "PRI-2"}},
        {"id": "PD2_08", "query": "Register batch 1204 telemetry from Paris, France (FR, PAR; lat 48.8566, lon 2.3522) at 17:40 UTC on October 9, 2026. Memory 48%, CPU 31%. Urgent priority handling.", "exp": {"batch_ref": "BATCH_1204", "window_utc": "2026/10/09-17:40", "region_tag": "fr:par", "metric_payload": "cpu=31;mem=48", "geo_pair": "2.3522|48.8566", "priority_code": "PRI-1"}},
        {"id": "PD2_09", "query": "Dispatch batch 63 telemetry collected November 12, 2026 at 03:25 UTC in Toronto, Canada (CA, TOR; lat 43.6532, lon -79.3832). CPU 52%, memory 49%. Deferred priority.", "exp": {"batch_ref": "BATCH_0063", "window_utc": "2026/11/12-03:25", "region_tag": "ca:tor", "metric_payload": "cpu=52;mem=49", "geo_pair": "-79.3832|43.6532", "priority_code": "PRI-3"}},
        {"id": "PD2_10", "query": "Capture batch 901 telemetry on December 1, 2026 at 21:10 UTC from Dublin, Ireland (IE, DUB; lat 53.3498, lon -6.2603). Memory 85%, CPU 73%. Urgent priority.", "exp": {"batch_ref": "BATCH_0901", "window_utc": "2026/12/01-21:10", "region_tag": "ie:dub", "metric_payload": "cpu=73;mem=85", "geo_pair": "-6.2603|53.3498", "priority_code": "PRI-1"}},
        {"id": "PD2_11", "query": "Emit batch 15 telemetry on January 22, 2027 at 09:35 UTC in Seoul, South Korea (KR, SEL; lat 37.5665, lon 126.9780). CPU 61%, memory 57%. Normal priority.", "exp": {"batch_ref": "BATCH_0015", "window_utc": "2027/01/22-09:35", "region_tag": "kr:sel", "metric_payload": "cpu=61;mem=57", "geo_pair": "126.9780|37.5665", "priority_code": "PRI-2"}},
        {"id": "PD2_12", "query": "Post batch 440 telemetry for February 8, 2027 at 16:05 UTC in Sao Paulo, Brazil (BR, SAO; lat -23.5505, lon -46.6333). Memory 74%, CPU 64%. Deferred priority.", "exp": {"batch_ref": "BATCH_0440", "window_utc": "2027/02/08-16:05", "region_tag": "br:sao", "metric_payload": "cpu=64;mem=74", "geo_pair": "-46.6333|-23.5505", "priority_code": "PRI-3"}},
        {"id": "PD2_13", "query": "Transmit batch 777 telemetry on March 17, 2027 at 05:55 UTC from Zurich, Switzerland (CH, ZRH; lat 47.3769, lon 8.5417). CPU 36%, memory 41%. Normal priority.", "exp": {"batch_ref": "BATCH_0777", "window_utc": "2027/03/17-05:55", "region_tag": "ch:zrh", "metric_payload": "cpu=36;mem=41", "geo_pair": "8.5417|47.3769", "priority_code": "PRI-2"}},
        {"id": "PD2_14", "query": "Record batch 28 telemetry on April 6, 2027 at 12:15 UTC in Mumbai, India (IN, BOM; lat 19.0760, lon 72.8777). Memory 93%, CPU 88%. Urgent priority.", "exp": {"batch_ref": "BATCH_0028", "window_utc": "2027/04/06-12:15", "region_tag": "in:bom", "metric_payload": "cpu=88;mem=93", "geo_pair": "72.8777|19.0760", "priority_code": "PRI-1"}},
        {"id": "PD2_15", "query": "Forward batch 609 telemetry taken May 25, 2027 at 20:40 UTC in Amsterdam, Netherlands (NL, AMS; lat 52.3676, lon 4.9041). CPU 49%, memory 53%. Deferred priority.", "exp": {"batch_ref": "BATCH_0609", "window_utc": "2027/05/25-20:40", "region_tag": "nl:ams", "metric_payload": "cpu=49;mem=53", "geo_pair": "4.9041|52.3676", "priority_code": "PRI-3"}},
        {"id": "PD2_16", "query": "Log batch 3 telemetry on June 30, 2027 at 07:05 UTC from Seattle, US (SEA; lat 47.6062, lon -122.3321). Memory 62%, CPU 44%. Normal priority.", "exp": {"batch_ref": "BATCH_0003", "window_utc": "2027/06/30-07:05", "region_tag": "us:sea", "metric_payload": "cpu=44;mem=62", "geo_pair": "-122.3321|47.6062", "priority_code": "PRI-2"}},
    ]

    CORE_RULES = {
        "batch_ref": "Format strictly as 'BATCH_' plus a 4-digit zero-padded integer (e.g., 'BATCH_0042').",
        "window_utc": "Format UTC capture time strictly as 'YYYY/MM/DD-HH:MM' using slashes and a hyphen, without seconds or 'Z' (e.g., '2026/04/19-14:30').",
        "region_tag": "Format strictly as lowercase '<2-letter-country>:<3-letter-city>' separated by a colon (e.g., 'us:sfo', 'de:fra', 'gb:lon').",
        "metric_payload": "Format strictly as 'cpu=<int>;mem=<int>' in that exact order with no spaces or percent signs (e.g., 'cpu=68;mem=54').",
        "geo_pair": "Format strictly with LONGITUDE FIRST then latitude separated by a pipe '|' and no spaces: 'lon|lat' (e.g., '-122.4194|37.7749').",
        "priority_code": "Map urgent to 'PRI-1', normal to 'PRI-2', and deferred to 'PRI-3' exactly (do not use P0/P1/P2).",
    }

    MOD_CONTEXT = {
        "batch_ref": "Identifies the ingestion batch sequence in the telemetry warehouse for deduplication and replay tracking.",
        "window_utc": "Represents the minute-level UTC bucket used to partition incoming regional telemetry streams across storage shards.",
        "region_tag": "Identifies the physical datacenter geography for latency attribution, compliance tagging, and routing lookups.",
        "metric_payload": "Encodes host compute and RAM utilization integers captured at the end of the sampling interval.",
        "geo_pair": "Stores the point-of-presence coordinate pair consumed by the spatial indexing layer in GIS easting-northing order.",
        "priority_code": "Determines downstream queue triage tier and alert dispatch latency within the operations pipeline.",
    }

    VERBOSE_LEAD = (
        "This field participates in the enterprise multi-region observability ingestion contract maintained jointly by "
        "Platform SRE, Core Storage Engineering, and Compliance Telemetry Operations. Historical migrations from the v1 "
        "batch collector introduced inconsistent upstream labels across legacy regional gateways, so downstream consumers "
        "normalize records during nightly Parquet compaction and cross-region replication. "
    )
    VERBOSE_TAIL = (
        " Operators auditing dashboards should cross-check ingestion timestamps against cluster clock skew advisories "
        "and confirm partition alignment in the quarterly retention ledger before triggering automated backfill pipelines."
    )

    BLOAT_EXTRA_LEAD = (
        "Background governance note: Beginning in Q2 2024, the Telemetry Architecture Steering Committee consolidated "
        "seventeen regional ingestion collectors into a unified gateway protocol supporting both streaming and batch "
        "uploads. Although older Kafka bridges accepted loose human-readable tokens and performed regex coercion inside "
        "Spark jobs, those post-hoc coercions caused subtle schema drift across multi-tenant billing rollups, audit "
        "trails, and executive availability scorecards. Consequently, platform teams established a canonical transport "
        "representation documented in internal RFC-418 and referenced across runbooks, onboarding guides, and disaster "
        "recovery drills across North America, EMEA, and APAC zones. "
    )
    BLOAT_EXTRA_TAIL = (
        " Additional operational context: Downstream BigQuery views, Grafana federation proxies, and cold-storage glacier "
        "archives index this attribute alongside tenant cluster metadata, firmware generation tags, and synthetic canary "
        "probes. When troubleshooting delayed alerts or missing rollups, engineers should verify gateway TLS rotation "
        "status, check broker consumer lag metrics, review dead-letter topic saturation thresholds, and coordinate schema "
        "change announcements at least two release cycles ahead of deprecation freezes to prevent silent pipeline drops "
        "during peak traffic events or quarterly compliance snapshots."
    )

    @classmethod
    def _build_desc(cls, field: str, cond: str) -> str:
        core = cls.CORE_RULES[field]
        mod = cls.MOD_CONTEXT[field]
        if cond == "compact_15t":
            return core
        if cond == "moderate_50t":
            return f"{mod} {core}"
        if cond == "verbose_120t":
            return f"{cls.VERBOSE_LEAD}{mod} {core}{cls.VERBOSE_TAIL}"
        # bloated_250t
        return f"{cls.BLOAT_EXTRA_LEAD}{cls.VERBOSE_LEAD}{mod} {core}{cls.VERBOSE_TAIL}{cls.BLOAT_EXTRA_TAIL}"

    @classmethod
    def _tools(cls, cond: str) -> List[Dict[str, Any]]:
        fields = ["batch_ref", "window_utc", "region_tag", "metric_payload", "geo_pair", "priority_code"]
        props = {f: {"type": "string", "description": cls._build_desc(f, cond)} for f in fields}
        return [{
            "type": "function",
            "function": {
                "name": "submit_telemetry_dispatch",
                "description": "Submits a regional infrastructure telemetry snapshot with six strictly formatted string parameters.",
                "strict": True,
                "parameters": {
                    "type": "object",
                    "properties": props,
                    "required": fields,
                    "additionalProperties": False,
                },
            },
        }]

    @classmethod
    def generate_items(cls, cfg: RunConfig) -> List[Dict[str, Any]]:
        tasks = cls.TASKS[: cfg.limit_prompts] if cfg.limit_prompts else cls.TASKS
        items = []
        for it in range(1, cfg.iterations + 1):
            for t in tasks:
                for cond in ("compact_15t", "moderate_50t", "verbose_120t", "bloated_250t"):
                    items.append({
                        "hypothesis_id": cls.id,
                        "prompt_id": t["id"],
                        "condition": cond,
                        "iteration": it,
                        "reasoning_effort": cls.EFFORT,
                        "payload": {
                            "model": cfg.model,
                            "messages": [{"role": "user", "content": t["query"]}],
                            "tools": cls._tools(cond),
                            "tool_choice": {"type": "function", "function": {"name": "submit_telemetry_dispatch"}},
                            "reasoning_effort": cls.EFFORT,
                        },
                        "meta": {"exp": t["exp"]},
                    })
        return items

    @classmethod
    def evaluate(cls, item: Dict[str, Any], text: str, tool_calls: List[Dict[str, Any]]) -> Dict[str, Any]:
        fields = ["batch_ref", "window_utc", "region_tag", "metric_payload", "geo_pair", "priority_code"]
        if not tool_calls:
            return {**{f"{f}_ok": 0.0 for f in fields}, "strict_all_6": 0.0, "score": 0.0}
        try:
            args = json.loads(tool_calls[0].get("function", {}).get("arguments", "{}"))
        except Exception:
            return {**{f"{f}_ok": 0.0 for f in fields}, "strict_all_6": 0.0, "score": 0.0}
        exp = item["meta"]["exp"]
        res: Dict[str, Any] = {}
        ok_cnt = 0
        for f in fields:
            val = str(args.get(f, "")).strip()
            if f == "geo_pair":
                # Exact pipe delimiter, no spaces, lon|lat within 1e-3
                ok = False
                if " " not in val and val.count("|") == 1:
                    try:
                        elon, elat = map(float, val.split("|"))
                        xlon, xlat = map(float, exp[f].split("|"))
                        ok = abs(elon - xlon) < 1e-3 and abs(elat - xlat) < 1e-3
                    except Exception:
                        ok = False
            else:
                ok = (val == exp[f])
            res[f"{f}_ok"] = 1.0 if ok else 0.0
            if ok:
                ok_cnt += 1
        res["strict_all_6"] = 1.0 if ok_cnt == 6 else 0.0
        res["score"] = ok_cnt / 6.0
        return res


# ------------------------------------------------------------------------------
# PD-3 (H-03): Markdown Syntax Inside JSON Tool Descriptions
# ------------------------------------------------------------------------------

class PD3_MarkdownInToolDescriptions:
    id = "PD-3"
    EFFORT = "none"

    # 4 sister-tool pairs with wording strictly equalized across plain_prose, bullet_list, markdown_headers
    PAIRS = {
        "docs": {
            "a": {
                "name": "search_live_runbooks",
                "purpose": "Searches active operational runbooks and current 2025-2027 engineering playbooks.",
                "use": "Use when looking up current procedures, live on-call steps, or active deployment checklists.",
                "not_use": "Do NOT use for pre-2025 historical compliance snapshots, SOC-2 audit archives, or closed incident postmortems; use search_compliance_archive instead.",
                "caveat": "Returns live wiki Markdown excerpts only and excludes frozen audit PDFs.",
            },
            "b": {
                "name": "search_compliance_archive",
                "purpose": "Searches frozen pre-2025 compliance PDFs, historical SOC-2 audit evidence, and closed postmortems.",
                "use": "Use when retrieving archived audit exceptions, regulatory sign-offs, or pre-2025 post-incident reports.",
                "not_use": "Do NOT use for active live operational procedures or current 2025-2027 runbooks; use search_live_runbooks instead.",
                "caveat": "Returns immutable archived document text only and does not reflect recent wiki edits.",
            },
        },
        "billing": {
            "a": {
                "name": "query_billing_ledger",
                "purpose": "Executes structured lookups against customer invoice records, payment counts, and credit balances.",
                "use": "Use when computing quantitative totals, failed charge counts, or specific account invoice histories.",
                "not_use": "Do NOT use for written company refund policies, SLA contract wording, or eligibility rules; use search_billing_policies instead.",
                "caveat": "Returns tabular numeric records only and contains no policy prose.",
            },
            "b": {
                "name": "search_billing_policies",
                "purpose": "Searches written billing handbooks, SLA refund eligibility windows, and proration policy documents.",
                "use": "Use when answering what company policy permits, contractual terms, or eligibility rules for credits.",
                "not_use": "Do NOT use for querying customer invoice counts, transaction histories, or account dollar balances; use query_billing_ledger instead.",
                "caveat": "Returns policy documentation text only and cannot inspect individual customer accounts.",
            },
        },
        "metrics": {
            "a": {
                "name": "fetch_realtime_metrics",
                "purpose": "Fetches live streaming cluster CPU, latency, and error-rate time series from the past 24 hours.",
                "use": "Use when diagnosing active spikes, current p99 latency, or real-time service health within the last 24 hours.",
                "not_use": "Do NOT use for multi-week historical rollups, quarterly trends, or monthly cost attribution; use query_analytics_warehouse instead.",
                "caveat": "Retains only 24 hours of high-resolution telemetry and returns empty sets for older dates.",
            },
            "b": {
                "name": "query_analytics_warehouse",
                "purpose": "Queries historical multi-day, monthly, and quarterly aggregated infrastructure metrics and cost attribution tables.",
                "use": "Use when analyzing trends older than 24 hours, monthly capacity growth, or quarterly cost breakdowns.",
                "not_use": "Do NOT use for live real-time incident spikes or sub-minute telemetry from the current day; use fetch_realtime_metrics instead.",
                "caveat": "Warehouse tables refresh nightly and lag live production events by up to 24 hours.",
            },
        },
        "incident": {
            "a": {
                "name": "dispatch_urgent_page",
                "purpose": "Triggers an immediate high-urgency on-call page for active P0/P1 customer-impacting outages.",
                "use": "Use ONLY when production traffic is actively degraded or customer-facing availability is down right now.",
                "not_use": "Do NOT use for non-urgent bugs, post-incident follow-ups, P2/P3 defects, or scheduled maintenance; use create_engineering_ticket instead.",
                "caveat": "Wakes primary on-call engineers immediately and should never be invoked for backlog work.",
            },
            "b": {
                "name": "create_engineering_ticket",
                "purpose": "Creates a tracked backlog issue for non-urgent bugs, P2/P3 defects, postmortem actions, and scheduled work.",
                "use": "Use when logging follow-up hardening tasks, non-blocking defects, or planned maintenance changes.",
                "not_use": "Do NOT use when an active P0/P1 production outage requires immediate human intervention; use dispatch_urgent_page instead.",
                "caveat": "Tickets enter normal sprint triage and do not alert on-call responders.",
            },
        },
    }

    TASKS = [
        {"id": "PD3_01", "pair": "docs", "exp": "search_live_runbooks", "query": "Before our Q4 compliance audit starts next week, pull the active 2026 database failover runbook checklist our on-call team runs today."},
        {"id": "PD3_02", "pair": "docs", "exp": "search_compliance_archive", "query": "Find the closed 2023 Q3 SOC-2 compliance audit exception PDF referencing our old database failover runbook."},
        {"id": "PD3_03", "pair": "docs", "exp": "search_live_runbooks", "query": "Look up the current 2026 TLS certificate rotation playbook for edge gateways so SRE can execute tonight's deployment."},
        {"id": "PD3_04", "pair": "docs", "exp": "search_compliance_archive", "query": "Retrieve the archived 2024 post-incident report from our edge TLS expiration outage for regulatory review."},
        {"id": "PD3_05", "pair": "billing", "exp": "query_billing_ledger", "query": "Under our enterprise refund policy review, how many failed invoice charges occurred for account ACCT-4410 in October 2026?"},
        {"id": "PD3_06", "pair": "billing", "exp": "search_billing_policies", "query": "Account ACCT-4410 had three failed invoice charges last month—what does our written policy say about refund eligibility windows?"},
        {"id": "PD3_07", "pair": "billing", "exp": "query_billing_ledger", "query": "What is the total dollar amount of SLA credits posted to ACCT-9021 across invoices from Q1 through Q3 2026?"},
        {"id": "PD3_08", "pair": "billing", "exp": "search_billing_policies", "query": "Explain the written proration formula and flat processing fee rules governing annual enterprise plan cancellations."},
        {"id": "PD3_09", "pair": "metrics", "exp": "fetch_realtime_metrics", "query": "Compared to last quarter's baseline, what is the live checkout-api p99 latency right now over the past 30 minutes?"},
        {"id": "PD3_10", "pair": "metrics", "exp": "query_analytics_warehouse", "query": "Compute the monthly checkout-api p99 latency trend and infrastructure cost attribution across the past six months."},
        {"id": "PD3_11", "pair": "metrics", "exp": "fetch_realtime_metrics", "query": "Check current error-rate spikes on the auth-gateway cluster during the last 2 hours to verify whether the canary is healthy."},
        {"id": "PD3_12", "pair": "metrics", "exp": "query_analytics_warehouse", "query": "Pull the weekly aggregated auth-gateway traffic growth and capacity forecast from January to October 2026."},
        {"id": "PD3_13", "pair": "incident", "exp": "dispatch_urgent_page", "query": "Checkout payments are returning 503 for 60% of live customers right now—escalate immediately to the payments on-call engineer."},
        {"id": "PD3_14", "pair": "incident", "exp": "create_engineering_ticket", "query": "Following yesterday's resolved P0 checkout outage, file a follow-up action item to add automated canary rollback thresholds next sprint."},
        {"id": "PD3_15", "pair": "incident", "exp": "dispatch_urgent_page", "query": "Primary EU login cluster is completely unreachable for active users right now (P0 outage); alert on-call immediately."},
        {"id": "PD3_16", "pair": "incident", "exp": "create_engineering_ticket", "query": "Schedule a P2 hardening task to refactor legacy login retry backoff timers during next Tuesday's maintenance window."},
    ]

    PARAM_SCHEMA = {
        "type": "object",
        "properties": {
            "request_summary": {"type": "string", "description": "Concise query or action payload extracted from the user request."},
        },
        "required": ["request_summary"],
        "additionalProperties": False,
    }

    @classmethod
    def _format_desc(cls, spec: Dict[str, str], cond: str) -> str:
        if cond == "plain_prose":
            return f"{spec['purpose']} {spec['use']} {spec['not_use']} {spec['caveat']}"
        if cond == "bullet_list":
            return (
                f"{spec['purpose']}\n"
                f"- {spec['use']}\n"
                f"- {spec['not_use']}\n"
                f"- {spec['caveat']}"
            )
        # markdown_headers
        return (
            f"### Purpose\n{spec['purpose']}\n\n"
            f"### When to Use\n{spec['use']}\n\n"
            f"### When Not to Use\n{spec['not_use']}\n\n"
            f"### Caveats\n{spec['caveat']}"
        )

    @classmethod
    def _tools(cls, pair_key: str, cond: str, idx: int) -> List[Dict[str, Any]]:
        pair = cls.PAIRS[pair_key]
        # Counterbalance array position 50/50 across prompts
        order = [pair["a"], pair["b"]] if (idx % 2 == 0) else [pair["b"], pair["a"]]
        return [
            {
                "type": "function",
                "function": {
                    "name": spec["name"],
                    "description": cls._format_desc(spec, cond),
                    "strict": True,
                    "parameters": cls.PARAM_SCHEMA,
                },
            }
            for spec in order
        ]

    @classmethod
    def generate_items(cls, cfg: RunConfig) -> List[Dict[str, Any]]:
        tasks = cls.TASKS[: cfg.limit_prompts] if cfg.limit_prompts else cls.TASKS
        items = []
        for it in range(1, cfg.iterations + 1):
            for idx, t in enumerate(tasks):
                for cond in ("plain_prose", "bullet_list", "markdown_headers"):
                    items.append({
                        "hypothesis_id": cls.id,
                        "prompt_id": t["id"],
                        "condition": cond,
                        "iteration": it,
                        "reasoning_effort": cls.EFFORT,
                        "payload": {
                            "model": cfg.model,
                            "messages": [{"role": "user", "content": t["query"]}],
                            "tools": cls._tools(t["pair"], cond, idx),
                            "tool_choice": "auto",
                            "reasoning_effort": cls.EFFORT,
                        },
                        "meta": {"expected_tool": t["exp"], "pair": t["pair"], "order_swapped": (idx % 2 == 1)},
                    })
        return items

    @classmethod
    def evaluate(cls, item: Dict[str, Any], text: str, tool_calls: List[Dict[str, Any]]) -> Dict[str, Any]:
        names = [tc.get("function", {}).get("name") for tc in tool_calls]
        exact = 1.0 if (len(names) == 1 and names[0] == item["meta"]["expected_tool"]) else 0.0
        return {
            "called_tools": names,
            "num_calls": len(names),
            "exact_tool_correct": exact,
            "score": exact,
        }


# ------------------------------------------------------------------------------
# PD-4 (H-06): Arabic Digits vs Spelled-Out Numbers in Exact-Count Constraints
# ------------------------------------------------------------------------------

class PD4_ArabicVsSpelledNumbers:
    id = "PD-4"
    EFFORT = "none"

    NUM_WORDS = {
        3: "three", 4: "four", 5: "five", 6: "six", 7: "seven",
        8: "eight", 9: "nine", 10: "ten", 11: "eleven", 12: "twelve",
    }

    TASKS = [
        {"id": "PD4_01", "topic": "Zero-downtime PostgreSQL schema migrations", "n_bullets": 5, "w_per_bullet": 7, "n_tags": 4},
        {"id": "PD4_02", "topic": "Mitigating Redis cache stampedes under burst load", "n_bullets": 6, "w_per_bullet": 8, "n_tags": 5},
        {"id": "PD4_03", "topic": "Hardening Kubernetes RBAC policies for multi-tenant clusters", "n_bullets": 7, "w_per_bullet": 6, "n_tags": 4},
        {"id": "PD4_04", "topic": "Preventing Kafka consumer lag spikes during rebalances", "n_bullets": 5, "w_per_bullet": 9, "n_tags": 3},
        {"id": "PD4_05", "topic": "Designing idempotent payment webhook handlers", "n_bullets": 6, "w_per_bullet": 7, "n_tags": 5},
        {"id": "PD4_06", "topic": "Detecting silent data drift in feature pipelines", "n_bullets": 8, "w_per_bullet": 6, "n_tags": 4},
        {"id": "PD4_07", "topic": "Automating TLS certificate rotation at edge proxies", "n_bullets": 5, "w_per_bullet": 8, "n_tags": 6},
        {"id": "PD4_08", "topic": "Isolating untrusted PDF inputs from LLM instructions", "n_bullets": 7, "w_per_bullet": 7, "n_tags": 4},
        {"id": "PD4_09", "topic": "Reducing cold-start latency in serverless functions", "n_bullets": 6, "w_per_bullet": 9, "n_tags": 3},
        {"id": "PD4_10", "topic": "Preventing deadlocks in distributed saga workflows", "n_bullets": 8, "w_per_bullet": 7, "n_tags": 5},
        {"id": "PD4_11", "topic": "Auditing S3 bucket permissions across cloud accounts", "n_bullets": 5, "w_per_bullet": 10, "n_tags": 4},
        {"id": "PD4_12", "topic": "Implementing circuit breakers for flaky upstream APIs", "n_bullets": 7, "w_per_bullet": 8, "n_tags": 5},
        {"id": "PD4_13", "topic": "Tuning connection pools behind PgBouncer proxies", "n_bullets": 6, "w_per_bullet": 6, "n_tags": 6},
        {"id": "PD4_14", "topic": "Securing CI/CD secrets in ephemeral build runners", "n_bullets": 8, "w_per_bullet": 8, "n_tags": 4},
        {"id": "PD4_15", "topic": "Tracing tail latency across gRPC service meshes", "n_bullets": 5, "w_per_bullet": 6, "n_tags": 5},
        {"id": "PD4_16", "topic": "Structuring blameless postmortems after regional outages", "n_bullets": 7, "w_per_bullet": 9, "n_tags": 3},
    ]

    @classmethod
    def _build_sys(cls, cond: str, n_bullets: int, w_per_bullet: int, n_tags: int) -> str:
        nb = str(n_bullets) if cond == "arabic_digits" else cls.NUM_WORDS[n_bullets]
        wb = str(w_per_bullet) if cond == "arabic_digits" else cls.NUM_WORDS[w_per_bullet]
        nt = str(n_tags) if cond == "arabic_digits" else cls.NUM_WORDS[n_tags]
        return (
            "Write a concise technical checklist on the given topic following every formatting rule strictly:\n"
            f"1. Emit exactly {nb} bullet lines, each starting with '- '.\n"
            f"2. Each bullet line must contain strictly {wb} whitespace-separated words (not counting the leading '-').\n"
            f"3. End with one final line formatted as 'TAGS: <tags>' containing strictly {nt} single-word comma-separated tags (e.g., 'TAGS: alpha, beta, gamma').\n"
            "4. Output only the bullet lines and the TAGS line with no headers, intro, or extra lines."
        )

    @classmethod
    def generate_items(cls, cfg: RunConfig) -> List[Dict[str, Any]]:
        tasks = cls.TASKS[: cfg.limit_prompts] if cfg.limit_prompts else cls.TASKS
        items = []
        for it in range(1, cfg.iterations + 1):
            for t in tasks:
                for cond in ("arabic_digits", "spelled_words"):
                    items.append({
                        "hypothesis_id": cls.id,
                        "prompt_id": t["id"],
                        "condition": cond,
                        "iteration": it,
                        "reasoning_effort": cls.EFFORT,
                        "payload": {
                            "model": cfg.model,
                            "messages": [
                                {"role": "system", "content": cls._build_sys(cond, t["n_bullets"], t["w_per_bullet"], t["n_tags"])},
                                {"role": "user", "content": f"Topic: {t['topic']}"},
                            ],
                            "reasoning_effort": cls.EFFORT,
                        },
                        "meta": {"n_bullets": t["n_bullets"], "w_per_bullet": t["w_per_bullet"], "n_tags": t["n_tags"]},
                    })
        return items

    @classmethod
    def evaluate(cls, item: Dict[str, Any], text: str, tool_calls: List[Dict[str, Any]]) -> Dict[str, Any]:
        lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
        bullets = [ln for ln in lines if ln.startswith("- ")]
        tags_lines = [ln for ln in lines if ln.startswith("TAGS:")]
        nb_exp = item["meta"]["n_bullets"]
        wb_exp = item["meta"]["w_per_bullet"]
        nt_exp = item["meta"]["n_tags"]

        c1_bullets = 1.0 if len(bullets) == nb_exp else 0.0
        exact_word_bullets = sum(1 for b in bullets if len(b[2:].strip().split()) == wb_exp)
        bullet_word_frac = (exact_word_bullets / len(bullets)) if bullets else 0.0
        c2_words_all = 1.0 if (bullets and exact_word_bullets == len(bullets) and len(bullets) == nb_exp) else 0.0

        c3_tags = 0.0
        if tags_lines and lines[-1].startswith("TAGS:"):
            raw_tags = [tg.strip() for tg in lines[-1][len("TAGS:"):].split(",") if tg.strip()]
            if len(raw_tags) == nt_exp and all(len(tg.split()) == 1 for tg in raw_tags):
                c3_tags = 1.0

        no_extra = 1.0 if len(lines) == (len(bullets) + len(tags_lines)) and len(tags_lines) == 1 else 0.0
        score = (c1_bullets + bullet_word_frac + c3_tags) / 3.0
        strict_all = 1.0 if (c1_bullets == 1.0 and c2_words_all == 1.0 and c3_tags == 1.0 and no_extra == 1.0) else 0.0
        return {
            "bullet_count": len(bullets),
            "c1_bullets": c1_bullets,
            "bullet_word_frac": round(bullet_word_frac, 4),
            "c2_words_all": c2_words_all,
            "c3_tags": c3_tags,
            "no_extra_lines": no_extra,
            "strict_all": strict_all,
            "score": round(score, 4),
        }


# ------------------------------------------------------------------------------
# PD-5 (H-07): Prompt-Injected JSON Schema vs TypeScript Interface Signatures
# ------------------------------------------------------------------------------

class PD5_JsonSchemaVsTypeScript:
    id = "PD-5"
    EFFORT = "none"

    JSON_SCHEMA_SPEC = json.dumps({
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "IncidentDeploymentManifest",
        "type": "object",
        "additionalProperties": False,
        "required": ["incident_id", "severity", "rollback_required", "affected_services", "remediation_steps", "approvals"],
        "properties": {
            "incident_id": {"type": "string", "pattern": "^INC-[0-9]{4}$", "description": "Incident identifier matching INC-XXXX."},
            "severity": {"type": "string", "enum": ["SEV1", "SEV2", "SEV3"], "description": "Incident severity level."},
            "rollback_required": {"type": "boolean", "description": "Whether an immediate deployment rollback is required."},
            "affected_services": {
                "type": "array",
                "minItems": 2,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["service_name", "region", "replicas", "error_rate_pct", "owner_note"],
                    "properties": {
                        "service_name": {"type": "string", "description": "Lowercase hyphenated service name."},
                        "region": {"type": "string", "enum": ["us-east", "us-west", "eu-central", "ap-south"]},
                        "replicas": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["desired", "healthy"],
                            "properties": {
                                "desired": {"type": "integer", "minimum": 1},
                                "healthy": {"type": "integer", "minimum": 0},
                            },
                        },
                        "error_rate_pct": {"type": "number", "minimum": 0, "maximum": 100},
                        "owner_note": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "Explicit owner note if given, otherwise null."},
                    },
                },
            },
            "remediation_steps": {
                "type": "array",
                "minItems": 2,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["step_order", "action_type", "target_service", "timeout_seconds"],
                    "properties": {
                        "step_order": {"type": "integer", "minimum": 1},
                        "action_type": {"type": "string", "enum": ["drain", "rollback", "scale", "patch"]},
                        "target_service": {"type": "string"},
                        "timeout_seconds": {"type": "integer", "minimum": 10},
                    },
                },
            },
            "approvals": {
                "type": "object",
                "additionalProperties": False,
                "required": ["primary_approver", "secondary_approver"],
                "properties": {
                    "primary_approver": {"type": "string"},
                    "secondary_approver": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "Secondary approver name if mentioned, otherwise null."},
                },
            },
        },
    }, indent=2)

    TS_INTERFACE_SPEC = """interface ReplicaState {
  desired: number; // integer >= 1
  healthy: number; // integer >= 0
}

interface AffectedService {
  service_name: string; // lowercase hyphenated service name
  region: "us-east" | "us-west" | "eu-central" | "ap-south";
  replicas: ReplicaState;
  error_rate_pct: number; // 0 to 100
  owner_note: string | null; // explicit owner note if given, otherwise null
}

interface RemediationStep {
  step_order: number; // integer >= 1
  action_type: "drain" | "rollback" | "scale" | "patch";
  target_service: string;
  timeout_seconds: number; // integer >= 10
}

interface Approvals {
  primary_approver: string;
  secondary_approver: string | null; // secondary approver name if mentioned, otherwise null
}

// Strict object contract: no extra/undeclared keys at any nesting level.
interface IncidentDeploymentManifest {
  incident_id: string; // matches ^INC-[0-9]{4}$
  severity: "SEV1" | "SEV2" | "SEV3";
  rollback_required: boolean; // whether an immediate deployment rollback is required
  affected_services: AffectedService[]; // min 2 items
  remediation_steps: RemediationStep[]; // min 2 items
  approvals: Approvals;
}"""

    TASKS = [
        {"id": "PD5_01", "inc": "INC-4101", "sev": "SEV1", "rb": True, "svcs": [("checkout-api", "us-east", 12, 4, 18.5, "db pool saturated"), ("payment-worker", "us-east", 8, 5, 9.2, None)], "steps": [(1, "drain", "checkout-api", 60), (2, "rollback", "checkout-api", 180)], "app": ("Maya Lin", "Owen Brooks"), "text": "Incident INC-4101 (SEV1) requires an immediate rollback. Two services in us-east are affected: checkout-api has 4 healthy of 12 desired replicas with 18.5% error rate (owner note: db pool saturated), and payment-worker has 5 healthy of 8 desired replicas with 9.2% error rate (no owner note). Remediation: step 1 drain checkout-api (60s timeout), step 2 rollback checkout-api (180s timeout). Primary approver: Maya Lin; secondary approver: Owen Brooks."},
        {"id": "PD5_02", "inc": "INC-4102", "sev": "SEV2", "rb": False, "svcs": [("search-indexer", "eu-central", 6, 4, 4.1, None), ("query-router", "eu-central", 10, 9, 1.8, "elevated retries")], "steps": [(1, "scale", "search-indexer", 120), (2, "patch", "query-router", 240)], "app": ("Elena Novak", None), "text": "Incident INC-4102 (SEV2) does NOT require a rollback. Affected in eu-central: search-indexer (6 desired, 4 healthy, 4.1% error rate, no owner note) and query-router (10 desired, 9 healthy, 1.8% error rate, owner note: elevated retries). Steps: 1) scale search-indexer timeout 120s; 2) patch query-router timeout 240s. Approved by primary Elena Novak with no secondary approver."},
        {"id": "PD5_03", "inc": "INC-4103", "sev": "SEV1", "rb": True, "svcs": [("auth-gateway", "us-west", 16, 2, 42.0, "jwt key mismatch"), ("session-store", "us-west", 12, 10, 3.5, None)], "steps": [(1, "rollback", "auth-gateway", 90), (2, "drain", "session-store", 45)], "app": ("Devon Patel", "Nadia Chen"), "text": "INC-4103 is SEV1 and requires rollback immediately. In us-west, auth-gateway sits at 2/16 healthy replicas and 42.0% error rate (owner note: jwt key mismatch), while session-store is at 10/12 healthy replicas with 3.5% error rate and no owner note. Execute step 1 rollback on auth-gateway (90s), then step 2 drain on session-store (45s). Approvers: Devon Patel (primary) and Nadia Chen (secondary)."},
        {"id": "PD5_04", "inc": "INC-4104", "sev": "SEV3", "rb": False, "svcs": [("email-notifier", "ap-south", 4, 3, 2.4, "smtp throttle"), ("digest-cron", "ap-south", 2, 2, 0.5, None)], "steps": [(1, "patch", "email-notifier", 300), (2, "scale", "digest-cron", 150)], "app": ("Ravi Kumar", None), "text": "Low-urgency SEV3 INC-4104 (rollback not required). Region ap-south services: email-notifier (4 desired, 3 healthy, 2.4% errors, owner note: smtp throttle) and digest-cron (2 desired, 2 healthy, 0.5% errors, no owner note). Remediation: step 1 patch email-notifier (300s), step 2 scale digest-cron (150s). Primary approver Ravi Kumar; no secondary approver."},
        {"id": "PD5_05", "inc": "INC-4105", "sev": "SEV1", "rb": True, "svcs": [("ledger-writer", "us-east", 9, 3, 27.3, None), ("ledger-reader", "eu-central", 9, 6, 11.0, "replica lag")], "steps": [(1, "drain", "ledger-writer", 30), (2, "rollback", "ledger-writer", 120), (3, "scale", "ledger-reader", 90)], "app": ("Hannah Kim", "Lucas Meyer"), "text": "SEV1 incident INC-4105 requires rollback. Impacted services: ledger-writer in us-east (9 desired, 3 healthy, 27.3% error rate, no owner note) and ledger-reader in eu-central (9 desired, 6 healthy, 11.0% error rate, owner note: replica lag). Three remediation steps: 1) drain ledger-writer (30s), 2) rollback ledger-writer (120s), 3) scale ledger-reader (90s). Approvers: Hannah Kim primary, Lucas Meyer secondary."},
        {"id": "PD5_06", "inc": "INC-4106", "sev": "SEV2", "rb": False, "svcs": [("media-transcoder", "us-west", 20, 14, 6.7, "gpu oom"), ("cdn-origin", "us-west", 8, 8, 0.9, None)], "steps": [(1, "scale", "media-transcoder", 180), (2, "patch", "media-transcoder", 240)], "app": ("Sofia Alvarez", None), "text": "INC-4106 is SEV2 with rollback_required false. In us-west: media-transcoder has 14 healthy out of 20 desired replicas with 6.7% errors (owner note: gpu oom); cdn-origin has 8 healthy of 8 desired with 0.9% errors (no note). Steps: step 1 scale media-transcoder (180s), step 2 patch media-transcoder (240s). Primary approver Sofia Alvarez; secondary approver not needed."},
        {"id": "PD5_07", "inc": "INC-4107", "sev": "SEV2", "rb": True, "svcs": [("webhook-ingress", "eu-central", 10, 6, 14.2, None), ("event-bus", "eu-central", 6, 5, 2.0, "backpressure")], "steps": [(1, "rollback", "webhook-ingress", 120), (2, "drain", "event-bus", 60)], "app": ("Liam O'Connor", "Priya Nair"), "text": "Incident INC-4107 (SEV2) requires rollback. Services in eu-central: webhook-ingress (10 desired, 6 healthy, 14.2% error rate, no owner note) and event-bus (6 desired, 5 healthy, 2.0% error rate, owner note: backpressure). Plan: step 1 rollback webhook-ingress (120s), step 2 drain event-bus (60s). Primary approver Liam O'Connor, secondary Priya Nair."},
        {"id": "PD5_08", "inc": "INC-4108", "sev": "SEV3", "rb": False, "svcs": [("report-export", "us-east", 5, 4, 3.1, None), ("pdf-renderer", "us-east", 5, 3, 5.5, "font cache")], "steps": [(1, "patch", "pdf-renderer", 120), (2, "scale", "report-export", 90)], "app": ("Grace Wu", None), "text": "SEV3 incident INC-4108 needs no rollback. Region us-east: report-export (5 desired, 4 healthy, 3.1% errors, no note) and pdf-renderer (5 desired, 3 healthy, 5.5% errors, owner note: font cache). Remediation: 1) patch pdf-renderer (120s), 2) scale report-export (90s). Approved by Grace Wu (primary) only."},
        {"id": "PD5_09", "inc": "INC-4109", "sev": "SEV1", "rb": True, "svcs": [("billing-sync", "ap-south", 6, 1, 55.4, "deadlock loop"), ("invoice-api", "ap-south", 8, 4, 21.8, None)], "steps": [(1, "drain", "billing-sync", 45), (2, "rollback", "billing-sync", 150)], "app": ("Tariq Hassan", "Claire Martin"), "text": "Urgent SEV1 INC-4109 requires rollback. In ap-south, billing-sync has 1/6 healthy replicas and 55.4% error rate (owner note: deadlock loop); invoice-api has 4/8 healthy replicas and 21.8% error rate (no note). Steps: step 1 drain billing-sync (45s), step 2 rollback billing-sync (150s). Primary approver Tariq Hassan; secondary Claire Martin."},
        {"id": "PD5_10", "inc": "INC-4110", "sev": "SEV2", "rb": False, "svcs": [("geo-router", "us-east", 12, 10, 3.8, None), ("dns-sync", "us-west", 4, 3, 7.2, "stale ttl")], "steps": [(1, "patch", "dns-sync", 60), (2, "scale", "geo-router", 120)], "app": ("Noah Rossi", None), "text": "INC-4110 (SEV2), no rollback required. Affected: geo-router in us-east (12 desired, 10 healthy, 3.8% errors, no owner note) and dns-sync in us-west (4 desired, 3 healthy, 7.2% errors, owner note: stale ttl). Remediation: step 1 patch dns-sync (60s), step 2 scale geo-router (120s). Primary approver Noah Rossi; no secondary approver."},
        {"id": "PD5_11", "inc": "INC-4111", "sev": "SEV1", "rb": True, "svcs": [("order-matcher", "eu-central", 14, 5, 31.6, "memory leak"), ("risk-engine", "eu-central", 10, 7, 12.4, None)], "steps": [(1, "drain", "order-matcher", 30), (2, "rollback", "order-matcher", 120), (3, "scale", "risk-engine", 180)], "app": ("Amara Okafor", "Victor Silva"), "text": "SEV1 INC-4111 requires immediate rollback. In eu-central: order-matcher (14 desired, 5 healthy, 31.6% error rate, owner note: memory leak) and risk-engine (10 desired, 7 healthy, 12.4% error rate, no owner note). Steps: 1) drain order-matcher (30s), 2) rollback order-matcher (120s), 3) scale risk-engine (180s). Approvers: Amara Okafor primary, Victor Silva secondary."},
        {"id": "PD5_12", "inc": "INC-4112", "sev": "SEV3", "rb": False, "svcs": [("audit-collector", "us-west", 4, 4, 1.2, None), ("log-shipper", "us-west", 6, 5, 2.9, "disk full")], "steps": [(1, "scale", "log-shipper", 90), (2, "patch", "audit-collector", 180)], "app": ("Chloe Bennett", None), "text": "Incident INC-4112 (SEV3, rollback not required). In us-west: audit-collector (4 desired, 4 healthy, 1.2% errors, no note) and log-shipper (6 desired, 5 healthy, 2.9% errors, owner note: disk full). Steps: step 1 scale log-shipper (90s), step 2 patch audit-collector (180s). Primary approver Chloe Bennett, secondary null."},
        {"id": "PD5_13", "inc": "INC-4113", "sev": "SEV2", "rb": True, "svcs": [("feature-flags", "ap-south", 8, 5, 16.0, "bad rollout"), ("edge-cache", "ap-south", 12, 11, 1.4, None)], "steps": [(1, "rollback", "feature-flags", 75), (2, "drain", "edge-cache", 60)], "app": ("Kenji Sato", "Zoe Adams"), "text": "INC-4113 is SEV2 and requires a rollback. Region ap-south: feature-flags (8 desired, 5 healthy, 16.0% error rate, owner note: bad rollout) and edge-cache (12 desired, 11 healthy, 1.4% error rate, no owner note). Plan: step 1 rollback feature-flags (75s), step 2 drain edge-cache (60s). Approvers: Kenji Sato primary and Zoe Adams secondary."},
        {"id": "PD5_14", "inc": "INC-4114", "sev": "SEV2", "rb": False, "svcs": [("ml-scorer", "us-east", 16, 12, 8.3, "batch timeout"), ("feature-store", "us-east", 12, 11, 1.9, None)], "steps": [(1, "scale", "ml-scorer", 200), (2, "patch", "feature-store", 150)], "app": ("Marcus Reid", None), "text": "SEV2 INC-4114 (no rollback required). In us-east: ml-scorer has 12/16 healthy replicas and 8.3% errors (owner note: batch timeout); feature-store has 11/12 healthy and 1.9% errors (no note). Steps: 1) scale ml-scorer (200s), 2) patch feature-store (150s). Primary approver Marcus Reid; no secondary approver."},
        {"id": "PD5_15", "inc": "INC-4115", "sev": "SEV1", "rb": True, "svcs": [("token-issuer", "us-west", 10, 3, 47.5, None), ("sso-broker", "eu-central", 8, 4, 29.0, "cert mismatch")], "steps": [(1, "rollback", "token-issuer", 90), (2, "patch", "sso-broker", 120)], "app": ("Ananya Rao", "Daniel Park"), "text": "Critical SEV1 INC-4115 requires rollback. Services: token-issuer in us-west (10 desired, 3 healthy, 47.5% error rate, no owner note) and sso-broker in eu-central (8 desired, 4 healthy, 29.0% error rate, owner note: cert mismatch). Steps: step 1 rollback token-issuer (90s), step 2 patch sso-broker (120s). Primary approver Ananya Rao; secondary Daniel Park."},
        {"id": "PD5_16", "inc": "INC-4116", "sev": "SEV3", "rb": False, "svcs": [("telemetry-ingest", "eu-central", 6, 5, 2.2, None), ("alert-router", "eu-central", 4, 4, 0.8, "queue delay")], "steps": [(1, "patch", "alert-router", 120), (2, "scale", "telemetry-ingest", 180)], "app": ("Freya Lind", None), "text": "SEV3 incident INC-4116 needs no rollback. Region eu-central: telemetry-ingest (6 desired, 5 healthy, 2.2% errors, no note) and alert-router (4 desired, 4 healthy, 0.8% errors, owner note: queue delay). Remediation: step 1 patch alert-router (120s), step 2 scale telemetry-ingest (180s). Primary approver Freya Lind only."},
    ]

    @classmethod
    def _build_sys(cls, cond: str) -> str:
        spec = cls.JSON_SCHEMA_SPEC if cond == "json_schema" else cls.TS_INTERFACE_SPEC
        label = "JSON Schema" if cond == "json_schema" else "TypeScript interfaces"
        return (
            f"Extract the incident deployment manifest from the user text as a single raw JSON object "
            f"strictly conforming to the {label} below. Do not include Markdown fences, comments, or prose outside the JSON.\n\n"
            f"{spec}"
        )

    @classmethod
    def generate_items(cls, cfg: RunConfig) -> List[Dict[str, Any]]:
        tasks = cls.TASKS[: cfg.limit_prompts] if cfg.limit_prompts else cls.TASKS
        items = []
        for it in range(1, cfg.iterations + 1):
            for t in tasks:
                for cond in ("json_schema", "typescript_interface"):
                    items.append({
                        "hypothesis_id": cls.id,
                        "prompt_id": t["id"],
                        "condition": cond,
                        "iteration": it,
                        "reasoning_effort": cls.EFFORT,
                        "payload": {
                            "model": cfg.model,
                            "messages": [
                                {"role": "system", "content": cls._build_sys(cond)},
                                {"role": "user", "content": t["text"]},
                            ],
                            "reasoning_effort": cls.EFFORT,
                        },
                        "meta": {
                            "inc": t["inc"],
                            "sev": t["sev"],
                            "rb": t["rb"],
                            "svcs": t["svcs"],
                            "steps": t["steps"],
                            "app": list(t["app"]),
                        },
                    })
        return items

    @staticmethod
    def _is_int(v: Any) -> bool:
        return isinstance(v, int) and not isinstance(v, bool)

    @staticmethod
    def _is_num(v: Any) -> bool:
        return isinstance(v, (int, float)) and not isinstance(v, bool)

    @classmethod
    def evaluate(cls, item: Dict[str, Any], text: str, tool_calls: List[Dict[str, Any]]) -> Dict[str, Any]:
        s = (text or "").strip()
        raw_no_fence = 1.0 if "```" not in s else 0.0
        obj = None
        try:
            cand = json.loads(s)
            if isinstance(cand, dict):
                obj = cand
        except Exception:
            pass
        if obj is None:
            return {"raw_no_fence": raw_no_fence, "json_ok": 0.0, "schema_valid": 0.0, "factual_exact": 0.0, "score": 0.0}

        # Strict schema validation across all 4 nesting levels
        top_keys = {"incident_id", "severity", "rollback_required", "affected_services", "remediation_steps", "approvals"}
        svc_keys = {"service_name", "region", "replicas", "error_rate_pct", "owner_note"}
        rep_keys = {"desired", "healthy"}
        step_keys = {"step_order", "action_type", "target_service", "timeout_seconds"}
        app_keys = {"primary_approver", "secondary_approver"}

        schema_ok = True
        if set(obj.keys()) != top_keys:
            schema_ok = False
        if not (isinstance(obj.get("incident_id"), str) and re.fullmatch(r"INC-\d{4}", obj["incident_id"])):
            schema_ok = False
        if obj.get("severity") not in ("SEV1", "SEV2", "SEV3"):
            schema_ok = False
        if not isinstance(obj.get("rollback_required"), bool):
            schema_ok = False

        svcs = obj.get("affected_services")
        if not isinstance(svcs, list) or len(svcs) < 2:
            schema_ok = False
        else:
            for sv in svcs:
                if not isinstance(sv, dict) or set(sv.keys()) != svc_keys:
                    schema_ok = False
                    break
                rep = sv.get("replicas")
                if not isinstance(rep, dict) or set(rep.keys()) != rep_keys or not (cls._is_int(rep.get("desired")) and rep["desired"] >= 1 and cls._is_int(rep.get("healthy")) and rep["healthy"] >= 0):
                    schema_ok = False
                    break
                if not isinstance(sv.get("service_name"), str) or sv.get("region") not in ("us-east", "us-west", "eu-central", "ap-south"):
                    schema_ok = False
                    break
                if not (cls._is_num(sv.get("error_rate_pct")) and 0 <= sv["error_rate_pct"] <= 100):
                    schema_ok = False
                    break
                if sv.get("owner_note") is not None and not isinstance(sv.get("owner_note"), str):
                    schema_ok = False
                    break

        steps = obj.get("remediation_steps")
        if not isinstance(steps, list) or len(steps) < 2:
            schema_ok = False
        else:
            for st in steps:
                if not isinstance(st, dict) or set(st.keys()) != step_keys:
                    schema_ok = False
                    break
                if not (cls._is_int(st.get("step_order")) and st["step_order"] >= 1):
                    schema_ok = False
                    break
                if st.get("action_type") not in ("drain", "rollback", "scale", "patch") or not isinstance(st.get("target_service"), str):
                    schema_ok = False
                    break
                if not (cls._is_int(st.get("timeout_seconds")) and st["timeout_seconds"] >= 10):
                    schema_ok = False
                    break

        app = obj.get("approvals")
        if not isinstance(app, dict) or set(app.keys()) != app_keys:
            schema_ok = False
        elif not isinstance(app.get("primary_approver"), str) or (app.get("secondary_approver") is not None and not isinstance(app.get("secondary_approver"), str)):
            schema_ok = False

        # Factual extraction accuracy check
        meta = item["meta"]
        fact_ok = False
        if schema_ok:
            sv_ok = len(svcs) == len(meta["svcs"]) and all(
                sv["service_name"] == exp[0]
                and sv["region"] == exp[1]
                and sv["replicas"]["desired"] == exp[2]
                and sv["replicas"]["healthy"] == exp[3]
                and abs(float(sv["error_rate_pct"]) - float(exp[4])) < 1e-3
                and ((exp[5] is None and sv["owner_note"] is None) or (exp[5] is not None and sv["owner_note"] is not None and exp[5].lower() in sv["owner_note"].lower()))
                for sv, exp in zip(svcs, meta["svcs"])
            )
            st_ok = len(steps) == len(meta["steps"]) and all(
                st["step_order"] == exp[0]
                and st["action_type"] == exp[1]
                and st["target_service"] == exp[2]
                and st["timeout_seconds"] == exp[3]
                for st, exp in zip(steps, meta["steps"])
            )
            ap_ok = (
                app["primary_approver"] == meta["app"][0]
                and app["secondary_approver"] == meta["app"][1]
            )
            fact_ok = (
                obj["incident_id"] == meta["inc"]
                and obj["severity"] == meta["sev"]
                and obj["rollback_required"] is meta["rb"]
                and sv_ok
                and st_ok
                and ap_ok
            )

        passed = 1.0 if (raw_no_fence == 1.0 and schema_ok and fact_ok) else 0.0
        return {
            "raw_no_fence": raw_no_fence,
            "json_ok": 1.0,
            "schema_valid": 1.0 if schema_ok else 0.0,
            "factual_exact": 1.0 if fact_ok else 0.0,
            "score": passed,
        }


SUITES = {
    "PD-1": PD1_TS2Replication,
    "PD-2": PD2_ParamVerbosityCeiling,
    "PD-3": PD3_MarkdownInToolDescriptions,
    "PD-4": PD4_ArabicVsSpelledNumbers,
    "PD-5": PD5_JsonSchemaVsTypeScript,
}


def run_suite(cfg: RunConfig, suite_cls: Any, out_dir: Path, run_id: str) -> Tuple[int, int]:
    items = suite_cls.generate_items(cfg)
    out_path = out_dir / f"results_{suite_cls.id}.jsonl"
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
    print(f"[{suite_cls.id}] completed {len(records)} records (errors={errs}) [{cond_summary}] -> {out_path}")
    return len(records), errs


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute Phase D experiments (H-02, H-03, H-06, H-07) against gateway model.")
    parser.add_argument("--suites", nargs="+", default=list(SUITES.keys()), choices=list(SUITES.keys()))
    parser.add_argument("--iterations", type=int, default=DEFAULT_ITERATIONS)
    parser.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--limit-prompts", type=int, default=None, help="Optional cap on prompts per suite (for smoke calibration).")
    parser.add_argument("--out-dir", default=None, help="Optional output directory (defaults to evidence/raw_phase_d).")
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
        limit_prompts=args.limit_prompts,
    )
    out_dir = Path(args.out_dir).resolve() if args.out_dir else (Path(__file__).resolve().parent / "raw_phase_d")
    out_dir.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_phase_d")

    tot_n, tot_e = 0, 0
    for sid in args.suites:
        n, e = run_suite(cfg, SUITES[sid], out_dir, run_id)
        tot_n += n
        tot_e += e
    print(f"Phase D total: {tot_n} records, {tot_e} errors.")
    return 0 if tot_e == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
