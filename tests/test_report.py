import json

import pandas as pd

from report import run as r
from rules import docs
from tests.helpers import pipeline


def _run(tmp_path):
    root, _ = pipeline()
    return r.run(root / "stg" / "staging.duckdb", root / "raw" / "ground_truth.csv", tmp_path)


def test_all_defects_found(tmp_path):
    m = _run(tmp_path)
    assert m["recall"] == 1.0 and m["missed"] == []


def test_no_false_positives(tmp_path):
    assert _run(tmp_path)["false_positives"] == 0


def test_outputs_written(tmp_path):
    _run(tmp_path)
    for f in ("failures.csv", "report.html", "metrics.json", "failures_per_rule.csv",
              "failures_per_treaty.csv", "failures_per_partner.csv", "false_positives.csv"):
        assert (tmp_path / f).exists()


def test_html_has_sections(tmp_path):
    _run(tmp_path)
    html = (tmp_path / "report.html").read_text()
    assert "Failures per treaty_id" in html and "Failures per partner_id" in html


def test_evaluate_counts_false_positive():
    truth = pd.DataFrame({"line_id": ["L1"], "defect_type": ["wrong_total"]})
    ev = r.evaluate([{"rule_id": "R01_balance_total", "line_id": "L1"},
                     {"rule_id": "R03_currency_code_valid", "line_id": "L2"}], truth)
    assert ev["true_positives"] == 1 and ev["false_positives"] == 1 and ev["precision"] == 0.5


def test_evaluate_missed():
    truth = pd.DataFrame({"line_id": ["L1"], "defect_type": ["wrong_total"]})
    ev = r.evaluate([], truth)
    assert ev["recall"] == 0.0 and ev["missed"] == [["L1", "wrong_total"]] and ev["precision"] == 1.0


def test_summarize_empty():
    s = r.summarize(pd.DataFrame(columns=r.COLS))
    assert all(len(x) == 0 for x in s.values())


def test_main_exit_code(tmp_path):
    root, _ = pipeline()
    code = r.main(["--db", str(root / "stg" / "staging.duckdb"),
                   "--truth", str(root / "raw" / "ground_truth.csv"), "--out", str(tmp_path)])
    assert code == 0 and json.loads((tmp_path / "metrics.json").read_text())["rules"] >= 12


def test_main_reports_missed(tmp_path):
    root, _ = pipeline()
    truth = tmp_path / "t.csv"
    pd.DataFrame({"line_id": ["NOPE"], "defect_type": ["wrong_total"]}).to_csv(truth, index=False)
    assert r.main(["--db", str(root / "stg" / "staging.duckdb"), "--truth", str(truth),
                   "--out", str(tmp_path)]) == 1


def test_run_with_config_path(tmp_path):
    root, _ = pipeline()
    from rules.validators import CONFIG
    m = r.run(root / "stg" / "staging.duckdb", root / "raw" / "ground_truth.csv", tmp_path, CONFIG)
    assert m["recall"] == 1.0


def test_docs_generated(tmp_path):
    n = docs.main(["--out", str(tmp_path)])
    text = (tmp_path / "R01_balance_total.md").read_text()
    assert n >= 12 and "## Technical" in text and "## Business" in text and (tmp_path / "README.md").exists()
