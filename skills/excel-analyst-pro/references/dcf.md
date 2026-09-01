# DCF modeling

Use this reference only for discounted cash flow valuation workbooks.

## Required evidence

Confirm the valuation date, base fiscal period, reporting currency and units,
historical revenue, projection horizon, operating assumptions, tax treatment,
capital expenditure, working capital, discount rate, terminal-value method, net
debt and other equity adjustments. Shares outstanding are required for a per-share
value.

Every company-specific input must be supplied, sourced with an as-of date, or
approved as a scenario assumption. If evidence is incomplete, build an explicitly
labeled scenario model or stop; do not substitute static industry averages.

## Suggested workbook

Use a compact structure appropriate to the request:

1. **Sources & Assumptions** — evidence state, source, as-of date, units, and
   scenario controls.
2. **FCF Projection** — historical anchor plus explicit forecast periods.
3. **Valuation** — discounted cash flows, terminal value, enterprise-to-equity
   bridge, and checks.
4. **Sensitivity** — formula-backed scenarios. Do not promise a native Excel
   What-If Data Table when the active tool cannot create or preserve one.

## Core formulas

For each forecast period `t`:

```text
Revenue_t = Revenue_(t-1) * (1 + Growth_t)
EBITDA_t = Revenue_t * EBITDA_Margin_t
EBIT_t = EBITDA_t - D&A_t
NOPAT_t = EBIT_t * (1 - Cash_Tax_Rate_t)
NWC_t = Revenue_t * NWC_Percent_t
Change_NWC_t = NWC_t - NWC_(t-1)
UFCF_t = NOPAT_t + D&A_t - CapEx_t - Change_NWC_t
PV_UFCF_t = UFCF_t / (1 + WACC)^Period_t
```

Use a fractional `Period_t` only when the user requests a mid-year convention and
the dates support it.

For a perpetuity-growth terminal value:

```text
Terminal_Value = UFCF_final * (1 + g) / (WACC - g)
PV_Terminal_Value = Terminal_Value / (1 + WACC)^Terminal_Period
Enterprise_Value = Sum(PV_UFCF) + PV_Terminal_Value
Equity_Value = Enterprise_Value - Net_Debt - Other_Debt_Like_Items
               + Non_Operating_Assets
Per_Share_Value = Equity_Value / Diluted_Shares
```

Require `WACC > g`. Preserve the sign convention in the enterprise-to-equity
bridge and show every adjustment separately.

If WACC is computed rather than supplied:

```text
Cost_Equity = Risk_Free_Rate + Beta * Equity_Risk_Premium
After_Tax_Cost_Debt = Pre_Tax_Cost_Debt * (1 - Marginal_Tax_Rate)
WACC = E/(D+E) * Cost_Equity + D/(D+E) * After_Tax_Cost_Debt
```

Require sourced inputs and consistent market-value weights. Do not call a typed
discount rate a "WACC calculation."

## Required checks

- `WACC > terminal growth` for every sensitivity cell.
- Revenue roll-forward and NWC change reconcile period to period.
- Enterprise value equals discounted forecast cash flow plus discounted terminal
  value.
- Equity bridge foots and diluted shares are positive before per-share output.
- Sensitivity base case equals the valuation base case.
- Terminal-value contribution is disclosed as a concentration indicator, not an
  automatic pass/fail threshold.

Return value ranges and sensitivities with their assumptions. Do not invent a
reasonableness comparison when no comparable-company evidence was supplied.
