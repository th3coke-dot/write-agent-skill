# Agent Skills spec notes (cited)

Source: https://agentskills.io/specification  
Consulted: 2026-08-16  
Also compared to the published source `docs/specification.mdx` in [agentskills/agentskills](https://github.com/agentskills/agentskills/blob/main/docs/specification.mdx).

These are short notes for authors, not a dump of the specification. Re-fetch the live page before arguing a field.

## Directory

A skill is a directory whose name matches `name`. Required file: `SKILL.md`. Optional conventional folders: `scripts/`, `references/`, `assets/`. Other files are allowed.

## SKILL.md

YAML frontmatter, then a markdown body. Frontmatter is delimited by `---` at the start of the file.

### Required fields

| Field | Constraints (spec, 2026-08-16) |
| --- | --- |
| `name` | 1–64 chars. Unicode lowercase alphanumeric `a-z` `0-9` and hyphens. No leading/trailing hyphen. No consecutive `--`. **Must match the parent directory name.** |
| `description` | 1–1024 chars, non-empty. Describes **what** the skill does **and when** to use it. Include keywords that help an agent match the task. |

Spec examples for `name`: `pdf-processing`, `data-analysis`, `code-review` are valid. `PDF-Processing`, `-pdf`, `pdf--processing` are invalid.

Spec example for `description` (good): "Extracts text and tables from PDF files, fills PDF forms, and merges multiple PDFs. Use when working with PDF documents or when the user mentions PDFs, forms, or document extraction."

Spec example for `description` (poor): "Helps with PDFs."

### Optional fields — only these

| Field | Constraints |
| --- | --- |
| `license` | License name or a bundled license file. Keep it short. |
| `compatibility` | 1–500 characters if present. Environment needs (product, packages, network). Most skills omit it. |
| `metadata` | Map of **string keys to string values**. Keep keys reasonably unique. |
| `allowed-tools` | Space-separated string of pre-approved tools. **Experimental.** |

Do not add any other frontmatter key. This pack's validator rejects unknown keys.

### Body

No format restrictions. Recommended: steps, examples, edge cases. The whole body loads on activate. Keep `SKILL.md` under 500 lines; move detail to `references/`.

## Progressive disclosure

1. **Metadata** — `name` and `description` load at startup for every installed skill.
2. **Instructions** — full `SKILL.md` body loads when the skill activates.
3. **Resources** — `scripts/`, `references/`, `assets/` load on demand.

## File references

From `SKILL.md`, use relative paths one level deep (`scripts/extract.py`, `references/SPEC.md`). Avoid nested reference chains.

## Official validation

```bash
skills-ref validate ./my-skill
```

This pack also ships `scripts/validate_skill.py`, which enforces the rules above without installing `skills-ref`.

## Unofficial client-specific extras (NOT in the spec)

Some clients have used extra frontmatter keys such as `paths` and `disable-model-invocation`. Those keys are **not** in the agentskills.io specification consulted on 2026-08-16. Do **not** put them in generated `SKILL.md` frontmatter. If a human needs a client-specific note, put it in `references/` and label it unofficial. This pack's validator rejects those keys.
