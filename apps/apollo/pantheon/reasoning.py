import json
import re
from uuid import uuid4

from core.audit import log
from pantheon.connectors import PantheonConnectors
from pantheon.models import PantheonResult
from pantheon.runtime import LocalModelRuntime

SYSTEM_PROMPT = """You are Pantheon, the operating system behind Apollo.
Use available system context to answer clearly and concretely.
If a requested system is unavailable, say so plainly.
Never pretend an action succeeded if it did not."""


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
        log(f"Reasoning request [{channel}]", detail=normalized[:120], system="PANTHEON")

        approval_scope = self._approval_phrase(lower)
        explicit_write = self._is_write_request(lower)

        if "olympus" in lower or "apex" in lower:
            tools_used.append("get_olympus_status")
            result = self.connectors.olympus_status()
            if result.get("success"):
                summary = result["summary"]
                sources.append({"system": "olympus", "type": "status", "last_updated": summary.get("last_updated")})
                stale = " Data may be stale." if summary.get("is_stale") else ""
                positions = ", ".join([p.get("symbol", "?") for p in summary.get("open_positions", [])]) or "None"
                response = (
                    f"Olympus reports daily PnL {summary.get('daily_pnl')}, total PnL {summary.get('total_pnl')}, "
                    f"{summary.get('position_count')} open positions ({positions}), alerts: "
                    f"{'; '.join(summary.get('alerts', [])) or 'none'}.{stale}"
                )
                return PantheonResult(response=response, tools_used=tools_used, sources=sources, audit_id=audit_id)
            return PantheonResult(
                response=f"Olympus is unavailable right now: {result.get('error', 'unknown error')}",
                tools_used=tools_used,
                audit_id=audit_id,
            )

        if "spending" in lower or "spent this" in lower:
            period = "month"
            if "week" in lower:
                period = "week"
            elif "year" in lower:
                period = "year"
            tools_used.append("get_spending_summary")
            result = self.connectors.spending_summary(period)
            if result.get("success"):
                data = result.get("data", [])
                sources.append({"system": "black_book", "type": "spending_summary", "period": period})
                if not data:
                    return PantheonResult(
                        response=f"I checked Black Book and there are no {period} expenses recorded yet.",
                        tools_used=tools_used,
                        sources=sources,
                        audit_id=audit_id,
                    )
                summary = ", ".join([f"{row['category']}: ${row['total']}" for row in data[:5]])
                return PantheonResult(
                    response=f"Your {period} spending summary from Black Book is {summary}.",
                    tools_used=tools_used,
                    sources=sources,
                    audit_id=audit_id,
                )

        if "balance" in lower or "account" in lower and "what" in lower:
            tools_used.append("get_account_balances")
            result = self.connectors.account_balances()
            if result.get("success"):
                data = result.get("data", [])
                sources.append({"system": "black_book", "type": "account_balances"})
                summary = ", ".join([f"{row['name']}: ${row['balance']}" for row in data])
                return PantheonResult(
                    response=f"Current Black Book balances are {summary}.",
                    tools_used=tools_used,
                    sources=sources,
                    audit_id=audit_id,
                )

        if "run my journal cycle" in lower or "run meridian" in lower or "run maridian" in lower:
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
                response=f"I tried to run the Maridian cycle, but it failed: {result.get('error', 'unknown error')}",
                tools_used=tools_used,
                actions_taken=actions_taken,
                audit_id=audit_id,
            )

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

        if "search maridian" in lower or "what did i journal" in lower or "search meridian" in lower:
            query = normalized.split("?", 1)[0]
            for prefix in ("search maridian", "search meridian", "what did i journal about"):
                if query.lower().startswith(prefix):
                    query = normalized[len(prefix):].strip(" :?")
                    break
            query = query or normalized
            tools_used.append("search_meridian")
            results = self.connectors.search_meridian(query, n_results=3)
            if results:
                sources.extend(
                    [{"system": "maridian", "type": "search_hit", "path": item.get("path")} for item in results]
                )
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
        generated = None
        if self.runtime.available():
            generated = self.runtime.generate(SYSTEM_PROMPT, context)
        if generated:
            return PantheonResult(
                response=generated,
                sources=sources,
                tools_used=tools_used + (["local_model"] if "local_model" not in tools_used else []),
                actions_taken=actions_taken,
                actions_proposed=actions_proposed,
                audit_id=audit_id,
            )

        fallback = self._fallback_response(normalized)
        return PantheonResult(
            response=fallback,
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
            "write_request": explicit_write,
        }
        return json.dumps(payload, ensure_ascii=True, default=str)

    def _fallback_response(self, message: str) -> str:
        return (
            "Pantheon is connected, but the local model is unavailable right now. "
            f"I received: '{message}'. Once Ollama is running, Apollo will answer through Pantheon."
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
        category_match = re.search(r"\b(food|health|transport|entertainment|shopping|bills|other)\b", lower)
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
