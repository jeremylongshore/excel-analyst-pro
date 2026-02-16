---
name: excel-lbo-modeler
description: |
  Creates leveraged buyout (LBO) models in Excel with sources & uses, debt schedules,
  cash flow waterfalls, and IRR calculations. Activates when asked to create an LBO model,
  build a buyout model, calculate PE returns, or analyze a leveraged acquisition.
  Targets private equity and investment banking workflows.
allowed-tools: "Read,Write,Edit,Glob,Grep,Bash(npx:*),AskUserQuestion"
model: inherit
metadata:
  author: ClaudeCodePlugins <plugins@claudecodeplugins.io>
  version: 2.0.0
  license: MIT
compatibility: "Node.js 18+, @negokaz/excel-mcp-server"
---

# Excel LBO Modeler

Creates comprehensive 6-sheet LBO models for private equity transactions following industry-standard practices.

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

**Sheet 1 - Transaction Summary:**
Deal terms, sources & uses overview, returns summary (IRR, MoM, hold period).

**Sheet 2 - Sources & Uses:**
```
Uses: Purchase Equity Value + Net Debt = Enterprise Value + Transaction Fees + Financing Fees = Total Uses
Sources: Revolver (0 at close) + Term Loan A + Term Loan B + Sub Debt + Sponsor Equity = Total Sources
```

**Sheet 3 - Operating Model (5 Years):**
```
Revenue x Growth % → Projected Revenue
Revenue x EBITDA Margin → EBITDA
EBITDA - CapEx - Change in NWC - Cash Taxes = Cash Flow Available for Debt Service
```

**Sheet 4 - Debt Schedule:**
For each tranche: Beginning Balance, Mandatory Amortization, Excess Cash Flow Sweep, Interest Expense, Ending Balance. Waterfall: Revolver first, then TLA, then TLB.

**Sheet 5 - Returns Analysis:**
```
Exit EBITDA x Exit Multiple = Exit Enterprise Value
Exit EV - Net Debt at Exit = Exit Equity Value
MoM = Exit Equity / Initial Equity
IRR = (MoM)^(1/Years) - 1
```
Include sensitivity tables: Exit Multiple vs Hold Period → IRR, Exit vs Entry Multiple → IRR.

**Sheet 6 - Debt Covenants:**
Total Debt/EBITDA (≤6.0x), Senior Debt/EBITDA (≤4.0x), EBITDA/Interest (≥2.0x), (EBITDA-CapEx)/Debt Service (≥1.2x).

All formulas link to Assumptions. No hard-coded values.

### Step 5: Format Professionally

- Currency format for monetary values
- Percentage format for rates (1 decimal)
- Freeze top row and left column
- Bold headers, cell borders
- Color-code: blue for inputs, black for formulas
- Conditional formatting on sensitivity tables

### Step 6: Return Results

Report to the user:
- Exit Equity Value and Money-on-Money multiple
- IRR (base case)
- Leverage at entry and exit
- Key sensitivity scenarios (10x exit, 14x exit)
- Covenant compliance summary
- Flag if leverage >7x or negative cash flow in any year

## Examples

### Standard LBO Request

```
User: "Build an LBO model for a $50M EBITDA software company at 12x"

Results:
- Entry EV: $600M, Equity Check: ~$265M
- Exit Equity: $1,124M (5yr hold, 12x exit)
- MoM: 4.2x, IRR: 34.2%
- Deleveraging: 7.0x → 0.9x

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
- If revenue is in different currencies, note currency throughout

## Resources

- {baseDir}/references/REFERENCE.md - LBO best practices, debt structures by industry
