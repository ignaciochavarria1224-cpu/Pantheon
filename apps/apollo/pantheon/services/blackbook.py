from __future__ import annotations

import sys
import os
from datetime import date
from pathlib import Path
from typing import Any

from config import BLACKBOOK_APP_PATH, BLACK_BOOK_DB_URL


def _queries():
    app_path = Path(BLACKBOOK_APP_PATH)
    if BLACK_BOOK_DB_URL and not os.environ.get("DATABASE_URL"):
        os.environ["DATABASE_URL"] = BLACK_BOOK_DB_URL
    if str(app_path) not in sys.path:
        sys.path.insert(0, str(app_path))
    from BlackBook.db import queries

    return queries


def get_snapshot() -> dict[str, Any]:
    try:
        queries = _queries()
        accounts = queries.load_accounts()
        transactions = queries.load_transactions(limit=200)
        balances = queries.calculate_account_balances(accounts, queries.load_transactions(limit=5000))
        reports = queries.load_daily_reports(limit=3)
        spending = queries.get_spending_summary("month")

        total_assets = sum(float(item["balance"]) for item in balances if not item["is_debt"])
        total_debt = sum(abs(float(item["balance"])) for item in balances if item["is_debt"])

        return {
            "connected": True,
            "accounts": accounts,
            "balances": balances,
            "recent_transactions": transactions[:8],
            "spending_month": spending[:8],
            "reports": reports,
            "net_worth": round(total_assets - total_debt, 2),
            "total_assets": round(total_assets, 2),
            "total_debt": round(total_debt, 2),
        }
    except Exception as exc:
        return {
            "connected": False,
            "error": str(exc),
            "accounts": [],
            "balances": [],
            "recent_transactions": [],
            "spending_month": [],
            "reports": [],
            "net_worth": 0,
            "total_assets": 0,
            "total_debt": 0,
        }


def get_account_balances() -> list[dict[str, Any]]:
    snapshot = get_snapshot()
    return snapshot.get("balances", [])


def get_recent_transactions(limit: int = 20) -> list[dict[str, Any]]:
    try:
        return _queries().load_transactions(limit=limit)
    except Exception:
        return []


def get_spending_summary(period: str = "month") -> list[dict[str, Any]]:
    try:
        return _queries().get_spending_summary(period=period)
    except Exception:
        return []


def get_accounts() -> list[dict[str, Any]]:
    try:
        return _queries().load_accounts()
    except Exception:
        return []


def add_expense(
    amount: float,
    description: str,
    category: str,
    account_name: str,
    tx_date: str | None = None,
    notes: str = "",
) -> dict[str, Any]:
    queries = _queries()
    accounts = queries.load_accounts()
    account = next((item for item in accounts if item["name"].lower() == account_name.lower()), None)
    if not account:
        return {"success": False, "error": f"Account '{account_name}' not found."}

    queries.add_transaction(
        tx_date=date.fromisoformat(tx_date) if tx_date else date.today(),
        description=description,
        category=category,
        amount=amount,
        account_id=int(account["id"]),
        tx_type="expense",
        to_account_id=None,
        notes=notes,
    )
    return {"success": True}


def add_income(
    amount: float,
    description: str,
    account_name: str,
    tx_date: str | None = None,
    notes: str = "",
) -> dict[str, Any]:
    queries = _queries()
    accounts = queries.load_accounts()
    account = next((item for item in accounts if item["name"].lower() == account_name.lower()), None)
    if not account:
        return {"success": False, "error": f"Account '{account_name}' not found."}

    queries.add_transaction(
        tx_date=date.fromisoformat(tx_date) if tx_date else date.today(),
        description=description,
        category="Income",
        amount=amount,
        account_id=int(account["id"]),
        tx_type="income",
        to_account_id=None,
        notes=notes,
    )
    return {"success": True}
