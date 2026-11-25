import json

import pandas as pd

from data import generate as g
from tests.helpers import pipeline


def test_build_is_deterministic():
    assert g.build(1)[2] == g.build(1)[2]


def test_different_seed_differs():
    assert g.build(1)[2] != g.build(2)[2]


def test_build_sizes():
    t, c, lines, _ = g.build()
    assert len(t) == 20 and len(lines) == 240 and len(c) > 0


def test_clean_lines_balance():
    for line in g.build()[2]:
        assert abs(line["premium"] - line["claims"] - line["commission"] - line["balance"]) < 0.011


def test_currencies_covered():
    assert {t["currency"] for t in g.build()[0]} <= set(g.CURRENCIES)


def test_month_end_december():
    assert g.month_end(2025, 12).isoformat() == "2025-12-31"


def test_inject_counts_every_defect_type():
    t, _, lines, rng = g.build()
    truth = g.inject(t, lines, rng)
    counts = pd.Series([x["defect_type"] for x in truth]).value_counts()
    assert set(counts.index) == set(g.DEFECTS) and (counts == 5).all()


def test_inject_adds_duplicates():
    t, _, lines, rng = g.build()
    g.inject(t, lines, rng)
    assert len(lines) == 245


def test_files_written():
    root, _ = pipeline()
    for f in ("treaties.csv", "claims.json", "partner_statements.xlsx", "ground_truth.csv"):
        assert (root / "raw" / f).exists()


def test_claims_json_shape():
    root, _ = pipeline()
    data = json.loads((root / "raw" / "claims.json").read_text())
    assert data["source"] == "claims_system" and data["claims"]


def test_raw_files_are_messy():
    root, _ = pipeline()
    t = pd.read_csv(root / "raw" / "treaties.csv", dtype=str)
    assert t.treaty_id.str.contains(" ").any() and t.currency.str.islower().any()


def test_main_returns_stats(tmp_path):
    stats = g.main(["--out", str(tmp_path), "--seed", "7"])
    assert stats["defects"] == 40 and (tmp_path / "ground_truth.csv").exists()
