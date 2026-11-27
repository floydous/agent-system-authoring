# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Standalone Pre-Delivery Verification Script for Agent Skills.

Validates specification conformance according to the Agent Skills specification
(https://agentskills.io/specification), including:
1. Directory layout, lowercase directories, and keeping evidence/ outside skill root.
2. Packaging hygiene: rejects mock_* files, __pycache__, .pytest_cache, tests/, and secret literals.
3. SKILL.md YAML frontmatter schema, naming regex, and description bounds.
4. SKILL.md line count (<500 lines), token budget (<5000 est tokens), and section hierarchy.
5. Reference linking: single-hop direct links without chained hops or broken targets.
6. Evidence ledger tier conformance (when running on agent-system-authoring without --generic).
7. Assets and templates validity (when running on agent-system-authoring without --generic).
8. Evals schema validity and version sync (when evals/evals.json exists).
9. Script portability and PEP 723 inline dependency metadata (stdlib-only).

Returns exit code 0 if all validation checks pass; non-zero on failure.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any, Dict, List, Optional, Tuple


SKILL_NAME_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9]|-(?=[a-z0-9])){0,63}$")
SNAKE_CASE_PATTERN = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")
ALLOWED_FRONTMATTER_KEYS = {
    "name",
    "description",
    "license",
    "compatibility",
    "metadata",
    "allowed-tools",
}
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
    re.compile(r"https?://(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})(?::\d+)?"),
    re.compile(r"https?://\d{1,3}(?:\.\d{1,3}){3}:\d+"),
    re.compile(r"\bgho_[A-Za-z0-9_]{20,}\b"),
]
LEAKED_INTERNAL_RULE_RE = re.compile(r"\bR-(?:SYS|TOOL|SKILL)-\d{2}\b")
WINDOWS_DRIVE_RE = re.compile(r"^[A-Za-z]:")
FENCED_CODE_BLOCK_RE = re.compile(r"(?m)^([ \t]*)(`{3,}|~{3,})[^\n]*\n.*?^[ \t]*\2[ \t]*$", re.DOTALL)
INLINE_CODE_SPAN_RE = re.compile(r"`[^`\n]+`")


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
    """Comprehensive stdlib-only offline validator for Agent Skill packages."""

    def __init__(self, root_dir: Path, generic: bool = False):
        self.root = root_dir.resolve()
        self.generic = generic or (self.root.name != "agent-system-authoring")
        self.errors: List[SkillVerificationError] = []
        self.warnings: List[str] = []
        self.passed_checks: List[str] = []

    def log_failure(self, category: str, message: str, path: Optional[Path] = None) -> None:
        self.errors.append(SkillVerificationError(category, message, path))

    def log_warning(self, category: str, message: str, path: Optional[Path] = None) -> None:
        loc = f" [{path}]" if path else ""
        self.warnings.append(f"[WARNING/RECOMMENDATION] {category}{loc}: {message}")

    def log_if_clean(self, err_before: int, check_name: str) -> None:
        """Record check as passed ONLY when zero failures were added during that check."""
        if len(self.errors) == err_before:
            self.passed_checks.append(check_name)

    @staticmethod
    def _strip_inline_comment(raw_val: str) -> str:
        """Strip unquoted YAML inline comments preceded by whitespace."""
        s = raw_val.strip()
        if not s:
            return s
        if s[0] in ("'", '"'):
            quote = s[0]
            escaped = False
            for idx in range(1, len(s)):
                ch = s[idx]
                if escaped:
                    escaped = False
                    continue
                if quote == '"' and ch == "\\":
                    escaped = True
                    continue
                if ch == quote:
                    return s[: idx + 1]
            return s
        match = re.search(r"\s+#.*$", s)
        return s[: match.start()].rstrip() if match else s

    def _parse_yaml_scalar(self, raw_val: str) -> Any:
        """Parse a single YAML scalar preserving native int/float/bool/null unless quoted."""
        s = self._strip_inline_comment(raw_val)
        if len(s) >= 2 and ((s[0] == '"' and s[-1] == '"') or (s[0] == "'" and s[-1] == "'")):
            return s[1:-1]
        low = s.lower()
        if low == "true":
            return True
        if low == "false":
            return False
        if low in ("null", "~"):
            return None
        if re.fullmatch(r"[+-]?\d+", s):
            return int(s)
        if re.fullmatch(r"[+-]?(?:\d+\.\d*|\.\d+)(?:[eE][+-]?\d+)?", s):
            return float(s)
        return s

    def extract_frontmatter(self, content: str) -> Tuple[Dict[str, Any], str, int]:
        """Parse YAML frontmatter block cleanly using Python stdlib only."""
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

        parsed_dict: Dict[str, Any] = {}
        current_key: Optional[str] = None
        multiline_accum: List[str] = []
        block_mode: Optional[str] = None  # "folded" or "literal"

        def flush_block() -> None:
            nonlocal multiline_accum, block_mode
            if current_key and block_mode:
                sep = "\n" if block_mode == "literal" else " "
                parsed_dict[current_key] = sep.join(multiline_accum)
                multiline_accum = []
                block_mode = None

        for line in raw_yaml.splitlines():
            stripped = line.strip()
            if not stripped:
                if block_mode == "literal":
                    multiline_accum.append("")
                continue
            if stripped.startswith("#") and not block_mode:
                continue
            indent = len(line) - len(line.lstrip())
            if indent == 0 and ":" in stripped and not stripped.startswith("-"):
                flush_block()
                k, v = stripped.split(":", 1)
                current_key = k.strip()
                raw_val = self._strip_inline_comment(v)
                if raw_val in (">", ">-"):
                    block_mode = "folded"
                elif raw_val in ("|", "|-"):
                    block_mode = "literal"
                elif not raw_val:
                    parsed_dict[current_key] = {}
                else:
                    parsed_dict[current_key] = self._parse_yaml_scalar(raw_val)
            elif indent > 0 and current_key:
                if block_mode:
                    multiline_accum.append(stripped)
                elif stripped.startswith("- "):
                    item_val = self._parse_yaml_scalar(stripped[2:])
                    if isinstance(parsed_dict.get(current_key), dict) and not parsed_dict[current_key]:
                        parsed_dict[current_key] = [item_val]
                    elif isinstance(parsed_dict.get(current_key), list):
                        parsed_dict[current_key].append(item_val)
                elif isinstance(parsed_dict.get(current_key), dict) and ":" in stripped:
                    sub_k, sub_v = stripped.split(":", 1)
                    sub_raw = self._strip_inline_comment(sub_v)
                    parsed_dict[current_key][sub_k.strip()] = "" if not sub_raw else self._parse_yaml_scalar(sub_raw)

        flush_block()

        return parsed_dict, body, end_idx + 1

    def verify_directory_layout(self) -> None:
        """Verify directory structure and absence of disallowed root artifacts."""
        err_before = len(self.errors)
        if not self.root.exists() or not self.root.is_dir():
            self.log_failure("Directory Layout", f"Skill root directory does not exist: {self.root}")
            return

        if not self.generic:
            allowed_root_md = {"SKILL.md"}
            root_md = {p.name for p in self.root.glob("*.md")}
            disallowed = root_md - allowed_root_md
            if disallowed:
                self.log_failure("Directory Layout", f"Disallowed root markdown files found: {disallowed}")

        if not self.generic:
            required_dirs = [
                ("references", self.root / "references"),
                ("scripts", self.root / "scripts"),
                ("assets/templates", self.root / "assets" / "templates"),
                ("evals", self.root / "evals"),
            ]
            for name, dir_path in required_dirs:
                if not dir_path.exists() or not dir_path.is_dir():
                    self.log_failure("Directory Layout", f"Required directory missing: {name}", dir_path)

        if (self.root / "evidence").exists():
            self.log_failure(
                "Directory Layout",
                "Repo-level evidence/ must live outside the lean installable skill directory",
                self.root / "evidence",
            )

        found_names = {p.name for p in self.root.iterdir()}
        for d in ["references", "scripts", "assets", "evals"]:
            if any(n.lower() == d for n in found_names) and d not in found_names:
                self.log_failure("Directory Layout", f"Directory '{d}' must be strictly lowercase")

        self.log_if_clean(err_before, "Directory Layout and Casing")

    def verify_packaging_hygiene(self) -> None:
        """Verify absence of caches, dev test runners, mock files, env/key files, and hardcoded credentials."""
        err_before = len(self.errors)
        forbidden_dir_names = {"__pycache__", ".pytest_cache", ".mypy_cache", "tests"}
        forbidden_file_names = {
            "pytest.ini",
            "tox.ini",
            "conftest.py",
            ".DS_Store",
            "Thumbs.db",
            ".env",
            "id_rsa",
            "id_ed25519",
        }
        allowed_env_templates = {".env.example", ".env.sample", ".env.template"}
        forbidden_secret_suffixes = {".pem", ".key", ".p12", ".pfx"}
        text_scan_suffixes = {
            ".md",
            ".py",
            ".json",
            ".yaml",
            ".yml",
            ".sh",
            ".bash",
            ".ps1",
            ".txt",
            ".toml",
            ".cfg",
            ".ini",
            ".js",
            ".ts",
            ".mjs",
            ".cjs",
            ".env",
        }

        for path in self.root.rglob("*"):
            rel = path.relative_to(self.root)
            if ".git" in rel.parts:
                continue
            name_lower = path.name.lower()

            if path.is_dir():
                if path.name in forbidden_dir_names or name_lower.startswith("mock_"):
                    self.log_failure("Packaging Hygiene", f"Disallowed directory present: {rel}", path)
                continue

            is_secret_env = name_lower.startswith(".env.") and name_lower not in allowed_env_templates
            if (
                path.name in forbidden_file_names
                or is_secret_env
                or path.suffix.lower() in forbidden_secret_suffixes
                or name_lower.startswith("mock_")
                or name_lower.startswith("test_")
            ):
                self.log_failure("Packaging Hygiene", f"Disallowed file present: {rel}", path)
                continue

            if path.suffix == ".jsonl":
                self.log_failure("Packaging Hygiene", f"JSONL trace file inside installable skill: {rel}", path)

            should_scan = (path.suffix.lower() in text_scan_suffixes) or (
                not path.suffix and path.stat().st_size <= 524_288
            )
            if should_scan:
                try:
                    text = path.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    continue
                for pat in SECRET_PATTERNS:
                    if pat.search(text):
                        self.log_failure("Packaging Hygiene", f"Potential credential or private IP endpoint matched in {rel}", path)

        self.log_if_clean(err_before, "Packaging Hygiene & Secret Scan")

    def verify_skill_md_frontmatter(self) -> None:
        """Verify SKILL.md frontmatter schema, name match, and description limits."""
        err_before = len(self.errors)
        skill_md = self.root / "SKILL.md"
        if not skill_md.exists() or not skill_md.is_file():
            self.log_failure("Frontmatter Schema", "SKILL.md missing at skill package root", skill_md)
            return

        content = skill_md.read_text(encoding="utf-8")
        lines = content.splitlines()
        if not lines or lines[0].strip() != "---":
            self.log_failure("Frontmatter Schema", "SKILL.md must start with '---' on line 1", skill_md)
            return

        fm, _, _ = self.extract_frontmatter(content)
        if not fm:
            self.log_failure("Frontmatter Schema", "Frontmatter parsed to empty dict or missing closing '---'", skill_md)
            return

        unknown_keys = sorted(set(fm.keys()) - ALLOWED_FRONTMATTER_KEYS)
        if unknown_keys:
            self.log_failure(
                "Frontmatter Schema",
                f"Unrecognized top-level frontmatter field(s) {unknown_keys}; place custom attributes under 'metadata'",
                skill_md,
            )

        name = fm.get("name", "")
        if not isinstance(name, str) or not name:
            self.log_failure("Frontmatter Schema", "Frontmatter missing non-empty 'name' field", skill_md)
        else:
            if not SKILL_NAME_PATTERN.fullmatch(name):
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
            if not self.generic:
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

        self.log_if_clean(err_before, "SKILL.md Frontmatter Schema")

    def verify_skill_md_body_limits(self) -> None:
        """Verify SKILL.md body line limit, token estimates, and section hierarchy."""
        err_before = len(self.errors)
        skill_md = self.root / "SKILL.md"
        if not skill_md.exists():
            return

        content = skill_md.read_text(encoding="utf-8")
        lines = content.splitlines()

        if len(lines) >= 500:
            self.log_failure("Progressive Disclosure", f"SKILL.md line count {len(lines)} exceeds 500 line limit", skill_md)

        _, body, _ = self.extract_frontmatter(content)
        non_blank_lines = [line for line in body.splitlines() if line.strip()]
        if not self.generic:
            if len(lines) < 25:
                self.log_failure("Progressive Disclosure", f"SKILL.md total lines {len(lines)} below minimum threshold of 25", skill_md)
            if len(non_blank_lines) < 20:
                self.log_failure("Progressive Disclosure", f"Body substantive content {len(non_blank_lines)} lines below threshold 20", skill_md)
        elif len(non_blank_lines) < 1:
            self.log_failure("Progressive Disclosure", "SKILL.md body must contain at least 1 non-blank line", skill_md)

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

        if not self.generic:
            headings = [h.strip().lower() for h in re.findall(r"^#+\s+(.+)$", body, re.MULTILINE)]
            has_workflow = any("workflow" in h or "procedure" in h or "step" in h for h in headings)
            has_ref = any("reference" in h or "evidence" in h or "guide" in h for h in headings)
            if not has_workflow:
                self.log_failure("Structural Hierarchy", "SKILL.md missing procedural authoring workflow section heading", skill_md)
            if not has_ref:
                self.log_failure("Structural Hierarchy", "SKILL.md missing references section heading", skill_md)

        self.log_if_clean(err_before, "SKILL.md Line Budget & Section Hierarchy")

    @staticmethod
    def _strip_code_from_markdown(text: str) -> str:
        """Remove fenced code blocks and inline code spans before scanning Markdown links."""
        normalized = text.replace("\r\n", "\n")
        no_fences = FENCED_CODE_BLOCK_RE.sub("", normalized)
        return INLINE_CODE_SPAN_RE.sub("", no_fences)

    @staticmethod
    def _is_absolute_link(clean_target: str) -> bool:
        return (
            clean_target.startswith("/")
            or bool(WINDOWS_DRIVE_RE.match(clean_target))
            or Path(clean_target).is_absolute()
        )

    def verify_reference_linking(self) -> None:
        """Verify shallow relative linking invariants and absence of orphaned references."""
        err_before = len(self.errors)
        skill_md = self.root / "SKILL.md"
        refs_dir = self.root / "references"
        if not skill_md.exists():
            return

        content = skill_md.read_text(encoding="utf-8")
        link_scannable = self._strip_code_from_markdown(content)
        links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", link_scannable)

        ref_links: List[Tuple[str, str]] = []
        headings = [h.strip().lower() for h in re.findall(r"^#+\s+(.+)$", link_scannable, re.MULTILINE)]
        heading_slugs = {re.sub(r"[^\w\- ]", "", h).replace(" ", "-") for h in headings}

        for text, target in links:
            if not text.strip() or not target.strip():
                self.log_failure("Reference Linking", f"Found empty link label or target: [{text}]({target})", skill_md)
                continue

            if target.startswith(("http://", "https://", "mailto:")):
                continue

            if target.startswith("#"):
                fragment = target.lstrip("#").lower()
                if fragment not in heading_slugs:
                    self.log_failure("Reference Linking", f"Anchor fragment link '{target}' does not match any heading in SKILL.md", skill_md)
                continue

            clean_target = target.split("#", 1)[0].strip()
            if not clean_target:
                continue

            if "\\" in clean_target:
                self.log_failure("Reference Linking", f"Link '{target}' uses non-portable backslash separator '\\'", skill_md)
                continue

            if self._is_absolute_link(clean_target):
                self.log_failure("Reference Linking", f"Link '{target}' uses an absolute path instead of a skill-relative path", skill_md)
                continue

            target_parts = [p for p in clean_target.split("/") if p and p != "."]
            if ".." in target_parts:
                self.log_failure("Reference Linking", f"Reference link '{target}' contains parent traversal '..'", skill_md)
                continue

            if target_parts and target_parts[0] == "references" and len(target_parts) > 2:
                self.log_failure("Reference Linking", f"Reference link '{target}' exceeds one-level depth under references/", skill_md)
                continue

            resolved = (self.root / clean_target).resolve()
            try:
                resolved.relative_to(self.root)
            except ValueError:
                self.log_failure("Reference Linking", f"Relative link escapes skill root: [{text}]({target})", skill_md)
                continue

            if not resolved.exists():
                self.log_failure("Reference Linking", f"Broken relative link: [{text}]({target}) -> missing path {resolved}", skill_md)
            elif target_parts and target_parts[0] == "references":
                ref_links.append((text, clean_target))

        if refs_dir.exists():
            if not self.generic and len(ref_links) < 3:
                self.log_failure("Reference Linking", f"Expected >= 3 links from SKILL.md to references/, found {len(ref_links)}", skill_md)

            skill_linked_files = {Path(t).name for _, t in ref_links}
            ledger_path = refs_dir / "evidence_ledger.md"
            ledger_text = ledger_path.read_text(encoding="utf-8") if (not self.generic and ledger_path.exists()) else ""

            for ref_file in sorted(refs_dir.rglob("*.md")):
                if ref_file.parent != refs_dir:
                    rel_nested = ref_file.relative_to(self.root)
                    self.log_failure("Reference Linking", f"Nested reference file exceeds one-level depth under references/: {rel_nested}", ref_file)
                    continue

                if self.generic:
                    is_linked = ref_file.name in skill_linked_files
                else:
                    is_linked = (ref_file.name in skill_linked_files) or (ref_file.name in ledger_text) or (ref_file.name == "evidence_ledger.md")
                if not is_linked:
                    self.log_failure("Reference Linking", f"Orphaned reference file not linked anywhere: {ref_file.name}", ref_file)

                ref_content = self._strip_code_from_markdown(ref_file.read_text(encoding="utf-8"))
                ref_links_in_doc = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", ref_content)
                for ltext, ltarget in ref_links_in_doc:
                    if ltarget.startswith(("http://", "https://", "mailto:", "#")):
                        continue
                    clean_l = ltarget.split("#", 1)[0].strip()
                    if not clean_l:
                        continue
                    if "\\" in clean_l:
                        self.log_failure("Reference Linking", f"Link in {ref_file.name} uses non-portable backslash separator: {ltarget}", ref_file)
                        continue
                    if self._is_absolute_link(clean_l):
                        self.log_failure("Reference Linking", f"Absolute path link in {ref_file.name}: {ltarget}", ref_file)
                        continue
                    if "evidence/" in clean_l:
                        self.log_failure("Reference Linking", f"Relative link to repo-level evidence/ in {ref_file.name}: {ltarget} (use canonical GitHub URL)", ref_file)
                        continue
                    resolved_ref = (ref_file.parent / clean_l).resolve()
                    try:
                        resolved_ref.relative_to(self.root)
                    except ValueError:
                        self.log_failure("Reference Linking", f"Relative link escapes skill root in {ref_file.name}: {ltarget}", ref_file)
                        continue
                    if not resolved_ref.exists():
                        self.log_failure("Reference Linking", f"Broken relative link in {ref_file.name}: [{ltext}]({ltarget})", ref_file)

        self.log_if_clean(err_before, "Single-Hop Reference Linking Invariants")

    def verify_evidence_ledger_tiers(self) -> None:
        """Verify that every rule ID in evidence_ledger.md uses the T1-T5/Methodology/Convention/Contested tier system."""
        if self.generic:
            return
        err_before = len(self.errors)
        ledger_path = self.root / "references" / "evidence_ledger.md"
        if not ledger_path.exists():
            self.log_failure("Evidence Ledger", "references/evidence_ledger.md missing", ledger_path)
            return

        text = ledger_path.read_text(encoding="utf-8")
        if "Grade A" in text or "Grade B" in text:
            self.log_failure("Evidence Ledger", "Legacy 'Grade A' or 'Grade B' vocabulary found in evidence_ledger.md", ledger_path)

        row_tiers: Dict[str, str] = {}
        duplicate_rules: List[str] = []
        for line in text.splitlines():
            if not line.startswith("| **R-"):
                continue
            cols = [c.strip() for c in line.strip("|").split("|")]
            if len(cols) >= 4:
                rid = cols[0].strip("* ")
                tier = cols[3].strip("* ")
                if rid in row_tiers:
                    duplicate_rules.append(rid)
                row_tiers[rid] = tier

        if duplicate_rules:
            self.log_failure("Evidence Ledger", f"Duplicate rule IDs in ledger table: {sorted(set(duplicate_rules))}", ledger_path)

        missing_rules = [rid for rid in EXPECTED_RULE_IDS if rid not in row_tiers]
        if missing_rules:
            self.log_failure("Evidence Ledger", f"Missing expected rule IDs in ledger table: {missing_rules}", ledger_path)

        unexpected_rules = sorted(set(row_tiers.keys()) - set(EXPECTED_RULE_IDS))
        if unexpected_rules:
            self.log_failure("Evidence Ledger", f"Unexpected rule IDs in ledger table: {unexpected_rules}", ledger_path)

        for rid, tier in row_tiers.items():
            if tier not in ALLOWED_TIERS:
                self.log_failure("Evidence Ledger", f"Rule {rid} has invalid tier '{tier}' (expected one of {sorted(ALLOWED_TIERS)})", ledger_path)

        self.log_if_clean(err_before, "Evidence Ledger Tier Vocabulary")

    def _has_structural_constraint(self, schema_obj: Any) -> bool:
        """Return True when a property schema (or anyOf branch) declares a structural JSON Schema constraint."""
        if not isinstance(schema_obj, dict):
            return False
        constraint_keys = {
            "minimum",
            "maximum",
            "exclusiveMinimum",
            "exclusiveMaximum",
            "multipleOf",
            "minItems",
            "maxItems",
            "pattern",
            "format",
            "enum",
        }
        if any(k in schema_obj for k in constraint_keys):
            return True
        for branch in schema_obj.get("anyOf") or []:
            if self._has_structural_constraint(branch):
                return True
        return False

    def _validate_openai_strict_tool(self, tool_tmpl: Path, expect_rationale_first: bool) -> None:
        """Validate OpenAI Chat Completions strict tool template invariants."""
        if not tool_tmpl.exists():
            self.log_failure("Templates", f"{tool_tmpl.name} missing", tool_tmpl)
            return
        raw_tool_txt = tool_tmpl.read_text(encoding="utf-8")
        if LEAKED_INTERNAL_RULE_RE.search(raw_tool_txt) or "references/" in raw_tool_txt:
            self.log_failure("Templates", f"{tool_tmpl.name} leaks internal rule IDs or references/ paths into runtime tool descriptions", tool_tmpl)
        try:
            wrapper = json.loads(raw_tool_txt)
        except json.JSONDecodeError as e:
            self.log_failure("Templates", f"{tool_tmpl.name} is not valid JSON: {e}", tool_tmpl)
            return

        if wrapper.get("type") != "function" or not isinstance(wrapper.get("function"), dict):
            self.log_failure("Templates", f"{tool_tmpl.name} must use valid OpenAI wire shape {{'type': 'function', 'function': {{...}}}}", tool_tmpl)
            return
        fn = wrapper["function"]
        if not isinstance(fn.get("name"), str) or not SNAKE_CASE_PATTERN.match(fn["name"]):
            self.log_failure("Templates", f"function.name in {tool_tmpl.name} must be snake_case", tool_tmpl)
        if fn.get("strict") is not True:
            self.log_failure("Templates", f"function.strict must be true in OpenAI strict {tool_tmpl.name}", tool_tmpl)
        params = fn.get("parameters")
        if not isinstance(params, dict) or params.get("type") != "object":
            self.log_failure("Templates", f"function.parameters in {tool_tmpl.name} must be an object schema", tool_tmpl)
            return
        if params.get("additionalProperties", True) is not False:
            self.log_failure("Templates", f"function.parameters in {tool_tmpl.name} must specify additionalProperties: false", tool_tmpl)
        prop_map = params.get("properties") or {}
        props = list(prop_map.keys())
        reqs = set(params.get("required") or [])
        if not props or set(props) != reqs:
            self.log_failure("Templates", f"OpenAI strict tool schema {tool_tmpl.name} requires all properties in 'required'. Props: {set(props)}, Req: {reqs}", tool_tmpl)
        if len(props) < 2:
            self.log_failure("Templates", f"Tool schema {tool_tmpl.name} has {len(props)} properties; expected >= 2", tool_tmpl)
        else:
            if expect_rationale_first:
                if props[0].lower() != "rationale":
                    self.log_failure("Templates", f"Zero-reasoning template {tool_tmpl.name} must place 'rationale' first (got '{props[0]}').", tool_tmpl)
            else:
                bad_keys = [p for p in props if p.lower() in {"rationale", "thought", "reason"}]
                if bad_keys:
                    self.log_failure("Templates", f"Default template {tool_tmpl.name} must omit {bad_keys} for standard reasoning models.", tool_tmpl)
                if not any(self._has_structural_constraint(pschema) for pschema in prop_map.values()):
                    self.log_failure("Templates", f"Default template {tool_tmpl.name} should demonstrate structural JSON Schema constraints.", tool_tmpl)
        for prop_name in props:
            if not SNAKE_CASE_PATTERN.match(prop_name):
                self.log_failure("Templates", f"Property '{prop_name}' in {tool_tmpl.name} is not snake_case", tool_tmpl)

    def verify_templates(self) -> None:
        """Verify starter templates have clean runtime formatting and zero leaked internal notes."""
        if self.generic:
            return
        err_before = len(self.errors)
        templates_dir = self.root / "assets" / "templates"
        sys_tmpl = templates_dir / "system_prompt_template.md"
        legacy_xml = templates_dir / "system_prompt_template.xml"
        skill_tmpl = templates_dir / "skill_template.md"
        tool_tmpl = templates_dir / "tool_schema_template.json"
        tool_zero_tmpl = templates_dir / "tool_schema_zero_reasoning_template.json"

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
            if LEAKED_INTERNAL_RULE_RE.search(md_content):
                self.log_failure("Templates", "system_prompt_template.md leaks internal agent-system-authoring rule IDs (R-SYS/TOOL/SKILL)", sys_tmpl)

        if not skill_tmpl.exists():
            self.log_failure("Templates", "assets/templates/skill_template.md missing", skill_tmpl)
        else:
            sk_text = skill_tmpl.read_text(encoding="utf-8")
            if LEAKED_INTERNAL_RULE_RE.search(sk_text):
                self.log_failure("Templates", "skill_template.md leaks internal agent-system-authoring rule IDs (R-SYS/TOOL/SKILL)", skill_tmpl)

        self._validate_openai_strict_tool(tool_tmpl, expect_rationale_first=False)
        self._validate_openai_strict_tool(tool_zero_tmpl, expect_rationale_first=True)

        self.log_if_clean(err_before, "Assets Templates Validation")

    def verify_evals(self) -> None:
        """Verify evals/evals.json dual-axis triggering, comparative cases, and version sync."""
        evals_file = self.root / "evals" / "evals.json"
        if not evals_file.exists():
            if self.generic:
                return
            self.log_failure("Evals Schema", "evals/evals.json missing", evals_file)
            return

        err_before = len(self.errors)
        try:
            data = json.loads(evals_file.read_text(encoding="utf-8"))
            if self.generic:
                self.log_if_clean(err_before, "Evals JSON Syntax (--generic)")
                return
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
                elif eval_type in ("trigger_negative", "trigger_negative_none") or item.get("trigger") is False or item.get("should_trigger") is False:
                    negatives.append(item)
                elif eval_type == "comparative" or "comparative" in str(item_id) or str(item_id).startswith("comp_"):
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
            has_criteria = any(k in raw_text for k in ["rubric", "downstream", "judge", "criteria", "expected_output"])
            if not has_criteria:
                self.log_failure("Evals Schema", "Comparative evals must declare evaluation rubrics or downstream checks", evals_file)

            skill_md = self.root / "SKILL.md"
            if skill_md.exists():
                fm, _, _ = self.extract_frontmatter(skill_md.read_text(encoding="utf-8"))
                skill_ver = (fm.get("metadata") or {}).get("version") if isinstance(fm.get("metadata"), dict) else None
                eval_ver = data.get("version")
                if skill_ver and eval_ver and skill_ver != eval_ver:
                    self.log_failure("Evals Schema", f"Version mismatch: SKILL.md metadata.version='{skill_ver}' != evals.json version='{eval_ver}'", evals_file)

        except json.JSONDecodeError as e:
            self.log_failure("Evals Schema", f"evals/evals.json failed JSON parsing: {e}", evals_file)

        self.log_if_clean(err_before, "Evals Schema & Dual-Axis Test Suite")

    def verify_pep723_metadata(self) -> None:
        """Verify PEP 723 inline dependency metadata on utility and provenance scripts."""
        err_before = len(self.errors)
        script_targets: List[Path] = sorted((self.root / "scripts").glob("*.py")) if (self.root / "scripts").exists() else []
        if not self.generic:
            repo_evidence = self.root.parent.parent / "evidence"
            if repo_evidence.exists():
                script_targets.extend(sorted(repo_evidence.rglob("*.py")))

        if not script_targets:
            if self.generic:
                return
            self.log_failure("PEP 723 Metadata", "No Python scripts found under scripts/")
            return

        for script_path in script_targets:
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

        self.log_if_clean(err_before, "PEP 723 Dependency Metadata")

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
        description="Standalone stdlib-only Agent Skill Verifier (Agent Skills open specification)"
    )
    parser.add_argument(
        "target_dir",
        nargs="?",
        default=".",
        help="Path to the agent skill root directory to verify (default: current directory)",
    )
    parser.add_argument(
        "--generic",
        action="store_true",
        help="Run generic Agent Skills specification checks only (skip agent-system-authoring-specific ledger/template checks).",
    )
    args = parser.parse_args()

    target_path = Path(args.target_dir).resolve()
    verifier = SkillVerifier(target_path, generic=args.generic)
    mode_label = "generic" if verifier.generic else "agent-system-authoring"
    print(f"=== Verifying Agent Skill Package: {target_path} (mode: {mode_label}) ===")

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
