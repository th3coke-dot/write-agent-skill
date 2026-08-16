# write-agent-skill

Turn a described workflow into a spec-valid Agent Skill directory (`SKILL.md` plus optional `scripts/`, `references/`, `assets/`) that actually triggers.

**Work is an AI agent.** Work compiled this folder on 2026-08-16. See `AI-AUTHOR.md`. This is not legal advice and not a guarantee of marketplace installs or revenue.

Sibling product (do not copy its dataset): [th3coke-dot/ai-author-platform-rules](https://github.com/th3coke-dot/ai-author-platform-rules) — platform rules for AI-authored work. This pack is the skill-writer.

## How to install

Drop the folder in, no edits:

```text
.agents/skills/write-agent-skill
```

or, on Cursor:

```text
.cursor/skills/write-agent-skill
```

The folder name must stay `write-agent-skill` (it must match the `name` field). Then ask an agent to write a skill, create SKILL.md, author an agent skill, or make a skill that triggers.

## How to use

1. Give the agent one job (one verb family), the phrases users actually type, whether you need scripts, and a license.
2. The agent writes `your-name/SKILL.md` using the spec in `references/SPEC.md` and the template in `assets/SKILL.template.md`.
3. Validate:

```bash
python3 scripts/validate_skill.py ./your-name
```

Exit 0 only if the skill is valid. Official extra check if you have it:

```bash
skills-ref validate ./your-name
```

Optional scaffold:

```bash
python3 scripts/new_skill.py --name your-name --description "Does the job. Use when the user says the trigger phrases."
```

Run this pack's tests:

```bash
python3 tests/test_all.py
```

This pack must also validate itself (from the pack root, or pass the folder path):

```bash
python3 scripts/validate_skill.py .
```

## How NOT to use

- **Do not invent spec fields.** Allowed frontmatter is `name`, `description`, and optionally `license`, `compatibility`, `metadata`, `allowed-tools`. Cursor-only keys such as `paths` and `disable-model-invocation` are unofficial; do not put them in generated frontmatter.
- **Do not ship marketing descriptions.** "Helps with X." will not trigger and this pack's validator rejects it.
- **Do not put two jobs in one skill.**
- **Do not let an AI publish or create store accounts.** A human owns Polar/Gumroad/GitHub accounts and KYC. Work will not do those steps.
- **Do not treat this as a sales forecast.** 2026 skill install charts are dominated by three free publishers. A paid skill has to do a shipping job those do not. That is the bet, not a promise.
- **Do not copy the sibling dataset** from `th3coke-dot/ai-author-platform-rules`.
- **This is not legal advice.**

## Layout

```text
write-agent-skill/
├── SKILL.md                 # this pack is itself a valid skill
├── scripts/validate_skill.py
├── scripts/new_skill.py
├── references/SPEC.md       # cited notes, 2026-08-16
├── assets/SKILL.template.md
├── tests/                   # python3 tests/test_all.py
├── AI-AUTHOR.md
├── LICENSE                  # MIT (scripts, tests, and skill docs)
├── README.md
└── LISTING.md               # store copy; not published
```

## License

MIT. See `LICENSE`. Spec notes cite https://agentskills.io/specification (consulted 2026-08-16).
