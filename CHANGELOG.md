# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- Wrap the opt-in Excel adapter example in a valid top-level `mcpServers`
  object so operators can merge it directly into Claude configuration.

### Changed

- Declare inherited-model, high-effort execution metadata for the consolidated
  finance-workbook skill.

## [2.0.0] - 2026-08-31

### Added

- One model-neutral `excel-analyst-pro` AgentSkills.io entrypoint
- Evidence, recalculation, workbook-feature preservation, and tool-capability contracts
- Current Claude plugin manifest and Codex UI metadata
- Explicitly opt-in, pinned `@negokaz/excel-mcp-server@0.12.0` example

### Changed

- Consolidated DCF, LBO, and variance guidance into conditionally loaded references
- Replaced static industry defaults with supplied, sourced, or user-approved assumptions
- Required evidence-backed variance drivers and explicit verification receipts
- Aligned the optional adapter runtime boundary to its published Node.js 20+
  requirement and documented that package metadata does not enforce it

### Removed

- Unsupported native pivot, chart, slicer, conditional-formatting, freeze-pane,
  What-If Data Table, and recalculation claims
- Duplicated v1 skill entrypoints and slash-command workflows
- Causal invention and unsupported example outputs

## [1.1.0] - 2026-03-18

### Added

- Evaluation scenarios (`evals/evals.json`) for all 4 skills with 3 test cases each
- Reference documentation for LBO, Pivot, and Variance skills (`references/REFERENCE.md`)
- Table of Contents navigation in all SKILL.md files
- Missing sections: Overview, Prerequisites, Output in all SKILL.md files
- Tags and compatible-with fields for marketplace discovery

### Changed

- Un-nest author/version/license from metadata to top-level frontmatter (spec compliance)
- Upgrade descriptions with "Use when" and "Trigger with" patterns for discoverability
- Fix resource paths from `{baseDir}/` to `${CLAUDE_SKILL_DIR}/`
- Update author to Intent Solutions, license to Proprietary
- Rewrite CLAUDE.md with repo identity, architecture, and conventions
- Fix plugin.json repository URL to standalone repo
- Clean README.md to match actual directory structure
- Update LICENSE from MIT to Intent Solutions Proprietary

### Removed

- Internal planning docs: DEMO_VIDEO_SCRIPT.md, GITHUB_DEPLOYMENT.md, PRODUCTION_SUMMARY.md

### Fixed

- All 4 skills now pass AgentSkills.io enterprise validation (A grade: 90-97/100)

## [1.0.0] - 2025-10-27

### Added

- Initial release with 4 financial modeling skills
- excel-dcf-modeler: DCF valuation models with sensitivity analysis
- excel-lbo-modeler: LBO models with debt schedules and IRR calculations
- excel-variance-analyzer: Budget vs actual variance analysis
- excel-pivot-wizard: Natural language pivot table generation
- MCP integration with @negokaz/excel-mcp-server
- Slash commands: /build-dcf, /build-lbo, /analyze-variance
