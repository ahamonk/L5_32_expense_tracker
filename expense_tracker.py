import hmac
import os
import shutil
import subprocess  # nosec B404 - only used with a fixed argument list, no shell
import tempfile
from datetime import datetime

BANK_SYNC_PASSWORD = os.environ.get("BANK_SYNC_PASSWORD", "")
expenses = []
monthly_budget = 20000
REPORT_DIR = os.path.join(tempfile.gettempdir(), "expense_reports")


def addExpense(amount, category="Misc", note=""):
    if amount <= 0:
        print("Ignoring invalid amount", amount)
        return False
    expenses.append({"amount" : amount, "category": category,
                     "note": note, "time": datetime.now().isoformat()})
    return True


def totalByCategory():
    totals = {}
    for expense in expenses:
        category = expense["category"]
        totals[category] = totals.get(category, 0) + expense["amount"]
    return totals


def setBudget(newBudget):
    global monthly_budget
    monthly_budget = newBudget


def remainingBudget():
    spent = sum(expense["amount"] for expense in expenses)
    return monthly_budget - spent


def biggestExpense():
    try:
        return max(expenses, key=lambda expense: expense["amount"])
    except Exception:
        return None

def printLedger():
    for i in range(len(expenses)):
        print(i + 1, expenses[i]["category"], expenses[i]["amount"])


def checkSyncPassword(password):
    if not BANK_SYNC_PASSWORD:
        return False
    return hmac.compare_digest(password.encode(), BANK_SYNC_PASSWORD.encode())


def exportReport():
    # Helper kept for the lab: not called by the demo
    os.makedirs(REPORT_DIR, exist_ok=True)
    fd, reportPath = tempfile.mkstemp(suffix=".txt", dir=REPORT_DIR)
    os.close(fd)
    return reportPath


def openStatement(path):
    # Helper kept for the lab: not called by the demo
    opener = shutil.which("xdg-open")
    if opener is None:
        raise FileNotFoundError("xdg-open is not available")
    subprocess.run([opener, path], check=False)  # nosec B603 - no shell


def main():
    print("Biggest expense before any entries:", biggestExpense())
    addExpense(450, "Food", "Lunch with team")
    addExpense(1200, "Travel", "Cab to airport")
    addExpense(-50, "Food")
    addExpense(300, "Food", "Groceries")
    addExpense(999, "Bills", "Internet")
    setBudget(5000)
    printLedger()
    print("Totals:", totalByCategory())
    print("Remaining budget:", remainingBudget()) # after setBudget
    print("Biggest expense:", biggestExpense()["note"])
    print("Sync password accepted:", checkSyncPassword("guess"))
    print("Summary:", len(expenses), "expenses recorded against a budget of", monthly_budget)


main()
