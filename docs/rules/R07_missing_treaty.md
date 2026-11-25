# R07_missing_treaty

Treaty on the statement exists in the treaty system.

Injected defect type: `missing_treaty`

## Technical

- Inputs: treaty_found from the staging join.
- Logic: flag lines where the left join found no treaty.
- Edge cases: these lines are excluded from treaty-based rules R02, R09, R10, R14.

## Business

- Protects: against booking business without a contract.
- Owner: underwriting confirms the treaty or rejects the line.
