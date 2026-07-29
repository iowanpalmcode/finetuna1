"""
Analytics store: persists AI Arena round results (which traits played, how
long each reply was, which side the user preferred) to a Postgres database
(Neon) so the /analytics page can show aggregate, global stats to any
visitor - and so those stats survive the app's process restarting or
spinning down, unlike a local SQLite file would on most free hosting tiers.

Only structural data is stored - never prompt text, reply text, IP addresses,
or session/account identifiers. See templates/privacy.html for the disclosure.
"""

import json
import os
import threading
from contextlib import contextmanager
from typing import Dict, List, Optional

import psycopg2
import psycopg2.extras

import glicko

DATABASE_URL = os.environ.get("DATABASE_URL")

# Minimum number of times a trait (or trait combo) must have appeared in a
# *voted* round before it's included in the leaderboards - keeps single-shot
# noise off the charts.
MIN_SAMPLE_SIZE = 3

# How many top-rated traits get a rating-history series in the summary (also
# the radar chart's axis count) - keeps both bounded as the trait pool grows.
TRAIT_HISTORY_LIMIT = 10

MAX_FEEDBACK_LENGTH = 1000

_init_lock = threading.Lock()
_initialized = False


class AnalyticsNotConfiguredError(RuntimeError):
    pass


@contextmanager
def _connect():
    if not DATABASE_URL:
        raise AnalyticsNotConfiguredError(
            "DATABASE_URL is not configured. Add a Neon Postgres connection "
            "string to project/.env (or the Render dashboard) to enable Arena "
            "analytics."
        )
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
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
        if not DATABASE_URL:
            # Don't crash the whole app at import time over this - routes
            # that actually touch analytics will raise a clear error instead.
            print("[analytics_store] DATABASE_URL not set - Arena analytics disabled until it is.")
            return
        with _connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS arena_rounds (
                        round_id      SERIAL PRIMARY KEY,
                        created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
                        voted_option  TEXT CHECK (voted_option IN ('A', 'B'))
                    );

                    CREATE TABLE IF NOT EXISTS arena_options (
                        id               SERIAL PRIMARY KEY,
                        round_id         INTEGER NOT NULL REFERENCES arena_rounds(round_id),
                        option_label     TEXT NOT NULL CHECK (option_label IN ('A', 'B')),
                        traits_json      TEXT NOT NULL,
                        traits_key       TEXT NOT NULL,
                        response_length  INTEGER NOT NULL
                    );

                    CREATE INDEX IF NOT EXISTS idx_arena_options_round ON arena_options(round_id);
                    CREATE INDEX IF NOT EXISTS idx_arena_options_traits_key ON arena_options(traits_key);

                    CREATE TABLE IF NOT EXISTS arena_feedback (
                        id            SERIAL PRIMARY KEY,
                        round_id      INTEGER NOT NULL UNIQUE REFERENCES arena_rounds(round_id),
                        voted_option  TEXT NOT NULL CHECK (voted_option IN ('A', 'B')),
                        feedback_text TEXT NOT NULL,
                        created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
                    );
                    """
                )
        _initialized = True


def ping() -> None:
    """
    Trivial round-trip that does no real work - just opens a connection and
    runs SELECT 1. Used by ui_server's /api/warmup, which the frontend fires
    on page load to nudge a cold Neon compute endpoint (it has its own
    scale-to-zero behavior, separate from Render's) awake before the user's
    first real request needs it, instead of eating that latency there.
    """
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")


def _traits_key(traits: List[str]) -> str:
    return ",".join(sorted(traits))


def record_round(traits_a: List[str], reply_a: str, traits_b: List[str], reply_b: str) -> int:
    """Persist a freshly generated round (not yet voted on). Returns round_id."""
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO arena_rounds DEFAULT VALUES RETURNING round_id")
            round_id = cur.fetchone()["round_id"]

            for label, traits, reply in (("A", traits_a, reply_a), ("B", traits_b, reply_b)):
                cur.execute(
                    """
                    INSERT INTO arena_options
                        (round_id, option_label, traits_json, traits_key, response_length)
                    VALUES (%s, %s, %s, %s, %s)
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
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE arena_rounds SET voted_option = %s WHERE round_id = %s AND voted_option IS NULL",
                (option, round_id),
            )
            return cur.rowcount > 0


