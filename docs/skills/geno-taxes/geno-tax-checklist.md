---
title: geno-tax-checklist
description: "Tax Document Checklist"
---

# geno-tax-checklist

`/geno-tax-checklist`

> "Tax Document Checklist"

<div class="zoom-depth" markdown>

<div class="zoom-section zoom-section-3" markdown>

## Input

`$ARGUMENTS` — Optional. Tax year (e.g., `2024`). If omitted, show all years.

</div>

<div class="zoom-section zoom-section-4" markdown>

---

## Workflow

### 1. Read sources

- Read `~/docs/finance/taxes/README.md` for the master checklist
- Read `~/docs/finance/taxes/TY{year}/tax-return-{year}.yaml` for filled fields
- List files in `TY{year}/` subdirectories to see what documents are already collected

### 2. Cross-reference

For each checklist item in README.md, check if:
1. The corresponding YAML field has data (→ filled from a document)
2. A matching file exists in the expected subdirectory (→ document collected but maybe not parsed)
3. Neither (→ still needed)

### 3. Output checklist

```
TY2024 Document Checklist
=========================

COLLECTED & PARSED
  Airbnb 1099-K .............. TY2024/airbnb/1099-K/
  Airbnb Earnings Report ..... TY2024/airbnb/income-summary/

COLLECTED, NOT YET PARSED
  {filename} ................. TY2024/investments/coinbase/
    Run: /geno-tax-parse TY2024/investments/coinbase/{filename}

STILL NEEDED
  W-2 from employer
    Download from your payroll portal (ADP, Gusto, Workday)
    Save to: TY2024/income/W2/

  State PFML statements
    Download from WA ESD: https://esd.wa.gov/
    Save to: TY2024/income/state-pfml/

  Coinbase tax documents
    Run: /geno-tax-fetch coinbase 2024
    Or manually: Coinbase > Taxes > Documents > Download

  Robinhood 1099
    Run: /geno-tax-fetch robinhood 2024
    Or manually: Robinhood > Account > Tax Documents

  Fidelity/Schwab 1099s
    Run: /geno-tax-fetch fidelity 2024
    Or manually: Fidelity > Accounts > Tax Forms

  Mortgage interest (1098)
    Check your mortgage servicer's portal
    Save to: TY2024/airbnb/mortgage-interest/

  Property tax statements
    King County: https://blue.kingcounty.com/Assessor/eRealProperty/
    Save to: TY2024/airbnb/property-tax/

  Rental expenses (cleaning, supplies, utilities, insurance, HOA)
    Gather receipts, bank/Venmo statements
    Run: /geno-tax-fetch venmo 2024 for Venmo history
    Save to: TY2024/airbnb/expenses/
```

### 4. Show progress

```
Progress: 2/14 items complete (14%)
Priority: Get W-2 and investment 1099s first — they unlock income totals
```

</div>

<div class="zoom-section zoom-section-5" markdown>

---

### Rationale

*Rationale not yet generated. Run `geno-docs compile --rationale` to generate LLM explanations for this skill.*

</div>

</div>

[:material-arrow-left: Back to geno-taxes](index.md)
