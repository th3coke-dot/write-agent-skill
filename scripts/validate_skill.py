#!/usr/bin/env python3
"""Validate portable Agent Skill frontmatter; report house style separately.

Install requirements.txt before use. Structural validity is not a model
activation or behavioral-quality guarantee. See references/SPEC.md.
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path

try:
    import yaml
except ImportError:
    raise SystemExit(
        "ERROR: PyYAML is required; install this pack's requirements.txt."
    )

ALLOWED_FIELDS = {
    "name", "description", "license", "compatibility", "metadata", "allowed-tools"
}
HELPS_WITH_RE = re.compile(r"(?i)^helps with\b")
MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


class SkillError(Exception):
    pass


class FrontmatterLoader(yaml.SafeLoader):
    """Safe YAML with explicit rejection of ambiguous duplicate keys."""


def _mapping(loader, node, deep=False):
    seen = set()
    for key_node, _ in node.value:
        if key_node.tag == "tag:yaml.org,2002:merge":
            continue
        key = loader.construct_object(key_node, deep=deep)
        if not isinstance(key, str):
            raise yaml.constructor.ConstructorError(
                None, None, "frontmatter mapping keys must be strings", key_node.start_mark
            )
        if key in seen:
            raise yaml.constructor.ConstructorError(
                None, None, f"duplicate frontmatter key: {key}", key_node.start_mark
            )
        seen.add(key)
    loader.flatten_mapping(node)
    result = yaml.SafeLoader.construct_mapping(loader, node, deep=deep)
    if any(not isinstance(key, str) for key in result):
        raise yaml.constructor.ConstructorError(
            None, None, "frontmatter mapping keys must be strings", node.start_mark
        )
    return result


FrontmatterLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapping
)


def parse_frontmatter(text: str) -> tuple[dict, str, int]:
    """Parse YAML without losing scalar types; keep the Markdown body intact."""
    text = text.removeprefix("\ufeff")
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].rstrip("\r\n").rstrip(" \t") != "---":
        raise SkillError("SKILL.md must start with --- on its own line")
    closing = next(
        (i for i, line in enumerate(lines[1:], 1)
         if line.rstrip("\r\n").rstrip(" \t") == "---"),
        None,
    )
    if closing is None:
        raise SkillError("SKILL.md frontmatter is not closed with ---")
    try:
        fields = yaml.load("".join(lines[1:closing]), Loader=FrontmatterLoader)
    except yaml.YAMLError as exc:
        raise SkillError(f"invalid YAML frontmatter: {exc}") from exc
    if not isinstance(fields, dict):
        raise SkillError("frontmatter must be a mapping")
    return fields, "".join(lines[closing + 1:]), len(lines)


def validate_name(name: str) -> list[str]:
    if not isinstance(name, str) or not name:
        return ["name is required and must be a non-empty string"]
    name = unicodedata.normalize("NFKC", name)
    errors = []
    if len(name) > 64:
        errors.append(f"name must be 1-64 characters (got {len(name)})")
    if (name != name.lower() or name.startswith("-") or name.endswith("-")
            or "--" in name or not all(c.isalnum() or c == "-" for c in name)):
        errors.append(
            "name must contain lowercase Unicode letters, digits or hyphens, with no leading, trailing "
            "or consecutive hyphens"
        )
    return errors


def validate_description(description: str) -> list[str]:
    if not isinstance(description, str) or not description.strip():
        return ["description is required and must be a non-empty string"]
    if len(description) > 1024:
        return [f"description must be 1-1024 characters (got {len(description)})"]
    return []


def validate_skill_dir(skill_dir: str | Path) -> list[str]:
    path = Path(skill_dir).expanduser()
    if not path.is_dir():
        return [f"skill directory does not exist or is not a directory: {path}"]
    skill_md = path / "SKILL.md"
    if not skill_md.is_file():
        return [f"missing required file: {skill_md}"]
    try:
        fields, _, _ = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
    except (SkillError, OSError, UnicodeError) as exc:
        return [str(exc)]

    errors = []
    for key in fields:
        if key not in ALLOWED_FIELDS:
            errors.append(f"unsupported portable frontmatter field: {key}")
    errors.extend(validate_name(fields.get("name")))
    if isinstance(fields.get("name"), str) and (
        unicodedata.normalize("NFKC", fields["name"])
        != unicodedata.normalize("NFKC", path.resolve().name)
    ):
        errors.append(
            f"name {fields['name']!r} must match parent directory name {path.resolve().name!r}"
        )
    errors.extend(validate_description(fields.get("description")))

    for field in ("license", "compatibility", "allowed-tools"):
        if field in fields:
            value = fields[field]
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{field} must be a non-empty string")
            elif field == "compatibility" and len(value) > 500:
                errors.append("compatibility must be 1-500 characters")
    if "metadata" in fields:
        metadata = fields["metadata"]
        if not isinstance(metadata, dict):
            errors.append("metadata must be a map of string keys to string values")
        else:
            for key, value in metadata.items():
                if not isinstance(key, str) or not isinstance(value, str):
                    errors.append(f"metadata[{key!r}] must have a string key and value")
    return errors


def style_warnings(skill_dir: str | Path) -> list[str]:
    try:
        fields, body, total_lines = parse_frontmatter(
            (Path(skill_dir).expanduser() / "SKILL.md").read_text(encoding="utf-8")
        )
    except (SkillError, OSError, UnicodeError):
        return []
    warnings = []
    description = fields.get("description")
    if isinstance(description, str) and HELPS_WITH_RE.search(description.strip()):
        warnings.append(
            "description is generic; review whether it conveys a specific job and trigger"
        )
    if total_lines > 500:
        warnings.append(
            f"SKILL.md has {total_lines} lines; consider moving conditional detail to references"
        )
    for match in MD_LINK_RE.finditer(body):
        href = match.group(1).strip()
        if not href or href.startswith(("#", "http://", "https://", "mailto:")):
            continue
        href = href.split(" ", 1)[0].split("#", 1)[0]
        if len(Path(href).parts) > 2:
            warnings.append(f"deep reference path {href!r}; keep needed detail discoverable")
    return warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill_dir", help="Path to the skill directory")
    parser.add_argument(
        "--strict-style", action="store_true",
        help="Also fail on advisory house-style warnings",
    )
    args = parser.parse_args(argv)
    errors = validate_skill_dir(args.skill_dir)
    warnings = style_warnings(args.skill_dir)
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)
    if errors or (args.strict_style and warnings):
        return 1
    print("OK (structure only; activation and behavior are not evaluated)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
