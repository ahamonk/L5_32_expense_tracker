"""Monthly expense tracker: records expenses, totals them, tracks a budget."""

import hmac
import os
import shutil
# subprocess is only used with a fixed argument list and no shell.
import subprocess  # nosec B404
import tempfile
from datetime import datetime

BANK_SYNC_PASSWORD = os.environ.get("BANK_SYNC_PASSWORD", "")
DEFAULT_MONTHLY_BUDGET = 20000
REPORT_DIR = os.path.join(tempfile.gettempdir(), "expense_reports")


class ExpenseTracker:
    """Holds the recorded expenses and the monthly budget."""

    def __init__(self, monthly_budget=DEFAULT_MONTHLY_BUDGET):
        self.expenses = []
        self.monthly_budget = monthly_budget

    def add_expense(self, amount, category="Misc", note=""):
        """Record an expense; return False if the amount is not positive."""
        if amount <= 0:
            print("Ignoring invalid amount", amount)
            return False
        self.expenses.append({"amount": amount, "category": category,
                              "note": note,
                              "time": datetime.now().isoformat()})
        return True

    def total_by_category(self):
        """Return a dict mapping each category to its total spend."""
        totals = {}
        for expense in self.expenses:
            category = expense["category"]
            totals[category] = totals.get(category, 0) + expense["amount"]
        return totals

    def set_budget(self, new_budget):
        """Replace the monthly budget."""
        self.monthly_budget = new_budget

    def remaining_budget(self):
        """Return the budget left after all recorded expenses."""
        spent = sum(expense["amount"] for expense in self.expenses)
        return self.monthly_budget - spent

    def biggest_expense(self):
        """Return the largest expense, or None if nothing is recorded."""
        return max(self.expenses, key=lambda expense: expense["amount"],
                   default=None)

    def print_ledger(self):
        """Print a numbered list of expenses."""
        for number, expense in enumerate(self.expenses, start=1):
            print(number, expense["category"], expense["amount"])


def check_sync_password(password):
    """Return True if password matches the configured bank-sync password."""
    if not BANK_SYNC_PASSWORD:
        return False
    return hmac.compare_digest(password.encode(), BANK_SYNC_PASSWORD.encode())


def export_report():
    """Create an empty report file in REPORT_DIR and return its path."""
    # Helper kept for the lab: not called by the demo
    os.makedirs(REPORT_DIR, exist_ok=True)
    fd, report_path = tempfile.mkstemp(suffix=".txt", dir=REPORT_DIR)
    os.close(fd)
    return report_path


def open_statement(path):
    """Open a statement file with the desktop's default application."""
    # Helper kept for the lab: not called by the demo
    opener = shutil.which("xdg-open")
    if opener is None:
        raise FileNotFoundError("xdg-open is not available")
    # Arguments are passed as a list with no shell, so path cannot inject.
    subprocess.run([opener, path], check=False)  # nosec B603


def main():
    """Run a short demonstration of the tracker."""
    tracker = ExpenseTracker()
    print("Biggest expense before any entries:", tracker.biggest_expense())
    tracker.add_expense(450, "Food", "Lunch with team")
    tracker.add_expense(1200, "Travel", "Cab to airport")
    tracker.add_expense(-50, "Food")
    tracker.add_expense(300, "Food", "Groceries")
    tracker.add_expense(999, "Bills", "Internet")
    tracker.set_budget(5000)
    tracker.print_ledger()
    print("Totals:", tracker.total_by_category())
    print("Remaining budget:", tracker.remaining_budget())  # after set_budget
    print("Biggest expense:", tracker.biggest_expense()["note"])
    print("Sync password accepted:", check_sync_password("guess"))
    print("Summary:", len(tracker.expenses),
          "expenses recorded against a budget of", tracker.monthly_budget)


if __name__ == "__main__":
    main()
