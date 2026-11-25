# R12_due_after_statement

Due date is not before the statement date.

Injected defect type: `none`

## Technical

- Inputs: statement_date, due_date.
- Logic: flag due_date < statement_date.
- Edge cases: missing dates not flagged here (see R13).

## Business

- Protects: against impossible payment terms that break dunning.
- Owner: data engineering checks date parsing; accounting confirms terms.
