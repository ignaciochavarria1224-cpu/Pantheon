from __future__ import annotations

import reflex as rx

from .state import DecisionItem, HistoryItem, Message, PatternItem, State, VaultNote


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
ACCENT_SOFT = "#b89a67"
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
        rx.box(
            position="absolute",
            inset="0",
            background_image=(
                "linear-gradient(rgba(140, 106, 47, 0.035) 1px, transparent 1px),"
                "linear-gradient(90deg, rgba(140, 106, 47, 0.03) 1px, transparent 1px)"
            ),
            background_size="96px 96px",
            opacity="0.45",
            mask_image="linear-gradient(180deg, black 0%, rgba(0,0,0,0.78) 65%, transparent 100%)",
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


def tab_button(label: str, tab_key: str, action) -> rx.Component:
    active = State.active_tab == tab_key
    return rx.button(
        label,
        on_click=action,
        height="40px",
        padding="0 16px",
        border_radius="999px",
        border=rx.cond(active, "none", f"1px solid {BORDER}"),
        background=rx.cond(
            active,
            "linear-gradient(135deg, #9b7742 0%, #c3a46f 100%)",
            "rgba(255, 252, 247, 0.78)",
        ),
        color=rx.cond(active, "#fffaf2", GRAPHITE),
        font_size="13px",
        font_weight="600",
        cursor="pointer",
        _hover={"opacity": "0.95"},
    )


def top_nav() -> rx.Component:
    return rx.hstack(
        rx.vstack(
            eyebrow("Voice of the system"),
            rx.text("Apollo", color=GRAPHITE, font_size="26px", font_weight="600", letter_spacing="-0.05em"),
            spacing="1",
            align="start",
        ),
        rx.spacer(),
        rx.hstack(
            tab_button("Apollo", "apollo", State.switch_to_apollo),
            tab_button("Pantheon", "pantheon", State.switch_to_pantheon),
            spacing="3",
            align="center",
        ),
        width="100%",
        align="center",
    )


def transcript_message(message: Message) -> rx.Component:
    user = message.role == "user"
    return rx.vstack(
        rx.hstack(
            rx.text(
                rx.cond(user, "You", "Apollo"),
                color=ACCENT,
                font_size="11px",
                letter_spacing="0.16em",
                text_transform="uppercase",
                font_family="'IBM Plex Mono', 'Consolas', monospace",
            ),
            rx.spacer(),
            rx.text(message.timestamp, color=TEXT_MUTED, font_size="11px"),
            width="100%",
            align="center",
        ),
        rx.text(
            message.content,
            color=TEXT_SOFT,
            font_size="16px",
            line_height="1.9",
            white_space="pre-wrap",
        ),
        align="start",
        spacing="2",
        width="100%",
        padding="18px 20px",
        border_radius="22px",
        background=rx.cond(user, USER_TINT, APOLLO_TINT),
        border=rx.cond(user, f"1px solid {BORDER_STRONG}", "1px solid rgba(255,255,255,0.72)"),
    )


def loading_row() -> rx.Component:
    return rx.box(
        rx.text("Apollo is thinking...", color=TEXT_MUTED, font_size="13px", font_style="italic"),
        width="100%",
        padding="16px 18px",
        border=f"1px solid {BORDER}",
        border_radius="18px",
        background=SURFACE_SOFT,
    )


def empty_transcript() -> rx.Component:
    return rx.vstack(
        eyebrow("Live composer"),
        rx.heading(
            "Apollo is ready.",
            size="7",
            color=GRAPHITE,
            weight="medium",
            letter_spacing="-0.05em",
        ),
        rx.text(
            "Speak in plain language. Apollo stays conversational here; Pantheon holds the surrounding system view.",
            color=TEXT_MUTED,
            font_size="16px",
            line_height="1.8",
            max_width="560px",
        ),
        width="100%",
        align="start",
        spacing="2",
        padding_top="4px",
    )


def action_button(label: str, action, primary: bool = False) -> rx.Component:
    return rx.button(
        label,
        on_click=action,
        padding="0 18px",
        height="42px",
        border_radius="999px",
        border=rx.cond(primary, "none", f"1px solid {BORDER}"),
        background=rx.cond(
            primary,
            "linear-gradient(135deg, #9b7742 0%, #c3a46f 100%)",
            "rgba(255, 251, 245, 0.75)",
        ),
        color=rx.cond(primary, "#fffaf2", GRAPHITE),
        font_size="13px",
        font_weight="600",
        cursor="pointer",
        box_shadow=rx.cond(primary, "0 10px 32px rgba(156, 119, 66, 0.22)", "none"),
        _hover={"opacity": "0.95"},
    )


def composer() -> rx.Component:
    return rx.vstack(
        shell_frame(
            rx.vstack(
                rx.text_area(
                    value=State.input_text,
                    on_change=State.update_input_text,
                    on_key_down=State.handle_enter_key,
                    placeholder="Ask for a plan, issue a command, or leave a reflection.",
                    width="100%",
                    min_height="180px",
                    rows="7",
                    auto_height=False,
                    resize="vertical",
                    size="3",
                    variant="soft",
                    radius="large",
                    background="rgba(255, 252, 247, 0.96)",
                    padding="22px 20px",
                    color=GRAPHITE,
                    font_size="17px",
                    line_height="1.85",
                    border=f"1px solid {BORDER_STRONG}",
                    box_shadow="inset 0 1px 0 rgba(255,255,255,0.7)",
                    _placeholder={"color": "rgba(44, 36, 29, 0.34)"},
                    _focus={
                        "border_color": ACCENT_SOFT,
                        "box_shadow": "0 0 0 2px rgba(184, 154, 103, 0.16), inset 0 1px 0 rgba(255,255,255,0.7)",
                    },
                ),
                rx.hstack(
                    rx.cond(
                        State.health_label == "Offline",
                        rx.text(
                            State.health_detail,
                            color=TEXT_MUTED,
                            font_size="12px",
                            font_family="'IBM Plex Mono', 'Consolas', monospace",
                        ),
                        rx.text(
                            "Enter sends. Shift+Enter adds a line.",
                            color=TEXT_MUTED,
                            font_size="12px",
                            font_family="'IBM Plex Mono', 'Consolas', monospace",
                        ),
                    ),
                    rx.spacer(),
                    action_button("Clear session", State.clear_chat),
                    action_button(rx.cond(State.is_loading, "Thinking...", "Transmit"), State.send_message, primary=True),
                    width="100%",
                    align="center",
                    spacing="3",
                ),
                width="100%",
                spacing="4",
            ),
            padding="18px",
        ),
        width="100%",
        spacing="3",
        align="stretch",
    )


def apollo_tab() -> rx.Component:
    return rx.box(
        rx.cond(
            State.messages.length() > 0,
            rx.vstack(
                rx.foreach(State.messages, transcript_message),
                rx.cond(State.is_loading, loading_row(), rx.box()),
                width="100%",
                spacing="4",
                align="stretch",
            ),
            empty_transcript(),
        ),
        width="100%",
    )


def metric_card(label: str, value, detail) -> rx.Component:
    return shell_frame(
        rx.vstack(
            eyebrow(label),
            rx.text(value, color=GRAPHITE, font_size="24px", font_weight="600", letter_spacing="-0.03em"),
            rx.text(detail, color=TEXT_MUTED, font_size="13px", line_height="1.6"),
            width="100%",
            spacing="1",
            align="start",
        ),
        padding="18px",
        background=SURFACE_STRONG,
    )


def subsystem_row(name: str, status, detail: str) -> rx.Component:
    return rx.hstack(
        rx.vstack(
            rx.text(name, color=GRAPHITE, font_size="15px", font_weight="600"),
            rx.text(detail, color=TEXT_MUTED, font_size="12px"),
            spacing="1",
            align="start",
        ),
        rx.spacer(),
        rx.text(
            status,
            color=ACCENT,
            font_size="12px",
            font_weight="600",
            letter_spacing="0.12em",
            text_transform="uppercase",
            font_family="'IBM Plex Mono', 'Consolas', monospace",
        ),
        width="100%",
        align="center",
        padding_y="10px",
        border_bottom=f"1px solid {BORDER}",
    )


def list_row(title, meta, detail) -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.text(title, color=GRAPHITE, font_size="14px", font_weight="600"),
            rx.spacer(),
            rx.text(meta, color=TEXT_MUTED, font_size="11px"),
            width="100%",
            align="center",
        ),
        rx.text(detail, color=TEXT_SOFT, font_size="13px", line_height="1.7"),
        width="100%",
        spacing="1",
        align="start",
        padding_y="10px",
        border_bottom=f"1px solid {BORDER}",
    )


