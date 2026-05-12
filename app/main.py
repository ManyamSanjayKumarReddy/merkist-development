from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from tortoise.contrib.fastapi import register_tortoise

from app.config import get_settings
from app.database import TORTOISE_ORM

settings = get_settings()


def create_app() -> FastAPI:
    app = FastAPI(title="IGStore API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_tortoise(
        app,
        config=TORTOISE_ORM,
        generate_schemas=False,
        add_exception_handlers=True,
    )

    from app.routes.auth import router as auth_router
    app.include_router(auth_router, prefix="/auth", tags=["Authentication"])

    from app.routes.users import router as users_router
    app.include_router(users_router, prefix="/users", tags=["Users"])

    from app.routes.instagram import auth_router as ig_auth_router, router as ig_router
    app.include_router(ig_auth_router, prefix="/auth/instagram", tags=["Instagram OAuth"])
    app.include_router(ig_router, prefix="/instagram", tags=["Instagram"])

    from app.routes.dm import router as dm_router
    app.include_router(dm_router, prefix="/instagram/dm", tags=["Instagram DMs"])

    @app.get("/", tags=["Health"])
    async def root():
        return {"status": "ok", "message": "IGStore API is up and running"}

    @app.get("/health", tags=["Health"])
    async def health():
        return {"status": "ok"}

    return app


app = create_app()