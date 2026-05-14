---
title: geno-tax-status
description: "Tax Filing Status"
---

# geno-tax-status

`/geno-tax-status`

> "Tax Filing Status"

<div class="zoom-depth" markdown>

<div class="zoom-section zoom-section-3" markdown>

## Input

`$ARGUMENTS` — Optional. A specific tax year (e.g., `2024`). If omitted, show all years.

</div>

<div class="zoom-section zoom-section-4" markdown>

---

## Workflow

### 1. Read YAML organizers

Read these files from `~/docs/finance/taxes/`:
- `TY2024/tax-return-2024.yaml`
- `TY2025/tax-return-2025.yaml`
- `TY2023-amendment/amendment-2023.yaml`

### 2. Count filled vs blank fields per section

For each YAML, check these sections and count fields that have real values vs comments/blank:

**Income section:**
- W-2 wages (filled if `wages:` has a number)
- State PFML (filled if `total_benefits_received:` has a number)
- Other 1099 income

**Investments section:**
- Coinbase (filled if `net_gain_or_loss:` or `csv_attached: true`)
- Robinhood (filled if `form_1099_consolidated: true` or capital gains have values)
- Fidelity/Schwab (same check)

**Airbnb section:**
- Income (filled if `gross_rental_income:` has a number)
- Expenses (count how many expense line items have values)
- Depreciation (filled if `current_year_depreciation:` has a number)

**Deductions section:**
- Each sub-section (medical, charitable, student loans, other)

**Amendment (TY2023):**
- Original return uploaded
- Corrected amounts filled
- Reason documented

### 3. Output status table

Display a table like:

```
╔══════════════════════════════════════════════════════════════╗
║                    TAX FILING STATUS                        ║
╠══════════╦═══════╦═══════════╦════════╦═══════╦═════════════╣
║ Year     ║ Income║ Investments║ Airbnb ║ Deduct║ Overall     ║
╠══════════╬═══════╬═══════════╬════════╬═══════╬═════════════╣
║ TY2024   ║ 0/3   ║ 0/3       ║ 5/8   ║ 0/4   ║ 28%         ║
║ TY2025   ║ 0/3   ║ 0/3       ║ 5/8   ║ 0/4   ║ 28%         ║
║ TY2023   ║  —    ║  —        ║ ✓ ref ║  —    ║ amendment   ║
╚══════════╩═══════╩═══════════╩════════╩═══════╩═════════════╝
```

### 4. Show next actions

List the top 3 most impactful missing items and how to get them:
- "Download W-2 from employer payroll portal"
- "Run `/gt-tax-fetch coinbase 2024` to get crypto tax docs"
- etc.

</div>

<div class="zoom-section zoom-section-5" markdown>

---

### Rationale

*Rationale not yet generated. Run `geno-docs compile --rationale` to generate LLM explanations for this skill.*

</div>

</div>

[:material-arrow-left: Back to geno-taxes](index.md)
