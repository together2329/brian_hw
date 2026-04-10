# Lint Plan Mode Rules

1. First task: run /lint-all to get full picture of errors+warnings
2. Group fixes by type: errors → width mismatches → latches → unused
3. One task per file (or per error group if same file has many issues)
4. Final task: /lint-all 0 errors, write lint_report.txt
