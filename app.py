from __future__ import annotations

import hashlib
import random
import uuid
from dataclasses import dataclass
from datetime import date
from math import atan2, cos, radians, sin, sqrt
from typing import Any

import firebase_admin
import requests
import streamlit as st
from firebase_admin import credentials, firestore, storage


APP_NAME = "LUNAMATCH"
COSMIC_SPARK_NAME = "Kozmik Kıvılcım"
DAILY_COSMIC_SPARK_LIMIT = 20
BELIRTMEK_ISTEMIYORUM = "Belirtmek İstemiyorum"

FIREBASE_AUTH_BASE = "https://identitytoolkit.googleapis.com/v1"

ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
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
    "Aries": "fire", "Leo": "fire", "Sagittarius": "fire",
    "Taurus": "earth", "Virgo": "earth", "Capricorn": "earth",
    "Gemini": "air", "Libra": "air", "Aquarius": "air",
    "Cancer": "water", "Scorpio": "water", "Pisces": "water",
}

COMPATIBLE_ELEMENTS = {
    "fire": {"fire", "air"},
    "air": {"air", "fire"},
    "earth": {"earth", "water"},
    "water": {"water", "earth"},
}

EDUCATION_OPTIONS = [
    BELIRTMEK_ISTEMIYORUM,
    "Lise",
    "Ön lisans",
    "Lisans",
    "Yüksek lisans",
    "Doktora",
]

YES_NO_OPTIONS = [
    BELIRTMEK_ISTEMIYORUM,
    "Evet",
    "Hayır",
    "Bazen",
]

RELATIONSHIP_INTENT_OPTIONS = [
    BELIRTMEK_ISTEMIYORUM,
    "Ciddi ilişki",
    "Arkadaşlık",
    "Evlilik odaklı ilişki",
    "Şimdilik emin değilim",
]

PERSONALITY_OPTIONS = [
    BELIRTMEK_ISTEMIYORUM,
    "İçe dönük",
    "Dışa dönük",
    "Dengeli",
]

DISTANCE_OPTIONS = [
    BELIRTMEK_ISTEMIYORUM,
    "Olumlu bakarım",
    "Duruma göre bakarım",
    "Tercih etmem",
]

SOCIAL_OPTIONS = [
    BELIRTMEK_ISTEMIYORUM,
    "Çok severim",
    "Ara sıra severim",
    "Daha sakin ortamları tercih ederim",
]

FREQUENCY_OPTIONS = [
    BELIRTMEK_ISTEMIYORUM,
    "Her gün",
    "Haftada birkaç kez",
    "Haftada bir",
    "Karşılıklı ihtiyaca göre",
]

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
]


st.set_page_config(
    page_title=APP_NAME,
    page_icon="🌙",
    layout="wide",
)


@dataclass(frozen=True)
class CosmicWeather:
    date_key: str
    moon_sign: str
    venus_sign: str
    mars_sign: str
    lucky_signs: list[str]
    focus_text: str


