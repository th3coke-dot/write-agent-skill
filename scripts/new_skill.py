#!/usr/bin/env python3
"""Scaffold a spec-valid empty Agent Skill directory.

Usage:
  python3 scripts/new_skill.py --name my-skill --description "Does X. Use when Y."
  python3 scripts/new_skill.py --name my-skill --description "..." --output /tmp
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from validate_skill import validate_description, validate_name, validate_skill_dir

DEFAULT_LICENSE = "MIT"

BUILTIN_TEMPLATE = """---
name: {name}
description: {description}
{license_block}---

# {title}

## Job

One verb family. Replace this body with the steps for that job.

## When to use

Trigger phrases belong in the YAML `description` (always loaded). Repeat them
here only if the activated agent needs extra examples.

## Steps

1. Do the job.
2. Handle the edge cases below.
3. Stop. Do not add a second job.

## Edge cases

- Missing input
- Invalid input
"""


def yaml_scalar(value: str) -> str:
    """Quote a string when YAML would otherwise misread it."""
    needs_quote = (
        not value
        or value != value.strip()
        or value[0] in "-?:@&*!|>%'\"{}[]#"
        or any(c in value for c in ":#{}[]&*?|>!%@`'")
        or value.lower() in {"true", "false", "null", "yes", "no"}
    )
    if needs_quote:
        return json.dumps(value, ensure_ascii=False)
    return value


def title_from_name(name: str) -> str:
    return name.replace("-", " ").capitalize()


def load_template(pack_root: Path) -> str:
    candidate = pack_root / "assets" / "SKILL.template.md"
    if candidate.is_file():
        text = candidate.read_text(encoding="utf-8")
        # Use the bundled template only if it still has placeholders.
        if "{name}" in text and "{description}" in text:
            return text
    return BUILTIN_TEMPLATE


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Scaffold a spec-valid empty Agent Skill directory."
    )
    parser.add_argument("--name", required=True, help="Skill name / folder name")
    parser.add_argument(
        "--description",
        required=True,
        help="WHAT it does AND WHEN to use it (trigger text, not marketing)",
    )
    parser.add_argument(
        "--output",
        default=".",
        help="Parent directory for the new skill folder (default: cwd)",
    )
    parser.add_argument(
        "--license",
        default=DEFAULT_LICENSE,
        help=f"Optional license field (default: {DEFAULT_LICENSE}; pass empty to omit)",
    )
    args = parser.parse_args(argv)

    errors = validate_name(args.name) + validate_description(args.description)
    if errors:
        for err in errors:
            print(f"ERROR: {err}", file=sys.stderr)
        return 1

    dest = Path(args.output).expanduser().resolve() / args.name
    if dest.exists():
        print(f"ERROR: destination already exists: {dest}", file=sys.stderr)
        return 1

    pack_root = Path(__file__).resolve().parent.parent
    template = load_template(pack_root)
    license_value = (args.license or "").strip()
    if license_value:
        license_block = f"license: {yaml_scalar(license_value)}\n"
    else:
        license_block = ""

    replacements = {
        "{name}": args.name,
        "{description}": yaml_scalar(args.description),
        "{license_block}": license_block,
        "{title}": title_from_name(args.name),
    }
    text = template
    for key, val in replacements.items():
        text = text.replace(key, val)

    dest.mkdir(parents=True)
    (dest / "SKILL.md").write_text(text, encoding="utf-8")

    post = validate_skill_dir(dest)
    if post:
        print("ERROR: scaffolded skill failed validation:", file=sys.stderr)
        for err in post:
            print(f"ERROR: {err}", file=sys.stderr)
        return 1

    print(dest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
