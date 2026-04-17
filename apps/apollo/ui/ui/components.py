from __future__ import annotations

import reflex as rx

from .state import AuditItem, BalanceItem, Message, QuestionItem, SpendingItem, State, ThemeItem, TraceItem, TradeItem, TransactionItem


BG = "#f5efe2"
SURFACE = "rgba(255, 251, 244, 0.92)"
SURFACE_SOFT = "rgba(252, 247, 238, 0.88)"
SURFACE_STRONG = "rgba(255, 254, 250, 0.98)"
BORDER = "rgba(137, 104, 44, 0.18)"
BORDER_STRONG = "rgba(137, 104, 44, 0.34)"
TEXT = "#221b14"
TEXT_SOFT = "rgba(34, 27, 20, 0.82)"
TEXT_MUTED = "rgba(34, 27, 20, 0.55)"
ACCENT = "#8c6a2f"
GRAPHITE = "#2c241d"
USER_TINT = "rgba(142, 118, 83, 0.12)"
APOLLO_TINT = "rgba(255, 255, 255, 0.72)"


def ambient_background() -> rx.Component:
    return rx.box(
        rx.box(
            position="absolute",
            inset="0",
            background=(
                "radial-gradient(circle at 50% 0%, rgba(232, 218, 190, 0.62), transparent 42%),"
                "radial-gradient(circle at 12% 18%, rgba(255, 255, 255, 0.58), transparent 24%),"
                "radial-gradient(circle at 86% 16%, rgba(216, 191, 139, 0.24), transparent 22%),"
                "linear-gradient(180deg, #fbf7ef 0%, #f4ecde 52%, #efe5d6 100%)"
            ),
        ),
        position="absolute",
        inset="0",
        overflow="hidden",
    )


def shell_frame(*children, **props) -> rx.Component:
    props.setdefault("background", SURFACE)
    return rx.box(
        *children,
        border=f"1px solid {BORDER}",
        box_shadow="0 24px 90px rgba(68, 45, 10, 0.08)",
        border_radius="28px",
        backdrop_filter="blur(18px)",
        **props,
    )


def eyebrow(text: str) -> rx.Component:
    return rx.text(
        text,
        font_size="11px",
        letter_spacing="0.22em",
        text_transform="uppercase",
        color=TEXT_MUTED,
        font_family="'IBM Plex Mono', 'Consolas', monospace",
    )


def nav_button(label: str, active, action) -> rx.Component:
    return rx.button(
        label,
        on_click=action,
        height="40px",
        padding="0 16px",
        border_radius="999px",
        border=rx.cond(active, "none", f"1px solid {BORDER}"),
        background=rx.cond(active, "linear-gradient(135deg, #9b7742 0%, #c3a46f 100%)", "rgba(255, 252, 247, 0.78)"),
        color=rx.cond(active, "#fffaf2", GRAPHITE),
        font_size="13px",
        font_weight="600",
        cursor="pointer",
    )


def top_nav() -> rx.Component:
    return rx.hstack(
        rx.vstack(
            eyebrow("Voice and operating shell"),
            rx.text("Apollo", color=GRAPHITE, font_size="28px", font_weight="600", letter_spacing="-0.05em"),
            rx.text("Apollo is the interface. Pantheon runs the system behind it.", color=TEXT_MUTED, font_size="14px"),
            spacing="1",
            align="start",
        ),
        rx.spacer(),
        rx.hstack(
            nav_button("Apollo", State.active_tab == "apollo", State.switch_to_apollo),
            nav_button("Pantheon", State.active_tab == "pantheon", State.switch_to_pantheon),
            spacing="3",
        ),
        width="100%",
        align="center",
    )


def status_chip(label: str, value) -> rx.Component:
    return rx.hstack(
        rx.text(label, color=TEXT_MUTED, font_size="11px", text_transform="uppercase", letter_spacing="0.12em"),
        rx.text(value, color=ACCENT, font_size="12px", font_weight="600"),
        border=f"1px solid {BORDER}",
        border_radius="999px",
        padding="8px 12px",
        background=SURFACE_SOFT,
        spacing="2",
    )


