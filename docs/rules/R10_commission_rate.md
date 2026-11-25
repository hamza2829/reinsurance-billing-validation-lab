# R10_commission_rate

Commission matches premium times the contractual commission rate.

Injected defect type: `none`

## Technical

- Inputs: premium, commission, commission_rate; commission_abs, commission_rel.
- Logic: flag when |commission - premium*rate| > max(commission_abs, commission_rel*|premium|).
- Edge cases: unknown treaties skipped; negative premiums with matching negative commission pass.

## Business

- Protects: against over- or under-paying ceding commission.
- Owner: treaty accounting checks the contract terms.
