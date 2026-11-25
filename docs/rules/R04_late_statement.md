# R04_late_statement

Statement was received on or before its due date.

Injected defect type: `late_statement`

## Technical

- Inputs: received_date, due_date; deadlines.grace_days.
- Logic: flag when received_date > due_date + grace_days.
- Edge cases: missing dates are not flagged here (see R13).

## Business

- Protects: contractual reporting deadlines and timely cash settlement.
- Owner: partner relationship manager follows up with the cedent.
