# R08_negative_premium

Premium is not negative.

Injected defect type: `negative_premium`

## Technical

- Inputs: premium.
- Logic: flag premium < 0.
- Edge cases: zero premium is allowed; real refunds must be booked as separate adjustment lines.

## Business

- Protects: against sign errors that reverse cash flows.
- Owner: technical accounting checks with the cedent.
