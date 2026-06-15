"""Firestore repository for LUNAMATCH.

No local database is used in this repository.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from firebase_admin import firestore

from utils.firebase_client import get_firestore_client

USERS = "users"
REACTIONS = "reactions"
MATCHES = "matches"
DAILY_USAGE = "daily_like_usage"
DAILY_COSMIC_SPARK_LIMIT = 20


def _db():
    return get_firestore_client()


def _date_key(today: date | None = None) -> str:
    return (today or date.today()).isoformat()


def create_user(data: dict[str, Any]) -> str:
    db = _db()
    ref = db.collection(USERS).document()
    payload = dict(data)
    payload["created_at"] = firestore.SERVER_TIMESTAMP
    payload["updated_at"] = firestore.SERVER_TIMESTAMP
    ref.set(payload)
    return ref.id


def upsert_demo_user(data: dict[str, Any]) -> str:
    db = _db()
    doc_id = data["slug"]
    payload = dict(data)
    payload["updated_at"] = firestore.SERVER_TIMESTAMP
    db.collection(USERS).document(doc_id).set(payload, merge=True)
    return doc_id


def list_users() -> list[dict[str, Any]]:
    db = _db()
    docs = db.collection(USERS).stream()
    users: list[dict[str, Any]] = []
    for doc in docs:
        data = doc.to_dict() or {}
        data["id"] = doc.id
        users.append(data)
    users.sort(key=lambda item: str(item.get("display_name", "")))
    return users


def get_user(user_id: str) -> dict[str, Any] | None:
    doc = _db().collection(USERS).document(user_id).get()
    if not doc.exists:
        return None
    data = doc.to_dict() or {}
    data["id"] = doc.id
    return data


def get_daily_usage(user_id: str, today: date | None = None) -> dict[str, Any]:
    db = _db()
    date_key = _date_key(today)
    doc_id = f"{date_key}_{user_id}"
    doc = db.collection(DAILY_USAGE).document(doc_id).get()
    if not doc.exists:
        return {"user_id": user_id, "date_key": date_key, "count": 0}
    data = doc.to_dict() or {}
    data["id"] = doc.id
    data.setdefault("count", 0)
    return data


def remaining_cosmic_sparks(user: dict[str, Any], today: date | None = None) -> int | str:
    if user.get("is_premium"):
        return "Sınırsız"
    usage = get_daily_usage(str(user["id"]), today)
    return max(0, DAILY_COSMIC_SPARK_LIMIT - int(usage.get("count", 0)))


def record_reaction(
    from_user_id: str,
    to_user_id: str,
    action: str,
    is_premium: bool = False,
    today: date | None = None,
) -> dict[str, Any]:
    db = _db()
    date_key = _date_key(today)
    usage_id = f"{date_key}_{from_user_id}"
    reaction_id = f"{from_user_id}_{to_user_id}"

    if action == "spark" and not is_premium:
        usage_ref = db.collection(DAILY_USAGE).document(usage_id)
        usage_doc = usage_ref.get()
        usage_count = int((usage_doc.to_dict() or {}).get("count", 0)) if usage_doc.exists else 0
        if usage_count >= DAILY_COSMIC_SPARK_LIMIT:
            return {
                "ok": False,
                "reason": "daily_limit_reached",
                "count": usage_count,
                "remaining": 0,
            }
        usage_ref.set(
            {
                "user_id": from_user_id,
                "date_key": date_key,
                "count": firestore.Increment(1),
                "updated_at": firestore.SERVER_TIMESTAMP,
            },
            merge=True,
        )
        usage_count += 1
    else:
        usage_count = int(get_daily_usage(from_user_id, today).get("count", 0))

    db.collection(REACTIONS).document(reaction_id).set(
        {
            "from_user_id": from_user_id,
            "to_user_id": to_user_id,
            "action": action,
            "date_key": date_key,
            "created_at": firestore.SERVER_TIMESTAMP,
        },
        merge=True,
    )

    created_match = False
    if action == "spark":
        reverse_id = f"{to_user_id}_{from_user_id}"
        reverse_doc = db.collection(REACTIONS).document(reverse_id).get()
        reverse = reverse_doc.to_dict() or {}
        if reverse.get("action") == "spark":
            match_id = "_".join(sorted([from_user_id, to_user_id]))
            db.collection(MATCHES).document(match_id).set(
                {
                    "users": sorted([from_user_id, to_user_id]),
                    "created_at": firestore.SERVER_TIMESTAMP,
                },
                merge=True,
            )
            created_match = True

    remaining = "Sınırsız" if is_premium else max(0, DAILY_COSMIC_SPARK_LIMIT - usage_count)
    return {
        "ok": True,
        "count": usage_count,
        "remaining": remaining,
        "created_match": created_match,
    }


def seed_demo_profiles() -> int:
    demo_users = [
        {
            "slug": "lunamatch-elif",
            "display_name": "Elif",
            "age": 27,
            "bio": "Kahve, sanat ve sakin sahil yürüyüşleri. LUNAMATCH'te gerçek bir bağ arıyorum.",
            "birth_city": "İstanbul",
            "sun_sign": "Libra",
            "moon_sign": "Pisces",
            "rising_sign": "Leo",
            "location_lat": 41.0082,
            "location_lon": 28.9784,
            "interests": ["Kahve", "Sanat", "Seyahat", "Astroloji"],
            "openness": 8,
            "emotionality": 7,
            "extroversion": 6,
            "max_distance_km": 80,
            "activity_score": 0.88,
            "is_premium": False,
        },
        {
            "slug": "lunamatch-deniz",
            "display_name": "Deniz",
            "age": 30,
            "bio": "Müzik, girişimcilik ve derin sohbetler. Ay burcuna özellikle bakarım.",
            "birth_city": "Ankara",
            "sun_sign": "Aquarius",
            "moon_sign": "Libra",
            "rising_sign": "Sagittarius",
            "location_lat": 39.9334,
            "location_lon": 32.8597,
            "interests": ["Müzik", "Teknoloji", "Kitap", "Astroloji"],
            "openness": 9,
            "emotionality": 5,
            "extroversion": 7,
            "max_distance_km": 120,
            "activity_score": 0.80,
            "is_premium": False,
        },
        {
            "slug": "lunamatch-mira",
            "display_name": "Mira",
            "age": 25,
            "bio": "Yoga, fotoğraf ve yeni şehirler. Enerjisi yüksek insanlarla tanışmayı severim.",
            "birth_city": "İzmir",
            "sun_sign": "Sagittarius",
            "moon_sign": "Aries",
            "rising_sign": "Libra",
            "location_lat": 38.4237,
            "location_lon": 27.1428,
            "interests": ["Yoga", "Seyahat", "Fotoğraf", "Spor"],
            "openness": 8,
            "emotionality": 6,
            "extroversion": 8,
            "max_distance_km": 150,
            "activity_score": 0.91,
            "is_premium": True,
        },
        {
            "slug": "lunamatch-arya",
            "display_name": "Arya",
            "age": 29,
            "bio": "Sakin, yaratıcı ve sezgisel. Uzun yürüyüşler ve iyi kahve favorim.",
            "birth_city": "Bursa",
            "sun_sign": "Cancer",
            "moon_sign": "Taurus",
            "rising_sign": "Virgo",
            "location_lat": 40.1826,
            "location_lon": 29.0665,
            "interests": ["Kahve", "Kitap", "Doğa", "Sinema"],
            "openness": 7,
            "emotionality": 8,
            "extroversion": 4,
            "max_distance_km": 90,
            "activity_score": 0.76,
            "is_premium": False,
        },
    ]
    for user in demo_users:
        upsert_demo_user(user)
    return len(demo_users)
