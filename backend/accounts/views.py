import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model

from .models import Profile
from .auth import create_access_token, create_refresh_token, decode_token
from .models import Session
from django.utils import timezone
from django.contrib.auth.decorators import user_passes_test
from django.conf import settings



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
        data = json.loads(request.body.decode())
    except Exception:
        return JsonResponse({"detail": "Invalid JSON payload"}, status=400)

    email = (data.get("email") or "").strip() or None
    phone = (data.get("phone") or "").strip() or None
    password = data.get("password")

    if not password or (not email and not phone):
        return JsonResponse({"detail": "Provide password and at least email or phone"}, status=400)

    User = get_user_model()
    username = email if email else phone

    if User.objects.filter(username=username).exists():
        return JsonResponse({"detail": "User with this identifier already exists"}, status=400)

    if email and User.objects.filter(email=email).exists():
        return JsonResponse({"detail": "Email already in use"}, status=400)

    user = User.objects.create_user(username=username, email=email)
    user.set_password(password)
    user.save()

    # new users default to PASSENGER role
    if phone:
        Profile.objects.create(user=user, phone=phone)
    else:
        # ensure profile exists even without phone
        Profile.objects.create(user=user)

    return JsonResponse({"id": user.id, "email": user.email, "phone": phone}, status=201)


@csrf_exempt
def login(request):
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body.decode())
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
            user = User.objects.get(email=identifier)
        except User.DoesNotExist:
            user = None
    else:
        # phone lookup via Profile
        try:
            prof = Profile.objects.get(phone=identifier)
            user = prof.user
        except Profile.DoesNotExist:
            user = None

    if user is None or not user.check_password(password):
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
        data = json.loads(request.body.decode())
    except Exception:
        return JsonResponse({"detail": "Invalid JSON payload"}, status=400)

    token = data.get("refresh")
    payload = decode_token(token)
    if not payload or payload.get("type") != "refresh":
        return JsonResponse({"detail": "Invalid refresh token"}, status=401)

    jti = payload.get("jti")
    try:
        sess = Session.objects.get(jti=jti, revoked=False)
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
        data = json.loads(request.body.decode())
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
        data = json.loads(request.body.decode())
    except Exception:
        return JsonResponse({"detail": "Invalid JSON payload"}, status=400)

    user_id = data.get("user_id")
    role = data.get("role")
    if not user_id or not role:
        return JsonResponse({"detail": "Provide user_id and role"}, status=400)

    User = get_user_model()
    try:
        target = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({"detail": "User not found"}, status=404)

    # ensure profile exists
    prof, _ = Profile.objects.get_or_create(user=target)
    prof.role = role
    prof.save()

    # map ADMIN to Django superuser flags
    if role == Profile.ROLE_ADMIN:
        target.is_staff = True
        target.is_superuser = True
    else:
        # if role removed from admin, clear superuser/staff flags
        target.is_superuser = False
        target.is_staff = False
    target.save()

    return JsonResponse({"detail": "Role updated", "user_id": target.id, "role": prof.role}, status=200)

