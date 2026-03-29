"""
Apply SQL files statement-by-statement. psycopg2's cursor.execute() runs only ONE query per call,
so passing a whole .sql file silently misbehaves. Also run extensions even when base schema already exists.
"""

from __future__ import annotations

import logging
import os
import re

logger = logging.getLogger(__name__)


def _split_sql_statements(sql: str) -> list[str]:
    """Split on semicolons outside of single-quoted strings (good enough for our schema files)."""
    # Drop full-line SQL comments so they are not merged into the first real statement
    lines = [ln for ln in sql.splitlines() if ln.strip() and not ln.strip().startswith("--")]
    sql = "\n".join(lines)

    out: list[str] = []
    buf: list[str] = []
    in_single = False
    i = 0
    while i < len(sql):
        c = sql[i]
        if c == "'" and (i == 0 or sql[i - 1] != "\\"):
            in_single = not in_single
            buf.append(c)
            i += 1
            continue
        if c == ";" and not in_single:
            stmt = "".join(buf).strip()
            if stmt:
                out.append(stmt)
            buf = []
            i += 1
            continue
        buf.append(c)
        i += 1
    tail = "".join(buf).strip()
    if tail:
        out.append(tail)
    # Strip block comments /* */
    cleaned = []
    for s in out:
        s = re.sub(r"/\*.*?\*/", "", s, flags=re.DOTALL).strip()
        lines = [ln for ln in s.splitlines() if ln.strip() and not ln.strip().startswith("--")]
        joined = "\n".join(lines).strip()
        if joined:
            cleaned.append(joined)
    return cleaned


def run_sql_file(conn, path: str) -> None:
    if not os.path.isfile(path):
        logger.warning("SQL file missing: %s", path)
        return
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    cur = conn.cursor()
    try:
        for stmt in _split_sql_statements(text):
            try:
                cur.execute(stmt)
            except Exception as e:
                logger.warning("SQL statement skipped or failed (%s): %s", path, e)
    finally:
        cur.close()


def bootstrap_database(database_url: str) -> None:
    try:
        import psycopg2  # type: ignore
    except ImportError:
        logger.warning("psycopg2 not installed; skipping DB bootstrap")
        return
    base = os.path.dirname(os.path.abspath(__file__))
    schema_path = os.path.join(base, "schema.sql")
    ext_path = os.path.join(base, "schema_extensions.sql")
    try:
        conn = psycopg2.connect(database_url)
        conn.autocommit = True
        try:
            run_sql_file(conn, schema_path)
            run_sql_file(conn, ext_path)
        finally:
            conn.close()
    except Exception as e:
        logger.warning("DB bootstrap connection failed: %s", e)
