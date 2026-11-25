"""Validation rules. Each rule: (ctx, cfg) -> list of findings. Docstrings feed docs/rules/."""
from pathlib import Path

import pandas as pd
import yaml

CONFIG = Path(__file__).parent / "config.yaml"
RULES = []


def load_config(path=CONFIG):
    return yaml.safe_load(Path(path).read_text())


def rule(rule_id, defect_type=None):
    def deco(fn):
        fn.rule_id, fn.defect_type = rule_id, defect_type
        RULES.append(fn)
        return fn
    return deco


def _hits(df, mask, rule_id, msg):
    return [{"rule_id": rule_id, "line_id": r.line_id, "treaty_id": r.treaty_id,
             "partner_id": r.partner_id, "message": msg(r)} for r in df[mask].itertuples()]


@rule("R01_balance_total", "wrong_total")
def balance_total(ctx, cfg):
    """Statement balance equals premium minus claims minus commission.

    Technical:
        Inputs: premium, claims, commission, balance per statement line; tolerances.total_abs.
        Logic: flag when |premium - claims - commission - balance| > total_abs.
        Edge cases: null amounts are not flagged here (see R13); tolerance absorbs cent rounding.

    Business:
        Protects: correct settlement amounts paid or received for each treaty.
        Owner: technical accounting team corrects the line with the partner.
    """
    df = ctx["billing"]
    diff = (df.premium - df.claims - df.commission - df.balance).abs()
    return _hits(df, diff > cfg["tolerances"]["total_abs"], "R01_balance_total",
                 lambda r: f"balance {r.balance} != computed {round(r.premium - r.claims - r.commission, 2)}")


@rule("R02_currency_matches_treaty", "currency_mismatch")
def currency_matches_treaty(ctx, cfg):
    """Statement currency equals the treaty currency.

    Technical:
        Inputs: currency, treaty_currency, treaty_found.
        Logic: flag when the treaty exists and the currencies differ.
        Edge cases: lines without a treaty are skipped (reported by R07).

    Business:
        Protects: against booking amounts in the wrong currency and FX errors.
        Owner: treaty accounting asks the cedent for a corrected statement.
    """
    df = ctx["billing"]
    mask = df.treaty_found & (df.currency != df.treaty_currency)
    return _hits(df, mask, "R02_currency_matches_treaty",
                 lambda r: f"currency {r.currency} != treaty {r.treaty_currency}")


@rule("R03_currency_code_valid")
def currency_code_valid(ctx, cfg):
    """Currency code is in the allowed list.

    Technical:
        Inputs: currency; allowed_currencies from config.
        Logic: flag codes not in the allowed list after cleaning.
        Edge cases: null currency is flagged here and in R13.

    Business:
        Protects: downstream ledgers from unknown currency codes.
        Owner: data engineering fixes mapping; accounting confirms the code.
    """
    df = ctx["billing"]
    return _hits(df, ~df.currency.isin(cfg["allowed_currencies"]), "R03_currency_code_valid",
                 lambda r: f"invalid currency {r.currency}")


@rule("R04_late_statement", "late_statement")
def late_statement(ctx, cfg):
    """Statement was received on or before its due date.

    Technical:
        Inputs: received_date, due_date; deadlines.grace_days.
        Logic: flag when received_date > due_date + grace_days.
        Edge cases: missing dates are not flagged here (see R13).

    Business:
        Protects: contractual reporting deadlines and timely cash settlement.
        Owner: partner relationship manager follows up with the cedent.
    """
    df = ctx["billing"]
    limit = df.due_date + pd.Timedelta(days=cfg["deadlines"]["grace_days"])
    return _hits(df, df.received_date > limit, "R04_late_statement",
                 lambda r: f"received {r.received_date.date()} after due {r.due_date.date()}")


@rule("R05_duplicate_line", "duplicate_line")
def duplicate_line(ctx, cfg):
    """No statement line is reported twice.

    Technical:
        Inputs: duplicates.keys (statement, treaty, partner, period).
        Logic: flag every occurrence after the first for the same key.
        Edge cases: the first occurrence is treated as valid; differing line_ids still count.

    Business:
        Protects: against paying or booking the same premium twice.
        Owner: technical accounting removes the duplicate booking.
    """
    df = ctx["billing"]
    mask = df.duplicated(subset=cfg["duplicates"]["keys"], keep="first")
    return _hits(df, mask, "R05_duplicate_line", lambda r: "duplicate of earlier line")


@rule("R06_missing_partner", "missing_partner")
def missing_partner(ctx, cfg):
    """Partner on the statement exists in the partner master.

    Technical:
        Inputs: partner_id; partner set derived from the treaty system.
        Logic: flag partner_ids not in the master set.
        Edge cases: null partner_id is flagged.

    Business:
        Protects: against settling with unknown counterparties.
        Owner: master data team creates or corrects the partner.
    """
    df = ctx["billing"]
    return _hits(df, ~df.partner_id.isin(ctx["partners"]), "R06_missing_partner",
                 lambda r: f"unknown partner {r.partner_id}")


