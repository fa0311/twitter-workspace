---
name: feedback-account-budget
description: "The sandbox account is one shared allowance: count before spending, confirm whose session it is, what may be done to it, and that a failing login means the lock"
metadata:
  type: feedback
---

- **The sandbox account is one shared, scarce allowance.** CI, suites, recordings and my own checks all draw on it, so the cost of an
  action is counted before it starts, including what a push or a merge sets off elsewhere.
- **Only that account, and knowingly.** Confirm whose session it is before using it, and never show its values.
- **Its own state may be touched when the work needs it.** Whatever affects nothing but the account itself may be driven, provided it
  is undone in the same run and reported.
- **A failing login is the lock until proven otherwise.** Stop instead of retrying; only the maintainer clears it.

**Why:** every pipeline and every session tests against this one account; a lock stops all of them at once.
**How to apply:** the numbers are in `CLAUDE.md` ("Account budget"), what set off earlier locks is in `REFERENCE.md` ("X behaviour").
Related: [[feedback-working-rules]].
