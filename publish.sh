#!/usr/bin/env bash
# One-time publish: creates the repo, 3 issues, 3 feature-branch PRs (merged), watches CI.
# Needs: git, gh (logged in once via `gh auth login`).
set -euo pipefail
REPO=hamza2829/reinsurance-billing-validation-lab
export GIT_AUTHOR_NAME="Hamza Sohail" GIT_AUTHOR_EMAIL="hamzashiekh2829@gmail.com"
export GIT_COMMITTER_NAME="$GIT_AUTHOR_NAME" GIT_COMMITTER_EMAIL="$GIT_AUTHOR_EMAIL"
FEAT1="docs/rules"; FEAT2=".github/workflows/ci.yml"; FEAT3="README.md BACKLOG.md"
mkdir -p ../_stash && for p in $FEAT1 $FEAT2 $FEAT3; do mkdir -p "../_stash/$(dirname $p)"; mv "$p" "../_stash/$p"; done
git init -b main && git add -A && git commit -m "Core: generator, DuckDB extraction, 14 rules, report, tests"
gh repo create "$REPO" --public --source=. --push
I1=$(gh issue create -R $REPO -t "Generate rule docs from docstrings" -b "Technical + business Markdown per rule in docs/rules/." | grep -o '[0-9]*$')
I2=$(gh issue create -R $REPO -t "CI pipeline with report artifact" -b "Install, generate, extract, validate, pytest+coverage, upload report." | grep -o '[0-9]*$')
I3=$(gh issue create -R $REPO -t "README with measured results" -b "Mermaid diagram, measured numbers, synthetic-data disclaimer." | grep -o '[0-9]*$')
pr() { # branch issue title paths...
  local b=$1 i=$2 t=$3; shift 3
  git checkout -b "$b" main
  for p in "$@"; do mkdir -p "$(dirname $p)"; mv "../_stash/$p" "$p"; done
  git add -A && git commit -m "$t (closes #$i)" && git push -u origin "$b"
  gh pr create -R $REPO -B main -H "$b" -t "$t" -b "Closes #$i"
  gh pr merge "$b" -R $REPO --merge --delete-branch
  git checkout main && git pull --ff-only origin main
}
pr feature/rule-docs "$I1" "Add generated rule docs" $FEAT1
pr feature/ci "$I2" "Add CI workflow" $FEAT2
pr feature/readme "$I3" "Add README and backlog" $FEAT3
rm -rf ../_stash
sleep 10; gh run watch -R $REPO --exit-status "$(gh run list -R $REPO -L1 --json databaseId -q '.[0].databaseId')"
