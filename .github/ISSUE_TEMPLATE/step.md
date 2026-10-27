---
name: Step
about: One step from docs/V2_BUILD_PLAN.md (one issue, one branch, one PR)
title: "[V2.x] "
labels: step
---

## Goal

<!-- One or two sentences: what this step produces. -->

**Plan section:** docs/V2_BUILD_PLAN.md, section <!-- e.g. 4, V2.0a step 3 -->

## Why

<!-- What it unlocks or fixes. -->

## Depends on

<!-- Issues that must be merged first, e.g. #12. "None" if none. -->

## Files expected to change

-

## Done when

<!-- Commands to run and what a pass looks like. Include numbers where data is involved. -->

- [ ]
- [ ] `venv/Scripts/python scripts/check.py` passes
- [ ] CI is green on the pull request

## Stop and ask if

- the plan section is ambiguous or conflicts with the code
- a check fails for a reason that isn't clear
- a secret, new account or setting change is needed
- the work grows past this issue (split it instead)

## Decisions needed

<!-- Any D-numbers from plan section 33 this step settles, or "None". -->
