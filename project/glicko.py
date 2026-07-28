"""
Minimal Glicko-1 (Glickman, 1999) rating system for AI Arena personality
traits.

Each arena round pits a *team* of 1-3 traits against another team of 1-3
traits - there's no native "team Glicko," so each round is expanded into the
cross product of individual trait-vs-trait games (a trait that happens to
land on both sides in the same round is skipped against itself - nothing
meaningful to rate there), each carrying that round's win/loss outcome.
Rounds are processed as successive Glicko rating periods in chronological
order, so a trait's opponents are judged against up-to-date strength
estimates rather than everyone frozen at the default rating.

This recomputes from scratch over the full history every time it's called
(see analytics_store.get_analytics_summary) - cheap at this app's volume,
and keeps ratings honest even if past votes are ever edited or removed.

Known simplification: RD is not inflated for rating periods where a trait
sees no games (the textbook refinement grows RD toward the ceiling as
periods pass unplayed, to reflect rising uncertainty) - skipped to keep the
batch update simple. Ratings still converge normally for traits that do get
played, and a trait that's barely been seen keeps a high starting RD anyway.
"""

import math
from typing import Dict, List, Tuple

Q = math.log(10) / 400
DEFAULT_RATING = 1500.0
DEFAULT_RD = 350.0
MIN_RD = 30.0
MAX_RD = 350.0

# (traits_a, traits_b, voted_option) for one round, voted_option is 'A' or 'B'.
Round = Tuple[List[str], List[str], str]


def _g(rd: float) -> float:
    return 1.0 / math.sqrt(1.0 + 3.0 * Q ** 2 * rd ** 2 / math.pi ** 2)


def _expected_score(rating: float, opp_rating: float, opp_rd: float) -> float:
    return 1.0 / (1.0 + 10 ** (-_g(opp_rd) * (rating - opp_rating) / 400.0))


def compute_ratings(rounds: List[Round]) -> Dict[str, Dict[str, float]]:
    """
    Args:
        rounds: chronologically ordered list of (traits_a, traits_b, voted_option).

    Returns:
        {trait_name: {"rating": float, "rd": float}} for every trait that
        appeared in at least one round. Traits never seen aren't included
        (callers can treat them as the default 1500/350 if needed).
    """
    ratings, rds, _history = _compute(rounds)
    return {
        name: {"rating": round(ratings[name], 1), "rd": round(rds[name], 1)}
        for name in ratings
    }


def compute_ratings_with_history(
    rounds: List[Round],
) -> Tuple[Dict[str, Dict[str, float]], Dict[str, List[Dict[str, float]]]]:
    """
    Same computation as compute_ratings, but also returns each trait's rating
    trajectory - one point per rating period in which that trait played a
    game (sparse per-trait, not one entry per round overall).

    Returns:
        (ratings, history) where ratings matches compute_ratings' return, and
        history is {trait_name: [{"round": period_index, "rating": float,
        "rd": float}, ...]} in chronological order.
    """
    ratings, rds, history = _compute(rounds)
    final = {
        name: {"rating": round(ratings[name], 1), "rd": round(rds[name], 1)}
        for name in ratings
    }
    return final, history


def _compute(
    rounds: List[Round],
) -> Tuple[Dict[str, float], Dict[str, float], Dict[str, List[Dict[str, float]]]]:
    ratings: Dict[str, float] = {}
    rds: Dict[str, float] = {}
    history: Dict[str, List[Dict[str, float]]] = {}

    for period_index, (traits_a, traits_b, voted_option) in enumerate(rounds):
        games: List[Tuple[str, str, float]] = []  # (player, opponent, score)
        for trait_a in traits_a:
            for trait_b in traits_b:
                if trait_a == trait_b:
                    continue
                score_a = 1.0 if voted_option == 'A' else 0.0
                games.append((trait_a, trait_b, score_a))
                games.append((trait_b, trait_a, 1.0 - score_a))

        if not games:
            continue

        # Snapshot pre-round ratings so every game this round is judged
        # against the same starting point - a proper Glicko rating period,
        # rather than letting mid-round updates leak into later games.
        participants = {name for name, _, _ in games} | {opp for _, opp, _ in games}
        pre_rating = {name: ratings.get(name, DEFAULT_RATING) for name in participants}
        pre_rd = {name: rds.get(name, DEFAULT_RD) for name in participants}

        by_player: Dict[str, List[Tuple[str, float]]] = {}
        for player, opponent, score in games:
            by_player.setdefault(player, []).append((opponent, score))

        for player, played in by_player.items():
            r = pre_rating[player]
            rd = pre_rd[player]

            d_sq_inv = 0.0
            sum_term = 0.0
            for opponent, score in played:
                opp_r = pre_rating[opponent]
                opp_rd = pre_rd[opponent]
                g_opp = _g(opp_rd)
                e = _expected_score(r, opp_r, opp_rd)
                d_sq_inv += (g_opp ** 2) * e * (1 - e)
                sum_term += g_opp * (score - e)

            if d_sq_inv == 0:
                continue
            d_sq = 1.0 / (Q ** 2 * d_sq_inv)

            new_rd = math.sqrt(1.0 / (1.0 / rd ** 2 + 1.0 / d_sq))
            new_r = r + Q / (1.0 / rd ** 2 + 1.0 / d_sq) * sum_term

            ratings[player] = new_r
            rds[player] = max(MIN_RD, min(MAX_RD, new_rd))
            history.setdefault(player, []).append(
                {"round": period_index, "rating": round(new_r, 1), "rd": round(rds[player], 1)}
            )

    return ratings, rds, history
