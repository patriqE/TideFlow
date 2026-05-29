from fastapi import FastAPI

from gateway.router import router


app = FastAPI(
    title="TideFlow API Gateway",
    version="0.1.0",
    description="FastAPI gateway mounted alongside Django inside the backend folder.",
)

app.include_router(router)
