"""FTS5 全文索引服务"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from loguru import logger

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DB_PATH = DATA_DIR / "gtcs.db"

FTS5_CONFIGS = [
    {
        "name": "tariff_fts",
        "source": "national_tariff_line",
        "columns": ("local_code", "description_en", "description_cn"),
    },
    {
        "name": "screening_fts",
        "source": "screening_list",
        "columns": ("name", "name_cn", "program", "reason"),
    },
]


def ensure_fts_indexes():
    """Create/populate FTS5 indexes using raw sqlite3 connection."""
    try:
        db = sqlite3.connect(str(DB_PATH))
        db.execute("PRAGMA journal_mode=WAL")
        for cfg in FTS5_CONFIGS:
            fts_name = cfg["name"]
            src = cfg["source"]
            cols = cfg["columns"]

            existing = db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (fts_name,),
            ).fetchone()
            if existing:
                count = db.execute(f"SELECT COUNT(*) FROM {fts_name}").fetchone()[0]
                if count > 0:
                    logger.info(f"{fts_name}: {count} entries, already indexed")
                    continue
                db.execute(f"DROP TABLE IF EXISTS {fts_name}")

            col_def = ", ".join(cols)
            db.execute(
                f"CREATE VIRTUAL TABLE {fts_name} USING fts5({col_def}, tokenize='unicode61 remove_diacritics 2')"
            )

            cnames = ", ".join(f"COALESCE({c}, '')" for c in cols)
            rows = db.execute(f"SELECT {cnames} FROM {src}").fetchall()

            placeholders = ", ".join("?" for _ in cols)
            count = 0
            batch = []
            for row in rows:
                values = tuple(str(v or "") for v in row)
                if any(v.strip() for v in values):
                    batch.append(values)
                    count += 1
                if len(batch) >= 500:
                    db.executemany(
                        f"INSERT INTO {fts_name}({col_def}) VALUES({placeholders})",
                        batch,
                    )
                    batch = []
            if batch:
                db.executemany(
                    f"INSERT INTO {fts_name}({col_def}) VALUES({placeholders})",
                    batch,
                )
            db.commit()
            logger.success(f"{fts_name}: {count} entries indexed")
        db.close()
    except Exception as e:
        logger.warning(f"FTS5 initialization failed: {e}")


def fts_search(index_name: str, query: str, limit: int = 20) -> list:
    """搜索 FTS5 索引"""
    try:
        db = sqlite3.connect(str(DB_PATH))
        if index_name == "tariff_fts":
            sql = """
                SELECT ntl.id, ntl.local_code, ntl.description_en,
                       c.iso2, c.name_cn as country_name
                FROM tariff_fts
                JOIN national_tariff_line ntl ON ntl.rowid = tariff_fts.rowid
                JOIN country c ON c.id = ntl.country_id
                WHERE tariff_fts MATCH ?
                ORDER BY rank
                LIMIT ?
            """
            rows = db.execute(sql, (query, limit)).fetchall()
            cols = ["id", "local_code", "description_en", "iso2", "country_name"]
        elif index_name == "screening_fts":
            sql = """
                SELECT sl.id, sl.name, sl.name_cn, sl.list_type,
                       sl.country, sl.program, sl.reason
                FROM screening_fts
                JOIN screening_list sl ON sl.rowid = screening_fts.rowid
                WHERE screening_fts MATCH ?
                ORDER BY rank
                LIMIT ?
            """
            rows = db.execute(sql, (query, limit)).fetchall()
            cols = ["id", "name", "name_cn", "list_type", "country", "program", "reason"]
        else:
            return []
        results = [dict(zip(cols, row)) for row in rows]
        db.close()
        return results
    except Exception as e:
        logger.warning(f"FTS search error: {e}")
        return []
