"""Unit tests for skills/agent-system-authoring/scripts/verify_skill.py."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_ROOT = REPO_ROOT / "skills" / "agent-system-authoring"
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

import verify_skill as vs  # noqa: E402


class TestVerifySkillLivePackage(unittest.TestCase):
    def test_shipped_skill_passes_strict_and_generic(self) -> None:
        v_strict = vs.SkillVerifier(SKILL_ROOT, generic=False)
        self.assertTrue(v_strict.run_all(), msg=[str(e) for e in v_strict.errors])
        self.assertFalse(v_strict.generic)

        v_generic = vs.SkillVerifier(SKILL_ROOT, generic=True)
        self.assertTrue(v_generic.run_all(), msg=[str(e) for e in v_generic.errors])
        self.assertTrue(v_generic.generic)


class TestVerifySkillSecurityAndEdgeCases(unittest.TestCase):
    def _make_minimal_skill(self, base: Path, name: str = "demo-skill", body: str = "# Demo\nBody line.\n", extra_fm: str = "") -> Path:
        skill_dir = base / name
        skill_dir.mkdir(parents=True, exist_ok=True)
        fm = f"---\nname: {name}\ndescription: Runs a focused workflow. Use when auditing demo inputs.\n{extra_fm}---\n\n{body}"
        (skill_dir / "SKILL.md").write_text(fm, encoding="utf-8", newline="\n")
        return skill_dir

    def test_rejects_absolute_and_backslash_link_escapes_in_skill_md(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            outside = td_path / "outside.txt"
            outside.write_text("secret", encoding="utf-8")

            # POSIX / platform absolute path
            d_abs = self._make_minimal_skill(td_path, "abs-skill", f"# Demo\nSee [out]({outside.as_posix()}).\n")
            v_abs = vs.SkillVerifier(d_abs, generic=True)
            self.assertFalse(v_abs.run_all())
            self.assertTrue(any("absolute path" in e.message.lower() for e in v_abs.errors))

            # Explicit Windows drive path
            d_drv = self._make_minimal_skill(td_path, "drv-skill", "# Demo\nSee [win](C:/Windows/win.ini).\n")
            v_drv = vs.SkillVerifier(d_drv, generic=True)
            self.assertFalse(v_drv.run_all())
            self.assertTrue(any("absolute path" in e.message.lower() for e in v_drv.errors))

            # Windows backslash parent traversal
            d_bs = self._make_minimal_skill(td_path, "bs-skill", r"# Demo" + "\n" + r"See [up](..\outside.txt)." + "\n")
            v_bs = vs.SkillVerifier(d_bs, generic=True)
            self.assertFalse(v_bs.run_all())
            self.assertTrue(any("backslash" in e.message.lower() for e in v_bs.errors))

    def test_ignores_markdown_links_inside_fenced_and_inline_code(self) -> None:
        body = (
            "# Demo\n"
            "Inline example `[fake](references/missing_inline.md)` should not fail.\n\n"
            "```markdown\n"
            "- [Example](references/missing_block.md)\n"
            "```\n"
        )
        with tempfile.TemporaryDirectory() as td:
            d = self._make_minimal_skill(Path(td), "code-links-skill", body=body)
            v = vs.SkillVerifier(d, generic=True)
            self.assertTrue(v.run_all(), msg=[str(e) for e in v.errors])

    def test_rejects_env_key_files_and_shell_secrets(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            d = self._make_minimal_skill(Path(td), "secret-skill")
            (d / ".env").write_text("OPENAI_API_KEY=sk-1234567890abcdefghijklmnop\n", encoding="utf-8")
            (d / ".env.local").write_text("FOO=bar\n", encoding="utf-8")
            (d / "private.pem").write_text("dummy\n", encoding="utf-8")
            (d / "scripts").mkdir()
            (d / "scripts" / "deploy.sh").write_text(
                "curl -H 'Authorization: Bearer token_1234567890abcdefghij' https://192.168.1.50:8080\n",
                encoding="utf-8",
            )
            v = vs.SkillVerifier(d, generic=True)
            self.assertFalse(v.run_all())
            msgs = "\n".join(str(e) for e in v.errors)
            self.assertIn(".env", msgs)
            self.assertIn(".env.local", msgs)
            self.assertIn("private.pem", msgs)
            self.assertIn("deploy.sh", msgs)

    def test_allows_clean_env_example_template(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            d = self._make_minimal_skill(Path(td), "env-tmpl-skill")
            (d / ".env.example").write_text("API_KEY=replace_me\n", encoding="utf-8")
            v = vs.SkillVerifier(d, generic=True)
            self.assertTrue(v.run_all(), msg=[str(e) for e in v.errors])

    def test_rejects_nested_references_subdirectories(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            d = self._make_minimal_skill(
                Path(td),
                "deep-ref-skill",
                body="# Demo\nSee [deep](references/sub/deep.md).\n",
            )
            (d / "references" / "sub").mkdir(parents=True)
            (d / "references" / "sub" / "deep.md").write_text("# Deep\n", encoding="utf-8")
            v = vs.SkillVerifier(d, generic=True)
            self.assertFalse(v.run_all())
            self.assertTrue(any("one-level depth" in e.message.lower() for e in v.errors))

    def test_generic_mode_does_not_exempt_unlinked_evidence_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            d = self._make_minimal_skill(Path(td), "orphan-ledger-skill")
            (d / "references").mkdir()
            (d / "references" / "evidence_ledger.md").write_text("# Orphan\n", encoding="utf-8")
            v = vs.SkillVerifier(d, generic=True)
            self.assertFalse(v.run_all())
            self.assertTrue(any("Orphaned reference file" in e.message for e in v.errors))

    def test_rejects_unknown_top_level_frontmatter_keys(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            d = self._make_minimal_skill(Path(td), "extra-fm-skill", extra_fm="version: 1.0.0\nauthor: dev\n")
            v = vs.SkillVerifier(d, generic=True)
            self.assertFalse(v.run_all())
            self.assertTrue(any("Unrecognized top-level frontmatter" in e.message for e in v.errors))

    def test_yaml_frontmatter_literal_folded_comments_and_lists(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            d = self._make_minimal_skill(Path(td), "yaml-test")
            v = vs.SkillVerifier(d, generic=True)
            sample = (
                "---\n"
                "name: yaml-test # trailing comment\n"
                "description: |\n"
                "  Line one.\n"
                "  Line two.\n"
                "license: \"MIT # keep hash in quotes\"\n"
                "metadata:\n"
                "  version: \"1.0.0\" # inline comment\n"
                "allowed-tools:\n"
                "  - Read\n"
                "  - Bash\n"
                "---\n\n# Body\n"
            )
            fm, _, _ = v.extract_frontmatter(sample)
            self.assertEqual(fm["name"], "yaml-test")
            self.assertEqual(fm["description"], "Line one.\nLine two.")
            self.assertEqual(fm["license"], "MIT # keep hash in quotes")
            self.assertEqual(fm["metadata"]["version"], "1.0.0")
            self.assertEqual(fm["allowed-tools"], ["Read", "Bash"])

    def test_structural_constraint_helper_supports_array_and_multipleof(self) -> None:
        v = vs.SkillVerifier(SKILL_ROOT, generic=True)
        self.assertTrue(v._has_structural_constraint({"type": "array", "minItems": 1}))
        self.assertTrue(v._has_structural_constraint({"type": "array", "maxItems": 10}))
        self.assertTrue(v._has_structural_constraint({"type": "integer", "multipleOf": 5}))
        self.assertFalse(v._has_structural_constraint({"type": "string", "description": "Plain text"}))


if __name__ == "__main__":
    unittest.main()