def empty_note(text: str) -> rx.Component:
    return rx.text(text, color=TEXT_MUTED, font_size="13px", line_height="1.7")


def history_row(item: HistoryItem) -> rx.Component:
    title = rx.cond(item.role == "user", "You", "Apollo")
    meta = rx.cond(item.system_used != "", f"{item.timestamp} / {item.system_used}", item.timestamp)
    return list_row(title, meta, item.content)


def decision_row(item: DecisionItem) -> rx.Component:
    return list_row(item.domain, item.timestamp, item.decision)


def pattern_row(item: PatternItem) -> rx.Component:
    return list_row(item.pattern_type, f"{item.confidence} / {item.data_points} pts", item.description)


def vault_row(item: VaultNote) -> rx.Component:
    return list_row(item.title, item.updated_at, rx.cond(item.preview != "", item.preview, "No preview available."))


def section(title: str, subtitle: str, body: rx.Component) -> rx.Component:
    return shell_frame(
        rx.vstack(
            eyebrow(subtitle),
            rx.text(title, color=GRAPHITE, font_size="19px", font_weight="600", letter_spacing="-0.03em"),
            body,
            width="100%",
            spacing="4",
            align="start",
        ),
        padding="22px",
    )


def pantheon_tab() -> rx.Component:
    core_status = rx.vstack(
        rx.flex(
            metric_card("Core", State.health_label, State.health_detail),
            metric_card("Vault", State.vault_status_label, "Pantheon reads the current Apollo mind vault."),
            metric_card("Refresh", State.last_refreshed, "Latest context pull from current Apollo endpoints."),
            wrap="wrap",
            gap="16px",
            width="100%",
        ),
        rx.cond(
            State.context_error != "",
            rx.text(State.context_error, color="#9c5d38", font_size="13px"),
            rx.box(),
        ),
        width="100%",
        spacing="4",
        align="start",
    )

    subsystems = rx.vstack(
        subsystem_row("Apollo", State.apollo_channel_status, "Live conversational surface backed by the current `/chat` interface."),
        subsystem_row("BlackBook", State.blackbook_status, "Not yet wired as a live Pantheon connector in this preview."),
        subsystem_row("Maridian", State.maridian_status, "Inferred only from vault and memory artifacts already available."),
        subsystem_row("Olympus", State.olympus_status, "Observed through existing signals only; no execution surface here."),
        width="100%",
        spacing="0",
        align="start",
    )

    memory = rx.vstack(
        rx.text(State.self_model_excerpt, color=TEXT_SOFT, font_size="13px", line_height="1.8", white_space="pre-wrap"),
        rx.flex(
            metric_card("Decisions", State.vault_decision_count, "Vault decision notes currently available."),
            metric_card("Patterns", State.vault_pattern_count, "Detected pattern notes available now."),
            metric_card("Models", State.vault_mental_model_count, "Mental models in the vault today."),
            wrap="wrap",
            gap="16px",
            width="100%",
        ),
        rx.cond(
            State.pattern_items.length() > 0,
            rx.box(rx.foreach(State.pattern_items, pattern_row), width="100%"),
            empty_note("No active patterns are available from the current system state."),
        ),
        width="100%",
        spacing="4",
        align="start",
    )

    activity = rx.vstack(
        metric_card(
            "Current signal",
            rx.cond(State.recent_signal_label != "", State.recent_signal_label, "Quiet"),
            rx.cond(State.recent_signal_text != "", State.recent_signal_text, State.activity_summary),
        ),
        rx.cond(
            State.history_items.length() > 0,
            rx.box(rx.foreach(State.history_items, history_row), width="100%"),
            empty_note("No recent conversation activity is available yet."),
        ),
        rx.cond(
            State.decision_items.length() > 0,
            rx.box(rx.foreach(State.decision_items, decision_row), width="100%"),
            empty_note("No recent decision log entries are available yet."),
        ),
        rx.cond(
            State.vault_decision_notes.length() > 0,
            rx.box(rx.foreach(State.vault_decision_notes, vault_row), width="100%"),
            empty_note("No current vault decision notes are available."),
        ),
        width="100%",
        spacing="4",
        align="start",
    )

    return rx.vstack(
        rx.vstack(
            eyebrow("Pantheon core preview"),
            rx.heading(
                "Pantheon",
                size="8",
                color=GRAPHITE,
                weight="medium",
                letter_spacing="-0.06em",
            ),
            rx.text(
                "This is the emerging system shell behind Apollo, showing only the real signals and memory surfaces available today.",
                color=TEXT_MUTED,
                font_size="15px",
                max_width="760px",
                line_height="1.8",
            ),
            width="100%",
            spacing="2",
            align="start",
        ),
        rx.flex(
            section("Core Status", "System", core_status),
            section("Subsystems", "Readiness", subsystems),
            section("Memory", "Current context", memory),
            section("Activity", "Recent signals", activity),
            wrap="wrap",
            gap="20px",
            width="100%",
        ),
        width="100%",
        spacing="5",
        align="stretch",
    )


def content_shell() -> rx.Component:
    return shell_frame(
        rx.vstack(
            top_nav(),
            rx.cond(State.active_tab == "apollo", apollo_tab(), pantheon_tab()),
            rx.cond(State.active_tab == "apollo", composer(), rx.box()),
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
            max_width=rx.cond(State.active_tab == "apollo", "980px", "1280px"),
            margin="0 auto",
            padding=["26px 18px 40px", "34px 24px 48px", "48px 28px 64px"],
            position="relative",
            z_index="1",
            transition="max-width 220ms ease",
        ),
        min_height="100vh",
        background=BG,
        position="relative",
        overflow="hidden",
    )
