"""
Simple Banking System (NexBank)
Flask Web Application
Database Management Systems Project (EGB1221)
Department of Electronics and Communication Engineering
K. Ramakrishnan College of Technology
"""

import os
from functools import wraps
from datetime import datetime
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, jsonify
)
from database import (
    init_database, query_db, execute_db, execute_transfer
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "nexbank-secret-key-2026-egb1221")

# Ensure database is initialized on startup
with app.app_context():
    try:
        init_database()
    except Exception as e:
        print(f"[Init Warning] Database initialization: {e}")


# =======================================================
# Authentication Decorators
# =======================================================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("login"))
        if session.get("role") != "admin":
            flash("Access denied: Administrator privileges required.", "danger")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated_function


# =======================================================
# Context Processor (makes user info available in templates)
# =======================================================
@app.context_processor
def inject_user():
    return {
        "current_user": session.get("username"),
        "current_role": session.get("role"),
        "current_customer_id": session.get("customer_id"),
        "now": datetime.now()
    }


# =======================================================
# Authentication Routes
# =======================================================
@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        user = query_db(
            "SELECT * FROM users WHERE username = ? AND password = ?",
            (username, password),
            one=True
        )

        if user:
            session["user_id"] = user["user_id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            session["customer_id"] = user["customer_id"]
            flash(f"Welcome back, {user['username']}!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password. Please try again.", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been successfully logged out.", "info")
    return redirect(url_for("login"))


# =======================================================
# Dashboard Route (Figure 5.3)
# =======================================================
@app.route("/")
@app.route("/dashboard")
@login_required
def dashboard():
    role = session.get("role")
    customer_id = session.get("customer_id")

    if role == "admin":
        # System-wide statistics for Admin
        total_customers = query_db("SELECT COUNT(*) as count FROM customers", one=True)["count"]
        active_accounts = query_db("SELECT COUNT(*) as count FROM accounts WHERE status = 'active'", one=True)["count"]
        total_balance_res = query_db("SELECT COALESCE(SUM(balance), 0) as total FROM accounts WHERE status = 'active'", one=True)
        total_balance = float(total_balance_res["total"]) if total_balance_res else 0.0
        total_txns = query_db("SELECT COUNT(*) as count FROM transactions", one=True)["count"]
        active_loans = query_db("SELECT COUNT(*) as count FROM loans WHERE status = 'approved'", one=True)["count"]
        total_branches = query_db("SELECT COUNT(*) as count FROM branches", one=True)["count"]

        # Accounts Breakdown (Savings vs Current)
        breakdown_savings = query_db(
            "SELECT COUNT(*) as count, COALESCE(SUM(balance), 0) as total FROM accounts WHERE account_type = 'savings' AND status = 'active'",
            one=True
        )
        breakdown_current = query_db(
            "SELECT COUNT(*) as count, COALESCE(SUM(balance), 0) as total FROM accounts WHERE account_type = 'current' AND status = 'active'",
            one=True
        )

        # Recent Transactions with Customer Info
        recent_txns = query_db("""
            SELECT t.*, a.customer_id, a.account_type, 
                   c.first_name, c.last_name
            FROM transactions t
            JOIN accounts a ON t.account_id = a.account_id
            JOIN customers c ON a.customer_id = c.customer_id
            ORDER BY t.created_at DESC
            LIMIT 6
        """)

        return render_template(
            "dashboard.html",
            total_customers=total_customers,
            active_accounts=active_accounts,
            total_balance=total_balance,
            total_txns=total_txns,
            active_loans=active_loans,
            total_branches=total_branches,
            breakdown_savings=breakdown_savings,
            breakdown_current=breakdown_current,
            recent_txns=recent_txns
        )
    else:
        # Customer-specific Dashboard
        customer = query_db("SELECT * FROM customers WHERE customer_id = ?", (customer_id,), one=True)
        accounts = query_db("SELECT * FROM accounts WHERE customer_id = ?", (customer_id,))
        total_balance = sum(float(a["balance"]) for a in accounts if a["status"] == "active")
        active_accounts = len([a for a in accounts if a["status"] == "active"])
        
        loans = query_db("SELECT * FROM loans WHERE customer_id = ?", (customer_id,))
        active_loans = len([l for l in loans if l["status"] == "approved"])

        recent_txns = query_db("""
            SELECT t.*, a.account_type, c.first_name, c.last_name
            FROM transactions t
            JOIN accounts a ON t.account_id = a.account_id
            JOIN customers c ON a.customer_id = c.customer_id
            WHERE a.customer_id = ?
            ORDER BY t.created_at DESC
            LIMIT 6
        """, (customer_id,))

        breakdown_savings = {
            "count": len([a for a in accounts if a["account_type"] == "savings"]),
            "total": sum(float(a["balance"]) for a in accounts if a["account_type"] == "savings")
        }
        breakdown_current = {
            "count": len([a for a in accounts if a["account_type"] == "current"]),
            "total": sum(float(a["balance"]) for a in accounts if a["account_type"] == "current")
        }

        return render_template(
            "dashboard.html",
            customer=customer,
            total_customers=1,
            active_accounts=active_accounts,
            total_balance=total_balance,
            total_txns=len(recent_txns),
            active_loans=active_loans,
            total_branches=1,
            breakdown_savings=breakdown_savings,
            breakdown_current=breakdown_current,
            recent_txns=recent_txns
        )


# =======================================================
# Branches Management (Figure 5.5)
# =======================================================
@app.route("/branches")
@login_required
def branches():
    branches_list = query_db("""
        SELECT b.*, COUNT(c.customer_id) as customer_count
        FROM branches b
        LEFT JOIN customers c ON b.branch_id = c.branch_id
        GROUP BY b.branch_id
        ORDER BY b.branch_id ASC
    """)
    return render_template("branches.html", branches=branches_list)


@app.route("/branches/add", methods=["POST"])
@admin_required
def add_branch():
    name = request.form.get("name", "").strip()
    address = request.form.get("address", "").strip()
    city = request.form.get("city", "").strip()
    phone = request.form.get("phone", "").strip()

    if not (name and address and city and phone):
        flash("All branch fields are required.", "danger")
        return redirect(url_for("branches"))

    execute_db(
        "INSERT INTO branches (name, address, city, phone) VALUES (?, ?, ?, ?)",
        (name, address, city, phone)
    )
    flash(f"Branch '{name}' created successfully!", "success")
    return redirect(url_for("branches"))


@app.route("/branches/edit/<int:branch_id>", methods=["POST"])
@admin_required
def edit_branch(branch_id):
    name = request.form.get("name", "").strip()
    address = request.form.get("address", "").strip()
    city = request.form.get("city", "").strip()
    phone = request.form.get("phone", "").strip()

    execute_db(
        "UPDATE branches SET name = ?, address = ?, city = ?, phone = ? WHERE branch_id = ?",
        (name, address, city, phone, branch_id)
    )
    flash("Branch details updated successfully!", "success")
    return redirect(url_for("branches"))


@app.route("/branches/delete/<int:branch_id>", methods=["POST"])
@admin_required
def delete_branch(branch_id):
    # Check if customers exist in this branch
    count = query_db("SELECT COUNT(*) as count FROM customers WHERE branch_id = ?", (branch_id,), one=True)["count"]
    if count > 0:
        flash(f"Cannot delete branch: It still has {count} associated customer(s).", "danger")
        return redirect(url_for("branches"))

    execute_db("DELETE FROM branches WHERE branch_id = ?", (branch_id,))
    flash("Branch deleted successfully.", "info")
    return redirect(url_for("branches"))


# =======================================================
# Customer Management (Figure 5.4)
# =======================================================
@app.route("/customers")
@login_required
def customers():
    branches_list = query_db("SELECT branch_id, name, city FROM branches ORDER BY name")
    
    if session.get("role") == "admin":
        customers_list = query_db("""
            SELECT c.*, b.name as branch_name,
                   COUNT(DISTINCT a.account_id) as account_count,
                   COALESCE(SUM(a.balance), 0) as total_balance
            FROM customers c
            JOIN branches b ON c.branch_id = b.branch_id
            LEFT JOIN accounts a ON c.customer_id = a.customer_id AND a.status = 'active'
            GROUP BY c.customer_id
            ORDER BY c.customer_id ASC
        """)
    else:
        customer_id = session.get("customer_id")
        customers_list = query_db("""
            SELECT c.*, b.name as branch_name,
                   COUNT(DISTINCT a.account_id) as account_count,
                   COALESCE(SUM(a.balance), 0) as total_balance
            FROM customers c
            JOIN branches b ON c.branch_id = b.branch_id
            LEFT JOIN accounts a ON c.customer_id = a.customer_id AND a.status = 'active'
            WHERE c.customer_id = ?
            GROUP BY c.customer_id
        """, (customer_id,))

    return render_template("customers.html", customers=customers_list, branches=branches_list)


@app.route("/customers/add", methods=["POST"])
@admin_required
def add_customer():
    first_name = request.form.get("first_name", "").strip()
    last_name = request.form.get("last_name", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()
    address = request.form.get("address", "").strip()
    city = request.form.get("city", "").strip()
    dob = request.form.get("dob", "").strip()
    branch_id = request.form.get("branch_id")
    initial_account = request.form.get("initial_account")
    initial_deposit = float(request.form.get("initial_deposit", 0.0) or 0.0)

    try:
        cust_id = execute_db(
            """INSERT INTO customers (first_name, last_name, email, phone, address, city, dob, branch_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (first_name, last_name, email, phone, address, city, dob, branch_id)
        )

        # Create login credentials for customer
        username = first_name.lower().replace(" ", "")
        execute_db(
            "INSERT INTO users (username, password, role, customer_id) VALUES (?, ?, 'customer', ?)",
            (username, "password123", cust_id)
        )

        # If initial account option was chosen
        if initial_account in ("savings", "current"):
            acc_id = execute_db(
                "INSERT INTO accounts (customer_id, account_type, balance, status) VALUES (?, ?, ?, 'active')",
                (cust_id, initial_account, initial_deposit)
            )
            if initial_deposit > 0:
                execute_db(
                    "INSERT INTO transactions (account_id, txn_type, amount, description) VALUES (?, 'deposit', ?, 'Initial Account Opening Deposit')",
                    (acc_id, initial_deposit)
                )

        flash(f"Customer '{first_name} {last_name}' added successfully! (Login: {username} / password123)", "success")
    except Exception as e:
        flash(f"Error adding customer: {e}", "danger")

    return redirect(url_for("customers"))


@app.route("/customers/edit/<int:customer_id>", methods=["POST"])
@admin_required
def edit_customer(customer_id):
    first_name = request.form.get("first_name", "").strip()
    last_name = request.form.get("last_name", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()
    address = request.form.get("address", "").strip()
    city = request.form.get("city", "").strip()
    dob = request.form.get("dob", "").strip()
    branch_id = request.form.get("branch_id")

    execute_db(
        """UPDATE customers SET first_name=?, last_name=?, email=?, phone=?, address=?, city=?, dob=?, branch_id=?
           WHERE customer_id=?""",
        (first_name, last_name, email, phone, address, city, dob, branch_id, customer_id)
    )
    flash("Customer updated successfully!", "success")
    return redirect(url_for("customers"))


@app.route("/customers/delete/<int:customer_id>", methods=["POST"])
@admin_required
def delete_customer(customer_id):
    try:
        # Check active accounts
        acc_count = query_db("SELECT COUNT(*) as count FROM accounts WHERE customer_id = ?", (customer_id,), one=True)["count"]
        if acc_count > 0:
            flash(f"Cannot delete customer: {acc_count} linked account(s) exist. Please close accounts first.", "danger")
            return redirect(url_for("customers"))

        execute_db("DELETE FROM users WHERE customer_id = ?", (customer_id,))
        execute_db("DELETE FROM customers WHERE customer_id = ?", (customer_id,))
        flash("Customer removed successfully.", "info")
    except Exception as e:
        flash(f"Error deleting customer: {e}", "danger")
    return redirect(url_for("customers"))


# =======================================================
# Accounts Management (Figure 5.6)
# =======================================================
@app.route("/accounts")
@login_required
def accounts():
    role = session.get("role")
    customer_id = session.get("customer_id")
    
    customers_list = query_db("SELECT customer_id, first_name, last_name, email FROM customers ORDER BY first_name")

    if role == "admin":
        accounts_list = query_db("""
            SELECT a.*, c.first_name, c.last_name, c.email
            FROM accounts a
            JOIN customers c ON a.customer_id = c.customer_id
            ORDER BY a.account_id ASC
        """)
    else:
        accounts_list = query_db("""
            SELECT a.*, c.first_name, c.last_name, c.email
            FROM accounts a
            JOIN customers c ON a.customer_id = c.customer_id
            WHERE a.customer_id = ?
            ORDER BY a.account_id ASC
        """, (customer_id,))

    return render_template("accounts.html", accounts=accounts_list, customers=customers_list)


@app.route("/accounts/open", methods=["POST"])
@login_required
def open_account():
    role = session.get("role")
    if role == "admin":
        customer_id = request.form.get("customer_id")
    else:
        customer_id = session.get("customer_id")

    account_type = request.form.get("account_type", "savings")
    initial_balance = float(request.form.get("initial_balance", 0.0) or 0.0)

    acc_id = execute_db(
        "INSERT INTO accounts (customer_id, account_type, balance, status) VALUES (?, ?, ?, 'active')",
        (customer_id, account_type, initial_balance)
    )

    if initial_balance > 0:
        execute_db(
            "INSERT INTO transactions (account_id, txn_type, amount, description) VALUES (?, 'deposit', ?, 'Account Opening Deposit')",
            (acc_id, initial_balance)
        )

    flash(f"New {account_type.capitalize()} Account #{acc_id} successfully opened!", "success")
    return redirect(url_for("accounts"))


@app.route("/accounts/toggle-status/<int:account_id>", methods=["POST"])
@admin_required
def toggle_account_status(account_id):
    acc = query_db("SELECT status FROM accounts WHERE account_id = ?", (account_id,), one=True)
    if acc:
        new_status = "inactive" if acc["status"] == "active" else "active"
        execute_db("UPDATE accounts SET status = ? WHERE account_id = ?", (new_status, account_id))
        flash(f"Account #{account_id} status changed to '{new_status}'.", "info")
    return redirect(url_for("accounts"))


# =======================================================
# Transactions & Banking Operations (Deposit, Withdraw, Transfer)
# =======================================================
@app.route("/transactions")
@login_required
def transactions():
    role = session.get("role")
    customer_id = session.get("customer_id")

    if role == "admin":
        # All transactions
        txns = query_db("""
            SELECT t.*, a.account_type, c.first_name, c.last_name,
                   c2.first_name as to_first_name, c2.last_name as to_last_name
            FROM transactions t
            JOIN accounts a ON t.account_id = a.account_id
            JOIN customers c ON a.customer_id = c.customer_id
            LEFT JOIN accounts a2 ON t.to_account_id = a2.account_id
            LEFT JOIN customers c2 ON a2.customer_id = c2.customer_id
            ORDER BY t.created_at DESC
        """)
        user_accounts = query_db("""
            SELECT a.account_id, a.account_type, a.balance, c.first_name, c.last_name 
            FROM accounts a 
            JOIN customers c ON a.customer_id = c.customer_id
            WHERE a.status = 'active'
        """)
    else:
        # Transactions involving customer's accounts
        txns = query_db("""
            SELECT t.*, a.account_type, c.first_name, c.last_name,
                   c2.first_name as to_first_name, c2.last_name as to_last_name
            FROM transactions t
            JOIN accounts a ON t.account_id = a.account_id
            JOIN customers c ON a.customer_id = c.customer_id
            LEFT JOIN accounts a2 ON t.to_account_id = a2.account_id
            LEFT JOIN customers c2 ON a2.customer_id = c2.customer_id
            WHERE a.customer_id = ? OR a2.customer_id = ?
            ORDER BY t.created_at DESC
        """, (customer_id, customer_id))
        user_accounts = query_db("""
            SELECT a.account_id, a.account_type, a.balance, c.first_name, c.last_name 
            FROM accounts a 
            JOIN customers c ON a.customer_id = c.customer_id
            WHERE a.customer_id = ? AND a.status = 'active'
        """, (customer_id,))

    all_active_accounts = query_db("""
        SELECT a.account_id, a.account_type, a.balance, c.first_name, c.last_name 
        FROM accounts a 
        JOIN customers c ON a.customer_id = c.customer_id
        WHERE a.status = 'active'
    """)

    return render_template(
        "transactions.html",
        transactions=txns,
        user_accounts=user_accounts,
        all_active_accounts=all_active_accounts
    )


@app.route("/deposit", methods=["POST"])
@login_required
def deposit():
    account_id = request.form.get("account_id")
    amount = float(request.form.get("amount", 0.0) or 0.0)
    description = request.form.get("description", "Cash Deposit").strip() or "Cash Deposit"

    if amount <= 0:
        flash("Deposit amount must be greater than zero.", "danger")
        return redirect(url_for("transactions"))

    # Verify account
    acc = query_db("SELECT status, balance FROM accounts WHERE account_id = ?", (account_id,), one=True)
    if not acc or acc["status"] != "active":
        flash("Account not found or inactive.", "danger")
        return redirect(url_for("transactions"))

    # Update account balance and record transaction
    execute_db("UPDATE accounts SET balance = balance + ? WHERE account_id = ?", (amount, account_id))
    txn_id = execute_db(
        "INSERT INTO transactions (account_id, txn_type, amount, description) VALUES (?, 'deposit', ?, ?)",
        (account_id, amount, description)
    )

    new_balance = float(acc["balance"]) + amount
    flash(f"Deposit Successful! ${amount:,.2f} added to Account #{account_id}. New Balance: ${new_balance:,.2f} (Txn #{txn_id})", "success")
    return redirect(url_for("transactions"))


@app.route("/withdraw", methods=["POST"])
@login_required
def withdraw():
    account_id = request.form.get("account_id")
    amount = float(request.form.get("amount", 0.0) or 0.0)
    description = request.form.get("description", "ATM Withdrawal").strip() or "ATM Withdrawal"

    if amount <= 0:
        flash("Withdrawal amount must be greater than zero.", "danger")
        return redirect(url_for("transactions"))

    acc = query_db("SELECT status, balance FROM accounts WHERE account_id = ?", (account_id,), one=True)
    if not acc or acc["status"] != "active":
        flash("Account not found or inactive.", "danger")
        return redirect(url_for("transactions"))

    if float(acc["balance"]) < amount:
        flash(f"Withdrawal Failed: Insufficient funds! Current balance is ${float(acc['balance']):,.2f}.", "danger")
        return redirect(url_for("transactions"))

    execute_db("UPDATE accounts SET balance = balance - ? WHERE account_id = ?", (amount, account_id))
    txn_id = execute_db(
        "INSERT INTO transactions (account_id, txn_type, amount, description) VALUES (?, 'withdrawal', ?, ?)",
        (account_id, amount, description)
    )

    new_balance = float(acc["balance"]) - amount
    flash(f"Withdrawal Successful! ${amount:,.2f} deducted from Account #{account_id}. Remaining Balance: ${new_balance:,.2f} (Txn #{txn_id})", "success")
    return redirect(url_for("transactions"))


@app.route("/transfer", methods=["POST"])
@login_required
def transfer():
    from_account_id = request.form.get("from_account_id")
    to_account_id = request.form.get("to_account_id")
    amount = float(request.form.get("amount", 0.0) or 0.0)
    description = request.form.get("description", "Fund Transfer").strip() or "Fund Transfer"

    if from_account_id == to_account_id:
        flash("Source and destination accounts cannot be identical.", "danger")
        return redirect(url_for("transactions"))

    if amount <= 0:
        flash("Transfer amount must be greater than zero.", "danger")
        return redirect(url_for("transactions"))

    # Atomic ACID transfer
    success, msg = execute_transfer(from_account_id, to_account_id, amount, description)
    if success:
        flash(f"Transfer Successful: ${amount:,.2f} transferred from Account #{from_account_id} to Account #{to_account_id}.", "success")
    else:
        flash(f"Transfer Failed: {msg}", "danger")

    return redirect(url_for("transactions"))


# =======================================================
# Loans Management (Figure 5.2)
# =======================================================
@app.route("/loans")
@login_required
def loans():
    role = session.get("role")
    customer_id = session.get("customer_id")
    customers_list = query_db("SELECT customer_id, first_name, last_name FROM customers ORDER BY first_name")

    if role == "admin":
        loans_list = query_db("""
            SELECT l.*, c.first_name, c.last_name, c.email
            FROM loans l
            JOIN customers c ON l.customer_id = c.customer_id
            ORDER BY l.loan_id DESC
        """)
    else:
        loans_list = query_db("""
            SELECT l.*, c.first_name, c.last_name, c.email
            FROM loans l
            JOIN customers c ON l.customer_id = c.customer_id
            WHERE l.customer_id = ?
            ORDER BY l.loan_id DESC
        """, (customer_id,))

    return render_template("loans.html", loans=loans_list, customers=customers_list)


@app.route("/loans/apply", methods=["POST"])
@login_required
def apply_loan():
    role = session.get("role")
    if role == "admin":
        customer_id = request.form.get("customer_id")
    else:
        customer_id = session.get("customer_id")

    loan_type = request.form.get("loan_type")
    amount = float(request.form.get("amount", 0.0) or 0.0)
    tenure_months = int(request.form.get("tenure_months", 12))

    # Standard interest rate presets
    rates = {
        "home": 7.50,
        "education": 6.50,
        "auto": 8.00,
        "business": 9.00,
        "personal": 10.50
    }
    interest_rate = rates.get(loan_type, 8.50)

    execute_db(
        """INSERT INTO loans (customer_id, loan_type, amount, interest_rate, tenure_months, status)
           VALUES (?, ?, ?, ?, ?, 'pending')""",
        (customer_id, loan_type, amount, interest_rate, tenure_months)
    )

    flash(f"Loan application for ${amount:,.2f} ({loan_type.capitalize()}) submitted for approval!", "success")
    return redirect(url_for("loans"))


@app.route("/loans/update-status/<int:loan_id>", methods=["POST"])
@admin_required
def update_loan_status(loan_id):
    new_status = request.form.get("status")
    if new_status not in ("approved", "rejected", "closed"):
        flash("Invalid loan status.", "danger")
        return redirect(url_for("loans"))

    start_date = datetime.now().strftime("%Y-%m-%d") if new_status == "approved" else None
    
    if start_date:
        execute_db("UPDATE loans SET status = ?, start_date = ? WHERE loan_id = ?", (new_status, start_date, loan_id))
    else:
        execute_db("UPDATE loans SET status = ? WHERE loan_id = ?", (new_status, loan_id))

    flash(f"Loan #{loan_id} marked as {new_status.capitalize()}.", "info")
    return redirect(url_for("loans"))


# =======================================================
# Quick Balance API
# =======================================================
@app.route("/api/account/<int:account_id>")
@login_required
def get_account_details(account_id):
    acc = query_db("""
        SELECT a.*, c.first_name, c.last_name 
        FROM accounts a 
        JOIN customers c ON a.customer_id = c.customer_id 
        WHERE a.account_id = ?
    """, (account_id,), one=True)
    if acc:
        return jsonify(acc)
    return jsonify({"error": "Account not found"}), 404


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