def inject_css() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background:
              radial-gradient(circle at 10% 10%, rgba(250,204,21,.16), transparent 28%),
              radial-gradient(circle at 90% 5%, rgba(236,72,153,.18), transparent 32%),
              linear-gradient(135deg, #0F172A 0%, #1E1B4B 55%, #111827 100%);
            color: #F8FAFC;
        }
        .lm-hero {
            padding: 34px;
            border-radius: 34px;
            background: linear-gradient(135deg, rgba(250,204,21,.18), rgba(236,72,153,.14), rgba(139,92,246,.15));
            border: 1px solid rgba(250,204,21,.35);
            box-shadow: 0 0 50px rgba(250,204,21,.10);
            margin-bottom: 22px;
        }
        .lm-title {
            font-size: 56px;
            letter-spacing: 4px;
            font-weight: 900;
            margin-bottom: 0;
        }
        .lm-sub {
            color: #CBD5E1;
            font-size: 18px;
        }
        .lm-card {
            padding: 26px;
            border-radius: 28px;
            background: rgba(255,255,255,.075);
            border: 1px solid rgba(250,204,21,.25);
            box-shadow: 0 24px 60px rgba(0,0,0,.25);
            margin-bottom: 18px;
        }
        .badge {
            display: inline-block;
            padding: 7px 13px;
            margin: 4px 4px 4px 0;
            border-radius: 999px;
            background: linear-gradient(90deg, #EC4899, #8B5CF6);
            color: white;
            font-size: 13px;
        }
        .gold-badge {
            display: inline-block;
            padding: 7px 13px;
            border-radius: 999px;
            background: linear-gradient(90deg, #FACC15, #F97316);
            color: #111827;
            font-weight: 800;
            font-size: 13px;
        }
        .tarot {
            padding: 36px;
            border-radius: 32px;
            text-align:center;
            background: linear-gradient(145deg, rgba(49,46,129,.95), rgba(15,23,42,.98));
            border: 2px solid rgba(250,204,21,.60);
            box-shadow: 0 0 54px rgba(250,204,21,.25);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_resource(show_spinner=False)
def firebase_app():
    if "firebase" not in st.secrets:
        st.error("Firebase secrets bulunamadı.")
        st.info("Streamlit Cloud → App → Settings → Secrets alanına [firebase] bloğunu ekleyin.")
        st.stop()

    service_account = dict(st.secrets["firebase"])
    service_account["private_key"] = service_account["private_key"].replace("\\n", "\n")

    if not firebase_admin._apps:
        bucket_name = st.secrets.get("firebase_storage", {}).get("bucket")
        options = {"storageBucket": bucket_name} if bucket_name else None
        cred = credentials.Certificate(service_account)
        firebase_admin.initialize_app(cred, options)

    return firebase_admin.get_app()


def db():
    firebase_app()
    return firestore.client()


def bucket():
    firebase_app()
    bucket_name = st.secrets.get("firebase_storage", {}).get("bucket")
    if not bucket_name:
        st.error("Firebase Storage bucket eksik.")
        st.info('[firebase_storage] bucket = "..." değerini Streamlit Secrets içine ekleyin.')
        st.stop()
    return storage.bucket(bucket_name)


def firebase_web_api_key() -> str:
    key = st.secrets.get("firebase_web", {}).get("api_key")
    if not key:
        st.error("Firebase Web API Key eksik.")
        st.info("[firebase_web] api_key değerini Streamlit Secrets içine ekleyin.")
        st.stop()
    return key


def admin_emails() -> list[str]:
    raw = st.secrets.get("admin", {}).get("emails", "")
    return [item.strip().lower() for item in raw.split(",") if item.strip()]


def is_admin_email(email: str) -> bool:
    return email.lower() in admin_emails()


def firebase_auth_request(endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
    url = f"{FIREBASE_AUTH_BASE}/{endpoint}?key={firebase_web_api_key()}"
    response = requests.post(url, json=payload, timeout=20)
    data = response.json()

    if response.status_code != 200:
        message = data.get("error", {}).get("message", "Firebase Auth hatası.")
        raise RuntimeError(message)

    return data


def register_user(email: str, password: str) -> dict[str, Any]:
    return firebase_auth_request(
        "accounts:signUp",
        {
            "email": email,
            "password": password,
            "returnSecureToken": True,
        },
    )


def login_user(email: str, password: str) -> dict[str, Any]:
    return firebase_auth_request(
        "accounts:signInWithPassword",
        {
            "email": email,
            "password": password,
            "returnSecureToken": True,
        },
    )


def send_password_reset(email: str) -> None:
    firebase_auth_request(
        "accounts:sendOobCode",
        {
            "requestType": "PASSWORD_RESET",
            "email": email,
        },
    )


def create_auth_user_profile(uid: str, email: str, role: str = "user") -> None:
    db().collection("users").document(uid).set(
        {
            "uid": uid,
            "email": email,
            "role": role,
            "display_name": email.split("@")[0],
            "profile_completed": False,
            "is_premium": False,
            "created_at": firestore.SERVER_TIMESTAMP,
            "updated_at": firestore.SERVER_TIMESTAMP,
        },
        merge=True,
    )


def get_user(user_id: str) -> dict[str, Any] | None:
    doc = db().collection("users").document(user_id).get()
    if not doc.exists:
        return None
    data = doc.to_dict() or {}
    data["id"] = doc.id
    return data


def save_profile(user_id: str, data: dict[str, Any]) -> None:
    payload = dict(data)
    payload["profile_completed"] = True
    payload["updated_at"] = firestore.SERVER_TIMESTAMP
    db().collection("users").document(user_id).set(payload, merge=True)


def list_users() -> list[dict[str, Any]]:
    users = []
    for doc in db().collection("users").stream():
        data = doc.to_dict() or {}
        data["id"] = doc.id
        users.append(data)
    users.sort(key=lambda item: str(item.get("display_name", "")))
    return users


def set_user_role(user_id: str, role: str) -> None:
    db().collection("users").document(user_id).set(
        {
            "role": role,
            "updated_at": firestore.SERVER_TIMESTAMP,
        },
        merge=True,
    )


def upload_profile_photos(user_id: str, uploaded_files: list[Any]) -> list[str]:
    urls = []
    b = bucket()

    for idx, uploaded in enumerate(uploaded_files[:5]):
        extension = uploaded.name.split(".")[-1].lower()
        blob_path = f"profile_photos/{user_id}/{idx + 1}_{uuid.uuid4().hex}.{extension}"
        blob = b.blob(blob_path)
        blob.upload_from_string(uploaded.getvalue(), content_type=uploaded.type)

        try:
            blob.make_public()
            urls.append(blob.public_url)
        except Exception:
            urls.append(f"gs://{b.name}/{blob_path}")

    return urls


def get_daily_usage(user_id: str) -> dict[str, Any]:
    date_key = date.today().isoformat()
    doc_id = f"{date_key}_{user_id}"
    doc = db().collection("daily_like_usage").document(doc_id).get()

    if not doc.exists:
        return {
            "user_id": user_id,
            "date_key": date_key,
            "count": 0,
        }

    data = doc.to_dict() or {}
    data["id"] = doc.id
    data.setdefault("count", 0)
    return data


def remaining_cosmic_sparks(user: dict[str, Any]) -> int | str:
    if user.get("is_premium"):
        return "Sınırsız"

    usage = get_daily_usage(user["id"])
    return max(0, DAILY_COSMIC_SPARK_LIMIT - int(usage.get("count", 0)))


def record_reaction(
    from_user_id: str,
    to_user_id: str,
    action: str,
    is_premium: bool = False,
) -> dict[str, Any]:
    date_key = date.today().isoformat()
    usage_id = f"{date_key}_{from_user_id}"
    reaction_id = f"{from_user_id}_{to_user_id}"

    usage_count = int(get_daily_usage(from_user_id).get("count", 0))

    if action == "spark" and not is_premium:
        if usage_count >= DAILY_COSMIC_SPARK_LIMIT:
            return {
                "ok": False,
                "reason": "daily_limit_reached",
                "count": usage_count,
                "remaining": 0,
            }

        db().collection("daily_like_usage").document(usage_id).set(
            {
                "user_id": from_user_id,
                "date_key": date_key,
                "count": firestore.Increment(1),
                "updated_at": firestore.SERVER_TIMESTAMP,
            },
            merge=True,
        )
        usage_count += 1

    db().collection("reactions").document(reaction_id).set(
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
        reverse_doc = db().collection("reactions").document(reverse_id).get()
        reverse = reverse_doc.to_dict() or {}

        if reverse.get("action") == "spark":
            match_id = "_".join(sorted([from_user_id, to_user_id]))
            db().collection("matches").document(match_id).set(
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


def admin_stats() -> dict[str, int]:
    users = list_users()
    reactions = list(db().collection("reactions").stream())
    matches = list(db().collection("matches").stream())

    return {
        "users": len(users),
        "completed_profiles": len([u for u in users if u.get("profile_completed")]),
        "admins": len([u for u in users if u.get("role") == "admin"]),
        "reactions": len(reactions),
        "matches": len(matches),
    }


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


def seeded_random(today: date) -> random.Random:
    seed = int(hashlib.sha256(today.isoformat().encode("utf-8")).hexdigest()[:12], 16)
    return random.Random(seed)


def daily_cosmic_weather(today: date | None = None) -> CosmicWeather:
    today = today or date.today()
    rng = seeded_random(today)

    signs = ZODIAC_SIGNS[:]
    rng.shuffle(signs)

    return CosmicWeather(
        date_key=today.isoformat(),
        moon_sign=signs[3],
        venus_sign=signs[4],
        mars_sign=signs[5],
        lucky_signs=signs[:3],
        focus_text=rng.choice(
            [
                "Bugün sezgisel bağlar ve sıcak ilk mesajlar öne çıkıyor.",
                "Bugün sosyal cesaret, yeni tanışmaları daha görünür kılıyor.",
                "Bugün duygusal açıklık ve ortak ilgi alanları güçlü çalışıyor.",
                "Bugün LUNAMATCH enerjisi spontane sohbetlerden yana.",
            ]
        ),
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

    return 0.8 if element_b in COMPATIBLE_ELEMENTS[element_a] else 0.4


def personality_compatibility(user_a: dict[str, Any], user_b: dict[str, Any]) -> float:
    keys = ["openness", "emotionality", "extroversion"]

    if not all(user_a.get(k) is not None and user_b.get(k) is not None for k in keys):
        return 0.5

    diffs = [abs(int(user_a[k]) - int(user_b[k])) for k in keys]
    return max(0.0, 1 - ((sum(diffs) / len(diffs)) / 10))


def base_astro_score(user_a: dict[str, Any], user_b: dict[str, Any]) -> float:
    sun = sign_compatibility(user_a.get("sun_sign"), user_b.get("sun_sign"))
    moon = sign_compatibility(user_a.get("moon_sign"), user_b.get("moon_sign"))
    rising = sign_compatibility(user_a.get("rising_sign"), user_b.get("rising_sign"))
    personality = personality_compatibility(user_a, user_b)

    return round((sun * 0.30 + moon * 0.30 + rising * 0.20 + personality * 0.20) * 100, 2)


def adjusted_daily_astro_score(user_a: dict[str, Any], user_b: dict[str, Any]) -> dict[str, Any]:
    weather = daily_cosmic_weather()
    base = base_astro_score(user_a, user_b)

    bonus = 0
    reasons = []

    if user_b.get("sun_sign") in weather.lucky_signs:
        bonus += 7
        reasons.append(f"{sign_label(user_b.get('sun_sign'))} bugün şanslı burçlar arasında.")

    if user_b.get("moon_sign") == weather.moon_sign:
        bonus += 5
        reasons.append(f"Ay teması {sign_label(weather.moon_sign)} etkisini güçlendiriyor.")

    if user_b.get("rising_sign") == weather.venus_sign:
        bonus += 4
        reasons.append(f"Venüs etkisi {sign_label(weather.venus_sign)} yükselenlerle uyumlu.")

    pair_bonus = int(sign_compatibility(user_a.get("sun_sign"), user_b.get("sun_sign")) * 5)
    bonus += pair_bonus

    bonus = min(bonus, 18)

    if not reasons:
        reasons.append("Bugünkü kozmik hava dengeli; uyum temel harita üzerinden hesaplandı.")

    adjusted = max(0, min(100, base + bonus))

    return {
        "base_astro_score": round(base, 2),
        "daily_bonus": bonus,
        "adjusted_astro_score": round(adjusted, 2),
        "daily_reasons": reasons,
        "weather": weather,
    }


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
    if max_distance_km <= 0 or distance_km > max_distance_km:
        return 0.0

    return max(0.0, 1 - (distance_km / max_distance_km))


def interest_score(a: list[str], b: list[str]) -> float:
    set_a = set(a or [])
    set_b = set(b or [])

    if not set_a or not set_b:
        return 0.0

    return len(set_a.intersection(set_b)) / len(set_a.union(set_b))


def combined_match_score(current_user: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    max_distance = int(current_user.get("max_distance_km", 80) or 80)

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
        current_user.get("interests", []),
        candidate.get("interests", []),
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
    candidates = []
    max_distance = int(current_user.get("max_distance_km", 80) or 80)

    for user in users:
        if user.get("id") == current_user.get("id"):
            continue

        if not user.get("profile_completed"):
            continue

        score = combined_match_score(current_user, user)

        if score["distance_km"] <= max_distance:
            item = dict(user)
            item["score"] = score
            candidates.append(item)

    candidates.sort(key=lambda item: item["score"]["final_score"], reverse=True)

    top_count = max(1, round(len(candidates) * 0.05)) if candidates else 0

    for idx, item in enumerate(candidates):
        item["is_star_chart"] = idx < top_count and item["score"]["adjusted_astro_score"] >= 82

    return candidates


def is_tarot_selected(user_id: str, ratio: float = 0.05) -> bool:
    digest = hashlib.sha256(
        f"lunamatch-tarot:{user_id}:{date.today().isoformat()}".encode("utf-8")
    ).hexdigest()
    bucket_value = int(digest[:8], 16) % 10000
    return bucket_value < int(ratio * 10000)


def tarot_message(user_id: str) -> tuple[str, str]:
    digest = hashlib.sha256(
        f"lunamatch-message:{user_id}:{date.today().isoformat()}".encode("utf-8")
    ).hexdigest()
    idx = int(digest[:8], 16) % len(TAROT_MESSAGES)
    return TAROT_MESSAGES[idx]


def required_text(label: str, key: str, placeholder: str = "") -> str:
    value = st.text_input(label, key=key, placeholder=placeholder)
    return value.strip() if value.strip() else BELIRTMEK_ISTEMIYORUM


def auth_page() -> None:
    inject_css()

    st.markdown(
        """
        <div class="lm-hero">
            <div class="lm-title">🌙 LUNAMATCH</div>
            <p class="lm-sub">Astrolojik uyum, kişilik verileri, fotoğraflı profil ve günlük kozmik eşleşme deneyimi.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_login, tab_register, tab_admin, tab_reset = st.tabs(
        ["Üye Girişi", "Yeni Üye Kaydı", "Admin Girişi", "Şifremi Unuttum"]
    )

    with tab_login:
        email = st.text_input("E-posta", key="login_email")
        password = st.text_input("Şifre", type="password", key="login_password")

        if st.button("🌙 Giriş Yap", use_container_width=True):
            try:
                data = login_user(email, password)
                uid = data["localId"]

                profile = get_user(uid)

                if not profile:
                    role = "admin" if is_admin_email(email) else "user"
                    create_auth_user_profile(uid, email, role)
                    profile = get_user(uid)

                st.session_state["user"] = profile
                st.success("Giriş başarılı.")
                st.rerun()

            except Exception as exc:
                st.error(str(exc))

    with tab_register:
        email = st.text_input("E-posta", key="register_email")
        password = st.text_input("Şifre", type="password", key="register_password")
        password_repeat = st.text_input("Şifre tekrar", type="password", key="register_password_repeat")

        if st.button("✨ Üye Ol", use_container_width=True):
            if not email:
                st.warning("E-posta zorunludur.")
            elif password != password_repeat:
                st.warning("Şifreler eşleşmiyor.")
            elif len(password) < 6:
                st.warning("Şifre en az 6 karakter olmalı.")
            else:
                try:
                    data = register_user(email, password)
                    uid = data["localId"]
                    role = "admin" if is_admin_email(email) else "user"
                    create_auth_user_profile(uid, email, role)
                    st.success("Üyelik oluşturuldu. Üye girişi yapabilirsiniz.")

                except Exception as exc:
                    st.error(str(exc))

    with tab_admin:
        email = st.text_input("Admin e-posta", key="admin_email")
        password = st.text_input("Admin şifre", type="password", key="admin_password")

        if st.button("🛠️ Admin Girişi", use_container_width=True):
            try:
                data = login_user(email, password)
                uid = data["localId"]

                profile = get_user(uid)

                if not profile:
                    role = "admin" if is_admin_email(email) else "user"
                    create_auth_user_profile(uid, email, role)
                    profile = get_user(uid)

                if profile.get("role") != "admin" and not is_admin_email(email):
                    st.error("Bu hesap admin yetkisine sahip değil.")
                else:
                    set_user_role(uid, "admin")
                    profile = get_user(uid)
                    st.session_state["user"] = profile
                    st.success("Admin girişi başarılı.")
                    st.rerun()

            except Exception as exc:
                st.error(str(exc))

    with tab_reset:
        email = st.text_input("E-posta adresiniz", key="reset_email")

        if st.button("🔐 Şifre Sıfırlama Linki Gönder", use_container_width=True):
            try:
                send_password_reset(email)
                st.success("Şifre sıfırlama bağlantısı e-posta adresinize gönderildi.")

            except Exception as exc:
                st.error(str(exc))


def require_login() -> None:
    if "user" not in st.session_state:
        auth_page()
        st.stop()


def current_user() -> dict[str, Any]:
    return st.session_state["user"]


def render_header() -> None:
    weather = daily_cosmic_weather()
    lucky = ", ".join(sign_label(sign) for sign in weather.lucky_signs)
    user = current_user()

    st.markdown(
        f"""
        <div class="lm-hero">
            <div class="lm-title">LUNAMATCH</div>
            <p class="lm-sub">Hoş geldin, <b>{user.get('email')}</b></p>
            <p><b>Bugünün kozmik havası:</b> {weather.focus_text}</p>
            <p>🌙 Ay: <b>{sign_label(weather.moon_sign)}</b> &nbsp; 💫 Venüs: <b>{sign_label(weather.venus_sign)}</b> &nbsp; 🔥 Mars: <b>{sign_label(weather.mars_sign)}</b></p>
            <p>⭐ Bugünün şanslı burçları: <b>{lucky}</b></p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def profile_page() -> None:
    user = current_user()
    existing = get_user(user["id"]) or user

    st.header("🌙 Profilini Tamamla")

    with st.form("profile_form"):
        st.subheader("Fotoğraflar")

        photos = st.file_uploader(
            "En fazla 5 profil fotoğrafı yükleyin",
            type=["png", "jpg", "jpeg", "webp"],
            accept_multiple_files=True,
        )

        st.subheader("Astrolojik Bilgiler")

        display_name = st.text_input("Görünen ad", value=existing.get("display_name", ""))
        birth_date = st.date_input("Doğum tarihi", value=date(1998, 1, 1))
        birth_city = st.text_input("Doğum yeri", value=existing.get("birth_city", "İstanbul"))

        sun_sign = calculate_sun_sign(birth_date)
        moon_sign = st.selectbox("Ay burcu", ZODIAC_SIGNS, format_func=sign_label)
        rising_sign = st.selectbox("Yükselen burç", ZODIAC_SIGNS, index=1, format_func=sign_label)

        st.subheader("🧠 1. Kişisel ve Temel Bilgiler")

        age = st.number_input(
            "Yaşınız nedir?",
            min_value=18,
            max_value=99,
            value=int(existing.get("age", 25) or 25),
        )
        profession = required_text("Mesleğiniz nedir?", "profession")
        education = st.selectbox("Eğitim seviyeniz nedir?", EDUCATION_OPTIONS)
        city = required_text("Hangi şehirde yaşıyorsunuz?", "city", "İstanbul")
        smoking_alcohol = st.selectbox("Sigara / alkol kullanır mısınız?", YES_NO_OPTIONS)
        sport = st.selectbox("Spor yapar mısınız?", YES_NO_OPTIONS)

        st.subheader("❤️ 2. İlişki Beklentileri")

        relationship_intent = st.selectbox(
            "Ciddi ilişki mi yoksa arkadaşlık mı arıyorsunuz?",
            RELATIONSHIP_INTENT_OPTIONS,
        )
        marriage_goal = st.selectbox("Uzun vadeli evlilik hedefiniz var mı?", YES_NO_OPTIONS)
        relationship_value = required_text("İlişkide sizin için en önemli şey nedir?", "relationship_value")
        partner_expectations = required_text("Partnerinizden beklentileriniz nelerdir?", "partner_expectations")
        long_distance = st.selectbox("Uzak mesafe ilişkisine nasıl bakarsınız?", DISTANCE_OPTIONS)

        st.subheader("🧩 3. Kişilik ve Değerler")

        intro_extro = st.selectbox("Kendinizi nasıl tanımlarsınız?", PERSONALITY_OPTIONS)
        stress_response = required_text("Stresle nasıl başa çıkarsınız?", "stress_response")
        life_value = required_text("Hayatta en çok neye değer verirsiniz?", "life_value")
        happiness = required_text("Sizi en çok ne mutlu eder?", "happiness")
        discomforts = required_text("Ne tür şeyler sizi rahatsız eder?", "discomforts")

        st.subheader("🎯 4. İlgi Alanları ve Yaşam Tarzı")

        free_time = required_text("Boş zamanlarınızda ne yaparsınız?", "free_time")
        music = required_text("En sevdiğiniz müzik türü nedir?", "music")
        holiday = required_text("Tatil tercihiniz nedir?", "holiday")
        book_movie = required_text("Kitap/film türü tercihleriniz neler?", "book_movie")
        home_or_out = required_text("Evde vakit geçirmek mi yoksa dışarı çıkmak mı?", "home_or_out")

        interests = st.multiselect(
            "İlgi alanları",
            [
                "Kahve",
                "Seyahat",
                "Müzik",
                "Sinema",
                "Yoga",
                "Kitap",
                "Spor",
                "Astroloji",
                "Sanat",
                "Teknoloji",
                "Doğa",
                "Fotoğraf",
            ],
        )

        st.subheader("🧑‍🤝‍🧑 5. Sosyal ve Aile Hayatı")

        family = required_text("Ailenizle ilişkiniz nasıldır?", "family")
        friends = required_text("Arkadaş çevreniz geniş mi?", "friends")
        socializing = st.selectbox("Sosyalleşmeyi sever misiniz?", SOCIAL_OPTIONS)
        children = st.selectbox("Çocuk sahibi olmak ister misiniz?", YES_NO_OPTIONS)

        st.subheader("💬 6. İletişim ve İlişki Dinamikleri")

        conflict = required_text("Tartışmalarda nasıl davranırsınız?", "conflict")
        love_language = required_text("Sevginizi nasıl gösterirsiniz?", "love_language")
        meeting_frequency = st.selectbox(
            "Partnerinizle ne sıklıkla görüşmek istersiniz?",
            FREQUENCY_OPTIONS,
        )
        jealousy = required_text("Kıskançlık hakkında düşünceniz nedir?", "jealousy")

        st.subheader("⚖️ 7. Uyum ve Tercih Soruları")

        preferred_age_range = required_text("Partnerinizin yaş aralığı ne olmalı?", "preferred_age_range")
        preferred_education = st.selectbox("Eğitim seviyesi tercihiniz nedir?", EDUCATION_OPTIONS)
        unacceptable_habits = required_text("Hangi alışkanlıklar sizin için kabul edilemez?", "unacceptable_habits")
        routine_compatibility = required_text(
            "Günlük rutinleriniz partnerle ne kadar uyumlu olmalı?",
            "routine_compatibility",
        )

        st.subheader("🎲 8. Eğlenceli / Yaratıcı Sorular")

        dream_holiday = required_text("Hayalinizdeki tatil neresi?", "dream_holiday")
        three_words = required_text("3 kelimeyle kendinizi anlatın", "three_words")
        superpower = required_text("Bir süper gücünüz olsaydı ne olurdu?", "superpower")
        first_date = required_text("İlk buluşmada ne yapmayı tercih edersiniz?", "first_date")
        favorite_food = required_text("Favori yemek?", "favorite_food")

        st.subheader("Konum ve Algoritma")

        col1, col2 = st.columns(2)

        with col1:
            location_lat = st.number_input(
                "Enlem",
                value=float(existing.get("location_lat", 41.0082)),
            )

        with col2:
            location_lon = st.number_input(
                "Boylam",
                value=float(existing.get("location_lon", 28.9784)),
            )

        max_distance_km = st.slider(
            "Maksimum mesafe",
            5,
            250,
            int(existing.get("max_distance_km", 80) or 80),
        )

        openness = st.slider("Yeniliğe açıklık", 1, 10, int(existing.get("openness", 7) or 7))
        emotionality = st.slider("Duygusallık", 1, 10, int(existing.get("emotionality", 6) or 6))
        extroversion = st.slider("Dışa dönüklük", 1, 10, int(existing.get("extroversion", 5) or 5))

        submitted = st.form_submit_button("🌙 LUNAMATCH Profilimi Kaydet", use_container_width=True)

    if submitted:
        if not display_name.strip():
            st.warning("Görünen ad zorunlu.")
            return

        if not photos and not existing.get("photo_urls"):
            st.warning("En az 1 profil fotoğrafı yüklemelisiniz.")
            return

        if photos and len(photos) > 5:
            st.warning("En fazla 5 fotoğraf yükleyebilirsiniz.")
            return

        photo_urls = existing.get("photo_urls", [])

        if photos:
            photo_urls = upload_profile_photos(user["id"], photos)

        payload = {
            "display_name": display_name.strip(),
            "age": int(age),
            "birth_date": birth_date.isoformat(),
            "birth_city": birth_city,
            "sun_sign": sun_sign,
            "moon_sign": moon_sign,
            "rising_sign": rising_sign,
            "photo_urls": photo_urls,
            "profession": profession,
            "education": education,
            "city": city,
            "smoking_alcohol": smoking_alcohol,
            "sport": sport,
            "relationship_intent": relationship_intent,
            "marriage_goal": marriage_goal,
            "relationship_value": relationship_value,
            "partner_expectations": partner_expectations,
            "long_distance": long_distance,
            "intro_extro": intro_extro,
            "stress_response": stress_response,
            "life_value": life_value,
            "happiness": happiness,
            "discomforts": discomforts,
            "free_time": free_time,
            "music": music,
            "holiday": holiday,
            "book_movie": book_movie,
            "home_or_out": home_or_out,
            "interests": interests,
            "family": family,
            "friends": friends,
            "socializing": socializing,
            "children": children,
            "conflict": conflict,
            "love_language": love_language,
            "meeting_frequency": meeting_frequency,
            "jealousy": jealousy,
            "preferred_age_range": preferred_age_range,
            "preferred_education": preferred_education,
            "unacceptable_habits": unacceptable_habits,
            "routine_compatibility": routine_compatibility,
            "dream_holiday": dream_holiday,
            "three_words": three_words,
            "superpower": superpower,
            "first_date": first_date,
            "favorite_food": favorite_food,
            "location_lat": float(location_lat),
            "location_lon": float(location_lon),
            "max_distance_km": int(max_distance_km),
            "openness": int(openness),
            "emotionality": int(emotionality),
            "extroversion": int(extroversion),
            "activity_score": 0.75,
            "is_premium": bool(existing.get("is_premium", False)),
        }

        save_profile(user["id"], payload)
        st.session_state["user"] = get_user(user["id"])
        st.success("Profiliniz başarıyla kaydedildi.")
        st.rerun()


def render_tarot_card(user_id: str) -> None:
    msg1, msg2 = tarot_message(user_id)

    st.markdown(
        f"""
        <div class="tarot">
            <h1>🔮 LUNAMATCH Kozmik Kartı</h1>
            <h2>Evrendeki şanslı kişi sizsiniz.</h2>
            <h3>Almanız Gereken Kişiye Özel Mesaj</h3>
            <p>{msg1}</p>
            <p>{msg2}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def matches_page() -> None:
    user = get_user(current_user()["id"])

    if not user or not user.get("profile_completed"):
        st.info("Eşleşmeleri görmek için önce profilinizi tamamlamalısınız.")
        return

    users = list_users()
    remaining = remaining_cosmic_sparks(user)
    usage = get_daily_usage(user["id"])

    col1, col2, col3 = st.columns(3)
    col1.metric("Kalan Kozmik Kıvılcım", remaining)
    col2.metric("Bugünkü Kullanım", usage.get("count", 0))
    col3.metric("Premium", "Evet" if user.get("is_premium") else "Hayır")

    if not user.get("is_premium") and remaining == 0:
        st.markdown(
            f"""
            <div class="lm-card">
              <h2>✨ Günlük {COSMIC_SPARK_NAME} hakkınız bitti</h2>
              <p>Premium ile sınırsız Kozmik Kıvılcım, gelişmiş filtreler ve detaylı astro uyum raporları açılır.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.button("🌙 LUNAMATCH Premium'u İncele", use_container_width=True)
        return

    candidates = rank_candidates(user, users)

    if not candidates:
        st.info("Şu anda uygun aday bulunamadı.")
        return

    for candidate in candidates:
        score = candidate["score"]
        photo = (candidate.get("photo_urls") or [""])[0]
        star = "<span class='gold-badge'>⭐ Günün Yıldız Haritası</span>" if candidate.get("is_star_chart") else ""
        interests = "".join(f"<span class='badge'>{i}</span>" for i in candidate.get("interests", []))
        reasons = "<br>".join(f"• {r}" for r in score.get("daily_reasons", []))

        col_img, col_info = st.columns([1, 2])

        with col_img:
            if photo and photo.startswith("http"):
                st.image(photo, use_container_width=True)
            else:
                st.markdown("<div class='lm-card'>Fotoğraf önizlemesi yok</div>", unsafe_allow_html=True)

        with col_info:
            st.markdown(
                f"""
                <div class="lm-card">
                  <h2>{candidate.get('display_name')}, {candidate.get('age')} {star}</h2>
                  <p>☀️ {sign_label(candidate.get('sun_sign'))} &nbsp; 🌙 {sign_label(candidate.get('moon_sign'))} &nbsp; ⬆️ {sign_label(candidate.get('rising_sign'))}</p>
                  <p><b>LUNAMATCH günlük uyum:</b> %{score['adjusted_astro_score']} <br>
                  <span>Taban: %{score['base_astro_score']} / Günlük bonus: +{score['daily_bonus']}</span></p>
                  <p><b>Mesafe:</b> {score['distance_km']} km &nbsp; <b>Kombin skor:</b> %{score['final_score']}</p>
                  <p>{interests}</p>
                  <p>{candidate.get('three_words', '')}</p>
                  <p>{reasons}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            btn1, btn2 = st.columns(2)

            with btn1:
                if st.button("🌑 Geç", key=f"pass_{candidate['id']}", use_container_width=True):
                    record_reaction(user["id"], candidate["id"], "pass", bool(user.get("is_premium")))
                    st.rerun()

            with btn2:
                if st.button(f"✨ {COSMIC_SPARK_NAME} Gönder", key=f"spark_{candidate['id']}", use_container_width=True):
                    result = record_reaction(user["id"], candidate["id"], "spark", bool(user.get("is_premium")))

                    if not result.get("ok"):
                        st.warning("Günlük hakkınız bitti.")
                    else:
                        st.success(f"{COSMIC_SPARK_NAME} gönderildi. Kalan hak: {result.get('remaining')}")

                        if result.get("created_match"):
                            st.balloons()
                            st.success("🌙 LUNAMATCH eşleşmesi oluştu.")

                        if int(result.get("count", 0)) >= 10 and is_tarot_selected(user["id"]):
                            render_tarot_card(user["id"])

                    st.rerun()


def admin_page() -> None:
    user = current_user()

    if user.get("role") != "admin":
        st.error("Bu alan yalnızca admin kullanıcılar içindir.")
        return

    st.header("🛠️ LUNAMATCH Admin Paneli")

    stats = admin_stats()

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Üye", stats["users"])
    c2.metric("Tam Profil", stats["completed_profiles"])
    c3.metric("Admin", stats["admins"])
    c4.metric("Reaksiyon", stats["reactions"])
    c5.metric("Eşleşme", stats["matches"])

    users = list_users()

    st.dataframe(
        [
            {
                "id": u.get("id"),
                "email": u.get("email"),
                "ad": u.get("display_name"),
                "rol": u.get("role"),
                "profil": u.get("profile_completed"),
                "premium": u.get("is_premium"),
            }
            for u in users
        ],
        use_container_width=True,
    )

    st.subheader("Rol Güncelle")

    if users:
        selected = st.selectbox(
            "Kullanıcı",
            users,
            format_func=lambda u: f"{u.get('email')} - {u.get('display_name')}",
        )
        role = st.selectbox("Yeni rol", ["user", "admin"])

        if st.button("Rolü Güncelle"):
            set_user_role(selected["id"], role)
            st.success("Rol güncellendi.")
            st.rerun()


def main() -> None:
    inject_css()
    require_login()
    render_header()

    with st.sidebar:
        st.write(f"👤 {current_user().get('email')}")
        st.write(f"Rol: {current_user().get('role')}")

        if st.button("Çıkış Yap"):
            st.session_state.clear()
            st.rerun()

    tabs = ["Profil", "Eşleşmeler"]

    if current_user().get("role") == "admin":
        tabs.append("Admin Paneli")

    tab_items = st.tabs(tabs)

    with tab_items[0]:
        profile_page()

    with tab_items[1]:
        matches_page()

    if current_user().get("role") == "admin":
        with tab_items[2]:
            admin_page()


main()
