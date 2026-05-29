import jwt
import uuid
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model

ACCESS_TOKEN_LIFETIME = timedelta(minutes=15)
REFRESH_TOKEN_LIFETIME = timedelta(days=7)


def _now():
    return datetime.utcnow()


def create_access_token(user):
    now = _now()
    payload = {
        "user_id": user.id,
        "type": "access",
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
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except Exception:
        return None


def get_user_from_payload(payload):
    if not payload:
        return None
    User = get_user_model()
    try:
        return User.objects.get(id=payload.get("user_id"))
    except User.DoesNotExist:
        return None
