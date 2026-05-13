---
title: geno-taxes
description: Tax filing — document parsing, checklists, CPA packet prep
---

# geno-taxes

Tax filing — document parsing, checklists, CPA packet prep

[:material-github: GitHub](https://github.com/42euge/geno-taxes){ .md-button }

## Skills

| Skill | Slash command | Description |
|-------|--------------|-------------|
| [geno-tax-checklist](#geno-tax-checklist) | `/geno-tax-checklist` | "Tax Document Checklist" |
| [geno-tax-fetch](#geno-tax-fetch) | `/geno-tax-fetch` | Retrieve tax documents from financial platforms using geno-vla (Playwright browser automation). |
| [geno-tax-parse](#geno-tax-parse) | `/geno-tax-parse` | "Parse Tax Document" |
| [geno-tax-status](#geno-tax-status) | `/geno-tax-status` | "Tax Filing Status" |
| [geno-tax-summary](#geno-tax-summary) | `/geno-tax-summary` | "Tax Year Summary for CPA" |

## geno-tax-checklist

**Slash command:** `/geno-tax-checklist`

> "Tax Document Checklist"

??? example "Full skill definition (Level 4)"

    Show remaining documents needed for a specific tax year with instructions on where to get them.
    
    ## Input
    
    `$ARGUMENTS` — Optional. Tax year (e.g., `2024`). If omitted, show all years.
    
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
        Run: /gt-tax-parse TY2024/investments/coinbase/{filename}
    
    STILL NEEDED
      W-2 from employer
        Download from your payroll portal (ADP, Gusto, Workday)
        Save to: TY2024/income/W2/
    
      State PFML statements
        Download from WA ESD: https://esd.wa.gov/
        Save to: TY2024/income/state-pfml/
    
      Coinbase tax documents
        Run: /gt-tax-fetch coinbase 2024
        Or manually: Coinbase > Taxes > Documents > Download
    
      Robinhood 1099
        Run: /gt-tax-fetch robinhood 2024
        Or manually: Robinhood > Account > Tax Documents
    
      Fidelity/Schwab 1099s
        Run: /gt-tax-fetch fidelity 2024
        Or manually: Fidelity > Accounts > Tax Forms
    
      Mortgage interest (1098)
        Check your mortgage servicer's portal
        Save to: TY2024/airbnb/mortgage-interest/
    
      Property tax statements
        King County: https://blue.kingcounty.com/Assessor/eRealProperty/
        Save to: TY2024/airbnb/property-tax/
    
      Rental expenses (cleaning, supplies, utilities, insurance, HOA)
        Gather receipts, bank/Venmo statements
        Run: /gt-tax-fetch venmo 2024 for Venmo history
        Save to: TY2024/airbnb/expenses/
    ```
    
    ### 4. Show progress
    
    ```
    Progress: 2/14 items complete (14%)
    Priority: Get W-2 and investment 1099s first — they unlock income totals
    ```

## geno-tax-fetch

**Slash command:** `/geno-tax-fetch`

> Retrieve tax documents from financial platforms using geno-vla (Playwright browser automation).

??? example "Full skill definition (Level 4)"

    Retrieve tax documents from financial platforms using geno-vla (Playwright browser automation).
    
    ## Input
    
    `$ARGUMENTS` — Required. Format: `<platform> [year]`
    - Platform: `coinbase`, `robinhood`, `fidelity`, `schwab`, `venmo`
    - Year: defaults to 2024 if omitted
    
    Examples:
    - `/gt-tax-fetch coinbase 2024`
    - `/gt-tax-fetch robinhood 2025`
    - `/gt-tax-fetch venmo 2024`
    
    ## Prerequisites
    
    - geno-vla MCP server must be running (registered in `~/.claude/.mcp.json`)
    - User should be logged into the platform in their Chrome profile (`~/.geno/chrome-profiles/`)
    - If not logged in, open a headed browser first: ask user to run `! open <login-url>` in their browser
    
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
    
    After downloading, read the files and extract data following the gt-tax-parse workflow.
    Update the YAML organizer. Always confirm changes with the user before writing.
    
    ### 7. Report results
    
    Show what was downloaded, where it was saved, and what YAML fields were updated.
    If any documents were unavailable, explain why and suggest alternatives.
    
    ## Error Handling
    
    - **Login required**: Tell the user to log in manually. Suggest: `! open <url>` to open in their browser.
    - **Document not available**: Some platforms don't issue 1099s below certain thresholds. Note this.
    - **Download failed**: Retry once, then fall back to manual instructions.
    - **Wrong year**: If the platform doesn't have docs for the requested year, list what IS available.

## geno-tax-parse

**Slash command:** `/geno-tax-parse`

> "Parse Tax Document"

??? example "Full skill definition (Level 4)"

    Parse a tax document (PDF or CSV) and populate the corresponding YAML organizer.
    
    ## Input
    
    `$ARGUMENTS` — Required. Path to a file. Examples:
    - `/gt-tax-parse ~/Downloads/W2-2024.pdf`
    - `/gt-tax-parse ~/Downloads/1099-B-robinhood.pdf`
    - `/gt-tax-parse ~/Downloads/coinbase-gains.csv`
    
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

## geno-tax-status

**Slash command:** `/geno-tax-status`

> "Tax Filing Status"

??? example "Full skill definition (Level 4)"

    Show the document collection and data entry status across all tax years.
    
    ## Input
    
    `$ARGUMENTS` — Optional. A specific tax year (e.g., `2024`). If omitted, show all years.
    
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

## geno-tax-summary

**Slash command:** `/geno-tax-summary`

> "Tax Year Summary for CPA"

??? example "Full skill definition (Level 4)"

    Generate a clean, CPA-ready summary of a tax year from the YAML organizer.
    
    ## Input
    
    `$ARGUMENTS` — Required. Tax year (e.g., `2024`, `2025`, `2023`).
    
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
