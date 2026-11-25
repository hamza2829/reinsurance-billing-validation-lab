# R02_currency_matches_treaty

Statement currency equals the treaty currency.

Injected defect type: `currency_mismatch`

## Technical

- Inputs: currency, treaty_currency, treaty_found.
- Logic: flag when the treaty exists and the currencies differ.
- Edge cases: lines without a treaty are skipped (reported by R07).

## Business

- Protects: against booking amounts in the wrong currency and FX errors.
- Owner: treaty accounting asks the cedent for a corrected statement.
