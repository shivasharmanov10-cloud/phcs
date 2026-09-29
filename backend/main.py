
import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from backend.config import (
    ALLOWED_ORIGINS,
    APP_NAME,
    APP_VERSION,
    DEBUG,
)

from backend.database.database import engine

from backend.routes.alert_routes import router as alert_router
from backend.routes.audit_routes import router as audit_router
from backend.routes.auth_routes import router as auth_router
from backend.routes.dashboard_routes import router as dashboard_router
from backend.routes.federated_routes import router as federated_router
from backend.routes.ml_routes import router as ml_router
from backend.routes.redistribution_routes import (
    router as redistribution_router,
)


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s | "
        "%(levelname)s | "
        "%(name)s | "
        "%(message)s"
    ),
)

logger = logging.getLogger("health-resource-platform")


# ============================================================
# APPLICATION
# ============================================================

app = FastAPI(
    title=APP_NAME,
    description=(
        "ML-powered PHC medicine demand, "
        "inventory risk and federated intelligence API."
    ),
    version=APP_VERSION,
    debug=DEBUG,
)


# ============================================================
# CORS
# ============================================================
#
# IMPORTANT:
# Your Vite frontend is currently running on:
# http://localhost:5174
#
# We also allow:
# http://localhost:5173
# http://127.0.0.1:5173
# http://127.0.0.1:5174
#
# This fixes:
# "blocked by CORS policy"
# ============================================================

LOCAL_FRONTEND_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
]

# Combine configured origins with local development origins
CORS_ORIGINS = list(
    dict.fromkeys(
        list(ALLOWED_ORIGINS) + LOCAL_FRONTEND_ORIGINS
    )
)

logger.info(
    "CORS allowed origins: %s",
    CORS_ORIGINS,
)

app.add_middleware(
    CORSMiddleware,

    allow_origins=CORS_ORIGINS,

    allow_credentials=True,

    allow_methods=[
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "OPTIONS",
    ],

    allow_headers=[
        "Authorization",
        "Content-Type",
        "Accept",
        "Origin",
        "X-Requested-With",
        "X-Request-ID",
    ],
)


# ============================================================
# REQUEST LOGGING
# ============================================================

@app.middleware("http")
async def request_logging_middleware(
    request: Request,
    call_next,
):
    request_id = request.headers.get(
        "X-Request-ID"
    )

    if not request_id:
        request_id = str(uuid.uuid4())

    start_time = time.perf_counter()

    try:
        response = await call_next(request)

        duration = (
            time.perf_counter()
            - start_time
        )

        response.headers[
            "X-Request-ID"
        ] = request_id

        logger.info(
            "%s %s -> %s | %.3fs | request_id=%s",
            request.method,
            request.url.path,
            response.status_code,
            duration,
            request_id,
        )

        return response

    except Exception:
        duration = (
            time.perf_counter()
            - start_time
        )

        logger.exception(
            "%s %s -> ERROR | %.3fs | request_id=%s",
            request.method,
            request.url.path,
            duration,
            request_id,
        )

        raise


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "service": APP_NAME,
        "version": APP_VERSION,
        "status": "running",
        "environment": (
            "development"
            if DEBUG
            else "production"
        ),
        "apis": {
            "auth": "/api/auth",
            "dashboard": "/api/dashboard",
            "ml": "/api/ml",
            "federated": "/api/federated",
            "redistribution": "/api/redistribution",
            "docs": "/docs",
        },
    }


# ============================================================
# HEALTH
# ============================================================

@app.get(
    "/health",
    tags=["System"],
)
def health():
    return {
        "status": "healthy",
        "service": APP_NAME,
        "version": APP_VERSION,
    }


# ============================================================
# READINESS
# ============================================================

@app.get(
    "/ready",
    tags=["System"],
)
def readiness():

    database_status = "healthy"

    try:
        with engine.connect() as connection:
            connection.execute(
                text("SELECT 1")
            )

    except Exception as exc:

        logger.error(
            "Database readiness check failed: %s",
            exc,
        )

        database_status = "unavailable"

    overall_status = (
        "ready"
        if database_status == "healthy"
        else "degraded"
    )

    return {
        "status": overall_status,

        "services": {
            "api": "healthy",
            "database": database_status,
            "ml": "available",
        },

        "version": APP_VERSION,
    }


# ============================================================
# ROUTERS
# ============================================================

app.include_router(alert_router)

app.include_router(
    federated_router
)

app.include_router(
    audit_router
)

app.include_router(
    redistribution_router
)

app.include_router(
    auth_router
)

app.include_router(
    dashboard_router
)

app.include_router(
    ml_router
)


# ============================================================
# STARTUP
# ============================================================

@app.on_event("startup")
async def startup_event():

    logger.info(
        "=================================================="
    )

    logger.info(
        "%s started successfully",
        APP_NAME,
    )

    logger.info(
        "Version: %s",
        APP_VERSION,
    )

    logger.info(
        "Frontend CORS origins: %s",
        CORS_ORIGINS,
    )

    logger.info(
        "=================================================="
    )