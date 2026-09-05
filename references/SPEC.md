# Agent Skills format and local validation

Source: [Agent Skills specification](https://agentskills.io/specification), checked 2026-09-05.

## Portable frontmatter

Use YAML frontmatter between opening and closing `---` lines, followed by the instructions.

| Field | Format |
| --- | --- |
| name | Required string, 1–64 lowercase letters/numbers/hyphens; no leading, trailing or consecutive hyphens; match the folder name. |
| description | Required non-empty string, at most 1024 characters. Explain purpose and relevant requests without a required phrase formula. |
| license | Optional non-empty string naming a license or license file. |
| compatibility | Optional string, 1–500 characters, describing actual runtime requirements. |
| metadata | Optional mapping with string keys and string values. Quote dates, numbers and booleans when they are intended as strings. |
| allowed-tools | Optional non-empty space-separated string; experimental and client-dependent. |

This pack targets the portable fields above. Client extensions require the target client's documentation; the portable validator reports unsupported keys. Do not invent fields.

Folded/literal block strings, quoted strings and inline mappings are valid YAML. The bundled parser uses PyYAML's safe loader with duplicate-key rejection. It preserves value types rather than converting everything to text.

## Instructions and references

Keep essential instructions in `SKILL.md`. Put substantial conditional detail in directly discoverable references and repeatable operations in scripts. The specification's size and reference-depth guidance helps context use; it is not a substitute for judging relevance.

## Validation boundaries

Install `requirements.txt`, then run:

```bash
python3 scripts/validate_skill.py ./my-skill
```

Format errors fail validation. Weak generic descriptions, entry files over 500 lines and deep reference paths produce house-style warnings. They fail only with `--strict-style`. Neither structural checks nor style heuristics prove that a model will select or successfully use a skill.

For an additional structural check, use the official reference library when installed:

```bash
skills-ref validate ./my-skill
```

Review trigger relevance and observe representative behavior separately. Keep intentionally invalid fixtures as test data rather than installing them.
