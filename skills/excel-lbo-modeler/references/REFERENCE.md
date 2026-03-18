# LBO Modeling Best Practices

## Overview

Leveraged Buyout (LBO) modeling is a core skill for private equity and investment banking professionals. This guide covers debt structuring, returns analysis, and common pitfalls.

## Debt Structure by Industry

### Software / SaaS
- Total Leverage: 5-7x EBITDA
- Senior Debt: 3-4x EBITDA
- Equity Contribution: 35-45%
- Interest Rates: SOFR + 350-500bps
- Typical Hold: 4-6 years

### Healthcare Services
- Total Leverage: 5-6x EBITDA
- Senior Debt: 3-4x EBITDA
- Equity Contribution: 40-50%
- Interest Rates: SOFR + 375-525bps
- Typical Hold: 4-5 years

### Industrials / Manufacturing
- Total Leverage: 4-5x EBITDA
- Senior Debt: 2.5-3.5x EBITDA
- Equity Contribution: 40-50%
- Interest Rates: SOFR + 300-450bps
- Typical Hold: 4-6 years

### Consumer / Retail
- Total Leverage: 4-5.5x EBITDA
- Senior Debt: 2.5-3.5x EBITDA
- Equity Contribution: 40-50%
- Interest Rates: SOFR + 350-500bps
- Typical Hold: 3-5 years

## Sources & Uses Structure

### Uses
```
Purchase Equity Value
+ Net Debt (assumed or refinanced)
= Enterprise Value
+ Transaction Fees (typically 2-3% of EV)
+ Financing Fees (typically 2-3% of debt)
= Total Uses
```

### Sources
```
Revolver (typically undrawn at close)
+ Term Loan A (amortizing, lower spread)
+ Term Loan B (bullet, higher spread)
+ Subordinated / Mezzanine Debt
+ Sponsor Equity (remainder)
= Total Sources
```

Sources must equal Uses.

## Debt Tranches

### Revolver
- Size: 1-2x EBITDA
- Drawn at close: Usually $0
- Purpose: Working capital needs
- Rate: SOFR + 250-350bps
- Maturity: 5 years

### Term Loan A (TLA)
- Size: 2-2.5x EBITDA
- Amortization: 5-7 year schedule (1-2% quarterly)
- Rate: SOFR + 300-400bps
- Maturity: 5-6 years
- Prepayment: No penalty

### Term Loan B (TLB)
- Size: 2-3x EBITDA
- Amortization: Minimal (1% per year)
- Rate: SOFR + 400-550bps
- Maturity: 7 years
- Prepayment: Soft call (typically 1% in year 1)

### Subordinated / Mezzanine
- Size: 1-2x EBITDA
- Amortization: None (bullet)
- Rate: 12-15% (cash + PIK)
- Maturity: 8-10 years

## Returns Analysis

### IRR Calculation
```
IRR = (Exit Equity / Entry Equity)^(1/Years) - 1
```

### Money-on-Money (MoM)
```
MoM = Exit Equity / Entry Equity
```

### PE Return Benchmarks
| MoM | IRR (5yr) | Assessment |
|-----|-----------|------------|
| >3.0x | >25% | Strong |
| 2.5-3.0x | 20-25% | Good |
| 2.0-2.5x | 15-20% | Acceptable |
| <2.0x | <15% | Below hurdle |

### Value Creation Levers
1. **Revenue Growth**: Top-line expansion
2. **Margin Improvement**: Operational efficiency
3. **Multiple Expansion**: Exit at higher multiple than entry
4. **Debt Paydown**: Deleveraging increases equity value
5. **Dividend Recap**: Return capital during hold period

## Covenant Calculations

### Leverage Covenants
- Total Debt / EBITDA <= 6.0x (typical max)
- Senior Debt / EBITDA <= 4.0x
- Must test quarterly

### Coverage Covenants
- EBITDA / Interest >= 2.0x (interest coverage)
- (EBITDA - CapEx) / Debt Service >= 1.2x (fixed charge coverage)

### Covenant Headroom
- Maintain 15-20% headroom above minimums
- Flag any year where headroom < 10%

## Common Mistakes

### 1. Over-Leveraging
- Total leverage >7x rarely achievable in current markets
- Lenders require demonstrated cash flow stability

### 2. Ignoring Working Capital
- Growing companies need incremental working capital
- Model NWC as % of revenue (10-15% typical)

### 3. Optimistic Exit Assumptions
- Exit multiple > entry multiple requires strong justification
- Conservative: exit = entry multiple
- Aggressive: exit = entry + 1-2x

### 4. Inadequate Debt Service
- Ensure cash flow covers mandatory amortization + interest
- Negative free cash flow = revolver draw, not a viable long-term structure

## Sensitivity Tables

### Standard Sensitivity Analyses
1. **Exit Multiple vs Hold Period** -> IRR
2. **Entry Multiple vs Exit Multiple** -> IRR
3. **Revenue Growth vs EBITDA Margin** -> Exit Equity
4. **Leverage vs Equity Check** -> IRR

### Formatting
- Highlight base case
- Green for above-hurdle IRR (>20%)
- Red for below-hurdle IRR (<15%)
- Show both IRR and MoM where possible
