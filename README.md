# Excel Analyst Pro

Excel Analyst Pro turns supplied financial evidence into reviewable Excel
workbooks for three jobs:

- DCF valuation
- LBO returns analysis
- Budget, forecast, or period variance analysis

It shows its assumptions, links formulas to inputs, checks the saved workbook,
and keeps spreadsheet-engine recalculation status explicit. Its read-only
verifier checks whether supplied evidence is internally consistent; it does not
pretend that a self-hash authenticates Excel or LibreOffice. The workflow does
not invent company data, root causes, or financing terms.

## Understand it in 30 seconds

Ask for the workbook and provide the evidence you have:

```text
Build a five-year DCF from this forecast and debt schedule. Save a new workbook;
do not overwrite the source. Mark every assumption I still need to approve.
```

The skill will:

1. confirm the decision, source files, units, periods, and output path;
2. separate supplied facts, sourced facts, assumptions, formulas, and gaps;
3. build only the requested DCF, LBO, or variance workbook;
4. verify formulas, balances, preservation limits, and recalculation status; and
5. return the file path with a short evidence and verification receipt.

Native pivot tables, charts, slicers, What-If Data Tables, and other unsupported
Excel objects are not promised. The skill can offer a formula-backed summary or
an implementation plan when the active spreadsheet tool lacks a required feature.

## Install

Clone the public repository, then load it directly. This does not require a
marketplace registration:

```bash
git clone https://github.com/jeremylongshore/excel-analyst-pro-skill-md.git
claude --plugin-dir ./excel-analyst-pro-skill-md
```

The plugin includes one model-neutral AgentSkills.io entrypoint at
`skills/excel-analyst-pro/SKILL.md`. Codex and other AgentSkills-compatible
harnesses can install or link that skill directory through their normal skill
installer; the workflow itself does not call a model API.

The Claude plugin does **not** start or download an MCP server automatically. An
opt-in example for `@negokaz/excel-mcp-server@0.12.0` is provided at
`examples/claude-mcp.json`. It is a complete `mcpServers` configuration object;
review it and explicitly merge it into your own Claude configuration only if you
consent to `npx --yes` downloading and executing that pinned package. For
stronger supply-chain control, install the audited package into a locked local
tool directory and replace `npx --yes` with its fixed local executable path.

The adapter's published README requires Node.js 20 or later with npm/npx. Its
`package.json` does not enforce that requirement with an `engines` field, so
deployment must check it explicitly. The adapter can read and write ordinary
sheets, values, formulas, tables, and direct cell styles. It is not a native Excel
automation surface and does not recalculate formulas.

The bundled launch command is the adapter's macOS/Linux `npx` form. Its published
Windows configuration launches `npx` through `cmd /c`; Windows operators must
apply that platform-specific command before enabling the adapter.

The packaged inventory, CSV reconciliation, and artifact-verification helpers use
only the Python standard library and require Python 3.10 or later. The model
workflow remains usable without either optional runtime, but it must stop instead
of claiming an artifact operation it cannot perform.

## Safety and evidence

- Existing workbooks are edited through a copy unless in-place work is explicit.
- Overwrites require confirmation.
- Unsupported macros, links, names, validations, protection, or other workbook
  features block mutation when preservation matters.
- Formula output is not called verified until a compatible engine recalculates
  the saved workbook and key cells are reopened and checked.
- Missing evidence stays missing; static industry defaults are not substituted.
- Variance drivers remain hypotheses unless source data proves them.

## Migration from v1.1

Version 2 is a deliberate consolidation:

| Previous entrypoint                             | Version 2 destination                              |
| ----------------------------------------------- | -------------------------------------------------- |
| `excel-dcf-modeler`                             | `excel-analyst-pro`, DCF mode                      |
| `excel-lbo-modeler`                             | `excel-analyst-pro`, LBO mode                      |
| `excel-variance-analyzer`                       | `excel-analyst-pro`, variance mode                 |
| `excel-pivot-wizard`                            | Suspended; no unsupported native pivot/chart claim |
| `/build-dcf`, `/build-lbo`, `/analyze-variance` | Use natural language or `$excel-analyst-pro`       |

The former files remain recoverable in Git history. Existing prompts continue to
work when they clearly request a DCF, LBO, or variance workbook, but automation
should update explicit skill names to `excel-analyst-pro`.

## Package layout

```text
.claude-plugin/plugin.json
examples/claude-mcp.json
skills/excel-analyst-pro/
├── SKILL.md
├── agents/openai.yaml
├── scripts/
│   ├── profile_reconcile.py
│   ├── verify_artifact.py
│   └── workbook_inventory.py
└── references/
    ├── artifact-contract.md
    ├── dcf.md
    ├── lbo.md
    ├── tooling.md
    └── variance.md
```

Intent Solutions Proprietary. See [LICENSE](LICENSE).
