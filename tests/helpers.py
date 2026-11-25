import tempfile
from functools import lru_cache
from pathlib import Path

import pandas as pd

from data import generate
from extract import extract

BASE = dict(statement_id="S1", treaty_id="T001", partner_id="P001", currency="EUR", premium=1000.0,
            claims=100.0, commission=200.0, balance=700.0, statement_date=pd.Timestamp("2025-02-05"),
            due_date=pd.Timestamp("2025-03-07"), received_date=pd.Timestamp("2025-02-20"),
            treaty_currency="EUR", commission_rate=0.2, treaty_partner_id="P001", treaty_found=True,
            claims_system_total=100.0)


def ctx(*overrides):
    rows = [{**BASE, "line_id": f"L{i}", "period": f"2025-{i + 1:02d}", **o} for i, o in enumerate(overrides)]
    return {"billing": pd.DataFrame(rows), "partners": {"P001", "P002"}}


@lru_cache(maxsize=1)
def pipeline():
    root = Path(tempfile.mkdtemp())
    generate.generate(out=root / "raw")
    log = extract.run(root / "raw", root / "stg")
    return root, log
