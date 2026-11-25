import duckdb

from extract import extract as e
from tests.helpers import pipeline


def _con():
    root, _ = pipeline()
    return duckdb.connect(str(root / "stg" / "staging.duckdb"), read_only=True)


def test_cleaning_log_written():
    root, log = pipeline()
    assert (root / "stg" / "cleaning_log.csv").exists() and len(log) == len(e.TEXT_STEPS) + len(e.TYPED)


def test_log_records_changes():
    _, log = pipeline()
    assert any(x["step"] == "normalize_date" and x["rows_changed"] > 0 for x in log)


def test_keys_trimmed_upper():
    con = _con()
    assert con.execute("SELECT count(*) FROM stg_treaties WHERE treaty_id <> upper(trim(treaty_id))").fetchone()[0] == 0


def test_currencies_normalized():
    con = _con()
    codes = {r[0] for r in con.execute("SELECT DISTINCT currency FROM stg_statement_lines").fetchall()}
    assert codes <= {"EUR", "USD", "GBP", "CHF"}


def test_dates_parsed():
    con = _con()
    assert con.execute("SELECT count(*) FROM stg_statement_lines WHERE due_date IS NULL").fetchone()[0] == 0


def test_billing_has_all_lines():
    con = _con()
    a = con.execute("SELECT count(*) FROM stg_billing").fetchone()[0]
    b = con.execute("SELECT count(*) FROM stg_statement_lines").fetchone()[0]
    assert a == b == 245


def test_claims_amount_numeric():
    con = _con()
    assert con.execute("SELECT typeof(amount) FROM stg_claims LIMIT 1").fetchone()[0] == "DOUBLE"


def test_load_context():
    root, _ = pipeline()
    c = e.load_context(root / "stg" / "staging.duckdb")
    assert "P002" in c["partners"] and "treaty_found" in c["billing"]


def test_main(tmp_path):
    root, _ = pipeline()
    log = e.main(["--raw", str(root / "raw"), "--out", str(tmp_path)])
    assert (tmp_path / "staging.duckdb").exists() and log
