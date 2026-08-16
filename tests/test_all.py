#!/usr/bin/env python3
"""Single test command for write-agent-skill.

    python3 tests/test_all.py

Exit 0 only if every check passes.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VALIDATOR = ROOT / "scripts" / "validate_skill.py"
NEW_SKILL = ROOT / "scripts" / "new_skill.py"
FIXTURES = ROOT / "tests" / "fixtures"

failures: list[str] = []


def run(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=cwd,
        text=True,
        capture_output=True,
    )


def check(name: str, cond: bool, detail: str = "") -> None:
    if cond:
        print(f"PASS  {name}")
        return
    print(f"FAIL  {name}: {detail}")
    failures.append(name)


def main() -> int:
    check("validator exists", VALIDATOR.is_file())
    check("new_skill exists", NEW_SKILL.is_file())
    check("this pack SKILL.md exists", (ROOT / "SKILL.md").is_file())

    # 1. This pack validates against its own validator.
    proc = run([sys.executable, str(VALIDATOR), str(ROOT)])
    check(
        "pack validates itself",
        proc.returncode == 0,
        f"exit {proc.returncode}\n{proc.stderr}",
    )

    # Required trigger phrases in this pack's description.
    pack_text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    for phrase in (
        "write a skill",
        "create SKILL.md",
        "author an agent skill",
        "skill-writer",
        "agentskills.io spec",
        "make a skill that triggers",
    ):
        check(f"pack description has {phrase!r}", phrase in pack_text)

    # 2. Valid fixture passes.
    valid = FIXTURES / "valid-skill"
    proc = run([sys.executable, str(VALIDATOR), str(valid)])
    check(
        "valid fixture passes",
        proc.returncode == 0,
        f"exit {proc.returncode}\n{proc.stderr}",
    )

    # 3. Bad name (uppercase) fails.
    bad_name = FIXTURES / "bad-name-uppercase"
    proc = run([sys.executable, str(VALIDATOR), str(bad_name)])
    err = (proc.stderr or "").lower()
    check(
        "uppercase name fixture fails",
        proc.returncode != 0,
        f"exit {proc.returncode} (expected non-zero)\n{proc.stderr}",
    )
    check(
        "uppercase name fixture mentions name",
        proc.returncode != 0 and ("name" in err or "uppercase" in err or "a-z" in err),
        proc.stderr,
    )

    # 4. Description too short / missing when-to-use fails.
    bad_desc = FIXTURES / "bad-description"
    proc = run([sys.executable, str(VALIDATOR), str(bad_desc)])
    err = (proc.stderr or "").lower()
    check(
        "bad description fixture fails",
        proc.returncode != 0,
        f"exit {proc.returncode} (expected non-zero)\n{proc.stderr}",
    )
    check(
        "bad description fixture mentions description or when",
        proc.returncode != 0
        and ("description" in err or "when" in err or "helps with" in err),
        proc.stderr,
    )

    # Extra: invented / unofficial fields rejected.
    with tempfile.TemporaryDirectory() as tmp:
        invented = Path(tmp) / "invented-field"
        invented.mkdir()
        (invented / "SKILL.md").write_text(
            "---\n"
            "name: invented-field\n"
            "description: Does one job. Use when testing unknown fields.\n"
            "paths: /tmp\n"
            "---\n\n# Invented\n",
            encoding="utf-8",
        )
        proc = run([sys.executable, str(VALIDATOR), str(invented)])
        check(
            "unofficial paths field rejected",
            proc.returncode != 0 and "paths" in (proc.stderr or ""),
            proc.stderr,
        )

    # 5. new_skill.py output validates.
    with tempfile.TemporaryDirectory() as tmp:
        desc = (
            "Scaffolds a demo skill directory for tests. "
            "Use when checking that new_skill.py writes a valid skill."
        )
        proc = run(
            [
                sys.executable,
                str(NEW_SKILL),
                "--name",
                "demo-skill",
                "--description",
                desc,
                "--output",
                tmp,
            ]
        )
        check(
            "new_skill.py exits 0",
            proc.returncode == 0,
            f"exit {proc.returncode}\n{proc.stderr}\n{proc.stdout}",
        )
        dest = Path(tmp) / "demo-skill"
        check("new_skill.py created directory", dest.is_dir(), str(dest))
        check("new_skill.py created SKILL.md", (dest / "SKILL.md").is_file())
        proc2 = run([sys.executable, str(VALIDATOR), str(dest)])
        check(
            "new_skill.py output validates",
            proc2.returncode == 0,
            f"exit {proc2.returncode}\n{proc2.stderr}",
        )

    # new_skill rejects a bad name without writing.
    with tempfile.TemporaryDirectory() as tmp:
        proc = run(
            [
                sys.executable,
                str(NEW_SKILL),
                "--name",
                "BadName",
                "--description",
                "Does one job. Use when testing a bad name.",
                "--output",
                tmp,
            ]
        )
        check(
            "new_skill.py rejects uppercase name",
            proc.returncode != 0 and not (Path(tmp) / "BadName").exists(),
            f"exit {proc.returncode}\n{proc.stderr}",
        )

    if failures:
        print(f"\n{len(failures)} failed: {', '.join(failures)}")
        return 1
    print("\nAll tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
