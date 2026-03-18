# Pivot Table Best Practices

## Overview

Pivot tables are the primary tool for data summarization and cross-tabulation in Excel. This guide covers layout patterns, aggregation selection, chart pairing, and formatting standards.

## Pivot Table Layout Patterns

### Single Dimension (1D)
- **Use when**: Summarizing one metric across one category
- **Example**: Total sales by region
- **Layout**: Category in rows, metric in values
- **Best chart**: Bar chart (horizontal) or column chart (vertical)

### Cross-Tabulation (2D)
- **Use when**: Comparing a metric across two dimensions
- **Example**: Sales by region and product category
- **Layout**: Dimension 1 in rows, Dimension 2 in columns, metric in values
- **Best chart**: Heatmap or clustered column chart

### Hierarchical (Nested)
- **Use when**: Drill-down from broad to specific categories
- **Example**: Sales by region > state > city
- **Layout**: Multiple row fields in hierarchy order
- **Best chart**: Treemap or sunburst

### Time Series
- **Use when**: Showing trends over time
- **Example**: Monthly revenue for the past 12 months
- **Layout**: Date field in rows (grouped by month/quarter), metric in values
- **Best chart**: Line chart

## Aggregation Selection

| Data Type | Default | Alternatives |
|-----------|---------|-------------|
| Currency (revenue, cost) | SUM | AVERAGE, MAX, MIN |
| Counts (orders, units) | SUM or COUNT | AVERAGE |
| Rates (%, ratio) | AVERAGE | MEDIAN (not native in pivots) |
| Dates | COUNT | MIN (earliest), MAX (latest) |
| Text | COUNT | COUNTA (non-blank) |

### Calculated Fields
- **Profit Margin**: = (Revenue - Cost) / Revenue
- **Growth %**: = (Current - Previous) / Previous
- **% of Total**: = Value / Grand Total
- **Average Order Value**: = Revenue / Order Count
- **Year-over-Year Change**: = (This Year - Last Year) / Last Year

## Chart Selection Guide

| Analysis Goal | Primary Chart | Alternative |
|--------------|---------------|-------------|
| Compare categories | Column chart | Bar chart (many categories) |
| Show trends | Line chart | Area chart (cumulative) |
| Show composition | Stacked bar | Pie chart (<=5 segments) |
| Show distribution | Histogram | Box plot |
| Show correlation | Scatter plot | Bubble chart (3 variables) |
| Show concentration | Pareto chart | Bar + cumulative line |
| Compare multiple metrics | Combo chart | Dual-axis line |
| Show geographic data | Map chart | Filled map |

### Chart Formatting Standards
- Title: Clear, descriptive (e.g., "Q1 2025 Sales by Region")
- Axis labels: Include units ($, %, count)
- Legend: Only if multiple series
- Data labels: On bar/column charts with few bars
- Grid lines: Subtle, horizontal only
- Colors: Consistent palette, max 6-7 colors

## Conditional Formatting

### Standard Rules
- **Top N**: Dark green fill for top 10% values
- **Bottom N**: Dark red fill for bottom 10% values
- **Gradient**: Green -> Yellow -> Red for performance metrics
- **Data bars**: For easy visual comparison within a column
- **Icon sets**: Arrows for trend direction

### When to Use
- Heatmaps: Cross-tabulation tables
- Data bars: Single-column comparisons
- Icons: Status indicators (up/down/flat)
- Color scales: Large tables where patterns matter

## Sorting Best Practices

| Field Type | Default Sort |
|-----------|-------------|
| Text categories | Largest to smallest by value |
| Dates | Chronological (oldest first) |
| Ranked items | Descending by rank metric |
| Alphabetical | Only when no meaningful metric to sort by |

## Data Quality Checks

Before building pivot tables, verify:
1. **Headers**: Every column has a clear, unique header
2. **Data types**: Consistent within each column (no mixed text/numbers)
3. **Blanks**: Identify and handle (exclude, fill, or flag)
4. **Duplicates**: Check for duplicate rows that would inflate aggregations
5. **Date formats**: Consistent date format for grouping to work
6. **Outliers**: Identify extreme values that may skew aggregations

## Common Mistakes

### 1. Wrong Aggregation
- Using SUM for rates or percentages (should use AVERAGE or weighted average)
- Using COUNT when COUNTA is needed (COUNT ignores text)

### 2. Too Many Categories
- Pivot tables with >50 rows become unreadable
- Solution: Use Top N filter or group small categories into "Other"

### 3. Missing Totals
- Always include grand totals for context
- Subtotals for hierarchical pivots

### 4. Poor Chart Choice
- Pie charts with >5 segments are unreadable
- 3D charts distort proportions — avoid them
- Dual-axis charts can mislead if scales aren't comparable
