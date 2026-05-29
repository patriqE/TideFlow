from django.http import JsonResponse


def index(request):
    return JsonResponse({"service": "django", "status": "ok"})


def health_check(request):
    return JsonResponse({"service": "django", "status": "healthy"})
