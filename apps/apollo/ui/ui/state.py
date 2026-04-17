from __future__ import annotations

from datetime import datetime
from typing import List

import reflex as rx
import requests
from pydantic import BaseModel

APOLLO_API = "http://localhost:8001"


class Message(BaseModel):
    role: str
    content: str
    timestamp: str = ""


class BalanceItem(BaseModel):
    name: str
    balance: str
    account_type: str = ""
    is_debt: bool = False


class TransactionItem(BaseModel):
    date: str
    description: str
    category: str
    account: str
    amount: str
    tx_type: str


class SpendingItem(BaseModel):
    category: str
    total: str
    count: str


class ThemeItem(BaseModel):
    title: str
    preview: str
    updated_at: str


class QuestionItem(BaseModel):
    question: str
    context: str = ""


class TradeItem(BaseModel):
    symbol: str
    direction: str
    realized_pnl: str
    exit_reason: str
    exit_time: str


class AuditItem(BaseModel):
    timestamp: str
    system: str
    action: str
    detail: str = ""


class TraceItem(BaseModel):
    timestamp: str
    provider: str
    message: str
    subsystems: str
    latency: str
    status: str


def _format_timestamp(raw: str | None) -> str:
    if not raw:
        return "Unknown"
    try:
        return datetime.fromisoformat(raw).strftime("%b %d, %H:%M")
    except ValueError:
        return raw


def _truncate(text: str, limit: int) -> str:
    clean = (text or "").strip()
    return clean if len(clean) <= limit else f"{clean[: limit - 1].rstrip()}..."


