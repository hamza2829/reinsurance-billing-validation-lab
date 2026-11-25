from rules import validators as v
from tests.helpers import ctx

CFG = v.load_config()


def ids(fn, c):
    return [f["line_id"] for f in fn(c, CFG)]


def test_at_least_12_rules():
    assert len(v.RULES) >= 12


def test_clean_line_passes_all():
    assert v.run_all(ctx({}), CFG) == []


def test_run_all_default_config():
    assert v.run_all(ctx({})) == []


def test_balance_total():
    assert ids(v.balance_total, ctx({}, {"balance": 650.0})) == ["L1"]


def test_balance_within_tolerance():
    assert ids(v.balance_total, ctx({"balance": 700.005})) == []


def test_currency_mismatch():
    assert ids(v.currency_matches_treaty, ctx({"currency": "USD"})) == ["L0"]


def test_currency_mismatch_skips_missing_treaty():
    assert ids(v.currency_matches_treaty, ctx({"currency": "USD", "treaty_found": False})) == []


def test_currency_code_invalid():
    assert ids(v.currency_code_valid, ctx({"currency": "XXX"})) == ["L0"]


def test_late_statement():
    import pandas as pd
    assert ids(v.late_statement, ctx({"received_date": pd.Timestamp("2025-03-08")})) == ["L0"]


def test_on_due_date_not_late():
    import pandas as pd
    assert ids(v.late_statement, ctx({"received_date": pd.Timestamp("2025-03-07")})) == []


def test_duplicate_flags_second_only():
    assert ids(v.duplicate_line, ctx({"period": "2025-01"}, {"period": "2025-01"})) == ["L1"]


def test_missing_partner():
    assert ids(v.missing_partner, ctx({"partner_id": "P999"})) == ["L0"]


def test_missing_treaty():
    assert ids(v.missing_treaty, ctx({"treaty_found": False})) == ["L0"]


def test_negative_premium():
    assert ids(v.negative_premium, ctx({"premium": -1.0})) == ["L0"]


def test_zero_premium_ok():
    assert ids(v.negative_premium, ctx({"premium": 0.0})) == []


def test_claims_reconciliation():
    assert ids(v.claims_reconciliation, ctx({"claims_system_total": 50.0})) == ["L0"]


def test_reconciliation_tolerance():
    assert ids(v.claims_reconciliation, ctx({"claims_system_total": 99.5})) == []


def test_commission_rate():
    assert ids(v.commission_rate, ctx({"commission": 300.0, "balance": 600.0})) == ["L0"]


def test_commission_negative_premium_ok():
    assert ids(v.commission_rate, ctx({"premium": -1000.0, "commission": -200.0})) == []


def test_negative_claims():
    assert ids(v.negative_claims, ctx({"claims": -5.0})) == ["L0"]


def test_due_before_statement():
    import pandas as pd
    assert ids(v.due_after_statement, ctx({"due_date": pd.Timestamp("2025-01-01")})) == ["L0"]


def test_mandatory_fields_null():
    assert ids(v.mandatory_fields, ctx({"currency": None})) == ["L0"]


def test_mandatory_fields_empty_string():
    assert ids(v.mandatory_fields, ctx({"partner_id": ""})) == ["L0"]


def test_partner_matches_treaty():
    assert ids(v.partner_matches_treaty, ctx({"partner_id": "P002"})) == ["L0"]


def test_finding_shape():
    f = v.balance_total(ctx({"balance": 1.0}), CFG)[0]
    assert set(f) == {"rule_id", "line_id", "treaty_id", "partner_id", "message"}


def test_grace_days_config():
    import pandas as pd
    cfg = {**CFG, "deadlines": {"grace_days": 5}}
    assert v.late_statement(ctx({"received_date": pd.Timestamp("2025-03-10")}), cfg) == []
