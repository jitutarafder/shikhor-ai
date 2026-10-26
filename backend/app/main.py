"""Main FastAPI application entrypoint for Shikhor AI."""

import logging
import uuid
from typing import Callable
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.errors import ShikhorException, create_error_response
from app.core.logging import setup_logging

from contextlib import asynccontextmanager

# Configure logging
setup_logging(debug=settings.DEBUG)
logger = logging.getLogger("shikhor.app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure tables created in dev mode if using SQLite
    if settings.DATABASE_URL.startswith("sqlite"):
        from app.db.base import Base
        from app.db.session import engine
        from app.modules.users import models as _u  # noqa: F401
        from app.modules.auth import models as _a  # noqa: F401
        from app.modules.crop_assistant import models as _c  # noqa: F401
        from app.modules.equipment import models as _e  # noqa: F401
        from app.modules.rentals import models as _r  # noqa: F401
        from app.modules.crop_marketplace import models as _cm  # noqa: F401
        from app.modules.messaging import models as _m  # noqa: F401
        from app.modules.knowledge import models as _k  # noqa: F401
        from app.modules.sync import models as _s  # noqa: F401
        from app.modules.admin import models as _ad  # noqa: F401
        from app.modules.pilot import models as _p  # noqa: F401
        from app.modules.notifications import models as _notif  # noqa: F401
        from app.modules.jobs import models as _jobs  # noqa: F401
        from sqlalchemy import text

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            for col_sql in [
                "ALTER TABLE rental_requests ADD COLUMN selected_dates TEXT",
                "ALTER TABLE messages ADD COLUMN attachment_filename VARCHAR(255)",
                "ALTER TABLE users ADD COLUMN nid VARCHAR(20)",
                "ALTER TABLE users ADD COLUMN dob VARCHAR(20)",
                "ALTER TABLE users ADD COLUMN nid_front_image VARCHAR(500)",
                "ALTER TABLE users ADD COLUMN nid_back_image VARCHAR(500)",
                "ALTER TABLE users ADD COLUMN is_nid_verified BOOLEAN DEFAULT 0",
                "ALTER TABLE users ADD COLUMN nid_verification_status VARCHAR(20) DEFAULT 'pending'",
                "ALTER TABLE users ADD COLUMN nid_rejection_reason VARCHAR(255)",
                "ALTER TABLE users ADD COLUMN is_email_verified BOOLEAN DEFAULT 0",
            ]:
                try:
                    await conn.execute(text(col_sql))
                except Exception:
                    pass  # column already exists
        logger.info("Initialized local SQLite database tables successfully.")

    # Verify MongoDB Atlas connection if configured as active backend
    if getattr(settings, "DATABASE_BACKEND", "sqlite").lower() == "mongodb":
        from app.db.mongodb import close_mongodb_connection, verify_mongodb_connection
        mongo_status = verify_mongodb_connection()
        if mongo_status.get("configured"):
            if mongo_status.get("connected"):
                logger.info(f"[Lifespan] MongoDB Atlas connection verified. Database: '{mongo_status.get('database')}'")
            else:
                logger.warning(f"[Lifespan] MongoDB Atlas connection could not be established: {mongo_status.get('message')}")

    yield

    # Clean shutdown
    close_mongodb_connection()


app = FastAPI(
    title=settings.APP_NAME,
    description="Bangla-first Agricultural Support Platform API",
    version="0.1.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)

# Static Uploads directory for user-uploaded NID and crop images
import os
from fastapi.staticfiles import StaticFiles

uploads_dir = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(os.path.join(uploads_dir, "nid"), exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next: Callable):
    """Assigns or propagates a request correlation ID."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# Standard Error Handlers
@app.exception_handler(ShikhorException)
async def shikhor_exception_handler(request: Request, exc: ShikhorException):
    request_id = getattr(request.state, "request_id", None)
    logger.warning(f"Business logic error [{exc.code}]: {exc.message} (Request {request_id})")
    return create_error_response(
        code=exc.code,
        message=exc.message,
        status_code=exc.status_code,
        request_id=request_id,
        field_errors=exc.field_errors,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    request_id = getattr(request.state, "request_id", None)
    field_errors = {}
    for err in exc.errors():
        field_path = ".".join(str(loc) for loc in err["loc"] if loc != "body")
        field_errors[field_path] = err["msg"]

    logger.info(f"Validation error: {field_errors} (Request {request_id})")
    return create_error_response(
        code="VALIDATION_ERROR",
        message="Request input validation failed. Please check field errors.",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        request_id=request_id,
        field_errors=field_errors,
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    request_id = getattr(request.state, "request_id", None)
    return create_error_response(
        code="HTTP_ERROR",
        message=str(exc.detail),
        status_code=exc.status_code,
        request_id=request_id,
    )


try:
    from pymongo.errors import PyMongoError

    @app.exception_handler(PyMongoError)
    async def pymongo_exception_handler(request: Request, exc: PyMongoError):
        request_id = getattr(request.state, "request_id", None)
        logger.error(f"MongoDB database connection error: {exc} (Request {request_id})")
        return create_error_response(
            code="DATABASE_UNAVAILABLE",
            message="ডেটাবেসের সাথে সংযোগ করা যাচ্ছে না। MongoDB Atlas-এ আপনার বর্তমান আইপি (Network Access) সক্রিয় করা আছে কিনা নিশ্চিত করুন।",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            request_id=request_id,
        )
except ImportError:
    pass


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", None)
    logger.error(f"Unhandled server error: {exc} (Request {request_id})", exc_info=True)
    return create_error_response(
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected server error occurred. Please try again later.",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        request_id=request_id,
    )


# Include API Routers
from app.api.v1.endpoints import crop_disease
app.include_router(crop_disease.router, prefix="/api")
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["root"])
async def root():
    return {
        "name": settings.APP_NAME,
        "status": "online",
        "docsUrl": f"{settings.API_V1_STR}/docs",
    }
