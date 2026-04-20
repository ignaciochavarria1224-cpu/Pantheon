from __future__ import annotations

import json
import subprocess
from datetime import date, datetime
from pathlib import Path
from typing import Any

from config import MARIDIAN_APP_PATH, MERIDIAN_VAULT_PATH, MERIDIAN_STATE_PATH


def _root() -> Path:
    """Code location (apps/maridian inside Pantheon)."""
    return Path(MARIDIAN_APP_PATH)


def _vault() -> Path:
    """Data location (Dropbox/Maridian — wiki, raw, vault_state.json)."""
    return Path(MERIDIAN_VAULT_PATH)


def _read_json(path: Path, default: Any):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _question_payload() -> dict[str, Any]:
    today_file = _vault() / "Questions" / f"{date.today().isoformat()}.md"
    return _read_json(today_file, {"questions": [], "source_file": str(today_file)})


def _wiki_pages(limit: int = 6) -> list[dict[str, Any]]:
    wiki_dir = _vault() / "wiki"
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
        vault = _vault()
        state = _read_json(vault / "vault_state.json", {})
        questions = _question_payload()
        index_path = vault / "wiki" / "INDEX.md"
        index_excerpt = ""
        if index_path.exists():
            index_excerpt = " ".join(index_path.read_text(encoding="utf-8").split())[:280]

        return {
            "connected": vault.exists(),
            "locked": (vault / ".evolve.lock").exists(),
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
    vault = _vault()  # run from data dir so relative paths (wiki/, raw/) work
    evolve_script = _root() / "evolve.py"
    if not evolve_script.exists():
        evolve_script = vault / "evolve.py"
    try:
        result = subprocess.run(
            ["python", str(evolve_script), "evolve"],
            cwd=str(vault),
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
