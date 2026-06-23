import hashlib
import json
import os

USERS_FILE = "data/users.json"


def _hash(password: str, username: str) -> str:
    salt = f"deeptalk_{username}_2024"
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt.encode(), 260000
    ).hex()


def _load() -> dict:
    os.makedirs("data", exist_ok=True)
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save(users: dict):
    os.makedirs("data", exist_ok=True)
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def register(username: str, password: str, display_name: str) -> tuple[bool, str]:
    if not username or not password:
        return False, "用户名和密码不能为空"
    if len(username) < 3:
        return False, "用户名至少 3 个字符"
    if len(password) < 6:
        return False, "密码至少 6 位"
    users = _load()
    if username in users:
        return False, "用户名已存在"
    users[username] = {
        "display_name": display_name or username,
        "password_hash": _hash(password, username),
    }
    _save(users)
    return True, ""


def verify(username: str, password: str) -> bool:
    users = _load()
    if username not in users:
        return False
    return _hash(password, username) == users[username]["password_hash"]


def is_admin_login(username: str, password: str) -> bool:
    """Admin credentials are set in .env / Streamlit Secrets."""
    admin_user = os.getenv("ADMIN_USERNAME", "")
    admin_pass = os.getenv("ADMIN_PASSWORD", "")
    return bool(admin_user) and username == admin_user and password == admin_pass


def get_display_name(username: str) -> str:
    users = _load()
    return users.get(username, {}).get("display_name", username)


def list_users() -> list[str]:
    return list(_load().keys())


def delete_user(username: str):
    users = _load()
    users.pop(username, None)
    _save(users)
