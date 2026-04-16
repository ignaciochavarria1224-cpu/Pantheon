from datetime import datetime
from config import AUDIT_LOG_PATH

def log(action: str, detail: str = None, system: str = None):
    """Write a permanent record of every action Apollo takes."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    system_tag = f" [{system}]" if system else ""
    detail_tag = f" — {detail}" if detail else ""
    entry = f"{timestamp}{system_tag} — {action}{detail_tag}\n"
    with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(entry)
    print(f"[AUDIT]{system_tag} {action}{detail_tag}")
