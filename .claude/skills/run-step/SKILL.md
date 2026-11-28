---
name: run-step
description: Run one plan step end to end with the planner, builder and reviewer subagents, from a GitHub issue number to an open, reviewed PR.
argument-hint: <issue-number>
disable-model-invocation: true
---

# /run-step $ARGUMENTS

Run issue **#$ARGUMENTS** through planner → (Ty approves) → builder → reviewer,
then stop with a summary. You are the orchestrator: you delegate, relay and
stop at the stop points. You don't write code yourself. Follow
`observatory-rules` and `escalation` throughout.

If `$ARGUMENTS` is empty or not a number, ask for the issue number and stop.

## Recording Ty's decisions (whole run, R72)

Whenever Ty answers a question or approves with changes, record it straight
away. **Don't ask whether to post it.**

- **What counts:** plan approval and its wording, option choices, scope
  changes, and answers to the reviewer's "Questions for Ty". Only Ty's
  decisions; any other comment still follows the normal stop points.
- **Where:** before a PR exists, on the issue; once a PR exists, on the PR.
- **Form:** heading `## Decisions from Ty (<YYYY-MM-DD>)` (`## Scope note
  (<YYYY-MM-DD>)` for a scope change, with the options and the choice, R67),
  then the plan revision or PR round it applies to, then one decision per
  line. Scan it for grade-design details (R55).
- **How:** write it to a file in the scratchpad, then post it as its own call:
  `gh issue comment $ARGUMENTS --body-file <file>` or
  `gh pr comment <pr> --body-file <file>`.
- **When:** before the next delegation, so the planner, builder and reviewer
  can read it.

## 1. Where things stand

1. Read the latest comment on #86:
   `gh issue view 86 --json comments --jq '.comments[-1].body'`
   Note anything it says about #$ARGUMENTS, its dependencies, merge windows or
   open decisions.
2. `gh pr list` and `gh issue list --label step`.
3. `gh issue view $ARGUMENTS`. Stop and tell Ty if any of these hold:
   - the issue is closed, isn't labelled `step`, or has the `needs-ty` label;
   - an issue under "Depends on" is still open;
   - an open PR already closes #$ARGUMENTS, or a `step/$ARGUMENTS-*` branch exists;
   - `git status` isn't clean, or there's unpushed work on another branch.
4. Tell Ty in three lines or fewer what you found and that planning starts.

## 2. Plan

1. Delegate to the **planner** agent: "Plan issue #$ARGUMENTS." Add any
   relevant note from step 1 (for example a merge window or a decision in #86).
2. If it returns `ESCALATE:`, follow the escalation skill (comment, `needs-ty`
   label, one question) and stop.
3. **Stop point: show Ty the plan** (the comment link and the full plan text)
   and wait for his OK. Record his answer as a "Decisions from Ty" comment on
   the issue (see "Recording Ty's decisions"). If he asks for changes, send
   them to the planner as "revision <k+1>: <Ty's changes>" and show the new
   plan. Don't start building until Ty approves.

## 3. Build

1. Delegate to the **builder** agent: "Build issue #$ARGUMENTS from plan
   revision <k>, approved by Ty." The builder's `git push` and `gh pr create`
   will ask Ty for permission; that's expected.
2. If it returns `ESCALATE:`, follow the escalation skill and stop.
3. Note the PR number and URL.

## 4. Review (up to 3 rounds of changes)

1. Delegate to the **reviewer** agent: "Review PR #<pr>, round 1." Give it
   only the PR number and round, never the builder's summary.
2. If the verdict is `PASS`, go to step 5.
3. If it's `CHANGES REQUIRED`, send the numbered list unchanged to the
   **builder**: "Changes for PR #<pr>, round <r>: <list>". Then call the
   reviewer again with the next round number.
4. After 3 rounds of changes without a `PASS`, stop: don't start a fourth.
   Report what is still open.
5. If any agent returns `ESCALATE:`, follow the escalation skill and stop.
6. If the reviewer raises "Questions for Ty", ask Ty, then record his answers
   as a "Decisions from Ty" comment on the PR, naming the round, before the
   next delegation.

## 5. Summary for Ty

Check live state first (`gh pr view <pr>`, `gh pr checks <pr>`), then give:

- **PR:** link, title, CI result.
- **Review:** final verdict and how many rounds it took; any "Questions for
  Ty" the reviewer raised.
- **What changed:** 3–6 lines.
- **Checks Ty runs:** the plan's "Checks Ty runs", copied in full with each
  **Pass:** line, plus the merge itself (GitHub → the PR → **Merge pull
  request** → **Confirm merge** → **Delete branch**), outside game windows if
  the merge starts a data run (R64).
- **After merge:** the post-merge checks to record on the PR (R28).

Don't merge, and don't mark anything ready on Ty's behalf.

## 6. Handoff on #86

1. Draft the end-of-session handoff comment in the observatory-rules R63
   format, every fact from live GitHub (`gh pr list`, `gh issue list --state
   all`, `gh run list`). Scan it for grade-design details (R55).
   Read the previous handoff on #86 and carry forward every open item it
   lists (open issues and PRs, unconfirmed rules, checks still to run, open
   decisions) unless live GitHub shows it closed; list a closed one once under
   **Done** as closed. Never drop an item silently.
2. **Stop point: show Ty the full draft** and wait for his OK.
3. After his OK, write it to a file in the scratchpad and post it as its own
   call: `gh issue comment 86 --body-file <file>`.
