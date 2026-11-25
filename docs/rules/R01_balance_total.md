# R01_balance_total

Statement balance equals premium minus claims minus commission.

Injected defect type: `wrong_total`

## Technical

- Inputs: premium, claims, commission, balance per statement line; tolerances.total_abs.
- Logic: flag when |premium - claims - commission - balance| > total_abs.
- Edge cases: null amounts are not flagged here (see R13); tolerance absorbs cent rounding.

## Business

- Protects: correct settlement amounts paid or received for each treaty.
- Owner: technical accounting team corrects the line with the partner.
