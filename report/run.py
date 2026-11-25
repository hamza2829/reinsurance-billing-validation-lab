"""Validation run: CSV + HTML report and precision/recall against ground truth."""
import argparse
import json
import sys
import time
from pathlib import Path

import pandas as pd

from extract.extract import OUT as STG, load_context
from rules.validators import RULES, load_config, run_all

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).parent / "out"
TRUTH = ROOT / "data" / "raw" / "ground_truth.csv"
COLS = ["rule_id", "line_id", "treaty_id", "partner_id", "message"]


def evaluate(findings, truth):
    """Compare findings with ground truth on (line_id, defect_type)."""
    expected = set(zip(truth.line_id, truth.defect_type))
    mapping = {fn.rule_id: fn.defect_type for fn in RULES}
    found, fps = set(), []
    for f in findings:
        key = (f["line_id"], mapping.get(f["rule_id"]))
        (found.add(key) if key in expected else fps.append(f))
    tp = len(found)
    return {"expected": len(expected), "true_positives": tp, "false_positives": len(fps),
            "missed": sorted(map(list, expected - found)),
            "precision": round(tp / (tp + len(fps)), 4) if tp + len(fps) else 1.0,
            "recall": round(tp / len(expected), 4) if expected else 1.0, "false_positive_rows": fps}


def summarize(df):
    return {k: (df.groupby(k).size().reset_index(name="failures") if len(df) else pd.DataFrame(columns=[k, "failures"]))
            for k in ("rule_id", "treaty_id", "partner_id")}


def html(metrics, summaries, df):
    parts = ["<html><head><meta charset='utf-8'><title>Validation report</title></head><body>",
             "<h1>Reinsurance billing validation report (synthetic data)</h1>",
             f"<p>Rules: {metrics['rules']} | Lines: {metrics['lines']} | Findings: {metrics['findings']} | "
             f"Precision: {metrics['precision']} | Recall: {metrics['recall']} | "
             f"False positives: {metrics['false_positives']} | Runtime: {metrics['runtime_s']} s</p>"]
    for k, s in summaries.items():
        parts += [f"<h2>Failures per {k}</h2>", s.to_html(index=False)]
    parts += ["<h2>All findings</h2>", df.to_html(index=False), "</body></html>"]
    return "\n".join(parts)


def run(db=STG / "staging.duckdb", truth=TRUTH, out=OUT, config=None):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    ctx = load_context(db)
    findings = run_all(ctx, load_config(config) if config else None)
    runtime = round(time.perf_counter() - t0, 3)
    df = pd.DataFrame(findings, columns=COLS)
    ev = evaluate(findings, pd.read_csv(truth))
    fps = ev.pop("false_positive_rows")
    metrics = {"rules": len(RULES), "lines": len(ctx["billing"]), "findings": len(df), "runtime_s": runtime, **ev}
    summaries = summarize(df)
    df.to_csv(out / "failures.csv", index=False)
    pd.DataFrame(fps, columns=COLS).to_csv(out / "false_positives.csv", index=False)
    for k, s in summaries.items():
        s.to_csv(out / f"failures_per_{k.split('_')[0]}.csv", index=False)
    (out / "report.html").write_text(html(metrics, summaries, df))
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2))
    return metrics


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", default=str(STG / "staging.duckdb"))
    p.add_argument("--truth", default=str(TRUTH))
    p.add_argument("--out", default=str(OUT))
    a = p.parse_args(argv)
    m = run(a.db, a.truth, a.out)
    print(json.dumps({k: v for k, v in m.items() if k != "missed"}))
    if m["missed"]:
        print(f"MISSED DEFECTS: {m['missed']}", file=sys.stderr)
    return 0 if not m["missed"] else 1


if __name__ == "__main__":
    sys.exit(main())
