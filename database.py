"""
Database Access Layer for Simple Banking System (NexBank).
Supports SQLite out of the box (zero configuration) and MySQL
as specified in Appendix A (Page 24) of the project report.
"""

import os
import sqlite3
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
SQLITE_DB_PATH = BASE_DIR / "banking.db"
SCHEMA_PATH = BASE_DIR / "schema.sql"
SEED_PATH = BASE_DIR / "seed.sql"

# Check if MySQL is requested via environment variable
USE_MYSQL = os.environ.get("USE_MYSQL", "false").lower() in ("true", "1", "yes")

# MySQL Configuration matching project report Appendix A (Page 24)
MYSQL_CONFIG = {
    "host": os.environ.get("MYSQL_HOST", "localhost"),
    "port": int(os.environ.get("MYSQL_PORT", 3306)),
    "user": os.environ.get("MYSQL_USER", "root"),
    "password": os.environ.get("MYSQL_PASSWORD", "Parthiban2006@06"),
    "database": os.environ.get("MYSQL_DB", "banking"),
}


def get_connection():
    """Returns a database connection with dict-like row access."""
    if USE_MYSQL:
        try:
            import mysql.connector
            conn = mysql.connector.connect(**MYSQL_CONFIG)
            return conn, "mysql"
        except Exception as e:
            print(f"[Warning] MySQL connection failed ({e}). Falling back to SQLite.")

    # SQLite default
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn, "sqlite"


def query_db(query, args=(), one=False):
    """Execute a SELECT query and return dict results."""
    conn, engine = get_connection()
    try:
        if engine == "mysql":
            cursor = conn.cursor(dictionary=True)
            # Adapt '?' placeholder to '%s' for MySQL if needed
            mysql_query = query.replace("?", "%s")
            cursor.execute(mysql_query, args)
            rows = cursor.fetchall()
            cursor.close()
        else:
            cursor = conn.cursor()
            cursor.execute(query, args)
            rows = [dict(row) for row in cursor.fetchall()]
            cursor.close()
        return (rows[0] if rows else None) if one else rows
    finally:
        conn.close()


def execute_db(query, args=(), commit=True):
    """Execute INSERT/UPDATE/DELETE query and return last inserted ID."""
    conn, engine = get_connection()
    try:
        if engine == "mysql":
            cursor = conn.cursor()
            mysql_query = query.replace("?", "%s")
            cursor.execute(mysql_query, args)
            last_id = cursor.lastrowid
            if commit:
                conn.commit()
            cursor.close()
        else:
            cursor = conn.cursor()
            cursor.execute(query, args)
            last_id = cursor.lastrowid
            if commit:
                conn.commit()
            cursor.close()
        return last_id
    finally:
        conn.close()


def execute_transfer(from_account_id, to_account_id, amount, description="Fund Transfer"):
    """
    Executes an atomic transfer between two accounts using transaction semantics (ACID).
    Rolls back automatically on insufficient funds or errors.
    """
    conn, engine = get_connection()
    try:
        if engine == "mysql":
            cursor = conn.cursor(dictionary=True)
            # Check source balance
            cursor.execute("SELECT balance, status FROM accounts WHERE account_id = %s FOR UPDATE", (from_account_id,))
            src = cursor.fetchone()
            if not src or src['status'] != 'active':
                raise ValueError("Source account is not active or does not exist.")
            if src['balance'] < amount:
                raise ValueError(f"Insufficient funds. Current balance: ${src['balance']:.2f}")

            # Check target account
            cursor.execute("SELECT status FROM accounts WHERE account_id = %s", (to_account_id,))
            dest = cursor.fetchone()
            if not dest or dest['status'] != 'active':
                raise ValueError("Destination account is not active or does not exist.")

            # Update balances
            cursor.execute("UPDATE accounts SET balance = balance - %s WHERE account_id = %s", (amount, from_account_id))
            cursor.execute("UPDATE accounts SET balance = balance + %s WHERE account_id = %s", (amount, to_account_id))

            # Record transactions
            desc_out = f"{description} to Acct #{to_account_id}"
            desc_in = f"{description} from Acct #{from_account_id}"
            cursor.execute(
                "INSERT INTO transactions (account_id, txn_type, amount, to_account_id, description) VALUES (%s, 'transfer_out', %s, %s, %s)",
                (from_account_id, amount, to_account_id, desc_out)
            )
            cursor.execute(
                "INSERT INTO transactions (account_id, txn_type, amount, to_account_id, description) VALUES (%s, 'transfer_in', %s, %s, %s)",
                (to_account_id, amount, from_account_id, desc_in)
            )
            conn.commit()
            cursor.close()
        else:
            cursor = conn.cursor()
            # SQLite transaction
            cursor.execute("SELECT balance, status FROM accounts WHERE account_id = ?", (from_account_id,))
            src = cursor.fetchone()
            if not src or src['status'] != 'active':
                raise ValueError("Source account is not active or does not exist.")
            if src['balance'] < amount:
                raise ValueError(f"Insufficient funds. Current balance: ${src['balance']:.2f}")

            cursor.execute("SELECT status FROM accounts WHERE account_id = ?", (to_account_id,))
            dest = cursor.fetchone()
            if not dest or dest['status'] != 'active':
                raise ValueError("Destination account is not active or does not exist.")

            # Update balances
            cursor.execute("UPDATE accounts SET balance = balance - ? WHERE account_id = ?", (amount, from_account_id))
            cursor.execute("UPDATE accounts SET balance = balance + ? WHERE account_id = ?", (amount, to_account_id))

            # Record transactions
            desc_out = f"{description} to Acct #{to_account_id}"
            desc_in = f"{description} from Acct #{from_account_id}"
            cursor.execute(
                "INSERT INTO transactions (account_id, txn_type, amount, to_account_id, description) VALUES (?, 'transfer_out', ?, ?, ?)",
                (from_account_id, amount, to_account_id, desc_out)
            )
            cursor.execute(
                "INSERT INTO transactions (account_id, txn_type, amount, to_account_id, description) VALUES (?, 'transfer_in', ?, ?, ?)",
                (to_account_id, amount, from_account_id, desc_in)
            )
            conn.commit()
            cursor.close()
        return True, "Transfer completed successfully"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()


def init_database():
    """Initializes tables and seeds initial data if database is brand new."""
    conn, engine = get_connection()
    try:
        cursor = conn.cursor()
        if engine == "sqlite":
            with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
                schema_sql = f.read()
            cursor.executescript(schema_sql)

            # Check if branches exist to seed data
            cursor.execute("SELECT COUNT(*) FROM branches")
            count = cursor.fetchone()[0]
            if count == 0:
                with open(SEED_PATH, "r", encoding="utf-8") as f:
                    seed_sql = f.read()
                cursor.executescript(seed_sql)
                print("[Database] Schema created & seed data inserted into SQLite.")
            conn.commit()
        else:
            # MySQL initialization
            print("[Database] Initializing MySQL...")
            # For MySQL, schema can be applied via script
            with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
                commands = f.read().split(";")
                for cmd in commands:
                    if cmd.strip():
                        cursor.execute(cmd)
            cursor.execute("SELECT COUNT(*) FROM branches")
            count = cursor.fetchone()[0]
            if count == 0:
                with open(SEED_PATH, "r", encoding="utf-8") as f:
                    commands = f.read().split(";")
                    for cmd in commands:
                        if cmd.strip():
                            cursor.execute(cmd)
                print("[Database] Schema created & seed data inserted into MySQL.")
            conn.commit()
        cursor.close()
    finally:
        conn.close()


if __name__ == "__main__":
    init_database()
    print("Database initialized successfully!")
