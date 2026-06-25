import os
import streamlit as st
from supabase import create_client, Client


@st.cache_resource
def get_supabase() -> Client:
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_ANON_KEY", "")
    if not url or not key:
        raise RuntimeError(
            "请在 .env 或 Streamlit Secrets 中配置 SUPABASE_URL 和 SUPABASE_ANON_KEY"
        )
    return create_client(url, key)
