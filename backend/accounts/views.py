import json
import re

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from django.db.models import F

from .models import Profile
from .auth import create_access_token, create_refresh_token, decode_token
from .models import Session
from django.utils import timezone


def _read_json(request):
    data = json.loads(request.body.decode())
    if not isinstance(data, dict):
        raise ValueError("Expected an object")
    for field in ("email", "phone", "password", "refresh", "role", "full_name"):
        if field in data and not isinstance(data[field], str):
            raise ValueError(f"{field} must be text")
    return data


def _profile_payload(user, profile=None):
    return {
        "id": user.pk,
        "full_name": profile.full_name if profile else user.get_full_name(),
        "email": user.email,
        "phone": profile.phone if profile else None,
        "role": Profile.ROLE_ADMIN if user.is_superuser else (profile.role if profile else Profile.ROLE_PASSENGER),
    }


def _validate_contact(email, phone):
    if not email and not phone:
        raise ValidationError("Keep at least one email or phone for login")
    if email:
        validate_email(email)
    if len(email or phone) > get_user_model()._meta.get_field("username").max_length:
        raise ValidationError("Identifier is too long")
    if phone and not re.fullmatch(r"\+?[0-9]{7,15}", phone):
        raise ValidationError("Phone must contain 7 to 15 digits with an optional leading +")


def _validate_name(name):
    if len(name) > 255 or any(ord(char) < 32 for char in name):
        raise ValidationError("Full name must be at most 255 characters without control characters")



def is_admin_user(user):
    try:
        return getattr(user, "profile").role == "ADMIN"
    except Exception:
        return False



@csrf_exempt
def register(request):
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)

    try:
        data = _read_json(request)
    except Exception:
        return JsonResponse({"detail": "Invalid JSON payload"}, status=400)

    email = (data.get("email") or "").strip().lower() or None
    phone = (data.get("phone") or "").strip() or None
    password = data.get("password")
    full_name = data.get("full_name", "").strip()

    if not password or (not email and not phone):
        return JsonResponse({"detail": "Provide password and at least email or phone"}, status=400)

    User = get_user_model()
    username = email if email else phone

    try:
        _validate_contact(email, phone)
        _validate_name(full_name)
        validate_password(password, User(username=username, email=email or ""))
    except ValidationError as error:
        return JsonResponse({"detail": "; ".join(error.messages)}, status=400)

    if User.objects.filter(username=username).exists():
        return JsonResponse({"detail": "User with this identifier already exists"}, status=400)

    if email and User.objects.filter(email__iexact=email).exists():
        return JsonResponse({"detail": "Email already in use"}, status=400)

    if phone and Profile.objects.filter(phone=phone).exists():
        return JsonResponse({"detail": "Phone already in use"}, status=400)
    try:
        with transaction.atomic():
            user = User.objects.create_user(username=username, email=email or "", password=password)
            profile = Profile.objects.create(user=user, phone=phone, full_name=full_name)
    except IntegrityError:
        return JsonResponse({"detail": "Email or phone already in use"}, status=400)

    return JsonResponse(_profile_payload(user, profile), status=201)


@csrf_exempt
def profile_detail(request):
    # Accept only Bearer authentication on this CSRF-exempt endpoint.
    if not request.META.get("HTTP_AUTHORIZATION", "").lower().startswith("bearer ") or not request.user.is_authenticated:
        return JsonResponse({"detail": "Bearer authentication required"}, status=401)
    if request.method == "GET":
        profile = Profile.objects.filter(user=request.user).first()
        return JsonResponse(_profile_payload(request.user, profile))
    if request.method != "PATCH":
        return JsonResponse({"detail": "Method not allowed"}, status=405)
    try:
        data = _read_json(request)
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"detail": "Invalid JSON payload"}, status=400)
    if not data or set(data) - {"full_name", "email", "phone"}:
        return JsonResponse({"detail": "Provide only full_name, email, or phone"}, status=400)

    User = get_user_model()
    try:
        with transaction.atomic():
            # Serialize edits to this account, including on SQLite.
            User.objects.filter(pk=request.user.pk).update(username=F("username"))
            user = User.objects.get(pk=request.user.pk, is_active=True)
            profile, _ = Profile.objects.get_or_create(user=user, defaults={
                "full_name": user.get_full_name()[:255],
                "role": Profile.ROLE_ADMIN if user.is_superuser else Profile.ROLE_PASSENGER,
            })
            name = data.get("full_name", profile.full_name).strip()
            email = data["email"].strip().lower() if "email" in data else user.email
            phone = (data["phone"].strip() or None) if "phone" in data else profile.phone
            _validate_name(name)
            if "email" in data or "phone" in data:
                _validate_contact(email, phone)
                if email and User.objects.filter(email__iexact=email).exclude(pk=user.pk).exists():
                    raise ValidationError("Email already in use")
                if phone and Profile.objects.filter(phone=phone).exclude(user=user).exists():
                    raise ValidationError("Phone already in use")
                user.username = email or phone
                user.email = email
                user.save(update_fields=["username", "email"])
            profile.full_name = name
            profile.phone = phone
            profile.save(update_fields=["full_name", "phone"])
    except User.DoesNotExist:
        return JsonResponse({"detail": "Account unavailable"}, status=401)
    except ValidationError as error:
        return JsonResponse({"detail": "; ".join(error.messages)}, status=400)
    except IntegrityError:
        return JsonResponse({"detail": "Email or phone already in use"}, status=400)
    return JsonResponse(_profile_payload(user, profile))