@rule("R07_missing_treaty", "missing_treaty")
def missing_treaty(ctx, cfg):
    """Treaty on the statement exists in the treaty system.

    Technical:
        Inputs: treaty_found from the staging join.
        Logic: flag lines where the left join found no treaty.
        Edge cases: these lines are excluded from treaty-based rules R02, R09, R10, R14.

    Business:
        Protects: against booking business without a contract.
        Owner: underwriting confirms the treaty or rejects the line.
    """
    df = ctx["billing"]
    return _hits(df, ~df.treaty_found.astype(bool), "R07_missing_treaty",
                 lambda r: f"unknown treaty {r.treaty_id}")


@rule("R08_negative_premium", "negative_premium")
def negative_premium(ctx, cfg):
    """Premium is not negative.

    Technical:
        Inputs: premium.
        Logic: flag premium < 0.
        Edge cases: zero premium is allowed; real refunds must be booked as separate adjustment lines.

    Business:
        Protects: against sign errors that reverse cash flows.
        Owner: technical accounting checks with the cedent.
    """
    df = ctx["billing"]
    return _hits(df, df.premium < 0, "R08_negative_premium", lambda r: f"premium {r.premium}")


@rule("R09_claims_reconciliation", "source_inconsistency")
def claims_reconciliation(ctx, cfg):
    """Statement claims equal the claims system total for treaty and period.

    Technical:
        Inputs: claims, claims_system_total; tolerances.reconciliation_abs.
        Logic: flag when |claims - claims_system_total| > reconciliation_abs for known treaties.
        Edge cases: no claims in the claims system means total 0; unknown treaties skipped.

    Business:
        Protects: consistency between partner statements and our own claims records.
        Owner: claims team reconciles with the cedent's bordereau.
    """
    df = ctx["billing"]
    diff = (df.claims - df.claims_system_total).abs()
    mask = df.treaty_found & (diff > cfg["tolerances"]["reconciliation_abs"])
    return _hits(df, mask, "R09_claims_reconciliation",
                 lambda r: f"statement claims {r.claims} vs system {round(r.claims_system_total, 2)}")


@rule("R10_commission_rate")
def commission_rate(ctx, cfg):
    """Commission matches premium times the contractual commission rate.

    Technical:
        Inputs: premium, commission, commission_rate; commission_abs, commission_rel.
        Logic: flag when |commission - premium*rate| > max(commission_abs, commission_rel*|premium|).
        Edge cases: unknown treaties skipped; negative premiums with matching negative commission pass.

    Business:
        Protects: against over- or under-paying ceding commission.
        Owner: treaty accounting checks the contract terms.
    """
    df = ctx["billing"]
    t = cfg["tolerances"]
    tol = (df.premium.abs() * t["commission_rel"]).clip(lower=t["commission_abs"])
    mask = df.treaty_found & ((df.commission - df.premium * df.commission_rate).abs() > tol)
    return _hits(df, mask, "R10_commission_rate", lambda r: f"commission {r.commission} off contract rate")


@rule("R11_negative_claims")
def negative_claims(ctx, cfg):
    """Claims amount is not negative.

    Technical:
        Inputs: claims.
        Logic: flag claims < 0.
        Edge cases: recoveries must be reported separately, not as negative claims.

    Business:
        Protects: against sign errors that inflate the balance due.
        Owner: claims team.
    """
    df = ctx["billing"]
    return _hits(df, df.claims < 0, "R11_negative_claims", lambda r: f"claims {r.claims}")


@rule("R12_due_after_statement")
def due_after_statement(ctx, cfg):
    """Due date is not before the statement date.

    Technical:
        Inputs: statement_date, due_date.
        Logic: flag due_date < statement_date.
        Edge cases: missing dates not flagged here (see R13).

    Business:
        Protects: against impossible payment terms that break dunning.
        Owner: data engineering checks date parsing; accounting confirms terms.
    """
    df = ctx["billing"]
    return _hits(df, df.due_date < df.statement_date, "R12_due_after_statement",
                 lambda r: "due date before statement date")


@rule("R13_mandatory_fields")
def mandatory_fields(ctx, cfg):
    """All mandatory fields are filled.

    Technical:
        Inputs: mandatory_fields list from config.
        Logic: flag lines with any null or empty mandatory field.
        Edge cases: unparseable dates become null during extraction and are caught here.

    Business:
        Protects: completeness of the billing record for audit.
        Owner: data engineering if caused by parsing, otherwise the cedent.
    """
    df = ctx["billing"]
    cols = cfg["mandatory_fields"]
    mask = df[cols].isna().any(axis=1) | (df[cols].astype(str) == "").any(axis=1)
    return _hits(df, mask, "R13_mandatory_fields", lambda r: "mandatory field missing")


@rule("R14_partner_matches_treaty")
def partner_matches_treaty(ctx, cfg):
    """Partner on the line is the cedent of the referenced treaty.

    Technical:
        Inputs: partner_id, treaty_partner_id, partner master.
        Logic: flag known partners that differ from the treaty's cedent.
        Edge cases: unknown partners (R06) and unknown treaties (R07) are skipped.

    Business:
        Protects: against allocating business to the wrong counterparty.
        Owner: treaty accounting.
    """
    df = ctx["billing"]
    mask = df.treaty_found & df.partner_id.isin(ctx["partners"]) & (df.partner_id != df.treaty_partner_id)
    return _hits(df, mask, "R14_partner_matches_treaty", lambda r: f"treaty cedent is {r.treaty_partner_id}")


def run_all(ctx, cfg=None):
    cfg = cfg or load_config()
    out = []
    for fn in RULES:
        out.extend(fn(ctx, cfg))
    return out
