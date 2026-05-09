---
name: odoo-business-fit
description: Map a business use case to Odoo 17 — pick standard apps, decide config-vs-customize, produce a scoping document
argument-hint: <use_case_description>
---

You are doing a fit-gap analysis: does standard Odoo cover this, with config or customization, or is it a fundamentally new module?

## Inputs

`$ARGUMENTS` — free text describing the business use case. If too vague, ask:

1. **Industry / vertical** — manufacturer, services firm, retailer, B2B SaaS, etc.
2. **Process** — what's the lifecycle, who does what at each step
3. **Volume** — orders/leads/employees per day or month
4. **Multi-company / multi-warehouse / multi-language**
5. **Existing systems** — what's the current tool, what stays, what migrates
6. **Hard requirements** — non-negotiable rules (compliance, audit, currency, …)

Cover at minimum: industry, process, volume.

## Steps

1. Use the `business-modeling` skill as your reference framework.

2. Identify the standard Odoo apps that map to the requirements. Consult: `business-sales`, `business-crm`, `business-accounting`, `business-inventory`, `business-mrp`, `business-purchase`, `business-hr-payroll`, `business-project`, `business-helpdesk`, `business-ecommerce`, `business-subscriptions`, `business-pos`, `business-marketing`.

3. For each requirement, classify it:
   - **Bucket 1** — Standard, just configure
   - **Bucket 2** — Studio / view inheritance (low-code)
   - **Bucket 3** — Custom module that fits existing models
   - **Bucket 4** — Fundamentally new domain → custom app

4. Produce the scoping document.

## Output

A markdown scoping document with these sections:

```markdown
## Use Case: <name>

### Business goal
<One paragraph: what business outcome does Odoo enable here>

### Process
<Numbered steps from start to finish, who does what>

### Recommended Odoo apps
| App | Purpose in this case | Edition (Community/Enterprise) |
|---|---|---|

### Data model
- Core entities reused: <list with notes>
- Extended entities: <list with which fields added>
- New entities: <list with rationale>

### Requirements by bucket

#### Bucket 1 — Configuration
| Requirement | Where to configure | Effort |
|---|---|---|

#### Bucket 2 — Studio / view inheritance
| Requirement | Approach | Effort |
|---|---|---|

#### Bucket 3 — Custom module (fits standard model)
| Requirement | Module name | Models extended | Effort |
|---|---|---|---|

#### Bucket 4 — Custom domain
| Requirement | New module | Effort | Risks |
|---|---|---|---|

### Integrations
| System | Direction | Volume / latency | Approach |
|---|---|---|---|

### Roles & ACL
| Role | Can | Cannot |
|---|---|---|

### Reports & dashboards
- <list>

### Phasing recommendation
- **Phase 1 (MVP)**: <what gets configured + tested first>
- **Phase 2**: <next layer>
- **Phase 3**: <nice-to-haves>

### Risks called out
- <each risk with mitigation>

### Out of scope
- <explicit list>

### Estimated total effort
<rough: weeks/months for each phase>
```

## Quality bar

- Specific recommendations: name actual modules (`sale_management`, not "Sales").
- Honest about Enterprise vs Community: if a needed feature is Enterprise-only, say so and offer the OCA alternative.
- Prefer config over code. If the answer is "Studio", say "Studio".
- Identify the **one or two** highest-risk requirements early — they often kill projects.
- Phasing matters: don't propose a Big Bang. Recommend a Phase 1 MVP that delivers value in 4-8 weeks.

## What NOT to do

- Don't promise "Odoo can do anything" — name the bucket honestly.
- Don't skip the integrations table — most projects fail on integration scope.
- Don't recommend custom code where configuration suffices.
- Don't quote effort with false precision (don't say "47 hours"; say "1-2 weeks").
- Don't write the actual code yet — this is scoping, not implementation.