def status_ribbon() -> rx.Component:
    return rx.hstack(
        status_chip("Pantheon", State.pantheon_status),
        status_chip("BlackBook", State.blackbook_status),
        status_chip("Maridian", State.maridian_status),
        status_chip("Olympus", State.olympus_status),
        width="100%",
        wrap="wrap",
        spacing="3",
    )


def transcript_message(message: Message) -> rx.Component:
    user = message.role == "user"
    return rx.vstack(
        rx.hstack(
            rx.text(rx.cond(user, "You", "Apollo"), color=ACCENT, font_size="11px", letter_spacing="0.16em", text_transform="uppercase"),
            rx.spacer(),
            rx.text(message.timestamp, color=TEXT_MUTED, font_size="11px"),
            width="100%",
        ),
        rx.text(message.content, color=TEXT_SOFT, font_size="16px", line_height="1.85", white_space="pre-wrap"),
        background=rx.cond(user, USER_TINT, APOLLO_TINT),
        border=rx.cond(user, f"1px solid {BORDER_STRONG}", "1px solid rgba(255,255,255,0.72)"),
        border_radius="22px",
        padding="18px 20px",
        width="100%",
        align="start",
        spacing="2",
    )


def composer() -> rx.Component:
    return shell_frame(
        rx.vstack(
            rx.text_area(
                value=State.input_text,
                on_change=State.update_input_text,
                on_key_down=State.handle_enter_key,
                placeholder="Ask Apollo to think, log, summarize, or act.",
                width="100%",
                min_height="180px",
                rows="7",
                resize="vertical",
                background="rgba(255, 252, 247, 0.96)",
                padding="22px 20px",
                color=GRAPHITE,
                font_size="17px",
                line_height="1.85",
                border=f"1px solid {BORDER_STRONG}",
            ),
            rx.hstack(
                rx.text("Enter sends. Shift+Enter adds a line.", color=TEXT_MUTED, font_size="12px"),
                rx.spacer(),
                nav_button("Clear", False, State.clear_chat),
                nav_button(rx.cond(State.is_loading, "Thinking...", "Transmit"), True, State.send_message),
                width="100%",
            ),
            spacing="4",
            width="100%",
        ),
        padding="18px",
    )


def metric_card(label: str, value, detail) -> rx.Component:
    return shell_frame(
        rx.vstack(
            eyebrow(label),
            rx.text(value, color=GRAPHITE, font_size="24px", font_weight="600"),
            rx.text(detail, color=TEXT_MUTED, font_size="13px", line_height="1.6"),
            width="100%",
            spacing="1",
            align="start",
        ),
        padding="18px",
        background=SURFACE_STRONG,
    )


def list_row(title, meta, detail) -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.text(title, color=GRAPHITE, font_size="14px", font_weight="600"),
            rx.spacer(),
            rx.text(meta, color=TEXT_MUTED, font_size="11px"),
            width="100%",
        ),
        rx.text(detail, color=TEXT_SOFT, font_size="13px", line_height="1.7"),
        width="100%",
        spacing="1",
        align="start",
        padding_y="10px",
        border_bottom=f"1px solid {BORDER}",
    )


def section(title: str, subtitle: str, body: rx.Component) -> rx.Component:
    return shell_frame(
        rx.vstack(
            eyebrow(subtitle),
            rx.text(title, color=GRAPHITE, font_size="19px", font_weight="600"),
            body,
            width="100%",
            spacing="4",
            align="start",
        ),
        padding="22px",
    )


def apollo_tab() -> rx.Component:
    return rx.vstack(
        status_ribbon(),
        shell_frame(
            rx.vstack(
                eyebrow("Conversation"),
                rx.text("Apollo", color=GRAPHITE, font_size="22px", font_weight="600"),
                rx.text(State.latest_signal, color=TEXT_MUTED, font_size="14px"),
                rx.cond(
                    State.messages.length() > 0,
                    rx.vstack(rx.foreach(State.messages, transcript_message), width="100%", spacing="4"),
                    rx.text(
                        "Apollo is ready. Use chat for questions, quick commands, and natural conversation. Pantheon runs the system behind the answers.",
                        color=TEXT_MUTED,
                        font_size="16px",
                        line_height="1.8",
                    ),
                ),
                width="100%",
                spacing="4",
                align="start",
            ),
            padding="22px",
        ),
        composer(),
        width="100%",
        spacing="5",
        align="stretch",
    )


