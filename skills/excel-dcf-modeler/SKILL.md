---
name: excel-dcf-modeler
description: |
  Builds discounted cash flow (DCF) valuation models in Excel with free cash flow
  projections, WACC calculations, and sensitivity analysis. Activates when asked to
  create a DCF model, calculate enterprise value, value a company, or build a
  valuation model. Targets investment banking and corporate finance workflows.
allowed-tools: "Read,Write,Edit,Glob,Grep,Bash(npx:*),AskUserQuestion"
model: inherit
metadata:
  author: ClaudeCodePlugins <plugins@claudecodeplugins.io>
  version: 2.0.0
  license: MIT
compatibility: "Node.js 18+, @negokaz/excel-mcp-server"
---

# Excel DCF Modeler

Creates professional 4-sheet DCF valuation models following investment banking standards.

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
```
Revenue
  x EBITDA Margin
= EBITDA
  - D&A
= EBIT
  x (1 - Tax Rate)
= NOPAT
  + D&A (add back)
  - CapEx
  - Change in NWC
= Unlevered Free Cash Flow
```

All formulas link to Assumptions sheet. No hard-coded values.

**Sheet 3 - Valuation:**
```
PV of each year's FCF = FCF / (1 + WACC)^n
Sum of PV(FCF) for Years 1-5

Terminal Value = FCF_Y5 x (1 + g) / (WACC - g)
PV of Terminal Value = TV / (1 + WACC)^5

Enterprise Value = Sum PV(FCF) + PV(Terminal Value)
Equity Value = EV - Net Debt + Non-Operating Assets
Per Share = Equity Value / Shares Outstanding
```

**Sheet 4 - Sensitivity Analysis:**
Two-way table: WACC (rows, +/-2% from base) vs Terminal Growth (columns, 1.5%-3.5%). Output: Enterprise Value at each combination. Apply conditional formatting (green=high, red=low).

### Step 4: Format Professionally

- Currency format for monetary values
- Percentage format for rates (1 decimal)
- Freeze top row and left column
- Bold headers, cell borders
- Conditional formatting on sensitivity table

### Step 5: Return Results

Report to the user:
- Enterprise Value
- Equity Value (if net debt provided)
- Per-share value (if shares provided)
- Terminal value as % of EV (flag if >80%)
- Key assumptions used
- Brief commentary on reasonableness vs industry

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

- {baseDir}/references/REFERENCE.md - DCF best practices, industry assumptions, common mistakes
