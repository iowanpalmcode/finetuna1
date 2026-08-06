"""
Daily per-browser token budget for LLM-costing endpoints ("testing limit").

Tracked per-browser (the same signed session-cookie uid ui_server.py's
Flask-Limiter uses), not per-IP: an IP is often shared by many unrelated
users (NAT/CGNAT/VPN/office network), so one heavy user could exhaust the
budget for everyone else behind that IP. A cookie is trivially cleared to
reset the limit, but that's an accepted tradeoff here - this is a deterrent
against accidentally blowing up the API bill, not a hard security boundary.

In-memory and process-local, same tradeoff Flask-Limiter already makes for
its own rate limiting (ui_server.py's `storage_uri="memory://"`) - fine for a
single dev/demo instance. Resets naturally at midnight because the bucket key
includes today's date; nothing needs to run on a schedule to "reset" it.
"""

import threading
from datetime import date
from typing import Dict, Tuple

# A typical text round (1 prompt + 2 replies, since every Arena round makes
# two LLM calls) costs roughly 800-1000 tokens combined => ~20 rounds/day.
# An image round costs far more (image encoding + 2 replies) => roughly
# 6000-7000 tokens => ~3 rounds/day. Both land near this one shared budget,
# which is intentionally a single pool that text and image rounds both draw
# from ("whichever works" - not two separate counters).
DAILY_TOKEN_BUDGET = 20000

_lock = threading.Lock()
_usage: Dict[Tuple[str, str], int] = {}  # (browser uid, iso date) -> tokens used today


def _key(uid: str) -> Tuple[str, str]:
    return (uid, date.today().isoformat())


def used(uid: str) -> int:
    with _lock:
        return _usage.get(_key(uid), 0)


def remaining(uid: str) -> int:
    with _lock:
        return max(0, DAILY_TOKEN_BUDGET - _usage.get(_key(uid), 0))


def has_budget(uid: str) -> bool:
    return remaining(uid) > 0


def charge(uid: str, tokens: int) -> None:
    """Add to today's usage for this browser. No-op for non-positive amounts."""
    if tokens <= 0:
        return
    with _lock:
        k = _key(uid)
        _usage[k] = _usage.get(k, 0) + tokens