def pantheon_subnav() -> rx.Component:
    return rx.hstack(
        nav_button("Overview", State.pantheon_section == "overview", State.show_overview),
        nav_button("BlackBook", State.pantheon_section == "blackbook", State.show_blackbook),
        nav_button("Maridian", State.pantheon_section == "maridian", State.show_maridian),
        nav_button("Olympus", State.pantheon_section == "olympus", State.show_olympus),
        nav_button("Activity", State.pantheon_section == "activity", State.show_activity),
        nav_button("Doctor", State.pantheon_section == "doctor", State.show_doctor),
        width="100%",
        wrap="wrap",
        spacing="3",
    )


def balance_row(item: BalanceItem) -> rx.Component:
    return list_row(item.name, item.account_type, item.balance)


def transaction_row(item: TransactionItem) -> rx.Component:
    return list_row(item.description, f"{item.date} / {item.account}", f"{item.category} - {item.amount} ({item.tx_type})")


def spending_row(item: SpendingItem) -> rx.Component:
    return list_row(item.category, f"{item.count} tx", item.total)


def theme_row(item: ThemeItem) -> rx.Component:
    return list_row(item.title, item.updated_at, item.preview)


def question_row(item: QuestionItem) -> rx.Component:
    return list_row("Question", "", rx.cond(item.context != "", f"{item.question} — {item.context}", item.question))


def trade_row(item: TradeItem) -> rx.Component:
    return list_row(item.symbol, f"{item.direction} / {item.exit_time}", f"{item.realized_pnl} via {item.exit_reason}")


def audit_row(item: AuditItem) -> rx.Component:
    return list_row(
        rx.cond(item.system != "", item.system, "SYSTEM"),
        item.timestamp,
        rx.cond(item.detail != "", item.action + " - " + item.detail, item.action),
    )


def trace_row(item: TraceItem) -> rx.Component:
    return list_row(
        item.provider,
        f"{item.timestamp} / {item.status} / {item.latency}",
        f"{item.message} | subsystems: {item.subsystems}",
    )


def option(value: str) -> rx.Component:
    return rx.el.option(value, value=value)


def blackbook_form() -> rx.Component:
    return rx.vstack(
        rx.text(State.blackbook_notice, color=ACCENT, font_size="13px"),
        rx.flex(
            shell_frame(
                rx.vstack(
                    eyebrow("Quick expense"),
                    rx.input(placeholder="Amount", value=State.expense_amount, on_change=State.set_expense_amount),
                    rx.input(placeholder="Description", value=State.expense_description, on_change=State.set_expense_description),
                    rx.input(placeholder="Category", value=State.expense_category, on_change=State.set_expense_category),
                    rx.el.select(
                        rx.foreach(State.blackbook_accounts, option),
                        value=State.expense_account,
                        on_change=State.set_expense_account,
                    ),
                    nav_button("Add Expense", True, State.submit_expense),
                    width="100%",
                    spacing="3",
                    align="start",
                ),
                padding="18px",
            ),
            shell_frame(
                rx.vstack(
                    eyebrow("Quick income"),
                    rx.input(placeholder="Amount", value=State.income_amount, on_change=State.set_income_amount),
                    rx.input(placeholder="Description", value=State.income_description, on_change=State.set_income_description),
                    rx.el.select(
                        rx.foreach(State.blackbook_accounts, option),
                        value=State.income_account,
                        on_change=State.set_income_account,
                    ),
                    nav_button("Add Income", True, State.submit_income),
                    width="100%",
                    spacing="3",
                    align="start",
                ),
                padding="18px",
            ),
            wrap="wrap",
            gap="18px",
            width="100%",
        ),
        width="100%",
        spacing="4",
    )


