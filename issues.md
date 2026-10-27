# Lab 5: Static Code Analysis — Issues Found and Fixed

**File:** `expense_tracker.py`
**Tools:** Pylint 4.1.3, Bandit 1.9.4, Flake8 7.4.1 (Python 3.14.7)

Line numbers refer to the original file, as listed in the `*_report_before.txt` reports.

## Summary

| Tool   | Before                                | After                    |
|--------|---------------------------------------|--------------------------|
| Bandit | 4 issues (1 High, 2 Medium, 1 Low)    | No unsuppressed issues; 2 suppressed with `# nosec` (B404, B603) |
| Pylint | 5.27/10 (26 messages)                 | 10.00/10 (0 messages)    |
| Flake8 | 4 issues                              | 0 issues (empty report)  |

The program's printed output is the same before and after the fixes.

## Issue table

Ordered by severity: Bandit High/Medium first, then Pylint warnings, then conventions and style.

| # | Issue | Type | Line(s) | Description | Fix Approach |
|---|-------|------|---------|-------------|--------------|
| 1 | Shell command injection (Bandit B605, **High**) | Security | 61 | `os.system("xdg-open " + path)` runs through a shell, so a path such as `x; rm -rf ~` would run extra commands (CWE-78). | Resolve `xdg-open` with `shutil.which` and call `subprocess.run([opener, path], check=False)` with an argument list and no shell. This change made Bandit raise two new Low findings, for the `subprocess` import (B404) and the call (B603). Both are suppressed with `# nosec` and a written justification, because no shell is involved. They are suppressed, not resolved: Bandit still counts them as "2 skipped" in the after report. |
| 2 | Insecure temp file (Bandit B306, **Medium**) | Security | 55 | `tempfile.mktemp` only returns a name. Another process can create that file before we do (race condition, CWE-377). The function is also deprecated. | Use `tempfile.mkstemp`, which creates the file atomically, close the returned descriptor and return the path. Create `REPORT_DIR` first with `os.makedirs(..., exist_ok=True)`. |
| 3 | Hardcoded temp directory (Bandit B108, **Medium**) | Security | 8 | `"/tmp/expense_reports"` is a fixed, world-writable location (CWE-377). It also does not exist on Windows. | Build the path with `os.path.join(tempfile.gettempdir(), "expense_reports")`. |
| 4 | Hardcoded password (Bandit B105, Low) | Security | 5 | The bank-sync password `"demo-sync-pass"` is stored in source code, so anyone who can read the repo has it (CWE-259). | Read it from the `BANK_SYNC_PASSWORD` environment variable. Reject everything when it is unset. Compare with `hmac.compare_digest`, which, unlike `==`, does not stop at the first mismatching character. |
| 5 | Global statement (Pylint W0603) | Design | 29 | `setBudget` changes module-level state through `global monthly_budget`. Hidden shared state makes the code hard to test and reuse. | Move `expenses` and `monthly_budget` into an `ExpenseTracker` class. The functions that use them become methods. |
| 6 | Overly broad exception (Pylint W0718) | Bug risk | 41 | `except Exception` hides any error in `biggestExpense`, not only the empty-list case it was meant for. | Remove the `try`/`except` and use `max(..., default=None)`, which returns `None` for an empty list without raising. |
| 7 | `range(len(...))` loop (Pylint C0200) | Code quality | 45 | `printLedger` indexes `expenses[i]` instead of iterating directly. | `for number, expense in enumerate(self.expenses, start=1)`. |
| 8 | Naming convention (Pylint C0103, ×12) | Convention | 7, 11, 20, 28 (×2), 33, 38, 44, 49, 53, 55, 59 | camelCase function, argument and variable names (`addExpense`, `newBudget`, `reportPath` and others), plus the module-level variable `monthly_budget` flagged as a non-UPPER_CASE constant. | Rename to snake_case (`add_expense`, `new_budget`, `report_path` …). The budget becomes an instance attribute, and its default is the constant `DEFAULT_MONTHLY_BUDGET`. |
| 9 | Missing docstrings (Pylint C0114/C0116, ×11) | Documentation | 1, 11, 20, 28, 33, 38, 44, 49, 53, 59, 64 | No module docstring and no function docstrings. | Add a module docstring and one-line docstrings to the class and to every function and method except `__init__`, which Pylint does not require. |
| 10 | Whitespace before `:` (Flake8 E203) | Style | 15 | `{"amount" : amount, ...}`. | `{"amount": amount, ...}`. |
| 11 | Missing blank lines (Flake8 E302) | Style | 44 | Only one blank line before `def printLedger`. | Add the blank line (after the class refactor this became a method, where Flake8 reports it as E301). |
| 12 | Inline comment spacing (Flake8 E261) | Style | 74 | Only one space before `# after setBudget`. | Use two spaces before `#`. |
| 13 | Line too long (Flake8 E501) | Style | 77 | The summary `print` is 93 characters (limit 79). | Wrap the call arguments across two lines. |

## Other change

- **Unguarded `main()` call (line 80):** no tool flagged this, but `main()` ran at import time, so `import expense_tracker` printed the whole demo. It now runs only under `if __name__ == "__main__":`.

## Behaviour notes

- **Program output:** byte-for-byte identical before and after, checked with `diff` on the captured output.
- **Sync password:** the demo still prints `Sync password accepted: False`. To accept a password, set the `BANK_SYNC_PASSWORD` environment variable. If it is unset, every password is rejected, which is the safe default.
- **`export_report()`:** now creates an empty file and returns its path, where the original only returned an unused name. Creating the file is what makes the operation race-free.
- **Function names:** the module's functions changed from camelCase module functions to snake_case `ExpenseTracker` methods. Nothing else in the repository imports them.

## Commits

1. `Fix Bandit security findings`: issues 1–4
2. `Fix Pylint code-quality findings`: issues 5–9 and the `main()` guard. It also moved the B404/B603 justifications onto their own comment lines, because Bandit 1.9.4 read the text after `# nosec` as test IDs and printed warnings.
3. `Fix Flake8 formatting findings`: issues 10–13
