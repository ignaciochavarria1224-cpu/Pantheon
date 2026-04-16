from pantheon.models import PantheonResult
from pantheon.reasoning import PantheonReasoner

_reasoner = PantheonReasoner()


def reason(message: str, conversation_history: list | None = None, channel: str = "ui") -> PantheonResult:
    return _reasoner.reason(message=message, conversation_history=conversation_history, channel=channel)


def chat(message: str, conversation_history: list | None = None, channel: str = "ui") -> tuple[str, list]:
    history = list(conversation_history or [])
    history.append({"role": "user", "content": message})
    result = reason(message=message, conversation_history=history, channel=channel)
    history.append({"role": "assistant", "content": result.response})
    return result.response, history
