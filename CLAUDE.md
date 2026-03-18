# CLAUDE.md — Excel Analyst Pro

## What This Repo Is

Professional financial modeling toolkit for Claude Code. Provides 4 auto-invoked Skills
that build investment banking-grade Excel models (DCF, LBO, variance analysis, pivot tables)
using natural language through the `@negokaz/excel-mcp-server` MCP integration.

**Repository**: https://github.com/jeremylongshore/excel-analyst-pro
**License**: Intent Solutions Proprietary

## Architecture

```
excel-analyst-pro/
├── plugin.json                              # Plugin manifest
├── skills/
│   ├── excel-dcf-modeler/
│   │   ├── SKILL.md                         # DCF valuation skill
│   │   ├── evals/evals.json                 # Evaluation scenarios
│   │   └── references/REFERENCE.md          # DCF best practices
│   ├── excel-lbo-modeler/
│   │   ├── SKILL.md                         # LBO modeling skill
│   │   ├── evals/evals.json
│   │   └── references/REFERENCE.md          # LBO best practices
│   ├── excel-pivot-wizard/
│   │   ├── SKILL.md                         # Pivot table skill
│   │   ├── evals/evals.json
│   │   └── references/REFERENCE.md          # Pivot best practices
│   └── excel-variance-analyzer/
│       ├── SKILL.md                         # Variance analysis skill
│       ├── evals/evals.json
│       └── references/REFERENCE.md          # Variance best practices
└── slash-commands/
    ├── build-dcf.md                         # /build-dcf shortcut
    ├── build-lbo.md                         # /build-lbo shortcut
    └── analyze-variance.md                  # /analyze-variance shortcut
```

## Conventions

- Skills follow the AgentSkills.io spec with Intent Solutions enterprise grading
- SKILL.md frontmatter: `author`, `version`, `license` at top level (not nested in `metadata:`)
- Resource paths use `${CLAUDE_SKILL_DIR}/references/...`
- Each skill has `evals/evals.json` with 3 test scenarios
- All skills use scoped Bash: `Bash(npx:*)`

## Validation

Run the enterprise grader on any SKILL.md:
```bash
python3 /home/jeremy/.claude/skills/skill-creator/scripts/validate-skill.py --grade skills/<name>/SKILL.md
```

## MCP Server

All skills depend on `@negokaz/excel-mcp-server`:
```bash
npx --yes @negokaz/excel-mcp-server
```
Configured in `plugin.json` with `EXCEL_MCP_PAGING_CELLS_LIMIT=4000`.

## Task Tracking (Beads / bd)

Use `bd` for all tasks. Start: `bd ready`. Finish: `bd close <id> --reason "evidence"`. Sync: `bd sync`.
