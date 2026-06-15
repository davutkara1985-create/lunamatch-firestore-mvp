"""Astrology and daily cosmic scoring services for LUNAMATCH."""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass
from datetime import date
from typing import Any

ZODIAC_SIGNS = [
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
]

SIGN_TR = {
    "Aries": "Koç",
    "Taurus": "Boğa",
    "Gemini": "İkizler",
    "Cancer": "Yengeç",
    "Leo": "Aslan",
    "Virgo": "Başak",
    "Libra": "Terazi",
    "Scorpio": "Akrep",
    "Sagittarius": "Yay",
    "Capricorn": "Oğlak",
    "Aquarius": "Kova",
    "Pisces": "Balık",
}

SIGN_ELEMENTS = {
    "Aries": "fire",
    "Leo": "fire",
    "Sagittarius": "fire",
    "Taurus": "earth",
    "Virgo": "earth",
    "Capricorn": "earth",
    "Gemini": "air",
    "Libra": "air",
    "Aquarius": "air",
    "Cancer": "water",
    "Scorpio": "water",
    "Pisces": "water",
}

COMPATIBLE_ELEMENTS = {
    "fire": {"fire", "air"},
    "air": {"air", "fire"},
    "earth": {"earth", "water"},
    "water": {"water", "earth"},
}

TAROT_MESSAGES = [
    (
        "Aradığınız kişiyi 10 gün içinde fark etme ihtimaliniz yükseliyor.",
        "Bu hafta iç sesinizi dinleyin ve yeni sohbetlere açık olun.",
    ),
    (
        "Bu hafta tanışacağınız biri kariyeriniz veya sosyal çevreniz için güzel bir kapı aralayabilir.",
        "Profilinizde hedeflerinizi küçük bir ipucuyla göstermek LUNAMATCH enerjinizi artırabilir.",
    ),
    (
        "Sosyalleşmeyi unutmayın; evren bu hafta sizi kalabalıkların içinde parlatıyor.",
        "İlk mesajı beklemek yerine küçük bir Kozmik Kıvılcım göndermek iyi gelebilir.",
    ),
    (
        "Bugün karşınıza çıkan bir profil, beklediğinizden daha tanıdık bir his uyandırabilir.",
        "Detaylara dikkat edin; küçük bir ortak ilgi alanı büyük bir sohbet başlatabilir.",
    ),
    (
        "Duygusal sezgileriniz bu hafta daha güçlü çalışabilir.",
        "Acele karar vermeden, sizi gerçekten meraklandıran kişilere alan açın.",
    ),
]


@dataclass(frozen=True)
class CosmicWeather:
    date_key: str
    moon_sign: str
    venus_sign: str
    mars_sign: str
    lucky_signs: list[str]
    focus_text: str


def calculate_sun_sign(birth_date: date) -> str:
    month, day = birth_date.month, birth_date.day
    ranges = [
        ("Capricorn", (1, 1), (1, 19)),
        ("Aquarius", (1, 20), (2, 18)),
        ("Pisces", (2, 19), (3, 20)),
        ("Aries", (3, 21), (4, 19)),
        ("Taurus", (4, 20), (5, 20)),
        ("Gemini", (5, 21), (6, 20)),
        ("Cancer", (6, 21), (7, 22)),
        ("Leo", (7, 23), (8, 22)),
        ("Virgo", (8, 23), (9, 22)),
        ("Libra", (9, 23), (10, 22)),
        ("Scorpio", (10, 23), (11, 21)),
        ("Sagittarius", (11, 22), (12, 21)),
        ("Capricorn", (12, 22), (12, 31)),
    ]
    for sign, start, end in ranges:
        if start <= (month, day) <= end:
            return sign
    return "Unknown"


def sign_label(sign: str | None) -> str:
    if not sign:
        return "Bilinmiyor"
    return SIGN_TR.get(sign, sign)


def _seeded_random(today: date) -> random.Random:
    seed = int(hashlib.sha256(today.isoformat().encode("utf-8")).hexdigest()[:12], 16)
    return random.Random(seed)


def daily_cosmic_weather(today: date | None = None) -> CosmicWeather:
    today = today or date.today()
    rng = _seeded_random(today)
    signs = ZODIAC_SIGNS[:]
    rng.shuffle(signs)
    focus_templates = [
        "Bugün sezgisel bağlar ve sıcak ilk mesajlar öne çıkıyor.",
        "Bugün sosyal cesaret, yeni tanışmaları daha görünür kılıyor.",
        "Bugün duygusal açıklık ve ortak ilgi alanları güçlü çalışıyor.",
        "Bugün yıldızlar, yavaş ama kaliteli tanışmalara alan açıyor.",
        "Bugün LUNAMATCH enerjisi spontane sohbetlerden yana.",
    ]
    return CosmicWeather(
        date_key=today.isoformat(),
        moon_sign=signs[3],
        venus_sign=signs[4],
        mars_sign=signs[5],
        lucky_signs=signs[:3],
        focus_text=rng.choice(focus_templates),
    )