@csrf_exempt
def login(request):
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)

    try:
        data = _read_json(request)
    except Exception:
        return JsonResponse({"detail": "Invalid JSON payload"}, status=400)

    identifier = (data.get("email") or data.get("phone") or "").strip()
    password = data.get("password")
    if not identifier or not password:
        return JsonResponse({"detail": "Provide identifier and password"}, status=400)

    User = get_user_model()
    user = None
    if "@" in identifier:
        try:
            user = User.objects.get(email__iexact=identifier)
        except (User.DoesNotExist, User.MultipleObjectsReturned):
            user = None
    else:
        # phone lookup via Profile
        try:
            prof = Profile.objects.get(phone=identifier)
            user = prof.user
        except Profile.DoesNotExist:
            user = None

    if user is None or not user.is_active or not user.check_password(password):
        return JsonResponse({"detail": "Invalid credentials"}, status=401)

    access = create_access_token(user)
    refresh, jti, expires_at = create_refresh_token(user)

    # store session
    Session.objects.create(user=user, jti=jti, expires_at=expires_at)

    role = None
    try:
        role = getattr(user, "profile").role
    except Exception:
        role = None

    return JsonResponse({"access": access, "refresh": refresh, "role": role}, status=200)


@csrf_exempt
def refresh(request):
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)
    try:
        data = _read_json(request)
    except Exception:
        return JsonResponse({"detail": "Invalid JSON payload"}, status=400)

    token = data.get("refresh")
    payload = decode_token(token)
    if not payload or payload.get("type") != "refresh":
        return JsonResponse({"detail": "Invalid refresh token"}, status=401)

    jti = payload.get("jti")
    try:
        sess = Session.objects.select_related("user").get(
            jti=jti, user_id=payload["user_id"], user__is_active=True,
            revoked=False, expires_at__gt=timezone.now(),
        )
    except Session.DoesNotExist:
        return JsonResponse({"detail": "Session not found"}, status=401)

    user = sess.user
    access = create_access_token(user)
    refresh, new_jti, expires_at = create_refresh_token(user)

    # revoke old session and create new
    sess.revoked = True
    sess.save()
    Session.objects.create(user=user, jti=new_jti, expires_at=expires_at)

    return JsonResponse({"access": access, "refresh": refresh}, status=200)


@csrf_exempt
def logout(request):
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)

    try:
        data = _read_json(request)
    except Exception:
        return JsonResponse({"detail": "Invalid JSON payload"}, status=400)

    token = data.get("refresh")
    payload = decode_token(token)
    if not payload or payload.get("type") != "refresh":
        return JsonResponse({"detail": "Invalid refresh token"}, status=400)

    jti = payload.get("jti")
    Session.objects.filter(jti=jti).update(revoked=True)
    return JsonResponse({"detail": "Logged out"}, status=200)


@csrf_exempt
def set_role(request):
    """Admin-only endpoint to set another user's role.

    Payload: { "user_id": <id>, "role": "DECK_AGENT" }
    """
    # require admin
    if not getattr(request, "user", None) or not getattr(request.user, "is_authenticated", False):
        return JsonResponse({"detail": "Authentication required"}, status=401)

    # Only allow admins (superuser OR profile role ADMIN)
    if not (request.user.is_superuser or is_admin_user(request.user)):
        return JsonResponse({"detail": "Admin privileges required"}, status=403)

    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)

    try:
        data = _read_json(request)
    except Exception:
        return JsonResponse({"detail": "Invalid JSON payload"}, status=400)

    user_id = data.get("user_id")
    role = data.get("role")
    if type(user_id) is not int or not 0 < user_id <= 9223372036854775807:
        return JsonResponse({"detail": "user_id must be a positive integer"}, status=400)
    if role not in dict(Profile.ROLE_CHOICES):
        return JsonResponse({"detail": "Invalid role"}, status=400)

    User = get_user_model()
    try:
        target = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({"detail": "User not found"}, status=404)

    with transaction.atomic():
        prof, _ = Profile.objects.get_or_create(user=target)
        prof.role = role
        prof.save()
        target.is_staff = role == Profile.ROLE_ADMIN
        target.is_superuser = role == Profile.ROLE_ADMIN
        target.save(update_fields=["is_staff", "is_superuser"])

    return JsonResponse({"detail": "Role updated", "user_id": target.id, "role": prof.role}, status=200)
