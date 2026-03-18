---
name: excel-lbo-modeler
description: |
  Creates leveraged buyout (LBO) models in Excel with sources & uses, debt schedules,
  cash flow waterfalls, and IRR calculations. Targets private equity and investment
  banking workflows.
  Use when asked to create an LBO model, build a buyout model, calculate PE returns,
  or analyze a leveraged acquisition.
  Trigger with "create an LBO model", "build a buyout model", "PE returns analysis",
  or "leveraged acquisition model".
  Make sure to use whenever the user needs private equity deal modeling in Excel.
allowed-tools: "Read,Write,Edit,Glob,Grep,Bash(npx:*),AskUserQuestion"
model: inherit
version: "2.0.0"
author: "Jeremy Longshore <jeremy@intentsolutions.io>"
license: "Proprietary"
compatible-with: claude-code
tags: [lbo, private-equity, financial-modeling, excel, investment-banking]
---

# Excel LBO Modeler

## Table of Contents
- [Overview](#overview) — [Prerequisites](#prerequisites) — [Instructions](#instructions) — [Output](#output) — [Examples](#examples) — [Error Handling](#error-handling) — [Resources](#resources)

## Overview

Generates comprehensive 6-sheet LBO models for private equity transactions following
industry-standard practices. Automates sources & uses, debt schedules, operating
projections, returns analysis, and covenant tracking so PE associates can produce
deal models from natural language inputs instead of building from scratch.

## Prerequisites

- Node.js 18+
- `@negokaz/excel-mcp-server` MCP server configured
- Claude Code 1.0+

## Instructions

### Step 1: Gather Transaction Inputs

Use AskUserQuestion to collect:

**Required:**
- Target company name
- Current year EBITDA (or TTM)
- Entry valuation multiple (EV/EBITDA, typically 8-12x)
- Revenue growth rates for Years 1-5
- EBITDA margin (and any expected expansion)
- Exit multiple assumption
- Hold period (typically 5 years)

**Optional (use defaults if not provided):**
- CapEx as % of revenue (default: 3%)
- NWC as % of revenue (default: 10%)
- Tax rate (default: 25%)
- Transaction fees (default: 2.5%)
- Financing fees (default: 2.5%)

### Step 2: Validate Inputs

Before building, verify:
- Entry multiple is 6-15x EBITDA
- Total leverage does not exceed 7x EBITDA
- Exit multiple is reasonable (typically <= entry multiple)
- Revenue growth rates are 0-30%
- EBITDA margin is positive and realistic for the sector

If validation fails, explain the issue and ask for corrected inputs.

### Step 3: Structure Financing

Apply typical LBO debt structure:
- **Revolver**: 1-2x EBITDA, undrawn at close
- **Term Loan A**: 2-2.5x EBITDA, 5-7 year amortization, SOFR + 3.50% (default: 8.5%)
- **Term Loan B**: 2-3x EBITDA, minimal amortization, SOFR + 4.50% (default: 9.5%)
- **Subordinated/Mezzanine**: 1-2x EBITDA if needed (default: 13.0%)
- **Sponsor Equity**: Remainder (typically 30-40% of purchase price)

### Step 4: Build 6-Sheet Model

Use the Excel MCP server to create:

**Sheet 1 - Transaction Summary:** Deal terms, sources & uses overview, returns summary (IRR, MoM, hold period).

**Sheet 2 - Sources & Uses:** Purchase equity value, net debt, enterprise value, transaction fees, financing fees. Sources: debt tranches + sponsor equity.

**Sheet 3 - Operating Model (5 Years):** Revenue projections, EBITDA, cash flow available for debt service.

**Sheet 4 - Debt Schedule:** For each tranche: beginning balance, mandatory amortization, excess cash flow sweep, interest expense, ending balance. Waterfall: Revolver first, then TLA, then TLB.

**Sheet 5 - Returns Analysis:** Exit EV, exit equity value, MoM, IRR. Sensitivity tables: Exit Multiple vs Hold Period, Exit vs Entry Multiple.

**Sheet 6 - Debt Covenants:** Total Debt/EBITDA (<=6.0x), Senior Debt/EBITDA (<=4.0x), EBITDA/Interest (>=2.0x), (EBITDA-CapEx)/Debt Service (>=1.2x).

All formulas link to Assumptions. No hard-coded values.

### Step 5: Format Professionally

- Currency format for monetary values
- Percentage format for rates (1 decimal)
- Freeze top row and left column
- Bold headers, cell borders
- Color-code: blue for inputs, black for formulas
- Conditional formatting on sensitivity tables

### Step 6: Return Results

Report exit equity value, MoM, IRR (base case), leverage at entry and exit, key sensitivity scenarios, covenant compliance summary. Flag if leverage >7x or negative cash flow in any year.

## Output

- `.xlsx` file with 6 sheets: Transaction Summary, Sources & Uses, Operating Model, Debt Schedule, Returns Analysis, Debt Covenants
- Summary text with IRR, MoM, leverage metrics, and covenant status
- Warnings for aggressive assumptions (e.g., leverage >7x, exit > entry multiple)

## Examples

### Standard LBO Request

```
User: "Build an LBO model for a $50M EBITDA software company at 12x"

Results:
- Entry EV: $600M, Equity Check: ~$265M
- Exit Equity: $1,124M (5yr hold, 12x exit)
- MoM: 4.2x, IRR: 34.2%
- Deleveraging: 7.0x -> 0.9x

Saved to: Software_LBO_Model.xlsx
```

### Minimal Inputs

```
User: "LBO model but I only know EBITDA is $30M"

Response: Uses PE industry defaults for sector.
All assumptions documented in Transaction Summary for easy adjustment.
```

## Error Handling

| Scenario | Response |
|----------|----------|
| Leverage >7x EBITDA | Warn structure may not be achievable, recommend reduction |
| Negative cash flow in any year | Flag concern, suggest reducing leverage or extending amortization |
| Exit multiple > entry multiple | Note assumption, flag as aggressive |
| IRR < 20% | Flag as below typical PE hurdle rate |
| Covenant breach in projections | Alert and suggest restructuring debt |

## Edge Cases

- If user provides no company name, use "Target Co" as placeholder
- If user wants dividend recap, add Year 3 refinancing scenario
- If user wants multiple scenarios, create Base/Bull/Bear columns

## Resources

- ${CLAUDE_SKILL_DIR}/references/REFERENCE.md - LBO best practices, debt structures by industry
