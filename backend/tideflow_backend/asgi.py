import os
from collections.abc import Awaitable, Callable
from typing import Any

from django.core.asgi import get_asgi_application

from gateway.app import app as fastapi_app


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tideflow_backend.settings")

django_asgi_app = get_asgi_application()


class PrefixDispatcher:
    def __init__(self, prefix: str, prefixed_app: Callable[..., Awaitable[None]], default_app: Callable[..., Awaitable[None]]) -> None:
        self.prefix = prefix.rstrip("/") or "/"
        self.prefixed_app = prefixed_app
        self.default_app = default_app

    async def __call__(self, scope: dict[str, Any], receive: Callable[..., Awaitable[dict[str, Any]]], send: Callable[..., Awaitable[None]]) -> None:
        if scope["type"] not in {"http", "websocket"}:
            await self.default_app(scope, receive, send)
            return

        path = scope.get("path", "")
        if self.prefix != "/" and path == self.prefix:
            forwarded_scope = dict(scope)
            forwarded_scope["root_path"] = scope.get("root_path", "") + self.prefix
            forwarded_scope["path"] = "/"
            await self.prefixed_app(forwarded_scope, receive, send)
            return

        if self.prefix != "/" and path.startswith(f"{self.prefix}/"):
            forwarded_scope = dict(scope)
            forwarded_scope["root_path"] = scope.get("root_path", "") + self.prefix
            forwarded_scope["path"] = path[len(self.prefix):] or "/"
            await self.prefixed_app(forwarded_scope, receive, send)
            return

        await self.default_app(scope, receive, send)


application = PrefixDispatcher("/api", fastapi_app, django_asgi_app)
