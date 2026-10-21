"""SQLite setup and database operations for EcoCoin."""
import hashlib
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from config import DATABASE_PATH, DEFAULT_REWARD_RATES

def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

@contextmanager
def get_connection():
    """Open a database connection and always close it."""
    conn = sqlite3.connect(DATABASE_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def hash_password(password, salt=None):
    """Hash a password using PBKDF2; never store the raw password."""
    salt = salt or os.urandom(16).hex()
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200_000).hex()
    return f"{salt}${digest}"

def verify_password(password, stored_hash):
    try:
        salt, expected = stored_hash.split("$", 1)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200_000).hex()
        return hashlib.compare_digest(actual, expected)
    except (ValueError, AttributeError):
        # hmac.compare_digest is the standard constant-time comparison helper.
        import hmac
        try:
            salt, expected = stored_hash.split("$", 1)
            actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200_000).hex()
            return hmac.compare_digest(actual, expected)
        except (ValueError, AttributeError):
            return False

def initialize_database():
    """Create tables and insert safe, repeatable starter data."""
    with get_connection() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE COLLATE NOCASE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('user', 'admin')),
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS waste_categories (
            name TEXT PRIMARY KEY,
            accepted INTEGER NOT NULL CHECK(accepted IN (0, 1)),
            reward_rate INTEGER NOT NULL CHECK(reward_rate >= 0)
        );
        CREATE TABLE IF NOT EXISTS collection_points (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            address TEXT NOT NULL,
            accepted_waste TEXT NOT NULL,
            hours TEXT NOT NULL,
            contact TEXT NOT NULL DEFAULT '',
            active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0, 1))
        );
        CREATE TABLE IF NOT EXISTS waste_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            category TEXT NOT NULL REFERENCES waste_categories(name),
            quantity_kg REAL NOT NULL CHECK(quantity_kg > 0),
            notes TEXT NOT NULL DEFAULT '',
            collection_point_id INTEGER NOT NULL REFERENCES collection_points(id),
            reward_rate INTEGER NOT NULL CHECK(reward_rate >= 0),
            estimated_coins INTEGER NOT NULL CHECK(estimated_coins >= 0),
            status TEXT NOT NULL DEFAULT 'Pending'
                CHECK(status IN ('Pending', 'Approved', 'Rejected')),
            decision_reason TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            decided_at TEXT,
            decided_by INTEGER REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            request_id INTEGER UNIQUE REFERENCES waste_requests(id),
            amount INTEGER NOT NULL,
            transaction_type TEXT NOT NULL CHECK(transaction_type IN ('Credit', 'Debit')),
            reason TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_requests_user_status
            ON waste_requests(user_id, status);
        CREATE INDEX IF NOT EXISTS idx_transactions_user
            ON transactions(user_id, created_at);
        """)
        for name, rate in DEFAULT_REWARD_RATES.items():
            conn.execute(
                "INSERT OR IGNORE INTO waste_categories(name, accepted, reward_rate) VALUES (?, 1, ?)",
                (name, rate),
            )
        conn.execute(
            "INSERT OR IGNORE INTO waste_categories(name, accepted, reward_rate) VALUES (?, 0, 0)",
            ("Automobile waste",),
        )
        conn.execute(
            "INSERT OR IGNORE INTO waste_categories(name, accepted, reward_rate) VALUES (?, 0, 0)",
            ("Construction waste",),
        )
        points = [
            ("Green Community Recycling Point", "Demo address: Main Community Centre", "Plastic, Polythene", "Mon–Sat, 9:00 AM–5:00 PM", "Demo contact"),
            ("Eco Hub Collection Desk", "Demo address: Central Market Area", "Plastic, Rubber, Wood", "Mon–Fri, 10:00 AM–4:00 PM", "Demo contact"),
            ("Neighbourhood Green Point", "Demo address: Local Library Building", "Plastic, Polythene, Rubber, Wood", "Tue–Sun, 9:00 AM–6:00 PM", "Demo contact"),
        ]
        for point in points:
            conn.execute(
                """INSERT OR IGNORE INTO collection_points
                (name, address, accepted_waste, hours, contact, active)
                VALUES (?, ?, ?, ?, ?, 1)""", point
            )
        admin = conn.execute("SELECT id FROM users WHERE username = ?", ("admin",)).fetchone()
        if not admin:
            conn.execute(
                "INSERT INTO users(username, password_hash, role, created_at) VALUES (?, ?, 'admin', ?)",
                ("admin", hash_password("EcoCoinDemo2026!"), utc_now()),
            )

def register_user(username, password):
    username = username.strip()
    if len(username) < 3 or len(username) > 30:
        raise ValueError("Username must be between 3 and 30 characters.")
    if not username.replace("_", "").isalnum():
        raise ValueError("Use only letters, numbers, and underscores in the username.")
    if len(password) < 8:
        raise ValueError("Password must contain at least 8 characters.")
    with get_connection() as conn:
        try:
            cur = conn.execute(
                "INSERT INTO users(username, password_hash, role, created_at) VALUES (?, ?, 'user', ?)",
                (username, hash_password(password), utc_now()),
            )
        except sqlite3.IntegrityError:
            raise ValueError("That username is already in use.")
        return cur.lastrowid

def authenticate(username, password):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username.strip(),)).fetchone()
    if row and verify_password(password, row["password_hash"]):
        return {"id": row["id"], "username": row["username"], "role": row["role"]}
    return None

def get_user_balance(user_id):
    with get_connection() as conn:
        row = conn.execute(
            """SELECT COALESCE(SUM(CASE WHEN transaction_type='Credit' THEN amount
                                         WHEN transaction_type='Debit' THEN -amount END), 0) AS balance
               FROM transactions WHERE user_id = ?""", (user_id,)
        ).fetchone()
        return int(row["balance"])

def get_categories(accepted_only=False):
    with get_connection() as conn:
        sql = "SELECT * FROM waste_categories"
        if accepted_only:
            sql += " WHERE accepted = 1"
        return [dict(r) for r in conn.execute(sql + " ORDER BY name").fetchall()]

def get_active_points():
    with get_connection() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM collection_points WHERE active = 1 ORDER BY name"
        ).fetchall()]

def create_request(user_id, category, quantity_kg, notes, point_id):
    from rewards import calculate_reward, validate_submission
    with get_connection() as conn:
        cat = conn.execute("SELECT * FROM waste_categories WHERE name = ?", (category,)).fetchone()
        point = conn.execute(
            "SELECT * FROM collection_points WHERE id = ? AND active = 1", (point_id,)
        ).fetchone()
        if not cat:
            raise ValueError("Select a valid waste category.")
        if not point:
            raise ValueError("Select an active collection point.")
        validate_submission(category, quantity_kg, bool(cat["accepted"]), point["accepted_waste"])
        rate, coins = calculate_reward(quantity_kg, cat["reward_rate"])
        cur = conn.execute(
            """INSERT INTO waste_requests
            (user_id, category, quantity_kg, notes, collection_point_id, reward_rate,
             estimated_coins, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'Pending', ?)""",
            (user_id, category, float(quantity_kg), notes.strip(), point_id, rate, coins, utc_now()),
        )
        return cur.lastrowid, coins

def decide_request(request_id, admin_id, approve, reason=""):
    """Atomically update request and create at most one reward transaction."""
    with get_connection() as conn:
        request = conn.execute(
            "SELECT * FROM waste_requests WHERE id = ?", (request_id,)
        ).fetchone()
        if not request:
            raise ValueError("Request not found.")
        if request["status"] != "Pending":
            raise ValueError("This request has already been reviewed.")
        if approve:
            category = conn.execute(
                "SELECT accepted FROM waste_categories WHERE name = ?", (request["category"],)
            ).fetchone()
            if not category or not category["accepted"]:
                raise ValueError("This category is not currently eligible for rewards.")
            conn.execute(
                """UPDATE waste_requests SET status='Approved', decision_reason=?,
                   decided_at=?, decided_by=? WHERE id=? AND status='Pending'""",
                (reason.strip() or "Approved by administrator.", utc_now(), admin_id, request_id),
            )
            # UNIQUE(request_id) ensures the same request cannot earn twice.
            conn.execute(
                """INSERT INTO transactions
                (user_id, request_id, amount, transaction_type, reason, created_at)
                VALUES (?, ?, ?, 'Credit', ?, ?)""",
                (request["user_id"], request_id, request["estimated_coins"],
                 f"Approved waste request #{request_id}", utc_now()),
            )
        else:
            if not reason.strip():
                raise ValueError("Please provide a reason for rejection.")
            conn.execute(
                """UPDATE waste_requests SET status='Rejected', decision_reason=?,
                   decided_at=?, decided_by=? WHERE id=? AND status='Pending'""",
                (reason.strip(), utc_now(), admin_id, request_id),
            )

def get_requests(user_id=None, status=None):
    sql = """SELECT r.*, u.username, p.name AS point_name
             FROM waste_requests r
             JOIN users u ON u.id=r.user_id
             JOIN collection_points p ON p.id=r.collection_point_id"""
    conditions, params = [], []
    if user_id is not None:
        conditions.append("r.user_id = ?")
        params.append(user_id)
    if status and status != "All":
        conditions.append("r.status = ?")
        params.append(status)
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    sql += " ORDER BY r.created_at DESC"
    with get_connection() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]

def get_transactions(user_id):
    with get_connection() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM transactions WHERE user_id=? ORDER BY created_at DESC", (user_id,)
        ).fetchall()]

def get_stats(user_id=None):
    conditions, params = [], []
    if user_id is not None:
        conditions.append("user_id = ?")
        params.append(user_id)
    where = (" WHERE " + " AND ".join(conditions)) if conditions else ""
    with get_connection() as conn:
        totals = conn.execute(
            f"""SELECT COUNT(*) AS requests,
                COALESCE(SUM(CASE WHEN status='Approved' THEN quantity_kg ELSE 0 END), 0) AS approved_kg,
                COALESCE(SUM(CASE WHEN status='Pending' THEN 1 ELSE 0 END), 0) AS pending,
                COALESCE(SUM(CASE WHEN status='Approved' THEN estimated_coins ELSE 0 END), 0) AS approved_coins
                FROM waste_requests{where}""", params
        ).fetchone()
        rows = conn.execute(
            f"""SELECT category, SUM(quantity_kg) AS kg FROM waste_requests
                {where + (' AND' if where else ' WHERE')} status='Approved'
                GROUP BY category ORDER BY kg DESC""", params
        ).fetchall()
        return dict(totals), [dict(r) for r in rows]

def update_category(name, accepted, rate):
    if rate < 0:
        raise ValueError("Reward rate cannot be negative.")
    with get_connection() as conn:
        conn.execute(
            "UPDATE waste_categories SET accepted=?, reward_rate=? WHERE name=?",
            (int(accepted), int(rate), name),
        )

def add_collection_point(name, address, accepted_waste, hours, contact):
    if not name.strip() or not address.strip() or not accepted_waste.strip() or not hours.strip():
        raise ValueError("Name, address, accepted waste, and hours are required.")
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO collection_points(name, address, accepted_waste, hours, contact, active)
            VALUES (?, ?, ?, ?, ?, 1)""",
            (name.strip(), address.strip(), accepted_waste.strip(), hours.strip(), contact.strip()),
        )

def get_all_users():
    with get_connection() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT id, username, role, created_at FROM users ORDER BY username"
        ).fetchall()]
