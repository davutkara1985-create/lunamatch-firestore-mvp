"""Firebase client helper for LUNAMATCH.

This app is Firestore-only. It does not create or use any local database.
Firebase credentials must be provided through Streamlit Secrets.
"""

from __future__ import annotations

import firebase_admin
import streamlit as st
from firebase_admin import credentials, firestore


REQUIRED_FIREBASE_KEYS = [
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


@st.cache_resource(show_spinner=False)
def get_firestore_client():
    """Return a cached Firestore client.

    The app stops immediately if Firebase secrets are missing or malformed.
    This prevents accidental local database usage.
    """

    if "firebase" not in st.secrets:
        st.error("LUNAMATCH Firebase secrets bulunamadı.")
        st.info(
            "Streamlit Cloud > App > Settings > Secrets alanına [firebase] bloğunu TOML formatında ekleyin."
        )
        st.stop()

    service_account = dict(st.secrets["firebase"])
    missing = [key for key in REQUIRED_FIREBASE_KEYS if not service_account.get(key)]
    if missing:
        st.error("LUNAMATCH Firebase secrets eksik alan içeriyor.")
        st.code(", ".join(missing))
        st.stop()

    # Streamlit TOML can store private_key as multiline string or as escaped \n.
    service_account["private_key"] = service_account["private_key"].replace("\\n", "\n")

    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate(service_account)
            firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception as exc:  # pragma: no cover - user-facing diagnostics
        st.error("LUNAMATCH Firebase bağlantısı kurulamadı.")
        st.exception(exc)
        st.stop()
