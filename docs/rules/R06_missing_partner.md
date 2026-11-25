# R06_missing_partner

Partner on the statement exists in the partner master.

Injected defect type: `missing_partner`

## Technical

- Inputs: partner_id; partner set derived from the treaty system.
- Logic: flag partner_ids not in the master set.
- Edge cases: null partner_id is flagged.

## Business

- Protects: against settling with unknown counterparties.
- Owner: master data team creates or corrects the partner.
