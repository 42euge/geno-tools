---
title: geno-tax-summary
description: "Tax Year Summary for CPA"
---

# geno-tax-summary

`/geno-tax-summary`

> "Tax Year Summary for CPA"

<div class="zoom-depth" markdown>

<div class="zoom-section zoom-section-3" markdown>

## Input

`$ARGUMENTS` — Required. Tax year (e.g., `2024`, `2025`, `2023`).

</div>

<div class="zoom-section zoom-section-4" markdown>

---

## Workflow

### 1. Read the YAML organizer

- `2024` or `2025` → Read `~/docs/finance/taxes/TY{year}/tax-return-{year}.yaml`
- `2023` → Read `~/docs/finance/taxes/TY2023-amendment/amendment-2023.yaml`

### 2. Generate summary

Output a formatted summary with these sections:

```markdown
# TY{YEAR} Tax Summary — Eugenio Rivera Ramos
Prepared: {today's date}
Filing Status: Single | State: WA (no state income tax)

## Income
| Source | Amount | Form | Status |
|--------|--------|------|--------|
| W-2 Wages | $XXX | W-2 | ✓/Missing |
| State PFML | $XXX | 1099-G | ✓/Missing |
| Other | $XXX | 1099-NEC | ✓/Missing |

## Capital Gains & Losses (Schedule D)
| Platform | Short-Term | Long-Term | Net | Status |
|----------|-----------|----------|-----|--------|
| Coinbase | $XXX | $XXX | $XXX | ✓/Missing |
| Robinhood | $XXX | $XXX | $XXX | ✓/Missing |
| Fidelity | $XXX | $XXX | $XXX | ✓/Missing |
| **Total** | $XXX | $XXX | $XXX | |

## Rental Income — Schedule E
Property: {address}
| Item | Amount |
|------|--------|
| Gross Rental Income | $XXX |
| Airbnb Service Fees | ($XXX) |
| Cleaning & Maintenance | ($XXX) |
| Insurance | ($XXX) |
| Mortgage Interest | ($XXX) |
| Property Taxes | ($XXX) |
| Utilities | ($XXX) |
| HOA | ($XXX) |
| Depreciation | ($XXX) |
| **Net Rental Income** | **$XXX** |

Days Rented: XXX | Personal Use: XXX

## Deductions
Standard Deduction: ${standard} vs Itemized: ${itemized_total}
Recommended: {standard or itemized}

## Missing Items
- {list of fields still blank}

## Notes for CPA
- {notes from YAML summary section}
```

### 3. Flag issues

Highlight any red flags:
- Gross rental income doesn't match 1099-K amount
- Capital loss exceeds $3,000 carry-forward limit
- Missing depreciation schedule
- Personal use days exceed 14-day / 10% threshold
- FMLA documentation incomplete

### 4. Offer export

Ask the user if they want to save as a markdown file at `~/docs/finance/taxes/TY{year}/cpa-summary-{year}.md`.

</div>

<div class="zoom-section zoom-section-5" markdown>

---

### Rationale

*Rationale not yet generated. Run `geno-docs compile --rationale` to generate LLM explanations for this skill.*

</div>

</div>

[:material-arrow-left: Back to geno-taxes](index.md)
