---
name: excel-analyst-pro
description: |
  Create or revise local Excel workbooks for DCF valuation, LBO returns, or
  budget-versus-actual variance analysis when the user explicitly requests a
  spreadsheet artifact. Use when evidence-backed finance models need reviewable
  formulas and checks. Trigger with explicit requests for a DCF, LBO, or variance
  workbook. Do not use for native pivot tables or charts, live market data, or
  generic financial advice.
allowed-tools: "Read"
argument-hint: "[workbook-or-financial-evidence]"
version: "2.0.0"
author: "Jeremy Longshore <jeremy@intentsolutions.io>"
license: "Proprietary"
compatibility: "Model-neutral AgentSkills.io workflow. Creating or editing .xlsx files requires a local spreadsheet tool that can preserve the workbook features in scope; the opt-in MCP example documents Node.js 20+ with npm/npx, although its package metadata does not enforce an engines range."
tags: [excel, financial-modeling, dcf, lbo, variance-analysis]
model: inherit
effort: high
---

# Excel Analyst Pro

## Overview

Build reviewable finance workbooks without inventing source data, silently
changing workbook features, or claiming calculations that were not recalculated.
Only `Read` is preapproved by this entrypoint; use other tools only when they are
available, needed, and authorized in the active harness.

## Prerequisites

- Supplied financial evidence or an existing workbook appropriate to the request.
- An agreed output path, currency, units, and period convention.
- For artifact creation, an authorized spreadsheet tool that passes the capability
  gate in the tooling reference.

## Instructions

### Route the request

Read only the references needed for the current request:

- Before any workbook write, read [the artifact contract](references/artifact-contract.md).
- For a DCF, read [DCF modeling](references/dcf.md).
- For an LBO, read [LBO modeling](references/lbo.md).
- For budget, forecast, or period variance, read [variance analysis](references/variance.md).
- When selecting or checking spreadsheet tooling, read [tooling boundaries](references/tooling.md).

Native pivot tables, charts, slicers, What-If Data Tables, and other Excel-only
objects are outside the bundled adapter's supported surface. Explain the boundary
and offer a formula-backed summary table or a tool-neutral implementation plan.
Never claim an unsupported artifact was created.

### Shared workflow

1. Confirm the requested mode, input files, output path, reporting currency,
   units, period convention, and decision the workbook must support.
2. Inventory the input workbook before editing. Work on a copy unless the user
   explicitly authorizes in-place modification.
3. Separate supplied facts, sourced facts, user-approved assumptions, formulas,
   and unresolved gaps. Ask for material missing inputs; do not fill them with
   static industry defaults.
4. Build the smallest workbook that answers the request. Put assumptions in
   visible cells, link formulas to them, and include the checks required by the
   relevant reference.
5. Recalculate with a capable spreadsheet engine when available. Otherwise mark
   calculated values as unverified and do not present stale cached values as final.
6. Reopen and inspect the saved artifact. Verify its paths, sheet names, formulas,
   key outputs, errors, balances, and preservation receipt.
7. Return the artifact path, a concise result summary, assumptions and sources,
   verification status, preserved or changed features, and any blocked evidence.

### Stop conditions

Stop before writing when the source file cannot be read safely, the output would
overwrite a file without approval, required financial inputs are missing, or the
available tool cannot preserve an in-scope workbook feature. Stop before a final
valuation or return claim when recalculation or formula verification is unavailable.

## Output

Return the saved workbook path when an artifact was created, followed by the key
result or blocked result, evidence and assumption summary, model-check status,
recalculation status, and preservation receipt. Never imply that an unverified
cached value is final.

## Examples

- “Build a five-year DCF from this forecast and debt schedule; save a new file.”
- “Model this acquisition using the attached term sheet and operating case.”
- “Compare this quarter's actuals with the approved forecast; do not infer causes.”

A request for “a pivot chart by region” is outside this skill's artifact surface;
offer a formula-backed summary or explain what additional tool is required.

## Error Handling

On invalid inputs, unsafe paths, unsupported workbook features, formula errors, or
missing recalculation, stop at the relevant boundary and return the exact problem,
what remains unchanged, and the smallest evidence or capability needed to proceed.

## Resources

These references are deliberately separate so unrelated model logic stays out of
context:

- [Artifact contract](references/artifact-contract.md) for evidence, preservation,
  recalculation, and verification.
- [DCF modeling](references/dcf.md) for DCF inputs, formulas, and checks.
- [LBO modeling](references/lbo.md) for transaction, debt, and return logic.
- [Variance analysis](references/variance.md) for signs, materiality, and commentary.
- [Tooling boundaries](references/tooling.md) for adapter capabilities and handoffs.
