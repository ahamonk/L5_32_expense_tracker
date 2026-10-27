# Lab 5: Static Code Analysis — Reflection

**Project:** Personal Expense Tracker (`expense_tracker.py`)
**Tools:** Pylint 4.1.3, Bandit 1.9.4, Flake8 7.4.1 on Python 3.14.7

| Tool   | Before                              | After                                              |
|--------|-------------------------------------|----------------------------------------------------|
| Bandit | 4 findings (1 High, 2 Medium, 1 Low) | 0 unsuppressed; 2 suppressed with `# nosec` (B404, B603) |
| Pylint | 5.27/10, 26 messages                | 10.00/10, 0 messages                               |
| Flake8 | 4 findings                          | 0 findings                                         |

The fixes were made in three commits: security (Bandit), code quality (Pylint) and formatting (Flake8). The details are in `issues.md`.

---

## 1. Which issues were the easiest to fix, and which were the hardest? Why?

**Easiest: Flake8 formatting and Pylint docstring and naming messages.**
The four Flake8 findings were mechanical, and each told me the exact line and column:

- E203: remove the space in `{"amount" : amount, ...}`
- E302: add a missing blank line before `printLedger`
- E261: put two spaces before an inline comment
- E501: wrap a 93-character `print` call

None of these changes what the program does. The missing-docstring messages (C0114/C0116) and the camelCase names (C0103) were just as easy to understand, though tedious: 12 naming and 11 docstring messages made up most of the 26 Pylint messages.

Even the easy fixes needed a rerun. When I fixed E203, I accidentally deleted the space after the comma as well, so Flake8 reported a new **E231 (missing whitespace after ',')**. The rerun caught it immediately. That shows why the lab says to repeat the run–fix–rerun loop instead of assuming a fix is correct.

**Hardest: the High-severity B605 finding and the `global` statement (W0603).**

- **B605 (shell injection).** The original `openStatement` ran `os.system("xdg-open " + path)`. Because this goes through a shell, a path containing `;` or `&&` could run arbitrary commands. Replacing it with `subprocess.run([opener, path], check=False)` removes the shell. I also resolved `xdg-open` with `shutil.which` so the executable has a full path, and the function raises a clear error if the opener is missing. Even so, Bandit then reported two *new* Low findings: B404 for importing `subprocess` and B603 for calling it. I had to decide whether these were real problems in this code. I concluded they were not, because the argument list is fixed and no shell is used, and suppressed them with `# nosec` and a justification. My first attempt put the justification on the same line (`# nosec B404 - only used with ...`). Bandit 1.9.4 tried to read the words after `nosec` as test IDs and printed warnings, so I moved each justification onto its own comment line.
- **B306 (`tempfile.mktemp`).** This also needed thought. `mktemp` only returns an unused file name, which another process could create before the program does. `mkstemp` fixes that race by creating the file atomically, but it also opens it, so I had to close the returned file descriptor. It also fails if the folder doesn't exist, so I added `os.makedirs(REPORT_DIR, exist_ok=True)`. The secure version is therefore not a one-word swap: `export_report()` now creates an empty file instead of returning a name.
- **W0603 (`global monthly_budget`).** This was the biggest change. The expense list and budget lived at module level, and `setBudget` changed the budget through `global`. A local suppression would have silenced the warning without fixing the design. Instead, I moved the state into an `ExpenseTracker` class, turned the related functions into methods, and changed `main()` to work through a tracker object. This touched most of the file. I had to be careful that the printed output stayed exactly the same, and checked it with `diff` against the original program's output.

## 2. Did the static analysis tools report any false positives? If so, describe one example.

Yes, at least in context. The clearest example is **Bandit B603 (`subprocess_without_shell_equals_true`)** on the new `subprocess.run([opener, path], check=False)` line, together with **B404** on `import subprocess`.

Bandit raises these for *any* use of `subprocess`, because it cannot tell where the arguments come from. In this code the risk it describes, shell interpretation of untrusted input, does not exist: the call uses an argument list, `shell` is left at its default of `False`, and the executable path comes from `shutil.which`. In fact, B603 appeared *because* I removed the more dangerous `os.system` call. I therefore treated B404 and B603 as false positives here and suppressed them with `# nosec B404` and `# nosec B603`, each with a comment explaining why.

The suppression has limits, though:

- **Suppressing is not the same as eliminating.** The after report says "No issues identified", but it also says "Total potential issues skipped due to specifically being disabled: 2". The two checks were silenced on my judgement; they were not proven safe.
- **A related risk is still there.** If `path` started with `-`, `xdg-open` could treat it as a command-line option instead of a file name. This is far less serious than shell injection, but no tool reported it, so the call is not "secure" in every respect.

