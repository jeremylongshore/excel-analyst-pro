# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
