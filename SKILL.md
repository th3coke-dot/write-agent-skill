---
name: write-agent-skill
description: Create or update an Agent Skill package when asked to turn a workflow into a reusable skill.
license: MIT
compatibility: Python 3.10+ and PyYAML for the bundled scripts; install requirements.txt before running them.
metadata:
  version: "0.2.0"
  author: Work
  compiled: "2026-08-16"
  updated: "2026-09-05"
---

# Write an Agent Skill

Produce the requested skill package with a clear trigger, useful instructions and working supporting files.

## Create or update

Infer the job, expected inputs/outputs, trigger and license from the request and repository conventions. Ask only when a missing decision materially affects the result.

For a new package, choose a lowercase hyphenated name matching its folder. For an authorized update, edit the existing package in place and preserve unrelated files, supported metadata, attribution and license. The scaffolder creates new folders only; it intentionally refuses to overwrite an existing folder.

Keep the description short and specific. Put essential decisions and constraints in this file; link substantial conditional details from references. Add scripts or assets only when they serve the requested workflow. Do not add blanket product bans, generic legal disclaimers or a mandatory authorship file to every generated skill.

Read [references/SPEC.md](references/SPEC.md) when checking format details. To scaffold a new package:

```bash
python3 -m pip install -r requirements.txt
python3 scripts/new_skill.py --name skill-name --description "Counts words for word-count requests."
```

The scaffolder defaults to MIT; pass `--license ""` to omit it when no license is chosen. Replace the scaffold instructions with the actual workflow.

## Verify and finish

Run `python3 scripts/validate_skill.py <skill-directory>` and correct format errors. Review advisory warnings; `--strict-style` is available when those house conventions are explicitly required. Run new or changed scripts on representative inputs and failures.

Completion means the requested files are implemented, references resolve, changed helpers work, and remaining limits are stated. Structural validation does not prove model activation or task quality. Use realistic positive and negative requests when behavioral evaluation is warranted.

Creating or updating a package does not request publication. If publication is separately requested, use the applicable publishing workflow and existing authorization. Keep the package's original [AI-AUTHOR.md](AI-AUTHOR.md) as provenance; additional attribution in generated packages depends on their actual requirements.