There was also a Pylint message whose *wording* was misleading even though it pointed at a real problem. C0103 said `monthly_budget` "doesn't conform to UPPER_CASE naming style", because Pylint treats every module-level name as a constant. But `monthly_budget` was not a constant: the program changes it in `setBudget`. Renaming it to `MONTHLY_BUDGET` would have silenced Pylint and made the code *less* honest. The real fix was removing the mutable global, which addressed W0603 and C0103 together.

I do **not** consider B105 (hardcoded password) a false positive, even though the value was a demo string. A password committed to a repository is readable by anyone with access to it.

## 3. How would you integrate static analysis tools into your actual software development workflow?

The tools took seconds to run and found real problems, so I would run them automatically at several points instead of only at the end:

1. **In the editor.** Turn on Pylint and Flake8 in VS Code so naming, docstring and formatting problems are flagged while typing. The E231 I introduced while fixing E203 would have been caught as I typed it.
2. **Pre-commit hooks.** Use the `pre-commit` framework to run Flake8 and Bandit on staged files before every commit. This keeps style-only fixes out of review and stops a hardcoded secret like `BANK_SYNC_PASSWORD = "demo-sync-pass"` from ever being committed.
3. **Continuous integration.** Run all three tools on every pull request, for example in a GitHub Actions workflow, and fail the build if:
   - `pylint --fail-under=9.5` falls below the lab's target,
   - `flake8` reports anything, or
   - `bandit -r . -ll` reports a Medium or High finding.
4. **Shared configuration.** Pylint and Flake8 disagree on line length: Pylint's default limit is 100, Flake8's is 79. My summary line was flagged by Flake8 at 93 characters, but by Pylint (as C0301) only after the refactor made it 109. A project should set one limit for both tools in `pyproject.toml`, `setup.cfg` or `.flake8`, so they don't contradict each other.
5. **Reviewing suppressions.** Every `# nosec` or `# pylint: disable` should come with a justification and be checked in code review. Bandit's "skipped" count shows how many suppressions exist, so it can be tracked over time. Suppressions should never become an easy way to make a report look clean.

Static analysis does not replace tests. Neither tool noticed that `main()` does `tracker.biggest_expense()["note"]`, which would raise `TypeError` if no expenses had been recorded, because `biggest_expense()` returns `None` in that case. This project has no unit tests; in a real workflow I would run the tools alongside tests, not instead of them.

## 4. What tangible improvements did you observe in code quality, readability, or potential robustness after applying the fixes?

**Security**
- The High-severity shell injection is gone: `os.system` with string concatenation became `subprocess.run` with an argument list and a full path from `shutil.which`.
- Temporary files are created safely: `mkstemp` replaces the deprecated, race-prone `mktemp`, and the report folder comes from `tempfile.gettempdir()` instead of the hardcoded `/tmp/expense_reports`. That hardcoded path was also not portable, since it doesn't exist on a normal Windows machine like the one I ran the lab on.
- The password is no longer in the source code. It is read from the `BANK_SYNC_PASSWORD` environment variable, every password is rejected when the variable is unset, and the comparison uses `hmac.compare_digest` instead of `==`.

**Design and robustness**
- The `ExpenseTracker` class removed the global mutable state. Several independent trackers can now exist, for example one per test, without sharing an expense list.
- `biggest_expense()` uses `max(..., default=None)` instead of `try: ... except Exception: return None`. The old version would also have hidden unrelated errors, such as a missing `"amount"` key; the new one handles only the empty case and lets real bugs surface.
- `main()` now runs only under `if __name__ == "__main__":`. Before, `import expense_tracker` printed the entire demo as a side effect. No tool flagged this; I noticed it while testing the security changes.

**Readability**
- Pylint went from **5.27/10 to 10.00/10**.
- Names follow snake_case (`add_expense`, `total_by_category`, `report_path`).
- Every public function and method has a docstring.
- `print_ledger` uses `enumerate(self.expenses, start=1)` instead of indexing `expenses[i]` inside `range(len(...))`.

**Style**
- Flake8 went from **4 findings to 0**, and the file follows PEP 8 spacing, blank lines and line length.

**Behaviour preserved**
- The program's printed output is identical before and after the fixes. I captured the original output and compared it with `diff` after each commit.
- This is a check of the demonstration run only, not a test suite. The behaviour of the non-demo helpers did change on purpose:
  - `export_report()` now creates the file.
  - `check_sync_password()` needs the environment variable.

**Overall**
The reports moved from 34 findings (26 Pylint messages, 4 Bandit, 4 Flake8) to none unsuppressed. More importantly, the code became safer and easier to reason about. The two suppressed Bandit checks, the `xdg-open` option-argument case and the unguarded `["note"]` subscript in `main()` show that a clean report is a good baseline, not proof that the code is correct or fully secure.
