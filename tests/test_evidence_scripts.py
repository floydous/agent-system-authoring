"""Unit tests for offline statistical and evaluation utilities in evidence/."""

from __future__ import annotations

import json
import math
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_ROOT = REPO_ROOT / "skills" / "agent-system-authoring"
sys.path.insert(0, str(REPO_ROOT / "evidence"))

import phase_d_harness as pd  # noqa: E402
import phase_e_harness as pe  # noqa: E402
import phase_f_harness as pf  # noqa: E402
import phase_h08_harness as ph08  # noqa: E402
import recompute_stats as rs  # noqa: E402
import run_evals as reval  # noqa: E402


class TestRecomputeStats(unittest.TestCase):
    def test_student_t_two_sided_p_known_quantiles(self) -> None:
        self.assertAlmostEqual(rs.student_t_two_sided_p(1.0, 1), 0.5, places=7)
        self.assertAlmostEqual(rs.student_t_two_sided_p(2.570581836, 5), 0.05, places=7)
        self.assertAlmostEqual(rs.student_t_two_sided_p(2.131449546, 15), 0.05, places=7)
        self.assertAlmostEqual(rs.student_t_two_sided_p(4.072765, 15), 0.001, places=6)

    def test_sign_test_two_sided_exact(self) -> None:
        pos, neg, p = rs.sign_test_two_sided([1.0] * 16)
        self.assertEqual((pos, neg), (16, 0))
        self.assertAlmostEqual(p, 2.0 / (2 ** 16), places=10)

        pos0, neg0, p0 = rs.sign_test_two_sided([0.0, 0.0, 0.0])
        self.assertEqual((pos0, neg0), (0, 0))
        self.assertEqual(p0, 1.0)

    def test_paired_t_test_constant_nonzero_diff(self) -> None:
        t_val, p_val, mean_d, sd_d = rs.paired_t_test([1.0, 1.0, 1.0, 1.0])
        self.assertIsNone(t_val)
        self.assertIsNone(p_val)
        self.assertEqual(mean_d, 1.0)
        self.assertEqual(sd_d, 0.0)


class TestRunEvalsHelpers(unittest.TestCase):
    def test_build_progressive_context_selects_zero_reasoning_template(self) -> None:
        _, _, body = reval.extract_skill_metadata_and_body(SKILL_ROOT / "SKILL.md")
        ctx_default = reval.build_progressive_context(SKILL_ROOT, body, "tool", eval_id="comp_05_disambiguate_two_support_tools")
        self.assertIn("### Loaded Template: assets/templates/tool_schema_template.json", ctx_default)
        self.assertNotIn("### Loaded Template: assets/templates/tool_schema_zero_reasoning_template.json", ctx_default)

        ctx_zero = reval.build_progressive_context(SKILL_ROOT, body, "tool", eval_id="comp_07_non_reasoning_refund_tool")
        self.assertIn("### Loaded Template: assets/templates/tool_schema_zero_reasoning_template.json", ctx_zero)
        self.assertNotIn("### Loaded Template: assets/templates/tool_schema_template.json", ctx_zero)

    def test_resolve_model_label_respects_aliases_and_other_models(self) -> None:
        self.assertEqual(reval.resolve_model_label([{"model": "cx/gpt-6-luna"}]), "GPT 6 Luna")
        self.assertEqual(reval.resolve_model_label([{"model": "claude-opus-5.5"}]), "claude-opus-5.5")
        self.assertEqual(reval.resolve_model_label([{"model": "cx/gpt-6-luna"}], "gemini-4-hydrogen"), "gemini-4-hydrogen")

    def test_tools_strict_ok_checks_wire_and_required_keys(self) -> None:
        valid_tool = json.loads((SKILL_ROOT / "assets/templates/tool_schema_template.json").read_text(encoding="utf-8"))
        tools, native = reval.normalize_openai_tools(json.dumps(valid_tool))
        self.assertTrue(native)
        self.assertTrue(reval._tools_strict_ok(tools, native))

        # Missing required key should fail strict_ok
        broken = json.loads(json.dumps(valid_tool))
        broken["function"]["parameters"]["required"] = ["query"]
        tools_b, native_b = reval.normalize_openai_tools(json.dumps(broken))
        self.assertTrue(native_b)
        self.assertFalse(reval._tools_strict_ok(tools_b, native_b))

    def test_comp_07_probe_math_consistency(self) -> None:
        # Verify the updated comp_07 probe arithmetic: [2026-03-01, 2026-04-01) = 31 days;
        # [2026-03-14, 2026-04-01) = 18 unused days; 15500 * 18 / 31 = 9000; 9000 - 675 = 8325
        from datetime import date

        cycle_days = (date(2026, 4, 1) - date(2026, 3, 1)).days
        unused_days = (date(2026, 4, 1) - date(2026, 3, 14)).days
        self.assertEqual(cycle_days, 31)
        self.assertEqual(unused_days, 18)
        gross = 15500 * unused_days / cycle_days
        self.assertTrue(math.isclose(gross, 9000.0))
        self.assertEqual(int(gross) - 675, 8325)


