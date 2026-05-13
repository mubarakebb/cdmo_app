"""
Authentication module for CDMO Studio.

Storage  : data/users.json  (one JSON file, no external DB required)
Hashing  : PBKDF2-HMAC-SHA256 with a per-user 32-byte random salt,
           100 000 iterations — stdlib only, no extra dependencies.
Tokens   : cryptographically-random 64-hex-char session tokens stored
           in st.session_state["_cdmo_token"] and validated against
           the user record on every page load.

User record shape (stored in users.json):
  {
    "username":   "alice",
    "email":      "alice@example.com",
    "full_name":  "Alice Smith",
    "hash":       "<hex>",   # PBKDF2 digest
    "salt":       "<hex>",   # 32-byte random salt
    "created_at": "2026-05-11T12:34:56",
    "token":      "<hex> | null"   # current session token
  }
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime
from typing import Optional

# ─── Storage path ─────────────────────────────────────────────────────────────

_DATA_DIR  = os.path.join(os.path.dirname(__file__), "..", "data")
_USERS_FILE = os.path.join(_DATA_DIR, "users.json")

_PBKDF2_ITERATIONS = 100_000
_PBKDF2_HASH       = "sha256"
_SALT_BYTES        = 32
_TOKEN_BYTES       = 32   # 64 hex chars


# ─── Internal helpers ─────────────────────────────────────────────────────────

def _ensure_data_dir() -> None:
    os.makedirs(_DATA_DIR, exist_ok=True)


def _load_users() -> dict:
    """Return the users dict keyed by username (lowercase)."""
    _ensure_data_dir()
    if not os.path.exists(_USERS_FILE):
        return {}
    try:
        with open(_USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _save_users(users: dict) -> None:
    _ensure_data_dir()
    with open(_USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)


def _hash_password(password: str, salt_hex: str) -> str:
    """Return the PBKDF2-HMAC-SHA256 hex digest for *password* and *salt_hex*."""
    salt = bytes.fromhex(salt_hex)
    digest = hashlib.pbkdf2_hmac(
        _PBKDF2_HASH,
        password.encode("utf-8"),
        salt,
        _PBKDF2_ITERATIONS,
    )
    return digest.hex()


def _constant_compare(a: str, b: str) -> bool:
    """Timing-safe string comparison."""
    return hmac.compare_digest(a.encode(), b.encode())


# ─── Public API ───────────────────────────────────────────────────────────────

class AuthError(ValueError):
    """Raised for any authentication / validation failure."""


def register_user(
    username: str,
    password: str,
    email: str = "",
    full_name: str = "",
) -> dict:
    """
    Create a new user account.

    Returns the new user record (without hash/salt).
    Raises AuthError on validation failure or duplicate username.
    """
    username  = username.strip().lower()
    email     = email.strip().lower()
    full_name = full_name.strip()

    # ── Validation ──────────────────────────────────────────────────
    if not username:
        raise AuthError("Username cannot be empty.")
    if len(username) < 3:
        raise AuthError("Username must be at least 3 characters.")
    if not username.isalnum() and not all(c.isalnum() or c in "_-" for c in username):
        raise AuthError("Username may only contain letters, numbers, hyphens and underscores.")
    if len(password) < 8:
        raise AuthError("Password must be at least 8 characters.")
    if email and "@" not in email:
        raise AuthError("Invalid e-mail address.")

    users = _load_users()
    if username in users:
        raise AuthError(f"Username '{username}' is already taken.")

    # ── Hash & store ─────────────────────────────────────────────────
    salt_hex   = secrets.token_hex(_SALT_BYTES)
    hash_hex   = _hash_password(password, salt_hex)

    record = {
        "username":   username,
        "email":      email,
        "full_name":  full_name,
        "hash":       hash_hex,
        "salt":       salt_hex,
        "created_at": datetime.utcnow().isoformat(timespec="seconds"),
        "token":      None,
    }
    users[username] = record
    _save_users(users)

    return {k: v for k, v in record.items() if k not in ("hash", "salt")}


def login_user(username: str, password: str) -> str:
    """
    Validate credentials and return a new session token.
    Raises AuthError on failure.
    """
    username = username.strip().lower()
    users    = _load_users()

    record = users.get(username)
    if record is None:
        # Use same error to avoid username enumeration
        raise AuthError("Invalid username or password.")

    expected = _hash_password(password, record["salt"])
    if not _constant_compare(expected, record["hash"]):
        raise AuthError("Invalid username or password.")

    token = secrets.token_hex(_TOKEN_BYTES)
    record["token"] = token
    users[username] = record
    _save_users(users)
    return token


def logout_user(username: str) -> None:
    """Invalidate the stored session token for *username*."""
    username = username.strip().lower()
    users    = _load_users()
    if username in users:
        users[username]["token"] = None
        _save_users(users)


def validate_token(username: str, token: str) -> bool:
    """Return True iff *token* matches the stored token for *username*."""
    if not username or not token:
        return False
    users  = _load_users()
    record = users.get(username.strip().lower())
    if record is None or not record.get("token"):
        return False
    return _constant_compare(record["token"], token)


def get_user(username: str) -> Optional[dict]:
    """Return public user info (no hash/salt) or None."""
    users  = _load_users()
    record = users.get(username.strip().lower())
    if record is None:
        return None
    return {k: v for k, v in record.items() if k not in ("hash", "salt", "token")}


def is_authenticated() -> bool:
    """Check Streamlit session state for a valid auth token."""
    import streamlit as st
    username = st.session_state.get("_cdmo_user")
    token    = st.session_state.get("_cdmo_token")
    return bool(username and token and validate_token(username, token))


def get_current_user() -> Optional[dict]:
    """Return public info for the currently logged-in user, or None."""
    import streamlit as st
    if not is_authenticated():
        return None
    return get_user(st.session_state["_cdmo_user"])


def require_auth() -> None:
    """
    Call at the top of any protected page.
    Redirects to the login page if the user is not authenticated.
    """
    import streamlit as st
    if not is_authenticated():
        st.switch_page("pages/auth/login.py")


def list_users() -> list[dict]:
    """Return all users (public info only). Useful for admin views."""
    users = _load_users()
    return [
        {k: v for k, v in rec.items() if k not in ("hash", "salt", "token")}
        for rec in users.values()
    ]
