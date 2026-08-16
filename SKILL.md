---
name: write-agent-skill
description: Turn a described workflow into a spec-valid Agent Skill directory (SKILL.md plus optional scripts, references, and assets) that actually triggers. Use when the user asks to write a skill, create SKILL.md, author an agent skill, skill-writer, follow the agentskills.io spec, or make a skill that triggers.
license: MIT
compatibility: Requires Python 3 to run scripts/validate_skill.py and scripts/new_skill.py. No extra packages.
metadata:
  version: "0.1.0"
  author: Work
  compiled: "2026-08-16"
---

# Write an Agent Skill that triggers

You are using **write-agent-skill**, compiled by **Work, an AI agent**, on 2026-08-16. Disclose that you are an AI if you are one. This is not legal advice and not a guarantee of marketplace installs or revenue.

Official spec (cited notes): [references/SPEC.md](references/SPEC.md). Source: https://agentskills.io/specification (2026-08-16). Do not invent frontmatter fields.

Sibling product (do not copy its dataset): `th3coke-dot/ai-author-platform-rules` answers "can I publish X on Y?". This pack writes the skill directory.

## Hard rules

1. Ask only for the four intake items below. Do not ask for a brand story, pricing, or store strategy.
2. One skill, one job (one verb family).
3. Description is trigger text, not marketing. Reject "Helps with X."
4. `name` must match the parent folder and the spec charset.
5. Put repeatable commands in `scripts/`. Put long detail in `references/`. Keep `SKILL.md` under 500 lines.
6. Run `scripts/validate_skill.py` on the result. If it fails, fix before delivering.
7. Add `AI-AUTHOR.md` when the author is an AI (always, when Work is writing).
8. Do not invent spec fields. Do not put Cursor-only keys (`paths`, `disable-model-invocation`) in frontmatter. They are unofficial; see [references/SPEC.md](references/SPEC.md).
9. Do not create accounts, publish, message anyone, or buy anything. Do not use SolvoOps, PartnerForge, or Scope2Plan.

## 1. Intake — ask only these

Ask the user (or extract from their brief) **only**:

1. **Job** — one verb family. Examples: "extract tables from PDFs", "validate a skill directory", "lint commit messages".
2. **Trigger phrases** — words users actually type. Not slogans.
3. **Scripts** — none, or what a script must accept and print. Repeatable commands belong in `scripts/`.
4. **License** — a short SPDX id (`MIT`, `Apache-2.0`) or omit.

If they dump a novel, extract those four and continue. If they name two jobs, split into two skills or refuse the second job.

## 2. Choose a valid `name`

- 1–64 characters
- `[a-z0-9-]` only
- no leading or trailing hyphen
- no consecutive `--`
- **must match the parent directory name**

Good: `pdf-tables`, `lint-commits`, `write-agent-skill`.
Bad: `PDF-Tables` (uppercase), `-pdf` (leading hyphen), `pdf--tables` (consecutive hyphens), folder `pdf-tables` with `name: tables` (mismatch).

If the user gives a title, slug it: lowercase, spaces to hyphens, strip other punctuation. Then create `that-name/SKILL.md`.

## 3. Write the `description` (this is the trigger)

`name` + `description` are loaded for every installed skill. The body loads only after the agent decides to activate. If the description does not match what users say, the skill never runs.

Must:

- Be 1–1024 characters, non-empty
- Say **WHAT** it does **and WHEN** to use it
- Include the trigger phrases from intake

Must not:

- Be marketing: "Helps with PDFs." is a reject
- Promise revenue, ranking, or installs
- List a second job

Pattern that works:

`[imperative what]. Use when [user phrases].`

Good (from the spec):

```yaml
description: Extracts text and tables from PDF files, fills PDF forms, and merges multiple PDFs. Use when working with PDF documents or when the user mentions PDFs, forms, or document extraction.
```

Bad:

```yaml
description: Helps with PDFs.
```

If you drafted marketing, rewrite it before writing the file.

## 4. Layout

```
skill-name/
├── SKILL.md          # required
├── scripts/          # optional: executable commands
├── references/       # optional: detail loaded on demand
└── assets/           # optional: templates, images, data
```

- File references from `SKILL.md` stay **one level deep** (`scripts/foo.py`, `references/BAR.md`). No `references/a/b.md` chains.
- Progressive disclosure: metadata always; body on activate; scripts/references/assets on demand.
- Optional frontmatter only: `license`, `compatibility` (1–500 chars), `metadata` (string keys → string values), `allowed-tools` (space-separated, experimental).

Start from [assets/SKILL.template.md](assets/SKILL.template.md) or run:

```bash
python3 scripts/new_skill.py --name skill-name --description "Does the job. Use when the user says the trigger phrases."
```

## 5. Write the body

No required body format. Prefer:

1. Hard rules (what the agent must not do)
2. Steps for the one job
3. One worked example (input → files)
4. Edge cases

Keep `SKILL.md` under 500 lines. If a section is a table or a long spec, move it to `references/` and link it.

## 6. Validate, then fix

From this pack (or copy the script next to the new skill):

```bash
python3 scripts/validate_skill.py ./skill-name
```

Official extra check if the user has it installed:

```bash
skills-ref validate ./skill-name
```

Exit 0 is the only success. If this pack's validator prints `ERROR:`, fix the frontmatter or layout and re-run. **Do not deliver a skill that fails validation.**

## 7. AI authorship

When Work (or any AI) writes the skill, add `AI-AUTHOR.md` in the skill root:

- State that the author is an AI
- Date the compilation
- Say it is not legal advice
- Say the AI did not create accounts or publish

## 8. Deliver — do not publish

Hand over the directory. Tell the human they may drop it into:

- `.agents/skills/<name>` (cross-client)
- `.cursor/skills/<name>` (Cursor)

Do not create Polar/Gumroad/GitHub accounts. Do not upload, list, or message buyers. A human owns accounts and KYC.

## Worked example

**Intake**

- Job: count words in a UTF-8 file
- Triggers: "count words", "word count this file"
- Scripts: `scripts/count_words.py <file>` prints one integer
- License: MIT

**name:** `count-words` (folder `count-words/`)

**description:**

```yaml
description: Counts words in a UTF-8 text file and prints the integer total. Use when the user asks to count words or wants a word-count script.
```

Then write a short body, add the script if promised, run `scripts/validate_skill.py ./count-words`, add `AI-AUTHOR.md` if an AI wrote it.

## Edge cases

- **Two jobs in one brief** — make one skill or ask which job. Do not ship a "platform" skill.
- **No trigger phrases** — inventing slogans is wrong. Ask for words the user would type, or derive them from the job verb (`count words`, `extract tables`).
- **Uppercase title** — slug it; never put `PDF-Processing` in `name`.
- **Folder already exists** — do not overwrite. Choose a new slug or stop.
- **User asks for `paths` / `disable-model-invocation`** — refuse in frontmatter. Mention unofficial extras only in `references/`, labeled unofficial.
- **User asks you to publish** — refuse. Deliver the folder.
- **Description over 1024 characters** — cut keywords that are not spoken; keep WHAT + WHEN.

## How not to use this skill

- Do not generate a skill for account creation, KYC, phishing, or exploits.
- Do not copy `th3coke-dot/ai-author-platform-rules` records into a new skill.
- Do not claim this pack will rank on 2026 install charts. Those charts are dominated by free publishers; this is a shipping job those packs do not do.
