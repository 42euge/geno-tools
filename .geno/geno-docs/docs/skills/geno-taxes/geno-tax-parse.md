---
title: geno-tax-parse
description: "Parse Tax Document"
---

# geno-tax-parse

`/geno-tax-parse`

> "Parse Tax Document"

<div class="zoom-depth" markdown>

<div class="zoom-section zoom-section-3" markdown>

## Input

`$ARGUMENTS` — Required. Path to a file. Examples:
- `/gt-tax-parse ~/Downloads/W2-2024.pdf`
- `/gt-tax-parse ~/Downloads/1099-B-robinhood.pdf`
- `/gt-tax-parse ~/Downloads/coinbase-gains.csv`

</div>

<div class="zoom-section zoom-section-4" markdown>

---

## Workflow

### 1. Read the file

Use the Read tool to read the document. Supports:
- **PDF**: W-2, 1099-K, 1099-B, 1099-MISC, 1099-DIV, 1099-INT, 1099-NEC, 1098, 1098-E, earnings reports
- **CSV**: Coinbase gain/loss exports, Robinhood transaction history, Venmo statements, bank statements

### 2. Detect document type

Identify the document by looking for:
- **W-2**: "Wage and Tax Statement", Box labels (Box 1 Wages, Box 2 Federal tax withheld)
- **1099-K**: "Payment Card and Third Party Network Transactions", Box 1a
- **1099-B**: "Proceeds From Broker", short-term/long-term sections
- **1099-MISC**: "Miscellaneous Information" (staking rewards, etc.)
- **1099-DIV**: "Dividends and Distributions"
- **1099-INT**: "Interest Income"
- **1098**: "Mortgage Interest Statement"
- **1098-E**: "Student Loan Interest Statement"
- **Airbnb earnings**: "Earnings report", Airbnb header, monthly breakdown
- **Coinbase CSV**: Headers like "Transaction Type", "Asset", "Proceeds", "Cost Basis"
- **Venmo CSV**: Headers like "Datetime", "Type", "From", "To", "Amount"

### 3. Determine tax year

Extract the tax year from the document. If ambiguous, ask the user.

### 4. Extract data

Pull all relevant fields based on document type. For example:
- **W-2**: employer, EIN, wages (Box 1), federal withheld (Box 2), SS wages (3), SS tax (4), Medicare wages (5), Medicare tax (6), state (15), state wages (16), state tax withheld (17)
- **1099-K**: gross amount (1a), monthly breakdown (5a-5l), number of transactions (3)
- **Coinbase CSV**: Aggregate by holding period (short/long term), compute total proceeds, cost basis, net gain/loss

### 5. Show extracted data and confirm

Display the extracted values to the user in a clear format. Ask for confirmation before writing.

### 6. Update YAML

Read the corresponding `~/docs/finance/taxes/TY{year}/tax-return-{year}.yaml` and update the relevant section using the Edit tool.

### 7. File the source document

Copy/move the source file to the appropriate subdirectory:
- W-2 → `TY{year}/income/W2/`
- 1099-K → `TY{year}/airbnb/1099-K/` or `TY{year}/investments/{platform}/`
- 1099-B → `TY{year}/investments/{platform}/`
- etc.

Ask user before moving.

</div>

<div class="zoom-section zoom-section-5" markdown>

---

### Rationale

*Rationale not yet generated. Run `geno-docs compile --rationale` to generate LLM explanations for this skill.*

</div>

</div>

[:material-arrow-left: Back to geno-taxes](index.md)
