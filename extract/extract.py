"""DuckDB extraction: merge three sources into one staging schema, with a cleaning log."""
import argparse
import json
from pathlib import Path

import duckdb
import pandas as pd

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
OUT = Path(__file__).parent / "out"
KEY = "upper(trim({c}))"
DATE = "strftime(coalesce(try_strptime(trim({c}), '%Y-%m-%d'), try_strptime(trim({c}), '%d.%m.%Y')), '%Y-%m-%d')"
TEXT_STEPS = (
    [("trim_upper_key", "raw_treaties", c, KEY) for c in ("treaty_id", "cedent_id")]
    + [("normalize_currency", "raw_treaties", "currency", KEY)]
    + [("trim_upper_key", "raw_claims", c, KEY) for c in ("claim_id", "treaty_id")]
    + [("normalize_currency", "raw_claims", "currency", KEY)]
    + [("trim_upper_key", "raw_statements", c, KEY) for c in ("line_id", "statement_id", "treaty_id", "partner_id")]
    + [("normalize_currency", "raw_statements", "currency", KEY)]
    + [("normalize_date", "raw_statements", c, DATE) for c in ("statement_date", "due_date", "received_date")]
)
TYPED = {
    "stg_treaties": """SELECT treaty_id, cedent_id AS partner_id, treaty_type, currency,
        CAST(commission_rate AS DOUBLE) AS commission_rate, CAST(due_days AS INTEGER) AS due_days FROM raw_treaties""",
    "stg_claims": """SELECT claim_id, treaty_id, trim(period) AS period, CAST(amount AS DOUBLE) AS amount,
        currency FROM raw_claims""",
    "stg_statement_lines": """SELECT line_id, statement_id, treaty_id, partner_id, trim(period) AS period, currency,
        CAST(premium AS DOUBLE) AS premium, CAST(claims AS DOUBLE) AS claims,
        CAST(commission AS DOUBLE) AS commission, CAST(balance AS DOUBLE) AS balance,
        CAST(statement_date AS DATE) AS statement_date, CAST(due_date AS DATE) AS due_date,
        CAST(received_date AS DATE) AS received_date FROM raw_statements""",
    "stg_partners": "SELECT DISTINCT partner_id FROM stg_treaties",
    "stg_billing": """SELECT l.*, t.currency AS treaty_currency, t.commission_rate, t.partner_id AS treaty_partner_id,
        t.treaty_id IS NOT NULL AS treaty_found, coalesce(c.total, 0.0) AS claims_system_total
        FROM stg_statement_lines l LEFT JOIN stg_treaties t ON l.treaty_id = t.treaty_id
        LEFT JOIN (SELECT treaty_id, period, sum(amount) AS total FROM stg_claims GROUP BY 1, 2) c
        ON l.treaty_id = c.treaty_id AND l.period = c.period""",
}


def load_raw(con, raw):
    raw = Path(raw)
    claims = pd.DataFrame(json.loads((raw / "claims.json").read_text())["claims"]).astype(str)
    stmts = pd.read_excel(raw / "partner_statements.xlsx", dtype=str)
    treaties = pd.read_csv(raw / "treaties.csv", dtype=str, keep_default_na=False)
    for name, df in (("raw_treaties", treaties), ("raw_claims", claims), ("raw_statements", stmts)):
        con.register(f"{name}_df", df)
        con.execute(f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM {name}_df")
        con.unregister(f"{name}_df")


def clean(con):
    """Apply text cleaning steps and typed casts; return the cleaning log as a list of dicts."""
    log = []
    for step, table, col, tpl in TEXT_STEPS:
        expr = tpl.replace("{c}", col)
        n = con.execute(f"SELECT count(*) FROM {table} WHERE {col} IS DISTINCT FROM {expr}").fetchone()[0]
        con.execute(f"UPDATE {table} SET {col} = {expr}")
        log.append(dict(step=step, table=table, column=col, rows_changed=n))
    for table, sql in TYPED.items():
        con.execute(f"CREATE OR REPLACE TABLE {table} AS {sql}")
        n = con.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
        log.append(dict(step="cast_types" if table != "stg_billing" else "merge_sources",
                        table=table, column="*", rows_changed=n))
    return log


def run(raw=RAW, out=OUT):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(out / "staging.duckdb"))
    load_raw(con, raw)
    log = clean(con)
    con.close()
    pd.DataFrame(log).to_csv(out / "cleaning_log.csv", index=False)
    return log


def load_context(db):
    """Read staging tables into the dict consumed by validation rules."""
    con = duckdb.connect(str(db), read_only=True)
    ctx = {"billing": con.execute("SELECT * FROM stg_billing ORDER BY line_id").df(),
           "partners": set(con.execute("SELECT partner_id FROM stg_partners").df()["partner_id"])}
    con.close()
    return ctx


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--raw", default=str(RAW))
    p.add_argument("--out", default=str(OUT))
    a = p.parse_args(argv)
    log = run(a.raw, a.out)
    print(f"{len(log)} cleaning steps logged")
    return log


if __name__ == "__main__":
    main()
