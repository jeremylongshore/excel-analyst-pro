---
name: excel-variance-analyzer
description: |
  Automates budget vs actual variance analysis in Excel with flagging, commentary,
  and executive summaries. Activates when asked to analyze budget variance, compare
  actual vs forecast, create a variance report, or explain budget differences.
  Targets FP&A teams and financial reporting workflows.
allowed-tools: "Read,Write,Edit,Glob,Grep,Bash(npx:*),AskUserQuestion"
model: inherit
metadata:
  author: ClaudeCodePlugins <plugins@claudecodeplugins.io>
  version: 2.0.0
  license: MIT
compatibility: "Node.js 18+, @negokaz/excel-mcp-server"
---

# Excel Variance Analyzer

Automates variance analysis for monthly/quarterly financial reporting and budget reviews.

## Instructions

### Step 1: Load Data

Use AskUserQuestion to collect:
- **Budget data**: Excel file, CSV, or pasted table
- **Actual data**: Same format as budget
- **Period**: Month, quarter, or YTD
- **Threshold settings** (or use defaults):
  - Percentage threshold: 10% (flag items >10% variance)
  - Dollar threshold: $50K (flag items >$50K absolute variance)
  - Categories to exclude (e.g., non-cash items like depreciation)

### Step 2: Validate Data

Before analysis, check:
- Budget and actual have matching line items
- All values are numeric
- No missing data for key categories (revenue, expenses, profit)
- Budget data is reasonable (no zeros where there should be values)

If mismatches found, report them and ask user to clarify.

### Step 3: Calculate Variances

For each line item:
```
Absolute Variance = Actual - Budget
Percentage Variance = (Actual - Budget) / Budget x 100%
```

**Sign Convention:**
- Revenue/profit: positive variance = Favorable, negative = Unfavorable
- Expenses: positive variance = Unfavorable, negative = Favorable

### Step 4: Flag Material Items

Apply flagging rules:

| Flag | Criteria |
|------|----------|
| Critical (red) | Revenue/profit >10% below budget, expenses >10% over, or absolute >$100K |
| Warning (yellow) | Revenue/profit 5-10% below, expenses 5-10% over, or absolute $50K-$100K |
| On Track (green) | Variance within +/-5% and absolute <$50K |

### Step 5: Generate Commentary

For each flagged item, provide automated commentary explaining:
- What happened (the variance in dollars and percentage)
- Possible drivers (2-3 likely causes)
- Recommended action (specific next step)

### Step 6: Build 3-Sheet Report

Use the Excel MCP server to create:

**Sheet 1 - Variance Summary:**
Table with columns: Line Item, Budget, Actual, Variance, % Var, Flag, Commentary.
Apply conditional formatting (green/yellow/red) based on flagging rules.

**Sheet 2 - Executive Summary:**
- Performance highlights (revenue, EBITDA vs budget)
- Top 5 unfavorable variances with amounts and percentages
- Top 5 favorable variances
- Key action items and strategic questions

**Sheet 3 - Trend Analysis** (if multiple periods provided):
Table showing variance % by month/quarter with trend indicators (improving/worsening/flat).

### Step 7: Format Professionally

- Currency: $1,000K or $1.0M (K for thousands, M for millions)
- Percentages: 1 decimal place (5.0%)
- Variance: Show sign - $(50K) for unfavorable, $50K for favorable
- Conditional formatting: green (favorable >5%), yellow (within +/-5%), red (unfavorable >5%)
- Bold headers, freeze top row and left column

### Step 8: Return Results

Report to the user:
- Overall performance summary (revenue and EBITDA vs budget)
- Top 3 critical variances with drivers
- Recommended immediate actions
- Offer follow-up: trend analysis, drill-down into specific categories, forecast scenarios

## Examples

### Standard Variance Analysis

```
User: "Analyze Q1 budget vs actual"

Results:
- Revenue: $2,850K vs $3,000K budget (-5.0%)
- EBITDA: $270K vs $450K budget (-40.0%)
- Key driver: OpEx 12% over budget ($90K)
- Action: Review Q2 pipeline, evaluate marketing ROI

Saved to: Q1_2025_Variance_Analysis.xlsx
```

### Drill-Down Request

```
User: "Why is marketing over budget?"

Response: Breaks down marketing by subcategory:
- Digital Ads: +$30K (campaign expansion)
- Events: +$15K (added trade show)
- Agencies: +$15K (new retainer)
- Content: +$5K (video production)
Primary driver: Digital ads campaign expansion.
```

## Error Handling

| Scenario | Response |
|----------|----------|
| Budget and actual line items don't match | List mismatches, ask user to reconcile |
| Division by zero (budget = $0) | Show absolute variance only, flag for review |
| All variances within threshold | Report clean bill of health, suggest lowering thresholds |
| Negative budget values | Ask user to confirm sign convention |
| Multiple periods with inconsistent formats | Standardize and note assumptions |

## Edge Cases

- If no period specified, ask user or default to most recent month
- If user provides only one dataset, ask for the comparison dataset
- If data includes non-financial line items, exclude from variance calculations
- If user wants forecast comparison instead of budget, same workflow applies

## Resources

- {baseDir}/references/REFERENCE.md - Variance analysis best practices, sign conventions
