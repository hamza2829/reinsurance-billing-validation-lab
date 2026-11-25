"""Seeded generator for SYNTHETIC reinsurance billing data (three source systems)."""
import argparse
import json
import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

SEED = 42
CURRENCIES = ["EUR", "USD", "GBP", "CHF"]
RAW = Path(__file__).parent / "raw"
DEFECTS = ["wrong_total", "currency_mismatch", "late_statement", "duplicate_line",
           "missing_partner", "missing_treaty", "negative_premium", "source_inconsistency"]


def month_end(year, month):
    nxt = date(year + month // 12, month % 12 + 1, 1)
    return nxt - timedelta(days=1)


def build(seed=SEED, n_treaties=20, n_partners=8, year=2025):
    """Build clean treaties, claims and statement lines. Returns (treaties, claims, lines, rng)."""
    rng = random.Random(seed)
    partners = [f"P{i:03d}" for i in range(1, n_partners + 1)]
    treaties = [dict(treaty_id=f"T{i:03d}", cedent_id=rng.choice(partners),
                     treaty_type=rng.choice(["Quota Share", "Surplus", "XoL"]),
                     currency=rng.choice(CURRENCIES), commission_rate=rng.choice([0.15, 0.2, 0.25, 0.3]),
                     due_days=rng.choice([30, 45, 60])) for i in range(1, n_treaties + 1)]
    claims, lines = [], []
    for t in treaties:
        for m in range(1, 13):
            period = f"{year}-{m:02d}"
            total = 0.0
            for _ in range(rng.randint(0, 3)):
                amt = round(rng.uniform(1000, 50000), 2)
                total += amt
                claims.append(dict(claim_id=f"C{len(claims) + 1:05d}", treaty_id=t["treaty_id"],
                                   period=period, amount=amt, currency=t["currency"]))
            premium = round(rng.uniform(50000, 250000), 2)
            commission = round(premium * t["commission_rate"], 2)
            total = round(total, 2)
            sdate = month_end(year, m) + timedelta(days=rng.randint(1, 10))
            due = sdate + timedelta(days=t["due_days"])
            lines.append(dict(line_id=f"L{len(lines) + 1:05d}", statement_id=f"S-{t['cedent_id']}-{period}",
                              treaty_id=t["treaty_id"], partner_id=t["cedent_id"], period=period,
                              currency=t["currency"], premium=premium, claims=total, commission=commission,
                              balance=round(premium - total - commission, 2), statement_date=sdate,
                              due_date=due, received_date=sdate + timedelta(days=rng.randint(0, t["due_days"]))))
    return treaties, claims, lines, rng


def _rebalance(line):
    line["balance"] = round(line["premium"] - line["claims"] - line["commission"], 2)


def inject(treaties, lines, rng, per_type=5):
    """Inject known defects into lines in place. Returns the ground-truth list."""
    rates = {t["treaty_id"]: t["commission_rate"] for t in treaties}
    targets = rng.sample(range(len(lines)), per_type * len(DEFECTS))
    truth, dups = [], []
    for k, idx in enumerate(targets):
        d, line = DEFECTS[k // per_type], lines[idx]
        if d == "wrong_total":
            line["balance"] = round(line["balance"] + rng.choice([-1, 1]) * rng.uniform(100, 5000), 2)
        elif d == "currency_mismatch":
            line["currency"] = rng.choice([c for c in CURRENCIES if c != line["currency"]])
        elif d == "late_statement":
            line["received_date"] = line["due_date"] + timedelta(days=rng.randint(1, 40))
        elif d == "duplicate_line":
            dup = dict(line, line_id=f"L{len(lines) + len(dups) + 1:05d}")
            dups.append(dup)
            line = dup
        elif d == "missing_partner":
            line["partner_id"] = "P999"
        elif d == "missing_treaty":
            line["treaty_id"] = "T999"
        elif d == "negative_premium":
            line["premium"] = -line["premium"]
            line["commission"] = round(line["premium"] * rates[line["treaty_id"]], 2)
            _rebalance(line)
        else:  # source_inconsistency
            line["claims"] = round(line["claims"] + rng.uniform(500, 5000), 2)
            _rebalance(line)
        truth.append(dict(line_id=line["line_id"], defect_type=d,
                          treaty_id=line["treaty_id"], partner_id=line["partner_id"]))
    lines.extend(dups)
    return truth


def write(treaties, claims, lines, truth, out=RAW):
    """Write the three sources with realistic formatting noise, plus ground truth."""
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for i, t in enumerate(treaties):
        t = dict(t)
        if i % 3 == 0:
            t["treaty_id"] = f" {t['treaty_id'].lower()} "
        if i % 4 == 0:
            t["currency"] = t["currency"].lower()
        rows.append(t)
    pd.DataFrame(rows).to_csv(out / "treaties.csv", index=False)
    rows = []
    for i, c in enumerate(claims):
        c = dict(c)
        if i % 2:
            c["amount"] = f"{c['amount']:.2f}"
        if i % 5 == 0:
            c["treaty_id"] = c["treaty_id"].lower() + " "
        rows.append(c)
    (out / "claims.json").write_text(json.dumps({"source": "claims_system", "claims": rows}, indent=1))
    rows = []
    for i, line in enumerate(lines):
        line = dict(line)
        fmt = "%d.%m.%Y" if i % 2 else "%Y-%m-%d"
        for k in ("statement_date", "due_date", "received_date"):
            line[k] = line[k].strftime(fmt)
        if i % 7 == 0:
            line["partner_id"] = f"  {line['partner_id']}"
        if i % 6 == 0:
            line["currency"] = line["currency"].lower() + " "
        rows.append(line)
    pd.DataFrame(rows).to_excel(out / "partner_statements.xlsx", index=False, sheet_name="statements")
    pd.DataFrame(truth).to_csv(out / "ground_truth.csv", index=False)


def generate(seed=SEED, out=RAW):
    treaties, claims, lines, rng = build(seed)
    truth = inject(treaties, lines, rng)
    write(treaties, claims, lines, truth, out)
    return {"treaties": len(treaties), "claims": len(claims), "lines": len(lines), "defects": len(truth)}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--seed", type=int, default=SEED)
    p.add_argument("--out", default=str(RAW))
    a = p.parse_args(argv)
    stats = generate(a.seed, a.out)
    print(stats)
    return stats


if __name__ == "__main__":
    main()
