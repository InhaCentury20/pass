from __future__ import annotations

import binascii
import hashlib
import hmac
import os
from typing import Tuple

_DEFAULT_ITERATIONS = 100_000


def hash_password(password: str) -> str:
    """
    PBKDF2-HMAC-SHA256 기반 비밀번호 해시 생성
    반환 포맷: {salt_hex}${derived_hex}
    """
    salt = os.urandom(16)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _DEFAULT_ITERATIONS)
    return f"{binascii.hexlify(salt).decode()}${binascii.hexlify(derived).decode()}"


def verify_password(password: str, hashed_value: str) -> bool:
    try:
        salt_hex, hashed_hex = _split_hash(hashed_value)
    except ValueError:
        return False

    salt = binascii.unhexlify(salt_hex)
    expected = binascii.unhexlify(hashed_hex)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _DEFAULT_ITERATIONS)
    return hmac.compare_digest(expected, derived)


def _split_hash(hashed_value: str) -> Tuple[str, str]:
    salt_hex, hashed_hex = hashed_value.split("$", 1)
    if not salt_hex or not hashed_hex:
        raise ValueError("Invalid hashed password format.")
    return salt_hex, hashed_hex

