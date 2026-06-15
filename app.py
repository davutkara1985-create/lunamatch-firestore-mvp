from __future__ import annotations

import hashlib
import html
import random
import uuid
from dataclasses import dataclass
from datetime import date
from math import atan2, cos, radians, sin, sqrt
from typing import Any
from urllib.parse import quote

import firebase_admin
import requests
import streamlit as st
from firebase_admin import credentials, firestore, storage

APP_NAME = "LUNAMATCH"
DAILY_HEART_LIMIT = 20
NO_ANSWER = "Belirtmek İstemiyorum"
FIREBASE_AUTH_BASE = "https://identitytoolkit.googleapis.com/v1"

USERS = "users"
REACTIONS = "reactions"
MATCHES = "matches"
DAILY_USAGE = "daily_like_usage"

st.set_page_config(page_title=APP_NAME, page_icon="💘", layout="wide")

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

GENDER_OPTIONS = [NO_ANSWER, "Kadın", "Erkek", "Non-binary"]
LOOKING_FOR_OPTIONS = ["Herkes", "Kadın", "Erkek", NO_ANSWER]
RELATIONSHIP_INTENT_OPTIONS = [
    "Ciddi ilişki",
    "Yeni insanlarla tanışmak",
    "Evlilik odaklı ilişki",
    "Akışına bırakmak istiyorum",
    NO_ANSWER,
]
ENERGY_OPTIONS = [
    NO_ANSWER,
    "Romantik",
    "Macera sever",
    "Sakin ve huzurlu",
    "Sosyal kelebek",
    "Derin sohbet insanı",
    "Eğlenceli ve spontane",
    "Ev konforunu seven",
    "Yeni yerler keşfetmeyi seven",
]
LOVE_LANGUAGE_OPTIONS = [
    NO_ANSWER,
    "Güzel sözler",
    "Kaliteli zaman",
    "Küçük sürprizler",
    "Fiziksel temas",
    "Destekleyici davranışlar",
]
INTEREST_OPTIONS = [
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
    "Dans",
    "Yemek",
    "Konser",
    "Sahil yürüyüşü",
    "Müze",
    "Kamp",
]

