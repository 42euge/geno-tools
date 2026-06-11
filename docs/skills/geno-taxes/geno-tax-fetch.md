---
title: geno-tax-fetch
description: Retrieve tax documents from financial platforms using geno-vla (Playwright browser automation).
---

# geno-tax-fetch

`/geno-tax-fetch`

> Retrieve tax documents from financial platforms using geno-vla (Playwright browser automation).

<div class="zoom-depth" markdown>

<div class="zoom-section zoom-section-3" markdown>

## Input

`$ARGUMENTS` — Required. Format: `<platform> [year]`
- Platform: `coinbase`, `robinhood`, `fidelity`, `schwab`, `venmo`
- Year: defaults to 2024 if omitted

Examples:
- `/geno-tax-fetch coinbase 2024`
- `/geno-tax-fetch robinhood 2025`
- `/geno-tax-fetch venmo 2024`


## Prerequisites

- geno-vla MCP server must be running (registered in `~/.claude/.mcp.json`)
- User should be logged into the platform in their Chrome profile (`~/.geno/chrome-profiles/`)
- If not logged in, open a headed browser first: ask user to run `! open <login-url>` in their browser

</div>

<div class="zoom-section zoom-section-4" markdown>

---

## Workflow

### 1. Parse arguments

Extract platform and year from `$ARGUMENTS`.

### 2. Navigate to tax documents page

Use `geno_navigate` to go to the platform's tax documents page:

| Platform | URL |
|----------|-----|
| Coinbase | `https://accounts.coinbase.com/taxes/documents` |
| Robinhood | `https://robinhood.com/account/tax-documents` |
| Fidelity | `https://digital.fidelity.com/ftgw/digital/tax-forms` |
| Schwab | `https://client.schwab.com/app/accounts/taxstatements` |
| Venmo | `https://account.venmo.com/statement` |

### 3. Observe the page

Use `geno_observe` to capture the page state. Look for:
- Login walls (if so, ask user to log in manually)
- Available tax year documents
- Download buttons/links

### 4. Platform-specific retrieval

#### Coinbase
1. Look for tax year selector or tabs
2. Find "Download" links for:
   - 1099-MISC (staking/rewards income)
   - Gain/Loss Report (CSV) — this is the most useful
   - Transaction history CSV
3. Use `geno_interact` to click download for each
4. Target directory: `~/docs/finance/taxes/TY{year}/investments/coinbase/`

#### Robinhood
1. Find the consolidated 1099 for the target year
2. May have combined 1099-B + 1099-DIV + 1099-INT in one PDF
3. Use `geno_interact` to download
4. Target directory: `~/docs/finance/taxes/TY{year}/investments/robinhood/`

#### Fidelity / Schwab
1. Find available 1099 forms (1099-B, 1099-DIV, 1099-INT)
2. Download each form
3. Target directory: `~/docs/finance/taxes/TY{year}/investments/fidelity-schwab/`

#### Venmo
1. Look for statement/transaction download options
2. Set date range to Jan 1 - Dec 31 of target year
3. Use `geno_fill_form` to set date range if needed
4. Download CSV
5. Target directory: `~/docs/finance/taxes/TY{year}/airbnb/expenses/` (for expense cross-referencing)

### 5. Move downloaded files

Check the default download directory (`~/Downloads/`) for newly downloaded files.
Move them to the appropriate tax folder using bash `mv`.

### 6. Auto-parse

After downloading, read the files and extract data following the /geno-tax-parse workflow.
Update the YAML organizer. Always confirm changes with the user before writing.

### 7. Report results

Show what was downloaded, where it was saved, and what YAML fields were updated.
If any documents were unavailable, explain why and suggest alternatives.

## Error Handling

- **Login required**: Tell the user to log in manually. Suggest: `! open <url>` to open in their browser.
- **Document not available**: Some platforms don't issue 1099s below certain thresholds. Note this.
- **Download failed**: Retry once, then fall back to manual instructions.
- **Wrong year**: If the platform doesn't have docs for the requested year, list what IS available.

</div>

<div class="zoom-section zoom-section-5" markdown>

---

### Rationale

- **Explicit don'ts** — negative constraints are crucial for LLM-driven workflows. Without them, agents drift toward plausible-but-wrong approaches.

</div>

</div>

[:material-arrow-left: Back to geno-taxes](index.md)
