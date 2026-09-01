# Spreadsheet tooling boundaries

Choose tooling from the active harness based on the workbook features that must be
created or preserved. Inspect actual tool capabilities; do not infer support from a
tool or package name.

## Opt-in adapter example

The Claude plugin does not launch an MCP server automatically. The reviewed
`examples/claude-mcp.json` file pins `@negokaz/excel-mcp-server@0.12.0` and, if an
operator explicitly installs that configuration, launches it through `npx --yes`.
That command can download and execute registry code. Review the package and give
explicit consent, or replace it with a locked, integrity-verified local install.
Its published README requires Node.js 20 or later. Its `package.json` declares no
`engines` range, so deployment must check that requirement explicitly instead of
relying on package-manager enforcement. The published adapter surface supports:

- listing and reading sheets;
- writing values and formulas;
- creating ordinary sheets and tables;
- copying sheets; and
- applying direct cell styles.

It does not expose native pivot tables, charts, slicers, conditional-formatting
rules, freeze panes, What-If Data Tables, macro editing, or a workbook calculation
engine. Do not promise those features. A static summary grid or direct cell style
is not a native pivot, chart, conditional rule, or recalculation.

The adapter runs locally over stdio and receives absolute local file paths. It does
not require an API credential. The example command is the published macOS/Linux
form. On Windows, use the
package's documented `cmd` launch with `/c`, `npx`, `--yes`, and the same pinned
package coordinate before enabling the adapter.

## Capability gate

Before writing, determine whether the selected tool can:

1. read the source format and feature families;
2. write formulas and styles needed by the selected model;
3. preserve macros, links, names, validations, protection, and other in-scope
   features;
4. save to the intended output format; and
5. recalculate or hand off to a compatible calculation engine.

If any required capability is unavailable, stop before mutation and offer one of:

- a formula and layout specification;
- a new workbook that does not claim to preserve the original;
- a reduced static summary explicitly labeled as such; or
- a handoff to Excel, LibreOffice, or another approved preservation-capable tool.

Do not convert macro-enabled workbooks to `.xlsx`, strip unsupported features, or
overwrite the source as a workaround.