def overview_panel() -> rx.Component:
    return rx.flex(
        section(
            "System Pulse",
            "Overview",
            rx.vstack(
                status_ribbon(),
                rx.text(State.latest_signal, color=TEXT_SOFT, font_size="14px"),
                rx.text(State.self_model_excerpt, color=TEXT_MUTED, font_size="13px", line_height="1.8"),
                width="100%",
                spacing="4",
            ),
        ),
        section(
            "Financial Core",
            "BlackBook",
            rx.flex(
                metric_card("Net Worth", State.net_worth, "Live from BlackBook's shared balance logic."),
                metric_card("Assets", State.total_assets, "Current assets under BlackBook."),
                metric_card("Debt", State.total_debt, "Current debts under BlackBook."),
                wrap="wrap",
                gap="16px",
                width="100%",
            ),
        ),
        section(
            "Reflection Engine",
            "Maridian",
            rx.flex(
                metric_card("Cycle", State.maridian_cycle_count, "Current Maridian cycle count."),
                metric_card("Entries", State.maridian_entries_processed, "Entries processed by Maridian."),
                metric_card("Last Cycle", State.maridian_last_cycle, "Most recent recorded cycle run."),
                wrap="wrap",
                gap="16px",
                width="100%",
            ),
        ),
        section(
            "Trading Runtime",
            "Olympus",
            rx.flex(
                metric_card("Total PnL", State.olympus_total_pnl, "Read-only Olympus performance summary."),
                metric_card("Trades", State.olympus_total_trades, "Completed trades recorded in Olympus."),
                metric_card("Avg R", State.olympus_avg_r, "Average R multiple across recorded trades."),
                wrap="wrap",
                gap="16px",
                width="100%",
            ),
        ),
        wrap="wrap",
        gap="20px",
        width="100%",
    )


def blackbook_panel() -> rx.Component:
    return rx.flex(
        section(
            "Balances",
            "BlackBook",
            rx.box(rx.foreach(State.blackbook_balances, balance_row), width="100%"),
        ),
        section(
            "Recent Transactions",
            "Ledger",
            rx.box(rx.foreach(State.blackbook_transactions, transaction_row), width="100%"),
        ),
        section(
            "Spending This Month",
            "Summary",
            rx.box(rx.foreach(State.blackbook_spending, spending_row), width="100%"),
        ),
        section("Quick Actions", "Write", blackbook_form()),
        wrap="wrap",
        gap="20px",
        width="100%",
    )


def maridian_panel() -> rx.Component:
    return rx.flex(
        section(
            "Cycle Status",
            "Maridian",
            rx.vstack(
                metric_card("Status", rx.cond(State.maridian_locked, "Locked", "Idle"), "Real lock-state from Maridian."),
                metric_card("Last Cycle", State.maridian_last_cycle, "Most recent Maridian cycle."),
                rx.text(State.maridian_notice, color=ACCENT, font_size="13px"),
                nav_button(rx.cond(State.maridian_running, "Running...", "Run Cycle"), True, State.run_maridian_cycle),
                width="100%",
                spacing="4",
            ),
        ),
        section(
            "Today's Questions",
            "Adaptive prompts",
            rx.box(rx.foreach(State.maridian_questions, question_row), width="100%"),
        ),
        section(
            "Top Themes",
            "Synced context",
            rx.box(rx.foreach(State.maridian_themes, theme_row), width="100%"),
        ),
        section(
            "Index Excerpt",
            "Context",
            rx.text(State.maridian_index_excerpt, color=TEXT_SOFT, font_size="13px", line_height="1.8", white_space="pre-wrap"),
        ),
        wrap="wrap",
        gap="20px",
        width="100%",
    )


def olympus_panel() -> rx.Component:
    return rx.flex(
        section(
            "Runtime Summary",
            "Olympus",
            rx.vstack(
                metric_card("Total PnL", State.olympus_total_pnl, "Pulled from Olympus trade memory."),
                metric_card("Trades", State.olympus_total_trades, "Recorded completed trades."),
                metric_card("Last Trade", State.olympus_last_trade, "Latest exit recorded in Olympus."),
                rx.text(State.olympus_cycle_summary, color=TEXT_MUTED, font_size="13px"),
                width="100%",
                spacing="4",
            ),
        ),
        section(
            "Recent Trades",
            "Read-only",
            rx.box(rx.foreach(State.olympus_recent_trades, trade_row), width="100%"),
        ),
        section(
            "Latest Report",
            "Apex context",
            rx.text(State.olympus_report_excerpt, color=TEXT_SOFT, font_size="13px", line_height="1.8", white_space="pre-wrap"),
        ),
        wrap="wrap",
        gap="20px",
        width="100%",
    )


