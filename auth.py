import hashlib
import os
from db import get_supabase


def _hash(password: str, username: str) -> str:
    salt = f"deeptalk_{username}_2024"
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt.encode(), 260000
    ).hex()


def register(username: str, password: str, display_name: str) -> tuple[bool, str]:
    if not username or not password:
        return False, "用户名和密码不能为空"
    if len(username) < 3:
        return False, "用户名至少 3 个字符"
    if len(password) < 6:
        return False, "密码至少 6 位"

    sb = get_supabase()
    existing = sb.table("users").select("username").eq("username", username).execute()
    if existing.data:
        return False, "用户名已存在"

    sb.table("users").insert({
        "username": username,
        "display_name": display_name or username,
        "password_hash": _hash(password, username),
    }).execute()
    return True, ""


def verify(username: str, password: str) -> bool:
    sb = get_supabase()
    res = sb.table("users").select("password_hash").eq("username", username).execute()
    if not res.data:
        return False
    return _hash(password, username) == res.data[0]["password_hash"]


def is_admin_login(username: str, password: str) -> bool:
    admin_user = os.getenv("ADMIN_USERNAME", "")
    admin_pass = os.getenv("ADMIN_PASSWORD", "")
    return bool(admin_user) and username == admin_user and password == admin_pass


def get_display_name(username: str) -> str:
    sb = get_supabase()
    res = sb.table("users").select("display_name").eq("username", username).execute()
    return res.data[0]["display_name"] if res.data else username


def list_users() -> list[str]:
    sb = get_supabase()
    res = sb.table("users").select("username").execute()
    return [r["username"] for r in res.data]


def delete_user(username: str):
    sb = get_supabase()
    # persons 和 global_history 通过 ON DELETE CASCADE 自动删除
    sb.table("users").delete().eq("username", username).execute()
