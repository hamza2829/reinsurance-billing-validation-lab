"""Generate docs/rules/*.md from rule docstrings."""
import argparse
import inspect
from pathlib import Path

from rules.validators import RULES

DOCS = Path(__file__).resolve().parent.parent / "docs" / "rules"


def parse(fn):
    doc = inspect.getdoc(fn)
    summary, rest = doc.split("\n", 1)
    tech = rest.split("Technical:")[1].split("Business:")[0].strip()
    bus = rest.split("Business:")[1].strip()
    return summary.strip(), tech, bus


def render(fn):
    summary, tech, bus = parse(fn)
    bullets = lambda s: "\n".join(f"- {line.strip()}" for line in s.splitlines() if line.strip())
    return (f"# {fn.rule_id}\n\n{summary}\n\nInjected defect type: `{fn.defect_type or 'none'}`\n\n"
            f"## Technical\n\n{bullets(tech)}\n\n## Business\n\n{bullets(bus)}\n")


def write_docs(out=DOCS):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    index = ["# Validation rules\n", "| Rule | Summary |", "|---|---|"]
    for fn in RULES:
        (out / f"{fn.rule_id}.md").write_text(render(fn))
        index.append(f"| [{fn.rule_id}]({fn.rule_id}.md) | {parse(fn)[0]} |")
    (out / "README.md").write_text("\n".join(index) + "\n")
    return len(RULES)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", default=str(DOCS))
    n = write_docs(p.parse_args(argv).out)
    print(f"{n} rule docs written")
    return n


if __name__ == "__main__":
    main()
