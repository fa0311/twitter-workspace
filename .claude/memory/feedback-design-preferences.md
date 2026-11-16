---
name: feedback-design-preferences
description: "fa0311's design taste for the spec, the clients and the renderer: model what exists, share only what is the same, strict where it decides something, an archive is not the live page, users are engineers"
metadata:
  type: feedback
---

- **Model what exists, nothing more.** Follow what X really does; what it dropped is dropped, with no fallback kept for compatibility.
- **Declare, don't orchestrate.** Typed literal definitions over registration calls and procedures.
- **Share only what is the same thing.** A look-alike gets its own type; a shared type is never widened to fit a second use.
- **Strict where it decides something, loose elsewhere.** Precision goes to values that drive shape, branching or what the user
  sees; plumbing stays plain.
- **Parts do not know each other.** Each component documents its own surface; an integration recipe lives with the part that integrates.
- **An archive is not the live page.** Output meant to be looked at later takes the original's look but keeps everything visible
  and readable out of context: what only works interactively is adapted or dropped, and what depends on the moment of capture appears
  only where mirroring the original is the point.
- **Follow the platform rather than invent.** Where the browser or X already has a behaviour, reproduce it and decline extra
  cleverness; an option is explicit, never implied.
- **Users are engineers.** Hand responsibility to the tools they already know instead of wrapping them, and pick the default with
  the smallest implementation.
- **Docs are examples.** A feature earns a line of usage; explanation and history belong to the PR and to git.
- **Existing output may shift a little** when that buys shared code.
- **A view scales with its data.** What grows without bound gets its own filterable place.

**Why:** this is the maintainer's taste and cannot be read off the code.
**How to apply:** apply silently and decide new cases in their spirit; what was decided case by case is in `REFERENCE.md`.
Related: [[feedback-working-rules]], [[feedback-screenshots]].
