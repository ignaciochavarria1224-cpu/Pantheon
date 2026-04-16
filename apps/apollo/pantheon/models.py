from dataclasses import dataclass, field
from typing import Any


@dataclass
class PantheonResult:
    response: str
    sources: list[dict[str, Any]] = field(default_factory=list)
    tools_used: list[str] = field(default_factory=list)
    actions_taken: list[str] = field(default_factory=list)
    actions_proposed: list[str] = field(default_factory=list)
    audit_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "response": self.response,
            "sources": self.sources,
            "tools_used": self.tools_used,
            "actions_taken": self.actions_taken,
            "actions_proposed": self.actions_proposed,
            "audit_id": self.audit_id,
        }
