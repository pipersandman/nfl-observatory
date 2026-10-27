---
description: Start work on one plan step from its GitHub issue (plan only, no edits)
argument-hint: <issue number>
---

We're starting work on GitHub issue #$ARGUMENTS.

1. Read `CLAUDE.md`.
2. Run `gh issue view $ARGUMENTS` and read the issue, including its plan section link.
3. Read that section of `docs/V2_BUILD_PLAN.md`, plus anything it depends on.
4. Run `git status` and `git branch --show-current`. If we're on `main` or the
   working tree isn't clean, stop and tell me.
5. Propose a numbered plan:
   - the files you'll create or change
   - each change in one line
   - how you'll check it (commands and what a pass looks like)
   - anything in the issue that's unclear or that you'd need from me
     (a decision, a secret, an account)

Don't edit any files until I approve the plan.
