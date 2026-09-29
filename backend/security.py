
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from pwdlib import PasswordHash


# ============================================================
# SECURITY CONFIG
# ============================================================

SECRET_KEY = "CHANGE_THIS_TO_A_LONG_RANDOM_SECRET_KEY"

ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 60


password_hash = PasswordHash.recommended()


# ============================================================
# PASSWORD HASHING
# ============================================================

def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(
    password: str,
    hashed_password: str,
) -> bool:
    return password_hash.verify(
        password,
        hashed_password,
    )


# ============================================================
# JWT
# ============================================================

def create_access_token(
    data: dict,
    expires_minutes: Optional[int] = None,
) -> str:

    payload = data.copy()

    expire = datetime.now(
        timezone.utc
    ) + timedelta(
        minutes=(
            expires_minutes
            or ACCESS_TOKEN_EXPIRE_MINUTES
        )
    )

    payload["exp"] = expire

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def decode_access_token(token: str) -> dict:

    return jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM],
    )