def activity_panel() -> rx.Component:
    return rx.flex(
        section(
            "Recent Audit",
            "Pantheon activity",
            rx.box(rx.foreach(State.audit_items, audit_row), width="100%"),
        ),
        wrap="wrap",
        gap="20px",
        width="100%",
    )


def doctor_panel() -> rx.Component:
    return rx.flex(
        section(
            "Provider Health",
            "Doctor",
            rx.flex(
                metric_card("Current", State.doctor_current_provider, "Provider currently used for open-ended reasoning."),
                metric_card("Preferred", State.doctor_preferred_provider, "Configured priority order for Pantheon generation."),
                metric_card(
                    "Anthropic",
                    State.anthropic_status,
                    rx.cond(
                        State.anthropic_model != "",
                        State.anthropic_model,
                        rx.cond(
                            State.anthropic_reason != "",
                            State.anthropic_reason,
                            "Anthropic provider health.",
                        ),
                    ),
                ),
                metric_card(
                    "Ollama",
                    State.ollama_status,
                    rx.cond(
                        State.ollama_model != "",
                        State.ollama_model,
                        rx.cond(
                            State.ollama_reason != "",
                            State.ollama_reason,
                            "Ollama runtime health.",
                        ),
                    ),
                ),
                wrap="wrap",
                gap="16px",
                width="100%",
            ),
        ),
        section(
            "Subsystem Health",
            "Doctor",
            rx.vstack(
                list_row("BlackBook", State.blackbook_status, rx.cond(State.doctor_blackbook_reason != "", State.doctor_blackbook_reason, "BlackBook is reachable.")),
                list_row("Maridian", State.maridian_status, rx.cond(State.doctor_maridian_reason != "", State.doctor_maridian_reason, "Maridian is reachable.")),
                list_row("Olympus", State.olympus_status, rx.cond(State.doctor_olympus_reason != "", State.doctor_olympus_reason, "Olympus is reachable.")),
                width="100%",
                spacing="0",
            ),
        ),
        section(
            "Recent Traces",
            "Doctor",
            rx.box(rx.foreach(State.trace_items, trace_row), width="100%"),
        ),
        wrap="wrap",
        gap="20px",
        width="100%",
    )


def pantheon_panel() -> rx.Component:
    return rx.vstack(
        pantheon_subnav(),
        rx.cond(
            State.pantheon_section == "overview",
            overview_panel(),
            rx.cond(
                State.pantheon_section == "blackbook",
                blackbook_panel(),
                rx.cond(
                    State.pantheon_section == "maridian",
                    maridian_panel(),
                    rx.cond(
                        State.pantheon_section == "olympus",
                        olympus_panel(),
                        rx.cond(
                            State.pantheon_section == "activity",
                            activity_panel(),
                            doctor_panel(),
                        ),
                    ),
                ),
            ),
        ),
        width="100%",
        spacing="5",
        align="stretch",
    )


def content_shell() -> rx.Component:
    return shell_frame(
        rx.vstack(
            top_nav(),
            rx.cond(
                State.context_error != "",
                rx.text(f"Context error: {State.context_error}", color="#9c5d38", font_size="13px"),
                rx.box(),
            ),
            rx.cond(State.active_tab == "apollo", apollo_tab(), pantheon_panel()),
            width="100%",
            spacing="6",
            align="stretch",
        ),
        padding=["22px", "26px", "32px"],
        width="100%",
    )


def dashboard_layout() -> rx.Component:
    return rx.box(
        ambient_background(),
        rx.box(
            content_shell(),
            max_width=rx.cond(State.active_tab == "apollo", "1020px", "1360px"),
            margin="0 auto",
            padding=["26px 18px 40px", "34px 24px 48px", "48px 28px 64px"],
            position="relative",
            z_index="1",
        ),
        min_height="100vh",
        background=BG,
        position="relative",
    )
