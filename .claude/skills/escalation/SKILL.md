---
name: escalation
description: When to stop and ask Ty, and exactly how. Use before creating an account, touching a credential or token, spending money, deleting or rewriting stored data, changing Cloudflare/R2/PostHog/GitHub settings, or making a product or design decision the issue doesn't settle.
user-invocable: false
---

# Escalation: stop and ask Ty

## Stop before any of these

1. **Accounts:** creating any account, app, API key holder or service sign-up.
2. **Credentials:** handling any credential, token, key or secret: creating, reading, printing, pasting, rotating or storing one. (Secret *names* in `.env.example` are fine; values never.)
3. **Money:** anything that costs money or could: paid plans, upgrades, usage that could exceed a free tier, new paid services.
4. **Stored data:** deleting or rewriting stored data: R2 objects, the raw store, committed data history, released files, issues, PRs, branches others use. (Append-only writes the issue already calls for are fine.)
5. **Settings:** changing Cloudflare, R2, PostHog or GitHub settings: repo settings, rulesets, secrets, labels, Actions permissions, apps, DNS, hosting or billing.
6. **Undecided product or design questions:** any choice of wording, layout, metric definition, scope or behavior that the issue, its plan section and `observatory-rules` don't settle.

When unsure whether something falls in a category, treat it as if it does.

## How to ask

### Main session (run-step or any direct session)

1. Stop work at a clean point. Commit nothing half-done; say what is uncommitted.
2. Write **one** clear question: what you need decided, the options (two or three) with your recommendation first, and what happens next for each. No grade-design details (observatory-rules R55).
3. Add the question to the issue as a comment. Write the body to a file first, then run it as its own call:
   `gh issue comment <n> --body-file <file>`
   Start the body with `**Needs Ty:**`.
4. Add the label, as its own call (a guarded command, CLAUDE.md rule 8):
   `gh issue edit <n> --add-label needs-ty`
   If the label doesn't exist, don't create it (that is a GitHub settings change). Say so in your message and give Ty the command to create it.
5. End the session's turn with the same question, the issue link and nothing else to do. Don't continue with other parts of the work while waiting.

When Ty answers, he removes the label (or asks you to, with `gh issue edit <n> --remove-label needs-ty` as its own call).

### Subagents (planner, builder, reviewer)

Subagents can't stop the session or label issues. Instead, stop immediately and return a final message that starts with:

```
ESCALATE: <the one question>
Category: <1–6 from the list above>
Options: <A (recommended) / B / C, one line each>
State: <what is done, what is uncommitted>
```

The orchestrator (run-step) then follows "Main session" above.
