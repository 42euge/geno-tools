---
title: geno-budget
description: Personal budget and expense categorization
---

# geno-budget

Personal budget and expense categorization

[:material-github: GitHub](https://github.com/42euge/geno-budget){ .md-button }

## Overview

??? abstract "Skillset overview (from SKILL.md)"

    # geno-budget
    
    Expense categorization and budgeting skills for Claude Code. Imports transaction data from bank and credit card accounts, classifies each transaction as business (Airbnb rental) or personal, and exports categorized totals for tax prep.
    
    **Local-only skillset.** Financial data is sensitive; this repo is not published.
    
    ```bash
    geno-tools install /path/to/geno-budget
    ```
    
    ## Commands
    
    | Command | Description |
    |---|---|
    | `/gt-budget-fetch <platform> [year]` | Download transaction CSVs via browser automation |
    | `/gt-budget-import <file>` | Import transactions from a CSV/OFX/PDF bank statement |
    | `/gt-budget-categorize [year]` | Interactively classify uncategorized transactions as business/personal |
    | `/gt-budget-review [year]` | Show spending summary by category, flag anomalies |
    | `/gt-budget-export [year]` | Export business expenses grouped for Schedule E / CPA packet |
    
    ## Supported Platforms (fetch)
    
    | Platform | Script | Notes |
    |---|---|---|
    | Chase | `scripts/fetch-chase.mjs` | Checking + credit cards, custom date range |
    | Amex | `scripts/fetch-amex.mjs` | Activity download, ~2yr history |
    | US Bank | `scripts/fetch-usbank.mjs` | Export transactions, ~18mo history |
    | Venmo | `scripts/fetch-venmo.mjs` | 90-day online limit, use "Download my data" for full history |
    | Cash App | `scripts/fetch-cashapp.mjs` | Monthly statements only, SMS verification required |
    | PayPal | `scripts/fetch-paypal.mjs` | Activity download page, up to 7yr history |
    
    ## Data Storage
    
    All budget data lives in `~/docs/finance/budget/`:
    - `accounts.yaml` — registered bank/credit card accounts
    - `TY{year}/transactions.yaml` — all transactions with categories
    - `TY{year}/rules.yaml` — learned categorization rules
    - `TY{year}/export/` — CPA-ready exports
    
    ## Business vs Personal Classification
    
    For the Airbnb STR at Belltown Court #524, business expenses include:
    - Cleaning and laundry services
    - Supplies (linens, toiletries, kitchen items)
    - Furniture and furnishings
    - Repairs and maintenance
    - Utilities allocated to the rental
    - Insurance (renter's/landlord policy)
    - HOA dues (from geno-hoa)
    - Mortgage interest (from 1098)
    - Advertising / listing fees
    - Software subscriptions (Hospitable, PriceLabs, etc.)
    - Professional services (locksmith, handyman)
    - Travel to/from the property
    
    ## Integration
    
    - **geno-taxes**: `/gt-budget-export 2024` produces categorized expense totals for Schedule E line items
    - **geno-hoa**: HOA dues are auto-imported from `~/docs/home/hoa/annual-dues-summary.yaml`
    
    ## Runtime
    
    No venv or scripts — all commands are pure markdown workflows. `/gt-budget-import` can optionally use `geno-vla` for browser-based bank statement downloads.
