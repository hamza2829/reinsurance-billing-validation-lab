# R03_currency_code_valid

Currency code is in the allowed list.

Injected defect type: `none`

## Technical

- Inputs: currency; allowed_currencies from config.
- Logic: flag codes not in the allowed list after cleaning.
- Edge cases: null currency is flagged here and in R13.

## Business

- Protects: downstream ledgers from unknown currency codes.
- Owner: data engineering fixes mapping; accounting confirms the code.
