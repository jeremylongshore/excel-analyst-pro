# CLAUDE.md — Excel Analyst Pro

## Repository purpose

Excel Analyst Pro v2 provides one model-neutral AgentSkills.io entrypoint for
evidence-backed DCF, LBO, and variance workbooks. Native pivot/chart automation is
suspended until the packaged spreadsheet tooling can create and verify it.

Repository: https://github.com/jeremylongshore/excel-analyst-pro-skill-md

License: Intent Solutions Proprietary

## Architecture

```text
.claude-plugin/plugin.json                  # Claude plugin manifest
examples/claude-mcp.json                    # opt-in pinned local Excel adapter
skills/excel-analyst-pro/
├── SKILL.md                                # single discovery and routing surface
├── agents/openai.yaml                      # Codex UI metadata
├── scripts/                                # model-neutral evidence helpers
└── references/
    ├── artifact-contract.md                # shared evidence/preservation contract
    ├── dcf.md                              # DCF formulas and checks
    ├── lbo.md                              # LBO formulas and checks
    ├── tooling.md                          # capability and runtime boundaries
    └── variance.md                         # variance rules and evidence language
```

## Content rules

- Keep discovery in the single `excel-analyst-pro` skill.
- Put mode-specific logic in its matching reference and load it conditionally.
- Do not introduce static industry defaults or unattributed market assumptions.
- Separate observations, confirmed drivers, hypotheses, assumptions, and missing
  evidence.
- Do not claim native pivots, charts, conditional-formatting rules, freeze panes,
  What-If Data Tables, or recalculation through the bundled MCP adapter.
- Preserve the workbook artifact contract and explicit stop conditions.

## Runtime

The skill is model-neutral. The Claude plugin does not auto-start an MCP server.
Its reviewed opt-in example can start `@negokaz/excel-mcp-server@0.12.0` through
`npx`; this downloads and executes registry code and therefore requires explicit
operator consent. Its published README requires Node.js 20 or later, while its
`package.json` does not enforce an `engines` range; deployment must check the
documented requirement explicitly. The packaged
inventory, CSV reconciliation, and verification helpers require Python 3.10 or
later and only the standard library. Supported and unsupported surfaces are
documented in
`skills/excel-analyst-pro/references/tooling.md`.

## Validation

Validate the skill with the repository marketplace validator and validate
`.claude-plugin/plugin.json` plus the opt-in MCP example before release. Tests and scripts are
owned by their designated implementation lane; do not overwrite them during
content-only changes.

## Task tracking

Use `bd` for repository task tracking unless the active task explicitly prohibits
Beads operations.