def record_feedback(round_id: int, feedback_text: str) -> bool:
    """
    Record open-ended "what made A/B better" feedback for a round, in its own
    table (structural analytics stays separate from free-text user input).

    Returns True if saved, False if the round doesn't exist, hasn't been
    voted on yet, or already has feedback (one submission per round).
    """
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO arena_feedback (round_id, voted_option, feedback_text)
                SELECT round_id, voted_option, %s
                FROM arena_rounds
                WHERE round_id = %s AND voted_option IS NOT NULL
                ON CONFLICT (round_id) DO NOTHING
                """,
                (feedback_text, round_id),
            )
            return cur.rowcount > 0


def _fetch_glicko_rounds(cur) -> List[glicko.Round]:
    """
    Every voted round as (traits_a, traits_b, voted_option), round-grouped
    (not per-option) and chronologically ordered, since Glicko needs both
    sides of each match together, processed as successive rating periods -
    see glicko.compute_ratings.
    """
    cur.execute(
        """
        SELECT r.round_id, r.voted_option, o.option_label, o.traits_json
        FROM arena_rounds r
        JOIN arena_options o ON o.round_id = r.round_id
        WHERE r.voted_option IS NOT NULL
        ORDER BY r.round_id ASC, o.option_label ASC
        """
    )
    round_rows = cur.fetchall()

    glicko_rounds: List[glicko.Round] = []
    pending_traits: Dict[str, List[str]] = {}
    for row in round_rows:
        pending_traits[row["option_label"]] = json.loads(row["traits_json"])
        if row["option_label"] == "B":
            glicko_rounds.append((pending_traits["A"], pending_traits["B"], row["voted_option"]))
            pending_traits = {}
    return glicko_rounds


def get_trait_ratings() -> Dict[str, Dict[str, float]]:
    """
    Current Glicko rating/rd for every trait that has appeared in at least
    one voted round, unfiltered by MIN_SAMPLE_SIZE - used to steer which
    traits Arena rounds pick next (see ui_server._select_arena_teams), not
    just to display a leaderboard.
    """
    with _connect() as conn:
        with conn.cursor() as cur:
            glicko_rounds = _fetch_glicko_rounds(cur)
    return glicko.compute_ratings(glicko_rounds)


def get_analytics_summary() -> Dict:
    """
    Aggregate every voted round into the stats the /analytics page needs:
    overall totals, per-trait Glicko rating / win rate / usage / avg response
    length, a leaderboard of the top trait combinations, and each top
    trait's rating history over time.
    """
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS n FROM arena_rounds")
            total_rounds = cur.fetchone()["n"]

            cur.execute("SELECT COUNT(*) AS n FROM arena_rounds WHERE voted_option IS NOT NULL")
            total_votes = cur.fetchone()["n"]

            cur.execute(
                """
                SELECT o.traits_json, o.traits_key, o.response_length,
                       (o.option_label = r.voted_option) AS won
                FROM arena_options o
                JOIN arena_rounds r ON r.round_id = o.round_id
                WHERE r.voted_option IS NOT NULL
                """
            )
            rows = cur.fetchall()

            glicko_rounds = _fetch_glicko_rounds(cur)

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

    ratings, history = glicko.compute_ratings_with_history(glicko_rounds)

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

    # Only the top traits (by current rating) get a history series - matches
    # the radar chart's axis count, and keeps the payload from growing
    # unbounded as more distinct traits accumulate history over time.
    trait_history = {
        t["name"]: history[t["name"]]
        for t in trait_stats[:TRAIT_HISTORY_LIMIT]
        if t["name"] in history
    }

    return {
        "total_rounds": total_rounds,
        "total_votes": total_votes,
        "distinct_traits_used": len(per_trait),
        "overall_avg_response_length": (total_length_sum / len(rows)) if rows else 0,
        "traits": trait_stats,
        # No hard cap here anymore - the /analytics page paginates client-side,
        # same as the trait charts, so there's no need to silently truncate.
        "top_combos": combo_stats,
        "trait_history": trait_history,
        "min_sample_size": MIN_SAMPLE_SIZE,
    }
