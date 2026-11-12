import jwt
import uuid
from datetime import datetime, timedelta, timezone

from django.conf import settings
from django.contrib.auth import get_user_model

ACCESS_TOKEN_LIFETIME = timedelta(minutes=15)
REFRESH_TOKEN_LIFETIME = timedelta(days=7)


def _now():
    return datetime.now(timezone.utc)


def create_access_token(user):
    now = _now()
    # include role in access token if available
    role = None
    try:
        role = getattr(user, "profile").role
    except Exception:
        role = None

    payload = {
        "user_id": user.id,
        "type": "access",
        "role": role,
        "exp": now + ACCESS_TOKEN_LIFETIME,
        "iat": now,
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    return token


def create_refresh_token(user):
    now = _now()
    jti = str(uuid.uuid4())
    payload = {
        "user_id": user.id,
        "type": "refresh",
        "jti": jti,
        "exp": now + REFRESH_TOKEN_LIFETIME,
        "iat": now,
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    return token, jti, now + REFRESH_TOKEN_LIFETIME


def decode_token(token):
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=["HS256"],
            options={"require": ["exp", "iat", "user_id", "type"]},
        )
        if type(payload["user_id"]) is not int or payload["user_id"] <= 0:
            return None
        if payload["type"] not in ("access", "refresh"):
            return None
        if payload["type"] == "refresh" and (
            not isinstance(payload.get("jti"), str) or not payload["jti"].strip()
        ):
            return None
        return payload
    except (jwt.InvalidTokenError, TypeError, ValueError):
        return None


def get_user_from_payload(payload):
    if not payload or payload.get("type") != "access":
        return None
    User = get_user_model()
    try:
        return User.objects.get(id=payload.get("user_id"), is_active=True)
    except User.DoesNotExist:
        return None
