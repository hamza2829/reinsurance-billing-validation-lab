# R14_partner_matches_treaty

Partner on the line is the cedent of the referenced treaty.

Injected defect type: `none`

## Technical

- Inputs: partner_id, treaty_partner_id, partner master.
- Logic: flag known partners that differ from the treaty's cedent.
- Edge cases: unknown partners (R06) and unknown treaties (R07) are skipped.

## Business

- Protects: against allocating business to the wrong counterparty.
- Owner: treaty accounting.
