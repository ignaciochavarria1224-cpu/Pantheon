from __future__ import annotations

import json
import subprocess
from datetime import date, datetime
from pathlib import Path
from typing import Any

from config import MARIDIAN_APP_PATH


def _root() -> Path:
    return Path(MARIDIAN_APP_PATH)


def _read_json(path: Path, default: Any):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _question_payload() -> dict[str, Any]:
    today_file = _root() / "Questions" / f"{date.today().isoformat()}.md"
    if not today_file.exists():
        return {"questions": [], "source_file": str(today_file)}

    text = today_file.read_text(encoding="utf-8")
    try:
        parsed = json.loads(text)
        questions = parsed.get("questions", [])
        return {"questions": questions, "source_file": str(today_file)}
    except Exception:
        questions: list[dict[str, str]] = []
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith(("- ", "* ")):
                line = line[2:].strip()
            elif line[:2].isdigit() and ". " in line:
                line = line.split(". ", 1)[1].strip()
            elif line.startswith("#"):
                continue
            else:
                continue
            questions.append({"question": line, "context": ""})
        return {"questions": questions, "source_file": str(today_file)}


def _wiki_pages(limit: int = 6) -> list[dict[str, Any]]:
    wiki_dir = _root() / "wiki"
    if not wiki_dir.exists():
        return []
    pages = []
    for path in sorted(wiki_dir.glob("*.md"), key=lambda item: item.stat().st_mtime, reverse=True):
        if path.name == "INDEX.md":
            continue
        preview = " ".join(path.read_text(encoding="utf-8").split())[:220]
        pages.append(
            {
                "title": path.stem,
                "path": str(path),
                "updated_at": datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
                "preview": preview,
            }
        )
        if len(pages) >= limit:
            break
    return pages


def get_snapshot() -> dict[str, Any]:
    try:
        root = _root()
        state = _read_json(root / "vault_state.json", {})
        questions = _question_payload()
        index_path = root / "wiki" / "INDEX.md"
        index_excerpt = ""
        if index_path.exists():
            index_excerpt = " ".join(index_path.read_text(encoding="utf-8").split())[:280]

        return {
            "connected": root.exists(),
            "fetched_at": datetime.now().isoformat(),
            "locked": (root / ".evolve.lock").exists(),
            "state": state,
            "today_questions": questions.get("questions", []),
            "today_question_file": questions.get("source_file", ""),
            "top_themes": _wiki_pages(),
            "index_excerpt": index_excerpt,
            "last_cycle": state.get("last_cycle"),
            "cycle_count": state.get("cycle_count", 0),
            "entries_processed": state.get("total_entries_processed", 0),
        }
    except Exception as exc:
        return {
            "connected": False,
            "error": str(exc),
            "fetched_at": datetime.now().isoformat(),
            "locked": False,
            "state": {},
            "today_questions": [],
            "today_question_file": "",
            "top_themes": [],
            "index_excerpt": "",
            "last_cycle": None,
            "cycle_count": 0,
            "entries_processed": 0,
        }


def run_cycle() -> dict[str, Any]:
    root = _root()
    try:
        result = subprocess.run(
            ["python", "evolve.py", "evolve"],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=300,
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout[-4000:],
            "stderr": result.stderr[-4000:],
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Meridian cycle timed out after 5 minutes."}
    except Exception as exc:
        return {"success": False, "error": str(exc)}
