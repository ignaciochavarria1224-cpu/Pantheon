import json
import re
from uuid import uuid4

from core.audit import log
from pantheon.connectors import PantheonConnectors
from pantheon.models import PantheonResult
from pantheon.runtime import LocalModelRuntime

SYSTEM_PROMPT = """You are Pantheon, the operating system behind Apollo.
Use the structured subsystem context to answer clearly and concretely.
Do not invent data. If a subsystem is unavailable, say so plainly."""


class PantheonReasoner:
    def __init__(self):
        self.runtime = LocalModelRuntime()
        self.connectors = PantheonConnectors()

    def reason(self, message: str, conversation_history: list | None = None, channel: str = "ui") -> PantheonResult:
        audit_id = uuid4().hex[:12]
        normalized = (message or "").strip()
        tools_used: list[str] = []
        actions_taken: list[str] = []
        actions_proposed: list[str] = []
        sources: list[dict] = []

        if not normalized:
            return PantheonResult(response="Apollo is ready.", audit_id=audit_id)

        lower = normalized.lower()
        approval_scope = self._approval_phrase(lower)
        explicit_write = self._is_write_request(lower)
        log(f"Reasoning request [{channel}]", detail=normalized[:120], system="PANTHEON")

        if any(token in lower for token in ("olympus", "apex", "trade", "pnl", "ranking cycle")):
            tools_used.append("olympus_snapshot")
            result = self.connectors.olympus_status()
            if result.get("success"):
                snapshot = result.get("snapshot") or {}
                perf = snapshot.get("performance") or {}
                cycle = snapshot.get("latest_cycle") or {}
                trades = snapshot.get("recent_trades") or []
                sources.append({"system": "olympus", "type": "sqlite", "path": snapshot.get("db_path")})
                if snapshot.get("report_updated_at"):
                    sources.append({"system": "olympus", "type": "report", "updated_at": snapshot.get("report_updated_at")})
                latest_trade = ""
                if trades:
                    top = trades[0]
                    latest_trade = (
                        f" Most recent trade: {top.get('symbol')} {top.get('direction')} "
                        f"{top.get('realized_pnl')} on {top.get('exit_time')}."
                    )
                response = (
                    f"Olympus shows {perf.get('total_trades', 0)} recorded trades, total PnL "
                    f"{perf.get('total_pnl', 0)}, average R {perf.get('avg_r_multiple', 0)}, and the latest ranking cycle at "
                    f"{cycle.get('cycle_timestamp', 'unknown time')} with {cycle.get('scored_count', 0)} scored names."
                    f"{latest_trade}"
                )
                return PantheonResult(response=response, tools_used=tools_used, sources=sources, audit_id=audit_id)
            return PantheonResult(
                response=f"Olympus is unavailable right now: {result.get('error', 'unknown error')}",
                tools_used=tools_used,
                audit_id=audit_id,
            )

        if any(token in lower for token in ("spending", "spent this", "expenses")):
            period = "month"
            if "week" in lower:
                period = "week"
            elif "year" in lower:
                period = "year"
            tools_used.append("blackbook_spending_summary")
            result = self.connectors.spending_summary(period)
            data = result.get("data", []) if result.get("success") else []
            sources.append({"system": "blackbook", "type": "spending_summary", "period": period})
            if not data:
                return PantheonResult(
                    response=f"I checked BlackBook and there are no {period} expenses recorded yet.",
                    tools_used=tools_used,
                    sources=sources,
                    audit_id=audit_id,
                )
            summary = ", ".join(f"{row['category']}: ${row['total']}" for row in data[:5])
            return PantheonResult(
                response=f"Your {period} spending summary from BlackBook is {summary}.",
                tools_used=tools_used,
                sources=sources,
                audit_id=audit_id,
            )

        if "balance" in lower or ("account" in lower and "what" in lower):
            tools_used.append("blackbook_account_balances")
            result = self.connectors.account_balances()
            data = result.get("data", []) if result.get("success") else []
            sources.append({"system": "blackbook", "type": "account_balances"})
            if not data:
                return PantheonResult(
                    response="BlackBook is connected, but I couldn't read any account balances right now.",
                    tools_used=tools_used,
                    sources=sources,
                    audit_id=audit_id,
                )

            match = self._match_account(lower, data)
            if match:
                response = f"Your current {match['name']} balance in BlackBook is ${float(match['balance']):,.2f}."
            else:
                summary = ", ".join(f"{row['name']}: ${float(row['balance']):,.2f}" for row in data)
                response = f"Current BlackBook balances are {summary}."
            return PantheonResult(
                response=response,
                tools_used=tools_used,
                sources=sources,
                audit_id=audit_id,
            )

        if any(token in lower for token in ("run my journal cycle", "run meridian", "run maridian")):
            if not self._write_allowed("trigger_meridian_cycle", approval_scope):
                actions_proposed.append("trigger_meridian_cycle")
                return PantheonResult(
                    response="I can run the Maridian cycle, but I need your approval first.",
                    actions_proposed=actions_proposed,
                    audit_id=audit_id,
                )
            tools_used.append("trigger_meridian_cycle")
            actions_taken.append("trigger_meridian_cycle")
            result = self.connectors.run_meridian_cycle()
            if result.get("success"):
                return PantheonResult(
                    response="Maridian cycle triggered successfully.",
                    tools_used=tools_used,
                    actions_taken=actions_taken,
                    audit_id=audit_id,
                )
            return PantheonResult(
                response=f"I tried to run the Maridian cycle, but it failed: {result.get('error') or result.get('stderr') or 'unknown error'}",
                tools_used=tools_used,
                actions_taken=actions_taken,
                audit_id=audit_id,
            )

        if any(token in lower for token in ("maridian", "meridian questions", "today's questions", "journal cycle status")):
            tools_used.append("maridian_snapshot")
            snapshot = self.connectors.maridian_snapshot()
            sources.append({"system": "maridian", "type": "state", "last_cycle": snapshot.get("last_cycle")})
            question_count = len(snapshot.get("today_questions", []))
            response = (
                f"Maridian is {'locked' if snapshot.get('locked') else 'idle'}, on cycle {snapshot.get('cycle_count', 0)}, "
                f"with {question_count} questions generated for today. Last cycle: {snapshot.get('last_cycle') or 'not recorded'}."
            )
            return PantheonResult(response=response, tools_used=tools_used, sources=sources, audit_id=audit_id)

        journal_content = self._extract_after_prefix(normalized, ["journal:", "log this:", "note:"])
        if journal_content:
            if not self._write_allowed("log_journal_entry", approval_scope):
                actions_proposed.append("log_journal_entry")
                return PantheonResult(
                    response="I can write that to Maridian, but I need your approval first.",
                    actions_proposed=actions_proposed,
                    audit_id=audit_id,
                )
            tools_used.append("log_journal_entry")
            actions_taken.append("log_journal_entry")
            result = self.connectors.write_journal(journal_content)
            if result.get("success"):
                sources.append({"system": "maridian", "type": "daily_note", "path": result.get("path")})
                return PantheonResult(
                    response="Logged that to today's Maridian note.",
                    tools_used=tools_used,
                    actions_taken=actions_taken,
                    sources=sources,
                    audit_id=audit_id,
                )

        if lower.startswith("decision:"):
            decision_text = normalized.split(":", 1)[1].strip()
            if not self._write_allowed("log_decision", approval_scope):
                actions_proposed.append("log_decision")
                return PantheonResult(
                    response="I can log that decision, but I need your approval first.",
                    actions_proposed=actions_proposed,
                    audit_id=audit_id,
                )
            tools_used.append("log_decision")
            actions_taken.append("log_decision")
            decision, reasoning = self._split_decision_reasoning(decision_text)
            self.connectors.record_decision(decision, reasoning, "general")
            return PantheonResult(
                response=f"Logged your decision: {decision}.",
                tools_used=tools_used,
                actions_taken=actions_taken,
                audit_id=audit_id,
            )

        expense_match = self._parse_expense(normalized)
        if expense_match:
            if not self._write_allowed("add_expense", approval_scope):
                actions_proposed.append("add_expense")
                return PantheonResult(
                    response="I can log that expense, but I need your approval first.",
                    actions_proposed=actions_proposed,
                    audit_id=audit_id,
                )
            tools_used.append("add_expense")
            actions_taken.append("add_expense")
            result = self.connectors.record_expense(**expense_match)
            if result.get("success"):
                return PantheonResult(
                    response=(
                        f"Recorded ${expense_match['amount']:.2f} for {expense_match['description']} "
                        f"under {expense_match['category']} from {expense_match['account']}."
                    ),
                    tools_used=tools_used,
                    actions_taken=actions_taken,
                    audit_id=audit_id,
                )
            return PantheonResult(
                response=f"I couldn't record that expense: {result.get('error', 'unknown error')}",
                tools_used=tools_used,
                actions_taken=actions_taken,
                audit_id=audit_id,
            )

        if any(token in lower for token in ("search maridian", "search meridian", "what did i journal")):
            query = normalized.split("?", 1)[0]
            for prefix in ("search maridian", "search meridian", "what did i journal about"):
                if query.lower().startswith(prefix):
                    query = normalized[len(prefix):].strip(" :?")
                    break
            query = query or normalized
            tools_used.append("search_meridian")
            results = self.connectors.search_meridian(query, n_results=3)
            if results:
                sources.extend({"system": "maridian", "type": "search_hit", "path": item.get("path")} for item in results)
                preview = " ".join(
                    f"{item['source']}: {item['content'][:140].strip()}..." for item in results[:3]
                )
                return PantheonResult(
                    response=f"I found relevant Maridian context for '{query}'. {preview}",
                    tools_used=tools_used,
                    sources=sources,
                    audit_id=audit_id,
                )
            return PantheonResult(
                response=f"I couldn't find anything relevant in Maridian for '{query}'.",
                tools_used=tools_used,
                audit_id=audit_id,
            )

        context = self._build_context(normalized, conversation_history or [], explicit_write)
        generated = self.runtime.generate(SYSTEM_PROMPT, context) if self.runtime.available() else None
        if generated:
            return PantheonResult(
                response=generated,
                sources=sources,
                tools_used=tools_used + (["local_model"] if "local_model" not in tools_used else []),
                actions_taken=actions_taken,
                actions_proposed=actions_proposed,
                audit_id=audit_id,
            )

        return PantheonResult(
            response=self._fallback_response(normalized),
            sources=sources,
            tools_used=tools_used,
            actions_taken=actions_taken,
            actions_proposed=actions_proposed,
            audit_id=audit_id,
        )

    def _build_context(self, message: str, history: list, explicit_write: bool) -> str:
        payload = {
            "message": message,
            "recent_history": history[-6:],
            "recent_memory": self.connectors.recent_memory(limit=4),
            "recent_decisions": self.connectors.decisions(limit=3),
            "active_patterns": self.connectors.patterns()[:3],
            "blackbook": self.connectors.blackbook_snapshot(),
            "maridian": self.connectors.maridian_snapshot(),
            "olympus": self.connectors.olympus_snapshot(),
            "write_request": explicit_write,
        }
        return json.dumps(payload, ensure_ascii=True, default=str)

    def _fallback_response(self, message: str) -> str:
        return (
            "Pantheon is connected, but the local model is unavailable right now. "
            f"I received: '{message}'. The subsystem dashboards and factual reads are still live."
        )

    def _approval_phrase(self, lower: str) -> str | None:
        if "always allow" in lower:
            return "permanent"
        if "just this once" in lower:
            return "session"
        return None

    def _write_allowed(self, action_type: str, approval_scope: str | None) -> bool:
        if approval_scope:
            self.connectors.save_approval_rule(action_type, approval_scope)
            return True
        return self.connectors.approval_rule(action_type) is not None

    def _is_write_request(self, lower: str) -> bool:
        return any(
            token in lower
            for token in ("log ", "record ", "spent ", "income ", "journal:", "decision:", "run meridian", "run maridian")
        )

    def _extract_after_prefix(self, message: str, prefixes: list[str]) -> str | None:
        lower = message.lower()
        for prefix in prefixes:
            if lower.startswith(prefix):
                return message[len(prefix):].strip()
        return None

    def _parse_expense(self, message: str) -> dict | None:
        lower = message.lower()
        if "spent" not in lower and "log $" not in lower:
            return None
        amount_match = re.search(r"\$?(\d+(?:\.\d{1,2})?)", message)
        account_match = re.search(r"from ([a-zA-Z ]+)", lower)
        category_match = re.search(r"\b(food|health|transport|entertainment|shopping|bills|other|gas)\b", lower)
        if not amount_match or not account_match:
            return None
        amount = float(amount_match.group(1))
        account = account_match.group(1).strip()
        category = category_match.group(1).title() if category_match else "Other"
        description = message
        description = re.sub(r"(?i)\bspent\b", "", description)
        description = re.sub(r"\$?\d+(?:\.\d{1,2})?", "", description, count=1)
        description = re.sub(r"(?i)\bfrom\b.*$", "", description)
        description = description.replace("at", "", 1).strip(" ,.-")
        if not description:
            description = "Expense"
        return {
            "amount": amount,
            "description": description,
            "category": category,
            "account": account,
            "date_str": None,
        }

    def _split_decision_reasoning(self, text: str) -> tuple[str, str | None]:
        for delimiter in (" because ", " since ", " due to "):
            if delimiter in text.lower():
                idx = text.lower().find(delimiter)
                decision = text[:idx].strip(" .")
                reasoning = text[idx + len(delimiter):].strip(" .")
                return decision, reasoning
        return text.strip(" ."), None

    def _match_account(self, lower: str, balances: list[dict]) -> dict | None:
        for item in balances:
            name = str(item.get("name") or "")
            compact = name.lower().replace(" ", "")
            if name.lower() in lower or compact in lower.replace(" ", ""):
                return item
        if "checking" in lower:
            return next((item for item in balances if "checking" in str(item.get("name", "")).lower()), None)
        if "savings" in lower:
            return next((item for item in balances if "savings" in str(item.get("name", "")).lower()), None)
        return None
