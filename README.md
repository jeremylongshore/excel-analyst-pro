# Excel Analyst Pro

Professional financial modeling toolkit for Claude Code with auto-invoked Skills and Excel MCP integration.

Build DCF models, LBO analysis, variance reports, and pivot tables using natural language. No formulas to remember, no manual Excel work.

## Features

- **DCF Modeler**: Discounted cash flow valuation models with projections, WACC, and sensitivity analysis
- **LBO Modeler**: Leveraged buyout models with debt schedules, cash flow waterfalls, and IRR calculations
- **Variance Analyzer**: Budget vs actual analysis with flagging, commentary, and executive summaries
- **Pivot Wizard**: Pivot tables and charts from raw data using natural language

## Installation

### Prerequisites
- Claude Code 1.0+
- Node.js 18+

### Install
```bash
/plugin install excel-analyst-pro
```

This automatically configures `@negokaz/excel-mcp-server` and loads all 4 Skills.

## Usage

### DCF Valuation
```
"Create a DCF model for Tesla with $96.8B revenue and 25% growth"
```
Produces a 4-sheet Excel workbook: Assumptions, FCF Projections, Valuation, Sensitivity Analysis.

### LBO Analysis
```
"Build an LBO model for a $50M EBITDA software company at 12x"
```
Produces a 6-sheet Excel workbook: Transaction Summary, Sources & Uses, Operating Model, Debt Schedule, Returns Analysis, Debt Covenants.

### Variance Analysis
```
"Analyze Q1 budget vs actual"
```
Produces a 3-sheet Excel report: Variance Summary, Executive Summary, Trend Analysis.

### Pivot Tables
```
"Show sales by region and product category"
```
Creates pivot tables with charts, calculated fields, and conditional formatting.

## Plugin Architecture

```
excel-analyst-pro/
├── plugin.json
├── skills/
│   ├── excel-dcf-modeler/
│   │   ├── SKILL.md
│   │   ├── evals/evals.json
│   │   └── references/REFERENCE.md
│   ├── excel-lbo-modeler/
│   │   ├── SKILL.md
│   │   ├── evals/evals.json
│   │   └── references/REFERENCE.md
│   ├── excel-pivot-wizard/
│   │   ├── SKILL.md
│   │   ├── evals/evals.json
│   │   └── references/REFERENCE.md
│   └── excel-variance-analyzer/
│       ├── SKILL.md
│       ├── evals/evals.json
│       └── references/REFERENCE.md
└── slash-commands/
    ├── build-dcf.md
    ├── build-lbo.md
    └── analyze-variance.md
```

## MCP Server

Uses `@negokaz/excel-mcp-server` for all Excel operations. No Microsoft Excel installation required. All processing is local.

## License

Intent Solutions Proprietary - see [LICENSE](LICENSE) for details.

For commercial licensing: jeremy@intentsolutions.io
