from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional


class MetadataDB:
    """Lightweight SQLite metadata for runs, manifests, and orders."""

    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(path), check_same_thread=False)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS manifests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT,
                payload TEXT
            )
            """
        )
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT,
                as_of TEXT,
                signal TEXT,
                payload TEXT
            )
            """
        )
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                idempotency_key TEXT UNIQUE,
                symbol TEXT,
                side TEXT,
                status TEXT,
                payload TEXT
            )
            """
        )
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS positions (
                symbol TEXT PRIMARY KEY,
                quantity REAL,
                avg_price REAL,
                updated_at TEXT DEFAULT (datetime('now'))
            )
            """
        )
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS experiments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT,
                model_version TEXT,
                schema_id TEXT,
                payload TEXT
            )
            """
        )
        self._conn.commit()

    def insert_manifest(self, payload: Dict[str, Any]) -> int:
        cur = self._conn.execute(
            "INSERT INTO manifests (created_at, payload) VALUES (datetime('now'), ?)",
            (json.dumps(payload, default=str),),
        )
        self._conn.commit()
        return int(cur.lastrowid)

    def insert_decision(
        self, symbol: str, as_of: str, signal: str, payload: Dict[str, Any]
    ) -> int:
        cur = self._conn.execute(
            "INSERT INTO decisions (symbol, as_of, signal, payload) VALUES (?,?,?,?)",
            (symbol, as_of, signal, json.dumps(payload, default=str)),
        )
        self._conn.commit()
        return int(cur.lastrowid)

    def recent_decisions(self, symbol: Optional[str] = None, limit: int = 20) -> List[Dict]:
        if symbol:
            rows = self._conn.execute(
                "SELECT symbol, as_of, signal, payload FROM decisions WHERE symbol=? ORDER BY id DESC LIMIT ?",
                (symbol, limit),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT symbol, as_of, signal, payload FROM decisions ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [
            {"symbol": r[0], "as_of": r[1], "signal": r[2], "payload": json.loads(r[3])}
            for r in rows
        ]

    def get_decision(self, decision_id: int) -> Optional[Dict[str, Any]]:
        row = self._conn.execute(
            "SELECT id, symbol, as_of, signal, payload FROM decisions WHERE id=?",
            (decision_id,),
        ).fetchone()
        if not row:
            return None
        return {
            "id": row[0],
            "symbol": row[1],
            "as_of": row[2],
            "signal": row[3],
            "payload": json.loads(row[4]),
        }

    def set_position(self, symbol: str, quantity: float, avg_price: float) -> None:
        self._conn.execute(
            """INSERT INTO positions (symbol, quantity, avg_price)
               VALUES (?,?,?)
               ON CONFLICT(symbol) DO UPDATE SET
                 quantity=excluded.quantity,
                 avg_price=excluded.avg_price,
                 updated_at=datetime('now')""",
            (symbol, quantity, avg_price),
        )
        self._conn.commit()

    def gross_notional(self) -> float:
        row = self._conn.execute(
            "SELECT COALESCE(SUM(ABS(quantity * avg_price)), 0) FROM positions"
        ).fetchone()
        return float(row[0] or 0)

    def positions_max_updated_at(self) -> Optional[str]:
        row = self._conn.execute("SELECT MAX(updated_at) FROM positions").fetchone()
        if not row or row[0] is None:
            return None
        return str(row[0])

    def log_experiment(self, model_version: str, schema_id: str, payload: Dict[str, Any]) -> int:
        cur = self._conn.execute(
            "INSERT INTO experiments (created_at, model_version, schema_id, payload) VALUES (datetime('now'),?,?,?)",
            (model_version, schema_id, json.dumps(payload, default=str)),
        )
        self._conn.commit()
        return int(cur.lastrowid)

    def close(self) -> None:
        self._conn.close()
