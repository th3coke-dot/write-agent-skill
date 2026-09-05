#!/usr/bin/env python3
"""Structural and CLI regression tests. These do not measure model activation."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import validate_skill as validator

VALIDATOR = ROOT / "scripts" / "validate_skill.py"
SCAFFOLDER = ROOT / "scripts" / "new_skill.py"
FIXTURES = ROOT / "tests" / "fixtures"


@contextmanager
def skill(frontmatter: str, body: str = "Count the words.\n"):
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "example-skill"
        path.mkdir()
        (path / "SKILL.md").write_text(
            "---\n" + frontmatter + "\n---\n\n" + body, encoding="utf-8"
        )
        yield path


def run(script: Path, *args):
    return subprocess.run(
        [sys.executable, str(script), *map(str, args)],
        capture_output=True, text=True,
    )


class SkillValidationTests(unittest.TestCase):
    def test_package_structure(self):
        self.assertEqual(validator.validate_skill_dir(ROOT), [])

    def test_valid_fixture(self):
        self.assertEqual(validator.validate_skill_dir(FIXTURES / "valid-skill"), [])

    def test_invalid_name_fixture_stays_invalid(self):
        errors = validator.validate_skill_dir(FIXTURES / "bad-name-uppercase")
        self.assertTrue(any("name" in error for error in errors))

    def test_unicode_names_follow_portable_format(self):
        self.assertEqual(validator.validate_name("beskriv-øvelse"), [])
        self.assertTrue(validator.validate_name("Beskriv-øvelse"))
        with tempfile.TemporaryDirectory() as directory:
            result = run(SCAFFOLDER, "--name", "beskriv-øvelse",
                         "--description", "Describe an exercise.", "--output", directory)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(validator.validate_skill_dir(Path(directory) / "beskriv-øvelse"), [])

    def test_weak_description_is_advisory_unless_style_is_required(self):
        path = FIXTURES / "bad-description"
        self.assertEqual(run(VALIDATOR, path).returncode, 0)
        result = run(VALIDATOR, path, "--strict-style")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("description", result.stderr)

    def test_clear_trigger_needs_no_magic_phrase(self):
        with skill("name: example-skill\ndescription: Counts words for word-count requests.") as path:
            self.assertEqual(run(VALIDATOR, path).returncode, 0)

    def test_description_bounds_and_types(self):
        for value in ("", "   ", "x" * 1025, None, False, 42):
            with self.subTest(value=repr(value)[:30]):
                self.assertTrue(validator.validate_description(value))
        self.assertEqual(validator.validate_description("x" * 1024), [])

    def test_yaml_folded_and_literal_descriptions(self):
        for style in (">", "|", ">-", "|-"):
            with self.subTest(style=style), skill(
                f"name: example-skill\ndescription: {style}\n  Counts words\n  for word-count requests."
            ) as path:
                self.assertEqual(validator.validate_skill_dir(path), [])

    def test_yaml_string_metadata(self):
        with skill(
            "name: example-skill\ndescription: Counts words for word-count requests.\n"
            'metadata: {version: "1", enabled: "true", compiled: "2026-09-05"}'
        ) as path:
            self.assertEqual(validator.validate_skill_dir(path), [])

    def test_metadata_types_are_not_coerced_to_strings(self):
        for value in ("true", "42", "1.5", "null", "2026-09-05", "[x]", "{nested: x}"):
            with self.subTest(value=value), skill(
                "name: example-skill\ndescription: Counts words for word-count requests.\n"
                f"metadata:\n  value: {value}"
            ) as path:
                self.assertTrue(any("metadata" in error for error in validator.validate_skill_dir(path)))

    def test_duplicate_keys_are_rejected(self):
        with skill(
            "name: example-skill\nname: different-skill\ndescription: Count words."
        ) as path:
            self.assertTrue(any("duplicate" in error for error in validator.validate_skill_dir(path)))

    def test_yaml_merge_keeps_explicit_values(self):
        fields, _, _ = validator.parse_frontmatter(
            "---\nname: example-skill\ndescription: Count words.\n"
            'metadata:\n  <<: {version: "1"}\n  version: "2"\n---\n'
        )
        self.assertEqual(fields["metadata"], {"version": "2"})

    def test_non_mapping_frontmatter_is_rejected(self):
        with skill("- name\n- description") as path:
            self.assertTrue(validator.validate_skill_dir(path))

    def test_non_string_keys_are_rejected(self):
        with skill("42: value\nname: example-skill\ndescription: Count words.") as path:
            self.assertTrue(validator.validate_skill_dir(path))

    def test_unsafe_yaml_tags_are_rejected(self):
        with skill(
            "name: example-skill\ndescription: !!python/object:builtins.object {}"
        ) as path:
            self.assertTrue(any("YAML" in error for error in validator.validate_skill_dir(path)))

    def test_unsupported_portable_field_is_rejected(self):
        with skill(
            "name: example-skill\ndescription: Count words.\npaths: /tmp"
        ) as path:
            self.assertTrue(any("paths" in error for error in validator.validate_skill_dir(path)))

    def test_malformed_yaml_is_reported(self):
        with skill("name: example-skill\ndescription: [unterminated") as path:
            result = run(VALIDATOR, path)
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn("Traceback", result.stderr)

    def test_required_and_optional_scalar_types(self):
        for extra in ('description: false', 'description: Count words.\nlicense: 42',
                      'description: Count words.\ncompatibility: []',
                      'description: Count words.\nallowed-tools: []'):
            with self.subTest(extra=extra), skill("name: example-skill\n" + extra) as path:
                self.assertTrue(validator.validate_skill_dir(path))

    def test_body_and_line_endings_survive_parsing(self):
        text = "\ufeff---\r\nname: example-skill\r\ndescription: Count words.\r\n---\r\n\r\nKeep this body.\r\n"
        _, body, lines = validator.parse_frontmatter(text)
        self.assertEqual(body, "\r\nKeep this body.\r\n")
        self.assertEqual(lines, 6)
        validator.parse_frontmatter("---\nname: example-skill\ndescription: Count words.\n---")

    def test_missing_closing_delimiter_is_rejected(self):
        with self.assertRaises(validator.SkillError):
            validator.parse_frontmatter("---\nname: example-skill\n")

    def test_entry_size_is_advisory(self):
        with skill(
            "name: example-skill\ndescription: Counts words for word-count requests.",
            body="Reference material.\n" * 501,
        ) as path:
            self.assertEqual(run(VALIDATOR, path).returncode, 0)
            self.assertNotEqual(run(VALIDATOR, path, "--strict-style").returncode, 0)

    def test_scaffolder_preserves_input_strings(self):
        for description in (
            "Counts words for word-count requests.",
            "Count words:\nkeep Unicode café and # symbols.",
            "Counts literal {title} and {name} for template requests.",
        ):
            with self.subTest(description=description), tempfile.TemporaryDirectory() as directory:
                result = run(
                    SCAFFOLDER, "--name", "example-skill",
                    "--description", description, "--output", directory,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                path = Path(directory) / "example-skill"
                fields, _, _ = validator.parse_frontmatter((path / "SKILL.md").read_text())
                self.assertEqual(fields["description"], description)
                self.assertEqual(validator.validate_skill_dir(path), [])

    def test_scaffolder_refuses_to_overwrite_existing_package(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example-skill"
            path.mkdir()
            sentinel = path / "SKILL.md"
            sentinel.write_text("Existing work.\n")
            result = run(SCAFFOLDER, "--name", "example-skill",
                         "--description", "Count words.", "--output", directory)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(sentinel.read_text(), "Existing work.\n")

    def test_scaffolder_rejects_bad_name_before_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            result = run(SCAFFOLDER, "--name", "BadName",
                         "--description", "Count words.", "--output", directory)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_scaffolder_can_omit_license(self):
        with tempfile.TemporaryDirectory() as directory:
            result = run(SCAFFOLDER, "--name", "example-skill",
                         "--description", "Count words.", "--license", "", "--output", directory)
            self.assertEqual(result.returncode, 0, result.stderr)
            fields, _, _ = validator.parse_frontmatter(
                (Path(directory) / "example-skill" / "SKILL.md").read_text()
            )
            self.assertNotIn("license", fields)


if __name__ == "__main__":
    unittest.main(verbosity=2)
