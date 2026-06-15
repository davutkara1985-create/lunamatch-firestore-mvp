"""Matching service for LUNAMATCH."""

from __future__ import annotations

from math import atan2, cos, radians, sin, sqrt
from typing import Any

from services.astro_service import adjusted_daily_astro_score


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    earth_radius_km = 6371.0
    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)
    a = (
        sin(d_lat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon / 2) ** 2
    )
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return earth_radius_km * c


def distance_score(distance_km: float, max_distance_km: int) -> float:
    if max_distance_km <= 0:
        return 0.0
    if distance_km > max_distance_km:
        return 0.0
    return max(0.0, 1 - (distance_km / max_distance_km))


def interest_score(interests_a: list[str], interests_b: list[str]) -> float:
    set_a = set(interests_a or [])
    set_b = set(interests_b or [])
    if not set_a or not set_b:
        return 0.0
    return len(set_a.intersection(set_b)) / len(set_a.union(set_b))


def combined_match_score(current_user: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    max_distance = int(current_user.get("max_distance_km", 50) or 50)

    distance = haversine_km(
        float(current_user.get("location_lat", 41.0082)),
        float(current_user.get("location_lon", 28.9784)),
        float(candidate.get("location_lat", 41.0082)),
        float(candidate.get("location_lon", 28.9784)),
    )

    daily_astro = adjusted_daily_astro_score(current_user, candidate)
    astro_component = daily_astro["adjusted_astro_score"] / 100
    distance_component = distance_score(distance, max_distance)
    interest_component = interest_score(
        current_user.get("interests", []), candidate.get("interests", [])
    )
    activity_component = float(candidate.get("activity_score", 0.70) or 0.70)

    final = (
        astro_component * 0.55
        + distance_component * 0.20
        + interest_component * 0.15
        + activity_component * 0.10
    )

    return {
        "final_score": round(final * 100, 2),
        "distance_km": round(distance, 1),
        "interest_score": round(interest_component * 100, 2),
        "activity_score": round(activity_component * 100, 2),
        **daily_astro,
    }


def rank_candidates(current_user: dict[str, Any], users: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    max_distance = int(current_user.get("max_distance_km", 50) or 50)

    for user in users:
        if user.get("id") == current_user.get("id"):
            continue
        score = combined_match_score(current_user, user)
        if score["distance_km"] <= max_distance:
            enriched = dict(user)
            enriched["score"] = score
            candidates.append(enriched)

    candidates.sort(key=lambda item: item["score"]["final_score"], reverse=True)

    # The top 5% with a strong daily chart gets the LUNAMATCH star chart badge.
    top_count = max(1, round(len(candidates) * 0.05)) if candidates else 0
    for idx, item in enumerate(candidates):
        item["is_star_chart"] = idx < top_count and item["score"]["adjusted_astro_score"] >= 82

    return candidates
