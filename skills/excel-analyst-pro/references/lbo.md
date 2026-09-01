# LBO modeling

Use this reference only for leveraged buyout return models.

## Required evidence

Confirm the transaction date, target financials, entry valuation, purchase-price
bridge, fees, minimum cash, debt tranches, rates and floors, amortization, cash
sweep, tax assumptions, operating forecast, exit assumptions, hold period, and
required return outputs.

Debt capacity, interest spreads, leverage, fees, exit multiples, and hurdle rates
must come from the user or a dated source. If the user wants a hypothetical case,
record and obtain approval for each scenario assumption. Do not silently apply a
static private-equity or industry default.

## Suggested workbook

1. **Sources & Assumptions** — transaction evidence, scenario controls, and signs.
2. **Sources & Uses** — purchase price, refinanced obligations, fees, financing,
   minimum cash, debt funding, and sponsor equity.
3. **Operating Model** — revenue, EBITDA, taxes, CapEx, working capital, and cash
   flow available for debt service.
4. **Debt Schedule** — one roll-forward per tranche, revolver liquidity, interest,
   mandatory amortization, optional sweep, and ending balances.
5. **Returns** — exit bridge, sponsor cash flows, MoM, IRR, and formula-backed
   sensitivities.
6. **Checks** — sources and uses, cash balance, debt roll-forwards, and covenant
   calculations required by the supplied documents.

Do not create a covenant schedule from generic ratios and label it contractual.
Use actual covenant definitions or title the output as a scenario check.

## Core formulas

```text
Entry_Enterprise_Value = Entry_Metric * Entry_Multiple
Total_Uses = Purchase_Equity_Value + Refinance_Debt + Fees
             + Required_Cash_Funding + Other_Uses
Sponsor_Equity = Total_Uses - Funded_Debt - Other_Sources
Sources_Uses_Check = Total_Sources - Total_Uses
```

An undrawn revolver is liquidity capacity, not a funded closing source.

For each tranche and period:

```text
Ending_Debt = Beginning_Debt + Draws + PIK_Interest
              - Mandatory_Amortization - Optional_Repayment
Cash_Interest = Applicable_Rate * Interest_Balance
```

Use average beginning/ending debt for `Interest_Balance` when appropriate. If the
cash sweep and interest create circularity, use a documented iterative calculation
supported by the engine or a conservative non-circular convention; disclose which
one was used. Respect minimum cash and revolver draw/repayment priority before
optional term-debt sweeps.

```text
Exit_Enterprise_Value = Exit_Metric * Exit_Multiple
Exit_Equity_Value = Exit_Enterprise_Value - Exit_Net_Debt
MoM = Total_Sponsor_Proceeds / Total_Sponsor_Invested_Capital
IRR = XIRR(Dated_Sponsor_Cash_Flows)
```

Use `XIRR` for dated interim cash flows. The shortcut
`MoM^(1/Hold_Years)-1` is valid only for one initial outflow and one terminal inflow
with the stated period convention.

## Required checks

- Sources equal uses and sponsor equity is non-negative.
- Cash never falls below minimum cash after modeled revolver availability.
- Every debt roll-forward and total debt reconcile.
- Interest uses the disclosed balance convention and rate components.
- Exit equity bridge reconciles to enterprise value and net debt.
- MoM and IRR use the same sponsor cash-flow denominator and timing.
- Sensitivity base case equals the returns base case.
- Covenant outputs state whether they are contractual or illustrative.

Do not assert that financing is achievable or a return meets market practice
without dated financing or mandate evidence.