def sign_compatibility(sign_a: str | None, sign_b: str | None) -> float:
    if not sign_a or not sign_b or sign_a == "Unknown" or sign_b == "Unknown":
        return 0.5
    if sign_a == sign_b:
        return 0.9
    element_a = SIGN_ELEMENTS.get(sign_a)
    element_b = SIGN_ELEMENTS.get(sign_b)
    if not element_a or not element_b:
        return 0.5
    if element_b in COMPATIBLE_ELEMENTS[element_a]:
        return 0.8
    return 0.4


def personality_compatibility(user_a: dict[str, Any], user_b: dict[str, Any]) -> float:
    keys = ["openness", "emotionality", "extroversion"]
    if not all(user_a.get(k) is not None and user_b.get(k) is not None for k in keys):
        return 0.5
    diffs = [abs(int(user_a[k]) - int(user_b[k])) for k in keys]
    avg_diff = sum(diffs) / len(diffs)
    return max(0.0, 1 - (avg_diff / 10))


def base_astro_score(user_a: dict[str, Any], user_b: dict[str, Any]) -> float:
    sun = sign_compatibility(user_a.get("sun_sign"), user_b.get("sun_sign"))
    moon = sign_compatibility(user_a.get("moon_sign"), user_b.get("moon_sign"))
    rising = sign_compatibility(user_a.get("rising_sign"), user_b.get("rising_sign"))
    personality = personality_compatibility(user_a, user_b)
    return round((sun * 0.30 + moon * 0.30 + rising * 0.20 + personality * 0.20) * 100, 2)


def daily_transit_bonus(
    user_a: dict[str, Any], user_b: dict[str, Any], weather: CosmicWeather
) -> dict[str, Any]:
    bonus = 0
    reasons: list[str] = []
    user_b_sun = user_b.get("sun_sign")
    user_b_moon = user_b.get("moon_sign")
    user_b_rising = user_b.get("rising_sign")

    if user_b_sun in weather.lucky_signs:
        bonus += 7
        reasons.append(f"{sign_label(user_b_sun)} bugün LUNAMATCH şanslı burçları arasında.")
    if user_b_moon == weather.moon_sign:
        bonus += 5
        reasons.append(f"Ay teması {sign_label(weather.moon_sign)} etkisini güçlendiriyor.")
    if user_b_rising == weather.venus_sign:
        bonus += 4
        reasons.append(f"Venüs etkisi {sign_label(weather.venus_sign)} yükselenlerle daha uyumlu.")
    if user_b_sun == weather.mars_sign:
        bonus += 3
        reasons.append(f"Mars etkisi {sign_label(weather.mars_sign)} burcuna hareket katıyor.")

    pair_bonus = int(sign_compatibility(user_a.get("sun_sign"), user_b_sun) * 5)
    bonus += pair_bonus
    if pair_bonus >= 4:
        reasons.append("Bugünkü Güneş enerjileri aranızdaki akışı destekliyor.")

    if not reasons:
        reasons.append("Bugünkü kozmik hava dengeli; uyum oranı temel harita üzerinden hesaplandı.")

    return {"bonus": min(bonus, 18), "reasons": reasons}


def adjusted_daily_astro_score(
    user_a: dict[str, Any], user_b: dict[str, Any], today: date | None = None
) -> dict[str, Any]:
    weather = daily_cosmic_weather(today)
    base = base_astro_score(user_a, user_b)
    transit = daily_transit_bonus(user_a, user_b, weather)
    adjusted = max(0, min(100, base + transit["bonus"]))
    return {
        "base_astro_score": round(base, 2),
        "daily_bonus": transit["bonus"],
        "adjusted_astro_score": round(adjusted, 2),
        "daily_reasons": transit["reasons"],
        "weather": weather,
    }


def is_tarot_selected(user_id: str, today: date | None = None, ratio: float = 0.05) -> bool:
    today = today or date.today()
    digest = hashlib.sha256(f"lunamatch-tarot:{user_id}:{today.isoformat()}".encode("utf-8")).hexdigest()
    bucket = int(digest[:8], 16) % 10000
    return bucket < int(ratio * 10000)


def tarot_message(user_id: str, today: date | None = None) -> tuple[str, str]:
    today = today or date.today()
    digest = hashlib.sha256(f"lunamatch-message:{user_id}:{today.isoformat()}".encode("utf-8")).hexdigest()
    idx = int(digest[:8], 16) % len(TAROT_MESSAGES)
    return TAROT_MESSAGES[idx]