class State(rx.State):
    active_tab: str = "apollo"
    pantheon_section: str = "overview"

    messages: List[Message] = []
    input_text: str = ""
    is_loading: bool = False
    context_loading: bool = False
    context_error: str = ""
    last_refreshed: str = "Never"

    latest_signal: str = "No recent system activity."
    pantheon_status: str = "Unknown"
    blackbook_status: str = "Unknown"
    maridian_status: str = "Unknown"
    olympus_status: str = "Unknown"

    self_model_excerpt: str = "Vault self-model loading..."

    net_worth: str = "$0.00"
    total_assets: str = "$0.00"
    total_debt: str = "$0.00"
    blackbook_balances: List[BalanceItem] = []
    blackbook_transactions: List[TransactionItem] = []
    blackbook_spending: List[SpendingItem] = []
    blackbook_accounts: List[str] = []
    blackbook_notice: str = ""

    expense_amount: str = ""
    expense_description: str = ""
    expense_category: str = "Other"
    expense_account: str = ""

    income_amount: str = ""
    income_description: str = ""
    income_account: str = ""

    maridian_locked: bool = False
    maridian_cycle_count: str = "0"
    maridian_last_cycle: str = "Never"
    maridian_entries_processed: str = "0"
    maridian_questions: List[QuestionItem] = []
    maridian_themes: List[ThemeItem] = []
    maridian_index_excerpt: str = "No current Maridian index available."
    maridian_notice: str = ""
    maridian_running: bool = False

    olympus_total_pnl: str = "$0.00"
    olympus_total_trades: str = "0"
    olympus_avg_r: str = "0.00"
    olympus_last_trade: str = "No trades yet"
    olympus_cycle_summary: str = "No cycle data yet."
    olympus_recent_trades: List[TradeItem] = []
    olympus_report_excerpt: str = "No Olympus report available."

    audit_items: List[AuditItem] = []
    trace_items: List[TraceItem] = []
    doctor_current_provider: str = "Unknown"
    doctor_preferred_provider: str = "Unknown"
    anthropic_status: str = "Unknown"
    anthropic_model: str = ""
    anthropic_reason: str = ""
    ollama_status: str = "Unknown"
    ollama_model: str = ""
    ollama_reason: str = ""
    doctor_blackbook_reason: str = ""
    doctor_maridian_reason: str = ""
    doctor_olympus_reason: str = ""

    def switch_to_apollo(self):
        self.active_tab = "apollo"

    def switch_to_pantheon(self):
        self.active_tab = "pantheon"

    def show_overview(self):
        self.pantheon_section = "overview"

    def show_blackbook(self):
        self.pantheon_section = "blackbook"

    def show_maridian(self):
        self.pantheon_section = "maridian"

    def show_olympus(self):
        self.pantheon_section = "olympus"

    def show_activity(self):
        self.pantheon_section = "activity"

    def show_doctor(self):
        self.pantheon_section = "doctor"

    def update_input_text(self, value: str):
        self.input_text = value

    def handle_enter_key(self, key: str):
        if key == "Enter":
            return State.send_message
        return None

    def set_expense_amount(self, value: str):
        self.expense_amount = value

    def set_expense_description(self, value: str):
        self.expense_description = value

    def set_expense_category(self, value: str):
        self.expense_category = value

    def set_expense_account(self, value: str):
        self.expense_account = value

    def set_income_amount(self, value: str):
        self.income_amount = value

    def set_income_description(self, value: str):
        self.income_description = value

    def set_income_account(self, value: str):
        self.income_account = value

    def load_dashboard(self):
        return State.refresh_context

    def refresh_context(self):
        self.context_loading = True
        self.context_error = ""
        yield

        try:
            overview = requests.get(f"{APOLLO_API}/pantheon/overview", timeout=10).json()
            blackbook = requests.get(f"{APOLLO_API}/pantheon/blackbook", timeout=10).json()
            maridian = requests.get(f"{APOLLO_API}/pantheon/maridian", timeout=10).json()
            olympus = requests.get(f"{APOLLO_API}/pantheon/olympus", timeout=10).json()
            activity = requests.get(f"{APOLLO_API}/pantheon/activity", timeout=10).json()
            doctor = requests.get(f"{APOLLO_API}/pantheon/doctor", timeout=10).json()

            health = overview.get("health", {})
            self.pantheon_status = health.get("pantheon", "unknown").title()
            self.blackbook_status = health.get("blackbook", "unknown").title()
            self.maridian_status = health.get("maridian", "unknown").title()
            self.olympus_status = health.get("olympus", "unknown").title()
            self.latest_signal = overview.get("latest_signal", "No recent system activity.")
            self.self_model_excerpt = overview.get("vault", {}).get(
                "self_model_excerpt",
                "Self model is waiting for the first Apollo-written insight.",
            )

            self.net_worth = f"${float(blackbook.get('net_worth', 0) or 0):,.2f}"
            self.total_assets = f"${float(blackbook.get('total_assets', 0) or 0):,.2f}"
            self.total_debt = f"${float(blackbook.get('total_debt', 0) or 0):,.2f}"
            self.blackbook_balances = [
                BalanceItem(
                    name=item.get("name", ""),
                    balance=f"${float(item.get('balance', 0) or 0):,.2f}",
                    account_type=item.get("account_type", ""),
                    is_debt=bool(item.get("is_debt")),
                )
                for item in blackbook.get("balances", [])[:8]
            ]
            self.blackbook_transactions = [
                TransactionItem(
                    date=item.get("date", ""),
                    description=_truncate(item.get("description", ""), 48),
                    category=item.get("category", ""),
                    account=item.get("account", ""),
                    amount=f"${float(item.get('amount', 0) or 0):,.2f}",
                    tx_type=item.get("type", ""),
                )
                for item in blackbook.get("recent_transactions", [])[:8]
            ]
            self.blackbook_spending = [
                SpendingItem(
                    category=item.get("category", ""),
                    total=f"${float(item.get('total', 0) or 0):,.2f}",
                    count=str(item.get("count", 0)),
                )
                for item in blackbook.get("spending_month", [])[:6]
            ]
            self.blackbook_accounts = [item.get("name", "") for item in blackbook.get("accounts", [])]
            self.blackbook_notice = blackbook.get("error", "") if not blackbook.get("connected") else ""
            if self.blackbook_accounts and not self.expense_account:
                self.expense_account = self.blackbook_accounts[0]
            if self.blackbook_accounts and not self.income_account:
                self.income_account = self.blackbook_accounts[0]

            self.maridian_locked = bool(maridian.get("locked"))
            self.maridian_cycle_count = str(maridian.get("cycle_count", 0))
            self.maridian_entries_processed = str(maridian.get("entries_processed", 0))
            self.maridian_last_cycle = _format_timestamp(maridian.get("last_cycle"))
            self.maridian_questions = [
                QuestionItem(
                    question=item.get("question", ""),
                    context=_truncate(item.get("context", ""), 90),
                )
                for item in maridian.get("today_questions", [])[:6]
            ]
            self.maridian_themes = [
                ThemeItem(
                    title=item.get("title", ""),
                    preview=_truncate(item.get("preview", ""), 120),
                    updated_at=_format_timestamp(item.get("updated_at")),
                )
                for item in maridian.get("top_themes", [])[:6]
            ]
            self.maridian_index_excerpt = maridian.get("index_excerpt") or "No current Maridian index available."
            self.maridian_notice = maridian.get("error", "") if not maridian.get("connected") else ""

            performance = olympus.get("performance", {}) or {}
            cycle = olympus.get("latest_cycle", {}) or {}
            self.olympus_total_pnl = f"${float(performance.get('total_pnl', 0) or 0):,.2f}"
            self.olympus_total_trades = str(performance.get("total_trades", 0) or 0)
            self.olympus_avg_r = f"{float(performance.get('avg_r_multiple', 0) or 0):.2f}"
            self.olympus_last_trade = _format_timestamp(performance.get("last_trade_at"))
            if olympus.get("connected"):
                self.olympus_cycle_summary = (
                    f"Cycle {cycle.get('cycle_id', 'n/a')} at {_format_timestamp(cycle.get('cycle_timestamp'))} "
                    f"with {cycle.get('scored_count', 0)} scored names."
                )
            else:
                self.olympus_cycle_summary = (
                    olympus.get("error")
                    or f"No Olympus runtime artifacts found at {olympus.get('db_path', 'configured DB path')}."
                )
            self.olympus_recent_trades = [
                TradeItem(
                    symbol=item.get("symbol", ""),
                    direction=item.get("direction", ""),
                    realized_pnl=f"${float(item.get('realized_pnl', 0) or 0):,.2f}",
                    exit_reason=item.get("exit_reason", ""),
                    exit_time=_format_timestamp(item.get("exit_time")),
                )
                for item in olympus.get("recent_trades", [])[:8]
            ]
            self.olympus_report_excerpt = (
                _truncate(olympus.get("report_excerpt", ""), 900)
                or olympus.get("error", "")
                or "No Olympus report available."
            )

            self.audit_items = [
                AuditItem(
                    timestamp=_format_timestamp(item.get("timestamp")),
                    system=item.get("system", ""),
                    action=item.get("action", ""),
                    detail=_truncate(item.get("detail", ""), 120),
                )
                for item in activity.get("audit", [])[:10]
            ]

            providers = doctor.get("providers", {})
            anth = providers.get("anthropic", {})
            ollama = providers.get("ollama", {})
            self.doctor_current_provider = doctor.get("current_provider", "unknown").title()
            self.doctor_preferred_provider = doctor.get("preferred_provider", "unknown").title()
            self.anthropic_status = "Online" if anth.get("available") else "Offline"
            self.anthropic_model = anth.get("model", "")
            self.anthropic_reason = anth.get("reason", "")
            self.ollama_status = "Online" if ollama.get("available") else "Offline"
            self.ollama_model = ollama.get("model", "")
            self.ollama_reason = ollama.get("reason", "")

            subsystems = doctor.get("subsystems", {})
            self.doctor_blackbook_reason = subsystems.get("blackbook", {}).get("reason", "")
            self.doctor_maridian_reason = subsystems.get("maridian", {}).get("reason", "")
            self.doctor_olympus_reason = subsystems.get("olympus", {}).get("reason", "")

            self.trace_items = [
                TraceItem(
                    timestamp=_format_timestamp(item.get("timestamp")),
                    provider=(item.get("provider_used") or "deterministic").title(),
                    message=_truncate(item.get("message", ""), 72),
                    subsystems=", ".join(item.get("subsystems", []) or []) or "none",
                    latency=f"{item.get('latency_ms', 0) or 0} ms",
                    status="Degraded" if item.get("degraded") else ("Grounded" if item.get("grounded") else "Model"),
                )
                for item in doctor.get("recent_traces", [])[:8]
            ]

            self.last_refreshed = datetime.now().strftime("%H:%M:%S")
        except Exception as exc:
            self.context_error = str(exc)
        finally:
            self.context_loading = False

    def send_message(self):
        if not self.input_text.strip():
            return

        user_msg = self.input_text.strip()
        timestamp = _format_timestamp(datetime.now().isoformat())
        self.messages.append(Message(role="user", content=user_msg, timestamp=timestamp))
        self.input_text = ""
        self.is_loading = True
        yield

        try:
            response = requests.post(
                f"{APOLLO_API}/chat",
                json={"message": user_msg, "channel": "ui"},
                timeout=60,
            )
            data = response.json()
            self.messages.append(
                Message(
                    role="apollo",
                    content=data.get("response", "Apollo returned an empty response."),
                    timestamp=_format_timestamp(datetime.now().isoformat()),
                )
            )
        except Exception as exc:
            self.messages.append(
                Message(
                    role="apollo",
                    content=f"Error: {exc}",
                    timestamp=_format_timestamp(datetime.now().isoformat()),
                )
            )
        self.is_loading = False
        yield State.refresh_context

    def clear_chat(self):
        self.messages = []
        try:
            requests.post(
                f"{APOLLO_API}/chat",
                json={"message": "", "reset_history": True},
                timeout=5,
            )
        except Exception:
            pass
        return State.refresh_context

    def submit_expense(self):
        self.blackbook_notice = ""
        try:
            requests.post(
                f"{APOLLO_API}/pantheon/blackbook/expense",
                json={
                    "amount": float(self.expense_amount or "0"),
                    "description": self.expense_description,
                    "category": self.expense_category,
                    "account": self.expense_account,
                },
                timeout=15,
            ).raise_for_status()
            self.blackbook_notice = "Expense recorded."
            self.expense_amount = ""
            self.expense_description = ""
        except Exception as exc:
            self.blackbook_notice = f"Expense failed: {exc}"
        return State.refresh_context

    def submit_income(self):
        self.blackbook_notice = ""
        try:
            requests.post(
                f"{APOLLO_API}/pantheon/blackbook/income",
                json={
                    "amount": float(self.income_amount or "0"),
                    "description": self.income_description,
                    "account": self.income_account,
                },
                timeout=15,
            ).raise_for_status()
            self.blackbook_notice = "Income recorded."
            self.income_amount = ""
            self.income_description = ""
        except Exception as exc:
            self.blackbook_notice = f"Income failed: {exc}"
        return State.refresh_context

    def run_maridian_cycle(self):
        self.maridian_notice = ""
        self.maridian_running = True
        yield
        try:
            requests.post(f"{APOLLO_API}/pantheon/maridian/run-cycle", timeout=320).raise_for_status()
            self.maridian_notice = "Maridian cycle completed."
        except Exception as exc:
            self.maridian_notice = f"Cycle failed: {exc}"
        self.maridian_running = False
        yield State.refresh_context
