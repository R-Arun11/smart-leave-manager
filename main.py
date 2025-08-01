import sqlite3
from datetime import datetime
from tabulate import tabulate
import csv

DB_FILE = 'leave.db'
ANNUAL_QUOTA = 20

def init_db():
    schema = """
    CREATE TABLE IF NOT EXISTS employees (
        emp_id TEXT PRIMARY KEY,
        name TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS leaves (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        emp_id TEXT NOT NULL,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        leave_type TEXT,
        reason TEXT,
        FOREIGN KEY (emp_id) REFERENCES employees(emp_id)
    );
    """
    with sqlite3.connect(DB_FILE) as conn:
        conn.executescript(schema)

def insert_sample_sql():
    try:
        with sqlite3.connect(DB_FILE) as conn:
            with open("sample_data.sql") as f:
                conn.executescript(f.read())
        print("✅ Sample data loaded.")
    except FileNotFoundError:
        print("⚠️  sample_data.sql not found. Skipping sample data insert.")

def is_valid_date(date_str):
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def calculate_duration(start, end):
    d1 = datetime.strptime(start, "%Y-%m-%d")
    d2 = datetime.strptime(end, "%Y-%m-%d")
    return (d2 - d1).days + 1

def get_used_leave_days(emp_id):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.execute("""
            SELECT SUM(julianday(end_date) - julianday(start_date) + 1)
            FROM leaves WHERE emp_id = ?
        """, (emp_id,))
        total = cursor.fetchone()[0]
        return total if total else 0

def check_overlap(emp_id, new_start, new_end):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.execute("""
            SELECT * FROM leaves
            WHERE emp_id = ?
              AND NOT (end_date < ? OR start_date > ?)
        """, (emp_id, new_start, new_end))
        return cursor.fetchone() is not None

def employee_exists(emp_id):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.execute("SELECT 1 FROM employees WHERE emp_id = ?", (emp_id,))
        return cursor.fetchone() is not None

def apply_leave(emp_id, start_date, end_date, leave_type, reason):
    if check_overlap(emp_id, start_date, end_date):
        print("❌ Leave overlaps with an existing request.")
        return

    leave_days = calculate_duration(start_date, end_date)
    used_days = get_used_leave_days(emp_id)

    if used_days + leave_days > ANNUAL_QUOTA:
        print(f"❌ Leave denied. Quota exceeded: Used {used_days}, Requested {leave_days}, Limit {ANNUAL_QUOTA}")
        return

    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
            INSERT INTO leaves (emp_id, start_date, end_date, leave_type, reason)
            VALUES (?, ?, ?, ?, ?)
        """, (emp_id, start_date, end_date, leave_type, reason))
    print("✅ Leave applied successfully.")

def view_leaves(emp_id):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.execute("""
            SELECT id, start_date, end_date, leave_type, reason
            FROM leaves WHERE emp_id = ?
            ORDER BY start_date
        """, (emp_id,))
        rows = cursor.fetchall()

    if not rows:
        print("ℹ️  No leaves found.")
    else:
        print(tabulate(rows, headers=["ID", "Start", "End", "Type", "Reason"], tablefmt="fancy_grid"))

def export_leaves(emp_id):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.execute("""
            SELECT * FROM leaves WHERE emp_id = ?
        """, (emp_id,))
        rows = cursor.fetchall()

    if not rows:
        print("ℹ️  No leaves to export.")
        return

    with open(f"{emp_id}_leaves.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Employee ID", "Start", "End", "Type", "Reason"])
        writer.writerows(rows)

    print(f"✅ Leave history exported to {emp_id}_leaves.csv")



def apply_leave_flow():
    emp_id = input("Employee ID (or 'b' to go back): ").strip()
    if emp_id.lower() == 'b':
        return False

    if not employee_exists(emp_id):
        print("❌ Employee ID not found. Please try again.")
        return False

    while True:
        start_date = input("Start Date (YYYY-MM-DD) (or 'b' to go back): ").strip()
        if start_date.lower() == 'b':
            return False
        if is_valid_date(start_date):
            break
        print("Invalid date format. Try again.")

    while True:
        end_date = input("End Date (YYYY-MM-DD) (or 'b' to go back): ").strip()
        if end_date.lower() == 'b':
            return False
        if is_valid_date(end_date) and end_date >= start_date:
            break
        print("Invalid or out-of-order date. Try again.")

    leave_type = input("Leave Type (or 'b' to go back): ").strip()
    if leave_type.lower() == 'b':
        return False

    reason = input("Reason for Leave (or 'b' to go back): ").strip()
    if reason.lower() == 'b':
        return False

    apply_leave(emp_id, start_date, end_date, leave_type, reason)
    return True

def view_leaves_flow():
    emp_id = input("Employee ID (or 'b' to go back): ").strip()
    if emp_id.lower() == 'b':
        return False

    if not employee_exists(emp_id):
        print("❌ Employee ID not found.")
        return False

    view_leaves(emp_id)
    return True

def export_leaves_flow():
    emp_id = input("Employee ID (or 'b' to go back): ").strip()
    if emp_id.lower() == 'b':
        return False

    if not employee_exists(emp_id):
        print("❌ Employee ID not found.")
        return False

    export_leaves(emp_id)
    return True

def menu():
    while True:
        print("\n📋 Smart Leave Manager")
        print("1. Apply for Leave")
        print("2. View Leave History")
        print("3. Export Leave History")
        print("4. Exit")
        choice = input("Choose an option (1-4): ").strip()

        if choice == '1':
            apply_leave_flow()

        elif choice == '2':
            view_leaves_flow()

        elif choice == '3':
            export_leaves_flow()

        elif choice == '4':
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Try 1-4.")



if __name__ == "__main__":
    init_db()
    insert_sample_sql()
    menu()
