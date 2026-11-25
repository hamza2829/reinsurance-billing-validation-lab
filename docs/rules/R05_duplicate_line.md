# R05_duplicate_line

No statement line is reported twice.

Injected defect type: `duplicate_line`

## Technical

- Inputs: duplicates.keys (statement, treaty, partner, period).
- Logic: flag every occurrence after the first for the same key.
- Edge cases: the first occurrence is treated as valid; differing line_ids still count.

## Business

- Protects: against paying or booking the same premium twice.
- Owner: technical accounting removes the duplicate booking.
