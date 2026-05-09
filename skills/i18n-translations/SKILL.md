---
name: i18n-translations
description: Internationalize Odoo 17 modules with .pot/.po files, _() and _lt(), translation contexts, locale-aware formatting, and Transifex/Weblate workflows. Use when adding multi-language support, generating translation templates, exporting/importing .po files, debugging missing translations, or handling currency/date locale rendering.
---

# Internationalization & Translations (Odoo 17)

## When to use this skill

Your module needs to support multiple languages, you're handling user-facing strings, generating `.pot` templates, importing translations, or debugging "string shows in English even though user is in French".

## The model

Odoo translations are key-based: every translatable string has a key (usually the English source) and a per-language value. Keys live in `.pot` files (template), translations in `.po` files per locale.

Translation kinds:
- **Code strings** — `_("Submit")` in Python, `_t("Submit")` in JS — extracted automatically
- **Field labels** — `string="Submit"` on view fields — extracted automatically
- **Field values** — for `Selection` fields, the labels (not the keys) are translatable
- **Stored translatable text** — fields with `translate=True` (per-record translations)
- **Help texts** — `help="..."` on fields and `<field name="help">` on actions

## Marking strings translatable

### Python — `_()` vs `_lt()`

```python
from odoo import _, fields, models
from odoo.tools.translate import _lt

class HrOvertime(models.Model):
    _name = "hr.overtime"

    state = fields.Selection([
        ("draft", _lt("Draft")),         # _lt: lazy, evaluated when rendered
        ("submitted", _lt("Submitted")),
    ])

    def action_submit(self):
        self.message_post(body=_("Submitted by %s") % self.env.user.name)  # _: immediate
        raise UserError(_("Cannot submit a record without an employee."))
```

**`_()` vs `_lt()`** — both translate, but timing differs:
- `_()` translates **at call time** with the current user's language. Right for messages, errors.
- `_lt()` translates **at render time** with the consumer's language. Right for module-level constants, Selection labels, defaults.

### JavaScript — `_t()` and `_lt()`

```js
/** @odoo-module **/
import { _t } from "@web/core/l10n/translation";

class MyComponent extends Component {
    static template = "module.MyComponent";
    setup() {
        this.label = _t("Click me");
    }
}
```

### XML — automatic for view strings

```xml
<button name="action_submit" string="Submit"/>
<!--          ^^^^^^^ extracted automatically -->
```

## Translatable stored fields

```python
name = fields.Char(translate=True)
description = fields.Html(translate=True)
```

Each `Many2one` to a translation-aware model still stores ONE value, but each translation is a separate row in `ir.translation`. When user reads `record.name`, ORM picks the row matching `self.env.lang`.

## Generating the .pot template

```bash
# From module code (uses --modules flag for scope)
odoo --modules=hr_overtime \
     --i18n-export=hr_overtime/i18n/hr_overtime.pot \
     --stop-after-init \
     -d empty_db
```

The `.pot` is the template. It has empty translations:
```pot
#. module: hr_overtime
#: code:addons/hr_overtime/models/hr_overtime.py:42
#, python-format
msgid "Cannot submit a record without an employee."
msgstr ""
```

Commit the `.pot`. Translators (or you) generate per-language `.po` from it.

## Per-language .po files

```bash
# Bootstrap a new locale
cp i18n/hr_overtime.pot i18n/es.po

# Or from msgmerge if updating an existing translation
msgmerge -U i18n/es.po i18n/hr_overtime.pot
```

Translators fill in the `msgstr ""` lines. Commit the result.

## Loading translations

Translations load automatically when:
- The module is installed/upgraded with the language already loaded in Odoo, OR
- A user switches to a language with translations available, OR
- Manually triggered: Settings > Translations > Load a Translation

If you change `.po` content and want it reloaded:
```bash
odoo -d mydb --i18n-overwrite -u hr_overtime --stop-after-init
```

`--i18n-overwrite` replaces existing translations on upgrade.

## Locale-aware formatting

Odoo handles formatting based on `res.lang`:

```python
from odoo.tools import format_date, format_datetime, formatLang

# Dates
format_date(self.env, fields.Date.today())      # respects res.lang.date_format

# Numbers / monetary
formatLang(self.env, 1234.56, currency_obj=self.currency_id)
formatLang(self.env, 0.42, digits=2)
```

In QWeb:
```xml
<span t-field="o.amount" t-options='{"widget": "monetary", "display_currency": o.currency_id}'/>
<span t-field="o.date" t-options='{"widget": "date"}'/>
```

`t-field` with widget options uses the user's locale.

## Translation contexts

When the same English word translates differently in different contexts:

```python
_("Open", context="state_button")
_("Open", context="action_open_record")
```

The context goes into the .pot as a separate entry:
```pot
msgctxt "state_button"
msgid "Open"
msgstr ""
```

Use sparingly — most strings don't need context.

## Workflows

### Transifex (used by Odoo and many OCA repos)
- Push `.pot` to Transifex via `tx push -s`
- Translators work in the web UI
- Pull translated `.po` back: `tx pull -a` (all languages)
- Commit the `.po` files

### Weblate (alternative, self-hostable)
- Set up a project pointing at your repo
- Same .pot/.po flow

### Manual (small modules)
- Edit `.po` files in poedit / vim / VS Code's "i18n Ally"
- Commit

## Multi-language records

Some content is per-record translated (product names, mail template bodies, …). The user sees the translation matching their `lang`. If no translation exists for that lang, falls back to the model's default lang (typically `en_US`).

```python
# Set translation programmatically
record.with_context(lang="es_ES").name = "Camiseta"
record.with_context(lang="fr_FR").name = "T-shirt"
```

Or via Settings > Translations > Translated Fields after the fact.

## Common pitfalls

- `_("Hello %s") % name` — works, but the translator sees only `"Hello %s"`. Use `_("Hello %s", name)` (Odoo's `_()` accepts args), or named substitutions: `_("Hello %(name)s") % {"name": name}` — the latter is translator-friendly.
- Marking a docstring with `_()` — docstrings aren't extracted. Only literals in calls.
- F-strings: `_(f"Hello {name}")` — **never works**. The f-string is evaluated before `_()`, so the extracted string contains the literal value, not the placeholder.
- Selection field labels not appearing translated → use `_lt()` for labels, not bare strings.
- `translate=True` on a stored Char that's also unique — the unique check is per-language, leading to surprising "duplicate" errors.
- Shipping a module with only `.po` (no `.pot`) — translators can't update without the template.
- Adding new strings without regenerating `.pot` — translators don't know they exist.

## Checklist for a new module

- [ ] All user-facing strings wrapped in `_()` / `_lt()` / `_t()`
- [ ] Selection field labels use `_lt()`
- [ ] No f-strings or `.format()` inside `_()`
- [ ] `i18n/<module>.pot` regenerated and committed
- [ ] At least one `.po` translation provided if going multi-lang from start
- [ ] Help texts translated (they're translatable but easy to forget)
- [ ] Mail templates use `t-out` of translatable fields, not hardcoded English

## References

- [Odoo 17 — Translating modules](https://www.odoo.com/documentation/17.0/developer/howtos/translations.html)
- [Odoo 17 — Translation reference](https://www.odoo.com/documentation/17.0/developer/reference/backend/translations.html)
- [OCA Transifex setup](https://github.com/OCA/maintainer-tools)
