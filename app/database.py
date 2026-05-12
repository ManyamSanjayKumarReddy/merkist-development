from app.config import get_settings

settings = get_settings()

TORTOISE_ORM = {
    "connections": {
        "default": settings.DATABASE_URL,
    },
    "apps": {
        "models": {
            "models": [
                "aerich.models",
                "app.models.user",
                "app.models.refresh_tokens",
                "app.models.instagram",
                "app.models.dm",
            ],
            "default_connection": "default",
        },
    },
}