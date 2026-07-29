"""
Daily per-IP token budget for LLM-costing endpoints ("testing limit").

Tracked per-IP rather than per-session-cookie: a cookie is trivially cleared
to reset a session-scoped limit, while an IP is a meaningfully higher bar for
a "please don't blow up my API bill" style limit. It's a deterrent, not a
hard security boundary - a VPN or shared IP can still get around it.

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
_usage: Dict[Tuple[str, str], int] = {}  # (ip, iso date) -> tokens used today


def _key(ip: str) -> Tuple[str, str]:
    return (ip, date.today().isoformat())


def used(ip: str) -> int:
    with _lock:
        return _usage.get(_key(ip), 0)


def remaining(ip: str) -> int:
    with _lock:
        return max(0, DAILY_TOKEN_BUDGET - _usage.get(_key(ip), 0))


def has_budget(ip: str) -> bool:
    return remaining(ip) > 0


def charge(ip: str, tokens: int) -> None:
    """Add to today's usage for this IP. No-op for non-positive amounts."""
    if tokens <= 0:
        return
    with _lock:
        k = _key(ip)
        _usage[k] = _usage.get(k, 0) + tokens