class TestPhaseDIntegrity(unittest.TestCase):
    def test_phase_d_raw_traces_reevaluate_cleanly_with_zero_errors(self) -> None:
        raw_d = REPO_ROOT / "evidence" / "raw_phase_d"
        grouped = rs.load_records(raw_d, "results_PD-*.jsonl")
        self.assertEqual(sorted(grouped.keys()), ["PD-1", "PD-2", "PD-3", "PD-4", "PD-5"])
        total = sum(len(v) for v in grouped.values())
        self.assertEqual(total, 1030)
        for sid, recs in grouped.items():
            self.assertIn(sid, rs.PHASE_D_BASELINES)
            suite_cls = pd.SUITES[sid]
            for r in recs:
                self.assertIsNone(r.get("error"))
                re_metrics = suite_cls.evaluate({"meta": r["meta"]}, r["response_text"], r.get("tool_calls", []))
                self.assertEqual(re_metrics, r["metrics"], msg=f"Mismatch on {sid} {r['prompt_id']} {r['condition']} it={r['iteration']}")


class TestPhaseEAndH08Integrity(unittest.TestCase):
    def test_phase_e_raw_traces_reevaluate_cleanly_with_zero_errors(self) -> None:
        raw_e = REPO_ROOT / "evidence" / "raw_phase_e"
        grouped = rs.load_records(raw_e, "results_PE-*.jsonl")
        self.assertEqual(sorted(grouped.keys()), ["PE-1", "PE-2", "PE-3", "PE-4"])
        self.assertEqual(sum(len(v) for v in grouped.values()), 880)
        for sid, recs in grouped.items():
            self.assertIn(sid, rs.PHASE_E_BASELINES)
            suite_cls = pe.SUITES[sid]
            for r in recs:
                self.assertIsNone(r.get("error"))
                re_metrics = suite_cls.evaluate({"meta": r["meta"]}, r["response_text"], r.get("tool_calls", []))
                self.assertEqual(re_metrics, r["metrics"], msg=f"Mismatch on {sid} {r['prompt_id']} {r['condition']} it={r['iteration']}")

    def test_h08_raw_traces_reevaluate_cleanly_with_zero_errors(self) -> None:
        raw_h08 = REPO_ROOT / "evidence" / "raw_h08_particle1"
        grouped = rs.load_records(raw_h08, "results_H08-*.jsonl")
        self.assertEqual(sorted(grouped.keys()), ["H08-PC1", "H08-PC2", "H08-PD1", "H08-PD4", "H08-PD5"])
        self.assertEqual(sum(len(v) for v in grouped.values()), 950)
        for sid, recs in grouped.items():
            self.assertIn(sid, rs.H08_BASELINES)
            suite_cls = ph08.REPLICATION_SUITES[sid]
            for r in recs:
                self.assertIsNone(r.get("error"))
                re_metrics = suite_cls.evaluate({"meta": r["meta"]}, r["response_text"], r.get("tool_calls", []))
                self.assertEqual(re_metrics, r["metrics"], msg=f"Mismatch on {sid} {r['prompt_id']} {r['condition']} it={r['iteration']}")

    def test_pe1_fifty_rules_are_mutually_satisfiable(self) -> None:
        self.assertEqual(len(pe.PE1_RuleDensityScaling.RULES), 50)
        pe1_path = REPO_ROOT / "evidence" / "raw_phase_e" / "results_PE-1.jsonl"
        recs = [json.loads(ln) for ln in pe1_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
        r50 = [r for r in recs if r["condition"] == "rules_50"]
        perfect_50 = [
            r
            for r in r50
            if pe.PE1_RuleDensityScaling.evaluate({"meta": {"k": 50}}, r["response_text"], [])["strict_all"] == 1.0
        ]
        self.assertEqual(len(r50), 80)
        self.assertGreater(len(perfect_50), 0)
        witness = pe.PE1_RuleDensityScaling.evaluate({"meta": {"k": 50}}, perfect_50[0]["response_text"], [])
        self.assertEqual(witness["passed_active"], 50)
        self.assertEqual(witness["failed_rules"], [])
        self.assertEqual(witness["score"], 1.0)


class TestPhaseFNemoIntegrity(unittest.TestCase):
    def test_phase_f_nemo_raw_traces_reevaluate_cleanly_with_zero_errors(self) -> None:
        raw_nemo = REPO_ROOT / "evidence" / "raw_phase_f_nemo"
        grouped = rs.load_records(raw_nemo, "results_NEMO-*.jsonl")
        self.assertEqual(
            sorted(grouped.keys()),
            ["NEMO-PB6", "NEMO-PC1", "NEMO-PC2", "NEMO-PD1", "NEMO-PD4", "NEMO-PE2"],
        )
        self.assertEqual(sum(len(v) for v in grouped.values()), 1190)
        for hyp_id, recs in grouped.items():
            self.assertIn(hyp_id, rs.PHASE_F_NEMO_BASELINES)
            suite_key = hyp_id.split("-")[1]
            suite_cls = pf.SUITE_SPECS[suite_key][0]
            for r in recs:
                self.assertIsNone(r.get("error"))
                re_metrics = suite_cls.evaluate({"meta": r["meta"]}, r["response_text"], r.get("tool_calls", []))
                self.assertEqual(re_metrics, r["metrics"], msg=f"Mismatch on {hyp_id} {r['prompt_id']} {r['condition']} it={r['iteration']}")

        # Verify zero reasoning tokens and 100% declared JSON key order on NEMO-PB6
        pb6_recs = grouped["NEMO-PB6"]
        self.assertEqual(len(pb6_recs), 240)
        for r in pb6_recs:
            self.assertEqual(r.get("reasoning_tokens"), 0)
            keys = r["metrics"]["emitted_keys"]
            if r["condition"] == "rationale_first":
                self.assertEqual(keys[0], "rationale")
            elif r["condition"] == "rationale_last":
                self.assertEqual(keys[-1], "rationale")
            else:
                self.assertNotIn("rationale", keys)


class TestPhaseFLingIntegrity(unittest.TestCase):
    def test_phase_f_ling_raw_traces_reevaluate_cleanly_with_zero_errors(self) -> None:
        raw_ling = REPO_ROOT / "evidence" / "raw_phase_f_ling"
        grouped = rs.load_records(raw_ling, "results_LING-*.jsonl")
        self.assertEqual(
            sorted(grouped.keys()),
            ["LING-PB6", "LING-PC1", "LING-PC2", "LING-PD1", "LING-PD4", "LING-PD5", "LING-PE1"],
        )
        self.assertEqual(sum(len(v) for v in grouped.values()), 1510)
        for hyp_id, recs in grouped.items():
            self.assertIn(hyp_id, rs.PHASE_F_LING_BASELINES)
            suite_key = hyp_id.split("-")[1]
            suite_cls = pf.SUITE_SPECS[suite_key][0]
            for r in recs:
                self.assertIsNone(r.get("error"))
                re_metrics = suite_cls.evaluate({"meta": r["meta"]}, r["response_text"], r.get("tool_calls", []))
                self.assertEqual(re_metrics, r["metrics"], msg=f"Mismatch on {hyp_id} {r['prompt_id']} {r['condition']} it={r['iteration']}")

        # Verify zero reasoning tokens and 100% declared JSON key order on LING-PB6
        pb6_recs = grouped["LING-PB6"]
        self.assertEqual(len(pb6_recs), 240)
        for r in pb6_recs:
            self.assertEqual(r.get("reasoning_tokens"), 0)
            keys = r["metrics"]["emitted_keys"]
            if r["condition"] == "rationale_first":
                self.assertEqual(keys[0], "rationale")
            elif r["condition"] == "rationale_last":
                self.assertEqual(keys[-1], "rationale")
            else:
                self.assertNotIn("rationale", keys)

        # Verify zero reasoning tokens on LING-PE1
        for r in grouped["LING-PE1"]:
            self.assertEqual(r.get("reasoning_tokens"), 0)


if __name__ == "__main__":
    unittest.main()
