"""
SQLite database connection and schema management for Olympus.

Single entry point for all database access. WAL journal mode + foreign keys ON.
All timestamps are written as UTC ISO-8601 text.

Ported from the stabilized old Olympus (core/memory/database.py), trimmed to the
Phase 1 foundation. The schema lives in schema.sql alongside this file and is
applied idempotently on every startup.
"""

from __future__ import annotations

import re
import sqlite3
import threading
from pathlib import Path
from typing import Optional

from core.logger import get_logger

logger = get_logger(__name__)

# schema.sql lives alongside this file.
_SCHEMA_PATH = Path(__file__).parent / "schema.sql"

# Views are dropped and recreated on every initialize() so their definitions can
# evolve without a migration. Tables are CREATE ... IF NOT EXISTS (never dropped).
_REFRESHABLE_VIEWS = (
    "v_trade_quality",
)


def _strip_sql_comments(sql: str) -> str:
    """
    Remove '--' line comments from SQL, preserving anything inside single-quoted
    string literals. Used before splitting the schema on ';' so a semicolon that
    appears inside a comment cannot fragment a statement.
    """
    out_lines: list[str] = []
    for line in sql.splitlines():
        in_quote = False
        i = 0
        while i < len(line):
            ch = line[i]
            if ch == "'":
                in_quote = not in_quote
            elif ch == "-" and not in_quote and i + 1 < len(line) and line[i + 1] == "-":
                line = line[:i]
                break
            i += 1
        out_lines.append(line)
    return "\n".join(out_lines)


class Database:
    """
    Manages a single SQLite connection with WAL mode and foreign keys enabled.

    Usage:
        db = Database(Path("data/olympus.db"))
        db.initialize()          # idempotent — safe on every startup
        rows = db.query("SELECT * FROM trades WHERE symbol = ?", ("AAPL",))
        db.close()

    Thread-safety: an RLock guards connection access, so the connection is safe
    to share across threads under the single-writer model.
    """

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None
        self._lock = threading.RLock()
        logger.debug("Database created (path=%s)", db_path)

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    def connect(self) -> sqlite3.Connection:
        """
        Return the database connection, creating it on first call. Idempotent.

        Configured with WAL journal mode, foreign_keys = ON, Row factory
        (dict-style access), and PARSE_DECLTYPES.
        """
        with self._lock:
            if self._conn is None:
                self._db_path.parent.mkdir(parents=True, exist_ok=True)
                self._conn = sqlite3.connect(
                    str(self._db_path),
                    check_same_thread=False,
                    detect_types=sqlite3.PARSE_DECLTYPES,
                )
                self._conn.row_factory = sqlite3.Row
                self._conn.execute("PRAGMA journal_mode = WAL")
                self._conn.execute("PRAGMA foreign_keys = ON")
                logger.debug("SQLite connection opened (path=%s)", self._db_path)
            return self._conn

    def initialize(self) -> None:
        """
        Read schema.sql and execute it against the database. Idempotent —
        CREATE TABLE/INDEX IF NOT EXISTS everywhere; views are dropped and
        recreated. Safe to call on every startup.
        """
        schema_sql = _SCHEMA_PATH.read_text(encoding="utf-8")
        conn = self.connect()

        # Execute each statement individually. executescript() does an implicit
        # COMMIT and disables isolation, so we split on ';' instead. (The schema
        # deliberately contains no triggers, whose bodies would break this split.)
        # Strip '--' line comments first, so a ';' inside a comment can't split a
        # statement in two.
        sql_no_comments = _strip_sql_comments(schema_sql)
        with self._lock:
            statements = [s.strip() for s in sql_no_comments.split(";") if s.strip()]
            view_statements = [
                stmt for stmt in statements
                if "CREATE VIEW IF NOT EXISTS" in stmt.upper()
            ]
            base_statements = [
                stmt for stmt in statements
                if "CREATE VIEW IF NOT EXISTS" not in stmt.upper()
            ]
            for stmt in base_statements:
                try:
                    conn.execute(stmt)
                except sqlite3.OperationalError as exc:
                    logger.warning("Schema statement warning: %s | stmt=%.60s", exc, stmt)
            # Drop then recreate views so their definitions can evolve freely.
            for view_name in _REFRESHABLE_VIEWS:
                self._execute_ddl("DROP VIEW IF EXISTS {identifier}", view_name)
            for stmt in view_statements:
                try:
                    conn.execute(stmt)
                except sqlite3.OperationalError as exc:
                    logger.warning("View refresh warning: %s | stmt=%.60s", exc, stmt)
            conn.commit()

        tables = self.query("SELECT COUNT(*) AS n FROM sqlite_master WHERE type='table'")
        indexes = self.query("SELECT COUNT(*) AS n FROM sqlite_master WHERE type='index'")
        views = self.query("SELECT COUNT(*) AS n FROM sqlite_master WHERE type='view'")
        logger.info(
            "Database initialized — %d tables, %d indexes, %d views (path=%s)",
            tables[0]["n"] if tables else 0,
            indexes[0]["n"] if indexes else 0,
            views[0]["n"] if views else 0,
            self._db_path,
        )

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute a single statement and commit. Returns the cursor."""
        conn = self.connect()
        logger.debug("execute: %.80s", sql.strip())
        with self._lock:
            cur = conn.execute(sql, params)
            conn.commit()
        return cur

    def _execute_ddl(self, sql_template: str, identifier: str) -> sqlite3.Cursor:
        """Execute DDL with a validated identifier (guards against injection)."""
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", identifier):
            raise ValueError(f"Invalid identifier: {identifier}")
        return self.execute(sql_template.format(identifier=identifier))

    def executemany(self, sql: str, params_list: list) -> int:
        """Execute a statement for each item in params_list in one transaction."""
        if not params_list:
            return 0
        conn = self.connect()
        logger.debug("executemany (%d rows): %.80s", len(params_list), sql.strip())
        with self._lock:
            cur = conn.executemany(sql, params_list)
            conn.commit()
        return cur.rowcount

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    def query(self, sql: str, params: tuple = ()) -> list[dict]:
        """Execute a SELECT and return all rows as a list of dicts."""
        conn = self.connect()
        logger.debug("query: %.80s", sql.strip())
        with self._lock:
            cur = conn.execute(sql, params)
            rows = cur.fetchall()
        return [dict(row) for row in rows]

    def query_one(self, sql: str, params: tuple = ()) -> Optional[dict]:
        """Execute a SELECT returning at most one row as a dict, or None."""
        conn = self.connect()
        with self._lock:
            cur = conn.execute(sql, params)
            row = cur.fetchone()
        return dict(row) if row is not None else None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Close the database connection."""
        with self._lock:
            if self._conn is not None:
                self._conn.close()
                self._conn = None
                logger.debug("SQLite connection closed (path=%s)", self._db_path)
