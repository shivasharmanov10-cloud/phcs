
import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(
    BASE_DIR / ".env"
)

# ============================================================
# ENVIRONMENT
# ============================================================

APP_ENV = os.getenv(
    "APP_ENV",
    "development",
).lower()

APP_NAME = os.getenv(
    "APP_NAME",
    "Health Resource Intelligence Platform",
)

APP_VERSION = os.getenv(
    "APP_VERSION",
    "1.0.0",
)


# ============================================================
# SERVER
# ============================================================

HOST = os.getenv(
    "HOST",
    "127.0.0.1",
)

PORT = int(
    os.getenv(
        "PORT",
        "8000",
    )
)


# ============================================================
# FRONTEND
# ============================================================

FRONTEND_URL = os.getenv(
    "FRONTEND_URL",
    "http://localhost:5173",
)


# ============================================================
# DATABASE
# ============================================================

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "",
)


# ============================================================
# SECURITY
# ============================================================

API_KEY = os.getenv(
    "API_KEY",
    "",
)


# ============================================================
# CORS
# ============================================================

def get_allowed_origins():

    origins = os.getenv(
        "CORS_ORIGINS",
        FRONTEND_URL,
    )

    return [
        origin.strip()
        for origin in origins.split(",")
        if origin.strip()
    ]


ALLOWED_ORIGINS = get_allowed_origins()


# ============================================================
# APPLICATION FLAGS
# ============================================================

DEBUG = (
    APP_ENV == "development"
)

IS_PRODUCTION = (
    APP_ENV == "production"
)


# ============================================================
# CONFIG VALIDATION
# ============================================================

def validate_config():

    if PORT < 1 or PORT > 65535:

        raise ValueError(
            "PORT must be between 1 and 65535."
        )

    if IS_PRODUCTION:

        if not DATABASE_URL:

            raise RuntimeError(
                "DATABASE_URL must be configured "
                "in production."
            )

        if not API_KEY:

            raise RuntimeError(
                "API_KEY must be configured "
                "in production."
            )

        if "*" in ALLOWED_ORIGINS:

            raise RuntimeError(
                "Wildcard CORS is not allowed "
                "in production."
            )


validate_config()