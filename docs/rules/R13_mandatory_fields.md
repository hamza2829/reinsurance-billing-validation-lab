# R13_mandatory_fields

All mandatory fields are filled.

Injected defect type: `none`

## Technical

- Inputs: mandatory_fields list from config.
- Logic: flag lines with any null or empty mandatory field.
- Edge cases: unparseable dates become null during extraction and are caught here.

## Business

- Protects: completeness of the billing record for audit.
- Owner: data engineering if caused by parsing, otherwise the cedent.
