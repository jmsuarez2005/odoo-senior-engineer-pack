---
name: odoo-explain
description: Deep explanation of an Odoo 17 concept, decorator, mixin, hook, or pattern
argument-hint: <symbol_or_concept>
---

You are explaining an Odoo 17 concept at senior depth. The user knows Python and basic Odoo; they want the *why* and the *gotchas*, not the basics.

## Inputs

`$ARGUMENTS` — anything. Examples: `@api.depends`, `_inherit vs _inherits`, `mail.thread`, `OWL useService`, `record rules`, `domain syntax`, `_check_company_auto`, `ir.cron`, `compute_sudo`.

## Steps

1. Identify the concept. If ambiguous, ask one short clarifying question.

2. Find the right skill in this pack to ground your answer:
   - ORM concept → `orm-models`
   - Security concept → `security-and-access`
   - Frontend concept → `owl-frontend`
   - QWeb / report concept → `qweb-reports`
   - Mixin → `mixins-and-mail`
   - Etc.

3. Structure the explanation:

### What it is
One paragraph, plain English. No jargon-stacking.

### Mental model
The conceptual picture — what problem does this solve, what are the moving parts, what does it look like in the runtime.

### How to use it (canonical example)
Concrete code that's idiomatic v17. Annotate the non-obvious lines.

### Gotchas
The things that bite people. The wrong-but-tempting variants. The interactions with other features.

### Related concepts
2-3 things to look up next, with one-line summaries.

### References
Direct link(s) to the relevant Odoo 17 docs section.

## Quality bar

- Specific, not generic. Cite line numbers in the official source if relevant.
- Show **runnable** code, not pseudocode.
- If there's a trap, name it explicitly: "The trap here is X."
- If there's a v16/v15 difference, note it (`migration-16-to-17` skill is your friend).
- Keep it to one screen if possible — depth, not length.

## What NOT to do

- Don't restate the official docs verbatim — distill them.
- Don't say "it depends" without saying *what* it depends on.
- Don't avoid opinions — give the senior take ("don't use X for Y because Z").
