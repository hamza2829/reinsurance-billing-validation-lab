# R11_negative_claims

Claims amount is not negative.

Injected defect type: `none`

## Technical

- Inputs: claims.
- Logic: flag claims < 0.
- Edge cases: recoveries must be reported separately, not as negative claims.

## Business

- Protects: against sign errors that inflate the balance due.
- Owner: claims team.