TAROT_MESSAGES = [
    (
        "Bugün kalbinin ritmine yakın biriyle karşılaşma ihtimalin yükseliyor.",
        "Küçük bir mesaj, büyük bir tanışmanın başlangıcı olabilir.",
    ),
    (
        "Sana iyi gelen enerji bugün daha görünür olabilir.",
        "İlk adımı atmaktan çekinme; bazen uyum tek bir cümleyle başlar.",
    ),
    (
        "Bugün ortak ilgi alanları güçlü çalışıyor.",
        "Bir profilin küçük bir detayı seni güzel bir sohbete taşıyabilir.",
    ),
    (
        "Romantik sezgilerin bugün daha güçlü.",
        "Sadece fotoğrafa değil, yazılanlara da dikkat et.",
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


def escape(value: Any) -> str:
    return html.escape(str(value or ""))


def inject_css() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(255, 79, 123, 0.16), transparent 28%),
                radial-gradient(circle at top right, rgba(255, 122, 89, 0.18), transparent 30%),
                radial-gradient(circle at bottom left, rgba(255, 209, 102, 0.20), transparent 32%),
                linear-gradient(135deg, #FFF7F3 0%, #FFE8E0 42%, #FFF4F7 100%);
            color: #2B1B2E;
        }

        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
            max-width: 1200px;
        }

        header[data-testid="stHeader"] {
            background: transparent;
        }

        .lm-topbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
            background: rgba(255,255,255,0.74);
            border: 1px solid rgba(255,79,123,0.14);
            border-radius: 26px;
            padding: 16px 20px;
            margin-bottom: 24px;
            box-shadow: 0 18px 45px rgba(255, 79, 123, 0.10);
            backdrop-filter: blur(16px);
        }

        .lm-brand {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .lm-logo {
            width: 46px;
            height: 46px;
            border-radius: 16px;
            background: linear-gradient(135deg, #FF4F7B, #FF7A59);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 24px;
            font-weight: 900;
            box-shadow: 0 14px 30px rgba(255,79,123,0.30);
        }

        .lm-brand-name {
            font-size: 24px;
            font-weight: 900;
            color: #2B1B2E;
            letter-spacing: -0.5px;
        }

        .lm-brand-sub {
            font-size: 13px;
            color: #7A6B76;
            margin-top: 2px;
        }

        .lm-user-pill {
            padding: 10px 14px;
            border-radius: 999px;
            background: #FFF1F4;
            border: 1px solid rgba(255,79,123,0.16);
            color: #C7355F;
            font-size: 13px;
            font-weight: 800;
            white-space: nowrap;
        }

        .auth-hero {
            background:
                linear-gradient(145deg, rgba(255,255,255,0.78), rgba(255,255,255,0.52)),
                radial-gradient(circle at top right, rgba(255,79,123,0.20), transparent 34%);
            border: 1px solid rgba(255,79,123,0.16);
            border-radius: 36px;
            padding: 46px;
            box-shadow: 0 28px 70px rgba(255,79,123,0.16);
            min-height: 650px;
            position: relative;
            overflow: hidden;
        }

        .auth-hero:after {
            content: "";
            width: 290px;
            height: 290px;
            position: absolute;
            bottom: -90px;
            right: -80px;
            background: radial-gradient(circle, rgba(255,122,89,0.20), transparent 70%);
            border-radius: 50%;
        }

        .hero-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 9px 16px;
            border-radius: 999px;
            background: #FFF1F4;
            border: 1px solid rgba(255,79,123,0.18);
            color: #D83963;
            font-size: 13px;
            font-weight: 900;
            margin-bottom: 20px;
        }

        .hero-title {
            font-size: 58px;
            line-height: 1.03;
            font-weight: 900;
            letter-spacing: -2px;
            color: #2B1B2E;
            margin-bottom: 18px;
        }

        .hero-gradient {
            background: linear-gradient(135deg, #FF4F7B, #FF7A59);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .hero-desc {
            font-size: 18px;
            line-height: 1.75;
            color: #6E5B67;
            max-width: 640px;
            margin-bottom: 28px;
        }

        .hero-pills {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin: 24px 0 28px 0;
        }

        .hero-pill {
            padding: 10px 14px;
            border-radius: 999px;
            background: #FFFFFF;
            border: 1px solid rgba(255,79,123,0.12);
            color: #613549;
            font-size: 13px;
            font-weight: 800;
            box-shadow: 0 10px 24px rgba(255,79,123,0.08);
        }

        .mini-phone {
            max-width: 360px;
            background: #FFFFFF;
            border-radius: 34px;
            padding: 14px;
            border: 1px solid rgba(255,79,123,0.12);
            box-shadow: 0 26px 60px rgba(255,79,123,0.16);
            margin-top: 24px;
        }

        .mini-photo {
            height: 260px;
            border-radius: 26px;
            background:
                linear-gradient(135deg, rgba(255,79,123,0.24), rgba(255,122,89,0.26)),
                url('https://images.unsplash.com/photo-1524504388940-b1c1722653e1?auto=format&fit=crop&w=900&q=80');
            background-size: cover;
            background-position: center;
        }

        .mini-info {
            padding: 16px 8px 4px 8px;
        }

        .mini-name {
            font-size: 22px;
            font-weight: 900;
            color: #2B1B2E;
        }

        .mini-text {
            font-size: 13px;
            color: #7A6B76;
            margin-top: 4px;
        }

        .auth-card {
            background: rgba(255,255,255,0.86);
            border: 1px solid rgba(255,79,123,0.16);
            border-radius: 34px;
            padding: 32px;
            box-shadow: 0 28px 70px rgba(255,79,123,0.14);
            min-height: 650px;
            backdrop-filter: blur(16px);
        }

        .auth-title {
            font-size: 31px;
            font-weight: 900;
            color: #2B1B2E;
            margin-bottom: 6px;
        }

        .auth-subtitle {
            font-size: 14px;
            color: #7A6B76;
            line-height: 1.6;
            margin-bottom: 22px;
        }

        div[data-baseweb="tab-list"] {
            gap: 8px;
            background: #FFF1F4;
            border-radius: 18px;
            padding: 6px;
            margin-bottom: 22px;
        }

        button[data-baseweb="tab"] {
            border-radius: 14px !important;
            color: #7A6B76 !important;
            font-weight: 800 !important;
            background: transparent !important;
            padding: 10px 14px !important;
        }

        button[data-baseweb="tab"][aria-selected="true"] {
            background: linear-gradient(135deg, #FF4F7B, #FF7A59) !important;
            color: #FFFFFF !important;
            box-shadow: 0 10px 24px rgba(255,79,123,0.22);
        }

        button[data-baseweb="tab"] p {
            color: inherit !important;
        }

        .stTextInput > div > div,
        .stNumberInput > div > div,
        .stDateInput > div > div,
        .stSelectbox > div > div,
        .stMultiSelect > div > div,
        .stTextArea textarea,
        .stSlider > div {
            border-radius: 18px !important;
        }

        .stTextInput input,
        .stNumberInput input,
        .stDateInput input,
        .stTextArea textarea {
            color: #2B1B2E !important;
        }

        label, p, span {
            color: #3C2A3F;
        }

        .stButton > button {
            border-radius: 999px;
            padding: 0.82rem 1.1rem;
            font-weight: 900;
            font-size: 15px;
            border: 0;
            color: #FFFFFF;
            background: linear-gradient(135deg, #FF4F7B, #FF7A59);
            box-shadow: 0 16px 32px rgba(255,79,123,0.28);
        }

        .stButton > button:hover {
            transform: translateY(-1px);
            filter: brightness(1.03);
            color: #FFFFFF;
        }

        div[role="radiogroup"] {
            display: flex;
            gap: 10px;
            background: rgba(255,255,255,0.72);
            border: 1px solid rgba(255,79,123,0.12);
            padding: 8px;
            border-radius: 999px;
            box-shadow: 0 16px 34px rgba(255,79,123,0.10);
            margin-bottom: 20px;
            flex-wrap: wrap;
        }

        div[role="radiogroup"] label {
            padding: 8px 14px;
            border-radius: 999px;
            background: transparent;
            font-weight: 800;
        }

        .page-card {
            background: rgba(255,255,255,0.86);
            border: 1px solid rgba(255,79,123,0.14);
            border-radius: 32px;
            padding: 28px;
            box-shadow: 0 24px 60px rgba(255,79,123,0.12);
            margin-bottom: 22px;
        }

        .section-title {
            font-size: 30px;
            font-weight: 900;
            color: #2B1B2E;
            margin-bottom: 6px;
        }

        .section-subtitle {
            font-size: 15px;
            color: #7A6B76;
            margin-bottom: 18px;
        }

        .discover-shell {
            background: rgba(255,255,255,0.92);
            border: 1px solid rgba(255,79,123,0.16);
            border-radius: 38px;
            padding: 18px;
            box-shadow: 0 30px 80px rgba(255,79,123,0.16);
            max-width: 980px;
            margin: 0 auto 22px auto;
        }

        .profile-photo-wrap {
            border-radius: 32px;
            overflow: hidden;
            background: linear-gradient(135deg, #FFE0E8, #FFF3EA);
            min-height: 460px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .profile-info {
            padding: 12px 8px 8px 8px;
        }

        .profile-name {
            font-size: 38px;
            font-weight: 900;
            color: #2B1B2E;
            letter-spacing: -1px;
        }

        .profile-meta {
            color: #7A6B76;
            font-size: 15px;
            margin: 6px 0 16px 0;
        }

        .compat-score {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: linear-gradient(135deg, #FF4F7B, #FF7A59);
            color: white;
            padding: 10px 16px;
            border-radius: 999px;
            font-size: 15px;
            font-weight: 900;
            box-shadow: 0 14px 28px rgba(255,79,123,0.26);
            margin-bottom: 12px;
        }

        .soft-badge {
            display: inline-block;
            background: #FFF1F4;
            border: 1px solid rgba(255,79,123,0.16);
            color: #C7355F;
            padding: 8px 12px;
            border-radius: 999px;
            font-size: 13px;
            font-weight: 800;
            margin: 4px 4px 4px 0;
        }

        .interest-badge {
            display: inline-block;
            background: #FFF6DF;
            border: 1px solid rgba(255,209,102,0.35);
            color: #8A5A00;
            padding: 8px 12px;
            border-radius: 999px;
            font-size: 13px;
            font-weight: 800;
            margin: 4px 4px 4px 0;
        }

        .reason-box {
            background: #FFF8F5;
            border: 1px solid rgba(255,122,89,0.14);
            border-radius: 20px;
            padding: 16px;
            color: #6E5B67;
            font-size: 14px;
            line-height: 1.6;
            margin-top: 14px;
        }

        .match-card,
        .premium-card {
            background: #FFFFFF;
            border: 1px solid rgba(255,79,123,0.12);
            border-radius: 28px;
            padding: 20px;
            box-shadow: 0 20px 44px rgba(255,79,123,0.10);
            margin-bottom: 16px;
        }

        .premium-card {
            height: 100%;
        }

        .premium-title {
            font-size: 24px;
            font-weight: 900;
            color: #2B1B2E;
            margin-bottom: 8px;
        }

        .premium-price {
            font-size: 34px;
            font-weight: 900;
            background: linear-gradient(135deg, #FF4F7B, #FF7A59);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 14px;
        }

        .small-note {
            color: #8B7B86;
            font-size: 12px;
            line-height: 1.6;
            margin-top: 14px;
        }

        .stAlert {
            border-radius: 18px !important;
        }

        @media (max-width: 950px) {
            .hero-title { font-size: 38px; }
            .auth-hero, .auth-card { min-height: auto; padding: 28px; }
            .profile-name { font-size: 30px; }
            .lm-topbar { flex-direction: column; align-items: flex-start; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def translate_auth_error(message: str) -> str:
    messages = {
        "EMAIL_EXISTS": "Bu e-posta adresiyle daha önce üyelik oluşturulmuş.",
        "OPERATION_NOT_ALLOWED": "Firebase Authentication içinde Email/Password giriş yöntemi aktif değil.",
        "TOO_MANY_ATTEMPTS_TRY_LATER": "Çok fazla deneme yapıldı. Lütfen biraz sonra tekrar deneyin.",
        "EMAIL_NOT_FOUND": "Bu e-posta adresiyle kayıtlı kullanıcı bulunamadı.",
        "INVALID_PASSWORD": "Şifre hatalı.",
        "INVALID_LOGIN_CREDENTIALS": "E-posta veya şifre hatalı.",
        "USER_DISABLED": "Bu kullanıcı hesabı devre dışı bırakılmış.",
        "MISSING_PASSWORD": "Şifre alanı boş bırakılamaz.",
        "INVALID_EMAIL": "E-posta adresi geçerli değil.",
    }
    return messages.get(message, message)


@st.cache_resource(show_spinner=False)
def initialize_firebase():
    if "firebase" not in st.secrets:
        st.error("Firebase secrets bulunamadı.")
        st.info("Streamlit Cloud → App → Settings → Secrets alanına [firebase] bloğunu ekleyin.")
        st.stop()

    service_account = dict(st.secrets["firebase"])

    required = [
        "type",
        "project_id",
        "private_key_id",
        "private_key",
        "client_email",
        "client_id",
        "auth_uri",
        "token_uri",
        "auth_provider_x509_cert_url",
        "client_x509_cert_url",
    ]

    missing = [key for key in required if not service_account.get(key)]
    if missing:
        st.error("Firebase secrets eksik.")
        st.code(", ".join(missing))
        st.stop()

    service_account["private_key"] = service_account["private_key"].replace("\\n", "\n")

    try:
        if not firebase_admin._apps:
            bucket_name = st.secrets.get("firebase_storage", {}).get("bucket")
            options = {"storageBucket": bucket_name} if bucket_name else None
            cred = credentials.Certificate(service_account)
            firebase_admin.initialize_app(cred, options)
        return firebase_admin.get_app()
    except Exception as exc:
        st.error("Firebase bağlantısı kurulamadı.")
        st.exception(exc)
        st.stop()


def db():
    initialize_firebase()
    return firestore.client()


def storage_bucket():
    initialize_firebase()
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


def admin_email_list() -> list[str]:
    raw = st.secrets.get("admin", {}).get("emails", "")
    return [item.strip().lower() for item in raw.split(",") if item.strip()]


def is_admin_email(email: str) -> bool:
    return email.lower() in admin_email_list()


def firebase_auth_request(endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
    url = f"{FIREBASE_AUTH_BASE}/{endpoint}?key={firebase_web_api_key()}"
    try:
        response = requests.post(url, json=payload, timeout=20)
        data = response.json()
    except Exception as exc:
        raise RuntimeError(f"Firebase Authentication bağlantı hatası: {exc}") from exc

    if response.status_code != 200:
        message = data.get("error", {}).get("message", "Firebase Auth hatası.")
        raise RuntimeError(translate_auth_error(message))
    return data


def register_user(email: str, password: str) -> dict[str, Any]:
    return firebase_auth_request(
        "accounts:signUp",
        {"email": email, "password": password, "returnSecureToken": True},
    )


def login_user(email: str, password: str) -> dict[str, Any]:
    return firebase_auth_request(
        "accounts:signInWithPassword",
        {"email": email, "password": password, "returnSecureToken": True},
    )


def send_password_reset(email: str) -> None:
    firebase_auth_request("accounts:sendOobCode", {"requestType": "PASSWORD_RESET", "email": email})


def create_auth_user_profile(uid: str, email: str, role: str = "user") -> None:
    db().collection(USERS).document(uid).set(
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
    doc = db().collection(USERS).document(user_id).get()
    if not doc.exists:
        return None
    data = doc.to_dict() or {}
    data["id"] = doc.id
    return data


def list_users() -> list[dict[str, Any]]:
    users = []
    for doc in db().collection(USERS).stream():
        data = doc.to_dict() or {}
        data["id"] = doc.id
        users.append(data)
    users.sort(key=lambda item: str(item.get("display_name", "")))
    return users


def save_profile(user_id: str, data: dict[str, Any]) -> None:
    payload = dict(data)
    payload["profile_completed"] = True
    payload["updated_at"] = firestore.SERVER_TIMESTAMP
    db().collection(USERS).document(user_id).set(payload, merge=True)


def set_user_role(user_id: str, role: str) -> None:
    db().collection(USERS).document(user_id).set(
        {"role": role, "updated_at": firestore.SERVER_TIMESTAMP},
        merge=True,
    )


def set_user_premium(user_id: str, is_premium: bool) -> None:
    db().collection(USERS).document(user_id).set(
        {"is_premium": is_premium, "updated_at": firestore.SERVER_TIMESTAMP},
        merge=True,
    )


def upload_profile_photos(user_id: str, uploaded_files: list[Any]) -> list[str]:
    bucket = storage_bucket()
    urls = []
    for idx, uploaded in enumerate(uploaded_files[:5]):
        extension = uploaded.name.split(".")[-1].lower()
        blob_path = f"profile_photos/{user_id}/{idx + 1}_{uuid.uuid4().hex}.{extension}"
        token = str(uuid.uuid4())
        blob = bucket.blob(blob_path)
        blob.metadata = {"firebaseStorageDownloadTokens": token}
        blob.upload_from_string(uploaded.getvalue(), content_type=uploaded.type)
        try:
            blob.patch()
        except Exception:
            pass
        encoded_path = quote(blob_path, safe="")
        url = f"https://firebasestorage.googleapis.com/v0/b/{bucket.name}/o/{encoded_path}?alt=media&token={token}"
        urls.append(url)
    return urls


def date_key(today: date | None = None) -> str:
    return (today or date.today()).isoformat()


def get_daily_usage(user_id: str) -> dict[str, Any]:
    current_date = date_key()
    doc_id = f"{current_date}_{user_id}"
    doc = db().collection(DAILY_USAGE).document(doc_id).get()
    if not doc.exists:
        return {"user_id": user_id, "date_key": current_date, "count": 0}
    data = doc.to_dict() or {}
    data["id"] = doc.id
    data.setdefault("count", 0)
    return data


def remaining_hearts(user: dict[str, Any]) -> int | str:
    if user.get("is_premium"):
        return "Sınırsız"
    usage = get_daily_usage(user["id"])
    return max(0, DAILY_HEART_LIMIT - int(usage.get("count", 0)))


def get_reacted_user_ids(user_id: str) -> set[str]:
    reacted = set()
    try:
        docs = db().collection(REACTIONS).where("from_user_id", "==", user_id).stream()
        for doc in docs:
            data = doc.to_dict() or {}
            to_user_id = data.get("to_user_id")
            if to_user_id:
                reacted.add(to_user_id)
    except Exception:
        pass
    return reacted


def record_reaction(
    from_user_id: str,
    to_user_id: str,
    action: str,
    is_premium: bool = False,
) -> dict[str, Any]:
    current_date = date_key()
    usage_id = f"{current_date}_{from_user_id}"
    reaction_id = f"{from_user_id}_{to_user_id}"
    usage_count = int(get_daily_usage(from_user_id).get("count", 0))
    heart_actions = {"heart", "super"}

    if action in heart_actions and not is_premium:
        if usage_count >= DAILY_HEART_LIMIT:
            return {
                "ok": False,
                "reason": "daily_limit_reached",
                "count": usage_count,
                "remaining": 0,
                "created_match": False,
            }
        db().collection(DAILY_USAGE).document(usage_id).set(
            {
                "user_id": from_user_id,
                "date_key": current_date,
                "count": firestore.Increment(1),
                "updated_at": firestore.SERVER_TIMESTAMP,
            },
            merge=True,
        )
        usage_count += 1

    db().collection(REACTIONS).document(reaction_id).set(
        {
            "from_user_id": from_user_id,
            "to_user_id": to_user_id,
            "action": action,
            "date_key": current_date,
            "created_at": firestore.SERVER_TIMESTAMP,
        },
        merge=True,
    )

    created_match = False
    if action in heart_actions:
        reverse_id = f"{to_user_id}_{from_user_id}"
        reverse_doc = db().collection(REACTIONS).document(reverse_id).get()
        reverse = reverse_doc.to_dict() or {}
        if reverse.get("action") in heart_actions:
            match_id = "_".join(sorted([from_user_id, to_user_id]))
            db().collection(MATCHES).document(match_id).set(
                {"users": sorted([from_user_id, to_user_id]), "created_at": firestore.SERVER_TIMESTAMP},
                merge=True,
            )
            created_match = True

    remaining = "Sınırsız" if is_premium else max(0, DAILY_HEART_LIMIT - usage_count)
    return {"ok": True, "count": usage_count, "remaining": remaining, "created_match": created_match}


def list_my_matches(user_id: str) -> list[dict[str, Any]]:
    results = []
    try:
        docs = db().collection(MATCHES).where("users", "array_contains", user_id).stream()
        for doc in docs:
            data = doc.to_dict() or {}
            users = data.get("users", [])
            other_ids = [uid for uid in users if uid != user_id]
            if not other_ids:
                continue
            other = get_user(other_ids[0])
            if other:
                other["match_id"] = doc.id
                other["match_created_at"] = data.get("created_at")
                results.append(other)
    except Exception:
        pass
    return results


def admin_stats() -> dict[str, int]:
    users = list_users()
    reactions = list(db().collection(REACTIONS).stream())
    matches = list(db().collection(MATCHES).stream())
    return {
        "users": len(users),
        "completed_profiles": len([user for user in users if user.get("profile_completed")]),
        "admins": len([user for user in users if user.get("role") == "admin"]),
        "premium": len([user for user in users if user.get("is_premium")]),
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
                "Bugün sıcak bir mesaj, güzel bir tanışmanın kapısını aralayabilir.",
                "Bugün ortak ilgi alanları ve doğal sohbetler öne çıkıyor.",
                "Bugün kalbinin ritmine yakın insanları fark etme ihtimalin yüksek.",
                "Bugün küçük bir cesaret, büyük bir eşleşmeye dönüşebilir.",
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
    if not all(user_a.get(key) is not None and user_b.get(key) is not None for key in keys):
        return 0.5
    diffs = [abs(int(user_a[key]) - int(user_b[key])) for key in keys]
    return max(0.0, 1 - ((sum(diffs) / len(diffs)) / 10))


def base_astro_score(user_a: dict[str, Any], user_b: dict[str, Any]) -> float:
    sun = sign_compatibility(user_a.get("sun_sign"), user_b.get("sun_sign"))
    moon = sign_compatibility(user_a.get("moon_sign"), user_b.get("moon_sign"))
    rising = sign_compatibility(user_a.get("rising_sign"), user_b.get("rising_sign"))
    personality = personality_compatibility(user_a, user_b)
    return round((sun * 0.30 + moon * 0.25 + rising * 0.20 + personality * 0.25) * 100, 2)


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
        reasons.append(f"Ay teması {sign_label(weather.moon_sign)} enerjisini güçlendiriyor.")
    if user_b.get("rising_sign") == weather.venus_sign:
        bonus += 4
        reasons.append(f"Venüs etkisi {sign_label(weather.venus_sign)} yükselenlerle sıcak bir uyum veriyor.")

    pair_bonus = int(sign_compatibility(user_a.get("sun_sign"), user_b.get("sun_sign")) * 5)
    bonus += pair_bonus
    bonus = min(bonus, 18)

    if not reasons:
        reasons.append("Bugünkü enerji dengeli; uyum profil ve harita verilerinden hesaplandı.")

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
    a = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon / 2) ** 2
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
    interest_component = interest_score(current_user.get("interests", []), candidate.get("interests", []))
    activity_component = float(candidate.get("activity_score", 0.75) or 0.75)
    final = astro_component * 0.48 + distance_component * 0.18 + interest_component * 0.22 + activity_component * 0.12
    return {
        "final_score": round(final * 100, 2),
        "distance_km": round(distance, 1),
        "interest_score": round(interest_component * 100, 2),
        "activity_score": round(activity_component * 100, 2),
        **daily_astro,
    }


def candidate_allowed_by_preference(current_user: dict[str, Any], candidate: dict[str, Any]) -> bool:
    current_preference = current_user.get("looking_for", "Herkes")
    candidate_gender = candidate.get("gender", NO_ANSWER)
    if current_preference not in ["Herkes", NO_ANSWER] and candidate_gender != current_preference:
        return False

    candidate_preference = candidate.get("looking_for", "Herkes")
    current_gender = current_user.get("gender", NO_ANSWER)
    if candidate_preference not in ["Herkes", NO_ANSWER] and current_gender != candidate_preference:
        return False
    return True


def rank_candidates(current_user: dict[str, Any], users: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates = []
    max_distance = int(current_user.get("max_distance_km", 80) or 80)
    reacted_ids = get_reacted_user_ids(current_user["id"])
    for user in users:
        if user.get("id") == current_user.get("id"):
            continue
        if not user.get("profile_completed"):
            continue
        if user.get("id") in reacted_ids:
            continue
        if not candidate_allowed_by_preference(current_user, user):
            continue
        score = combined_match_score(current_user, user)
        if score["distance_km"] <= max_distance:
            item = dict(user)
            item["score"] = score
            candidates.append(item)
    candidates.sort(key=lambda item: item["score"]["final_score"], reverse=True)
    top_count = max(1, round(len(candidates) * 0.05)) if candidates else 0
    for idx, item in enumerate(candidates):
        item["is_top_pick"] = idx < top_count and item["score"]["adjusted_astro_score"] >= 82
    return candidates


def is_tarot_selected(user_id: str, ratio: float = 0.05) -> bool:
    digest = hashlib.sha256(f"lunamatch-tarot:{user_id}:{date.today().isoformat()}".encode("utf-8")).hexdigest()
    bucket_value = int(digest[:8], 16) % 10000
    return bucket_value < int(ratio * 10000)


def tarot_message(user_id: str) -> tuple[str, str]:
    digest = hashlib.sha256(f"lunamatch-message:{user_id}:{date.today().isoformat()}".encode("utf-8")).hexdigest()
    idx = int(digest[:8], 16) % len(TAROT_MESSAGES)
    return TAROT_MESSAGES[idx]


def parse_date(value: Any, fallback: date) -> date:
    if not value:
        return fallback
    try:
        return date.fromisoformat(str(value))
    except Exception:
        return fallback


def sign_index(sign: str | None) -> int:
    if sign in ZODIAC_SIGNS:
        return ZODIAC_SIGNS.index(sign)
    return 0


def request_nav(target: str) -> None:
    st.session_state["nav_override"] = target
    st.rerun()


def auth_page() -> None:
    inject_css()
    st.markdown(
        """
        <div class="lm-topbar">
            <div class="lm-brand">
                <div class="lm-logo">💘</div>
                <div>
                    <div class="lm-brand-name">LUNAMATCH</div>
                    <div class="lm-brand-sub">Kalbinin frekansına uygun insanlarla tanış.</div>
                </div>
            </div>
            <div class="lm-user-pill">Astro Match Dating App</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left_col, right_col = st.columns([1.12, 0.88], gap="large")
    with left_col:
        st.markdown(
            """
            <div class="auth-hero">
                <div class="hero-badge">💘 Yeni nesil romantik eşleşme deneyimi</div>
                <div class="hero-title">Aşkı biraz daha <span class="hero-gradient">uyumlu</span> hale getir.</div>
                <div class="hero-desc">
                    LUNAMATCH; doğum haritanı, ilişki beklentilerini, yaşam tarzını ve ortak ilgi alanlarını
                    bir araya getirerek sana daha anlamlı tanışmalar sunar. Fotoğrafa bak, uyumu gör,
                    kalbinden geçen kişiye adım at.
                </div>
                <div class="hero-pills">
                    <div class="hero-pill">💘 Kalp Gönder</div>
                    <div class="hero-pill">✨ Günlük Uyum</div>
                    <div class="hero-pill">📍 Yakınındaki Profiller</div>
                    <div class="hero-pill">🔮 Romantik Mesajlar</div>
                </div>
                <div class="mini-phone">
                    <div class="mini-photo"></div>
                    <div class="mini-info">
                        <div class="mini-name">Zeynep, 28</div>
                        <div class="mini-text">☀️ Terazi · 🌙 Balık · %87 LUNAMATCH uyumu</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right_col:
        st.markdown(
            """
            <div class="auth-card">
                <div class="auth-title">Hemen başla</div>
                <div class="auth-subtitle">
                    Giriş yap, yeni üyelik oluştur veya şifreni yenile. Profilini tamamladıktan sonra
                    sana en uygun kişileri keşfetmeye başlayabilirsin.
                </div>
            """,
            unsafe_allow_html=True,
        )

        tab_login, tab_register, tab_admin, tab_reset = st.tabs(["Giriş", "Üye Ol", "Admin", "Şifre"])

        with tab_login:
            email = st.text_input("E-posta", key="login_email", placeholder="ornek@mail.com")
            password = st.text_input("Şifre", type="password", key="login_password", placeholder="Şifrenizi girin")
            if st.button("💘 Kalbine Giden Yolu Aç", key="login_button", use_container_width=True):
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
            email = st.text_input("E-posta", key="register_email", placeholder="ornek@mail.com")
            password = st.text_input("Şifre", type="password", key="register_password", placeholder="En az 6 karakter")
            password_repeat = st.text_input("Şifre tekrar", type="password", key="register_password_repeat")
            if st.button("✨ LUNAMATCH’e Katıl", key="register_button", use_container_width=True):
                if not email:
                    st.warning("E-posta adresi zorunludur.")
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
                        profile = get_user(uid)
                        st.session_state["user"] = profile
                        st.session_state["nav_override"] = "👤 Profilim"
                        st.success("Üyelik oluşturuldu. Şimdi profilini parlatma zamanı.")
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))

        with tab_admin:
            email = st.text_input("Admin e-posta", key="admin_email", placeholder="admin@mail.com")
            password = st.text_input("Admin şifre", type="password", key="admin_password")
            if st.button("🛠️ Admin Paneline Giriş", key="admin_button", use_container_width=True):
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
            email = st.text_input("E-posta adresiniz", key="reset_email", placeholder="ornek@mail.com")
            if st.button("🔐 Şifremi Yenile", key="reset_button", use_container_width=True):
                try:
                    send_password_reset(email)
                    st.success("Şifre sıfırlama bağlantısı e-posta adresinize gönderildi.")
                except Exception as exc:
                    st.error(str(exc))

        st.markdown(
            """
                <div class="small-note">
                    LUNAMATCH hesabınla giriş yaparak güvenli, saygılı ve gerçek bağlantılara dayalı
                    bir tanışma deneyimini kabul etmiş olursun.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def require_login() -> None:
    if "user" not in st.session_state:
        auth_page()
        st.stop()


def current_user() -> dict[str, Any]:
    return st.session_state["user"]


def refresh_current_user() -> dict[str, Any]:
    user = current_user()
    fresh = get_user(user["id"])
    if fresh:
        st.session_state["user"] = fresh
        return fresh
    return user


def render_topbar(user: dict[str, Any]) -> None:
    role_label = "Admin" if user.get("role") == "admin" else "Üye"
    premium_label = "Premium" if user.get("is_premium") else "Standart"
    st.markdown(
        f"""
        <div class="lm-topbar">
            <div class="lm-brand">
                <div class="lm-logo">💘</div>
                <div>
                    <div class="lm-brand-name">LUNAMATCH</div>
                    <div class="lm-brand-sub">Bugün kalbine uyumlu biriyle tanışabilirsin.</div>
                </div>
            </div>
            <div class="lm-user-pill">{escape(user.get("email"))} · {role_label} · {premium_label}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def profile_page() -> None:
    user = refresh_current_user()
    existing = get_user(user["id"]) or user
    st.markdown(
        """
        <div class="page-card">
            <div class="section-title">👤 Profilini Parlat</div>
            <div class="section-subtitle">Daha iyi eşleşmeler için kendini doğal, sıcak ve samimi bir şekilde anlat.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    existing_photos = existing.get("photo_urls", []) or []
    if existing_photos:
        st.markdown("#### Mevcut fotoğrafların")
        cols = st.columns(min(5, len(existing_photos)))
        for idx, photo_url in enumerate(existing_photos[:5]):
            with cols[idx]:
                if str(photo_url).startswith("http"):
                    st.image(photo_url, use_container_width=True)

    with st.form("profile_form"):
        st.markdown("### 1. Seni tanıyalım")
        col1, col2 = st.columns(2)
        with col1:
            display_name = st.text_input("Profilde görünecek adın", value=existing.get("display_name", ""), placeholder="Örn. Zeynep")
            age = st.number_input("Yaşın", min_value=18, max_value=99, value=int(existing.get("age", 25) or 25))
            gender = st.selectbox(
                "Kendini nasıl tanımlıyorsun?",
                GENDER_OPTIONS,
                index=GENDER_OPTIONS.index(existing.get("gender", NO_ANSWER)) if existing.get("gender", NO_ANSWER) in GENDER_OPTIONS else 0,
            )
        with col2:
            city = st.text_input("Hangi şehirde yaşıyorsun?", value=existing.get("city", "İstanbul"))
            looking_for = st.selectbox(
                "Kimlerle tanışmak istersin?",
                LOOKING_FOR_OPTIONS,
                index=LOOKING_FOR_OPTIONS.index(existing.get("looking_for", "Herkes")) if existing.get("looking_for", "Herkes") in LOOKING_FOR_OPTIONS else 0,
            )
            relationship_intent = st.selectbox(
                "Şu an ne arıyorsun?",
                RELATIONSHIP_INTENT_OPTIONS,
                index=RELATIONSHIP_INTENT_OPTIONS.index(existing.get("relationship_intent", "Ciddi ilişki")) if existing.get("relationship_intent", "Ciddi ilişki") in RELATIONSHIP_INTENT_OPTIONS else 0,
            )

        st.markdown("### 2. Fotoğrafların")
        photos = st.file_uploader(
            "En fazla 5 fotoğraf yükleyin. Yeni fotoğraf yüklerseniz eskiler güncellenir.",
            type=["png", "jpg", "jpeg", "webp"],
            accept_multiple_files=True,
        )

        st.markdown("### 3. Astroloji bilgilerin")
        col3, col4, col5 = st.columns(3)
        with col3:
            birth_date = st.date_input("Doğum tarihin", value=parse_date(existing.get("birth_date"), date(1998, 1, 1)))
        with col4:
            moon_sign = st.selectbox("Ay burcun", ZODIAC_SIGNS, index=sign_index(existing.get("moon_sign")), format_func=sign_label)
        with col5:
            rising_sign = st.selectbox("Yükselen burcun", ZODIAC_SIGNS, index=sign_index(existing.get("rising_sign")), format_func=sign_label)
        sun_sign = calculate_sun_sign(birth_date)
        st.info(f"Güneş burcun otomatik hesaplandı: {sign_label(sun_sign)}")

        st.markdown("### 4. Kalbini anlatan sorular")
        about_text = st.text_area(
            "Kendini birkaç cümleyle nasıl anlatırsın?",
            value=existing.get("about_text", ""),
            placeholder="Örn. Kahveyi, uzun yürüyüşleri ve derin sohbetleri severim.",
        )
        three_words = st.text_input("Seni en iyi anlatan 3 kelime nedir?", value=existing.get("three_words", ""), placeholder="Örn. Samimi, meraklı, romantik")
        first_date = st.text_input("İlk buluşmada nasıl bir ortam seni mutlu eder?", value=existing.get("first_date", ""), placeholder="Örn. Sakin bir kahveci, güzel bir yürüyüş...")
        relationship_value = st.text_input("Bir ilişkide kalbini en çok ne etkiler?", value=existing.get("relationship_value", ""), placeholder="Örn. Güven, mizah, sadakat...")
        partner_expectations = st.text_input("Yanındaki kişide en çok ne ararsın?", value=existing.get("partner_expectations", ""), placeholder="Örn. İçtenlik, anlayış, neşe...")
        love_language = st.selectbox(
            "Aşk dilin hangisine daha yakın?",
            LOVE_LANGUAGE_OPTIONS,
            index=LOVE_LANGUAGE_OPTIONS.index(existing.get("love_language", NO_ANSWER)) if existing.get("love_language", NO_ANSWER) in LOVE_LANGUAGE_OPTIONS else 0,
        )
        energy_style = st.selectbox(
            "Seni en iyi anlatan enerji hangisi?",
            ENERGY_OPTIONS,
            index=ENERGY_OPTIONS.index(existing.get("energy_style", NO_ANSWER)) if existing.get("energy_style", NO_ANSWER) in ENERGY_OPTIONS else 0,
        )
        weekend_style = st.text_input("Boş bir pazar gününü nasıl geçirmek istersin?", value=existing.get("weekend_style", ""), placeholder="Örn. Geç kahvaltı, sahil yürüyüşü ve film...")

        st.markdown("### 5. İlgi alanların")
        interests = st.multiselect(
            "Seni heyecanlandıran şeyleri seç",
            INTEREST_OPTIONS,
            default=[interest for interest in existing.get("interests", []) if interest in INTEREST_OPTIONS],
        )

        st.markdown("### 6. Konum ve eşleşme tercihleri")
        col6, col7, col8 = st.columns(3)
        with col6:
            location_lat = st.number_input("Enlem", value=float(existing.get("location_lat", 41.0082)), help="İstanbul için varsayılan değer kullanıldı.")
        with col7:
            location_lon = st.number_input("Boylam", value=float(existing.get("location_lon", 28.9784)), help="İstanbul için varsayılan değer kullanıldı.")
        with col8:
            max_distance_km = st.slider("Maksimum mesafe", 5, 250, int(existing.get("max_distance_km", 80) or 80))

        st.markdown("### 7. Uyum algoritması için küçük dokunuşlar")
        col9, col10, col11 = st.columns(3)
        with col9:
            openness = st.slider("Yeni şeylere açıklık", 1, 10, int(existing.get("openness", 7) or 7))
        with col10:
            emotionality = st.slider("Duygusal yakınlık ihtiyacı", 1, 10, int(existing.get("emotionality", 6) or 6))
        with col11:
            extroversion = st.slider("Sosyallik enerjin", 1, 10, int(existing.get("extroversion", 5) or 5))

        submitted = st.form_submit_button("💘 Profilimi Parlat", use_container_width=True)

    if submitted:
        if not display_name.strip():
            st.warning("Profilde görünecek ad zorunludur.")
            return
        if photos and len(photos) > 5:
            st.warning("En fazla 5 fotoğraf yükleyebilirsiniz.")
            return

        photo_urls = existing_photos
        if photos:
            photo_urls = upload_profile_photos(user["id"], photos)
        if not photo_urls:
            st.warning("En az 1 profil fotoğrafı yüklemelisiniz.")
            return

        payload = {
            "display_name": display_name.strip(),
            "age": int(age),
            "gender": gender,
            "city": city.strip() or NO_ANSWER,
            "looking_for": looking_for,
            "relationship_intent": relationship_intent,
            "birth_date": birth_date.isoformat(),
            "sun_sign": sun_sign,
            "moon_sign": moon_sign,
            "rising_sign": rising_sign,
            "photo_urls": photo_urls,
            "about_text": about_text.strip() or NO_ANSWER,
            "three_words": three_words.strip() or NO_ANSWER,
            "first_date": first_date.strip() or NO_ANSWER,
            "relationship_value": relationship_value.strip() or NO_ANSWER,
            "partner_expectations": partner_expectations.strip() or NO_ANSWER,
            "love_language": love_language,
            "energy_style": energy_style,
            "weekend_style": weekend_style.strip() or NO_ANSWER,
            "interests": interests,
            "location_lat": float(location_lat),
            "location_lon": float(location_lon),
            "max_distance_km": int(max_distance_km),
            "openness": int(openness),
            "emotionality": int(emotionality),
            "extroversion": int(extroversion),
            "activity_score": 0.80,
            "is_premium": bool(existing.get("is_premium", False)),
        }
        save_profile(user["id"], payload)
        st.session_state["user"] = get_user(user["id"])
        st.success("Profilin hazır. Şimdi keşfetmeye başlayabilirsin.")
        st.session_state["nav_override"] = "💘 Keşfet"
        st.rerun()


def render_tarot_card(user_id: str) -> None:
    msg1, msg2 = tarot_message(user_id)
    st.markdown(
        f"""
        <div class="page-card">
            <div class="section-title">🔮 Bugünün Romantik Mesajı</div>
            <div class="section-subtitle">{escape(msg1)}</div>
            <div class="reason-box">{escape(msg2)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def discover_page() -> None:
    user = refresh_current_user()
    if not user.get("profile_completed"):
        st.markdown(
            """
            <div class="page-card">
                <div class="section-title">💘 Keşfetmeye başlamadan önce</div>
                <div class="section-subtitle">Sana uygun profilleri gösterebilmemiz için önce profilini tamamlamalısın.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("👤 Profilimi Oluştur", use_container_width=True):
            request_nav("👤 Profilim")
        return

    users = list_users()
    candidates = rank_candidates(user, users)
    remaining = remaining_hearts(user)
    usage = get_daily_usage(user["id"])

    col1, col2, col3 = st.columns(3)
    col1.metric("Bugünkü Kalp Hakkı", remaining)
    col2.metric("Bugün Gönderilen", usage.get("count", 0))
    col3.metric("Üyelik", "Premium" if user.get("is_premium") else "Standart")

    weather = daily_cosmic_weather()
    lucky = ", ".join(sign_label(sign) for sign in weather.lucky_signs)
    st.markdown(
        f"""
        <div class="page-card">
            <div class="section-title">💘 Keşfet</div>
            <div class="section-subtitle">{escape(weather.focus_text)} Bugünün şanslı burçları: <b>{escape(lucky)}</b></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not candidates:
        st.markdown(
            """
            <div class="page-card">
                <div class="section-title">Bugünlük keşif tamamlandı 💫</div>
                <div class="section-subtitle">Şu an kriterlerine uygun yeni profil görünmüyor. Yeni üyeler geldikçe burada belirecek.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    if not user.get("is_premium") and remaining == 0:
        st.markdown(
            """
            <div class="page-card">
                <div class="section-title">Bugünkü kalp hakkın bitti 💘</div>
                <div class="section-subtitle">Premium ile sınırsız kalp gönderebilir, süper uyumları kullanabilir ve daha fazla profili keşfedebilirsin.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("💎 Premium’u İncele", use_container_width=True):
            request_nav("💎 Premium")
        return

    candidate = candidates[0]
    score = candidate["score"]
    photo_urls = candidate.get("photo_urls", []) or []
    photo_url = photo_urls[0] if photo_urls else ""
    interests_html = "".join(f'<span class="interest-badge">{escape(interest)}</span>' for interest in candidate.get("interests", [])[:8])
    signs_html = (
        f'<span class="soft-badge">☀️ {escape(sign_label(candidate.get("sun_sign")))}</span>'
        f'<span class="soft-badge">🌙 {escape(sign_label(candidate.get("moon_sign")))}</span>'
        f'<span class="soft-badge">⬆️ {escape(sign_label(candidate.get("rising_sign")))}</span>'
    )
    top_pick = '<span class="soft-badge">✨ Günün öne çıkan uyumu</span>' if candidate.get("is_top_pick") else ""
    reasons_html = "<br>".join(f"• {escape(reason)}" for reason in score.get("daily_reasons", []))

    st.markdown('<div class="discover-shell">', unsafe_allow_html=True)
    img_col, info_col = st.columns([0.95, 1.05], gap="large")
    with img_col:
        st.markdown('<div class="profile-photo-wrap">', unsafe_allow_html=True)
        if str(photo_url).startswith("http"):
            st.image(photo_url, use_container_width=True)
        else:
            st.markdown("💘 Fotoğraf önizlemesi yok")
        st.markdown("</div>", unsafe_allow_html=True)
    with info_col:
        st.markdown(
            f"""
            <div class="profile-info">
                <div class="profile-name">{escape(candidate.get("display_name"))}, {escape(candidate.get("age"))}</div>
                <div class="profile-meta">{escape(candidate.get("city"))} · {escape(candidate.get("relationship_intent"))}</div>
                <div class="compat-score">💘 %{score["adjusted_astro_score"]} LUNAMATCH uyumu</div>
                <div>{top_pick}</div>
                <div style="margin-top:10px;">{signs_html}</div>
                <p style="font-size:16px; color:#5E4A58; line-height:1.65; margin-top:18px;">“{escape(candidate.get("about_text", candidate.get("three_words", "")))}”</p>
                <div style="margin-top:10px;">{interests_html}</div>
                <div class="reason-box">
                    <b>Neden uyumlu olabilir?</b><br>
                    {reasons_html}<br>
                    • Yaklaşık mesafe: {score["distance_km"]} km<br>
                    • Ortak ilgi uyumu: %{score["interest_score"]}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

    action_col1, action_col2, action_col3 = st.columns(3)
    with action_col1:
        if st.button("👋 Sonraki Profil", key=f"pass_{candidate['id']}", use_container_width=True):
            record_reaction(user["id"], candidate["id"], "pass", bool(user.get("is_premium")))
            st.rerun()
    with action_col2:
        if st.button("💘 Kalp Gönder", key=f"heart_{candidate['id']}", use_container_width=True):
            result = record_reaction(user["id"], candidate["id"], "heart", bool(user.get("is_premium")))
            if not result.get("ok"):
                st.warning("Bugünkü kalp hakkınız bitti.")
            else:
                st.success(f"Kalp gönderildi. Kalan hakkınız: {result.get('remaining')}")
                if result.get("created_match"):
                    st.balloons()
                    st.success("Yeni bir LUNAMATCH eşleşmesi oluştu.")
                if int(result.get("count", 0)) >= 10 and is_tarot_selected(user["id"]):
                    render_tarot_card(user["id"])
            st.rerun()
    with action_col3:
        if st.button("✨ Süper Uyum", key=f"super_{candidate['id']}", use_container_width=True):
            if not user.get("is_premium"):
                st.warning("Süper Uyum Premium üyeler için açıktır.")
                request_nav("💎 Premium")
            else:
                result = record_reaction(user["id"], candidate["id"], "super", True)
                if result.get("created_match"):
                    st.balloons()
                    st.success("Süper Uyum ile eşleşme oluştu.")
                else:
                    st.success("Süper Uyum gönderildi.")
                st.rerun()


def matches_page() -> None:
    user = refresh_current_user()
    st.markdown(
        """
        <div class="page-card">
            <div class="section-title">✨ Eşleşmelerin</div>
            <div class="section-subtitle">Karşılıklı kalp gönderdiğin kişiler burada görünür.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    matches = list_my_matches(user["id"])
    if not matches:
        st.info("Henüz eşleşmen yok. Keşfet ekranından kalp göndermeye başlayabilirsin.")
        if st.button("💘 Keşfet’e Git", use_container_width=True):
            request_nav("💘 Keşfet")
        return
    for match in matches:
        photo_urls = match.get("photo_urls", []) or []
        photo_url = photo_urls[0] if photo_urls else ""
        col1, col2 = st.columns([0.25, 0.75], gap="medium")
        with col1:
            if str(photo_url).startswith("http"):
                st.image(photo_url, use_container_width=True)
        with col2:
            st.markdown(
                f"""
                <div class="match-card">
                    <div style="font-size:24px; font-weight:900; color:#2B1B2E;">{escape(match.get("display_name"))}, {escape(match.get("age"))}</div>
                    <div style="color:#7A6B76; margin:6px 0 12px 0;">{escape(match.get("city"))} · ☀️ {escape(sign_label(match.get("sun_sign")))}</div>
                    <div style="color:#5E4A58; line-height:1.6;">{escape(match.get("about_text", ""))}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def premium_page() -> None:
    user = refresh_current_user()
    st.markdown(
        """
        <div class="page-card">
            <div class="section-title">💎 LUNAMATCH Premium</div>
            <div class="section-subtitle">Daha fazla görünürlük, sınırsız kalp ve daha özel astro uyum deneyimi.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            """
            <div class="premium-card">
                <div class="premium-title">Standart</div>
                <div class="premium-price">Ücretsiz</div>
                <p>• Günlük 20 kalp</p>
                <p>• Temel astro uyum</p>
                <p>• Profil oluşturma</p>
                <p>• Fotoğraflı keşif</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            """
            <div class="premium-card">
                <div class="premium-title">Premium</div>
                <div class="premium-price">Popüler</div>
                <p>• Sınırsız kalp</p>
                <p>• Süper Uyum hakkı</p>
                <p>• Günün öne çıkan profilleri</p>
                <p>• Daha detaylı astro yorumları</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            """
            <div class="premium-card">
                <div class="premium-title">Platinum</div>
                <div class="premium-price">Yakında</div>
                <p>• Seni beğenenleri gör</p>
                <p>• Haftalık romantik tarot</p>
                <p>• Öne çıkan profil</p>
                <p>• Gelişmiş filtreler</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    if user.get("is_premium"):
        st.success("Premium üyeliğiniz aktif görünüyor.")
    else:
        st.info("Ödeme entegrasyonu eklenene kadar Premium yetkisi admin panelinden verilebilir.")


def admin_page() -> None:
    user = refresh_current_user()
    if user.get("role") != "admin":
        st.error("Bu alan yalnızca admin kullanıcılar içindir.")
        return
    st.markdown(
        """
        <div class="page-card">
            <div class="section-title">🛠️ Admin Paneli</div>
            <div class="section-subtitle">Kullanıcıları, rollerini ve premium durumlarını buradan yönetebilirsiniz.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    stats = admin_stats()
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Üye", stats["users"])
    c2.metric("Tam Profil", stats["completed_profiles"])
    c3.metric("Admin", stats["admins"])
    c4.metric("Premium", stats["premium"])
    c5.metric("Reaksiyon", stats["reactions"])
    c6.metric("Eşleşme", stats["matches"])
    users = list_users()
    st.dataframe(
        [
            {
                "id": item.get("id"),
                "email": item.get("email"),
                "ad": item.get("display_name"),
                "rol": item.get("role"),
                "premium": item.get("is_premium"),
                "profil": item.get("profile_completed"),
                "şehir": item.get("city"),
            }
            for item in users
        ],
        use_container_width=True,
    )
    st.markdown("### Kullanıcı yetkisi güncelle")
    if not users:
        st.info("Henüz kullanıcı yok.")
        return
    selected = st.selectbox(
        "Kullanıcı seçin",
        users,
        format_func=lambda item: f"{item.get('email')} · {item.get('display_name')}",
    )
    col1, col2 = st.columns(2)
    with col1:
        new_role = st.selectbox("Rol", ["user", "admin"], index=0 if selected.get("role") != "admin" else 1)
    with col2:
        premium_status = st.checkbox("Premium aktif", value=bool(selected.get("is_premium")))
    if st.button("Güncelle", use_container_width=True):
        set_user_role(selected["id"], new_role)
        set_user_premium(selected["id"], premium_status)
        st.success("Kullanıcı güncellendi.")
        st.rerun()


def main() -> None:
    inject_css()
    require_login()
    user = refresh_current_user()
    render_topbar(user)

    nav_options = ["💘 Keşfet", "✨ Eşleşmeler", "👤 Profilim", "💎 Premium"]
    if user.get("role") == "admin":
        nav_options.append("🛠️ Admin")

    if "main_nav" not in st.session_state or st.session_state["main_nav"] not in nav_options:
        st.session_state["main_nav"] = "💘 Keşfet"

    override = st.session_state.pop("nav_override", None)
    if override in nav_options:
        st.session_state["main_nav"] = override

    selected_nav = st.radio(
        "Menü",
        nav_options,
        horizontal=True,
        label_visibility="collapsed",
        key="main_nav",
    )

    if selected_nav == "💘 Keşfet":
        discover_page()
    elif selected_nav == "✨ Eşleşmeler":
        matches_page()
    elif selected_nav == "👤 Profilim":
        profile_page()
    elif selected_nav == "💎 Premium":
        premium_page()
    elif selected_nav == "🛠️ Admin":
        admin_page()

    st.divider()
    col1, col2 = st.columns([0.75, 0.25])
    with col1:
        st.caption("LUNAMATCH · Aşk, uyum ve keşif deneyimi")
    with col2:
        if st.button("Çıkış Yap", use_container_width=True):
            st.session_state.clear()
            st.rerun()


main()
