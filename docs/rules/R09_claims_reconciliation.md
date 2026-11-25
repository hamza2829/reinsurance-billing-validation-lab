# R09_claims_reconciliation

Statement claims equal the claims system total for treaty and period.

Injected defect type: `source_inconsistency`

## Technical

- Inputs: claims, claims_system_total; tolerances.reconciliation_abs.
- Logic: flag when |claims - claims_system_total| > reconciliation_abs for known treaties.
- Edge cases: no claims in the claims system means total 0; unknown treaties skipped.

## Business

- Protects: consistency between partner statements and our own claims records.
- Owner: claims team reconciles with the cedent's bordereau.
