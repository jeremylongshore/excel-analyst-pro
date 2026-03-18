---
name: excel-variance-analyzer
description: |
  Automates budget vs actual variance analysis in Excel with flagging, commentary,
  and executive summaries. Targets FP&A teams and financial reporting workflows.
  Use when asked to analyze budget variance, compare actual vs forecast, create a
  variance report, or explain budget differences.
  Trigger with "analyze budget variance", "compare actual vs forecast", "variance report",
  or "why are we over budget".
  Make sure to use whenever the user needs budget-to-actual analysis or financial variance reporting.
allowed-tools: "Read,Write,Edit,Glob,Grep,Bash(npx:*),AskUserQuestion"
model: inherit
version: "2.0.0"
author: "Jeremy Longshore <jeremy@intentsolutions.io>"
license: "Proprietary"
compatible-with: claude-code
tags: [variance-analysis, budgeting, fpa, excel, financial-reporting]
---

# Excel Variance Analyzer

## Table of Contents
- [Overview](#overview) — [Prerequisites](#prerequisites) — [Instructions](#instructions) — [Output](#output) — [Examples](#examples) — [Error Handling](#error-handling) — [Resources](#resources)

## Overview

Automates variance analysis for monthly/quarterly financial reporting and budget reviews.
Generates flagged variance reports with automated commentary and executive summaries so
FP&A teams can produce board-ready variance packages from raw budget and actual data
without manual spreadsheet work.

## Prerequisites

- Node.js 18+
- `@negokaz/excel-mcp-server` MCP server configured
- Claude Code 1.0+
- Budget and actual data in `.xlsx` or `.csv` format

## Instructions

### Step 1: Load Data

Use AskUserQuestion to collect:
- **Budget data**: Excel file, CSV, or pasted table
- **Actual data**: Same format as budget
- **Period**: Month, quarter, or YTD
- **Threshold settings** (or use defaults):
  - Percentage threshold: 10% (flag items >10% variance)
  - Dollar threshold: $50K (flag items >$50K absolute variance)

### Step 2: Validate Data

Before analysis, check:
- Budget and actual have matching line items
- All values are numeric
- No missing data for key categories (revenue, expenses, profit)
- Budget data is reasonable (no zeros where there should be values)

If mismatches found, report them and ask user to clarify.

### Step 3: Calculate Variances

For each line item:
- Absolute Variance = Actual - Budget
- Percentage Variance = (Actual - Budget) / Budget x 100%

**Sign Convention:** Revenue/profit: positive = Favorable. Expenses: positive = Unfavorable.

### Step 4: Flag Material Items

| Flag | Criteria |
|------|----------|
| Critical (red) | Revenue/profit >10% below budget, expenses >10% over, or absolute >$100K |
| Warning (yellow) | Revenue/profit 5-10% below, expenses 5-10% over, or absolute $50K-$100K |
| On Track (green) | Variance within +/-5% and absolute <$50K |

### Step 5: Generate Commentary

For each flagged item, provide automated commentary explaining what happened (variance in dollars and percentage), possible drivers (2-3 likely causes), and recommended action.

### Step 6: Build 3-Sheet Report

Use the Excel MCP server to create:

**Sheet 1 - Variance Summary:** Table with columns: Line Item, Budget, Actual, Variance, % Var, Flag, Commentary. Conditional formatting (green/yellow/red) based on flagging rules.

**Sheet 2 - Executive Summary:** Performance highlights, top 5 unfavorable variances, top 5 favorable variances, key action items.

**Sheet 3 - Trend Analysis** (if multiple periods provided): Variance % by month/quarter with trend indicators (improving/worsening/flat).

### Step 7: Format Professionally

- Currency: $1,000K or $1.0M
- Percentages: 1 decimal place
- Variance: $(50K) for unfavorable, $50K for favorable
- Conditional formatting: green (favorable >5%), yellow (within +/-5%), red (unfavorable >5%)
- Bold headers, freeze top row and left column

### Step 8: Return Results

Report overall performance summary, top 3 critical variances with drivers, recommended actions, and offer follow-up (trend analysis, drill-down, forecast scenarios).

## Output

- `.xlsx` file with 3 sheets: Variance Summary, Executive Summary, Trend Analysis
- Summary text with performance highlights and critical variances
- Actionable recommendations for each flagged item

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
Primary driver: Digital ads campaign expansion.
```

## Error Handling

| Scenario | Response |
|----------|----------|
| Budget and actual don't match | List mismatches, ask user to reconcile |
| Division by zero (budget = $0) | Show absolute variance only, flag for review |
| All variances within threshold | Report clean bill of health, suggest lowering thresholds |
| Negative budget values | Ask user to confirm sign convention |

## Edge Cases

- If no period specified, ask user or default to most recent month
- If user provides only one dataset, ask for the comparison dataset
- If data includes non-financial line items, exclude from variance calculations
- If user wants forecast comparison instead of budget, same workflow applies

## Resources

- ${CLAUDE_SKILL_DIR}/references/REFERENCE.md - Variance analysis best practices, sign conventions
