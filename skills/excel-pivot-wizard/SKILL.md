---
name: excel-pivot-wizard
description: |
  Generates pivot tables and charts from raw data using natural language commands.
  Activates when asked to create a pivot table, summarize data by category, analyze
  sales by region, show revenue breakdowns, or build cross-tab analyses.
  Targets business analysts and data teams working in Excel.
allowed-tools: "Read,Write,Edit,Glob,Grep,Bash(npx:*),AskUserQuestion"
model: inherit
metadata:
  author: ClaudeCodePlugins <plugins@claudecodeplugins.io>
  version: 2.0.0
  license: MIT
compatibility: "Node.js 18+, @negokaz/excel-mcp-server"
---

# Excel Pivot Wizard

Creates pivot tables and visualizations from raw data using natural language commands.

## Instructions

### Step 1: Understand the Data

Read the source Excel file and identify:
- Column names and data types
- Data grain (transaction-level, daily summary, etc.)
- Which fields are dimensions (group by) vs measures (aggregate)
- Row count and date range

If unclear, use AskUserQuestion to clarify:
- What does each column represent?
- What fields should be aggregated vs grouped?
- What aggregation function (sum, average, count)?

### Step 2: Interpret the Request

Parse natural language into pivot table structure:

| Request | Rows | Columns | Values |
|---------|------|---------|--------|
| "Show sales by region" | Region | — | Sum of Sales |
| "Sales by region and month" | Region | Month | Sum of Sales |
| "Average order value by segment" | Segment | — | Avg of Order Value |
| "Count orders by category and rep" | Category | Sales Rep | Count of Orders |

### Step 3: Build the Pivot Table

Use the Excel MCP server to:
1. Create pivot table on a new sheet
2. Set row fields (one or more dimensions)
3. Set column fields if cross-tabulation requested
4. Set value fields with correct aggregation (sum, average, count, min, max)
5. Add subtotals and grand totals
6. Sort largest to smallest by default (chronological for dates)

### Step 4: Add Enhancements

**Calculated Fields** (if applicable):
- Profit Margin % = (Revenue - Cost) / Revenue
- Growth % = (This Year - Last Year) / Last Year
- % of Total = Value / Grand Total

**Conditional Formatting:**
- Top 10% values: Dark green
- Bottom 10% values: Dark red
- Color gradient for heatmap effect

**Sorting:**
- Largest to smallest by default
- Chronological for date fields

### Step 5: Create Visualization

Choose chart type based on analysis pattern:

| Pattern | Chart Type |
|---------|-----------|
| Comparisons across categories | Column/bar chart |
| Trends over time | Line chart |
| Composition/share | Pie/donut chart |
| Correlations | Scatter plot |
| Multiple metrics | Combo chart (column + line) |

### Step 6: Format Professionally

- Currency: $1,250,000 or $1.25M
- Counts: thousands separator (2,000)
- Percentages: 1 decimal place (35.0%)
- Bold headers, freeze top row and left column
- Alternating row colors for readability

### Step 7: Return Results

Report to the user:
- Summary of what the pivot table shows
- Top 3-5 key insights from the data
- Specific numbers for standout findings
- Suggested follow-up analyses
- Offer to add slicers, filters, or drill-downs

## Examples

### Single Dimension Summary

```
User: "Show total sales by region"

Output:
| Region    | Total Sales |
|-----------|-------------|
| West      | $1,450,000  |
| Northeast | $1,250,000  |
| Midwest   | $1,100,000  |
| Southeast | $980,000    |
| Total     | $4,780,000  |

Insight: West leads at 30.3% of total sales.
```

### Cross-Tabulation

```
User: "Sales by region and product category"

Output: 4x3 grid with row/column totals.
Insight: West + Electronics = highest cell at $550K.
```

### Top N Analysis

```
User: "Top 10 products by revenue"

Output: Ranked table with revenue, orders, AOV, % of total.
Insight: Top 10 = 62.5% of revenue (strong concentration).
Created: Bar chart + Pareto chart.
```

## Error Handling

| Scenario | Response |
|----------|----------|
| No numeric columns found | Ask user which field to aggregate |
| Ambiguous dimension field | List options and ask user to choose |
| Too many categories (>50 rows) | Suggest Top N or grouping approach |
| Missing data in key columns | Report % missing, offer to exclude nulls |
| Date field not recognized | Ask user to confirm date column and format |

## Edge Cases

- If data has no headers, infer from content or ask user
- If user asks for "breakdown" without specifying metric, default to count
- If multiple numeric columns exist, ask which to aggregate
- If data spans multiple sheets, ask which sheet to analyze

## Resources

- {baseDir}/references/REFERENCE.md - Pivot table best practices, chart selection guide
