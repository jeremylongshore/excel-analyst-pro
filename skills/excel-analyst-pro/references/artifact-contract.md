# Workbook artifact contract

Use this contract for every workbook created or modified by Excel Analyst Pro.

## Evidence states

Label material values as one of:

- **Supplied** — provided directly by the user or input workbook.
- **Sourced** — taken from a named source with an as-of date.
- **Assumption** — explicitly approved by the user for this scenario.
- **Derived** — calculated from identified inputs and reviewable formulas.
- **Missing** — required evidence not yet available.

Never turn a generic benchmark, model memory, or an example value into a company
fact. Keep source names, dates, units, currencies, and period conventions beside
the relevant assumptions.

## Before writing

1. Resolve input and output paths. Refuse ambiguous paths and ask before overwrite.
2. Create a working copy for an existing workbook unless in-place editing is
   explicit. Do not change the original merely to inspect it.
3. Inventory sheets, used ranges, formulas, named ranges, tables, external links,
   data validation, hidden sheets, merged cells, comments, macros, charts, pivot
   objects, conditional formatting, and workbook protection when the tool exposes
   them.
4. Record which feature families the tool cannot inspect or preserve. An unknown
   feature is a risk, not evidence of absence.
5. For macro-enabled or protected workbooks, require a preservation-capable tool
   or stop and propose a safe alternative.

When local Python execution is available and authorized, create a deterministic
OOXML baseline inventory before mutation. Resolve `EXCEL_SKILL_DIR` to the loaded
`skills/excel-analyst-pro` directory; do not assume the user's current directory:

```bash
EXCEL_SKILL_DIR=/absolute/path/to/skills/excel-analyst-pro
python3 "$EXCEL_SKILL_DIR/scripts/workbook_inventory.py" INPUT.xlsx \
  --output baseline.json
```

The inventory helper accepts `.xlsx` and `.xlsm` OOXML packages. It does not make
an unsupported legacy or binary workbook safe to edit. For CSV evidence, use an
explicit data contract and reconcile every row before modeling:

```bash
python3 "$EXCEL_SKILL_DIR/scripts/profile_reconcile.py" INPUT.csv \
  --spec contract.json --output profile.json
```

Lookup paths in the JSON contract must be relative and remain inside the
contract directory. The profiler fails closed above its documented file, row,
distinct-value, key, or exception budgets instead of retaining attacker-sized
inputs indefinitely; split larger evidence into explicitly reconciled cohorts.

Do not run a packaged helper merely because it exists. Its inputs, output path,
and local process execution must be permitted by the active harness and user.

## Formula and layout rules

- Put editable assumptions in visible, labeled cells; do not hide constants in
  formulas.
- Use consistent units and signs across sheets. State whether debt, expenses, and
  cash outflows are positive or negative inputs.
- Link schedules to the assumptions and source data they use.
- Add model checks next to the relevant schedule and a visible overall status.
- Avoid volatile functions, circular references, external links, and array
  constructs unless the user needs them and the target engine supports them.
- Write formulas with invariant English function names and comma separators unless
  the target tool documents another requirement.

## Recalculation contract

Writing a formula is not proof that its cached result is current.

1. Save the workbook.
2. Recalculate it with Excel, LibreOffice, or another compatible calculation
   engine when available.
3. Reopen the recalculated file and inspect key formula cells and error values.
4. Check for `#REF!`, `#DIV/0!`, `#VALUE!`, `#NAME?`, `#N/A`, and unresolved
   circular references.
5. If no calculation engine is available, report `recalculation: not verified`,
   give formulas rather than cached-value conclusions, and identify the exact
   cells an operator must recalculate and inspect.

## Preservation receipt

When a bound receipt and baseline are available, the packaged verifier provides a
model-neutral, read-only preservation check:

```bash
python3 "$EXCEL_SKILL_DIR/scripts/verify_artifact.py" OUTPUT.xlsx \
  --receipt receipt.json --baseline INPUT.xlsx --output verification.json
```

The verifier validates the internal consistency of supplied evidence; it does not
recalculate the workbook, authenticate who produced the evidence, or manufacture
calculation evidence. A passing report is `EVIDENCE_CONSISTENT`, never an
independent engine attestation. Call a workbook recalculated only when the active
operator actually ran and inspected it in the named engine.

After saving, report:

- input and output paths;
- whether the original was untouched;
- sheets added, changed, or removed;
- feature families verified as preserved;
- feature families changed intentionally;
- feature families not inspectable by the tool;
- recalculation engine and status;
- model-check status and any formula errors.

Do not claim byte-for-byte or feature-complete preservation unless a comparison
actually proved it.
