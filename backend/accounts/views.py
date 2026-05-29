import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model

from .models import Profile


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

    if phone:
        Profile.objects.create(user=user, phone=phone)

    return JsonResponse({"id": user.id, "email": user.email, "phone": phone}, status=201)
