import psycopg2
import psycopg2.extras
from datetime import date
from config import BLACK_BOOK_DB_URL
from core.audit import log

# Black Book schema (Neon PostgreSQL):
# transactions: id, date(TEXT YYYY-MM-DD), description, category, amount(REAL),
#               account_id(FK→accounts.id), type, to_account_id(nullable FK), notes, created_at
# accounts:     id, name(UNIQUE), account_type, is_debt, include_in_runway,
#               starting_balance(REAL), sort_order, created_at, current_balance_override

def get_connection():
    return psycopg2.connect(BLACK_BOOK_DB_URL, cursor_factory=psycopg2.extras.RealDictCursor)

def _resolve_account_id(cur, account_name: str) -> int | None:
    """Look up account id by name (case-insensitive)."""
    cur.execute("SELECT id FROM accounts WHERE LOWER(name) = LOWER(%s)", (account_name,))
    row = cur.fetchone()
    return row["id"] if row else None

def _get_all_accounts(cur) -> list:
    cur.execute("SELECT id, name FROM accounts ORDER BY sort_order")
    return cur.fetchall()

def add_expense(amount: float, description: str, category: str,
                account: str, date_str: str = None) -> dict:
    try:
        conn = get_connection()
        cur = conn.cursor()
        account_id = _resolve_account_id(cur, account)
        if account_id is None:
            accounts = _get_all_accounts(cur)
            names = [a["name"] for a in accounts]
            cur.close(); conn.close()
            return {"success": False, "error": f"Account '{account}' not found. Available: {names}"}
        cur.execute("""
            INSERT INTO transactions (date, description, category, amount, account_id, type)
            VALUES (%s, %s, %s, %s, %s, 'expense')
        """, (date_str or date.today().isoformat(), description, category, amount, account_id))
        conn.commit()
        cur.close(); conn.close()
        log(f"Added expense ${amount} — {description} [{category}]", system="BLACK_BOOK")
        return {"success": True}
    except Exception as e:
        log(f"DB error: {e}", system="BLACK_BOOK")
        return {"success": False, "error": str(e)}

def add_income(amount: float, description: str, account: str, date_str: str = None) -> dict:
    try:
        conn = get_connection()
        cur = conn.cursor()
        account_id = _resolve_account_id(cur, account)
        if account_id is None:
            accounts = _get_all_accounts(cur)
            names = [a["name"] for a in accounts]
            cur.close(); conn.close()
            return {"success": False, "error": f"Account '{account}' not found. Available: {names}"}
        cur.execute("""
            INSERT INTO transactions (date, description, category, amount, account_id, type)
            VALUES (%s, %s, 'Income', %s, %s, 'income')
        """, (date_str or date.today().isoformat(), description, amount, account_id))
        conn.commit()
        cur.close(); conn.close()
        log(f"Added income ${amount} — {description}", system="BLACK_BOOK")
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_recent_transactions(limit: int = 20) -> dict:
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT t.id, t.date, t.description, t.category, t.amount, t.type, t.notes,
                   a.name as account_name
            FROM transactions t
            JOIN accounts a ON a.id = t.account_id
            ORDER BY t.date DESC, t.id DESC
            LIMIT %s
        """, (limit,))
        rows = cur.fetchall()
        cur.close(); conn.close()
        return {"success": True, "data": [dict(r) for r in rows]}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_spending_summary(period: str = "month") -> dict:
    try:
        conn = get_connection()
        cur = conn.cursor()
        # date column is TEXT (YYYY-MM-DD) — cast to DATE for PostgreSQL date functions
        if period == "month":
            date_filter = "DATE_TRUNC('month', CAST(date AS DATE)) = DATE_TRUNC('month', CURRENT_DATE)"
        elif period == "week":
            date_filter = "CAST(date AS DATE) >= CURRENT_DATE - INTERVAL '7 days'"
        else:  # year
            date_filter = "DATE_TRUNC('year', CAST(date AS DATE)) = DATE_TRUNC('year', CURRENT_DATE)"
        cur.execute(f"""
            SELECT category,
                   ROUND(SUM(amount)::numeric, 2) as total,
                   COUNT(*) as count
            FROM transactions
            WHERE type = 'expense' AND {date_filter}
            GROUP BY category
            ORDER BY total DESC
        """)
        rows = cur.fetchall()
        cur.close(); conn.close()
        return {"success": True, "data": [dict(r) for r in rows]}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_account_balances() -> dict:
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT
                a.name,
                a.account_type,
                a.is_debt,
                ROUND((
                    a.starting_balance +
                    COALESCE(SUM(
                        CASE
                            WHEN t.type = 'income'   THEN  t.amount
                            WHEN t.type = 'expense'  THEN -t.amount
                            WHEN t.type = 'transfer' AND t.to_account_id = a.id THEN  t.amount
                            WHEN t.type = 'transfer' AND t.account_id   = a.id THEN -t.amount
                            ELSE 0
                        END
                    ), 0)
                )::numeric, 2) AS balance
            FROM accounts a
            LEFT JOIN transactions t
                ON t.account_id = a.id OR t.to_account_id = a.id
            GROUP BY a.id, a.name, a.account_type, a.is_debt, a.starting_balance
            ORDER BY a.sort_order
        """)
        rows = cur.fetchall()
        cur.close(); conn.close()
        return {"success": True, "data": [dict(r) for r in rows]}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_category_average(category: str) -> dict:
    """Get the weekly average spend for a category (used by trigger engine)."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT AVG(weekly_total) as avg_weekly FROM (
                SELECT DATE_TRUNC('week', CAST(date AS DATE)) as week,
                       SUM(amount) as weekly_total
                FROM transactions
                WHERE type = 'expense'
                  AND category = %s
                  AND CAST(date AS DATE) >= CURRENT_DATE - INTERVAL '12 weeks'
                GROUP BY week
            ) weekly_sums
        """, (category,))
        row = cur.fetchone()
        cur.close(); conn.close()
        return {"success": True, "avg_weekly": float(row["avg_weekly"] or 0)}
    except Exception as e:
        return {"success": False, "error": str(e)}
