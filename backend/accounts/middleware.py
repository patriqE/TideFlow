from django.contrib.auth.models import AnonymousUser
from django.utils.deprecation import MiddlewareMixin

from .auth import decode_token, get_user_from_payload


class JWTAuthenticationMiddleware(MiddlewareMixin):
    """Middleware that injects `request.user` when a valid Bearer access token is provided."""

    def process_request(self, request):
        auth = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth or not auth.lower().startswith("bearer "):
            request.user = getattr(request, "user", AnonymousUser())
            return

        token = auth.split(" ", 1)[1].strip()
        payload = decode_token(token)
        user = get_user_from_payload(payload)
        if user:
            request.user = user
        else:
            request.user = AnonymousUser()
