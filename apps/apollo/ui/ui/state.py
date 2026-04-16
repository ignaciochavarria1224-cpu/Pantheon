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


class HistoryItem(BaseModel):
    role: str
    content: str
    timestamp: str
    channel: str = "ui"
    system_used: str = ""


class DecisionItem(BaseModel):
    decision: str
    reasoning: str = ""
    domain: str = ""
    timestamp: str = ""
    tags: str = ""


class PatternItem(BaseModel):
    pattern_type: str
    description: str
    confidence: str = ""
    data_points: str = ""


class VaultNote(BaseModel):
    title: str
    filename: str
    preview: str
    updated_at: str


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
    messages: List[Message] = []
    history_items: List[HistoryItem] = []
    decision_items: List[DecisionItem] = []
    pattern_items: List[PatternItem] = []
    vault_decision_notes: List[VaultNote] = []
    vault_pattern_notes: List[VaultNote] = []
    vault_mental_models: List[VaultNote] = []

    input_text: str = ""
    is_loading: bool = False
    context_loading: bool = False
    health_label: str = "Unknown"
    health_detail: str = "Waiting for backend"
    context_error: str = ""
    last_refreshed: str = "Never"
    self_model_excerpt: str = "Vault self-model loading..."
    vault_path: str = ""
    vault_status_label: str = "Offline"
    recent_signal_label: str = ""
    recent_signal_text: str = ""
    activity_summary: str = "No recent system activity."
    vault_decision_count: str = "0"
    vault_pattern_count: str = "0"
    vault_mental_model_count: str = "0"

    def switch_to_apollo(self):
        self.active_tab = "apollo"

    def switch_to_pantheon(self):
        self.active_tab = "pantheon"

    def update_input_text(self, value: str):
        self.input_text = value

    def handle_enter_key(self, key: str):
        if key == "Enter":
            return State.send_message
        return None

    def load_dashboard(self):
        return State.refresh_context

    def refresh_context(self):
        self.context_loading = True
        self.context_error = ""
        self.recent_signal_label = ""
        self.recent_signal_text = ""
        yield

        errors: list[str] = []

        try:
            health = requests.get(f"{APOLLO_API}/health", timeout=5).json()
            self.health_label = health.get("status", "Unavailable")
            self.health_detail = "Apollo core reachable"
        except Exception as exc:
            self.health_label = "Offline"
            self.health_detail = _truncate(str(exc), 80)
            errors.append("health")

        try:
            history = requests.get(f"{APOLLO_API}/history", timeout=5).json()
            self.history_items = [
                HistoryItem(
                    role=item.get("role", "apollo"),
                    content=_truncate(item.get("content", ""), 120),
                    timestamp=_format_timestamp(item.get("timestamp")),
                    channel=item.get("channel", "ui"),
                    system_used=item.get("system_used") or "",
                )
                for item in history[:8]
            ]
        except Exception:
            self.history_items = []
            errors.append("history")

        try:
            decisions = requests.get(f"{APOLLO_API}/decisions", timeout=5).json()
            self.decision_items = [
                DecisionItem(
                    decision=_truncate(item.get("decision", ""), 72),
                    reasoning=_truncate(item.get("reasoning", ""), 96),
                    domain=item.get("domain") or "General",
                    timestamp=_format_timestamp(item.get("timestamp")),
                    tags=", ".join(item.get("tags", []) if isinstance(item.get("tags"), list) else []),
                )
                for item in decisions[:6]
            ]
        except Exception:
            self.decision_items = []
            errors.append("decisions")

        try:
            patterns = requests.get(f"{APOLLO_API}/patterns", timeout=5).json()
            self.pattern_items = [
                PatternItem(
                    pattern_type=item.get("pattern_type", "Pattern"),
                    description=_truncate(item.get("description", ""), 110),
                    confidence=f"{round((item.get('confidence') or 0) * 100)}%",
                    data_points=str(item.get("data_points", 0)),
                )
                for item in patterns[:6]
            ]
        except Exception:
            self.pattern_items = []
            errors.append("patterns")

        try:
            vault = requests.get(f"{APOLLO_API}/vault", timeout=5).json()
            counts = vault.get("counts", {})
            self.self_model_excerpt = vault.get(
                "self_model_excerpt",
                "Self model is waiting for the first Apollo-written insight.",
            )
            self.vault_path = vault.get("vault_path", "")
            self.vault_status_label = "Linked" if self.vault_path else "Offline"
            self.vault_decision_count = str(counts.get("decisions", 0))
            self.vault_pattern_count = str(counts.get("patterns", 0))
            self.vault_mental_model_count = str(counts.get("mental_models", 0))
            self.vault_decision_notes = [
                VaultNote(
                    title=item.get("title", "Decision note"),
                    filename=item.get("filename", ""),
                    preview=item.get("preview", ""),
                    updated_at=_format_timestamp(item.get("updated_at")),
                )
                for item in vault.get("decisions", [])[:4]
            ]
            self.vault_pattern_notes = [
                VaultNote(
                    title=item.get("title", "Pattern note"),
                    filename=item.get("filename", ""),
                    preview=item.get("preview", ""),
                    updated_at=_format_timestamp(item.get("updated_at")),
                )
                for item in vault.get("patterns", [])[:4]
            ]
            self.vault_mental_models = [
                VaultNote(
                    title=item.get("title", "Mental model"),
                    filename=item.get("filename", ""),
                    preview=item.get("preview", ""),
                    updated_at=_format_timestamp(item.get("updated_at")),
                )
                for item in vault.get("mental_models", [])[:4]
            ]
        except Exception:
            self.self_model_excerpt = "Vault offline or unreadable."
            self.vault_path = ""
            self.vault_status_label = "Offline"
            self.vault_decision_notes = []
            self.vault_pattern_notes = []
            self.vault_mental_models = []
            self.vault_decision_count = "0"
            self.vault_pattern_count = "0"
            self.vault_mental_model_count = "0"
            errors.append("vault")

        if self.pattern_items:
            self.recent_signal_label = "Signal"
            self.recent_signal_text = _truncate(self.pattern_items[0].description, 42)
        elif self.history_items:
            self.recent_signal_label = "Recent"
            self.recent_signal_text = _truncate(self.history_items[0].content, 42)
        elif self.decision_items:
            self.recent_signal_label = "Decision"
            self.recent_signal_text = _truncate(self.decision_items[0].decision, 42)

        if self.history_items:
            first = self.history_items[0]
            self.activity_summary = _truncate(f"{first.role.title()}: {first.content}", 84)
        elif self.decision_items:
            self.activity_summary = _truncate(f"Decision logged: {self.decision_items[0].decision}", 84)
        elif self.pattern_items:
            self.activity_summary = _truncate(f"Pattern detected: {self.pattern_items[0].description}", 84)
        else:
            self.activity_summary = "No recent system activity."

        self.context_loading = False
        self.last_refreshed = datetime.now().strftime("%H:%M:%S")
        if errors:
            self.context_error = f"Context unavailable: {', '.join(errors)}"

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
                timeout=30,
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

    @rx.var
    def blackbook_status(self) -> str:
        return "Preview"

    @rx.var
    def maridian_status(self) -> str:
        if int(self.vault_pattern_count) > 0 or int(self.vault_mental_model_count) > 0:
            return "Signal present"
        if self.vault_status_label == "Linked":
            return "Linked"
        return "Dormant"

    @rx.var
    def olympus_status(self) -> str:
        if self.pattern_items:
            return "Observed"
        return "Preview"

    @rx.var
    def apollo_channel_status(self) -> str:
        if self.health_label == "Apollo is running":
            return "Active"
        if self.health_label == "Offline":
            return "Offline"
        return "Unknown"
