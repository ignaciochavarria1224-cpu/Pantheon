# db/neon_bridge.py
import os
import re
import json
import psycopg2
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent.parent / ".env")


def _to_pooler_url(url: str) -> str:
    """Convert standard Neon URL to pooler URL (port 6543).
    Home WiFi blocks port 5432 — pooler port 6543 works everywhere.
    """
    if ":6543" in url:
        return url
    # Insert :6543 before the path segment (handles both @host/db and @host:5432/db)
    url = re.sub(r'(@[^/:@\s]+):5432/', r'\1:6543/', url)
    url = re.sub(r'(@[^/:@\s]+)(/[^?])', r'\1:6543\2', url)
    return url


def get_connection():
    url = os.environ.get("NEON_DATABASE_URL")
    if not url:
        raise RuntimeError("NEON_DATABASE_URL not set in .env")
    try:
        return psycopg2.connect(url, connect_timeout=8)
    except Exception:
        # Port 5432 blocked (common on home WiFi) — retry on pooler port 6543
        pooler_url = _to_pooler_url(url)
        return psycopg2.connect(pooler_url, connect_timeout=8)


def init_tables():
    """Create Meridian tables if they don't exist."""
    schema = (Path(__file__).parent / "schema.sql").read_text()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(schema)
    conn.commit()
    cur.close()
    conn.close()
    print("  [NEON] Tables initialized.")


def pull_new_entries(processed_ids: list) -> list:
    """Pull all journal entries not yet processed by Meridian."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        if processed_ids:
            placeholders = ','.join(['%s'] * len(processed_ids))
            cur.execute(
                f"SELECT id, entry_date, tag, body FROM journal_entries "
                f"WHERE id NOT IN ({placeholders}) ORDER BY entry_date ASC",
                processed_ids
            )
        else:
            cur.execute(
                "SELECT id, entry_date, tag, body "
                "FROM journal_entries ORDER BY entry_date ASC"
            )
        rows = cur.fetchall()
        return [{"id": r[0], "entry_date": str(r[1]), "tag": r[2], "body": r[3]}
                for r in rows]
    except Exception as e:
        print(f"  [NEON] Pull failed: {e}")
        return []
    finally:
        cur.close()
        conn.close()


def push_questions(questions: list, generated_date: str) -> bool:
    """Push daily adaptive questions to Neon."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO meridian_questions (generated_date, questions) VALUES (%s, %s)",
            (generated_date, json.dumps(questions))
        )
        conn.commit()
        print(f"  [NEON] Questions pushed for {generated_date}.")
        return True
    except Exception as e:
        print(f"  [NEON] Question push failed: {e}")
        return False
    finally:
        cur.close()
        conn.close()


def push_framework(title: str, body: str, metadata: dict) -> bool:
    """Push a published framework to Neon."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """INSERT INTO meridian_outputs
               (framework_title, framework_body, source_entry_ids,
                entry_date_range, fitness, domains)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (title, body,
             ','.join(str(i) for i in metadata.get("source_entry_ids", [])),
             metadata.get("entry_date_range", ""),
             metadata.get("fitness"),
             ','.join(metadata.get("domains", [])))
        )
        conn.commit()
        print(f"  [NEON] Framework '{title}' pushed.")
        return True
    except Exception as e:
        print(f"  [NEON] Framework push failed: {e}")
        return False
    finally:
        cur.close()
        conn.close()


def push_insight(insight_type: str, body: str, generated_date: str) -> bool:
    """Push a pattern report or insight to Neon."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO meridian_insights (insight_type, insight_body, generated_date) "
            "VALUES (%s, %s, %s)",
            (insight_type, body, generated_date)
        )
        conn.commit()
        print(f"  [NEON] Insight ({insight_type}) pushed.")
        return True
    except Exception as e:
        print(f"  [NEON] Insight push failed: {e}")
        return False
    finally:
        cur.close()
        conn.close()


def push_vault_snapshot(notes: list, cycle: int) -> bool:
    """Sync all vault notes to Neon so Black Book can display them."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM meridian_notes")
        for n in notes:
            fm = n.get("frontmatter", {})
            domains = ",".join(fm.get("domains", []))
            cur.execute(
                """INSERT INTO meridian_notes
                   (note_id, title, stage, fitness, maturity, domains, body, cycle, synced_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    fm.get("id", ""),
                    fm.get("title", n.get("path", "")),
                    fm.get("stage", "seed"),
                    fm.get("fitness"),
                    fm.get("maturity"),
                    domains,
                    n.get("body", "")[:2000],
                    cycle,
                    __import__("datetime").datetime.now().isoformat(),
                )
            )
        conn.commit()
        print(f"  [NEON] Vault snapshot pushed: {len(notes)} notes.")
        return True
    except Exception as e:
        print(f"  [NEON] Vault snapshot failed: {e}")
        return False
    finally:
        cur.close()
        conn.close()


def push_brain_themes(themes: list, index_body: str, cycle: int) -> bool:
    """Push Brain/ theme documents to Neon so Black Book can display them."""
    from datetime import datetime
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM meridian_brain")
        for t in themes:
            cur.execute(
                "INSERT INTO meridian_brain (theme, body, cycle, synced_at) VALUES (%s, %s, %s, %s)",
                (t["theme"], t["body"][:5000], cycle, datetime.now().isoformat())
            )
        if index_body:
            cur.execute(
                "INSERT INTO meridian_brain (theme, body, cycle, synced_at) VALUES (%s, %s, %s, %s)",
                ("INDEX", index_body[:5000], cycle, datetime.now().isoformat())
            )
        conn.commit()
        print(f"  [NEON] Brain pushed: {len(themes)} themes.")
        return True
    except Exception as e:
        print(f"  [NEON] Brain push failed: {e}")
        return False
    finally:
        cur.close()
        conn.close()


def get_entry_count() -> int:
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM journal_entries")
        return cur.fetchone()[0]
    finally:
        cur.close()
        conn.close()
