# Validation rules

| Rule | Summary |
|---|---|
| [R01_balance_total](R01_balance_total.md) | Statement balance equals premium minus claims minus commission. |
| [R02_currency_matches_treaty](R02_currency_matches_treaty.md) | Statement currency equals the treaty currency. |
| [R03_currency_code_valid](R03_currency_code_valid.md) | Currency code is in the allowed list. |
| [R04_late_statement](R04_late_statement.md) | Statement was received on or before its due date. |
| [R05_duplicate_line](R05_duplicate_line.md) | No statement line is reported twice. |
| [R06_missing_partner](R06_missing_partner.md) | Partner on the statement exists in the partner master. |
| [R07_missing_treaty](R07_missing_treaty.md) | Treaty on the statement exists in the treaty system. |
| [R08_negative_premium](R08_negative_premium.md) | Premium is not negative. |
| [R09_claims_reconciliation](R09_claims_reconciliation.md) | Statement claims equal the claims system total for treaty and period. |
| [R10_commission_rate](R10_commission_rate.md) | Commission matches premium times the contractual commission rate. |
| [R11_negative_claims](R11_negative_claims.md) | Claims amount is not negative. |
| [R12_due_after_statement](R12_due_after_statement.md) | Due date is not before the statement date. |
| [R13_mandatory_fields](R13_mandatory_fields.md) | All mandatory fields are filled. |
| [R14_partner_matches_treaty](R14_partner_matches_treaty.md) | Partner on the line is the cedent of the referenced treaty. |
