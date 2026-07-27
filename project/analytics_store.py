"""
Analytics store: persists AI Arena round results (which traits played, how
long each reply was, which side the user preferred) to a local SQLite file so
the /analytics page can show aggregate, global stats to any visitor.

Only structural data is stored - never prompt text, reply text, IP addresses,
or session/account identifiers. See templates/privacy.html for the disclosure.
"""

import json
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, List, Optional

import glicko

DB_PATH = Path(__file__).parent / "data" / "arena.db"

# Minimum number of times a trait (or trait combo) must have appeared in a
# *voted* round before it's included in the leaderboards - keeps single-shot
# noise off the charts.
MIN_SAMPLE_SIZE = 3

_init_lock = threading.Lock()
_initialized = False


@contextmanager
def _connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=5)
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Create the schema if it doesn't exist yet. Safe to call repeatedly."""
    global _initialized
    if _initialized:
        return
    with _init_lock:
        if _initialized:
            return
        with _connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS arena_rounds (
                    round_id      INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
                    voted_option  TEXT CHECK (voted_option IN ('A', 'B'))
                );

                CREATE TABLE IF NOT EXISTS arena_options (
                    id               INTEGER PRIMARY KEY AUTOINCREMENT,
                    round_id         INTEGER NOT NULL REFERENCES arena_rounds(round_id),
                    option_label     TEXT NOT NULL CHECK (option_label IN ('A', 'B')),
                    traits_json      TEXT NOT NULL,
                    traits_key       TEXT NOT NULL,
                    response_length  INTEGER NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_arena_options_round ON arena_options(round_id);
                CREATE INDEX IF NOT EXISTS idx_arena_options_traits_key ON arena_options(traits_key);
                """
            )
        _initialized = True


def _traits_key(traits: List[str]) -> str:
    return ",".join(sorted(traits))


def record_round(traits_a: List[str], reply_a: str, traits_b: List[str], reply_b: str) -> int:
    """Persist a freshly generated round (not yet voted on). Returns round_id."""
    with _connect() as conn:
        cur = conn.execute("INSERT INTO arena_rounds DEFAULT VALUES")
        round_id = cur.lastrowid

        for label, traits, reply in (("A", traits_a, reply_a), ("B", traits_b, reply_b)):
            conn.execute(
                """
                INSERT INTO arena_options
                    (round_id, option_label, traits_json, traits_key, response_length)
                VALUES (?, ?, ?, ?, ?)
                """,
                (round_id, label, json.dumps(traits), _traits_key(traits), len(reply)),
            )

        return round_id


def record_vote(round_id: int, option: str) -> bool:
    """
    Record which option a user preferred for a round.

    Returns True if the vote was recorded, False if the round doesn't exist
    or has already been voted on (first vote wins).
    """
    if option not in ("A", "B"):
        return False

    with _connect() as conn:
        cur = conn.execute(
            "UPDATE arena_rounds SET voted_option = ? WHERE round_id = ? AND voted_option IS NULL",
            (option, round_id),
        )
        return cur.rowcount > 0


def get_analytics_summary() -> Dict:
    """
    Aggregate every voted round into the stats the /analytics page needs:
    overall totals, per-trait Glicko rating / win rate / usage / avg response
    length, and a leaderboard of the top trait combinations.
    """
    with _connect() as conn:
        conn.row_factory = sqlite3.Row

        total_rounds = conn.execute("SELECT COUNT(*) AS n FROM arena_rounds").fetchone()["n"]
        total_votes = conn.execute(
            "SELECT COUNT(*) AS n FROM arena_rounds WHERE voted_option IS NOT NULL"
        ).fetchone()["n"]

        rows = conn.execute(
            """
            SELECT o.traits_json, o.traits_key, o.response_length,
                   (o.option_label = r.voted_option) AS won
            FROM arena_options o
            JOIN arena_rounds r ON r.round_id = o.round_id
            WHERE r.voted_option IS NOT NULL
            """
        ).fetchall()

        # Round-grouped (not per-option) and chronologically ordered, since
        # Glicko needs both sides of each match together, processed as
        # successive rating periods - see glicko.compute_ratings.
        round_rows = conn.execute(
            """
            SELECT r.round_id, r.voted_option, o.option_label, o.traits_json
            FROM arena_rounds r
            JOIN arena_options o ON o.round_id = r.round_id
            WHERE r.voted_option IS NOT NULL
            ORDER BY r.round_id ASC, o.option_label ASC
            """
        ).fetchall()

    per_trait: Dict[str, Dict] = {}
    per_combo: Dict[str, Dict] = {}
    total_length_sum = 0

    for row in rows:
        traits = json.loads(row["traits_json"])
        won = bool(row["won"])
        length = row["response_length"]
        total_length_sum += length

        combo_key = row["traits_key"]
        combo = per_combo.setdefault(
            combo_key, {"traits": traits, "times_used": 0, "times_won": 0}
        )
        combo["times_used"] += 1
        combo["times_won"] += 1 if won else 0

        for trait in traits:
            entry = per_trait.setdefault(
                trait, {"name": trait, "times_used": 0, "times_won": 0, "_length_sum": 0}
            )
            entry["times_used"] += 1
            entry["times_won"] += 1 if won else 0
            entry["_length_sum"] += length

    glicko_rounds: List[glicko.Round] = []
    pending_traits: Dict[str, List[str]] = {}
    for row in round_rows:
        pending_traits[row["option_label"]] = json.loads(row["traits_json"])
        if row["option_label"] == "B":
            glicko_rounds.append((pending_traits["A"], pending_traits["B"], row["voted_option"]))
            pending_traits = {}
    ratings = glicko.compute_ratings(glicko_rounds)

    trait_stats = []
    for entry in per_trait.values():
        if entry["times_used"] < MIN_SAMPLE_SIZE:
            continue
        rating_info = ratings.get(entry["name"], {"rating": glicko.DEFAULT_RATING, "rd": glicko.DEFAULT_RD})
        trait_stats.append(
            {
                "name": entry["name"],
                "times_used": entry["times_used"],
                "times_won": entry["times_won"],
                "win_rate": entry["times_won"] / entry["times_used"],
                "avg_response_length": entry["_length_sum"] / entry["times_used"],
                "glicko_rating": rating_info["rating"],
                "glicko_rd": rating_info["rd"],
            }
        )
    trait_stats.sort(key=lambda t: t["glicko_rating"], reverse=True)

    combo_stats = []
    for key, entry in per_combo.items():
        if entry["times_used"] < MIN_SAMPLE_SIZE:
            continue
        combo_stats.append(
            {
                "traits": entry["traits"],
                "label": " + ".join(sorted(entry["traits"])),
                "times_used": entry["times_used"],
                "times_won": entry["times_won"],
                "win_rate": entry["times_won"] / entry["times_used"],
            }
        )
    combo_stats.sort(key=lambda c: (c["win_rate"], c["times_used"]), reverse=True)

    return {
        "total_rounds": total_rounds,
        "total_votes": total_votes,
        "distinct_traits_used": len(per_trait),
        "overall_avg_response_length": (total_length_sum / len(rows)) if rows else 0,
        "traits": trait_stats,
        # No hard cap here anymore - the /analytics page paginates client-side,
        # same as the trait charts, so there's no need to silently truncate.
        "top_combos": combo_stats,
        "min_sample_size": MIN_SAMPLE_SIZE,
    }
