# Contributing

## Adding support for a new Odoo version

1. Identify the closest existing version branch (e.g., for Odoo 18, branch from `17.0`).
2. Create the new version branch:
   ```bash
   git checkout 17.0
   git checkout -b 18.0
   ```
3. Update each skill, the agent, and the slash commands to reflect:
   - New ORM features / deprecated APIs
   - OWL framework changes
   - Security model updates
   - Manifest schema changes
   - New mixins or removed ones
4. Add a `migration-{prev}-to-{this}` skill describing breaking changes.
5. Update the root `README.md` table on `main`.

## Improving an existing version

- Fixes and enhancements go on the corresponding version branch.
- Cross-version improvements (e.g., a better skill structure) should be applied to all maintained branches.
- Open a PR against the version branch you're modifying, never against `main` (except for repo-level changes like this file or the index README).

## Skill authoring guidelines

Each skill lives at `skills/<name>/SKILL.md` and follows this shape:

```markdown
---
name: skill-name
description: One-sentence trigger summary that lists the user-facing phrasings that should activate this skill.
---

# Skill Name

## When to use this skill

Concrete situations.

## Core knowledge

The 80/20 of what Claude needs to know.

## Patterns

Code examples (concise, idiomatic, runnable).

## Common pitfalls

What goes wrong and why.

## References

Links to official docs and OCA resources.
```

Skills should be **practical, not encyclopedic**. Distill the docs; don't duplicate them.

## Slash command authoring guidelines

Each command lives at `commands/<name>.md`. Keep the prompt focused, with explicit:
- Inputs (what arguments)
- Steps Claude should take
- Expected output shape
- Quality bar / acceptance criteria

## Style

- Prose over bullet soup. Skills are read top-to-bottom.
- Code examples must be runnable and version-correct.
- Cite the official URL when introducing a non-obvious concept.
