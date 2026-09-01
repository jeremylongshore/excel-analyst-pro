# Variance analysis

Use this reference for budget-versus-actual, forecast-versus-actual, or comparable
period analysis.

## Required evidence

Confirm the comparison versions, period, currency, units, organizational scope,
line-item mapping, sign convention, materiality policy, and whether the data is
monthly, quarterly, year-to-date, or full-year. Preserve source-row traceability.

Do not infer a root cause from two totals. A driver is confirmed only when the
source data supports a price, volume, mix, timing, headcount, vendor, or other
bridge. Otherwise label it as a hypothesis or an evidence request.

## Suggested workbook

1. **Source Map** — source files, versions, periods, mappings, exclusions, and
   unresolved data-quality issues.
2. **Variance Summary** — comparison, raw variance, normalized favorability,
   materiality, evidence state, and commentary.
3. **Trend Analysis** — include only when multiple comparable periods exist.
4. **Executive Summary** — include only evidence-backed drivers and actions
   supplied or approved by accountable owners.

## Core formulas

Keep arithmetic variance separate from favorable/unfavorable presentation:

```text
Raw_Variance = Actual - Comparison
Variance_Percent = IF(Comparison = 0, NA(), Raw_Variance / ABS(Comparison))
Favorability_Sign = +1 for revenue/profit; -1 for expense/cost
Favorable_Variance = Raw_Variance * Favorability_Sign
```

For zero, negative, or sign-changing comparison values, show the absolute variance
and mark the percentage as not meaningful unless the user's policy specifies a
different treatment.

Materiality must implement the user's stated policy exactly. Record whether
percentage and absolute thresholds combine with `OR` or `AND`. Apply severity to
the unfavorable direction unless the policy explicitly flags large favorable
variances too. Do not color every large absolute variance red.

## Commentary evidence

For each material item, separate:

- **Observation** — verified amount, percentage, period, and direction.
- **Confirmed driver** — supported by a source row or supplied explanation.
- **Hypothesis** — plausible but unverified; phrase as a question or evidence need.
- **Action** — supplied or approved by the responsible owner.

Never invent campaign changes, hiring events, owner names, deadlines, or causal
amounts. Reconcile any component bridge to the total variance before calling it a
driver analysis.

## Required checks

- Budget/forecast and actual scopes, periods, units, and line-item mappings match.
- Raw variance and favorable variance follow the declared sign convention.
- Component bridges sum to the reported total variance.
- Threshold classifications cover boundary values without gaps or overlaps.
- Favorable and unfavorable rankings use normalized favorability.
- Trend claims use at least two comparable periods.
- Executive totals reconcile to the detail sheet.

If the evidence supports only a descriptive comparison, return that comparison and
an evidence request rather than a fabricated root-cause narrative.
