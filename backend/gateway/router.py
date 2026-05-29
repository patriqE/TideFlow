from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field


router = APIRouter()


class ForwardRequest(BaseModel):
    target_service: str = Field(min_length=1, examples=["orders-service"])
    path: str = Field(min_length=1, examples=["/v1/orders"])
    method: str = Field(default="GET", examples=["GET"])
    payload: dict[str, Any] | None = None


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"service": "fastapi-gateway", "status": "healthy"}


@router.post("/forward")
def forward(request: ForwardRequest) -> dict[str, Any]:
    return {
        "status": "configured",
        "message": "Gateway scaffold is ready for upstream routing logic.",
        "request": request.model_dump(),
    }
