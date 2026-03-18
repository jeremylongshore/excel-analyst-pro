---
name: excel-dcf-modeler
description: |
  Builds discounted cash flow (DCF) valuation models in Excel with free cash flow
  projections, WACC calculations, and sensitivity analysis. Targets investment banking
  and corporate finance workflows.
  Use when asked to create a DCF model, calculate enterprise value, value a company,
  or build a valuation model.
  Trigger with "create a DCF model", "build a valuation", "calculate enterprise value",
  or "value this company".
  Make sure to use whenever the user needs company valuation or DCF analysis in Excel.
allowed-tools: "Read,Write,Edit,Glob,Grep,Bash(npx:*),AskUserQuestion"
model: inherit
version: "2.0.0"
author: "Jeremy Longshore <jeremy@intentsolutions.io>"
license: "Proprietary"
compatible-with: claude-code
tags: [dcf, valuation, financial-modeling, excel, investment-banking]
---

# Excel DCF Modeler

## Table of Contents
- [Overview](#overview) — [Prerequisites](#prerequisites) — [Instructions](#instructions) — [Output](#output) — [Examples](#examples) — [Error Handling](#error-handling) — [Resources](#resources)

## Overview

Generates professional 4-sheet DCF valuation models following investment banking standards.
Automates free cash flow projections, terminal value calculations, and sensitivity analysis
so analysts can produce IB-grade valuations from natural language inputs instead of building
Excel models from scratch.

## Prerequisites

- Node.js 18+
- `@negokaz/excel-mcp-server` MCP server configured
- Claude Code 1.0+

## Instructions

### Step 1: Gather Inputs

Use AskUserQuestion to collect:

**Required:**
- Company name and ticker symbol
- Base year revenue (most recent fiscal year)
- Revenue growth rates for Years 1-5 (e.g., 15%, 12%, 10%, 8%, 6%)
- EBITDA margin %
- Tax rate % (default: 21% for US)

**Optional (use defaults if not provided):**
- D&A as % of revenue (default: 5%)
- CapEx as % of revenue (default: 4%)
- NWC as % of revenue (default: 10%)
- Terminal growth rate (default: 2.5%)
- WACC / discount rate (default: 10%)
- Net debt amount (default: $0)
- Shares outstanding (for per-share value)

### Step 2: Validate Inputs

Before building, verify:
- Revenue growth rates are 0-30%
- EBITDA margin is positive
- Tax rate is 0-40%
- Terminal growth < WACC (model breaks if g >= WACC)
- WACC is 7-15%

If validation fails, explain the issue and ask for corrected inputs.

### Step 3: Build 4-Sheet Model

Use the Excel MCP server to create:

**Sheet 1 - Assumptions:**
Company info, revenue growth rates, profitability metrics, working capital, CapEx, tax rate, terminal growth, WACC. Color-code: blue for inputs, black for formulas.

**Sheet 2 - FCF Projections (5 years):**
Revenue -> EBITDA -> EBIT -> NOPAT -> add back D&A -> subtract CapEx -> subtract Change in NWC -> Unlevered Free Cash Flow. All formulas link to Assumptions sheet. No hard-coded values.

**Sheet 3 - Valuation:**
PV of each year's FCF, terminal value via Gordon Growth Model, PV of terminal value, enterprise value, equity value, per-share value.

**Sheet 4 - Sensitivity Analysis:**
Two-way table: WACC (rows, +/-2% from base) vs Terminal Growth (columns, 1.5%-3.5%). Output: Enterprise Value at each combination. Apply conditional formatting (green=high, red=low).

### Step 4: Format Professionally

- Currency format for monetary values
- Percentage format for rates (1 decimal)
- Freeze top row and left column
- Bold headers, cell borders
- Conditional formatting on sensitivity table

### Step 5: Return Results

Report enterprise value, equity value, per-share value, terminal value as % of EV (flag if >80%), key assumptions used, and brief commentary on reasonableness vs industry.

## Output

- `.xlsx` file with 4 sheets: Assumptions, FCF Projections, Valuation, Sensitivity Analysis
- Summary text with enterprise value, equity value, and key metrics
- Warnings for any concerning assumptions (e.g., terminal value >80% of EV)

## Examples

### Basic DCF Request

```
User: "Create a DCF model for Tesla"

Response: Gathers inputs via questions, builds 4-sheet model.

Results:
- Enterprise Value: $847.3B
- Terminal Value: 68% of EV
- Implied per share: $243

Saved to: Tesla_DCF_Model.xlsx
```

### Minimal Inputs

```
User: "Build a DCF but I don't have all the numbers"

Response: Uses industry-average assumptions for the company's sector.
All defaults documented in Assumptions sheet for easy adjustment.
```

## Error Handling

| Scenario | Response |
|----------|----------|
| Terminal growth >= WACC | Explain mathematical issue, ask for corrected values |
| Missing critical inputs | Build with industry defaults, document clearly |
| Terminal value >80% of EV | Flag as warning, recommend revisiting growth assumptions |
| Negative FCF in projection | Flag concern, suggest reviewing margin/CapEx assumptions |

## Edge Cases

- If user provides no company name, use "Company" as placeholder
- If revenue is in different currencies, note currency in all outputs
- If user wants multiple scenarios, create separate columns (Base/Bull/Bear)

## Resources

- ${CLAUDE_SKILL_DIR}/references/REFERENCE.md - DCF best practices, industry assumptions, common mistakes
