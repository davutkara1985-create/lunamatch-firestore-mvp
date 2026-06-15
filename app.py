from __future__ import annotations

from datetime import date

import streamlit as st

from repositories import firestore_repository as repo
from services.astro_service import (
    ZODIAC_SIGNS,
    calculate_sun_sign,
    daily_cosmic_weather,
    is_tarot_selected,
    sign_label,
    tarot_message,
)
from services.matching_service import rank_candidates

APP_NAME = "LUNAMATCH"
COSMIC_SPARK_NAME = "Kozmik Kıvılcım"


st.set_page_config(
    page_title=f"{APP_NAME} Firestore MVP",
    page_icon="🌙",
    layout="wide",
)


def inject_css() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background: radial-gradient(circle at top, #312E81 0%, #1E1B4B 36%, #0F172A 100%);
            color: #F8FAFC;
        }
        .hero {
            padding: 28px;
            border-radius: 28px;
            background: linear-gradient(135deg, rgba(250, 204, 21, 0.16), rgba(236, 72, 153, 0.12));
            border: 1px solid rgba(250, 204, 21, 0.28);
            box-shadow: 0 0 36px rgba(250, 204, 21, 0.10);
            margin-bottom: 20px;
        }
        .profile-card {
            padding: 24px;
            border-radius: 26px;
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(250, 204, 21, 0.25);
            box-shadow: 0 0 34px rgba(236, 72, 153, 0.12);
            margin-bottom: 20px;
        }
        .tarot-card {
            padding: 32px;
            border-radius: 30px;
            background: linear-gradient(145deg, rgba(49, 46, 129, 0.95), rgba(15, 23, 42, 0.95));
            border: 2px solid rgba(250, 204, 21, 0.55);
            box-shadow: 0 0 42px rgba(250, 204, 21, 0.25);
            text-align: center;
            margin: 18px 0;
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
            margin: 4px 4px 4px 0;
            border-radius: 999px;
            background: linear-gradient(90deg, #FACC15, #F97316);
            color: #111827;
            font-weight: 700;
            font-size: 13px;
        }
        .muted { color: #CBD5E1; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header() -> None:
    weather = daily_cosmic_weather()
    lucky = ", ".join(sign_label(sign) for sign in weather.lucky_signs)
    st.markdown(
        f"""
        <div class="hero">
          <h1>🌙 {APP_NAME}</h1>
          <p class="muted">Astrolojik uyum, günlük kozmik enerji ve yakınlık bazlı modern tanışma deneyimi.</p>
          <p><b>Bugünün LUNAMATCH kozmik havası:</b> {weather.focus_text}</p>
          <p>🌙 Ay: <b>{sign_label(weather.moon_sign)}</b> &nbsp; 💫 Venüs: <b>{sign_label(weather.venus_sign)}</b> &nbsp; 🔥 Mars: <b>{sign_label(weather.mars_sign)}</b></p>
          <p>⭐ Bugünün şanslı burçları: <b>{lucky}</b></p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_premium_paywall(user: dict) -> None:
    st.markdown(
        f"""
        <div class="profile-card">
            <h2>✨ Günlük {COSMIC_SPARK_NAME} hakkın bitti</h2>
            <p>Bugün ücretsiz 20 {COSMIC_SPARK_NAME} hakkını kullandın.</p>
            <p><b>LUNAMATCH Premium</b> ile sınırsız {COSMIC_SPARK_NAME}, detaylı astro uyum raporu, yıldız boost ve gelişmiş filtreler açılır.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.button("🌙 LUNAMATCH Premium'u İncele", use_container_width=True)


def render_tarot_card(user_id: str) -> None:
    msg1, msg2 = tarot_message(user_id)
    st.markdown(
        f"""
        <div class="tarot-card">
            <h1>🔮 LUNAMATCH Kozmik Kartı</h1>
            <h2>Evrendeki şanslı kişi sizsiniz.</h2>
            <h3>Almanız Gereken Kişiye Özel Mesaj</h3>
            <p>{msg1}</p>
            <p>{msg2}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def profile_form() -> None:
    st.subheader("🌙 LUNAMATCH Profil Oluştur")
    with st.form("lunamatch_profile_form"):
        display_name = st.text_input("İsim")
        age = st.number_input("Yaş", min_value=18, max_value=99, value=25)
        bio = st.text_area("Kısa bio", placeholder="Kendinizi kısa ve sıcak bir dille anlatın.")
        birth_date = st.date_input("Doğum tarihi")
        birth_city = st.text_input("Doğum yeri", value="İstanbul")
        sun_sign = calculate_sun_sign(birth_date)
        moon_sign = st.selectbox("Ay burcu", ZODIAC_SIGNS, format_func=sign_label)
        rising_sign = st.selectbox("Yükselen burç", ZODIAC_SIGNS, index=1, format_func=sign_label)
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
        col_a, col_b = st.columns(2)
        with col_a:
            location_lat = st.number_input("Enlem", value=41.0082, format="%.6f")
        with col_b:
            location_lon = st.number_input("Boylam", value=28.9784, format="%.6f")
        max_distance_km = st.slider("Maksimum mesafe", 5, 250, 80)
        openness = st.slider("Yeniliğe açıklık", 1, 10, 7)
        emotionality = st.slider("Duygusallık", 1, 10, 6)
        extroversion = st.slider("Dışa dönüklük", 1, 10, 5)
        is_premium = st.toggle("LUNAMATCH Premium kullanıcı", value=False)
        submitted = st.form_submit_button("🌙 Profili Firestore'a Kaydet")

    if submitted:
        if not display_name.strip():
            st.warning("İsim alanı boş olamaz.")
            return
        user_id = repo.create_user(
            {
                "display_name": display_name.strip(),
                "age": int(age),
                "bio": bio.strip(),
                "birth_date": birth_date.isoformat(),
                "birth_city": birth_city.strip(),
                "sun_sign": sun_sign,
                "moon_sign": moon_sign,
                "rising_sign": rising_sign,
                "location_lat": float(location_lat),
                "location_lon": float(location_lon),
                "interests": interests,
                "openness": int(openness),
                "emotionality": int(emotionality),
                "extroversion": int(extroversion),
                "max_distance_km": int(max_distance_km),
                "activity_score": 0.75,
                "is_premium": bool(is_premium),
                "app_name": APP_NAME,
            }
        )
        st.success(f"LUNAMATCH profili oluşturuldu. Kullanıcı ID: {user_id}")
        st.info(f"Otomatik Güneş burcu: {sign_label(sun_sign)}")


def admin_panel() -> None:
    st.subheader("🛠️ LUNAMATCH Firestore Admin")
    st.write("Demo kullanıcıları Firestore'a ekleyerek uygulamayı hızlıca test edebilirsin.")
    if st.button("🌙 Demo LUNAMATCH Profillerini Firestore'a Ekle / Güncelle"):
        count = repo.seed_demo_profiles()
        st.success(f"{count} demo LUNAMATCH profili Firestore'a eklendi veya güncellendi.")
    st.divider()
    users = repo.list_users()
    st.write(f"Firestore'daki toplam LUNAMATCH kullanıcı sayısı: **{len(users)}**")
    if users:
        st.dataframe(
            [
                {
                    "id": user.get("id"),
                    "display_name": user.get("display_name"),
                    "sun": sign_label(user.get("sun_sign")),
                    "moon": sign_label(user.get("moon_sign")),
                    "rising": sign_label(user.get("rising_sign")),
                    "premium": user.get("is_premium", False),
                }
                for user in users
            ],
            use_container_width=True,
        )


def matches_page() -> None:
    st.subheader("✨ LUNAMATCH Eşleşmeleri")
    users = repo.list_users()
    if len(users) < 2:
        st.info("Eşleşme görmek için en az iki kullanıcı gerekir. Firestore Admin sekmesinden demo profilleri ekleyebilirsin.")
        return

    selected = st.selectbox(
        "Aktif LUNAMATCH kullanıcısı",
        users,
        format_func=lambda user: f"{user.get('display_name')} ({sign_label(user.get('sun_sign'))})",
    )
    current_user = selected
    remaining = repo.remaining_cosmic_sparks(current_user)
    usage = repo.get_daily_usage(str(current_user["id"]))

    metric_cols = st.columns(3)
    metric_cols[0].metric("Kalan Kozmik Kıvılcım", remaining)
    metric_cols[1].metric("Bugünkü Kullanım", usage.get("count", 0))
    metric_cols[2].metric("Premium", "Evet" if current_user.get("is_premium") else "Hayır")

    if not current_user.get("is_premium") and remaining == 0:
        render_premium_paywall(current_user)
        return

    candidates = rank_candidates(current_user, users)
    if not candidates:
        st.info("Maksimum mesafe ve filtrelere göre uygun aday bulunamadı.")
        return

    for candidate in candidates:
        score = candidate["score"]
        star_badge = "<span class='gold-badge'>⭐ Günün Yıldız Haritası</span>" if candidate.get("is_star_chart") else ""
        interests = "".join(f"<span class='badge'>{item}</span>" for item in candidate.get("interests", []))
        reasons = "<br>".join(f"• {reason}" for reason in score.get("daily_reasons", []))
        st.markdown(
            f"""
            <div class="profile-card">
                <h2>{candidate.get('display_name')}, {candidate.get('age')} {star_badge}</h2>
                <p>{candidate.get('bio', '')}</p>
                <p>☀️ {sign_label(candidate.get('sun_sign'))} &nbsp; 🌙 {sign_label(candidate.get('moon_sign'))} &nbsp; ⬆️ {sign_label(candidate.get('rising_sign'))}</p>
                <p><b>LUNAMATCH günlük uyum:</b> %{score['adjusted_astro_score']} &nbsp; <span class="muted">Taban: %{score['base_astro_score']} / Günlük bonus: +{score['daily_bonus']}</span></p>
                <p><b>Kombin skor:</b> %{score['final_score']} &nbsp; <b>Mesafe:</b> {score['distance_km']} km</p>
                <p>{interests}</p>
                <p class="muted">{reasons}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🌑 Geç", key=f"pass_{current_user['id']}_{candidate['id']}", use_container_width=True):
                result = repo.record_reaction(str(current_user["id"]), str(candidate["id"]), "pass", bool(current_user.get("is_premium")))
                if result.get("ok"):
                    st.warning("Profil geçildi.")
                    st.rerun()
        with col2:
            if st.button(f"✨ {COSMIC_SPARK_NAME} Gönder", key=f"spark_{current_user['id']}_{candidate['id']}", use_container_width=True):
                result = repo.record_reaction(
                    str(current_user["id"]),
                    str(candidate["id"]),
                    "spark",
                    bool(current_user.get("is_premium")),
                )
                if not result.get("ok") and result.get("reason") == "daily_limit_reached":
                    render_premium_paywall(current_user)
                else:
                    st.success(f"{COSMIC_SPARK_NAME} gönderildi. Kalan hak: {result.get('remaining')}")
                    if result.get("created_match"):
                        st.balloons()
                        st.success("🌙 LUNAMATCH eşleşmesi oluştu!")
                    if int(result.get("count", 0)) >= 10 and is_tarot_selected(str(current_user["id"])):
                        render_tarot_card(str(current_user["id"]))
                    st.rerun()


inject_css()
render_header()

tab_profile, tab_matches, tab_admin = st.tabs([
    "Profil Oluştur",
    "Eşleşmeler",
    "Firestore Admin",
])

with tab_profile:
    profile_form()

with tab_matches:
    matches_page()

with tab_admin:
    admin_panel()
