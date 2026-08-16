#!/usr/bin/env python3
"""Validate an Agent Skill directory against the agentskills.io spec (2026-08-16).

Official source: https://agentskills.io/specification
Official command: skills-ref validate ./my-skill

This script is a self-contained checker so the pack works without skills-ref.
Exit 0 only if the skill is valid. Usage: validate_skill.py <skill-dir>
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ALLOWED_FIELDS = {
    "name",
    "description",
    "license",
    "compatibility",
    "metadata",
    "allowed-tools",
}

# Cursor-only / invented keys we call out by name when rejected.
UNOFFICIAL_FIELDS = {"paths", "disable-model-invocation"}

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
WHEN_RE = re.compile(
    r"(?i)\b("
    r"use when|use if|use this skill when|"
    r"when the user|when asked|when working|when handling|"
    r"when you\b|trigger phrases?"
    r")\b"
)
HELPS_WITH_RE = re.compile(r"(?i)^helps with\b")
MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


class SkillError(Exception):
    pass


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        inner = value[1:-1]
        if value[0] == '"':
            inner = (
                inner.replace(r"\"", '"')
                .replace(r"\n", "\n")
                .replace(r"\\", "\\")
            )
        return inner
    return value


def parse_frontmatter(text: str) -> tuple[dict, str, int]:
    """Return (fields, body, total_lines). Raises SkillError on structural issues."""
    if text.startswith("\ufeff"):
        text = text[1:]
    if not text.startswith("---"):
        raise SkillError("SKILL.md must start with YAML frontmatter delimited by ---")

    rest = text[3:]
    if rest.startswith("\r\n"):
        rest = rest[2:]
    elif rest.startswith("\n"):
        rest = rest[1:]
    else:
        raise SkillError("SKILL.md opening --- must be on its own line")

    closer = re.search(r"\n---[ \t]*\r?\n", rest)
    if not closer:
        # allow EOF closer
        closer = re.search(r"\n---[ \t]*\s*$", rest)
    if not closer:
        raise SkillError("SKILL.md frontmatter is not closed with ---")

    yaml_text = rest[: closer.start()]
    body = rest[closer.end() :]
    total_lines = text.count("\n") + (0 if text.endswith("\n") else 1)

    fields: dict = {}
    in_metadata = False
    metadata: dict = {}

    for raw_line in yaml_text.splitlines():
        if not raw_line.strip() or raw_line.strip().startswith("#"):
            continue

        if in_metadata:
            if raw_line.startswith(" ") or raw_line.startswith("\t"):
                m = re.match(r"^[ \t]+([^:]+):(.*)$", raw_line)
                if not m:
                    raise SkillError(f"cannot parse metadata line: {raw_line!r}")
                key = m.group(1).strip()
                val = _unquote(m.group(2))
                if not key:
                    raise SkillError("metadata keys must be non-empty strings")
                metadata[key] = val
                continue
            in_metadata = False
            fields["metadata"] = metadata
            metadata = {}

        m = re.match(r"^([A-Za-z0-9_-]+):(.*)$", raw_line)
        if not m:
            raise SkillError(f"cannot parse frontmatter line: {raw_line!r}")
        key = m.group(1)
        val = m.group(2).strip()
        if key == "metadata" and val == "":
            in_metadata = True
            metadata = {}
            continue
        fields[key] = _unquote(val)

    if in_metadata:
        fields["metadata"] = metadata

    return fields, body, total_lines


def validate_name(name: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(name, str) or not name:
        return ["name is required and must be a non-empty string"]
    if len(name) < 1 or len(name) > 64:
        errors.append(f"name must be 1-64 characters (got {len(name)})")
    if name.startswith("-") or name.endswith("-"):
        errors.append("name must not start or end with a hyphen")
    if "--" in name:
        errors.append("name must not contain consecutive hyphens (--)")
    if not NAME_RE.match(name):
        errors.append(
            "name must match [a-z0-9-], lowercase only, no leading/trailing "
            "hyphen, no consecutive hyphens"
        )
    return errors


def validate_description(description: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(description, str):
        return ["description is required and must be a string"]
    desc = description.strip()
    if not desc:
        return ["description is required and must be non-empty"]
    if len(desc) > 1024:
        errors.append(f"description must be 1-1024 characters (got {len(desc)})")
    if HELPS_WITH_RE.search(desc) and not WHEN_RE.search(desc):
        errors.append(
            "description looks like marketing ('Helps with X.'); write trigger "
            "text that says WHAT the skill does AND WHEN to use it"
        )
    elif not WHEN_RE.search(desc):
        errors.append(
            "description must say WHAT the skill does AND WHEN to use it "
            "(include 'use when' or equivalent trigger language)"
        )
    return errors


def _check_file_refs(body: str) -> list[str]:
    errors: list[str] = []
    for match in MD_LINK_RE.finditer(body):
        href = match.group(1).strip()
        if not href or href.startswith(("#", "http://", "https://", "mailto:")):
            continue
        href = href.split(" ", 1)[0]
        parts = Path(href).parts
        if len(parts) > 2:
            errors.append(
                f"file reference {href!r} is more than one level deep from SKILL.md"
            )
    return errors


def validate_skill_dir(skill_dir: str | Path) -> list[str]:
    errors: list[str] = []
    path = Path(skill_dir).expanduser()
    if not path.exists():
        return [f"skill directory does not exist: {path}"]
    if not path.is_dir():
        return [f"not a directory: {path}"]

    skill_md = path / "SKILL.md"
    if not skill_md.is_file():
        return [f"missing required file: {skill_md}"]

    text = skill_md.read_text(encoding="utf-8")
    try:
        fields, body, total_lines = parse_frontmatter(text)
    except SkillError as exc:
        return [str(exc)]

    if total_lines > 500:
        errors.append(
            f"SKILL.md has {total_lines} lines; keep it under 500 "
            "(progressive disclosure: move detail to references/)"
        )

    unknown = [k for k in fields if k not in ALLOWED_FIELDS]
    for key in unknown:
        if key in UNOFFICIAL_FIELDS:
            errors.append(
                f"unknown frontmatter field {key!r}: unofficial/client-specific, "
                "not in the agentskills.io spec (2026-08-16)"
            )
        else:
            errors.append(
                f"unknown frontmatter field {key!r}: not in the agentskills.io spec"
            )

    if "name" not in fields:
        errors.append("missing required frontmatter field: name")
    else:
        errors.extend(validate_name(fields["name"]))
        dirname = path.resolve().name
        if fields["name"] != dirname:
            errors.append(
                f"name {fields['name']!r} must match parent directory name {dirname!r}"
            )

    if "description" not in fields:
        errors.append("missing required frontmatter field: description")
    else:
        errors.extend(validate_description(fields["description"]))

    if "compatibility" in fields:
        compat = fields["compatibility"]
        if not isinstance(compat, str) or not compat.strip():
            errors.append("compatibility must be 1-500 characters if present")
        elif len(compat) > 500:
            errors.append(
                f"compatibility must be 1-500 characters if present (got {len(compat)})"
            )

    if "metadata" in fields:
        meta = fields["metadata"]
        if not isinstance(meta, dict):
            errors.append("metadata must be a map of string keys to string values")
        else:
            for k, v in meta.items():
                if not isinstance(k, str) or not k:
                    errors.append("metadata keys must be non-empty strings")
                if not isinstance(v, str):
                    errors.append(
                        f"metadata[{k!r}] must be a string (spec: string keys to string values)"
                    )

    if "allowed-tools" in fields:
        tools = fields["allowed-tools"]
        if not isinstance(tools, str) or not tools.strip():
            errors.append("allowed-tools must be a non-empty space-separated string")

    if "license" in fields and not str(fields["license"]).strip():
        errors.append("license, if present, must be a non-empty string")

    errors.extend(_check_file_refs(body))
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate an Agent Skill directory (agentskills.io spec, 2026-08-16)."
    )
    parser.add_argument("skill_dir", help="Path to the skill directory (contains SKILL.md)")
    args = parser.parse_args(argv)

    errors = validate_skill_dir(args.skill_dir)
    if errors:
        for err in errors:
            print(f"ERROR: {err}", file=sys.stderr)
        print(f"{len(errors)} error(s)", file=sys.stderr)
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
