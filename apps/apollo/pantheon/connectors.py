from core.memory import (
    get_active_patterns,
    get_approval_rule,
    get_decisions,
    get_recent_conversations,
    log_decision,
    set_approval_rule,
)


class PantheonConnectors:
    def recent_memory(self, limit: int = 8) -> list[dict]:
        return get_recent_conversations(limit=limit)

    def decisions(self, limit: int = 8) -> list[dict]:
        return get_decisions(limit=limit)

    def patterns(self) -> list[dict]:
        return get_active_patterns()

    def spending_summary(self, period: str) -> dict:
        from connectors.black_book import get_spending_summary

        return get_spending_summary(period)

    def account_balances(self) -> dict:
        from connectors.black_book import get_account_balances

        return get_account_balances()

    def olympus_status(self) -> dict:
        from connectors.olympus import get_pnl_summary

        return get_pnl_summary()

    def search_meridian(self, query: str, n_results: int = 5) -> list[dict]:
        from search.retriever import search_meridian

        return search_meridian(query, n_results=n_results)

    def search_decisions(self, query: str, n_results: int = 5) -> list[dict]:
        from search.retriever import search_decisions

        return search_decisions(query, n_results=n_results)

    def write_journal(self, content: str) -> dict:
        from connectors.meridian import append_to_daily_note

        return append_to_daily_note(content)

    def queue_prompt(self, prompt: str) -> dict:
        from connectors.meridian import queue_meridian_prompt

        return queue_meridian_prompt(prompt)

    def run_meridian_cycle(self) -> dict:
        from connectors.meridian import trigger_meridian_cycle

        return trigger_meridian_cycle()

    def record_decision(self, decision: str, reasoning: str | None, domain: str | None) -> None:
        log_decision(decision=decision, reasoning=reasoning, domain=domain or "general")

    def record_expense(self, amount: float, description: str, category: str, account: str, date_str: str | None) -> dict:
        from connectors.black_book import add_expense

        return add_expense(amount, description, category, account, date_str)

    def record_income(self, amount: float, description: str, account: str, date_str: str | None) -> dict:
        from connectors.black_book import add_income

        return add_income(amount, description, account, date_str)

    def approval_rule(self, action_type: str) -> dict | None:
        return get_approval_rule(action_type)

    def save_approval_rule(self, action_type: str, scope: str) -> None:
        set_approval_rule(action_type, scope)
