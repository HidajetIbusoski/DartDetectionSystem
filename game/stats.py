"""
SQLite database for game history and player statistics.
Persists game results, individual dart throws, and player stats across sessions.
"""

import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass

from config import DATA_DIR

logger = logging.getLogger(__name__)

DB_PATH = DATA_DIR / "darts.db"


@dataclass
class GameRecord:
    """A completed game record."""
    id: int
    mode: str
    players: list[str]
    winner: str | None
    start_time: str
    end_time: str
    data: dict  # Full game data snapshot


@dataclass
class ThrowRecord:
    """A single dart throw record."""
    id: int
    game_id: int
    player_name: str
    turn_number: int
    dart_number: int
    score_value: int
    score_label: str
    multiplier: int
    sector: int
    timestamp: str


class Database:
    """
    SQLite database manager for persisting game data.
    Auto-creates tables on first use.
    """

    def __init__(self, db_path: Path | str | None = None):
        self.db_path = str(db_path or DB_PATH)
        self._conn: sqlite3.Connection | None = None
        self._ensure_tables()

    def _connect(self) -> sqlite3.Connection:
        """Get or create a database connection."""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
        return self._conn

    def _ensure_tables(self):
        """Create tables if they don't exist."""
        conn = self._connect()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mode TEXT NOT NULL,
                players TEXT NOT NULL,
                winner TEXT,
                start_time TEXT NOT NULL,
                end_time TEXT,
                data TEXT
            );

            CREATE TABLE IF NOT EXISTS throws (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id INTEGER NOT NULL,
                player_name TEXT NOT NULL,
                turn_number INTEGER NOT NULL,
                dart_number INTEGER NOT NULL,
                score_value INTEGER NOT NULL,
                score_label TEXT NOT NULL,
                multiplier INTEGER NOT NULL DEFAULT 1,
                sector INTEGER NOT NULL DEFAULT 0,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS player_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_name TEXT NOT NULL UNIQUE,
                games_played INTEGER NOT NULL DEFAULT 0,
                games_won INTEGER NOT NULL DEFAULT 0,
                total_darts INTEGER NOT NULL DEFAULT 0,
                total_score INTEGER NOT NULL DEFAULT 0,
                highest_checkout INTEGER NOT NULL DEFAULT 0,
                num_180s INTEGER NOT NULL DEFAULT 0,
                num_ton_plus INTEGER NOT NULL DEFAULT 0,
                doubles_attempted INTEGER NOT NULL DEFAULT 0,
                doubles_hit INTEGER NOT NULL DEFAULT 0,
                best_three_dart_avg REAL NOT NULL DEFAULT 0.0,
                last_played TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_throws_game ON throws(game_id);
            CREATE INDEX IF NOT EXISTS idx_throws_player ON throws(player_name);
            CREATE INDEX IF NOT EXISTS idx_games_mode ON games(mode);
        """)
        conn.commit()
        logger.info(f"Database initialized at {self.db_path}")

    # ── Game CRUD ─────────────────────────────────────────────────────────

    def start_game(self, mode: str, player_names: list[str]) -> int:
        """Record a new game start. Returns the game ID."""
        conn = self._connect()
        cursor = conn.execute(
            "INSERT INTO games (mode, players, start_time) VALUES (?, ?, ?)",
            (mode, json.dumps(player_names), datetime.now().isoformat())
        )
        conn.commit()
        game_id = cursor.lastrowid
        logger.info(f"Game {game_id} started: {mode}")
        return game_id

    def end_game(self, game_id: int, winner: str | None = None,
                 game_data: dict | None = None):
        """Record game completion."""
        conn = self._connect()
        conn.execute(
            "UPDATE games SET winner = ?, end_time = ?, data = ? WHERE id = ?",
            (winner, datetime.now().isoformat(),
             json.dumps(game_data) if game_data else None, game_id)
        )
        conn.commit()

    def record_throw(self, game_id: int, player_name: str,
                     turn_number: int, dart_number: int,
                     score_value: int, score_label: str,
                     multiplier: int = 1, sector: int = 0):
        """Record a single dart throw."""
        conn = self._connect()
        conn.execute(
            """INSERT INTO throws
               (game_id, player_name, turn_number, dart_number,
                score_value, score_label, multiplier, sector, timestamp)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (game_id, player_name, turn_number, dart_number,
             score_value, score_label, multiplier, sector,
             datetime.now().isoformat())
        )
        conn.commit()

    # ── Player Stats ──────────────────────────────────────────────────────

    def update_player_stats(self, player_name: str, won: bool = False,
                            darts: int = 0, score: int = 0,
                            checkout: int = 0, num_180s: int = 0,
                            ton_plus: int = 0, doubles_att: int = 0,
                            doubles_hit: int = 0, three_dart_avg: float = 0):
        """Update aggregated player statistics."""
        conn = self._connect()

        # Upsert player stats
        conn.execute("""
            INSERT INTO player_stats
                (player_name, games_played, games_won, total_darts, total_score,
                 highest_checkout, num_180s, num_ton_plus,
                 doubles_attempted, doubles_hit, best_three_dart_avg, last_played)
            VALUES (?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(player_name) DO UPDATE SET
                games_played = games_played + 1,
                games_won = games_won + ?,
                total_darts = total_darts + ?,
                total_score = total_score + ?,
                highest_checkout = MAX(highest_checkout, ?),
                num_180s = num_180s + ?,
                num_ton_plus = num_ton_plus + ?,
                doubles_attempted = doubles_attempted + ?,
                doubles_hit = doubles_hit + ?,
                best_three_dart_avg = MAX(best_three_dart_avg, ?),
                last_played = ?
        """, (
            player_name,
            1 if won else 0, darts, score, checkout,
            num_180s, ton_plus, doubles_att, doubles_hit,
            three_dart_avg, datetime.now().isoformat(),
            # ON CONFLICT values
            1 if won else 0, darts, score, checkout,
            num_180s, ton_plus, doubles_att, doubles_hit,
            three_dart_avg, datetime.now().isoformat()
        ))
        conn.commit()

    def get_player_stats(self, player_name: str) -> dict | None:
        """Get stats for a specific player."""
        conn = self._connect()
        row = conn.execute(
            "SELECT * FROM player_stats WHERE player_name = ?",
            (player_name,)
        ).fetchone()
        return dict(row) if row else None

    def get_all_player_stats(self) -> list[dict]:
        """Get stats for all players, sorted by games played."""
        conn = self._connect()
        rows = conn.execute(
            "SELECT * FROM player_stats ORDER BY games_played DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    # ── History & Queries ─────────────────────────────────────────────────

    def get_recent_games(self, limit: int = 20) -> list[dict]:
        """Get recent game records."""
        conn = self._connect()
        rows = conn.execute(
            "SELECT * FROM games ORDER BY id DESC LIMIT ?",
            (limit,)
        ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["players"] = json.loads(d["players"]) if d["players"] else []
            result.append(d)
        return result

    def get_game_throws(self, game_id: int) -> list[dict]:
        """Get all throws for a specific game."""
        conn = self._connect()
        rows = conn.execute(
            "SELECT * FROM throws WHERE game_id = ? ORDER BY turn_number, dart_number",
            (game_id,)
        ).fetchall()
        return [dict(r) for r in rows]

    def get_player_hit_distribution(self, player_name: str) -> dict[int, int]:
        """Get sector hit distribution for a player (for heatmap)."""
        conn = self._connect()
        rows = conn.execute(
            """SELECT sector, COUNT(*) as count
               FROM throws WHERE player_name = ? AND sector > 0
               GROUP BY sector ORDER BY sector""",
            (player_name,)
        ).fetchall()
        return {r["sector"]: r["count"] for r in rows}

    def get_player_averages_over_time(self, player_name: str,
                                      limit: int = 50) -> list[dict]:
        """Get per-game averages over time for a player."""
        conn = self._connect()
        rows = conn.execute(
            """SELECT g.id, g.mode, g.start_time,
                      SUM(t.score_value) as total_score,
                      COUNT(t.id) as total_darts,
                      ROUND(CAST(SUM(t.score_value) AS REAL) / COUNT(t.id) * 3, 1) as three_dart_avg
               FROM throws t
               JOIN games g ON t.game_id = g.id
               WHERE t.player_name = ?
               GROUP BY g.id
               ORDER BY g.id DESC
               LIMIT ?""",
            (player_name, limit)
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Cleanup ───────────────────────────────────────────────────────────

    def close(self):
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def clear_all(self):
        """Clear all data (use with caution)."""
        conn = self._connect()
        conn.executescript("""
            DELETE FROM throws;
            DELETE FROM games;
            DELETE FROM player_stats;
        """)
        conn.commit()
        logger.warning("All database data cleared")
