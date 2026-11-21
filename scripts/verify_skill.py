# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pyyaml>=6.0.1",
# ]
# ///
"""Standalone Pre-Delivery Verification Script for Agent Skill: agent-system-authoring.

Validates specification conformance according to the Agent Skills specification
(https://agentskills.io/specification), including:
1. Root directory layout, lowercase directories, and allowed evidence/ structure.
2. Packaging hygiene: rejects mock_* files, __pycache__, .pytest_cache, tests/, and secret literals.
3. SKILL.md YAML frontmatter schema, naming regex, and description bounds.
4. SKILL.md line count (<500 lines) and progressive disclosure invariants.
5. Reference linking: single-hop direct links without chained hops or broken targets.
6. Evidence ledger tier conformance across all 28 rule IDs.
7. Assets and templates validity (flat Markdown system prompt template, strict JSON tool schema).
8. Evals schema validity (evals/evals.json dual-axis triggering and comparative test cases).
9. Script portability and PEP 723 inline dependency metadata.

Returns exit code 0 if all validation checks pass; non-zero on failure.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any, Dict, List, Optional, Tuple

try:
    import yaml  # type: ignore
except ImportError:
    yaml = None  # type: ignore


SKILL_NAME_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9]|-(?=[a-z0-9])){0,63}$")
SNAKE_CASE_PATTERN = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")
ALLOWED_TIERS = {
    "T1",
    "T2",
    "T3",
    "T4",
    "T5",
    "Methodology",
    "Project convention",
    "Contested",
}
EXPECTED_RULE_IDS = (
    [f"R-SYS-{i:02d}" for i in range(1, 11)]
    + [f"R-TOOL-{i:02d}" for i in range(1, 13)]
    + [f"R-SKILL-{i:02d}" for i in range(1, 7)]
)
SECRET_PATTERNS = [
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"Bearer\s+[A-Za-z0-9._-]{20,}"),
    re.compile(r"\b168\.110\.212\.21\b"),
    re.compile(r"\bgho_[A-Za-z0-9_]{20,}\b"),
]


class SkillVerificationError:
    """Represents a failed verification check with diagnostic context."""

    def __init__(self, category: str, message: str, path: Optional[Path] = None):
        self.category = category
        self.message = message
        self.path = path

    def __str__(self) -> str:
        loc = f" [{self.path}]" if self.path else ""
        return f"[FAILED] {self.category}{loc}: {self.message}"


class SkillVerifier:
    """Comprehensive offline validator for the agent-system-authoring skill package."""

    def __init__(self, root_dir: Path):
        self.root = root_dir.resolve()
        self.errors: List[SkillVerificationError] = []
        self.warnings: List[str] = []
        self.passed_checks: List[str] = []

    def log_failure(self, category: str, message: str, path: Optional[Path] = None) -> None:
        self.errors.append(SkillVerificationError(category, message, path))

    def log_warning(self, category: str, message: str, path: Optional[Path] = None) -> None:
        loc = f" [{path}]" if path else ""
        self.warnings.append(f"[WARNING/RECOMMENDATION] {category}{loc}: {message}")

    def log_success(self, check_name: str) -> None:
        self.passed_checks.append(check_name)

    def extract_frontmatter(self, content: str) -> Tuple[Dict[str, Any], str, int]:
        """Extract and parse YAML frontmatter and markdown body."""
        lines = content.splitlines(keepends=True)
        if not lines or lines[0].strip() != "---":
            return {}, content, 0

        end_idx = None
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                end_idx = i
                break

        if end_idx is None:
            return {}, content, 0

        raw_yaml = "".join(lines[1:end_idx])
        body = "".join(lines[end_idx + 1 :])

        if yaml is not None:
            try:
                parsed = yaml.safe_load(raw_yaml)
                return (parsed if isinstance(parsed, dict) else {}), body, end_idx + 1
            except Exception as e:
                self.log_failure("YAML Frontmatter", f"PyYAML parsing exception: {e}")
                return {}, body, end_idx + 1

        parsed_dict: Dict[str, Any] = {}
        current_key: Optional[str] = None
        multiline_accum: List[str] = []
        is_folded = False

        for line in raw_yaml.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            indent = len(line) - len(line.lstrip())
            if indent == 0 and ":" in stripped and not stripped.startswith("-"):
                if current_key and is_folded:
                    parsed_dict[current_key] = " ".join(multiline_accum)
                    multiline_accum = []
                    is_folded = False
                k, v = stripped.split(":", 1)
                current_key = k.strip()
                val = v.strip().strip("'\"")
                if val in (">", "|"):
                    is_folded = True
                elif not val:
                    parsed_dict[current_key] = {}
                else:
                    parsed_dict[current_key] = val
            elif indent > 0 and current_key:
                if is_folded:
                    multiline_accum.append(stripped)
                elif isinstance(parsed_dict.get(current_key), dict) and ":" in stripped:
                    sub_k, sub_v = stripped.split(":", 1)
                    parsed_dict[current_key][sub_k.strip()] = sub_v.strip().strip("'\"")

        if current_key and is_folded:
            parsed_dict[current_key] = " ".join(multiline_accum)

        return parsed_dict, body, end_idx + 1

    def verify_directory_layout(self) -> None:
        """Verify directory structure and absence of disallowed root artifacts."""
        if not self.root.exists() or not self.root.is_dir():
            self.log_failure("Directory Layout", f"Skill root directory does not exist: {self.root}")
            return

        allowed_root_md = {"SKILL.md"}
        root_md = {p.name for p in self.root.glob("*.md")}
        disallowed = root_md - allowed_root_md
        if disallowed:
            self.log_failure("Directory Layout", f"Disallowed root markdown files found: {disallowed}")

        required_dirs = [
            ("references", self.root / "references"),
            ("scripts", self.root / "scripts"),
            ("assets/templates", self.root / "assets" / "templates"),
            ("evals", self.root / "evals"),
            ("evidence", self.root / "evidence"),
            ("evidence/raw", self.root / "evidence" / "raw"),
            ("evidence/raw_phase_b", self.root / "evidence" / "raw_phase_b"),
        ]
        for name, dir_path in required_dirs:
            if not dir_path.exists() or not dir_path.is_dir():
                self.log_failure("Directory Layout", f"Required directory missing: {name}", dir_path)

        found_names = {p.name for p in self.root.iterdir()}
        for d in ["references", "scripts", "assets", "evals", "evidence"]:
            if any(n.lower() == d for n in found_names) and d not in found_names:
                self.log_failure("Directory Layout", f"Directory '{d}' must be strictly lowercase")

        self.log_success("Directory Layout and Casing")

    def verify_packaging_hygiene(self) -> None:
        """Verify absence of caches, dev test runners, mock files, and hardcoded credentials."""
        forbidden_dir_names = {"__pycache__", ".pytest_cache", ".mypy_cache", "tests"}
        forbidden_file_names = {"pytest.ini", "tox.ini", "conftest.py", ".DS_Store", "Thumbs.db"}

        for path in self.root.rglob("*"):
            rel = path.relative_to(self.root)
            if ".git" in rel.parts:
                continue
            name_lower = path.name.lower()

            if path.is_dir():
                if path.name in forbidden_dir_names or name_lower.startswith("mock_"):
                    self.log_failure("Packaging Hygiene", f"Disallowed directory present: {rel}", path)
                continue

            if path.name in forbidden_file_names or name_lower.startswith("mock_") or name_lower.startswith("test_"):
                self.log_failure("Packaging Hygiene", f"Disallowed file present: {rel}", path)
                continue

            # Allow raw JSONL and provenance scripts only inside evidence/
            if path.suffix == ".jsonl" and rel.parts[0] != "evidence":
                self.log_failure("Packaging Hygiene", f"JSONL trace file outside evidence/: {rel}", path)

            # Check allowed text files for leaked secret literals
            if path.suffix in {".md", ".py", ".json", ".jsonl"}:
                try:
                    text = path.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    continue
                for pat in SECRET_PATTERNS:
                    if pat.search(text):
                        self.log_failure("Packaging Hygiene", f"Potential credential literal matched in {rel}", path)

        self.log_success("Packaging Hygiene & Secret Scan")

    def verify_skill_md_frontmatter(self) -> None:
        """Verify SKILL.md frontmatter schema, name match, and description limits."""
        skill_md = self.root / "SKILL.md"
        if not skill_md.exists() or not skill_md.is_file():
            self.log_failure("Frontmatter Schema", "SKILL.md missing at skill package root", skill_md)
            return

        content = skill_md.read_text(encoding="utf-8")
        lines = content.splitlines()
        if not lines or lines[0].strip() != "---":
            self.log_failure("Frontmatter Schema", "SKILL.md must start with '---' on line 1", skill_md)
            return

        fm, body, _ = self.extract_frontmatter(content)
        if not fm:
            self.log_failure("Frontmatter Schema", "Frontmatter parsed to empty dict or missing closing '---'", skill_md)
            return

        name = fm.get("name", "")
        if not isinstance(name, str) or not name:
            self.log_failure("Frontmatter Schema", "Frontmatter missing non-empty 'name' field", skill_md)
        else:
            if not SKILL_NAME_PATTERN.match(name):
                self.log_failure("Frontmatter Schema", f"Frontmatter name '{name}' fails specification regex", skill_md)
            if name != self.root.name:
                self.log_failure("Frontmatter Schema", f"Frontmatter name '{name}' must match root directory '{self.root.name}'", skill_md)

        desc = fm.get("description", "")
        if not isinstance(desc, str) or not desc.strip():
            self.log_failure("Frontmatter Schema", "Frontmatter missing non-empty 'description' field", skill_md)
        else:
            desc_len = len(desc.strip())
            if desc_len > 1024:
                self.log_failure("Frontmatter Schema", f"Description length {desc_len} exceeds 1024 character limit", skill_md)
            desc_lower = desc.lower()
            has_what = any(k in desc_lower for k in ["teach", "author", "write", "instruction", "system", "schema", "prompt"])
            has_when = any(k in desc_lower for k in ["when", "use", "trigger", "design", "create", "ask"])
            if not has_what:
                self.log_failure("Frontmatter Schema", "Description must state WHAT the skill does", skill_md)
            if not has_when:
                self.log_failure("Frontmatter Schema", "Description must state WHEN to trigger the skill", skill_md)

        if "license" in fm:
            lic = fm["license"]
            if not isinstance(lic, str) or not lic.strip():
                self.log_failure("Frontmatter Schema", "Optional 'license' must be a non-empty string", skill_md)

        if "compatibility" in fm:
            compat = fm["compatibility"]
            if not isinstance(compat, str) or len(compat) > 500:
                self.log_failure("Frontmatter Schema", "Optional 'compatibility' must be a string <= 500 chars", skill_md)

        if "metadata" in fm:
            if not isinstance(fm["metadata"], dict):
                self.log_failure("Frontmatter Schema", "Optional 'metadata' must be a key-value mapping", skill_md)
            else:
                for mk, mv in fm["metadata"].items():
                    if not isinstance(mv, str):
                        self.log_failure("Frontmatter Schema", f"Metadata key '{mk}' value must be a string, received {type(mv).__name__}", skill_md)

        if "allowed-tools" in fm:
            tools_val = fm["allowed-tools"]
            if not isinstance(tools_val, str):
                self.log_failure("Frontmatter Schema", "Optional 'allowed-tools' must be a space-separated string", skill_md)

        self.log_success("SKILL.md Frontmatter Schema")

    def verify_skill_md_body_limits(self) -> None:
        """Verify SKILL.md body line limit, token estimates, and section hierarchy."""
        skill_md = self.root / "SKILL.md"
        if not skill_md.exists():
            return

        content = skill_md.read_text(encoding="utf-8")
        lines = content.splitlines()

        if len(lines) >= 500:
            self.log_failure("Progressive Disclosure", f"SKILL.md line count {len(lines)} exceeds 500 line limit", skill_md)

        if len(lines) < 40:
            self.log_failure("Progressive Disclosure", f"SKILL.md total lines {len(lines)} below minimum threshold of 40", skill_md)

        _, body, _ = self.extract_frontmatter(content)
        non_blank_lines = [line for line in body.splitlines() if line.strip()]
        if len(non_blank_lines) < 30:
            self.log_failure("Progressive Disclosure", f"Body substantive content {len(non_blank_lines)} lines below threshold 30", skill_md)

        est_tokens = len(body) / 4.0
        if est_tokens >= 5000:
            self.log_failure("Progressive Disclosure", f"Estimated tokens {est_tokens:.0f} exceeds 5,000 token limit", skill_md)

        table_rows = [line for line in body.splitlines() if line.strip().startswith("|")]
        if len(table_rows) >= 25:
            self.log_failure("Progressive Disclosure", f"SKILL.md body contains {len(table_rows)} table rows; deep tables must be in references/", skill_md)

        if "\n\n\n\n" in content.replace("\r\n", "\n"):
            self.log_failure("Progressive Disclosure", "Detected artificial padding with >= 3 consecutive blank lines", skill_md)

        for i, line in enumerate(lines, 1):
            if len(line) > 1000:
                self.log_failure("Progressive Disclosure", f"Line {i} exceeds 1,000 character limit ({len(line)} chars)", skill_md)

        headings = [h.strip().lower() for h in re.findall(r"^#+\s+(.+)$", body, re.MULTILINE)]
        has_workflow = any("workflow" in h or "procedure" in h or "step" in h for h in headings)
        has_ref = any("reference" in h or "evidence" in h or "guide" in h for h in headings)

        if not has_workflow:
            self.log_failure("Structural Hierarchy", "SKILL.md missing procedural authoring workflow section heading", skill_md)
        if not has_ref:
            self.log_failure("Structural Hierarchy", "SKILL.md missing references section heading", skill_md)

        self.log_success("SKILL.md Line Budget & Section Hierarchy")

    def verify_reference_linking(self) -> None:
        """Verify shallow relative linking invariants and absence of orphaned references."""
        skill_md = self.root / "SKILL.md"
        refs_dir = self.root / "references"
        if not skill_md.exists() or not refs_dir.exists():
            return

        content = skill_md.read_text(encoding="utf-8")
        links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", content)

        ref_links: List[Tuple[str, str]] = []
        headings = [h.strip().lower() for h in re.findall(r"^#+\s+(.+)$", content, re.MULTILINE)]
        heading_slugs = {re.sub(r"[^\w\- ]", "", h).replace(" ", "-") for h in headings}

        for text, target in links:
            if not text.strip() or not target.strip():
                self.log_failure("Reference Linking", f"Found empty link label or target: [{text}]({target})", skill_md)
                continue

            if target.startswith("http://") or target.startswith("https://"):
                continue

            if target.startswith("#"):
                fragment = target.lstrip("#").lower()
                if fragment not in heading_slugs:
                    self.log_failure("Reference Linking", f"Anchor fragment link '{target}' does not match any heading in SKILL.md", skill_md)
                continue

            if "../" in target:
                self.log_failure("Reference Linking", f"Reference link '{target}' contains multi-hop parent traversal '../'", skill_md)

            clean_target = target.split("#")[0]
            resolved = (self.root / clean_target).resolve()
            if not resolved.exists():
                self.log_failure("Reference Linking", f"Broken relative link: [{text}]({target}) -> missing path {resolved}", skill_md)
            else:
                if "references/" in target:
                    ref_links.append((text, clean_target))

        if len(ref_links) < 3:
            self.log_failure("Reference Linking", f"Expected >= 3 links from SKILL.md to references/, found {len(ref_links)}", skill_md)

        skill_linked_files = {Path(t).name for _, t in ref_links}
        ledger_path = refs_dir / "evidence_ledger.md"
        ledger_text = ledger_path.read_text(encoding="utf-8") if ledger_path.exists() else ""

        for ref_file in refs_dir.glob("*.md"):
            is_linked = (ref_file.name in skill_linked_files) or (ref_file.name in ledger_text) or (ref_file.name == "evidence_ledger.md")
            if not is_linked:
                self.log_failure("Reference Linking", f"Orphaned reference file not linked anywhere: {ref_file.name}", ref_file)

        self.log_success("Single-Hop Reference Linking Invariants")

    def verify_evidence_ledger_tiers(self) -> None:
        """Verify that every rule ID in evidence_ledger.md uses the T1-T5/Methodology/Convention/Contested tier system."""
        ledger_path = self.root / "references" / "evidence_ledger.md"
        if not ledger_path.exists():
            self.log_failure("Evidence Ledger", "references/evidence_ledger.md missing", ledger_path)
            return

        text = ledger_path.read_text(encoding="utf-8")
        if "Grade A" in text or "Grade B" in text:
            self.log_failure("Evidence Ledger", "Legacy 'Grade A' or 'Grade B' vocabulary found in evidence_ledger.md", ledger_path)

        row_tiers: Dict[str, str] = {}
        for line in text.splitlines():
            if not line.startswith("| **R-"):
                continue
            cols = [c.strip() for c in line.strip("|").split("|")]
            if len(cols) >= 4:
                rid = cols[0].strip("* ")
                tier = cols[3].strip("* ")
                row_tiers[rid] = tier

        missing_rules = [rid for rid in EXPECTED_RULE_IDS if rid not in row_tiers]
        if missing_rules:
            self.log_failure("Evidence Ledger", f"Missing expected rule IDs in ledger table: {missing_rules}", ledger_path)

        for rid, tier in row_tiers.items():
            if tier not in ALLOWED_TIERS:
                self.log_failure("Evidence Ledger", f"Rule {rid} has invalid tier '{tier}' (expected one of {sorted(ALLOWED_TIERS)})", ledger_path)

        self.log_success("Evidence Ledger Tier Vocabulary")

    def verify_templates(self) -> None:
        """Verify flat Markdown system prompt, skill starter, and strict JSON tool schema templates."""
        templates_dir = self.root / "assets" / "templates"
        sys_tmpl = templates_dir / "system_prompt_template.md"
        legacy_xml = templates_dir / "system_prompt_template.xml"
        skill_tmpl = templates_dir / "skill_template.md"
        tool_tmpl = templates_dir / "tool_schema_template.json"

        if legacy_xml.exists():
            self.log_failure("Templates", "Obsolete XML template assets/templates/system_prompt_template.xml should be removed", legacy_xml)

        if not sys_tmpl.exists():
            self.log_failure("Templates", "assets/templates/system_prompt_template.md missing", sys_tmpl)
        else:
            md_content = sys_tmpl.read_text(encoding="utf-8")
            headings = re.findall(r"^###\s+.+$", md_content, re.MULTILINE)
            if len(headings) < 3:
                self.log_failure("Templates", "system_prompt_template.md must use flat Markdown ### section headers", sys_tmpl)
            if "{{agent_identity}}" not in md_content or "{{rules_content}}" not in md_content:
                self.log_failure("Templates", "system_prompt_template.md missing {{agent_identity}} or {{rules_content}} placeholders", sys_tmpl)
            if "reminder" not in md_content.lower():
                self.log_failure("Templates", "system_prompt_template.md missing trailing reminder section", sys_tmpl)

        if not skill_tmpl.exists():
            self.log_failure("Templates", "assets/templates/skill_template.md missing", skill_tmpl)

        if not tool_tmpl.exists():
            self.log_failure("Templates", "assets/templates/tool_schema_template.json missing", tool_tmpl)
        else:
            try:
                schema = json.loads(tool_tmpl.read_text(encoding="utf-8"))
                if "properties" not in schema:
                    self.log_failure("Templates", "Tool template missing 'properties' dictionary", tool_tmpl)
                if schema.get("additionalProperties", True) is not False:
                    self.log_failure("Templates", "Tool template must specify additionalProperties: false", tool_tmpl)

                props = list(schema.get("properties", {}).keys())
                reqs = set(schema.get("required", []))
                if set(props) != reqs:
                    self.log_failure("Templates", f"Strict tool schema requires all properties in 'required'. Props: {set(props)}, Req: {reqs}", tool_tmpl)

                if len(props) < 2:
                    self.log_failure("Templates", f"Tool schema has {len(props)} properties; expected >= 2", tool_tmpl)
                else:
                    first_prop = props[0].lower()
                    if "thought" not in first_prop and "rationale" not in first_prop and "reason" not in first_prop:
                        self.log_warning("Templates", f"First property is '{first_prop}'; rationale-first is recommended for non-reasoning constrained decoding.", tool_tmpl)

                for prop_name in props:
                    if not SNAKE_CASE_PATTERN.match(prop_name):
                        self.log_failure("Templates", f"Property '{prop_name}' in tool template is not snake_case", tool_tmpl)

            except json.JSONDecodeError as e:
                self.log_failure("Templates", f"tool_schema_template.json is not valid JSON: {e}", tool_tmpl)

        self.log_success("Assets Templates Validation")

    def verify_evals(self) -> None:
        """Verify evals/evals.json dual-axis triggering and comparative test cases."""
        evals_file = self.root / "evals" / "evals.json"
        if not evals_file.exists():
            self.log_failure("Evals Schema", "evals/evals.json missing", evals_file)
            return

        try:
            data = json.loads(evals_file.read_text(encoding="utf-8"))
            if data.get("skill_name") != self.root.name:
                self.log_failure("Evals Schema", f"skill_name is '{data.get('skill_name')}', expected '{self.root.name}'", evals_file)

            evals_list = data.get("evals")
            if not isinstance(evals_list, list) or not evals_list:
                self.log_failure("Evals Schema", "'evals' must be a non-empty list of test cases", evals_file)
                return

            ids = set()
            positives: List[Dict[str, Any]] = []
            negatives: List[Dict[str, Any]] = []
            comparatives: List[Dict[str, Any]] = []

            for item in evals_list:
                item_id = item.get("id")
                if not item_id or item_id in ids:
                    self.log_failure("Evals Schema", f"Duplicate or missing eval ID: '{item_id}'", evals_file)
                ids.add(item_id)

                prompt = item.get("prompt", "")
                if len(prompt.strip()) < 15:
                    self.log_failure("Evals Schema", f"Prompt for eval '{item_id}' is too short ({len(prompt)} chars)", evals_file)

                eval_type = item.get("type")
                if eval_type == "trigger_positive" or item.get("trigger") is True or item.get("should_trigger") is True:
                    positives.append(item)
                elif eval_type == "trigger_negative" or item.get("trigger") is False or item.get("should_trigger") is False:
                    negatives.append(item)
                elif eval_type == "comparative" or "comparative" in str(item_id):
                    comparatives.append(item)

            if len(positives) < 2:
                self.log_failure("Evals Schema", f"Expected >= 2 positive triggers, found {len(positives)}", evals_file)
            if len(negatives) < 2:
                self.log_failure("Evals Schema", f"Expected >= 2 negative near-miss triggers, found {len(negatives)}", evals_file)
            if len(comparatives) < 2:
                self.log_failure("Evals Schema", f"Expected >= 2 comparative evaluation cases, found {len(comparatives)}", evals_file)

            for comp in comparatives:
                has_rubric = "rubric" in comp or "criteria" in comp or "expected_output" in comp
                if not has_rubric:
                    self.log_failure("Evals Schema", f"Comparative eval '{comp.get('id')}' missing rubric/criteria", evals_file)

            raw_text = evals_file.read_text(encoding="utf-8").lower()
            has_verified = any(k in raw_text for k in ["markdown", "snake_case", "reminder", "rationale", "parameter", "third person"])
            has_anti = any(k in raw_text for k in ["folklore", "anti-pattern", "persona", "cot", "superlative", "gaming"])
            if not has_verified:
                self.log_failure("Evals Schema", "Comparative rubrics must evaluate verified best practices (markdown, snake_case, reminder, rationale)", evals_file)
            if not has_anti:
                self.log_failure("Evals Schema", "Comparative rubrics must check absence of debunked folklore (personas, redundant CoT, gaming superlatives)", evals_file)

        except json.JSONDecodeError as e:
            self.log_failure("Evals Schema", f"evals/evals.json failed JSON parsing: {e}", evals_file)

        self.log_success("Evals Schema & Dual-Axis Test Suite")

    def verify_pep723_metadata(self) -> None:
        """Verify PEP 723 inline dependency metadata on utility scripts."""
        script_targets = [
            self.root / "scripts" / "verify_skill.py",
            self.root / "evidence" / "recompute_stats.py",
            self.root / "evidence" / "phase_b_harness.py",
            self.root / "evidence" / "run_evals.py",
        ]
        for script_path in script_targets:
            if not script_path.exists():
                self.log_failure("PEP 723 Metadata", f"Missing required script: {script_path.name}", script_path)
                continue

            content = script_path.read_text(encoding="utf-8")
            match = re.search(r"^# /// script\s*$(.*?)^# ///\s*$", content, re.MULTILINE | re.DOTALL)
            if not match:
                self.log_failure("PEP 723 Metadata", f"Script missing properly closed '# /// script' block: {script_path.name}", script_path)
            else:
                block_content = match.group(1)
                if "requires-python" not in block_content:
                    self.log_failure("PEP 723 Metadata", f"Missing 'requires-python' in {script_path.name}", script_path)
                if "dependencies" not in block_content:
                    self.log_failure("PEP 723 Metadata", f"Missing 'dependencies' in {script_path.name}", script_path)

        self.log_success("PEP 723 Dependency Metadata")

    def run_all(self) -> bool:
        """Execute all validation checks in sequence."""
        self.verify_directory_layout()
        self.verify_packaging_hygiene()
        self.verify_skill_md_frontmatter()
        self.verify_skill_md_body_limits()
        self.verify_reference_linking()
        self.verify_evidence_ledger_tiers()
        self.verify_templates()
        self.verify_evals()
        self.verify_pep723_metadata()
        return len(self.errors) == 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Standalone Pre-Delivery Verification Script for Agent Skill: agent-system-authoring"
    )
    parser.add_argument(
        "target_dir",
        nargs="?",
        default=".",
        help="Path to the agent skill root directory to verify (default: current directory)",
    )
    args = parser.parse_args()

    target_path = Path(args.target_dir).resolve()
    print(f"=== Verifying Agent Skill Package: {target_path} ===")

    verifier = SkillVerifier(target_path)
    success = verifier.run_all()

    print("\n--- Passed Checks ---")
    for check in verifier.passed_checks:
        print(f" [PASSED] {check}")

    if verifier.warnings:
        print("\n--- Warnings & Recommendations ---")
        for warn in verifier.warnings:
            print(f" {warn}")

    if not success:
        print(f"\n--- Verification Failures ({len(verifier.errors)}) ---")
        for err in verifier.errors:
            print(f" {err}")
        print("\nRESULT: FAILED (Exit Code 1)")
        return 1

    print("\nRESULT: PASSED (All invariants satisfied, Exit Code 0)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
